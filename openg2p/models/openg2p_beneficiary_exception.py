# -*- coding: utf-8 -*-
# Copyright 2020 OpenG2P (https://openg2p.org)
# @author: Salton Massally <saltonmassally@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class Openg2pBeneficiaryException(models.Model):
    _name = "openg2p.beneficiary.exception"
    _description = "Beneficiary Exception"
    _order = "date desc"
    _inherit = ["mail.thread", "generic.mixin.no.unlink"]
    _allow_unlink_domain = [("state", "=", "draft")]

    name = fields.Char(
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
        string="Summary",
    )
    date = fields.Datetime(
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    type_id = fields.Many2one(
        "openg2p.beneficiary.exception.type",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    state = fields.Selection(
        [("draft", "Draft"), ("open", "Open"), ("closed", "Closed")],
        default="draft",
        track_visibility="onchange",
        required=True,
    )
    note = fields.Text()
    beneficiary_id = fields.Many2one("openg2p.beneficiary", required=True)
    associated_beneficiary_ids = fields.Many2many(
        "openg2p.beneficiary",
        string="Associated Beneficiaries",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    user_id = fields.Many2one("res.users", string="Responsible")
    confirmed = fields.Boolean(track_visibility="onchange", readonly=True)
    active = fields.Boolean(default=True)

    @api.multi
    def action_confirm(self):
        self.write({"confirmed": True, "state": "open"})

    @api.multi
    def action_close(self):
        self.write({"state": "closed", "active": False})

    def action_merge(self, retained_id, merge_ids, copy_data):
        """
        @param copy_data - usually from the UI
        """
        self.env["openg2p.beneficiary"].browse(retained_id).merge(
            self.env["openg2p.beneficiary"].browse(merge_ids), copy_data or {}
        )
