# -*- coding: utf-8 -*-
# Copyright 2020 OpenG2P (https://openg2p.org)
# @author: Salton Massally <saltonmassally@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "OpenG2P Disbursement Reconciliation Report",
    "summary": "Prints reconciliation report for disbursement batches",
    "author": "OpenG2P",
    "website": "https://openg2p.org",
    "category": "OpenG2P",
    "version": "0.1",
    "depends": ["openg2p_disbursement", "report_xlsx", "report_xlsx_helper"],
    "data": [
        "wizard/openg2p_disbursement_reconciliation_report.xml",
        "views/openg2p_disbursement_reconciliation_report.xml",
        "report/openg2p_disbursement_reconciliation_report.xml",
    ],
    "installable": True,
    "auto_install": True,
}
