# -*- coding:utf-8 -*-
# Copied entirely from Odoo. See Odoo LICENSE file for full copyright and licensing details.

from odoo import fields, models


class Openg2pDisbursementRuleInput(models.Model):
    _name = "openg2p.disbursement.rule.input"
    _description = "Disbursement Rule Input"

    name = fields.Char(
        string="Description",
    )
    code = fields.Char(help="The code that can be used in the disbursement rules")
    input_id = fields.Many2one(
        "openg2p.disbursement.rule", string="Disbursement Rule Input", required=True
    )

    _inherit = ["generic.mixin.name_with_code", "generic.mixin.uniq_name_code"]
