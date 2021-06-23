# -*- coding: utf-8 -*-
from odoo.addons.queue_job.job import job
from odoo import api, fields, models


class Beneficiary(models.Model):
    _inherit = "openg2p.beneficiary"
    _description = "Beneficiary"

    program_ids = fields.Many2many(
        "openg2p.program",
        string="Active Programs",
        help="Active programs enrolled to",
        readonly=True,
        track_visibility="onchange",
        compute="_compute_active_programs",
        store=True,
    )
    program_enrollment_ids = fields.One2many(
        "openg2p.program.enrollment",
        "beneficiary_id",
        string="Enrollment History",
        track_visibility="onchange",
    )
    program_enrollments_count = fields.Integer(
        compute="_compute_program_enrollments_count", string="Enrollment Count"
    )

    @api.multi
    @job
    def program_enroll(
        self,
        program_id,
        category_id,
        date_start=fields.Date.today(),
        confirm=False,
        raise_error=True,
    ):
        # TODO smarter way to check and skip or notify if enrollment exists now it just fails + use savepoints
        regs = self.env["openg2p.program.enrollment"]
        for rec in self:
            regs += self.env["openg2p.program.enrollment"].create(
                {
                    "program_id": program_id,
                    "beneficiary_id": rec.id,
                    "category_id": category_id,
                    "date_start": date_start,
                }
            )
        if confirm:
            regs.action_activate()

    def _compute_program_enrollments_count(self):
        # read_group as sudo, since program enrollment count is displayed on form view
        program_enrollment_data = (
            self.env["openg2p.program.enrollment"]
            .sudo()
            .read_group(
                [("beneficiary_id", "in", self.ids)],
                ["beneficiary_id"],
                ["beneficiary_id"],
            )
        )
        result = dict(
            (data["beneficiary_id"][0], data["beneficiary_id_count"])
            for data in program_enrollment_data
        )
        for beneficiary in self:
            beneficiary.program_enrollments_count = result.get(beneficiary.id, 0)

    @api.multi
    @api.depends("program_enrollment_ids", "program_enrollment_ids.state")
    def _compute_active_programs(self):
        for record in self:
            record.program_ids = record.program_enrollment_ids.filtered(
                lambda i: i.state == "open"
            ).mapped("program_id.id")
