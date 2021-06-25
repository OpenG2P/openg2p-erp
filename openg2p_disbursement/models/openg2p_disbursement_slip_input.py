# -*- coding:utf-8 -*-
# Copied entirely from Odoo. See Odoo LICENSE file for full copyright and licensing details.

from odoo import fields, models


class SlipInput(models.Model):
    _name = "openg2p.disbursement.slip.input"
    _description = "Slip Input"
    _order = "slip_id, sequence"

    _inherit = ["generic.mixin.name_with_code", "generic.mixin.uniq_name_code"]

    name = fields.Char(
        string="Description",
    )
    slip_id = fields.Many2one(
        "openg2p.disbursement.slip",
        string="Disbursement Slip",
        required=True,
        ondelete="cascade",
        index=True,
    )
    sequence = fields.Integer(required=True, index=True, default=10)
    code = fields.Char(help="The code that can be used in the disbursement rules")
    amount = fields.Float(
        help="It is used in computation. For e.g. A rule for sales having "
        "1% commission of basic disbursement for per product can defined in expression "
        "like result = inputs.SALEURO.amount * enrollment.wage*0.01."
    )
    enrollment_id = fields.Many2one(
        "openg2p.program.enrollment",
        related="slip_id.enrollment_id",
        store=True,
        readonly=True,
        string="Enrollment",
        required=True,
        help="The enrollment for which applied this input",
    )
