# -*- coding: utf-8 -*-
# Copyright 2020 OpenG2P (https://openg2p.org)
# @author: Salton Massally <saltonmassally@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "OpenG2P Registration",
    "summary": "Track beneficiary registrations into your database",
    "author": "OpenG2P",
    "website": "https://openg2p.org",
    "category": "OpenG2P",
    "version": "0.1",
    "depends": [
        "openg2p",
        "calendar",
        "fetchmail",
        "document",
        #   'digest',
    ],
    "data": [
        "data/openg2p_registration_data.xml",
        "data/cron.xml",
        "security/openg2p_registration_security.xml",
        "security/ir.model.access.csv",
        "views/menu.xml",
        "views/openg2p_beneficiary.xml",
        "views/openg2p_registration.xml",
        "views/openg2p_registration_category.xml",
        "views/openg2p_registration_stage.xml",
        "views/openg2p_location.xml",
        #    'views/digest_views.xml',
    ],
    "demo": ["data/openg2p_registration_demo.xml"],
    "installable": True,
    "auto_install": False,
    "registration": True,
    "post_init_hook": "post_init",
}
