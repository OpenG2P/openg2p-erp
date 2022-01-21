# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ODKConfig(models.Model):
    _name = "odk.config"
    _description = "ODK Form Configuration"
    _order = "id"

    # Columns
    form_name = fields.Char(
        string="Form Name",
        required=True,
    )
    odk_endpoint = fields.Char(
        string="ODK Base URL",
        required=True,
        # readonly=True
    )
    odk_project_id = fields.Integer(
        string="ODK Project ID",
        required=True,
        # readonly=True
    )
    odk_form_id = fields.Char(
        string="ODK Form ID",
        required=True,
        # readonly=True
    )
    odk_email = fields.Char(
        string="ODK User EMail",
        required=True,
        # readonly=True
    )
    odk_password = fields.Char(
        string="ODK User Password",
        required=True,
        # readonly=True
    )
    is_active = fields.Boolean(string="Active", default=False)
    odk_last_sync_date = fields.Datetime(
        string="Last Sync Date with ODK", readonly=True
    )
    odk_submissions_count = fields.Integer(
        string="Submissions Count", readonly=True, default=0
    )
    program_id = fields.Many2one(
        "openg2p.program",
        help="Active programs enrolled to",
        store=True,
        required=True,
    )
    program_enroll_date = fields.Date(
        "Program Enrollment Date", default=fields.Date.today()
    )

    @api.multi
    def odk_button_update_form_submissions(self):
        self.call_submission()

    # Method executed by cron job to fetch submissions
    def cron_update_all_active_forms(self):
        configs = self.search([("is_active", "=", True)])
        configs.odk_button_update_all_form_submissions()
        return True

    # Method called by button to fetch submissions for all forms
    def odk_button_update_all_form_submissions(self):
        for config in self:
            print("Config: ", config.form_name)
            config.call_submission()

    # Method calling submissions call to fetch data
    def call_submission(self):
        submissions_obj = self.env["odk.submissions"]
        regd_ids = submissions_obj.update_submissions(self)
        self.env["openg2p.process"].handle_tasks(
            [
                ("task_subtype_odk_pull", self.id),
                ("task_subtype_regd_create", regd_ids),
            ]
        )
        print("Call Submission ends")

    def write(self, vals):
        res = super().write(vals)
        if self.program_enroll_date > self.program_id.date_start:
            raise ValidationError(
                "Program Enrollment start date must not be earlier  than program's start date."
            )
        return res

    @api.model
    def create(self, vals_list):
        res = super().create(vals_list)
        if res.program_enroll_date > res.program_id.date_start:
            raise ValidationError(
                "Program Enrollment start date must not be earlier  than program's start date."
            )
        return res
