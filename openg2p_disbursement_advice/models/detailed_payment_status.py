from odoo import fields, models, api
import uuid
import requests
import json
from datetime import datetime
import os
from urllib.parse import urlparse
from . import secret_keys
import boto3


class BeneficiaryTransactionWizard(models.TransientModel):
    _name = "openg2p.disbursement.batch.transaction.wizard"

    file_url = fields.Char(
        string="CSV Link", readonly=True, compute="bulk_transfer_detailed_status"
    )
    csv_data = fields.Text(string="CSV Data", readonly=True)

    def bulk_transfer_detailed_status(self):
        batch = self.env["openg2p.disbursement.batch.transaction"].browse(
            self.env.context.get("active_ids")
        )
        params = (
            ("batch_id", str(batch.transaction_batch_id)),
            ("detailed", "true"),
        )

        url = "http://15.207.23.72:5000/channel/bulk/transfer"

        try:
            response = requests.get(url, params=params)

            response_data = response.json()

            print(response_data)
            self.file_url = response_data["file"]

            url = self.file_url
            a = urlparse(url)

            file_name = os.path.basename(a.path)

            s3 = boto3.resource(
                "s3",
                aws_access_key_id=secret_keys.ACCESS_KEY,
                aws_secret_access_key=secret_keys.SECRET_KEY,
            )

            s3.Bucket("openg2p-dev").download_file(file_name, file_name)
            # print("Download Successful!")
            # file_data = ""

            # with open(file_name) as f:
            #     file_data += "".join(f.readlines())

            # print(file_data)

            # self.csv_data = file_data

        except BaseException as e:
            print(e)

        return {
            "type": "ir.actions.do_nothing",
        }
