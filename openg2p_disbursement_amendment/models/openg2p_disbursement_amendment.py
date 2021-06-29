# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import Warning as UserError, ValidationError


class Openg2pDisbursementAmendment(models.Model):
    _name = "openg2p.disbursement.amendment"
    _description = "Disbursement Slip Amendment"
    _inherit = ["mail.thread"]

    name = fields.Char(
        "Description",
        size=128,
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    program_id = fields.Many2one(
        "openg2p.program",
        string="Program",
        index=True,
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    date = fields.Date(
        "Effective Date",
        required=True,
        default=fields.Date.context_today,
        index=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    category_id = fields.Many2one(
        "openg2p.disbursement.amendment.category",
        "Category",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
        index=True,
    )
    input_id = fields.Many2one(
        "openg2p.disbursement.rule.input",
        "Disbursement Rule Input",
        store=True,
        readonly=True,
        related="category_id.input_rule_id",
        index=True,
    )
    slip_id = fields.Many2one("openg2p.disbursement.slip", "Paid On", readonly=True)
    batch_id = fields.Many2one(
        "openg2p.disbursement.batch",
        "Process in Batch",
        index=True,
        states={"cancel": [("readonly", True)], "done": [("readonly", True)]},
        domain="[('state', '=', 'draft'), ('program_id', '=', program_id)]",
    )
    beneficiary_id = fields.Many2one(
        "openg2p.beneficiary",
        "Beneficiary",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
        index=True,
    )
    amount = fields.Float(
        "Amount",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
        help="The meaning of this field is dependent on the disbursement rule that uses it.",
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("validate", "Confirmed"),
            ("cancel", "Cancelled"),
            ("done", "Effected"),
        ],
        "State",
        default="draft",
        required=True,
        readonly=True,
    )
    active = fields.Boolean("Active", default=True)
    note = fields.Text("Memo")

    @api.constrains("batch_id")
    def constrain_batch(self):
        # TODO instead of constraining slip_count let's regenerate the affected slip adter confirmation
        if self.filtered(
            lambda r: r.state == "draft"
            and (r.batch_id.state == "draft" or r.batch_id.slip_count != 0)
        ):
            raise ValidationError(
                _(
                    "Batch has to be in the draft state with no computed slip to be selected here"
                )
            )

    @api.onchange("beneficiary_id")
    @api.multi
    def _constraint_amendment(self):
        for rec in self:
            if (
                not rec.program_id
                and rec.beneficiary_id
                and len(rec.beneficiary_id.program_ids) == 1
            ):
                rec.program_id = rec.beneficiary_id.program_ids[0]

    @api.constrains("beneficiary_id", "program_id")
    @api.multi
    def _constraint_check_enrollment(self):
        for rec in self:
            if rec.program_id not in rec.beneficiary_id.program_ids:
                raise ValidationError(
                    "Beneficiary %s is not registered to program %s"
                    % (rec.beneficiary_id.display_name, rec.program_id.name)
                )

    @api.constrains("beneficiary_id", "state", "category_id")
    @api.multi
    def _constraint_check_duplicate(self):
        for rec in self:
            amendment = self.search(
                [
                    ("beneficiary_id", "=", rec.beneficiary_id.id),
                    ("state", "in", ("draft", "validate")),
                    ("category_id", "=", rec.category_id.id),
                    ("program_id", "=", rec.program_id.id),
                    ("id", "!=", rec.id),
                ]
            )
            if amendment:
                raise ValidationError(
                    "Amendment %s (%s) seem to be a duplicate of %s (%s)"
                    % (rec.name, rec.id, amendment.name, amendment.id)
                )

    @api.onchange("beneficiary_id", "category_id")
    @api.multi
    def onchange_beneficiary(self):
        for rec in self:
            if rec.beneficiary_id and rec.category_id:
                rec.name = _("%s Amendment for %s") % (
                    rec.category_id.name,
                    rec.beneficiary_id.display_name,
                )

    @api.multi
    def force_unlink(self):
        return self.with_context(force_remove=True).unlink()

    @api.multi
    def unlink(self):
        if not self.env.context.get("force_remove", False):
            for psa in self:
                if psa.state in ["validate", "done"]:
                    raise UserError(
                        "A Disbursement Slip Amendment that has been confirmed"
                        " cannot be deleted!"
                    )
        return super(Openg2pDisbursementAmendment, self).unlink()

    @api.multi
    def action_done(self):
        self.write({"state": "done"})

    @api.multi
    def action_confirm(self):
        self.write({"state": "validate"})

    @api.multi
    def action_cancel(self):
        self.write({"state": "cancel", "active": False})

    @api.multi
    def action_reset(self):
        for rec in self:
            if rec.state == "done":
                raise ValidationError(
                    _("You cannot reset amendments in the drat stage")
                )
        self.write({"state": "draft"})
