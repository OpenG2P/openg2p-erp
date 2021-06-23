# -*- coding: utf-8 -*-
# Copyright 2020 OpenG2P (https://openg2p.org)
# @author: Salton Massally <saltonmassally@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class Openg2pBeneficiary(models.Model):
    _inherit = "openg2p.beneficiary"

    slip_ids = fields.One2many(
        "openg2p.disbursement.slip", "beneficiary_id", string="Slips", readonly=True
    )
    slip_count = fields.Integer(
        compute="_compute_slip_count",
        string="Disbursement Slip Count",
    )

    @api.multi
    def _compute_slip_count(self):
        for beneficiary in self:
            beneficiary.slip_count = self.env["openg2p.disbursement.slip"].search_count(
                [("beneficiary_id", "=", beneficiary.id), ("state", "=", "done")]
            )
