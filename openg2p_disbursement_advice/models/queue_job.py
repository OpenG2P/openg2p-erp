# -*- coding: utf-8 -*-
# Copyright 2020 OpenG2P (https://openg2p.org)
# @author: Salton Massally <saltonmassally@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, models, _


class QueueJob(models.Model):
    """Job status and result"""

    _inherit = "queue.job"

    @api.multi
    def _related_action_disbursement_advice(self):
        return {
            "name": _("Disbursement Advice"),
            "type": "ir.actions.act_window",
            "res_model": "openg2p.disbursement.advice",
            "view_type": "form",
            "view_mode": "form",
            "domain": str(
                [
                    (
                        "id",
                        "in",
                        [
                            self.kwargs.get("att_id"),
                        ],
                    )
                ]
            ),
        }
