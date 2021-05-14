from odoo import api, fields, models


class BeneficiarySchoolMap(models.Model):
    _name = "openg2p.beneficiary.schoolmap"
    _description = "Beneficiary School Map Model"

    field_name = fields.Char(
        'Field Name'
    )

    field_value = fields.Char(
        'Field Value'
    )

    registration = fields.Many2one(
        'openg2p.registration',
        required=True,
        index=True,
    )

    # @api.model
    # def create(self, vals):
    #     total_quality = vals.get('total_quality')
    #     total_equity = vals.get('total_equity')
    #     retention_progression = vals.get('retention_progression')
    #     grand_total = vals.get('grand_total')
    #     data = {
    #         'total_quality': self.total_quality,
    #         'total_equity':self.total_equity,
    #         'retention_progression':self.retention_progression,
    #         'grand_total':self.grand_total,
    #     }
    #     res = super(BeneficiarySchoolMap, self).create(data)
    #     return res