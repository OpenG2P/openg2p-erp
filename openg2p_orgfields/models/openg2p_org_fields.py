from odoo import models, api, fields


class Openg2pOrgFields(models.Model):
    _name = "openg2p.org.fields"
    _description = "Storing custom fields"

    field_name = fields.Char(
        "Field Name",
        required=True,
    )

    field_value = fields.Char(
        "Field Value",
        required=True,
    )

    def create(self, vals_list):
        super(Openg2pOrgFields, self).create(vals_list)

    def write(self, vals_list):
        super(Openg2pOrgFields, self).write(vals_list)
