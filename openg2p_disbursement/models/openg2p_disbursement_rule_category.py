# -*- coding:utf-8 -*-
# Copied entirely from Odoo. See Odoo LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class Openg2pDisbursementRuleCategory(models.Model):
    _name = "openg2p.disbursement.rule.category"
    _description = "Disbursement Rule Category"

    _inherit = ["generic.mixin.name_with_code", "generic.mixin.uniq_name_code"]

    parent_id = fields.Many2one(
        "openg2p.disbursement.rule.category",
        string="Parent",
        help="Linking a disbursement category to its parent is used only for the reporting purpose.",
    )
    children_ids = fields.One2many(
        "openg2p.disbursement.rule.category", "parent_id", string="Children"
    )
    note = fields.Text(string="Description")
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env["res.company"]._company_default_get(),
    )

    @api.constrains("parent_id")
    def _check_parent_id(self):
        if not self._check_recursion():
            raise ValidationError(
                _(
                    "Error! You cannot create recursive hierarchy of Disbursement Rule Category."
                )
            )
