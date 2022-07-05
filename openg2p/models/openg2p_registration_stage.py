# -*- coding: utf-8 -*-

from odoo import fields, models
from odoo.tools.translate import _

AVAILABLE_PRIORITIES = [
    ("0", "Normal"),
    ("1", "High"),
    ("2", "Urgent"),
]


class RegistrationStage(models.Model):
    _name = "openg2p.registration.stage"
    _description = "Registration Stages"
    _order = "sequence"

    name = fields.Char("Stage name", required=True, translate=True)
    sequence = fields.Integer(
        "Sequence",
        default=10,
        help="Gives the sequence order when displaying a list of stages.",
    )
    requirements = fields.Text("Requirements")
    fold = fields.Boolean(
        "Folded in Registration Pipe",
        help="This stage is folded in the kanban view when there are no records in that stage to display.",
    )
    legend_blocked = fields.Char(
        "Red Kanban Label",
        default=lambda self: _("Blocked"),
        translate=True,
        required=True,
    )
    legend_done = fields.Char(
        "Green Kanban Label",
        default=lambda self: _("Ready for Next Stage"),
        translate=True,
        required=True,
    )
    legend_normal = fields.Char(
        "Grey Kanban Label",
        default=lambda self: _("In Progress"),
        translate=True,
        required=True,
    )
    action = fields.Selection([("create_beneficiary", "Create Beneficiary")])
