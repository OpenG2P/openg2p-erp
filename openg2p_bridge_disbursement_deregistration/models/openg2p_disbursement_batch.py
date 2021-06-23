# -*- coding: utf-8 -*-
# Copyright 2020 OpenG2P (https://openg2p.org)
# @author: Salton Massally <saltonmassally@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models, fields, api


class DisbursementBatch(models.Model):
    _inherit = "openg2p.disbursement.batch"

    has_checklist_draft = fields.Boolean(default=True)
    checklist_draft_complete_deregistration = fields.Boolean()
    active_deregistration_count = fields.Integer(
        compute="_compute_active_deregistration_count", string="Pending Deregistration"
    )

    @api.multi
    def _compute_can_generate(self):
        self.ensure_one()
        if self.checklist_draft_complete_deregistration:
            super(DisbursementBatch, self)._compute_can_generate()
        else:
            self.can_generate = False

    @api.multi
    def _compute_active_deregistration_count(self):
        for rec in self:
            rec.active_deregistration_count = self.env[
                "openg2p.deregistration"
            ].search_count(
                [
                    ("state", "=", "confirm"),
                    ("date", "<=", rec.date_end),
                    "|",
                    ("program_id", "=", rec.program_id.id),
                    ("program_id", "=", False),
                ]
            )
