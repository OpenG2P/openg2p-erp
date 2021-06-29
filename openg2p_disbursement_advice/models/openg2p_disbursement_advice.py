# -*- coding: utf-8 -*-
# Copyright 2020 OpenG2P (https://openg2p.org)
# @author: Salton Massally <saltonmassally@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64

from odoo.addons.queue_job.job import related_action, job
from odoo import fields, models, api, _
from odoo.addons.http_routing.models.ir_http import slugify
from odoo.exceptions import ValidationError, UserError


class DisbursementAdvice(models.Model):
    """
    Bank Advice
    """

    _inherit = ["mail.thread", "openg2p.mixin.has_document"]
    _order = "id desc"
    _name = "openg2p.disbursement.advice"
    _description = "Disbursement Bank Advice"

    name = fields.Char(required=True, states={"draft": [("readonly", False)]})
    note = fields.Text(
        "Description",
        default="Please make transfers to the below mentioned account numbers:",
    )
    date_generated = fields.Date(
        readonly=True,
        required=True,
        states={"draft": [("readonly", False)]},
        default=fields.Date.context_today,
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("confirm", "Approved"),
            ("done", "Executed"),  # when sent
            ("cancel", "Cancelled"),
        ],
        "Status",
        readonly=True,
        default="draft",
    )
    date_executed = fields.Date(
        readonly=True,
    )
    number = fields.Char("Reference", readonly=True)
    line_ids = fields.One2many(
        "openg2p.disbursement.advice.line",
        "advice_id",
        "Disbursements",
        states={"draft": [("readonly", False)]},
        readonly=True,
    )
    company_id = fields.Many2one(
        "res.company",
        "Company",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
        ondelete="restrict",
        default=lambda self: self.env.user.company_id,
    )
    currency_id = fields.Many2one(
        related="company_id.currency_id", store=True, readonly=True
    )
    bank_id = fields.Many2one(
        "res.bank", "Bank", states={"draft": [("readonly", False)]}, required=True
    )
    batch_id = fields.Many2one("openg2p.disbursement.batch", "Batch", required=True)
    line_count = fields.Integer(compute="_compute_line_count", readonly=True)
    total = fields.Monetary(compute="_compute_total", store=True, readonly=True)

    _sql_constraints = [
        (
            "uniq_bank_per_batch",
            "unique (batch_id,bank_id)",
            "Only one advice can be sent to a bank per disbursement batch.",
        )
    ]

    @api.depends("line_ids")
    @api.multi
    def _compute_line_count(self):
        for rec in self:
            rec.line_count = len(rec.line_ids)

    @api.multi
    def compute_advice(self):
        """
        Advice - Create Advice lines in Payment Advice and
        compute Advice lines.
        """
        advice_bank_map = {}
        for advice in self:
            if advice.state != "draft":
                raise ValidationError(
                    _(
                        "Advice should be in the draft state for operation to be permitted"
                    )
                )

            advice.line_ids.unlink()
            advice_bank_map[advice.bank_id.id] = advice.id

        batch = self[0].batch_id
        slips = batch.slip_ids
        if len(slips) < 1000:
            self._generate_advice_split_job(batch, slips, advice_bank_map)
            return True
        else:
            # TODO this needs to be cleaned up, we need a way for status of this job to be commuinicated to UI
            self.sudo().with_delay(
                priority=0,
                description="Disbursement Advice: " + batch.name,
                max_retries=1,
            )._generate_advice_split_job(batch, slips, advice_bank_map)
            return {
                "type": "ir.actions.act_window.message",
                "title": _("Disbursement Advice Queued"),
                "message": _(
                    "Generation of the disbursement advice has been queued for processing"
                ),
            }

    @api.multi
    @related_action("_related_action_disbursement_advice")
    @job
    def _generate_advice_split_job(self, batch, slips, advice_bank_map):
        no_bank_rule = self.env.ref(
            "openg2p_disbursement_advice.exception_rule_bank_not_available"
        )
        for slip in slips:
            if slip.state != "done":
                raise ValidationError(
                    "Slip "
                    + slip.name
                    + " should be in the 'done' state for advice to be generated"
                )

            account = slip.beneficiary_id.bank_account_id
            line = slip.line_ids.filtered(lambda i: i.code == "NET")
            if not line:
                raise ValidationError("Could not figure out net for " + slip.name)
            line = line[0]
            created_line = None
            if account:
                advice_line = {
                    "advice_id": advice_bank_map[account.bank_id.id],
                    "bank_account_id": account.id,
                    "beneficiary_id": slip.beneficiary_id.id,
                    "amount": line.total,
                    "slip_id": slip.id,
                }
                created_line = self.env["openg2p.disbursement.advice.line"].create(
                    advice_line
                )
            elif not account and slip.batch_id.no_advice_bank:
                advice_line = {
                    "advice_id": advice_bank_map[batch.no_advice_bank.id],
                    "beneficiary_id": slip.beneficiary_id.id,
                    "amount": line.total,
                    "slip_id": slip.id,
                }
                created_line = self.env["openg2p.disbursement.advice.line"].create(
                    advice_line
                )
            else:
                self.env["openg2p.disbursement.exception"].create(
                    {
                        "rule_id": no_bank_rule.id,
                        "batch_id": slip.batch_id.id,
                        "beneficiary_id": slip.beneficiary_id.id,
                        "slip_id": slip.id,
                    }
                )
            slip.write({"advice_line_id": created_line.id})

    @api.multi
    def confirm_sheet(self):
        """
        confirm Advice - confirmed Advice after computing Advice Lines..
        """
        seq_obj = self.env["ir.sequence"]
        for advice in self:
            if not advice.line_count:
                raise ValidationError(
                    "You can not confirm Payment advice without advice lines."
                )
            advice_year = (
                advice.date_generated.strftime("%m")
                + "-"
                + advice.date_generated.strftime("%Y")
            )
            number = seq_obj.next_by_code("disbursement.advice")
            sequence_num = (
                "PAY"
                + "/"
                + slugify(advice.bank_id.name, max_length=8).upper()
                + "/"
                + advice_year
                + "/"
                + number
            )
            advice.write({"number": sequence_num, "state": "confirm"})
        return True

    @api.multi
    def set_to_draft(self):
        """Resets Advice as draft."""
        self.write({"state": "draft"})

    @api.multi
    def cancel_sheet(self):
        """Marks Advice as cancelled."""
        self.write({"state": "cancel"})

    @api.multi
    def action_execute(self):
        """
        different payment methods use this to do their magic
        Returns (payment file as string, filename)
        """
        self.ensure_one()
        if self.state != "confirm":
            raise UserError(
                _("Operation permitted on on advices in the confirmed state")
            )

        if self.bank_id.execute_method == "manual":
            self.write({"state": "done", "date_executed": fields.Date.today()})
            return self.env.ref(
                "openg2p_disbursement_advice.disbursement_advice"
            ).report_action(self)
        elif self.bank_id.provider:  # TODO use jobs here
            gateway_transaction_obj = self.env["openg2p.gateway.transaction"]
            for line in self.line_ids:
                gateway_transaction_obj.register(line)
            return self.write({"state": "done", "date_executed": fields.Date.today()})
        else:
            raise UserError(_("No handler for this payment method."))

    @api.multi
    @api.depends("line_ids", "line_ids.amount")
    def _compute_total(self):
        for rec in self:
            rec.total = sum(rec.mapped("line_ids.amount") or [0.0])

    @api.multi
    def unlink(self):
        for advice in self:
            if advice.state != "draft":
                raise UserError(_("You cannot delete an advice past its draft state."))
        return super(DisbursementAdvice, self).unlink()

    @api.multi
    def _store_attachment(self, payment_file_str, filename):
        self.ensure_one()
        action = {}
        if payment_file_str and filename:
            attachment = self.env["ir.attachment"].create(
                {
                    "res_model": "openg2p.disbursement.advice",
                    "res_id": self.id,
                    "name": filename,
                    "datas": base64.b64encode(payment_file_str),
                    "datas_fname": filename,
                }
            )
            form_view = self.env.ref("base.view_attachment_form")
            action = {
                "name": _("Disbursement Advice File"),
                "view_mode": "form",
                "view_id": form_view.id,
                "res_model": "ir.attachment",
                "type": "ir.actions.act_window",
                "target": "current",
                "res_id": attachment.id,
            }
        return action
