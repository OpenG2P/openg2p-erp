# -*- coding: utf-8 -*-

from odoo import api, fields, models


class Openg2pLocation(models.Model):
    _inherit = "openg2p.location"

    new_registration_count = fields.Integer(
        compute="_compute_new_registration_count", string="New Registration"
    )
    new_registered_beneficiary = fields.Integer(
        compute="_compute_registration_stats", string="New Registered Beneficiaries"
    )
    expected_beneficiary = fields.Integer(
        compute="_compute_registration_stats", string="Expected Beneficiaries"
    )

    @api.multi
    def _compute_new_registration_count(self):
        registration_data = self.env["openg2p.registration"].read_group(
            [("location_id", "in", self.ids), ("stage_id.sequence", "<=", "1")],
            ["location_id"],
            ["location_id"],
        )
        result = dict(
            (data["location_id"][0], data["location_id_count"])
            for data in registration_data
        )
        for location in self:
            location.new_registration_count = result.get(location.id, 0)

    @api.multi
    def _compute_registration_stats(self):
        # TODO fix
        # beneficiary_data = self.env['openg2p.beneficiary'].read_group(
        #     [('location_id', 'in', self.ids)],
        #     ['no_of_registered_beneficiary', 'no_of_registration', 'location_id'], ['location_id'])
        # new_emp = dict((data['location_id'][0], data['no_of_registered_beneficiary']) for data in beneficiary_data)
        # expected_emp = dict((data['location_id'][0], data['no_of_registration']) for data in beneficiary_data)
        for location in self:
            # location.new_registered_beneficiary = new_emp.get(location.id, 0)
            # location.expected_beneficiary = expected_emp.get(location.id, 0)
            location.new_registered_beneficiary = 0
            location.expected_beneficiary = 0
