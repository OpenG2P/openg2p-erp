# -*- coding: utf-8 -*-
from random import randint

from odoo import fields, models


class ProgramEnrollmentCategory(models.Model):
    _name = "openg2p.program.enrollment_category"
    _description = "Program Classification"
    _order = "sequence, id"

    program_id = fields.Many2one(
        "openg2p.program",
        string="Program",
        index=True,
        required=True,
    )
    name = fields.Char(string="Classification", required=True, translate=True)
    sequence = fields.Integer(
        help="Gives the sequence when displaying a list of enrollments.",
        default=10,
        required=True,
    )
    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.user.company_id
    )
    color = fields.Integer(string="Color Index", default=lambda self: randint(1, 6))
