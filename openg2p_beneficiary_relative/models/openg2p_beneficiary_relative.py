# Copyright (C) 2018 Brainbean Apps (https://brainbeanapps.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime

from dateutil.relativedelta import relativedelta

from odoo import fields, models, api


class Openg2pBeneficiaryRelative(models.Model):
    _name = "openg2p.beneficiary.relative"
    _description = "Beneficiary Relative"

    beneficiary_id = fields.Many2one(
        string="Beneficiary", comodel_name="openg2p.beneficiary", requird=True
    )
    relation_id = fields.Many2one(
        "openg2p.beneficiary.relative.relation",
        string="Relation",
        required=True,
    )
    name = fields.Char(
        string="Name",
        required=True,
    )
    gender = fields.Selection(
        string="Gender",
        selection=[
            ("male", "Male"),
            ("female", "Female"),
            ("other", "Other"),
        ],
    )
    date_of_birth = fields.Date(
        string="Date of Birth",
    )
    age = fields.Float(
        compute="_compute_age",
    )

    job = fields.Char()
    phone = fields.Char()

    notes = fields.Text(
        string="Notes",
    )

    @api.depends("date_of_birth")
    def _compute_age(self):
        for record in self:
            age = relativedelta(datetime.now(), record.date_of_birth)
            record.age = age.years + (age.months / 12)
