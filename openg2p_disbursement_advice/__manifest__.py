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
    "depends": ["openg2p_disbursement", "openg2p_payment_gateway"],
    "data": [
        "data/openg2p_disbursement_advice_data.xml",
        "security/openg2p_banks_security.xml",
        "security/ir.model.access.csv",
        "views/openg2p_beneficiary.xml",
        "views/openg2p_disbursement_advice.xml",
        "views/openg2p_disbursement_advice_line.xml",
        "views/openg2p_disbursement_advice_report.xml",
        "views/openg2p_disbursement_batch.xml",
        "views/openg2p_disbursement_slip.xml",
        "views/report_disbursement_advice.xml",
        "views/report_disbursementslip.xml",
        "views/openg2p_registration.xml",
        "views/report_disbursementslipdetails.xml",
        "views/res_bank.xml",
        "views/res_partner_bank.xml",
        "views/openg2p_gateway_transaction.xml",
        "views/openg2p_disbursement_single_transaction.xml",
        "views/openg2p_disbursement_batch_transaction.xml",
        "views/openg2p_disbursement_main.xml",
    ],
    "demo": ["data/demo.xml"],
}
