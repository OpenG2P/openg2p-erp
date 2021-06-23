# -*- coding: utf-8 -*-
# Copyright 2020 OpenG2P (https://openg2p.org)
# @author: Salton Massally <saltonmassally@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models, fields, api


class DisbursementBatch(models.Model):
    _inherit = "openg2p.disbursement.batch"

    has_checklist_draft = fields.Boolean(default=True)
    checklist_draft_complete_enrollment = fields.Boolean()
    active_enrollment_count = fields.Integer(
        compute="_compute_active_enrollment_count", string="Pending Enrollment"
    )

    @api.multi
    def _compute_can_generate(self):
        self.ensure_one()
        if self.checklist_draft_complete_enrollment:
            super(DisbursementBatch, self)._compute_can_generate()
        else:
            self.can_generate = False

    @api.one
    def _compute_active_enrollment_count(self):
        for rec in self:
            rec.active_enrollment_count = self.env["openg2p.registration"].search_count(
                [("stage_id.fold", "=", False), ("create_date", "<=", self.date_end)]
            )
