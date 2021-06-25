from odoo import fields, models


class HelpdeskCategory(models.Model):
    _inherit = "helpdesk.ticket.category"

    program_id = fields.Many2one(
        "openg2p.program",
        string="Program",
    )
