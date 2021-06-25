# -*- coding: utf-8 -*-
from odoo import fields, models


class Ticket(models.Model):
    _inherit = "helpdesk.ticket"

    beneficiary_id = fields.Many2one("openg2p.beneficiary", index=True)
    program_id = fields.Many2one("openg2p.program", string="Program", index=True)
