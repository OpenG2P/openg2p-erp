# Part of Odoo. See LICENSE file for full copyright and licensing details.
from datetime import timedelta

from odoo import api, fields, models


class Openg2pBeneficiary(models.Model):
    _inherit = "openg2p.beneficiary"

    newly_enrolled_beneficiary = fields.Boolean(
        'Newly enrolled beneficiary',
        compute='_compute_newly_enrolled_beneficiary',
        search='_search_newly_enrolled_beneficiary'
    )

    @api.multi
    def _compute_newly_enrolled_beneficiary(self):
        read_group_result = self.env['openg2p.applicant'].read_group(
            [('beneficiary_id', 'in', self.ids), ('enrolled_date', '>=', fields.Datetime.now() - timedelta(days=30))],
            ['beneficiary_id'], ['beneficiary_id'])
        result = dict((data['beneficiary_id'], data['beneficiary_id_count'] > 0) for data in read_group_result)
        for record in self:
            record.newly_enrolled_beneficiary = result.get(record.id, False)

    def _search_newly_enrolled_beneficiary(self, operator, value):
        applicants = self.env['openg2p.applicant'].search(
            [('enrolled_date', '>=', fields.Datetime.now() - timedelta(days=30))])
        return [('id', 'in', applicants.ids)]
