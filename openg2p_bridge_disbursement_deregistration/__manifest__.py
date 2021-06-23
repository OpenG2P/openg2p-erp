# -*- coding: utf-8 -*-
# Copyright 2020 OpenG2P (https://openg2p.org)
# @author: Salton Massally <saltonmassally@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "OpenG2P Disbursement Deregistration Bridge",
    "summary": "Integrate deregistration with disbursement",
    "author": "OpenG2P",
    "website": "https://openg2p.org",
    "category": "OpenG2P",
    "version": "0.1",
    "depends": [
        "openg2p_disbursement",
        "openg2p_deregistration",
    ],
    "data": ["views/openg2p_disbursement_batch.xml", "data/exception_rules.xml"],
    "auto_install": True,
}
