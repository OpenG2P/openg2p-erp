# -*- coding: utf-8 -*-
# Copyright 2020 OpenG2P (https://openg2p.org)
# @author: Salton Massally <saltonmassally@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class Openg2pDisbursementSlip(models.Model):
    _inherit = "openg2p.disbursement.slip"

    advice_line_id = fields.Many2one(
        "openg2p.disbursement.advice.line", "Bank Advice Line", copy=False
    )
