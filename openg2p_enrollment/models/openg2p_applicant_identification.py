# -*- coding: utf-8 -*-
# Copyright 2020 OpenG2P (https://openg2p.org)
# @author: Salton Massally <saltonmassally@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models, api


class ApplicantIdentification(models.Model):
    _name = "openg2p.applicant.identity"
    _description = "Category of Applicant"

    @api.model
    def _get_supported_id_categories(self):
        categories = []
        for i in self.env['openg2p.beneficiary.id_category'].search([]):
            categories.append((i.code, i.name))

    name = fields.Char(
        "ID #",
        required=True
    )
    type = fields.Selection(
        selection=lambda x: x._get_supported_id_categories(),
        required=True
    )
    applicant_id = fields.Many2one(
        'openg2p.applicant',
        required=True,
        index=True
    )

    _sql_constraints = [
        ('id_uniq', 'unique (type, name)', "ID already exists !"),
    ]
