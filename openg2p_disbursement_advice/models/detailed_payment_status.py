import os
from urllib.parse import urlparse
from dotenv import load_dotenv  # for python-dotenv method
import boto3
import requests

from odoo import fields, models

load_dotenv()  # for python-dotenv method


class BeneficiaryTransactionWizard(models.TransientModel):
    _name = "openg2p.disbursement.batch.transaction.wizard"

    result_file = fields.Char(string="CSV File", readonly=True)

    def bulk_transfer_detailed_status(self):
        batch = self.env["openg2p.disbursement.batch.transaction"].browse(
            self.env.context.get("active_ids")
        )

        params = (("batch_id", str(batch.transaction_batch_id)),)

        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:90.0) Gecko/20100101 Firefox/90.0",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.5",
            "Platform-TenantId": "ibank-usa",
            "Authorization": "Bearer " + str(batch.token_response),
            "Connection": "keep-alive",
        }

        url = "http://ops-bk.ibank.financial/api/v1/batch"

        try:
            response = requests.get(url, params=params, headers=headers)

            response_data = response.json()

            self.result_file = response_data["requestFile"]

            s3 = boto3.resource(
                "s3",
                aws_access_key_id=os.environ.get("access_key"),
                aws_secret_access_key=os.environ.get("secret_access_key"),
            )

            s3.Bucket("paymenthub-ee-dev").download_file(
                self.result_file, self.result_file
            )

        except BaseException as e:
            print(e)

        return {
            "type": "ir.actions.do_nothing",
        }
