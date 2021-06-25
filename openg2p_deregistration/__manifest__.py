# -*- coding: utf-8 -*-
{
    "name": "OpenG2P Deregistration",
    "summary": "Enables beneficiary deregistration",
    "author": "OpenG2P",
    "website": "https://openg2p.org",
    "category": "OpenG2P",
    "version": "0.1",
    "depends": ["openg2p_program", "openg2p_registration"],
    "data": [
        "security/ir.model.access.csv",
        "wizard/wiz_deregistration.xml",
        "data/cron.xml",
        "views/openg2p_deregistration.xml",
        "views/openg2p_deregistration_reason.xml",
    ],
    "auto_install": True,
}
