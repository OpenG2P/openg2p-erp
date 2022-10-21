from odoo import models, fields


class DisbursementConfiguration(models.Model):
    _name = "openg2p.disbursement.configuration"
    _description = "Disbursement Configuration"

    bulk_transfer_url = fields.Text(string="Bulk Transfer URL", required=True)
    batch_summary_url = fields.Text(string="Batch Summary URL", required=False)
    auth_url = fields.Text(string="Authorization URL", required=True)
    username = fields.Char(string="Username", required=False)
    password = fields.Char(string="Password", required=False)
    grant_type = fields.Char(string="Grant Type", required=False)
    tenant_name = fields.Char(string="Tenant Name", required=True)
