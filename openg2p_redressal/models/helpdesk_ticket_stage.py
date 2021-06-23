from odoo import fields, models


class HelpdeskTicketStage(models.Model):
    _inherit = "helpdesk.ticket.stage"

    sms_template_id = fields.Many2one(
        "sms.template",
        string="SMS Template",
        domain=[("model", "=", "helpdesk.ticket")],
        help="If set an sms will be sent to the beneficiary when the ticket reaches this step.",
    )
