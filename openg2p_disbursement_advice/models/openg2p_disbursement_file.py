from datetime import datetime
from odoo import fields, models, api
import csv
import base64
import io
import uuid
import pandas as pd


class DisbursementFile(models.Model):
    _name = "openg2p.disbursement.file"

    batch_name = fields.Char(string="Batch Name", required=True)

    file = fields.Binary(string="CSV File", required=True)

    @api.multi
    def parse_csv(self):
        # id,firstname,lastname,program,location,street,gender,city,state,country,acc_number,amount,payment_mode,currency
        csv_data = base64.b64decode(self.file)
        data_file = io.StringIO(csv_data.decode("utf-8"))

        df = pd.read_csv(data_file, delimiter=",", header=None)
        df = pd.DataFrame(
            df.values,
            columns=[
                "ID",
                "firstname",
                "lastname",
                "program",
                "location",
                "street",
                "gender",
                "city",
                "state",
                "country",
                "acc_number",
                "amount",
                "payment_mode",
                "currency",
            ],
        )

        beneficiary_list = []
        # Creating beneficiaries
        for index, b in df.iterrows():

            # Checking country
            country_id = (
                self.env["res.country"].search([("name", "=", str(b["country"]))]).id
            )
            if not country_id:
                country_id = self.env["res.country"].create({"name": b["country"]}).id

            # Checking state
            state_id = (
                self.env["res.country.state"]
                .search([("name", "=", str(b["state"]))])
                .id
            )
            if not state_id:
                state_id = self.env["res.country.state"].create({"name": b["state"]}).id

            # Checking location
            location_id = (
                self.env["openg2p.location"]
                .search([("name", "=", str(b["location"]))])
                .id
            )
            if not location_id:
                location_id = (
                    self.env["openg2p.location"].create({"name": b["location"]}).id
                )

            # Checking program
            program_id = (
                self.env["openg2p.program"]
                .search([("name", "=", str(b["program"]))])
                .id
            )
            if not program_id:
                program_id = (
                    self.env["openg2p.program"].create({"name": b["program"]}).id
                )

            bank_id, existing = self._get_bank_id(b)
            if not existing:
                beneficiary = self.env["openg2p.beneficiary"].create(
                    {
                        "firstname": b["firstname"],
                        "lastname": b["lastname"],
                        "location_id": location_id,
                        "street": b["street"],
                        "gender": b["gender"],
                        "city": b["city"],
                        "state_id": state_id,
                        "country_id": country_id,
                        "bank_account_id": bank_id.id,
                    }
                )

            else:
                beneficiary = self.env["openg2p.beneficiary"].search(
                    [("bank_account_id", "=", bank_id.id)]
                )
            beneficiary.write({"program_ids": [(4, program_id)]})
            beneficiary_list.append(beneficiary)
        self.create_batch_transaction(beneficiary_list)

    @api.multi
    def _get_bank_id(self, data=None):
        if isinstance(data, pd.core.series.Series):
            bank_id = self.env["res.partner.bank"].search(
                [("acc_number", "=", str(data["acc_number"]))], limit=1
            )
        else:
            bank_id = self.env["res.partner.bank"].search(
                [("acc_number", "=", data.bank_account_id.acc_number)], limit=1
            )

        if len(bank_id) == 0:
            bank_id = self.env["res.partner.bank"].create(
                {
                    "acc_holder_name": str(data["firstname"] + " " + data["lastname"]),
                    "acc_number": str(data["acc_number"]),
                    "partner_id": self.env.ref("base.main_partner").id,
                    "payment_mode": data["payment_mode"],
                    "currency_id": self.env["res.currency"]
                    .search([("name", "=", data["currency"])])
                    .id,
                }
            )
            return bank_id, False
        else:
            return bank_id, True

    @api.multi
    def create_batch_transaction(self, beneficiaries_selected):
        # id,firstname,lastname,program,location,street,gender,city,state,country,acc_number,amount,payment_mode,currency
        program_wise = {}
        for b in beneficiaries_selected:
            print(b.program_ids.ids)
            for program_id in b.program_ids.ids:
                if program_id in program_wise.keys():
                    program_wise[program_id].append(b)
                else:
                    program_wise[program_id] = [b]

        for program, beneficiaries in program_wise.items():
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
                    bank_id, existing = self._get_bank_id(b)
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
                            "currency_id": 1,
                            "payment_mode": bank_id.payment_mode,
                        }
                    )
                    m.generate_uuid()
                count += 1000
        return {"type": "ir.actions.act_window_close"}
