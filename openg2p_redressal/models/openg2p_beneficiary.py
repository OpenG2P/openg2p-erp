from odoo import fields, models


class Beneficiary(models.Model):
    _inherit = "openg2p.beneficiary"

    helpdesk_ticket_ids = fields.One2many(
        comodel_name="helpdesk.ticket",
        inverse_name="beneficiary_id",
        string="Tickets",
    )

    helpdesk_ticket_count = fields.Integer(
        compute="_compute_helpdesk_ticket_count", string="Ticket Count"
    )

    helpdesk_ticket_active_count = fields.Integer(
        compute="_compute_helpdesk_ticket_count", string="Active Ticket Count"
    )

    helpdesk_ticket_count_string = fields.Char(
        compute="_compute_helpdesk_ticket_count", string="Tickets"
    )

    def _compute_helpdesk_ticket_count(self):
        for record in self:
            ticket_ids = record.helpdesk_ticket_ids
            record.helpdesk_ticket_count = len(ticket_ids)
            record.helpdesk_ticket_active_count = len(
                ticket_ids.filtered(lambda ticket: not ticket.stage_id.closed)
            )
            count_active = record.helpdesk_ticket_active_count
            count = record.helpdesk_ticket_count
            record.helpdesk_ticket_count_string = "{} / {}".format(count_active, count)

    def action_view_helpdesk_tickets(self):
        return {
            "name": self.name,
            "view_type": "form",
            "view_mode": "tree,form",
            "res_model": "helpdesk.ticket",
            "type": "ir.actions.act_window",
            "domain": [("beneficiary_id", "=", self.id)],
            "context": self.env.context,
        }
