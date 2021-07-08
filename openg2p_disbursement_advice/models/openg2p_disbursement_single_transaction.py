import json
import requests
import logging
import uuid
import odoo.addons.decimal_precision as dp
from datetime import date, datetime

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.addons.queue_job.job import job, related_action
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class SingleTransaction(models.Model):
    _name = "openg2p.disbursement.single.transaction"
    _description = "Single Transaction"
    _inherit = ["generic.mixin.no.unlink", "mail.thread", "openg2p.mixin.has_document"]
    allow_unlink_domain = [("state", "=", "draft")]

    bank_account_id = fields.Many2one(
        "res.partner.bank", "Account ID", ondelete="restrict"
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
    beneficiary_id = fields.Many2one(
        "openg2p.beneficiary", "Beneficiary", required=True
    )
    currency_id = fields.Many2one("res.currency", required=True, default=1)

    program_id = fields.Many2one(
        "openg2p.program",
        string="Program",
        copy=False,
        store=True,
    )
    payment_mode = fields.Selection(
        "Payment Mode",
        related="bank_account_id.payment_mode",
        store=True,
        readonly=True,
    )
    state = fields.Selection(
        [
            ("draft", "Drafting"),
            ("confirm", "Confirmed"),
            ("pending", "Pending"),
            ("paymentstatus", "Completed"),
        ],
        string="Status",
        readonly=True,
        default="draft",
    )
    amount = fields.Float(
        "Amount",
        digits=dp.get_precision("Disbursement"),
        required=True,
    )
    company_id = fields.Many2one(
        "res.company",
        readonly=True,
        store=True,
    )
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
    request_id = fields.Char(string="Request ID", compute="_generate_uuid", store=True)
    transaction_status = fields.Char(readonly=True)

    _sql_constraints = [
        ("size_gt_zero", "CHECK (amount>0)", "Amount has to be greater than zero."),
    ]

    @api.onchange("beneficiary_id")
    def on_change_beneficiary_id(self):
        for rec in self:
            return {
                "domain": {
                    "bank_account_id": [("beneficiary_id", "=", rec.beneficiary_id.id)]
                }
            }

    @api.multi
    def _transaction_execution_amount(self):
        """
        Get the amount to execute for this record
        :return: float
        """
        self.ensure_one()
        return self.amount

    @api.depends("bank_account_id")
    def _compute_acc_holder_name(self):
        for rec in self:

            rec.acc_holder_name = (
                rec.bank_account_id.acc_holder_name
                or rec.bank_account_id.beneficiary_id.name
            )

    def action_confirm(self):
        for rec in self:
            rec.state = "confirm"

    def action_pending(self):
        for rec in self:
            rec.state = "pending"

    def action_transaction(self):
        for rec in self:
            rec.state = "paymentstatus"

    def create_single_transfer(self):

        self._generate_uuid()

        headers = {"Content-Type": "application/json"}
        data = {
            "request_id": str(self.request_id),
            "account_number": str(self.name),
            "amount": int(self.amount),
            "currency": str(self.currency_id.name),
            "note": "Sample Transaction",
        }
        json_data = json.dumps(data)

        url = "http://15.207.23.72:5000/channel/" + str(self.payment_mode) + "/transfer"

        try:
            response = requests.post(url, headers=headers, data=json_data)

            self.transaction_status = response.json().get("status")

        except BaseException as e:
            return e

    def single_transfer_status(self):
        params = (("request_id", str(self.request_id)),)
        url = "http://15.207.23.72:5000/channel/" + str(self.payment_mode) + "/transfer"

        try:
            response = requests.get(url, params=params)
            self.transaction_status = response.json()[0]["status"]

        except BaseException as e:
            return e

    def _generate_uuid(self):
        for rec in self:
            if not rec.request_id:
                rec.request_id = uuid.uuid4().hex
