# -*- coding: utf-8 -*-
# Copyright 2020 OpenG2P (https://openg2p.org)
# @author: Salton Massally <saltonmassally@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class Openg2pBeneficiary(models.Model):
    _inherit = "openg2p.beneficiary"

    bank_account_id = fields.Many2one(
        "res.partner.bank", string="Bank Account", index=True
    )
    bank_account_number = fields.Char(
        related="bank_account_id.acc_number", readonly=True, store=True, index=True
    )
    bank_account_type = fields.Selection(
        related="bank_account_id.acc_type", readonly=True, store=True
    )

    _sql_constraints = [
        (
            "bank_account_id_uniq",
            "UNIQUE (bank_account_id)",
            "Bank account must be unique to beneficiary.",
        ),
    ]
