# -*- coding: utf-8 -*-

from odoo import fields, models


class ApplicantRejectReason(models.Model):

    _name = "openg2p.applicant.reject.reason"
    _description = "Application Reject Reason"

    name = fields.Char('Reason', required=1)
    desc = fields.Text('Description')