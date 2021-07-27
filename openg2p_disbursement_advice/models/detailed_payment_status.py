import os
from urllib.parse import urlparse
from dotenv import load_dotenv  # for python-dotenv method
import boto3
import requests

from odoo import fields, models

load_dotenv()  # for python-dotenv method


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

        url_mock = "http://15.207.23.72:5000/channel/bulk/transfer"
        url_real = "http://892c546a-us-east.lb.appdomain.cloud/channel/bulk/transfer"

        try:
            response_mock = requests.get(url_mock, params=params)
            response_real = requests.get(url_real, params=params)

            response_mock_data = response_mock.json()

            print(response_mock_data)
            self.file_url = response_mock_data["file"]

            url_mock = self.file_url
            a = urlparse(url_mock)

            file_name = os.path.basename(a.path)

            s3 = boto3.resource(
                "s3",
                aws_access_key_id=os.environ.get(
                    "access_key"
                ),  # secret_keys.ACCESS_KEY,
                aws_secret_access_key=os.environ.get(
                    "secret_access_key"
                ),  # secret_keys.SECRET_KEY,
            )

            s3.Bucket("openg2p-dev").download_file(file_name, file_name)

        except BaseException as e:
            print(e)

        return {
            "type": "ir.actions.do_nothing",
        }
