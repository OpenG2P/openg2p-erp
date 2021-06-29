# -*- coding: utf-8 -*-
# Copyright 2020 OpenG2P (https://openg2p.org)
# @author: Salton Massally <saltonmassally@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models, fields


class Openg2pDisbursementException(models.Model):
    _name = "openg2p.disbursement.exception"
    _description = "Disbursement Exception"

    name = fields.Char(related="rule_id.name", store=True, readonly=True)
    rule_id = fields.Many2one(
        "openg2p.disbursement.exception.rule",
        "Rule",
        required=True,
        ondelete="cascade",
        index=True,
    )
    beneficiary_id = fields.Many2one(
        "openg2p.beneficiary",
        "Beneficiary",
        ondelete="cascade",
        required=True,
        index=True,
    )
    slip_id = fields.Many2one(
        "openg2p.disbursement.slip",
        "Payslip",
        ondelete="cascade",
    )
    batch_id = fields.Many2one(
        "openg2p.disbursement.batch", readonly=True, ondelete="cascade", index=True
    )
    severity = fields.Selection(
        related="rule_id.severity",
        store=True,
    )
    note = fields.Text()
