from odoo import models, api, fields


class Openg2pOrgFields(models.Model):
    _inherit = "openg2p.org.fields"
    _description = "Storing custom fields"

    regd_id = fields.Many2one(
        "openg2p.registration",
        required=True,
    )
