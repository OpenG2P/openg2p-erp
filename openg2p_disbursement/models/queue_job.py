# -*- coding: utf-8 -*-
from odoo import api, models, _


class QueueJob(models.Model):
    """Job status and result"""

    _inherit = "queue.job"

    @api.multi
    def _related_action_disbursement_batch(self):
        return {
            "name": _("Disbursement Batch"),
            "type": "ir.actions.act_window",
            "res_model": "openg2p.disbursement.batch",
            "view_type": "form",
            "view_mode": "tree,form",
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
