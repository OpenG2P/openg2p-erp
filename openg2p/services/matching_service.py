# -*- coding: utf-8 -*-
# Copyright 2020 OpenG2P (https://openg2p.org)
# @author: Salton Massally <saltonmassally@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import AbstractComponent, Component
from odoo.osv import expression
from odoo.exceptions import UserError
from odoo import models
import logging
_logger = logging.getLogger(__name__)

"""
Fastest but least comprehensive matching mode
"""
MATCH_MODE_QUICK = 1

"""
Takes a while but runs more complex matching algo
"""
MATCH_MODE_NORMAL = 2

"""
Slowest and runs the most computationally intensive algos and should only be called in async or job context
"""
MATCH_MODE_COMPREHENSIVE = 3


class MatchingService(AbstractComponent):
    _name = 'matching.service'
    _description = 'Matching Service'
    _collection = 'openg2p.beneficiary'
    _usage = 'beneficiary.matcher'

    @property
    def matcher_name(self):
        return self._name.replace('matching.service.', '')

    @property
    def mode(self):
        raise NotImplemented

    @property
    def sequence(self):
        raise NotImplemented

    def match(self, query):
        raise NotImplemented


class MatchingServiceExactIdentities(Component):
    _inherit = 'matching.service'
    _name = 'matching.service.exact_identities'

    @property
    def mode(self):
        return MATCH_MODE_QUICK

    @property
    def sequence(self):
        return 0

    def match(self, query):
        assert isinstance(query, models.Model)
        identities = query.get_identities()
        if not identities:
            return False

        domain = expression.OR([('category_id.code', '=', ID), ('name', '=', number)]
                               for ID, number in query.get_identities())
        matches = self.with_context(active_test=False).env['openg2p.beneficiary.id_number'].search(domain)
        return matches.mapped('beneficiary_id') if len(matches) > 0 else False
