# -*- coding: utf-8 -*-
# Copyright 2020 OpenG2P (https://openg2p.org)
# @author: Salton Massally <saltonmassally@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging
import random

from odoo import _
from odoo import api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class ExceptionType(models.Model):
    _name = "openg2p.beneficiary.exception.type"
    _description = "Beneficiary Exception Type"
    _order = "name"

    name = fields.Char(string="Type", required=True, translate=True)

    _sql_constraints = [
        ("name_id_uniq", "unique(name)", "Name must be unique."),
    ]
