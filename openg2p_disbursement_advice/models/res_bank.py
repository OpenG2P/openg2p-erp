# -*- coding: utf-8 -*-
# Copyright 2020 OpenG2P (https://openg2p.org)
# @author: Salton Massally <saltonmassally@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class Bank(models.Model):
    _inherit = "res.bank"

    country = fields.Many2one(
        "res.country", default=lambda self: self.env.user.company_id.country_id
    )
    validation_regex = fields.Char()
    type = fields.Selection(
        [("normal", "Normal"), ("mobile", "Mobile Money")],
        required=True,
        default="normal",
    )
    gateway_account = fields.Char(
        "Gateway Account",
        help="Account that your organization is paying from with this bank",
    )
