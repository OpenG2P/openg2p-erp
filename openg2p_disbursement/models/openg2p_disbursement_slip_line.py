# -*- coding:utf-8 -*-
# Copied entirely from Odoo. See Odoo LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError


class SlipLine(models.Model):
    _name = "openg2p.disbursement.slip.line"
    _inherit = "openg2p.disbursement.rule"
    _description = "Disbursement Slip Line"
    _order = "enrollment_id, sequence"

    slip_id = fields.Many2one(
        "openg2p.disbursement.slip",
        string="Disbursement Slip",
        required=True,
        ondelete="cascade",
        index=True,
    )
    batch_id = fields.Many2one(
        "openg2p.disbursement.batch",
        string="Disbursement Batch",
        ondelete="cascade",
        index=True,
        readonly=True,
        store=True,
        related="slip_id.batch_id",
    )
    disbursement_rule_id = fields.Many2one(
        "openg2p.disbursement.rule", string="Rule", required=True
    )
    beneficiary_id = fields.Many2one(
        "openg2p.beneficiary", string="Beneficiary", required=True
    )
    enrollment_id = fields.Many2one(
        "openg2p.program.enrollment", string="Enrollment", required=True, index=True
    )
    rate = fields.Float(
        string="Rate (%)", digits=dp.get_precision("Disbursement Rate"), default=100.0
    )
    amount = fields.Float(digits=dp.get_precision("Disbursement"))
    quantity = fields.Float(digits=dp.get_precision("Disbursement"), default=1.0)
    total = fields.Float(
        compute="_compute_total",
        string="Total",
        digits=dp.get_precision("Disbursement"),
        store=True,
    )

    @api.depends("quantity", "amount", "rate")
    def _compute_total(self):
        for line in self:
            line.total = float(line.quantity) * line.amount * line.rate / 100

    @api.model_create_multi
    def create(self, vals_list):
        for values in vals_list:
            if "beneficiary_id" not in values or "enrollment_id" not in values:
                slip = self.env["openg2p.disbursement.slip"].browse(
                    values.get("slip_id")
                )
                values["beneficiary_id"] = (
                    values.get("beneficiary_id") or slip.beneficiary_id.id
                )
                values["enrollment_id"] = (
                    values.get("enrollment_id")
                    or slip.enrollment_id
                    and slip.enrollment_id.id
                )
                if not values["enrollment_id"]:
                    raise UserError(
                        _(
                            "You must set a enrollment to create a disbursement slip line."
                        )
                    )
        return super(SlipLine, self).create(vals_list)
