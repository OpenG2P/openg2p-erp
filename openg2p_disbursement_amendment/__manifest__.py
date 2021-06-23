# -*- coding: utf-8 -*-
{
    "name": "OpenG2P Disbursement Amendments",
    "summary": "Enables amendments to be made to disbursement",
    "author": "OpenG2P",
    "website": "https://openg2p.org",
    "category": "OpenG2P",
    "version": "0.1",
    "depends": ["openg2p_disbursement"],
    "data": [
        "views/openg2p_disbursement_amendment.xml",
        "views/openg2p_disbursement_batch.xml",
        "views/openg2p_disbursement_category.xml",
        "security/ir.model.access.csv",
        "data/openg2p_disbursement_amendment_data.xml",
    ],
    "installable": False,  # bring back when module is ready
}
