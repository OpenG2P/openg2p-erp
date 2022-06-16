# -*- coding: utf-8 -*-
# Copyright 2020 OpenG2P (https://openg2p.org)
# @author: Salton Massally <saltonmassally@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "OpenG2P Digital Payments",
    "summary": "Enable Digital Payments to Beneficiaries",
    "author": "OpenG2P",
    "website": "https://openg2p.org",
    "category": "OpenG2P",
    "version": "0.1",
    "depends": ["openg2p", "sms", "openg2p_registration"],
    "data": [
        "security/openg2p_banks_security.xml",
        "views/openg2p_beneficiary.xml",
        "views/openg2p_registration.xml",
        "views/res_bank.xml",
        "views/res_partner_bank.xml",
        "views/action_menu.xml",
        "views/transaction_menu.xml",
        "views/openg2p_disbursement_single_transaction.xml",
        "views/openg2p_disbursement_batch_transaction.xml",
        "views/openg2p_disbursement_main.xml",
        "views/openg2p_disbursement_file.xml",
        "security/ir.model.access.csv",
    ],
    "demo": [
        "data/demo.xml",
    ],
}
