# -*- coding: utf-8 -*-
{
    'name': 'OpenG2P Disenrollment',
    'summary': "Enables beneficiary disenrollment",
    'author': "OpenG2P",
    'website': "https://openg2p.org",
    'category': 'OpenG2P',
    'version': '0.1',

    'depends': [
        'openg2p_program',
        'openg2p_enrollment'
    ],
    'data': [
        'security/ir.model.access.csv',
        'wizard/wiz_disenrollment.xml',
        'data/cron.xml',
        'views/openg2p_disenrollment.xml',
        'views/openg2p_disenrollment_reason.xml'
    ],
    'auto_install': True,
}
