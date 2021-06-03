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
                'mail.thread', 'openg2p.mixin.no_copy']
    _description = 'Disbursement Main Transaction'

    name = fields.Char(
        'Bank Account No.',
        # related='bank_account_id.acc_number',
        store=True,
        # readonly=True
    )

    acc_holder_name = fields.Char(
        string='Account Holder Name',
        # compute="_compute_acc_holder_name",
        store=True
    )
    bank_account_id = fields.Many2one(
        'res.partner.bank',
        'Account ID',
        ondelete='restrict'
    )

    currency_id = fields.Many2one(
        'res.currency',
        # related="slip_id.currency_id"
    )
    batch_id = fields.Many2one(
        'openg2p.disbursement.batch',
        'Batch',
        store=True,
        ondelete='cascade',
        # related="slip_id.batch_id"
    )

    batch_id = fields.Many2one(
        'openg2p.disbursement.batch',
        string='Disbursement Batch',
        index=True,
        readonly=True,
        copy=False,
        states={'draft': [('readonly', False)]},
        required=True
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
        store=True,
        # related='advice_id.company_id'
    )
    receipt_confirmed = fields.Boolean(
        related="transaction_id.receipt_confirmed"
    )
    date_from = fields.Date(
        string='Date From',
        readonly=True,
        required=True,
        default=lambda self: fields.Date.to_string(
            date.today().replace(day=1)),
        states={'draft': [('readonly', False)]}
    )
    date_to = fields.Date(
        string='Date To',
        readonly=True,
        required=True,
        default=lambda self: fields.Date.to_string(
            (datetime.now() + relativedelta(months=+1, day=1, days=-1)).date()),
        states={'draft': [('readonly', False)]}
    )
    total = fields.Monetary(
        # compute='_compute_slip_stats',
        string='Net',
        store=True
    )
    program_id = fields.Many2one(
        'openg2p.program',
        string='Program',
        readonly=True,
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
