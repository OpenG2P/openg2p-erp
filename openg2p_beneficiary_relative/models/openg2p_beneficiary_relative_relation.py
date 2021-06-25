# Copyright (C) 2018 Brainbean Apps (https://brainbeanapps.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class BeneficiaryRelativeRelation(models.Model):
    _name = "openg2p.beneficiary.relative.relation"
    _description = "Beneficiary Relative Relation"

    name = fields.Char(string="Relation", required=True, translate=True)

    _sql_constraints = [
        ("name_id_uniq", "unique(name)", "Name must be unique."),
    ]
