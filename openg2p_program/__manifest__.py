# -*- coding: utf-8 -*-
{
    'name': 'OpenG2P Program Management',
    'summary': "Register beneficiaries into payment programs and pay them",
    'author': "OpenG2P",
    'website': "https://openg2p.org",
    'category': 'OpenG2P',
    'version': '0.1',
    'depends': [
        'openg2p'
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/openg2p_program.xml',
        'views/openg2p_program_registration_category.xml',
        'views/openg2p_program.xml',
        'views/openg2p_program_registration.xml',
        'views/openg2p_beneficiary.xml',
        'wizard/register_beneficiary.xml'
    ],
    'demo': ['data/openg2p_program_demo.xml'],
    'installable': True,
    'auto_install': True,
}
