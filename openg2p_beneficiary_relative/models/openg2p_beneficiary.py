# -*- coding: utf-8 -*-
from odoo import fields, models


class Openg2pBeneficiary(models.Model):
    _inherit = "openg2p.beneficiary"

    relative_ids = fields.One2many(
        string="Relatives",
        comodel_name="openg2p.beneficiary.relative",
        inverse_name="beneficiary_id",
        track_visibility="onchange",
    )
