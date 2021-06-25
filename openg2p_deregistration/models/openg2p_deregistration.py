# -*- coding: utf-8 -*-
# Copyright 2020 OpenG2P (https://openg2p.org)
# @author: Salton Massally <saltonmassally@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging

from odoo import fields, models, api, _
from odoo.exceptions import Warning as UserError, ValidationError

_logger = logging.getLogger(__name__)


class Openg2pDeregistration(models.Model):
    _name = "openg2p.deregistration"
    _description = "Beneficiary De-registration"
    _order = "name DESC"

    _inherit = ["mail.thread", "generic.mixin.no.unlink", "openg2p.mixin.has_document"]

    allow_unlink_domain = [("state", "=", "draft")]

    date = fields.Date(
        "Effective Date",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)], "confirm": [("readonly", False)]},
    )
    type = fields.Selection(
        [
            ("program", "Dis-enroll from a Program"),
            ("database", "De-register - End all Programs and Archive"),
        ],
        required=True,
    )
    program_id = fields.Many2one(
        "openg2p.program",
        "Program",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    name = fields.Char(related="reason_id.name", store=True)
    reason_id = fields.Many2one(
        "openg2p.deregistration.reason",
        "Reason",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    notes = fields.Text("Notes", readonly=True, states={"draft": [("readonly", False)]})
    beneficiary_id = fields.Many2one(
        "openg2p.beneficiary",
        "Beneficiary",
        required=True,
        readonly=True,
        index=True,
        states={"draft": [("readonly", False)]},
    )
    location_id = fields.Many2one(
        "openg2p.location",
        "Location",
        store=True,
        readonly=True,
        related="beneficiary_id.location_id",
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("confirm", "Confirmed"),
            ("cancel", "Cancelled"),
            ("done", "Done"),
        ],
        readonly=True,
        default="draft",
        track_visibility="onchange",
    )
    active = fields.Boolean(default=True)

    @api.constrains("beneficiary_id")
    def _constraint_beneficiary_id(self):
        for rec in self:  # TODO performance improve
            if not rec.beneficiary_id.active:
                raise ValidationError(
                    _("%s is already inactive" % (rec.beneficiary_id.display_name,))
                )

            if self.search_count(
                [
                    ("beneficiary_id", "=", rec.beneficiary_id.id),
                    ("state", "in", ("draft", "confirm")),
                    ("id", "!=", rec.id),
                ]
            ):
                raise ValidationError(
                    _(
                        "An active de-registration record already exists for %s"
                        % (rec.beneficiary_id.display_name,)
                    )
                )

    @api.model
    @api.returns("self", lambda value: value.id)
    def create(self, vals):
        res = super(Openg2pDeregistration, self).create(vals)
        if res.beneficiary_id.location_id.manager_id:
            res.message_subscribe_users(
                user_ids=[res.beneficiary_id.location_id.manager_id.id]
            )
        return res

    @api.multi
    def state_cancel(self):
        return self.write({"state": "cancel", "active": False})

    @api.multi
    def state_confirm(self):
        return self.write({"state": "confirm"})

    @api.multi
    def state_done(self):
        today = fields.Date.today()
        for termination in self:
            if today < termination.date:
                raise UserError(
                    "Unable to complete operation as the effective date is still in the future!"
                )
            elif termination.type == "database" and termination.beneficiary_id.active:
                termination.beneficiary_id.toggle_active()
            elif termination.type == "program":
                termination.beneficiary_id.program_enrollment_ids.filtered(
                    lambda r: r.program_id == termination.program_id
                    and r.state in ("open", "draft")
                ).write({"date_end": termination.date, "state": "close"})
        return self.write({"state": "done", "active": False})

    @api.model
    def try_effecting_ended(self):
        self.search(
            [("state", "=", "confirm"), ("name", "<=", fields.Date.today())]
        ).state_done()
