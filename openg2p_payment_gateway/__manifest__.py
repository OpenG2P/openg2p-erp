# -*- coding: utf-8 -*-
# Copyright 2020 OpenG2P (https://openg2p.org)
# @author: Salton Massally <saltonmassally@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "OpenG2P Payments Gateways",
    "summary": "Abstraction payment gatweway layer for the OpenG2P project",
    "author": "OpenG2P",
    "website": "https://openg2p.org",
    "category": "OpenG2P",
    "version": "0.1",
    "depends": [
        "openg2p",
        "component",
        "queue_job",
        "keychain",
    ],
    "data": [
        "views/res_bank.xml",
        "views/openg2p_gateway_transaction.xml",
        "security/ir.model.access.csv",
    ],
}
