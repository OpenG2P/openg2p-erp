# -*- coding: utf-8 -*-
from odoo import fields, models
from .odk import ODK
import logging

_logger = logging.getLogger(__name__)


class ODKSubmissions(models.Model):
    _name = "odk.submissions"
    _description = "ODK Form Submissions"
    _order = "submission_date desc"

    # Columns
    odk_submission_id = fields.Char(
        string="ODK Submission Instance ID", required=True, index=True, readonly=True
    )
    submission_date = fields.Datetime(
        string="Submission Date Time in ODK", required=True, readonly=True
    )
    odk_config_id = fields.Many2one(
        "odk.config", string="Configuration", required=True, readonly=True
    )
    submission_response = fields.Char(
        string="Form Response", required=True, readonly=True
    )
    odoo_corresponding_id = fields.Many2one(
        "openg2p.registration",
        string="OpenG2P Registration",
        help="Registration linked to the submission.",
        readonly=True,
    )
    odk_batch_id = fields.Char()

    regd_creation_status = fields.Boolean(default=False)