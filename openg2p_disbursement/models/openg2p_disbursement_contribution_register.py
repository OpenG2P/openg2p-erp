# -*- coding:utf-8 -*-
# Copied entirely from Odoo. See Odoo LICENSE file for full copyright and licensing details.

from odoo import fields, models


class Openg2pContributionRegister(models.Model):
    _name = "openg2p.disbursement.contribution.register"
    _description = "Contribution Register"

    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env["res.company"]._company_default_get(),
    )
    partner_id = fields.Many2one("res.partner", string="Contribution To")
    name = fields.Char(required=True)
    register_line_ids = fields.One2many(
        "openg2p.disbursement.slip.line",
        "register_id",
        string="Register Line",
        readonly=True,
    )
    note = fields.Text(string="Description")
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ("name_uniq", "UNIQUE (name)", "Name must be unique."),
    ]
