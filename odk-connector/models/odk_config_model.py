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
        string="ODK User Email",
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
