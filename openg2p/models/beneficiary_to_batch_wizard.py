from odoo import fields, models, api
import uuid
from datetime import datetime


class BeneficiaryTransactionWizard(models.TransientModel):
    _name = "openg2p.beneficiary.transaction.wizard"

    batch_name = fields.Char(
        string="Batch Name",
        store=True,
    )

    def _get_bank_id(self, b):
        bank_id = self.env["res.partner.bank"].search([("beneficiary_id", "=", b.id)])
        return bank_id

    @api.multi
    def create_single(self):
        beneficiaries = self.env["openg2p.beneficiary"].browse(
            self.env.context.get("active_ids")
        )
        # print(beneficiaries)
        for b in beneficiaries:
            bank_id = self._get_bank_id(b)
            single = self.env["openg2p.disbursement.single.transaction"].create(
                {
                    "bank_account_id": bank_id[0].id,
                    "name": str(b.id),
                    "program_id": b.program_ids.ids[0],
                    "state": "draft",
                    "date_start": datetime.now(),
                    "date_end": datetime.now(),
                    "beneficiary_id": b.id,
                    "amount": 100.0,
                    "currency_id": 1,
                    "payment_mode": bank_id[0].payment_mode,
                }
            )
            # single.create_single_transfer()
        return {"type": "ir.actions.act_window_close"}

    @api.multi
    def create_batch(self):
        beneficiaries_selected = self.env["openg2p.beneficiary"].browse(
            self.env.context.get("active_ids")
        )
        program_wise = {}
        for b in beneficiaries_selected:
            if b.program_ids[0] in program_wise.keys():
                program_wise[b.program_ids[0]].append(b)
            else:
                program_wise[b.program_ids[0]] = [b]

        # print(program_wise)

        for program, beneficiaries in program_wise.items():
            batch_id = uuid.uuid4().hex
            batch_size = 1000
            count = 0
            # lbs = len(beneficiaries)
            while len(beneficiaries[count:]) > 0:

                beneficiaries_list = beneficiaries[
                    count : min(count + batch_size, len(beneficiaries))
                ]

                # print("Hello")
                # print(program.id)
                # Creating batch
                batch = self.env["openg2p.disbursement.batch.transaction"].create(
                    {
                        "name": self.batch_name
                        + "-"
                        + str(datetime.now().strftime("%d%m%y-%I:%M")),
                        "program_id": program.id,
                        "state": "draft",
                        "date_start": datetime.now(),
                        "date_end": datetime.now(),
                        "request_id": batch_id,
                    }
                )

                print(batch)
                print("Batch Created")
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
                # batch.create_bulk_transfer()
                count += 1000
        return {"type": "ir.actions.act_window_close"}
