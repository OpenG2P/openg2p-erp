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
import boto3
import pandas as pd
from io import StringIO
import os
from dotenv import load_dotenv

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

            with open(csvname, "w", newline="", encoding="utf-8") as csvfile:
                csvwriter = csv.writer(csvfile)
                for rec in beneficiary_transactions:
                    # id,request_id,payment_mode,acc_number,acc_holder_name,amount,currency,note
                    entry = [
                        rec.id,
                        rec.beneficiary_request_id,
                        rec.payment_mode,
                        rec.name,
                        rec.acc_holder_name,
                        rec.amount,
                        rec.currency_id.name,
                    ]

                    csvwriter.writerow(entry)

            offset += len(beneficiary_transactions)

            if len(beneficiary_transactions) < limit:
                break
            beneficiary_transactions = self.env["openg2p.disbursement.main"].search(
                [("batch_id", "=", self.id)], limit=limit, offset=offset
            )

        # Uploading to AWS bucket
        uploaded = self.upload_to_aws(csvname, "openg2p-dev")

        headers = {
            # "Content-Type": "multipart/form-data",
        }
        files = {
            "data": (csvname, open(csvname, "rb")),
            "note": (None, "Bulk transfers"),
            "checksum": (None, str(self.generate_hash(csvname))),
            "request_id": (None, str(self.request_id)),
        }

        url = "http://15.207.23.72:5000/channel/bulk/transfer"

        try:
            response = requests.post(url, headers=headers, files=files)

            response_data = response.json()

            self.transaction_status = response_data["status"]

            self.transaction_batch_id = response_data["batch_id"]
        except BaseException as e:
            return e

    def bulk_transfer_status(self):
        params = (
            ("batch_id", str(self.transaction_batch_id)),
            ("detailed", "true"),
        )

        url = "http://15.207.23.72:5000/channel/bulk/transfer"

        try:
            response = requests.get(url, params=params)
            response_data = response.json()

            self.transaction_status = response_data["status"]

            self.total = response_data["total"]

            self.successful = response_data["successful"]

            self.failed = response_data["failed"]

        except BaseException as e:
            return e

    def upload_to_aws(self, local_file, bucket):

        try:
            load_dotenv("F:\odoo12\odoo\openg2p-erp\.env")
            hc = pd.read_csv(local_file)

            s3 = boto3.client(
                "s3",
                aws_access_key_id=os.getenv("ACCESS_KEY"),
                aws_secret_access_key=os.getenv("SECRET_KEY"),
            )
            csv_buf = StringIO()

            hc.to_csv(csv_buf, header=True, index=False)
            csv_buf.seek(0)

            s3.put_object(Bucket=bucket, Body=csv_buf.getvalue(), Key=local_file)

        except FileNotFoundError:
            return False

    def all_transactions_status(self):
        try:
            response = requests.get("https://15.207.23.72:5000/channel/transfer")
            return response
        except BaseException as e:
            return e

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
