from odoo import api, fields, models


class BeneficiarySchool(models.Model):
    _name = "openg2p.beneficiary.school"
    _description = "Beneficiary School Model"

    total_quality = fields.Float(
        string='Total Quality',
        store=True,
        track_visibility='onchange',
        required=True,
    )
    total_equity = fields.Float(
        string='Total Equity',
        store=True,
        track_visibility='onchange',
        required=True,
    )
    retention_progression = fields.Float(
        string='Retention & Progression',
        store=True,
        track_visibility='onchange',
        required=True,
    )

    grand_total = fields.Float(
        string='Grand Total',
        compute='_compute_grand_total',
        store=True,
        readonly=True,
        track_visibility='onchange',
    )

    @api.model
    def create(self, vals):
        total_quality = vals.get('total_quality')
        total_equity = vals.get('total_equity')
        retention_progression = vals.get('retention_progression')
        grand_total = vals.get('grand_total')
        data = {
            'total_quality': self.total_quality,
            'total_equity':self.total_equity,
            'retention_progression':self.retention_progression,
            'grand_total':self.grand_total,
        }
        res = super(BeneficiarySchool, self).create(data)
        return res