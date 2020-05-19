# -*- coding: utf-8 -*-
# Copyright 2020 OpenG2P (https://openg2p.org)
# @author: Salton Massally <saltonmassally@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    'name': 'OpenG2P Enrollment',
    'summary': "Track beneficiary enrollments into your database",
    'author': "OpenG2P",
    'website': "https://openg2p.org",
    'category': 'OpenG2P',
    'version': '0.1',
    'depends': [
        'openg2p',
        'calendar',
        'fetchmail',
        'document',
        #   'digest',
    ],
    'data': [
        'data/openg2p_enrollment_data.xml',
        'data/cron.xml',

        'security/openg2p_enrollment_security.xml',
        'security/ir.model.access.csv',

        'views/menu.xml',
        'views/openg2p_applicant_reject_reason.xml',
        'views/openg2p_beneficiary.xml',
        'views/openg2p_applicant.xml',
        'views/openg2p_applicant_category.xml',
        'views/openg2p_enrollment_stage.xml',
        'views/openg2p_location.xml',
        'wizard/reject_reason.xml',
        #    'views/digest_views.xml',
    ],
    'demo': [
        'data/openg2p_enrollment_demo.xml'
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
    'post_init_hook': 'post_init',
}
