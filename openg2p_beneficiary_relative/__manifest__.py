# Copyright (C) 2018 Brainbean Apps (https://brainbeanapps.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Beneficiary Relatives",
    "version": "12.0.1.1.0",
    "category": "Human Resources",
    "author": "Brainbean Apps, " "Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "installable": True,
    "application": False,
    "summary": "Allows storing information about beneficiary's family",
    "depends": [
        "openg2p",
    ],
    "external_dependencies": {
        "python": [
            "dateutil",
        ],
    },
    "data": [
        "data/data_relative_relation.xml",
        "security/ir.model.access.csv",
        "views/openg2p_beneficiary.xml",
        "views/openg2p_beneficiary_relative.xml",
    ],
}
