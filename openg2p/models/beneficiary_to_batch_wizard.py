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
        bank_id = self.env["res.partner.bank"].search(
            [("acc_number", "=", b.bank_account_number)]
        )
        return bank_id

    @api.multi
    def create_single(self):
        beneficiaries = self.env["openg2p.beneficiary"].browse(
            self.env.context.get("active_ids")
        )

        for b in beneficiaries:
            bank_id = self._get_bank_id(b)
            for program_id in b.program_ids.ids:

                single = self.env["openg2p.disbursement.single.transaction"].create(
                    {
                        "bank_account_id": bank_id[0].id,
                        "name": str(b.name),
                        "program_id": program_id,
                        "state": "draft",
                        "date_start": datetime.now(),
                        "date_end": datetime.now(),
                        "beneficiary_id": b.id,
                        "amount": b.grand_total,
                        "currency_id": 1,
                        "payment_mode": bank_id[0].payment_mode,
                    }
                )

        return {"type": "ir.actions.act_window_close"}

    @api.multi
    def create_batch(self):
        self.task_create_batch(self.env.context.get("active_ids"))
        return {"type": "ir.actions.act_window_close"}

    def task_create_batch(self, bene_ids):
        batch_ids = []
        beneficiaries_selected = self.env["openg2p.beneficiary"].browse(bene_ids)
        program_wise = {}
        for b in beneficiaries_selected:
            if not b.bank_account_number:
                continue
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
                        + str(datetime.now().strftime("%d-%m-%Y-%H:%M")),
                        "program_id": program,
                        "state": "draft",
                        "date_start": datetime.now(),
                        "date_end": datetime.now(),
                        "request_id": request_id,
                    }
                )
                batch_ids.append(batch.id)

                for b in beneficiaries_list:
                    bank_id = self._get_bank_id(b)

                    m = self.env["openg2p.disbursement.main"].create(
                        {
                            "bank_account_id": bank_id[0].id,
                            "batch_id": batch.id,
                            "state": "draft",
                            "name": str(b.name),
                            "beneficiary_id": b.id,
                            "amount": b.grand_total,
                            "program_id": b.program_ids.ids[0],
                            "date_start": datetime.now(),
                            "date_end": datetime.now(),
                            "currency_id": 1,
                            "payment_mode": bank_id[0].payment_mode,
                        }
                    )
                    m.generate_uuid()
                count += 1000
