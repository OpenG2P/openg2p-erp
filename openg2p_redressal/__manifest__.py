# -*- coding: utf-8 -*-
{
    "name": "OpenG2P Redressal",
    "summary": "Redressal support for payment programs",
    "author": "OpenG2P",
    "website": "https://openg2p.org",
    "category": "OpenG2P",
    "version": "0.1",
    "description": "Process disbursement for beneficiaries",
    # any module necessary for this one to work correctly
    "depends": ["openg2p", "openg2p_program", "helpdesk_mgmt"],
    # always loaded
    "data": [
        "security/openg2p_redressal_security.xml",
        "views/helpdesk_ticket.xml",
        "views/helpdesk_ticket_category.xml",
        "views/helpdesk_ticket_stage.xml",
        "views/openg2p_beneficiary.xml",
    ],
    # only loaded in demonstration mode
    "demo": [
        "demo/openg2p_redressal.xml",
    ],
}
