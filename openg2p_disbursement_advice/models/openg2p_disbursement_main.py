# Created a separate model for disbursement without relating advice and slip

import odoo.addons.decimal_precision as dp

from dateutil.relativedelta import relativedelta
from datetime import date, datetime, time
from odoo import fields, models, api
from odoo.exceptions import ValidationError
import uuid
import hashlib
import requests


class DisbursementMain(models.Model):
    _name = "openg2p.disbursement.main"
    _inherit = [
        "openg2p.transaction.mixin",
        "mail.thread",
        "mail.activity.mixin",
        "openg2p.mixin.no_copy",
    ]
    _description = "Disbursement Main Transaction"

    batch_id = fields.Many2one(
        "openg2p.disbursement.batch.transaction", "Batch", required=True
    )
    bank_account_id = fields.Many2one(
        "res.partner.bank", "Account ID", ondelete="restrict"
    )
    program_id = fields.Many2one(
        "openg2p.program",
        string="Program",
        readonly=True,
        copy=False,
        store=True,
        related="batch_id.program_id",
    )
    beneficiary_id = fields.Many2one(
        "openg2p.beneficiary", "Beneficiary", required=True
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
    amount = fields.Float(
        "Amount",
        digits=dp.get_precision("Disbursement"),
        required=True,
    )
    company_id = fields.Many2one("res.company", readonly=True, store=True)
    date_start = fields.Date(
        string="Date From",
        required=True,
        default=lambda self: fields.Date.to_string(date.today().replace(day=1)),
        track_visibility="onchange",
    )
    date_end = fields.Date(
        string="Date To",
        required=True,
        default=lambda self: fields.Date.to_string(
            (datetime.now() + relativedelta(months=+1, day=1, days=-1)).date()
        ),
        track_visibility="onchange",
    )
    currency_id = fields.Many2one("res.currency", required=True)
    payment_mode = fields.Selection(
        "Payment Mode",
        related="bank_account_id.payment_mode",
        store=True,
        readonly=True,
    )

    @api.depends("bank_account_id")
    def _compute_acc_holder_name(self):
        for rec in self:
            rec.acc_holder_name = (
                rec.bank_account_id.acc_holder_name
                or rec.bank_account_id.beneficiary_id.name
            )
