from odoo import api, fields, models


class BeneficiaryOrgMap(models.Model):
    _name = "openg2p.beneficiary.orgmap"
    _description = "Beneficiary Org Map Model"

    field_name = fields.Char(
        'Field Name',
        required=True,
    )

    field_value = fields.Char(
        'Field Value',
        required=True,
    )

    registration = fields.Many2one(
        'openg2p.registration',
        required=True,
    )

    def create(self, vals_list):
        super(BeneficiaryOrgMap, self).create(vals_list)