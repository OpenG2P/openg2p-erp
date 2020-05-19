# -*- coding: utf-8 -*-
from odoo.addons.openg2p.services.matching_service import MATCH_MODE_COMPREHENSIVE, MATCH_MODE_NORMAL

from odoo.addons.queue_job.job import job
from odoo import api, fields, models, SUPERUSER_ID
from odoo.exceptions import UserError, ValidationError
from odoo.tools.translate import _

AVAILABLE_PRIORITIES = [
    ('0', 'Urgent'),
    ('1', 'High'),
    ('2', 'Normal'),
    ('3', 'Low')
]


class Applicant(models.Model):
    _name = "openg2p.applicant"
    _description = "Application"
    _order = "priority asc, id desc"
    _inherit = ["openg2p.beneficiary"]

    def _default_stage_id(self):
        ids = self.env['openg2p.enrollment.stage'].search([
            ('fold', '=', False)
        ], order='sequence asc', limit=1).ids
        if ids:
            return ids[0]
        return False

    def _default_company_id(self):
        return self.env['res.company']._company_default_get()

    partner_id = fields.Many2one(
        'res.partner',
        required=False,
    )

    description = fields.Text()
    create_date = fields.Datetime(
        "Creation Date",
        readonly=True,
        index=True,
        default=fields.Datetime.now
    )
    enrolled_date = fields.Datetime(
        "Enrolled Date",
        readonly=True,
        index=True
    )
    stage_id = fields.Many2one(
        'openg2p.enrollment.stage',
        'Stage',
        ondelete='restrict',
        track_visibility='onchange',
        copy=False,
        index=True,
        group_expand='_read_group_stage_ids',
        default=_default_stage_id
    )
    last_stage_id = fields.Many2one(
        'openg2p.enrollment.stage',
        "Last Stage",
        help="Stage of the applicant before being in the current stage. Used for lost cases analysis."
    )
    categ_ids = fields.Many2many(
        'openg2p.applicant.category',
        string="Tags"
    )
    company_id = fields.Many2one(
        'res.company',
        "Company",
        default=_default_company_id
    )
    user_id = fields.Many2one(
        'res.users',
        "Responsible",
        track_visibility="onchange",
        default=lambda self: self.env.uid
    )
    date_closed = fields.Datetime(
        "Closed",
        readonly=True,
        index=True
    )
    date_open = fields.Datetime(
        "Assigned",
        readonly=True,
        index=True
    )
    date_last_stage_update = fields.Datetime(
        "Last Stage Update",
        index=True,
        default=fields.Datetime.now
    )
    priority = fields.Selection(
        AVAILABLE_PRIORITIES,
        default='1'
    )
    day_open = fields.Float(
        compute='_compute_day',
        string="Days to Open"
    )
    day_close = fields.Float(
        compute='_compute_day',
        string="Days to Close"
    )
    delay_close = fields.Float(
        compute="_compute_day",
        string='Delay to Close',
        readonly=True,
        group_operator="avg",
        help="Number of days to close",
        store=True
    )
    color = fields.Integer(
        "Color Index",
        default=0
    )
    beneficiary_name = fields.Char(
        related="beneficiary_id.name",
        store=True,
        readonly=True
    )
    beneficiary_id = fields.Many2one(
        'openg2p.beneficiary',
        string="Beneficiary",
        track_visibility="onchange",
        help="Beneficiary linked to the applicant."
    )
    identity_national = fields.Char(
        string='National ID',
        track_visibility='onchange',
    )
    identity_passport = fields.Char(
        string='Passport No',
        track_visibility='onchange',
    )
    kanban_state = fields.Selection(
        [
            ('normal', 'Grey'),
            ('done', 'Green'),
            ('blocked', 'Red')
        ],
        string='Kanban State',
        copy=False,
        default='normal',
        required=True
    )
    legend_blocked = fields.Char(
        related='stage_id.legend_blocked',
        string='Kanban Blocked',
        readonly=False
    )
    legend_done = fields.Char(
        related='stage_id.legend_done',
        string='Kanban Valid',
        readonly=False
    )
    legend_normal = fields.Char(
        related='stage_id.legend_normal',
        string='Kanban Ongoing',
        readonly=False
    )
    can_create_beneficiary = fields.Boolean(
        related='stage_id.can_create_beneficiary',
        readonly=True
    )
    duplicate_beneficiaries_ids = fields.Many2many(
        "openg2p.beneficiary"
    )
    identities = fields.One2many(
        "openg2p.applicant.identity",
        'applicant_id'
    )
    reject_reason_id = fields.Many2one(
        'openg2p.applicant.reject.reason',
        "Reason"
    )

    @api.depends('date_open', 'date_closed')
    @api.one
    def _compute_day(self):
        if self.date_open:
            date_create = self.create_date
            date_open = self.date_open
            self.day_open = (date_open - date_create).total_seconds() / (24.0 * 3600)

        if self.date_closed:
            date_create = self.create_date
            date_closed = self.date_closed
            self.day_close = (date_closed - date_create).total_seconds() / (24.0 * 3600)
            self.delay_close = self.day_close - self.day_open

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        stage_ids = stages._search([], order=order, access_rights_uid=SUPERUSER_ID)
        return stages.browse(stage_ids)

    @api.onchange('stage_id')
    def onchange_stage_id(self):
        vals = self._onchange_stage_id_internal(self.stage_id.id)
        if vals['value'].get('date_closed'):
            self.date_closed = vals['value']['date_closed']

    def _onchange_stage_id_internal(self, stage_id):
        if not stage_id:
            return {'value': {}}
        stage = self.env['openg2p.enrollment.stage'].browse(stage_id)
        if stage.fold:
            return {'value': {'date_closed': fields.datetime.now()}}
        return {'value': {'date_closed': False}}

    @api.model
    def create(self, vals):
        if vals.get('location_id') and not self._context.get('default_location_id'):
            self = self.with_context(default_location_id=vals.get('location_id'))
        if vals.get('user_id'):
            vals['date_open'] = fields.Datetime.now()
        if 'stage_id' in vals:
            vals.update(self._onchange_stage_id_internal(vals.get('stage_id'))['value'])
        res = super(Applicant, self.with_context(mail_create_nolog=True)).create(vals)
        res.sudo().with_delay().ensure_unique(mode=MATCH_MODE_COMPREHENSIVE)  # let's queue uniqueness check
        return res

    @api.multi
    def write(self, vals):
        # user_id change: update date_open
        if vals.get('user_id'):
            vals['date_open'] = fields.Datetime.now()
        # stage_id: track last stage before update
        if 'stage_id' in vals:
            vals['date_last_stage_update'] = fields.Datetime.now()
            vals.update(self._onchange_stage_id_internal(vals.get('stage_id'))['value'])
            if 'kanban_state' not in vals:
                vals['kanban_state'] = 'normal'
            for applicant in self:
                vals['last_stage_id'] = applicant.stage_id.id

                next_stage = self.env['openg2p.enrollment.stage'].browse(vals['stage_id'])
                if not applicant.stage_id.fold and next_stage.fold and next_stage.sequence > 1 and applicant.active \
                        and not applicant.beneficiary_id:  # ending stage
                    raise UserError(_('You need to create beneficiary before moving applicant to this stage.'))

                if applicant.stage_id.sequence > next_stage.sequence and applicant.beneficiary_id:
                    raise UserError(_('You cannot move application back as beneficiary already created.'))

                res = super(Applicant, self).write(vals)
        else:
            res = super(Applicant, self).write(vals)
        return res

    @api.multi
    def action_get_created_beneficiary(self):
        self.ensure_one()
        context = dict(self.env.context)
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'openg2p.beneficiary',
            'res_id': self.mapped('beneficiary_id').ids[0],
            'context': context,
        }

    @api.multi
    def _track_subtype(self, init_values):
        record = self[0]
        if 'beneficiary_id' in init_values and record.beneficiary_id and record.beneficiary_id.active:
            return 'openg2p_enrollment.mt_applicant_enrolled'
        elif 'stage_id' in init_values and record.stage_id and record.stage_id.sequence <= 1:
            return 'openg2p_enrollment.mt_applicant_new'
        elif 'stage_id' in init_values and record.stage_id and record.stage_id.sequence > 1:
            return 'openg2p_enrollment.mt_applicant_stage_changed'
        return super(Applicant, self)._track_subtype(init_values)

    def cron_check_uniqueness(self):
        self.search([('beneficiary_id', '=', None), ('duplicate_beneficiaries_ids', '=', None)]) \
            .sudo().with_delay().ensure_unique(MATCH_MODE_COMPREHENSIVE)

    @api.multi
    def get_identities(self):
        self.ensure_one()
        return [(i.type, i.name) for i in self.identities]

    @job
    def ensure_unique(self, mode):
        for rec in self:
            self.env['openg2p.beneficiary'].matches(rec, mode, stop_on_first=False)

    @api.multi
    def create_beneficiary_from_applicant(self):
        """ Create an openg2p.beneficiary from the openg2p.applicants """
        self.ensure_one()

        if not self.duplicate_beneficiaries_ids:  # last chance to make sure no duplicates
            self.ensure_unique(mode=MATCH_MODE_COMPREHENSIVE)

        if self.duplicate_beneficiaries_ids:  # TODO ability to force create if maanger... pass via context
            raise ValidationError(_("Potential duplicates exists for this record and so can not be added"))

        data = {
            'firstname': self.firstname,
            'lastname': self.lastname,
            'othernames': self.othernames,
            'location_id': self.location_id.id,
            'street': self.street,
            'street2': self.street2,
            'city': self.city,
            'state_id': self.state_id.id,
            'zip': self.zip,
            'country_id': self.country_id.id,
            'phone': self.phone,
            'mobile': self.mobile,
            'email': self.email,
            'title': self.title.id,
            'lang': self.lang,
            'gender': self.gender,
            'birthday': self.birthday,
            'image': self.image,
            'marital': self.marital,
            'national_id': self.identity_national,
            'passport_id': self.identity_passport,
            'emergency_contact': self.emergency_contact,
            'emergency_phone': self.emergency_phone
        }
        beneficiary = self.env['openg2p.beneficiary'].create(data)

        for code, number in self.get_identities():
            category = self.env['openg2p.beneficiary.id_category'].search([('type', '=', code)])
            self.env['openg2p.beneficiary.id_number'].create({
                'category_id': category.id,
                'name': number,
                'beneficiary_id': beneficiary.id
            })

        self.write({'beneficiary_id': beneficiary.id, 'enrolled_date': fields.Datetime.now()})
        context = dict(self.env.context)
        context['form_view_initial_mode'] = 'edit'
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'openg2p.beneficiary',
            'res_id': beneficiary.id,
            'context': context
        }

    @api.multi
    def archive_applicant(self):
        for applicant in self:
            if applicant.beneficiary_id:
                raise UserError(_("You can not archive an application for which a beneficiary has been created"))
        [reject_reason_action] = self.env.ref('openg2p_enrollment.action_add_reject_reason').read()
        return reject_reason_action

    @api.multi
    def reset_applicant(self):
        """ Reinsert the applicant into the enrollment pipe in the first stage"""
        if self.filtered('beneficiary_id'):
            raise UserError(_("You can not reset an application for which a beneficiary has been created"))
        default_stage_id = self._default_stage_id()
        self.write({'active': True, 'stage_id': default_stage_id})
