# -*- coding: utf-8 -*-
# Copyright 2020 OpenG2P (https://openg2p.org)
# @author: Salton Massally <saltonmassally@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import _
from odoo import api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class Location(models.Model):
    _name = "openg2p.location"
    _description = "Location"
    _inherit = ["mail.thread"]
    _order = "name"
    _rec_name = "complete_name"

    name = fields.Char(
        "Location Name", required=True, index=True, track_visibility="onchange"
    )
    complete_name = fields.Char(
        "Complete Name", compute="_compute_complete_name", store=True
    )
    active = fields.Boolean(default=True, track_visibility="onchange")
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        index=True,
        default=lambda self: self.env.user.company_id,
    )
    parent_id = fields.Many2one(
        "openg2p.location",
        string="Parent Location",
        index=True,
        track_visibility="onchange",
    )
    child_ids = fields.One2many(
        "openg2p.location", "parent_id", string="Child Locations"
    )
    member_ids = fields.One2many(
        "openg2p.beneficiary", "location_id", string="Members", readonly=True
    )
    members_count = fields.Integer(compute="_compute_member_count")
    manager_id = fields.Many2one(
        "res.users", string="Manager", index=True, track_visibility="onchange"
    )
    note = fields.Text("Note")
    color = fields.Integer("Color Index")

    @api.depends("member_ids")
    def _compute_member_count(self):
        for location in self:
            location.members_count = self.env["openg2p.beneficiary"].search_count(
                [("location_id", "child_of", location.id)]
            )

    @api.depends("name", "parent_id.complete_name")
    def _compute_complete_name(self):
        for location in self:
            if location.parent_id:
                location.complete_name = "%s / %s" % (
                    location.parent_id.complete_name,
                    location.name,
                )
            else:
                location.complete_name = location.name

    @api.constrains("parent_id")
    def _check_parent_id(self):
        if not self._check_recursion():
            raise ValidationError(_("You cannot create recursive locations."))
