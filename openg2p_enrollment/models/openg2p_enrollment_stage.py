# -*- coding: utf-8 -*-

from odoo import fields, models
from odoo.tools.translate import _

AVAILABLE_PRIORITIES = [
    ('0', 'Normal'),
    ('1', 'Good'),
    ('2', 'Very Good'),
    ('3', 'Excellent')
]


class EnrollmentStage(models.Model):
    _name = "openg2p.enrollment.stage"
    _description = "Enrollment Stages"
    _order = 'sequence'

    name = fields.Char(
        "Stage name",
        required=True,
        translate=True
    )
    sequence = fields.Integer(
        "Sequence",
        default=10,
        help="Gives the sequence order when displaying a list of stages."
    )
    requirements = fields.Text("Requirements")
    fold = fields.Boolean(
        "Folded in Enrollment Pipe",
        help="This stage is folded in the kanban view when there are no records in that stage to display."
    )
    legend_blocked = fields.Char(
        'Red Kanban Label',
        default=lambda self: _('Blocked'),
        translate=True,
        required=True
    )
    legend_done = fields.Char(
        'Green Kanban Label',
        default=lambda self: _('Ready for Next Stage'),
        translate=True,
        required=True
    )
    legend_normal = fields.Char(
        'Grey Kanban Label',
        default=lambda self: _('In Progress'),
        translate=True,
        required=True
    )
    can_create_beneficiary = fields.Boolean(
        default=False
    )
