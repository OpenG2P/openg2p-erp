# -*- coding: utf-8 -*-
# Copyright 2020 OpenG2P (https://openg2p.org)
# @author: Salton Massally <saltonmassally@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class Openg2pDeregistrationReason(models.Model):
    _name = "openg2p.deregistration.reason"
    _description = "Reason for De-registration"

    name = fields.Char("Name", required=True)

    _sql_constraints = [
        ("name_id_uniq", "unique(name)", "Name must be unique."),
    ]
