# -*- coding: utf-8 -*-
# Copyright 2020 OpenG2P (https://openg2p.org)
# @author: Salton Massally <saltonmassally@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    'name': "OpenG2P School",
    'summary': "Comprehensive suite providing list management and payment routing for large scare payment programs",
    'author': "OpenG2P",
    'website': "https://openg2p.org",
    'category': 'OpenG2P',
    'version': '0.1',
    'depends': [
        "openg2p_registration",
    ],
    'data': [
        'openg2p_beneficiary_school.xml',
        'security/ir.model.access.csv',
    ],
    'demo': [],
    # 'post_init_hook': 'post_init',
    'installable': True,
    'application': True,
    'auto_install': False,
}
