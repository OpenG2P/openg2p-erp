# -*- coding: utf-8 -*-
# Copyright 2020 OpenG2P (https://openg2p.org)
# @author: Salton Massally <saltonmassally@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import json
import requests
import logging
import hashlib
import uuid
import csv
from datetime import date, datetime

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.addons.queue_job.job import job, related_action
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)
BATCH_SIZE = 500


class BatchTransaction(models.Model):
    _name = "openg2p.disbursement.batch.transaction"
    _description = "Disbursement Batch"
    _inherit = ["generic.mixin.no.unlink", "mail.thread", "openg2p.mixin.has_document"]
    allow_unlink_domain = [("state", "=", "draft")]

    name = fields.Char(
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
        track_visibility="onchange",
    )
    program_id = fields.Many2one(
        "openg2p.program",
        required=True,
        readonly=True,
        index=True,
        states={"draft": [("readonly", False)]},
        track_visibility="onchange",
    )
    state = fields.Selection(
        [
            ("draft", "Drafting"),
            ("confirm", "Confirmed"),
            ("pending", "Pending"),
            ("paymentstatus", "Transaction Status"),
        ],
        string="Status",
        index=True,
        readonly=True,
        copy=False,
        default="draft",
        track_visibility="onchange",
    )
    date_start = fields.Date(
        string="Date From",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
        default=lambda self: fields.Date.to_string(date.today().replace(day=1)),
        track_visibility="onchange",
    )
    date_end = fields.Date(
        string="Date To",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
        default=lambda self: fields.Date.to_string(
            (datetime.now() + relativedelta(months=+1, day=1, days=-1)).date()
        ),
        track_visibility="onchange",
    )
    company_id = fields.Many2one(
        "res.company",
        "Company",
        required=True,
        readonly=True,
        ondelete="restrict",
        default=lambda self: self.env.user.company_id,
    )
    request_id = fields.Char(string="UUID", compute="_generate_uuid", store=True)
    transaction_status = fields.Char(
        readonly=True,
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

    def create_bulk_transfer(self):
        self._generate_uuid()

        # import os
        # if os.path.exists('accounts.csv'):
        #     os.remove('accounts.csv')

        limit = 100
        beneficiary_transactions = self.env["openg2p.disbursement.main"].search(
            [("batch_id", "=", self.id)], limit=limit
        )

        offset = 0
        while len(beneficiary_transactions) > 0:

            with open("accounts.csv", "a") as csvfile:
                csvwriter = csv.writer(csvfile)
                for rec in beneficiary_transactions:
                    entry = [
                        rec.acc_holder_name,
                        rec.name,
                        rec.amount,
                        rec.currency_id.name,
                        rec.payment_mode,
                    ]
                    # print(entry)
                    beneficiary_transaction_records = []
                    beneficiary_transaction_records.append(entry)
                    csvwriter.writerows(
                        map(lambda x: [x], beneficiary_transaction_records)
                    )

            offset += len(beneficiary_transactions)

            if len(beneficiary_transactions) < limit:
                break
            beneficiary_transactions = self.env["openg2p.disbursement.main"].search(
                [("batch_id", "=", self.id)], limit=limit, offset=offset
            )

        headers = {
            "Content-Type": "multipart/form-data",
        }

        files = {
            "data": ("accounts.csv", open("accounts.csv", "rb")),
            "note": (None, "Bulk transfers"),
            "checksum": (None, str(self.generate_hash())),
            "request_id": (None, str(self.request_id)),
        }
        print(self.request_id)
        url = "http://15.207.23.72:5000/channel/bulk/transfer"

        try:
            response = requests.post(url, headers=headers, files=files)
            self.transaction_status = response.json().get("status")
            print(response.text)
        except requests.exceptions.RequestException as e:
            print(e)

    def bulk_transfer_status(self):
        params = (("request_id", str(self.request_id)),)

        url = "http://15.207.23.72:5000/channel/bulk/transfer"

        try:
            response = requests.get(url, params=params)
            print(response.text)
            self.transaction_status = response.json()[0]["status"]
            return response
        except requests.exceptions.RequestException as e:
            print(e)

    def all_transactions_status(self):
        try:
            response = requests.get("https://15.207.23.72:5000/channel/transfer")
            return response
        except BaseException as e:
            print(e)

    def generate_hash(self):
        sha256 = hashlib.sha256()
        block_size = 256 * 128

        try:
            with open("accounts.csv", "rb") as f:
                for chunk in iter(lambda: f.read(block_size), b""):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except BaseException as e:
            print(e)

    def _generate_uuid(self):
        for rec in self:
            if not rec.request_id:
                rec.request_id = uuid.uuid4().hex
