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


class BeneficiaryCategory(models.Model):
    _description = "Beneficiary Category"
    _name = "openg2p.beneficiary.category"
    _order = "name"
    _parent_store = True

    name = fields.Char(string="Tag Name", required=True, translate=True, index=True)
    color = fields.Integer(
        string="Color Index", default=lambda self: random.randint(1, 11)
    )
    parent_id = fields.Many2one(
        "openg2p.beneficiary.category",
        string="Parent Category",
        index=True,
        ondelete="cascade",
    )
    child_ids = fields.One2many(
        "openg2p.beneficiary.category", "parent_id", string="Child Categories"
    )
    active = fields.Boolean(
        default=True,
        help="The active field allows you to hide the category without removing it.",
    )
    parent_path = fields.Char(index=True)

    @api.constrains("parent_id")
    def _check_parent_id(self):
        if not self._check_recursion():
            raise ValidationError(_("You can not create recursive categories."))

    @api.multi
    def name_get(self):
        """Return the categories' display name, including their direct
        parent by default.

        If ``context['beneficiary_category_display']`` is ``'short'``, the short
        version of the category name (without the direct parent) is used.
        The default is the long version.
        """
        if self._context.get("beneficiary_category_display") == "short":
            return super(BeneficiaryCategory, self).name_get()

        res = []
        for category in self:
            names = []
            current = category
            while current:
                names.append(current.name)
                current = current.parent_id
            res.append((category.id, " / ".join(reversed(names))))
        return res

    @api.model
    def _name_search(
        self, name, args=None, operator="ilike", limit=100, name_get_uid=None
    ):
        args = args or []
        if name:
            # Be sure name_search is symetric to name_get
            name = name.split(" / ")[-1]
            args = [("name", operator, name)] + args
        beneficiary_category_ids = self._search(
            args, limit=limit, access_rights_uid=name_get_uid
        )
        return self.browse(beneficiary_category_ids).name_get()
