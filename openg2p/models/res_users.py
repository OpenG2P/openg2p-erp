# -*- coding: utf-8 -*-
# Copyright 2020 OpenG2P (https://openg2p.org)
# @author: Salton Massally <saltonmassally@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields


class ResUsers(models.Model):
    _inherit = "res.users"

    location_id = fields.Many2one("openg2p.location", string="Location", index=True)
