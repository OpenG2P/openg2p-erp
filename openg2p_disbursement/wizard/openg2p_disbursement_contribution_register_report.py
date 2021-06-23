# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class SlipLinesContributionRegister(models.TransientModel):
    _name = "slip.lines.contribution.register"
    _description = "Disbursement Slip Lines by Contribution Registers"

    batch_id = fields.Many2one(
        "openg2p.disbursement.batch", string="Disbursement Batch"
    )

    @api.multi
    def print_report(self):
        active_ids = self.env.context.get("active_ids", [])
        datas = {
            "ids": active_ids,
            "model": "openg2p.disbursement.contribution.register",
            "form": self.read()[0],
        }
        return self.env.ref(
            "openg2p_disbursement.action_contribution_register"
        ).report_action([], data=datas)
