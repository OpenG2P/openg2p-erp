# -*- coding: utf-8 -*-
# Copyright 2020 OpenG2P (https://openg2p.org)
# @author: Salton Massally <saltonmassally@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import json
import logging
from datetime import date, datetime

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.addons.queue_job.job import job, related_action
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)
BATCH_SIZE = 500


class SlipBatch(models.Model):
    _name = "openg2p.disbursement.batch"
    _description = "Disbursement Batch"
    _inherit = ["generic.mixin.no.unlink", "mail.thread", "openg2p.mixin.has_document"]
    allow_unlink_domain = [("state", "=", "draft")]

    name = fields.Char(
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
        track_visibility="onchange",
    )
    program_id = fields.Many2one(
        "openg2p.program",
        required=True,
        readonly=True,
        index=True,
        states={"draft": [("readonly", False)]},
        track_visibility="onchange",
    )
    slip_ids = fields.One2many(
        "openg2p.disbursement.slip",
        "batch_id",
        string="Slips",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    slip_count = fields.Integer(
        compute="_compute_slip_stats",
        string="Disbursement Slip Count",
    )
    slip_amount = fields.Monetary(
        compute="_compute_slip_stats",
        string="Total Net",
    )
    state = fields.Selection(
        [
            ("draft", "Drafting"),
            ("generating", "Generating"),
            ("failed", "Generation Failed"),
            ("generated", "Confirming"),
            ("confirm", "Approving"),
            ("approved", "Payment Processing"),
            ("disbursing", "Disbursing"),
            ("done", "Done"),
            ("cancel", "Rejected"),
        ],
        string="Status",
        index=True,
        readonly=True,
        copy=False,
        default="draft",
        track_visibility="onchange",
    )
    date_start = fields.Date(
        string="Date From",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
        default=lambda self: fields.Date.to_string(date.today().replace(day=1)),
        track_visibility="onchange",
    )
    date_end = fields.Date(
        string="Date To",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
        default=lambda self: fields.Date.to_string(
            (datetime.now() + relativedelta(months=+1, day=1, days=-1)).date()
        ),
        track_visibility="onchange",
    )
    job_batch_id = fields.Many2one(
        "queue.job.batch", index=True, string="Background Job"
    )
    job_completeness = fields.Float(
        compute="_compute_job_stat", string="Progress", compute_sudo=True
    )
    job_failures = fields.Float(
        compute="_compute_job_stat", string="Failures", compute_sudo=True
    )
    job_failed_count = fields.Float(
        related="job_batch_id.failed_job_count", related_sudo=True
    )
    job_state = fields.Selection(
        [
            ("draft", "Draft"),
            ("enqueued", "Enqueued"),
            ("progress", "In Progress"),
            ("finished", "Finished"),
        ],
        related="job_batch_id.state",
        related_sudo=True,
        readonly=True,
    )
    company_id = fields.Many2one(
        "res.company",
        "Company",
        required=True,
        readonly=True,
        ondelete="restrict",
        default=lambda self: self.env.user.company_id,
    )
    currency_id = fields.Many2one(
        string="Currency", related="company_id.currency_id", readonly=True, store=True
    )
    exception_count = fields.Integer(compute="_compute_exception_count")
    intended_beneficiaries = fields.Text()

    # states helper fields
    can_confirm = fields.Boolean(
        compute="_compute_can_confirm",
    )
    can_generate = fields.Boolean(
        compute="_compute_can_generate",
    )
    can_approve = fields.Boolean(
        compute="_compute_can_approve",
    )
    can_disburse = fields.Boolean(
        compute="_compute_can_disburse",
    )
    can_close = fields.Boolean(
        compute="_compute_can_close",
    )
    can_cancel = fields.Boolean(
        compute="_compute_can_cancel",
    )
    is_approved = fields.Boolean(
        compute="_compute_state_approved",
    )
    has_checklist_draft = fields.Boolean()
    note = fields.Text()

    @api.multi
    def _compute_can_generate(self):
        self.ensure_one()
        self.can_generate = self.state == "draft" and not isinstance(
            self.id, models.NewId
        )

    @api.multi
    def _compute_can_cancel(self):
        self.ensure_one()
        self.can_cancel = (
            self.state
            in (
                "generating",
                "draft",
                "confirm",
                "approved",
            )
            and not isinstance(self.id, models.NewId)
        )

    @api.multi
    def _compute_can_confirm(self):
        self.ensure_one()
        self.can_confirm = (
            self.state in ("generated", "draft")
            and len(self.slip_ids)
            and (
                self.job_batch_id
                and (self.job_state == "finished" and self.job_failed_count == 0)
                or True
            )
        )

    @api.multi
    def _compute_can_approve(self):
        self.ensure_one()
        self.can_approve = self.state == "confirm"

    @api.multi
    def _compute_can_disburse(self):
        self.ensure_one()
        self.can_disburse = self.state == "approved"

    @api.multi
    def _compute_can_close(self):
        self.ensure_one()
        self.can_close = self.state == "disbursing"

    @api.multi
    @api.depends(
        "job_batch_id", "job_batch_id.completeness", "job_batch_id.failed_percentage"
    )
    def _compute_job_stat(self):
        for rec in self:
            rec.job_completeness = rec.job_batch_id.completeness * 100
            rec.job_failures = rec.job_batch_id.failed_percentage * 100

    @api.multi
    def default_run_beneficiaries(self):
        self.ensure_one()
        date_to = self.date_end
        date_from = self.date_start
        program = self.program_id

        # a enrollment is valid if it ends between the given dates
        clause_1 = ["&", ("date_end", "<=", date_to), ("date_end", ">=", date_from)]
        # OR if it starts between the given dates
        clause_2 = ["&", ("date_start", "<=", date_to), ("date_start", ">=", date_from)]
        # OR if it starts before the date_from and finish after the date_end (or never finish)
        # OR if it starts before the date_from and finish after the date_end (or never finish)
        clause_3 = [
            "&",
            ("date_start", "<=", date_from),
            "|",
            ("date_end", "=", False),
            ("date_end", ">=", date_to),
        ]
        clause_final = (
            [("program_id", "=", program.id), ("state", "=", "open"), "|", "|"]
            + clause_1
            + clause_2
            + clause_3
        )

        return [
            i["beneficiary_id"][0]
            for i in self.env["openg2p.program.enrollment"].search_read(
                clause_final, ["beneficiary_id"]
            )
        ]

    @api.multi
    def action_generate_run(self):
        return self.generate_run()

    @api.multi
    def generate_run(self, beneficiaries=None, redo=True):
        self.ensure_one()
        if self.state != "draft":
            raise UserError("Operation only allowed on batches in the the draft state")

        def chunks(lst, n):
            """Yield successive n-sized chunks from lst."""
            for i in range(0, len(lst), n):
                yield lst[i : i + n]

        if not beneficiaries:
            beneficiaries = self.default_run_beneficiaries()
        if redo:
            self.slip_ids.filtered(
                lambda r: r.beneficiary_id.id in beneficiaries
            ).unlink()  # @TODO potential optimization point

        # we use suspend security to we can run batch with the same user
        batch = (
            self.env["queue.job.batch"]
            .suspend_security()
            .get_new_batch("Disbursement Batch: " + self.name)
        )
        count = 0
        for chunk in chunks(beneficiaries, BATCH_SIZE):
            count += 1
            self.suspend_security().with_context(job_batch=batch).with_delay(
                priority=0,
                description="Disbursement Batch: %s  Part: %s"
                % (self.name, str(count)),
                max_retries=1,
            )._generate_run_split_job(chunk)
        batch.enqueue()
        self.write(
            {
                "state": "generating",
                "job_batch_id": batch.id,
                "intended_beneficiaries": json.dumps(beneficiaries),
            }
        )
        self.env.user.notify_info(
            title=_("Disbursement Batch Queued"),
            message=_(
                "Generation of the batch has been queued; you will be notified when completed"
            ),
            sticky=True,
        )
        return {"type": "ir.actions.close_wizard_refresh_view"}

    @api.multi
    def post_generate_run(self, beneficiaries):
        """
        Mainly here to allow modules that want to act on the actual recordset (as this changes)
        of beneficiaries post run to hook in
        """
        self.ensure_one()
        self.ommitted_beneficiaries_check(beneficiaries)

    @api.multi
    @related_action("_related_action_disbursement_batch")
    @job
    def _generate_run_split_job(self, beneficiaries):
        slip_obj = self.env["openg2p.disbursement.slip"]
        beneficiary_obj = self.env["openg2p.beneficiary"]
        from_date = self.date_start
        to_date = self.date_end
        non_active_enrollment_rule = self.env.ref(
            "openg2p_disbursement.exception_rule_active_enrollment"
        )
        unknown_error_rule = self.env.ref(
            "openg2p_disbursement.exception_rule_unknown_error"
        )

        # let's remove existing exceptions for beneficiaries we are generating slips for
        self.env["openg2p.disbursement.exception"].search(
            [("beneficiary_id", "in", beneficiaries), ("batch_id", "=", self.id)]
        ).unlink()

        for beneficiary in beneficiary_obj.browse(beneficiaries):
            slip_data = self.env["openg2p.disbursement.slip"].build_slip_data(
                from_date, to_date, self.program_id, beneficiary
            )
            res = {
                "beneficiary_id": beneficiary.id,
                "name": slip_data["value"].get("name"),
                "struct_id": slip_data["value"].get("struct_id"),
                "enrollment_id": slip_data["value"].get("enrollment_id"),
                "batch_id": self.id,
                "input_line_ids": [
                    (0, 0, x) for x in slip_data["value"].get("input_line_ids")
                ],
                "date_from": from_date,
                "date_to": to_date,
            }
            if res["enrollment_id"]:
                try:
                    with self.env.cr.savepoint():  # let's have save point here so we can recover from errors
                        slip_obj.create(res).compute_sheet()
                except Exception as e:
                    _logger.exception(_("Error generating disbursement slip"))
                    self.env["openg2p.disbursement.exception"].create(
                        {
                            "rule_id": unknown_error_rule.id,
                            "batch_id": self.id,
                            "beneficiary_id": beneficiary.id,
                            "note": str(e),
                        }
                    )
            else:  # if we are here we could not figure out the active enrollment so let us report this
                self.env["openg2p.disbursement.exception"].create(
                    {
                        "rule_id": non_active_enrollment_rule.id,
                        "batch_id": self.id,
                        "beneficiary_id": beneficiary.id,
                    }
                )

    @api.multi
    @api.depends("slip_ids", "slip_ids.total")
    def _compute_slip_stats(self):
        for rec in self:
            active_slips = rec.slip_ids.filtered(lambda i: i.state != "cancel")
            rec.slip_count = len(active_slips)
            rec.slip_amount = sum(active_slips.mapped("total"))

    @api.multi
    def approve_slip_run(self):
        self.slip_ids.action_slip_done()
        return self.write({"state": "approved"})

    @api.multi
    def start_disbursing_slip_run(self):
        return self.write({"state": "disbursing"})

    @api.multi
    def reset_slip_run(self):
        self.slip_ids.action_reset_draft()
        return self.write({"state": "draft"})

    @api.multi
    def confirm_slip_run(self):
        if not self.slip_ids:
            raise ValidationError(
                _(
                    "Disbursement slips should be generated before batch can be confirmed"
                )
            )
        self.slip_ids.action_slip_confirm()
        return self.write({"state": "confirm"})

    @api.multi
    def cancel_slip_run(self):
        self.slip_ids.action_slip_cancel()
        return self.write({"state": "cancel"})

    @api.multi
    def close_slip_run(self):
        return self.write({"state": "done"})

    @api.multi
    def state_approved(self):
        self.ensure_one()
        return self.state in ("approved", "disbursing", "done")

    @api.multi
    def batch_notify_success(self):
        self.ensure_one()
        self.write({"state": "draft"})
        self.post_generate_run(json.loads(self.intended_beneficiaries))
        self.job_batch_id.user_id.notify_success(
            title=_("Disbursement Processing Successful"),
            message=_("Successfully computed slips for " + self.name),
            sticky=True,
        )

    @api.multi
    def batch_notify_failed(self):
        self.ensure_one()
        self.write({"state": "failed"})
        self.job_batch_id.user_id.notify_danger(
            title=_("Disbursement Processing Failed"),
            message=_("Encountered an error while computing slips for " + self.name),
            sticky=True,
        )

    @api.one
    @api.depends("state")
    def _compute_state_approved(self):
        for rec in self:
            rec.is_approved = rec.state_approved()

    @api.one
    def _compute_exception_count(self):
        for rec in self:
            rec.exception_count = self.env[
                "openg2p.disbursement.exception"
            ].search_count([("batch_id", "=", rec.id)])

    @api.multi
    def view_batch_exceptions(self):
        """Replace the static action used to call the wizard"""
        self.ensure_one()

        res = {
            "type": "ir.actions.act_window",
            "name": "Disbursement Alerts",
            "res_model": "openg2p.disbursement.exception",
            "domain": ("[('batch_id','in',%s)]" % (self.ids,)),
            "view_type": "form",
            "view_mode": "tree,form",
            "view_id": False,
            "target": "current",
        }
        return res

    @job
    def ommitted_beneficiaries_check(self, beneficiaries):
        included = set(self.slip_ids.mapped("beneficiary_id.id"))

        # let's not include in omitted if we already have an exisiting alert there for beneficiary
        existing = set(
            self.env["openg2p.disbursement.exception"]
            .search([("batch_id", "=", self.id)])
            .mapped("beneficiary_id.id")
        )
        included.update(existing)
        rule = self.env.ref("openg2p_disbursement.exception_rule_excluded")

        # let's unlink if exception for this type exists or it remains opharned as slip not attached
        for i in set(beneficiaries) - included:
            self.env["openg2p.disbursement.exception"].create(
                {"rule_id": rule.id, "batch_id": self.id, "beneficiary_id": i}
            )

    _sql_constraints = [
        ("name_uniq", "UNIQUE (name)", "Name must be unique."),
    ]
