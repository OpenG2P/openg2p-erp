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
    _inherit = ["mail.thread", "openg2p.mixin.has_document"]
    allow_unlink_domain = [("state", "=", "draft")]

    name = fields.Char(
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
        tracking=True,
    )
    program_id = fields.Many2one(
        "openg2p.program",
        required=True,
        readonly=True,
        index=True,
        states={"draft": [("readonly", False)]},
        tracking=True,
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

    company_id = fields.Many2one(
        "res.company",
        "Company",
        required=False,
        readonly=True,
        ondelete="restrict",
        default=lambda self: self.env.company,
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

    ongoing = fields.Char(string="Reconcile", readonly=True)

    failed = fields.Char(string="Failed", readonly=True)

    total_amount = fields.Char(string="Total Amount Transacted", readonly=True)

    completed_amount = fields.Char(string="Completed Amount", readonly=True)

    ongoing_amount = fields.Char(string="Pending Amount", readonly=True)

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

    def _all_beneficiaries(self):
        self.all_beneficiaries = self.env["openg2p.disbursement.main"].search(
            [("batch_id", "=", self.id)]
        )

        for b in self.all_beneficiaries:
            self.total_disbursement_amount += b.amount

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
                    "account_number",
                    "amount",
                    "currency",
                    "note",
                ]
                csvwriter.writerow(entry)
                for rec in beneficiary_transactions:
                    entry = [
                        rec.id,
                        rec.beneficiary_request_id,
                        rec.payment_mode or "slcb",
                        rec.bank_account_id.acc_number,
                        rec.amount,
                        rec.currency_id.name or "LE",
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

        # Uploading to AWS bucket
        uploaded = self.upload_to_aws(csvname, os.environ.get("bucketName"))
        _logger.info("Bucket name : {}".format(os.environ.get("bucketName")))

        # bulk transfer
        url = os.environ.get("bulkTransferUrl")

        params = {
            "type": "csv",
        }
        files = {
            "data": open(csvname, "rb"),
        }
        headers = {
            "Purpose": "test payment",
            "filename": csvname,
            "X-CorrelationID": str(self.request_id),
            "Platform-TenantId": os.environ.get("tenantName"),
        }
        try:
            response = requests.request(
                "POST", url, headers=headers, files=files, params=params, verify=False
            )
            response_data = response.json()

            self.transaction_status = response_data["status"]
            self.transaction_batch_id = response_data["batch_id"]
        except BaseException as e:
            _logger.exception(e)

    def get_auth_token(self):
        try:
            headers = {
                "Platform-TenantId": os.environ.get("tenantName"),
                "Authorization": os.environ.get("authHeader"),
                "Content-Type": "text/plain",
            }
            params = {
                "username": os.environ.get("username"),
                "password": os.environ.get("password"),
                "grant_type": os.environ.get("grant_type"),
            }
            response = requests.post(
                os.environ.get("authUrl"),
                params=params,
                headers=headers,
                verify=False,
            )
            response_data = response.json()
            return response_data["access_token"]
        except BaseException as e:
            _logger.exception(e)

    # detailed
    def bulk_transfer_status(self):
        self.token_response = self.get_auth_token()
        params = {
            "batchId": str(self.transaction_batch_id),
        }
        headers = {
            "Platform-TenantId": os.environ.get("tenantName"),
            "Authorization": "Bearer " + str(self.token_response),
        }

        url = os.environ.get("bulkTransferStatusUrl")

        try:
            response = requests.get(url, params=params, headers=headers, verify=False)
            response_data = response.json()

            if response.status_code == 200:
                self.transaction_status = "completed"

                self.total_transactions = response_data["total"]
                self.ongoing = response_data["ongoing"]
                self.failed = response_data["failed"]
                self.total_amount = response_data["totalAmount"]
                self.completed_amount = response_data["successfulAmount"]
                self.ongoing_amount = response_data["pendingAmount"]
                self.failed_amount = response_data["failedAmount"]

        except BaseException as e:
            _logger.exception(e)

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
            _logger.error("File not found")

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
