from odoo import fields, models


class Openg2pRegistration(models.Model):
    _inherit = "openg2p.registration"

    bank_account_id = fields.Many2one(
        "res.partner.bank", string="Bank Account", index=True
    )
    bank_account_number = fields.Char(
        related="bank_account_id.acc_number", readonly=True, store=True, index=True
    )
    bank_account_type = fields.Selection(
        related="bank_account_id.acc_type", readonly=True, store=True
    )

    _sql_constraints = [
        (
            "bank_account_id_uniq",
            "UNIQUE (bank_account_id)",
            "Bank account must be unique to beneficiary.",
        ),
    ]
