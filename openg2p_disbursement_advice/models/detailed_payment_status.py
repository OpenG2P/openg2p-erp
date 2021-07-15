from odoo import fields, models, api
import uuid
import requests
import json
from datetime import datetime


class BeneficiaryTransactionWizard(models.TransientModel):
    _name = "openg2p.disbursement.batch.transaction.wizard"

    file_url = fields.Char(
        string="CSV Link", readonly=True, compute="bulk_transfer_detailed_status"
    )

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
            print(response_data["file"])

            self.file_url = response_data["file"]
            print(self.file_url)
        except BaseException as e:
            print(e)

        return {
            "type": "ir.actions.do_nothing",
        }
