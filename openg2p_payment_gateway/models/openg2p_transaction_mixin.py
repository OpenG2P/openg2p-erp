# -*- coding: utf-8 -*-
# Copyright 2020 OpenG2P (https://www.eficent.com)
# @author: Salton Massally <saltonmassally@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models
from odoo.fields import first


class TransactionMixin(models.AbstractModel):
    _name = "openg2p.transaction.mixin"
    _description = "Gateway Transaction Mixin"

    bank_account_id = fields.Many2one(
        "res.partner.bank", "Account", required=True, index=True
    )
    partner_id = fields.Many2one(
        "res.partner",
        string="Partner",
        related="bank_account_id.partner_id",
        store=True,
        readonly=True,
    )
    currency_id = fields.Many2one("res.currency", string="Currency", required=True)
    transaction_id = fields.Many2one(
        "openg2p.gateway.transaction",
        string="Transaction",
    )

    @api.multi
    def _transaction_execution_amount(self):
        """
        Get the amount to execute for this record
        :return: float
        """
        return NotImplementedError

    def _get_transaction_name(self):
        return self.name or ("%s with id %s" % (self._name, self.id))
