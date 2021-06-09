# -*- coding: utf-8 -*-
# Copyright 2020 OpenG2P (https://openg2p.org)
# @author: Salton Massally <saltonmassally@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import json
import logging
from datetime import date, datetime

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.addons.queue_job.job import job, related_action
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)
BATCH_SIZE = 500


class NewBatch(models.Model):
    _name = 'openg2p.disbursement.new.batch'
    _description = 'Disbursement Batch'
    _inherit = ['generic.mixin.no.unlink',
                'mail.thread', 'openg2p.mixin.has_document']
    allow_unlink_domain = [('state', '=', 'draft')]

    name = fields.Char(
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
        track_visibility='onchange'
    )
    program_id = fields.Many2one(
        'openg2p.program',
        required=True,
        readonly=True,
        index=True,
        states={'draft': [('readonly', False)]},
        track_visibility='onchange'
    )
    state = fields.Selection(
        [
            ('draft', 'Drafting'),
            ('confirm', 'Confirmed'),
            ('pending', 'Pending'),
            ('paymentstatus', 'Transaction Status')
        ],
        string='Status',
        # index=True,
        readonly=True,
        # copy=False,
        default='draft',
        # track_visibility='onchange'
    )
    date_start = fields.Date(
        string='Date From',
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
        default=lambda self: fields.Date.to_string(
            date.today().replace(day=1)),
        track_visibility='onchange'
    )
    date_end = fields.Date(
        string='Date To',
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
        default=lambda self: fields.Date.to_string(
            (datetime.now() + relativedelta(months=+1, day=1, days=-1)).date()),
        track_visibility='onchange'
    )
    # job_batch_id = fields.Many2one(
    #     'queue.job.batch',
    #     index=True,
    #     string='Background Job'
    # )
    # job_completeness = fields.Float(
    #     compute="_compute_job_stat",
    #     string='Progress',
    #     compute_sudo=True
    # )
    # job_failures = fields.Float(
    #     compute="_compute_job_stat",
    #     string='Failures',
    #     compute_sudo=True
    # )
    # job_failed_count = fields.Float(
    #     related='job_batch_id.failed_job_count',
    #     related_sudo=True
    # )
    # job_state = fields.Selection(
    #     [
    #         ('draft', 'Draft'),
    #         ('enqueued', 'Enqueued'),
    #         ('progress', 'In Progress'),
    #         ('finished', 'Finished')
    #     ],
    #     related='job_batch_id.state',
    #     related_sudo=True,
    #     readonly=True
    # )
    company_id = fields.Many2one(
        'res.company',
        'Company',
        required=True,
        readonly=True,
        ondelete='restrict',
        default=lambda self: self.env.user.company_id
    )
    currency_id = fields.Many2one(
        string="Currency",
        related='company_id.currency_id',
        readonly=True,
        store=True
    )
    # exception_count = fields.Integer(
    #     compute='_compute_exception_count'
    # )
    # intended_beneficiaries = fields.Text()

    # states helper fields
    # can_confirm = fields.Boolean(
    #     compute='_compute_can_confirm',
    # )
    # can_generate = fields.Boolean(
    #     compute='_compute_can_generate',
    # )
    # can_approve = fields.Boolean(
    #     compute='_compute_can_approve',
    # )
    # can_disburse = fields.Boolean(
    #     compute='_compute_can_disburse',
    # )
    # can_close = fields.Boolean(
    #     compute='_compute_can_close',
    # )
    # can_cancel = fields.Boolean(
    #     compute='_compute_can_cancel',
    # )
    # is_approved = fields.Boolean(
    #     compute='_compute_state_approved',
    # )
    # has_checklist_draft = fields.Boolean()
    # note = fields.Text()
