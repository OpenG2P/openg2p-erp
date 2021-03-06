# -*- coding: utf-8 -*-
# Copyright 2020 OpenG2P (https://openg2p.org)
# @author: Salton Massally <saltonmassally@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    'name': 'OpenG2P Disbursement',
    'summary': "Process disbursement for beneficiaries",
    'author': "OpenG2P",
    'website': "https://openg2p.org",
    'category': 'OpenG2P',
    'version': '0.1',
    'description': "Process disbursement for beneficiaries",
    'depends': [
        'openg2p',
        'openg2p_program',
        'decimal_precision',
        'sms'
    ],
    'data': [
        'security/openg2p_disbursement_security.xml',
        'security/ir.model.access.csv',
        'views/openg2p_program_enrollment.xml',
        'views/openg2p_disbursement_structure.xml',
        'views/openg2p_disbursement_rule_category.xml',
        'views/openg2p_disbursement_contribution_register.xml',
        'views/openg2p_disbursement_rule.xml',
        'views/openg2p_disbursement_slip.xml',
        'views/openg2p_beneficiary.xml',
        'views/openg2p_disbursement_slip_line.xml',
        'views/openg2p_disbursement_report.xml',
        'data/openg2p_disbursement_data.xml',
        'views/report_contributionregister_templates.xml',
        'views/report_slip_templates.xml',
        'views/report_slipdetails_templates.xml',
        'views/openg2p_program_enrollment_category.xml',
        'wizard/openg2p_disbursement_contribution_register_report.xml',
        'wizard/openg2p_disbursement_slips_by_beneficiaries.xml',
        'views/openg2p_disbursement_batch.xml',
        'data/mail_template.xml',
        'wizard/batch_from_selected_beneficiary.xml',
        'wizard/print_contribution_register_view.xml',
        'wizard/send_slip_notifcation_view.xml',
        'views/report_batch_xls.xml',
        'data/exception_rules.xml',
        'views/openg2p_disbursement_exception_rule.xml',
        'views/openg2p_disbursement_exception.xml',
        'views/res_config_settings_views.xml'
    ],
    'demo': [
        'data/openg2p_disbursement_demo.xml'
    ],
}
