# -*- coding: utf-8 -*-
# Copyright 2020 OpenG2P (https://openg2p.org)
# @author: Salton Massally <saltonmassally@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class KeychainAccount(models.Model):
    _inherit = "keychain.account"

    namespace = fields.Selection(selection_add=[("demo", "Demo")])

    def _demo_init_data(self):
        return {"client_id": None, "mode": "sandbox"}

    def _demo_validate_data(self, data):
        return True
