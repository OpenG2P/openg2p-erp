# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class RegistrationCategory(models.Model):
    _name = "openg2p.registration.category"
    _description = "Category of Registration"

    name = fields.Char("Name", required=True)
    color = fields.Integer(string="Color Index", default=10)

    _sql_constraints = [
        ("name_uniq", "unique (name)", "Tag name already exists !"),
    ]
