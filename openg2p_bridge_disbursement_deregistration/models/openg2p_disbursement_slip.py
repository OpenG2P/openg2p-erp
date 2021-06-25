# -*- coding: utf-8 -*-
# Copyright 2020 OpenG2P (https://openg2p.org)
# @author: Salton Massally <saltonmassally@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models, api


class Openg2pDisbursementSlip(models.Model):
    _inherit = "openg2p.disbursement.slip"

    @api.multi
    def compute_sheet(self):
        """
        do we have an unprocessed deregistration record for subject with effective date before the end of the batch?
        """
        super(Openg2pDisbursementSlip, self).compute_sheet()
        self.check_pending_denrollments()

    def check_pending_denrollments(self):
        batch = self[0].batch_id
        active_disenrolls = self.env["openg2p.deregistration"].search_read(
            [
                ("beneficiary_id", "in", self.mapped("beneficiary_id.id")),
                ("state", "=", "confirm"),
                ("date", "<", batch.date_end),
            ],
            [
                "beneficiary_id",
            ],
        )
        rule = self.env.ref(
            "openg2p_bridge_disbursement_deregistration.exception_rule_deregistration_started"
        )

        for i in active_disenrolls:
            beneficiary_id = i["beneficiary_id"][0]
            self.env["openg2p.disbursement.exception"].create(
                {
                    "rule_id": rule.id,
                    "slip_id": self.filtered(
                        lambda r: r.beneficiary_id.id == beneficiary_id
                    ).id,
                    "batch_id": batch.id,
                    "beneficiary_id": beneficiary_id,
                }
            )
