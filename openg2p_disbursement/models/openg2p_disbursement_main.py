# Created a separate model for disbursement without relating advice and slip

# import odoo.addons.decimal_precision as dp

from dateutil.relativedelta import relativedelta
from datetime import date, datetime, time
from odoo import fields, models, api
from odoo.exceptions import ValidationError
import uuid
import hashlib
import requests


class DisbursementMain(models.Model):
    _name = "openg2p.disbursement.main"
    _description = "Disbursement Main Transaction"
    _inherit = ["mail.thread", "openg2p.mixin.has_document"]

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
        digits="Disbursement",
        required=True,
    )
    company_id = fields.Many2one("res.company", readonly=True, store=True)
    date_start = fields.Date(
        string="Date From",
        required=True,
        default=lambda self: fields.Date.to_string(date.today().replace(day=1)),
        tracking=True,
    )
    date_end = fields.Date(
        string="Date To",
        required=True,
        default=lambda self: fields.Date.to_string(
            (datetime.now() + relativedelta(months=+1, day=1, days=-1)).date()
        ),
        tracking=True,
    )
    currency_id = fields.Many2one("res.currency", required=True, default=1)
    payment_mode = fields.Selection(
        "Payment Mode",
        related="bank_account_id.payment_mode",
        store=True,
        readonly=True,
    )
    beneficiary_request_id = fields.Char(
        string="Request ID", compute="generate_uuid", store=True
    )

    note = fields.Text(
        string="Note for Benficiary",
        required=False,
        default="",
    )

    def generate_uuid(self):
        for rec in self:
            if not rec.beneficiary_request_id:
                rec.beneficiary_request_id = uuid.uuid4().hex

    @api.depends("bank_account_id")
    def _compute_acc_holder_name(self):
        for rec in self:
            rec.acc_holder_name = (
                rec.bank_account_id.acc_holder_name
                or rec.bank_account_id.beneficiary_id.name
            )

    @api.onchange("beneficiary_id")
    def on_change_beneficiary_id(self):
        for rec in self:
            return {
                "domain": {
                    "bank_account_id": [("beneficiary_id", "=", rec.beneficiary_id.id)]
                }
            }
        self.generate_uuid()

    def api_json(self):
        return {
            "name": self.acc_holder_name,
            "bank account no.": self.name,
            "amount": self.amount,
            "paymentmode": self.payment_mode,
            "currency": self.currency_id.name,
            "startdate": self.date_start,
            "enddate": self.date_end,
        }
