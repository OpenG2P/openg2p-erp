from odoo import api, fields, models


class BeneficiarySchoolMap(models.Model):
    _name = "openg2p.beneficiary.schoolmap"
    _description = "Beneficiary School Map Model"

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
        index=True,
    )