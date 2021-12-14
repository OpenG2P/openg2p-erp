# -*- coding: utf-8 -*-
# Copyright 2020 OpenG2P (https://openg2p.org)
# @author: Salton Massally <saltonmassally@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import csv
import hashlib
import logging
import os
import uuid
from datetime import date, datetime
from io import StringIO

import boto3
import pandas as pd
import requests
from dateutil.relativedelta import relativedelta
from dotenv import load_dotenv  # for python-dotenv method

from odoo import api, fields, models

_logger = logging.getLogger(__name__)
BATCH_SIZE = 500

load_dotenv()  # for python-dotenv method


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
            ("paymentstatus", "Completed"),
        ],
        string="Status",
        readonly=True,
        default="draft",
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

    company_id = fields.Many2one(
        "res.company",
        "Company",
        required=False,
        readonly=True,
        ondelete="restrict",
        default=lambda self: self.env.user.company_id,
    )
    transaction_batch_id = fields.Char(readonly=True, string="Batch ID")

    request_id = fields.Char(string="Request ID", compute="_generate_uuid", store=True)

    transaction_status = fields.Char(
        readonly=True,
    )

    token_response = fields.Text(
        string="Token for transaction",
        required=False,
        default=None,
    )
    all_beneficiaries = fields.One2many(
        "openg2p.disbursement.main",
        string="Beneficiaries",
        compute="_all_beneficiaries",
    )
    total_disbursement_amount = fields.Float(
        string="Total Disbursement Amount",
        compute="_all_beneficiaries",
        default=0.0,
    )

    total_transactions = fields.Char(string="Total Transactions", readonly=True)

    ongoing = fields.Char(string="Ongoing", readonly=True)

    failed = fields.Char(string="Failed", readonly=True)

    total_amount = fields.Char(string="Total Amount Transacted", readonly=True)

    completed_amount = fields.Char(string="Completed Amount", readonly=True)

    ongoing_amount = fields.Char(string="Ongoing Amount", readonly=True)

    failed_amount = fields.Char(string="Failed Amount", readonly=True)

    def api_json(self):
        beneficiaries = self.env["openg2p.disbursement.main"].search(
            [("batch_id", "=", self.id)]
        )
        beneficiary_ids = [b.id for b in beneficiaries]
        return {
            "id": self.id,
            "name": self.name or "",
            "program": {
                "id": self.program_id.id,
                "name": self.program_id.name,
            },
            "state": self.state or "",
            "date_start": self.date_start or "",
            "date_end": self.date_end or "",
            "transaction_status": self.transaction_status or None,
            "transactions": {
                "total_transactions": self.total or None,
                "ongoing": self.successful or None,
                "failed": self.failed or None,
            },
            "beneficiary_ids": beneficiary_ids,
        }

    @api.multi
    def _all_beneficiaries(self):
        self.all_beneficiaries = self.env["openg2p.disbursement.main"].search(
            [("batch_id", "=", self.id)]
        )

        for b in self.all_beneficiaries:
            self.total_disbursement_amount += b.amount

    def action_confirm(self):
        for rec in self:
            rec.state = "confirm"
        self.env["openg2p.process"].handle_tasks(
            [("task_subtype_disbursement_approve_batch", self.id)]
        )

    def action_pending(self):
        for rec in self:
            rec.state = "pending"

    def action_transaction(self):
        for rec in self:
            rec.state = "paymentstatus"

    def _generate_uuid(self):
        for rec in self:
            if not rec.request_id:
                rec.request_id = uuid.uuid4().hex

    def create_bulk_transfer(self):
        self._generate_uuid()

        limit = 100
        beneficiary_transactions = self.env["openg2p.disbursement.main"].search(
            [("batch_id", "=", self.id)], limit=limit
        )

        offset = 0

        # CSV filename as RequestID+Datetime
        csvname = (
            self.request_id
            + "-"
            + str(datetime.now().strftime(r"%d-%m-%Y-%H:%M"))
            + ".csv"
        )

        while len(beneficiary_transactions) > 0:

            with open(csvname, "a") as csvfile:
                csvwriter = csv.writer(csvfile)
                entry = [
                    "id",
                    "request_id",
                    "payment_mode",
                    "amount",
                    "currency",
                    "note",
                ]
                csvwriter.writerow(entry)
                for rec in beneficiary_transactions:
                    entry = [
                        rec.id,
                        rec.beneficiary_request_id,
                        "gsma",  # rec.payment_mode or "gsma",
                        rec.amount,
                        "LE",  # rec.currency_id.name,
                        rec.note,
                    ]

                    # id,request_id,payment_mode,acc_number,acc_holder_name,amount,currency,note
                    csvwriter.writerow(entry)

            offset += len(beneficiary_transactions)

            if len(beneficiary_transactions) < limit:
                break
            beneficiary_transactions = self.env["openg2p.disbursement.main"].search(
                [("batch_id", "=", self.id)], limit=limit, offset=offset
            )

        url_token = "http://identity.ibank.financial/oauth/token"

        headers_token = {
            "Platform-TenantId": "ibank-usa",
            "Authorization": "Basic Y2xpZW50Og==",
            "Content-Type": "text/plain",
        }
        params_token = {
            "username": os.environ.get("username"),
            "password": os.environ.get("password"),
            "grant_type": os.environ.get("grant_type"),
        }

        try:
            response_token = requests.request(
                "POST", url_token, headers=headers_token, params=params_token
            )

            response_token_data = response_token.json()
            self.token_response = response_token_data["access_token"]

        except BaseException as e:
            print(e)

        # Uploading to AWS bucket
        uploaded = self.upload_to_aws(csvname, "paymenthub-ee-dev")

        headers = {"Platform-TenantId": "ibank-usa"}

        files = {
            "data": (csvname, open(csvname, "rb"), "text/csv"),
            "requestId": (None, str(self.request_id)),
            "note": (None, "Bulk transfers"),
            # "checksum": (None, str(self.generate_hash(csvname))),
        }

        url = "http://channel.ibank.financial/channel/bulk/transfer"

        try:
            response = requests.post(url, headers=headers, files=files)
            response_data = response.json()

            self.transaction_status = response_data["status"]
            self.transaction_batch_id = response_data["batch_id"]
            self.env["openg2p.process"].handle_tasks(
                [
                    ("task_subtype_disbursement_send_batch", self.id),
                    ("task_subtype_disbursement_review_settlement_report", self.id),
                    ("task_subtype_disbursement_complete_reconciliation", self.id),
                ]
            )
        except BaseException as e:
            print(e)

    # detailed
    def bulk_transfer_status(self):
        params = (("batchId", str(self.transaction_batch_id)),)

        headers = {
            "Platform-TenantId": "ibank-usa",
            "Authorization": "Bearer " + str(self.token_response),
        }

        url = "http://ops-bk.ibank.financial/api/v1/batch"

        try:
            response = requests.get(url, params=params, headers=headers)
            response_data = response.json()

            if response.status_code == 200:
                self.transaction_status = "completed"

                self.total_transactions = response_data["totalTransactions"]
                self.ongoing = response_data["ongoing"]
                self.failed = response_data["failed"]
                self.total_amount = response_data["total_amount"]
                self.completed_amount = response_data["completed_amount"]
                self.ongoing_amount = response_data["ongoing_amount"]
                self.failed_amount = response_data["failed_amount"]

        except BaseException as e:
            print(e)

    def upload_to_aws(self, local_file, bucket):

        try:
            hc = pd.read_csv(local_file)

            s3 = boto3.client(
                "s3",
                aws_access_key_id=os.environ.get("access_key"),
                aws_secret_access_key=os.environ.get("secret_access_key"),
            )
            csv_buf = StringIO()

            hc.to_csv(csv_buf, header=True, index=False)
            csv_buf.seek(0)

            s3.put_object(Bucket=bucket, Body=csv_buf.getvalue(), Key=local_file)

        except FileNotFoundError:
            print("File not found")

    def generate_hash(self, csvname):
        sha256 = hashlib.sha256()
        block_size = 256 * 128

        try:
            with open(csvname, "rb") as f:
                for chunk in iter(lambda: f.read(block_size), b""):
                    sha256.update(chunk)

            res = sha256.hexdigest()
            return res
        except BaseException as e:
            return e
