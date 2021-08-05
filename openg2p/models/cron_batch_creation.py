from odoo import fields, models, api
import uuid
from datetime import datetime


class CronBatchCreation(models.Model):
    _name = "openg2p.beneficiary.cron.batch.creation"

    def _get_bank_id(self, b):
        bank_id = self.env["res.partner.bank"].search(
            [("acc_number", "=", b.bank_account_number)]
        )
        return bank_id

    @api.multi
    def cron_create_batch(self):
        #Fetching all beneficiaries those are not under any batch
        all_beneficiaries = self.env['openg2p.beneficiary'].search([("batch_status","=",False)])

        if not all_beneficiaries:
            print("No beneficiaries for Batch Creation")
            return
        
        program_wise = {}
        for b in all_beneficiaries:
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
                        "name": str(datetime.now().strftime("%d%m%y-%I:%M:%S")),
                        "program_id": program,
                        "state": "draft",
                        "date_start": datetime.now(),
                        "date_end": datetime.now(),
                        "request_id": request_id,
                    }
                )

                for b in beneficiaries_list:
                    bank_id = self._get_bank_id(b)
                    m = self.env["openg2p.disbursement.main"].create(
                        {
                            "bank_account_id": bank_id[0].id,
                            "batch_id": batch.id,
                            "state": "draft",
                            "name": str(b.id),
                            "beneficiary_id": b.id,
                            "amount": 100.0,
                            "program_id": b.program_ids.ids[0],
                            "date_start": datetime.now(),
                            "date_end": datetime.now(),
                            "currency_id": 1,
                            "payment_mode": bank_id[0].payment_mode,
                        }
                    )
                    m.generate_uuid()
                count += 1000
        
        #Changing batch status of records true
        for record in all_beneficiaries:
            record.batch_status=True