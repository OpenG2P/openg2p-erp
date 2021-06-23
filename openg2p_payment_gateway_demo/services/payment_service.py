# -*- coding: utf-8 -*-
# Copyright 2020 OpenG2P (https://openg2p.org)
# @author: Salton Massally <saltonmassally@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _
from odoo.exceptions import Warning as UserError
from odoo.tools import float_round, float_repr
from odoo.addons.component.core import Component

import json
import logging

_logger = logging.getLogger(__name__)


class PaymentService(Component):
    _inherit = "payment.service"
    _name = "payment.service.demo"
    _usage = "gateway.provider"
    _allowed_execute_method = ["server2server"]

    def execute(self):
        transaction = self.collection
        vals = {"external_id": "we did it"}
        transaction.write(vals)
