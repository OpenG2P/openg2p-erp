# -*- coding: utf-8 -*-
from datetime import date

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ProgramRegistration(models.Model):
    _name = 'openg2p.program.registration'
    _description = 'Program Registration'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'generic.mixin.no.unlink', 'openg2p.mixin.has_document']

    program_id = fields.Many2one(
        'openg2p.program',
        string='Program',
        index=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
        required=True
    )
    name = fields.Char(
        'Reference',
        required=False,
        readonly=True,
        copy=False,
        default='/'
    )
    active = fields.Boolean(default=True)
    beneficiary_id = fields.Many2one(
        'openg2p.beneficiary',
        string='Beneficiary',
        readonly=True,
        states={'draft': [('readonly', False)]},
        required=True
    )
    category_id = fields.Many2one(
        'openg2p.program.registration_category',
        string="Category",
        required=True,
        track_visibility='onchange'
    )
    date_start = fields.Date(
        'Registration Date',
        required=True,
        default=fields.Date.context_today,
        help="Start date of the program registration.",
        states={'draft': [('readonly', False)]},
        track_visibility='onchange'
    )
    date_end = fields.Date(
        'Registration End',
        help="End date of the program registration (if it's a fixed-term program registration).",
        track_visibility='onchange',
    )
    notes = fields.Text('Notes')
    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('open', 'Active'),
            ('close', 'Expired'),
            ('cancel', 'Cancelled')
        ],
        string='Status',
        group_expand='_expand_states',
        track_visibility='onchange',
        help='Status of registration',
        default='draft',
        readonly=True,
        states={'draft': [('readonly', False)]},  # we seem to need this to have our demo data change the state
    )
    company_id = fields.Many2one(
        'res.company',
        default=lambda self: self.env.user.company_id
    )
    currency_id = fields.Many2one(
        string="Currency",
        related='company_id.currency_id',
        readonly=True
    )

    def action_activate(self):
        self.write({'state': 'open'})

    @api.multi
    def toggle_active(self):
        for rec in self:
            if not rec.active and not rec.date_end:
                rec.date_end = fields.Date.today()
                if rec.state not in ('close', 'cancel'):
                    rec.state = 'close'
        super(ProgramRegistration, self).toggle_active()

    @api.model
    def create(self, vals):
        if vals.get('name', False) in ('/', False):
            vals['name'] = self.env['ir.sequence'].next_by_code('openg2p.program.registration.ref')
        return super(ProgramRegistration, self).create(vals)

    def _expand_states(self, states, domain, order):
        return [key for key, val in type(self).state.selection]

    @api.constrains('date_start', 'date_end', 'program_id')
    def _check_dates(self):
        for c in self:
            if c.date_end and c.date_start > c.date_end:
                raise ValidationError(
                    _('Program Registration start date must be earlier than program registration end date.'))

            if c.date_start > c.program_id.date_start:
                raise ValidationError(
                    _('Program Registration start date must not be earlier  than program\'s start date.'))

            if c.date_end and c.date_end > c.program_id.date_end:
                raise ValidationError(
                    _('Program Registration end date must be later than program end date.'))

    @api.model
    def update_state(self):
        self.search([
            ('state', '=', 'open'),
            ('date_end', '<=', fields.Date.to_string(date.today() + relativedelta(days=1))),  # more than a day expired
        ]).write({
            'state': 'close'
        })
        return True

    @api.multi
    def _track_subtype(self, init_values):
        self.ensure_one()
        if 'state' in init_values and self.state == 'close':
            return 'openg2p_program.mt_program_registration_close'
        return super(ProgramRegistration, self)._track_subtype(init_values)

    @api.constrains('program_id', 'state', 'beneficiary_id')
    def _check_concurrent_active_enrollment(self):
        """
        Let's ensure that we do not have a situation in which a beneficiary has multuple active enrollment to the same
        program
        """
        for i in self:
            domain = [
                ('beneficiary_id', '=', i.beneficiary_id.id),
                ('state', '=', 'open'),
                ('program_id', '=', i.program_id.id),
                ('id', '!=', i.id)
            ]
            if self.search_count(domain):
                raise ValidationError(
                    'Concurrent enrollments to the same program not allowed. \n'
                    'This beneficiary is already enrolled to this program!'
                    % i.beneficiary_id.name
                )
