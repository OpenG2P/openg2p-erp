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

from odoo import fields, models

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
        required=True,
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

    total = fields.Char(string="Total", readonly=True)

    successful = fields.Char(string="Successful", readonly=True)

    failed = fields.Char(string="Failed", readonly=True)

    def action_confirm(self):
        for rec in self:
            rec.state = "confirm"

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
            + str(datetime.now().strftime(r"%Y%m%d%H%M%S"))
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

        # return

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

        response_token = requests.request(
            "POST", url_token, headers=headers_token, params=params_token
        )

        response_token_data = response_token.json()
        self.token_response = response_token_data["access_token"]

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

        except BaseException as e:
            print(e)

    def bulk_transfer_status(self):
        params = (("batchId", str(self.transaction_batch_id)),)

        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:90.0) Gecko/20100101 Firefox/90.0",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.5",
            "Platform-TenantId": "ibank-usa",
            "Authorization": "Bearer " + str(self.token_response),
            "Connection": "keep-alive",
        }

        url = "http://ops-bk.ibank.financial/api/v1/batch"

        try:
            response = requests.get(url, params=params, headers=headers)
            response_data = response.json()

            if response.status_code == 200:
                self.transaction_status = "completed"

                self.total = response_data["totalTransactions"]
                self.successful = response_data["ongoing"]
                self.failed = response_data["failed"]

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
