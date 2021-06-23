# -*- coding: utf-8 -*-
# Copyright 2020 OpenG2P (https://openg2p.org)
# @author: Salton Massally <saltonmassally@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields


class CountryState(models.Model):
    _inherit = "res.country.state"

    country_id = fields.Many2one(
        default=lambda self: self.env.user.company_id.country_id.id
    )
