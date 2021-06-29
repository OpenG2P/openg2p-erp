# -*- coding: utf-8 -*-
from odoo import fields, models, api


class RegisterWizard(models.TransientModel):
    """
    A wizard to manage the creation/removal of register users.
    """

    _name = "beneficiary.create_batch.wizard"
    _description = "Create Disbursement Batch"

    name = fields.Char(
        required=True,
        string="Name of Batch",
        help="Name to be given to the created disbursment batch",
    )
    program_id = fields.Many2one(
        "openg2p.program",
        string="Program",
        required=True,
    )
    date_start = fields.Date(string="Date From", required=True)
    date_end = fields.Date(
        string="Date To",
        required=True,
    )
    use_active_domain = fields.Boolean("Use active domain")

    @api.multi
    def action_apply(self):
        beneficiary_obj = self.env["openg2p.beneficiary"]
        # TODO let us have a check here that makes sure the idividual is enrolled in the selected program .. also let's have it in the slip computatoion

        self.ensure_one()
        if self.use_active_domain:
            beneficiaries = beneficiary_obj.search(
                self.env.context.get("active_domain")
            )
        else:
            beneficiaries = beneficiary_obj.browse(self.env.context.get("active_ids"))

        batch = self.env["openg2p.disbursement.batch"].create(
            {
                "name": self.name,
                "program_id": self.program_id.id,
                "date_start": self.date_start,
                "date_end": self.date_end,
            }
        )

        batch.generate_run(beneficiaries=beneficiaries.ids, redo=False)

        return {
            "type": "ir.actions.act_window",
            "res_model": "openg2p.disbursement.batch",
            "views": [[False, "form"]],
            "res_id": batch.id,
            "context": {"create": False},
        }
