# -*- coding: utf-8 -*-
# Copyright 2020 OpenG2P (https://openg2p.org)
# @author: Salton Massally <saltonmassally@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import odoo.addons.decimal_precision as dp

from odoo import fields, models, api
from odoo.exceptions import ValidationError
import uuid
import hashlib
import requests


class DisbursementAdviceLine(models.Model):
    """
    Bank Advice Lines
    """

    _name = "openg2p.disbursement.advice.line"
    _inherit = "openg2p.transaction.mixin"
    _description = "Bank Advice Lines"

    advice_id = fields.Many2one(
        "openg2p.disbursement.advice", "Bank Advice", required=True, ondelete="cascade"
    )
    name = fields.Char(
        "Bank Account No.",
        related="bank_account_id.acc_number",
        store=True,
        readonly=True,
    )
    acc_holder_name = fields.Char(
        string="Account Holder Name", compute="_compute_acc_holder_name", store=True
    )
    bank_account_id = fields.Many2one(
        "res.partner.bank", "Account ID", ondelete="restrict"
    )
    slip_id = fields.Many2one(
        "openg2p.disbursement.slip", "Payslip", required=True, ondelete="cascade"
    )
    currency_id = fields.Many2one("res.currency", related="slip_id.currency_id")
    batch_id = fields.Many2one(
        "openg2p.disbursement.batch",
        "Batch",
        store=True,
        ondelete="cascade",
        related="slip_id.batch_id",
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("confirm", "Approved"),
            ("done", "Executed"),  # when sent
            ("cancel", "Cancelled"),
        ],
        "Status",
        readonly=True,
        related="advice_id.state",
        store=True,
    )
    beneficiary_id = fields.Many2one(
        "openg2p.beneficiary", "Beneficiary", required=True
    )
    amount = fields.Float(
        "Amount",
        digits=dp.get_precision("Disbursement"),
        required=True,
    )
    company_id = fields.Many2one(
        "res.company", readonly=True, store=True, related="advice_id.company_id"
    )
    receipt_confirmed = fields.Boolean(related="transaction_id.receipt_confirmed")

    _sql_constraints = [
        ("size_gt_zero", "CHECK (amount>0)", "Amount has to be greater than zero."),
        (
            "beneficiary_batch_uniq",
            "UNIQUE (beneficiary_id, batch_id)",
            "Beneficiary must be unique per batch.",
        ),
    ]

    @api.multi
    def _transaction_execution_amount(self):
        """
        Get the amount to execute for this record
        :return: float
        """
        self.ensure_one()
        return self.amount

    @api.constrains("bank_account_id")
    def _constrains_account_id(self):
        for rec in self:
            if (
                rec.bank_account_id
                and rec.bank_account_id.bank_id != rec.advice_id.bank_id
            ):
                raise ValidationError(
                    "Bank of the account of advice line can not be different from the bank of the advice"
                )

    @api.depends("bank_account_id")
    def _compute_acc_holder_name(self):
        for rec in self:
            rec.acc_holder_name = (
                rec.bank_account_id.acc_holder_name
                or rec.bank_account_id.beneficiary_id.name
            )
