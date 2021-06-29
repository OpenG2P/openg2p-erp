# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class HrSlipBeneficiaries(models.TransientModel):
    _name = "openg2p.disbursement.slip.beneficiaries"
    _description = "Generate slips for all selected beneficiaries"

    @api.multi
    def _add_program_domain(self):
        active_id = self.env.context.get("active_id")
        batch = self.env["openg2p.disbursement.batch"].browse(active_id)
        beneficiaries = (
            self.env["openg2p.disbursement.batch"]
            .browse(active_id)
            .default_run_beneficiaries()
        )
        return [
            (
                "id",
                "in",
                list(
                    set(beneficiaries) - set(batch.slip_ids.mapped("beneficiary_id.id"))
                ),
            )
        ]

    beneficiary_ids = fields.Many2many(
        "openg2p.beneficiary",
        "openg2p_beneficiary_group_rel",
        "slip_id",
        "beneficiary_id",
        "Beneficiaries",
        #   domain=_add_program_domain
    )

    @api.multi
    def compute_sheet(self):
        self.ensure_one()
        active_id = self.env.context.get("active_id")
        res = (
            self.env["openg2p.disbursement.batch"]
            .browse(active_id)
            .generate_run(beneficiaries=self.beneficiary_ids.ids, redo=True)
        )
        if isinstance(res, dict):
            return res
        else:
            return {"type": "ir.actions.act_window_close"}
