from odoo import fields, models, api
import uuid
from datetime import datetime
from odoo.exceptions import ValidationError, UserError


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
                        "currency_id": bank_id[0].currency_id,
                        "payment_mode": bank_id[0].payment_mode,
                    }
                )

        return {"type": "ir.actions.act_window_close"}

    @api.multi
    def create_batch(self):

        self.task_create_batch(self.batch_name, self.env.context.get("active_ids"))
        return {"type": "ir.actions.act_window_close"}

    def task_create_batch(self, batch_name, beneficiary_ids):
        beneficiaries_selected = self.env["openg2p.beneficiary"].browse(beneficiary_ids)
        batch_ids = []
        batch_wise = {}

        for b in beneficiaries_selected:

            if not b.bank_account_number:
                raise ValidationError(
                    "One or more beneficiaries do not have bank account details"
                )

            # if b.batch_status:
            #     raise ValidationError("Beneficiary already under a batch")

            # Storing according to batch ID's
            # batch_wise={
            #     'batchid1':
            #         'programid':[b1,b2,b3.....]
            # }

            batch_id = b.odk_batch_id

            if batch_id in batch_wise.keys():
                program_wise = batch_wise[batch_id]
                for program_id in b.program_ids.ids:
                    if program_id in program_wise.keys():
                        program_wise[program_id].append(b)
                    else:
                        program_wise[program_id] = [b]
            else:
                batch_wise[batch_id] = {
                    program_id: [b] for program_id in b.program_ids.ids
                }

        for batch_id in batch_wise:
            request_id = batch_id

            beneficiaries_list = []

            for program_id in batch_wise[batch_id]:
                beneficiaries_list = batch_wise[batch_id][program_id]

                # Creating batch
                batch = self.env["openg2p.disbursement.batch.transaction"].create(
                    {
                        "name": batch_name
                        + "-"
                        + str(datetime.now().strftime("%d-%m-%Y-%H:%M")),
                        "program_id": program_id,
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
                            "currency_id": bank_id[0].currency_id.id,
                            "payment_mode": bank_id[0].payment_mode,
                        }
                    )
                    m.generate_uuid()

        # Changing batch status of records true
        # for beneficiary in beneficiaries_selected:
        #     beneficiary.batch_status = True
        return batch_ids
