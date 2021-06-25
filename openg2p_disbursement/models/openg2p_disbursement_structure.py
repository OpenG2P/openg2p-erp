# -*- coding:utf-8 -*-
# Copied entirely from Odoo. See Odoo LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class Openg2pDisbursementStructure(models.Model):
    _name = "openg2p.disbursement.structure"
    _description = "Disbursement Structure"

    _inherit = ["generic.mixin.name_with_code", "generic.mixin.uniq_name_code"]

    @api.model
    def _get_parent(self):
        return self.env.ref("openg2p_disbursement.structure_base", False)

    code = fields.Char(
        string="Reference",
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        copy=False,
        default=lambda self: self.env["res.company"]._company_default_get(),
    )
    note = fields.Text(string="Description")
    parent_id = fields.Many2one(
        "openg2p.disbursement.structure", string="Parent", default=_get_parent
    )
    children_ids = fields.One2many(
        "openg2p.disbursement.structure", "parent_id", string="Children", copy=True
    )
    rule_ids = fields.Many2many(
        "openg2p.disbursement.rule",
        "openg2p_structure_disbursement_rule_rel",
        "struct_id",
        "rule_id",
        string="Disbursement Rules",
    )

    @api.constrains("parent_id")
    def _check_parent_id(self):
        if not self._check_recursion():
            raise ValidationError(
                _("You cannot create a recursive disbursement structure.")
            )

    @api.multi
    @api.returns("self", lambda value: value.id)
    def copy(self, default=None):
        self.ensure_one()
        default = dict(default or {}, code=_("%s (copy)") % (self.code))
        return super(Openg2pDisbursementStructure, self).copy(default)

    @api.multi
    def get_all_rules(self):
        """
        @return: returns a list of tuple (id, sequence) of rules that are maybe to apply
        """
        all_rules = []
        for struct in self:
            all_rules += struct.rule_ids._recursive_search_of_rules()
        return all_rules

    @api.multi
    def _get_parent_structure(self):
        parent = self.mapped("parent_id")
        if parent:
            parent = parent._get_parent_structure()
        return parent + self
