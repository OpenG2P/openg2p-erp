from odoo import api, fields, models


class BeneficiarySchool(models.Model):
    _name = "openg2p.beneficiary_school"
    _description = "Beneficiary School Model"
    _inherit = ["openg2p.registration"]

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

    beneficiary_name = fields.Many2one(
        'openg2p.registration',
        compute=''
    )

    @api.depends('retention_progression', 'total_equity', 'total_quality')
    def _compute_grand_total(self):
        print('COMPUTE GRAND TOTAL', self.env['openg2p.registration.stage'].name)
        for record in self:
            record.grand_total = record.retention_progression + record.total_quality + record.total_equity
