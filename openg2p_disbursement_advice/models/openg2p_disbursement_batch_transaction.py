# -*- coding: utf-8 -*-
# Copyright 2020 OpenG2P (https://openg2p.org)
# @author: Salton Massally <saltonmassally@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import json
import requests
import logging
import hashlib
import uuid
from datetime import date, datetime

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.addons.queue_job.job import job, related_action
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)
BATCH_SIZE = 500


class BatchTransaction(models.Model):
    _name = 'openg2p.disbursement.batch.transaction'
    _description = 'Disbursement Batch'
    _inherit = ['generic.mixin.no.unlink',
                'mail.thread', 'openg2p.mixin.has_document']
    allow_unlink_domain = [('state', '=', 'draft')]

    name = fields.Char(
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
        track_visibility='onchange'
    )
    program_id = fields.Many2one(
        'openg2p.program',
        required=True,
        readonly=True,
        index=True,
        states={'draft': [('readonly', False)]},
        track_visibility='onchange'
    )
    state = fields.Selection(
        [
            ('draft', 'Drafting'),
            ('confirm', 'Confirmed'),
            ('pending', 'Pending'),
            ('paymentstatus', 'Transaction Status')
        ],
        string='Status',
        # index=True,
        readonly=True,
        # copy=False,
        default='draft',
        # track_visibility='onchange'
    )
    date_start = fields.Date(
        string='Date From',
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
        default=lambda self: fields.Date.to_string(
            date.today().replace(day=1)),
        track_visibility='onchange'
    )
    date_end = fields.Date(
        string='Date To',
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
        default=lambda self: fields.Date.to_string(
            (datetime.now() + relativedelta(months=+1, day=1, days=-1)).date()),
        track_visibility='onchange'
    )
    company_id = fields.Many2one(
        'res.company',
        'Company',
        required=True,
        readonly=True,
        ondelete='restrict',
        default=lambda self: self.env.user.company_id
    )
    currency_id = fields.Many2one(
        string="Currency",
        related='company_id.currency_id',
        readonly=True,
        store=True
    )

    def action_confirm(self):
        self.create_bulk_transfer()
        for rec in self:
            rec.state = 'confirm'

    def action_pending(self):
        for rec in self:
            rec.state = 'pending'

    def action_transaction(self):
        for rec in self:
            rec.state = 'paymentstatus'

    def create_bulk_transfer(self):
        query = """SELECT p.acc_holder_name,p.name,p.amount,p.currency_id, p.payment_mode
                        FROM public.openg2p_disbursement_main AS p    
                        ON p.batch_id=c.id  
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
            'https://ph.ee/channel/self.name/bulk/transfer', headers=headers, files=files)

    def bulk_transfer_status(self, val):
        params = (('bulk_id', val),)

        response = requests.get(
            'https://ph.ee/channel/self.name/bulk/transfer', params=params)
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
