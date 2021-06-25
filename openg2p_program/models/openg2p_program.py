# -*- coding: utf-8 -*-
from random import randint

from odoo import models, fields, api


class Program(models.Model):
    _name = "openg2p.program"
    _description = "Disbursement Program"
    _order = "name, id"
    _inherit = [
        "generic.mixin.name_with_code",
        "generic.mixin.uniq_name_code",
        "generic.mixin.no.unlink",
        "mail.thread",
        "openg2p.mixin.has_document",
    ]
    allow_unlink_domain = [("state", "=", "draft")]

    name = fields.Char(track_visibility="onchange")
    code = fields.Char(readonly=True, states={"draft": [("readonly", False)]})
    state = fields.Selection(
        [("draft", "Draft"), ("active", "Active"), ("done", "Done")],
        string="Status",
        readonly=True,
        required=True,
        track_visibility="always",
        default="draft",
        help="Status",
    )
    type = fields.Selection(
        [("remuneration", "Remuneratory"), ("social", "Social Net")],
        string="Type",
        required=True,
        help="Nature of the program. \n"
        "Remuneratory: For programs that are paying workers for work they are performing. E.g. contact tracers "
        "during and epidermic. \n "
        "Social Net: Social payments made to beneficiaries",
        states={"draft": [("readonly", False)]},
        readonly=True,
    )
    note = fields.Text("Description", states={"close": [("readonly", True)]})
    date_start = fields.Date(
        "Start Date",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
        default=fields.Date.context_today,
    )
    date_end = fields.Date(
        "End Date",
        states={"close": [("readonly", True), ("required", True)]},
        index=True,
        track_visibility="onchange",
    )
    active = fields.Boolean(
        default=True,
        readonly=True,
        help="If the active field is set to False, it will allow you to hide the program without removing it.",
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        index=True,
        default=lambda self: self.env.user.company_id,
    )
    currency_id = fields.Many2one(
        "res.currency",
        related="company_id.currency_id",
        string="Currency",
        readonly=True,
    )
    color = fields.Integer(string="Color Index", default=lambda self: randint(1, 6))
    category_ids = fields.One2many("openg2p.program.enrollment_category", "program_id")
    category_count = fields.Integer(compute="_compute_category_count", store=True)

    _sql_constraints = [
        (
            "program_date_greater",
            "check(date_end >= date_start)",
            "Error! program start-date must be lower than program end-date.",
        )
    ]

    @api.depends("category_ids")
    def _compute_category_count(self):
        for program in self:
            program.category_count = len(program.category_ids)

    @api.multi
    def action_activate(self):
        self.write({"state": "active"})

    @api.multi
    def action_done(self):
        self.env["openg2p.program.enrollment"].search(
            ("program_id", "in", self.ids), ("state", "in", ("open", "draft"))
        ).toggle_active()
        self.write({"state": "done"})
