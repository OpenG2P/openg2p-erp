# -*- coding: utf-8 -*-
# Copyright 2020 OpenG2P (https://openg2p.org)
# @author: Salton Massally <saltonmassally@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    beneficiary_id_gen_method = fields.Selection(
        selection=[
            ("random", "Random"),
            ("sequence", "Sequence"),
        ],
        string="Generation Method",
        default="random",
    )
    beneficiary_id_random_digits = fields.Integer(
        string="# of Digits",
        default=8,
        help="Number of digits in beneficiary identifier",
    )
    beneficiary_id_sequence = fields.Many2one(
        comodel_name="ir.sequence",
        string="Identifier Sequence",
        help="Pattern to be used for beneficiary identifier generation",
        default=lambda self: self.env.ref("openg2p.seq_openg2p_beneficiary_id", False)
        or None,
    )
