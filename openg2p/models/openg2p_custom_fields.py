from odoo import models, api, fields


class Openg2pOrgFields(models.Model):
    _inherit = "openg2p.org.fields"
    _description = "Storing custom fields"

    beneficiary_id = fields.Many2one(
        "openg2p.beneficiary",
        required=False,
    )
