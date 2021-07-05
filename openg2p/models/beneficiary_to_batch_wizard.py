from odoo import fields, models, api
import uuid
from datetime import datetime


class BeneficiaryTransactionWizard(models.TransientModel):
    _name = "openg2p.beneficiary.transaction.wizard"

    def _beneficiary_data(self, b):
        bank_id = self.env["res.partner.bank"].search([("beneficiary_id", "=", b.id)])
        return bank_id

    @api.multi
    def create_single(self):
        beneficiaries = self.env["openg2p.beneficiary"].browse(
            self.env.context.get("active_ids")
        )
        # print(beneficiaries)
        for b in beneficiaries:
            bank_id = self._beneficiary_data(b)
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
                    "currency_id": 0,
                    "payment_mode": bank_id[0].payment_mode,
                }
            )
            # single.create_single_transfer()
        return {"type": "ir.actions.act_window_close"}

    @api.multi
    def create_batch(self):
        beneficiaries = self.env["openg2p.beneficiary"].browse(
            self.env.context.get("active_ids")
        )
        program_wise = {}
        for b in beneficiaries:
            if b.program_ids[0] in program_wise.keys():
                program_wise[b.program_ids[0]].append(b)
            else:
                program_wise[b.program_ids[0]] = [b]

        print(program_wise)

        for p, bs in program_wise.items():
            batch_id = uuid.uuid4().hex
            batch_size = 1000
            c = 0
            # lbs = len(bs)
            while len(bs[c:]) > 0:

                bt = bs[c : min(c + batch_size, len(bs))]

                print("Hello")
                print(p.id)
                # Creating batch
                batch = self.env["openg2p.disbursement.batch.transaction"].create(
                    {
                        "name": str(p.id) + str(datetime.now()),
                        "program_id": p.id,
                        "state": "draft",
                        "date_start": datetime.now(),
                        "date_end": datetime.now(),
                        "request_id": batch_id,
                    }
                )

                print(batch)
                print("Batch Created")
                for b in bt:
                    bank_id = self._beneficiary_data(b)
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
                            "currency_id": 0,
                            "payment_mode": bank_id[0].payment_mode,
                        }
                    )
                # batch.create_bulk_transfer()
                c += 1000
        return {"type": "ir.actions.act_window_close"}
