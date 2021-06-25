# -*- coding: utf-8 -*-
# Copyright 2020 OpenG2P (https://www.eficent.com)
# @author: Salton Massally <saltonmassally@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.tools.translate import _


class Bank(models.Model):
    _inherit = "res.bank"

    provider = fields.Selection(
        selection="_selection_provider", string="Payment Initiator"
    )
    provider_account = fields.Many2one(
        comodel_name="keychain.account",
        domain=[("namespace", "!=", False)],
        string="Payment Initiator Credentials",
    )
    execute_method = fields.Selection(
        selection="_selection_execute_method",
        required=True,
        string="Execution Method",
        default="manual",
    )

    def _selection_execute_method(self):
        return [("manual", _("Manual")), ("server2server", _("Server-to-Server"))]

    def _selection_provider(self):
        if self._context.get("install_mode"):
            builder = self.env["component.builder"]
            components_registry = builder._init_global_registry()
            builder.build_registry(
                components_registry, states=("installed", "to upgrade", "to install")
            )
        return [
            (p._provider_name, p._provider_name.title())
            for p in self.env["openg2p.gateway.transaction"].get_all_providers
        ]

    def _get_allowed_execute_method(self):
        return self.env[
            "openg2p.gateway.transaction"
        ].get_provider._allowed_execute_method

    @api.onchange("provider")
    def onchange_provider(self):
        if self.provider and self.provider != "manual":
            self.execute_method = self._get_allowed_execute_method()[0]

    @api.onchange("execute_method")
    def onchange_execute(self):
        if self.provider:
            execute_methods = self._get_allowed_execute_method()
            if self.execute_method not in execute_methods:
                self.execute_method = execute_methods[0]
                return {
                    "warning": {
                        "title": _("Incorrect Value"),
                        "message": _(
                            "This method is not compatible with the provider selected"
                        ),
                    }
                }
