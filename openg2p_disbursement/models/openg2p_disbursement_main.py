# Creating a separate model for disbursement without using advice and slip

import odoo.addons.decimal_precision as dp

from dateutil.relativedelta import relativedelta
from datetime import date, datetime, time
from odoo import fields, models, api
from odoo.exceptions import ValidationError
import uuid
import hashlib
import requests


class DisbursementMain(models.Model):
    _name = 'openg2p.disbursement.main'
    _inherit = ['openg2p.transaction.mixin',
                'mail.thread', 'mail.activity.mixin', 'openg2p.mixin.no_copy']
    _description = 'Disbursement Main Transaction'

    bank_account_id = fields.Many2one(
        'res.partner.bank',
        'Account ID',
        ondelete='restrict'
    )
    name = fields.Char(
        'Bank Account No.',
        related='bank_account_id.acc_number',
        store=True,
        readonly=True
    )

    acc_holder_name = fields.Char(
        string='Account Holder Name',
        compute="_compute_acc_holder_name",
        store=True
    )
    batch_id = fields.Many2one(
        'openg2p.disbursement.batch',
        'Batch',
        required=True
    )

    currency_id = fields.Many2one(
        string="Currency",
        related='batch_id.currency_id',
        # readonly=True,
        # store=True
    )
    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('confirm', 'Approved'),
            ('done', 'Executed'),  # when sent
            ('cancel', 'Cancelled'),
        ],
        'Status',
        readonly=True,
        # related='advice_id.state',
        store=True
    )
    beneficiary_id = fields.Many2one(
        'openg2p.beneficiary',
        'Beneficiary',
        required=True
    )
    amount = fields.Float(
        'Amount',
        digits=dp.get_precision('Disbursement'),
        required=True,
    )
    company_id = fields.Many2one(
        'res.company',
        readonly=True,
        store=True
    )
    receipt_confirmed = fields.Boolean(
        related="transaction_id.receipt_confirmed"
    )
    date_start = fields.Date(
        string='Date From',
        required=True,
        # readonly=True,
        # states={'draft': [('readonly', False)]},
        default=lambda self: fields.Date.to_string(
            date.today().replace(day=1)),
        track_visibility='onchange'
    )
    date_end = fields.Date(
        string='Date To',
        required=True,
        # readonly=True,
        # states={'draft': [('readonly', False)]},
        default=lambda self: fields.Date.to_string(
            (datetime.now() + relativedelta(months=+1, day=1, days=-1)).date()),
        track_visibility='onchange'
    )
    program_id = fields.Many2one(
        'openg2p.program',
        string='Program',
        # readonly=True,
        copy=False,
        store=True,
        related="batch_id.program_id"
    )
    note = fields.Text(
        string='Internal Note',
        readonly=True,
        states={'draft': [('readonly', False)]}
    )
    paid = fields.Boolean(
        string='Made Disbursement Order?',
        readonly=True,
        copy=False,
        states={'draft': [('readonly', False)]}
    )
    payment_mode = fields.Selection(
        [('AFM', 'AfriMoney'), ('SLB', 'Sierra Leone Commercial Bank')],
        required=True
    )

    @api.depends('bank_account_id')
    def _compute_acc_holder_name(self):
        for rec in self:
            rec.acc_holder_name = rec.bank_account_id.acc_holder_name or rec.bank_account_id.beneficiary_id.name

    def create_bulk_transfer(self):
        query = """SELECT p.total, p.currency_id, c.sanitized_acc_number
                        FROM public.openg2p_disbursement_advice AS p  
                        LEFT JOIN public.openg2p_disbursement_advice FROM public.res_partner_bank AS c  
                        ON p.id=c.id  
                        INTO OUTFILE 'accounts.csv' """

        headers = {
            'Content-Type': 'multipart/form-data',
        }

        files = {
            'data': ('accounts.csv', open('accounts.csv', 'rb')),
            'note': (None, 'Bulk transfers'),
            'checksum': (None, str(self.hash_generate())),
            'request_id': (None, str(self.requestID())),
        }

        response = requests.post(
            'https://ph.ee/channel/{payment_mode}/bulk/transfer', headers=headers, files=files)

    def create_single_transfer(self):
        headers = {
            'Content-Type': 'application/json',
        }
        data = {"request_id": str(self.requestID()),
                "account_number": "7878780080316316",
                "amount": 1000000,
                "currency": "RWF",
                "note": "Sample Transaction"}
        response = requests.post(
            'https://ph.ee/channel/{payment_mode}/transfer', headers=headers, data=data)

    def bulk_transfer_status(self, val):
        params = (('bulk_id', val),)
        response = requests.get(
            'https://ph.ee/channel/{payment_mode}/bulk/transfer', params=params)
        return response

    def single_transfer_status(self, val):
        params = (('id', val),)
        response = requests.get(
            'https://ph.ee/channel/{payment_mode}/transfer', params=params)
        return response

    def all_transactions_status(self, mode_of_payment):
        response = requests.get(
            'https://ph.ee/channel/mode_of_payment/transfer')
        return response

    def hash_generate(self):
        m = hashlib.sha256()
        return m

    def requestID(self):
        u = uuid.uuid4()
        return u
