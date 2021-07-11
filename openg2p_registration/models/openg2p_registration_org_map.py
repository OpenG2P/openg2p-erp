from odoo import api, fields, models


class RegistrationOrgMap(models.Model):
    _name = "openg2p.registration.orgmap"
    _description = "Registration Org Map Model"

    field_name = fields.Char(
        "Field Name",
        required=True,
    )

    field_value = fields.Char(
        "Field Value",
        required=True,
    )

    regd_id = fields.Many2one(
        "openg2p.registration",
        required=True,
    )

    def create(self, vals_list):
        super(RegistrationOrgMap, self).create(vals_list)
