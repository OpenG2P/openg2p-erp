from datetime import datetime
from odoo import fields, models, api
import csv
import base64
import io
import uuid


class DisbursementFile(models.Model):
    _name = "openg2p.disbursement.file"

    batch_name = fields.Char(string="Batch Name", required=True)

    file = fields.Binary(string="CSV File", required=True)

    def create_batch(self):
        print("hello")
        return
        print(type(self.file), self.file)

        # with open(self.file,"rb") as f:
        #     print(f.read())
        csv_data = base64.b64decode(self.file)
        data_file = io.StringIO(csv_data.decode("utf-8"))
        # data_file.seek(0)
        file_reader = []
        csv_reader = csv.reader(data_file, delimiter=",")
        file_reader.extend(csv_reader)
        print(file_reader)

    def _get_bank_id(self, data=None):
        bank_id = self.env["res.partner.bank"].search(
            [("acc_number", "=", data["acc_number"])], limit=1
        )
        if len(bank_id) == 0:
            bank_id = self.env["res.partner.bank"].create(
                {
                    "acc_number": data["acc_number"],
                    "partner_id": self.env.ref("base.main_partner").id,
                    "payment_mode": data["payment_mode"],
                    "currency_id": self.env["res.currency"]
                    .search([("name", "=", data["currency"])])
                    .id,
                }
            )
        return bank_id

    @api.multi
    def create_batch(self, csv_data):
        # id,request_id,payment_mode,acc_number,acc_holder_name,amount,currency,note
        for program, beneficiaries in csv_data.items():
            request_id = uuid.uuid4().hex
            batch_size = 1000
            count = 0

            while len(beneficiaries[count:]) > 0:

                beneficiaries_list = beneficiaries[
                    count : min(count + batch_size, len(beneficiaries))
                ]

                # Creating batch
                batch = self.env["openg2p.disbursement.batch.transaction"].create(
                    {
                        "name": self.batch_name
                        + "-"
                        + str(datetime.now().strftime("%d%m%y-%I:%M")),
                        "program_id": program,
                        "state": "draft",
                        "date_start": datetime.now(),
                        "date_end": datetime.now(),
                        "request_id": request_id,
                    }
                )
                # id,request_id,payment_mode,acc_number,acc_holder_name,amount,currency,note
                for b in beneficiaries_list:

                    bank_id = self._get_bank_id(b)
                    m = self.env["openg2p.disbursement.main"].create(
                        {
                            "bank_account_id": bank_id.id,
                            "batch_id": batch.id,
                            "state": "draft",
                            "name": str(b.id),
                            "beneficiary_id": b.id,
                            "amount": 100.0,
                            "program_id": b.program_ids.ids[0],
                            "date_start": datetime.now(),
                            "date_end": datetime.now(),
                            "currency_id": bank_id.currency_id,
                            "payment_mode": bank_id.payment_mode,
                        }
                    )
                    m.generate_uuid()
                count += 1000
        return {"type": "ir.actions.act_window_close"}
