# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class PrintBatchContribRegister(models.TransientModel):
    _name = "print.batch.contrib_register"
    _description = "Print Contribution Register"

    register_ids = fields.Many2many(
        "openg2p.disbursement.contribution.register",
        "print_batch_beneficiary_rel",
        "print_batch_id",
        "beneficiary_id",
        string="Contribution Registers",
    )

    @api.multi
    def print_contrib_register(self):
        self.ensure_one()
        batch_id = self.env.context["active_id"]
        batch = self.env["openg2p.disbursement.batch"].browse(batch_id)

        if not batch.state_approved():
            raise ValidationError(
                _("Batch has tp be approved before registers can be printed")
            )

        datas = {
            "model": "openg2p.disbursement.contribution.register",
            "ids": self.register_ids.ids,
            "form": {
                "date_from": batch.date_start,
                "date_to": batch.date_end,
                "batch_id": batch.id,
            },
        }
        return self.env.ref(
            "openg2p_disbursement.action_contribution_register"
        ).report_action(self.register_ids, data=datas)
