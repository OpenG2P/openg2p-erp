# -*- coding: utf-8 -*-
from odoo import fields, models


class ProgramEnrollmentCategory(models.Model):
    _inherit = "openg2p.program.enrollment_category"

    evaluation_mode = fields.Selection(
        [("basic", "Basic"), ("advanced", "Advanced")],
        string="Evaluation Mode",
        help="Disbursed amount evaluation rule",
        required=True,
        readonly=True,
        default="basic",
    )
    struct_id = fields.Many2one(
        "openg2p.disbursement.structure",
        string="Disbursement Structure",
        readonly=True,
        required=True,
        default=lambda self: self.env.ref("openg2p_disbursement.structure_base", False),
    )
    disbursement_amount = fields.Monetary(
        "Disbursement Amount", required=True, default=0
    )
    currency_id = fields.Many2one(
        string="Currency", related="company_id.currency_id", readonly=True, store=True
    )
