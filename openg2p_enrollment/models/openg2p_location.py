# -*- coding: utf-8 -*-

from odoo import api, fields, models


class Openg2pLocation(models.Model):
    _inherit = 'openg2p.location'

    new_applicant_count = fields.Integer(
        compute='_compute_new_applicant_count', string='New Applicant')
    new_enrolled_beneficiary = fields.Integer(
        compute='_compute_enrollment_stats', string='New Enrolled Beneficiaries')
    expected_beneficiary = fields.Integer(
        compute='_compute_enrollment_stats', string='Expected Beneficiaries')

    @api.multi
    def _compute_new_applicant_count(self):
        applicant_data = self.env['openg2p.applicant'].read_group(
            [('location_id', 'in', self.ids), ('stage_id.sequence', '<=', '1')],
            ['location_id'], ['location_id'])
        result = dict((data['location_id'][0], data['location_id_count']) for data in applicant_data)
        for location in self:
            location.new_applicant_count = result.get(location.id, 0)

    @api.multi
    def _compute_enrollment_stats(self):
        # TODO fix
        # beneficiary_data = self.env['openg2p.beneficiary'].read_group(
        #     [('location_id', 'in', self.ids)],
        #     ['no_of_enrolled_beneficiary', 'no_of_enrollment', 'location_id'], ['location_id'])
        # new_emp = dict((data['location_id'][0], data['no_of_enrolled_beneficiary']) for data in beneficiary_data)
        # expected_emp = dict((data['location_id'][0], data['no_of_enrollment']) for data in beneficiary_data)
        for location in self:
            # location.new_enrolled_beneficiary = new_emp.get(location.id, 0)
            # location.expected_beneficiary = expected_emp.get(location.id, 0)
            location.new_enrolled_beneficiary = 0
            location.expected_beneficiary = 0
