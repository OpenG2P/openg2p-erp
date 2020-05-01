# -*- coding: utf-8 -*-
# Copyright 2020 OpenG2P (https://openg2p.org)
# @author: Salton Massally <saltonmassally@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    module_openg2p_beneficiary_relative = fields.Boolean(string="Record Beneficiaries Relatives Data")
    module_openg2p_enrollment = fields.Boolean(string="Track Beneficiary Enrollments")
    module_openg2p_disenrollment = fields.Boolean(string="Track Beneficiary Disenrollments")
    module_openg2p_security = fields.Boolean(string="Advanced User Security Measures")
    module_openg2p_disbursement = fields.Boolean(string="Manage Disbursements to Beneficiaries")
    module_openg2p_disbursement_advice = fields.Boolean(string="Manage Digital Payments to Beneficiaries")
    module_openg2p_disbursement_reconciliation = fields.Boolean(string="Disbursement Reconciliation tools")
    module_openg2p_redressal = fields.Boolean(string="Record and Track issues reported by Beneficiaries")
    beneficiary_id_gen_method = fields.Selection(
        related='company_id.beneficiary_id_gen_method'
    )
    beneficiary_id_random_digits = fields.Integer(
        related='company_id.beneficiary_id_random_digits'
    )
    beneficiary_id_sequence = fields.Many2one(
        'ir.sequence',
        related='company_id.beneficiary_id_sequence'
    )
