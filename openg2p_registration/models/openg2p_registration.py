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


class Registration(models.Model):
    _name = "openg2p.registration"
    _description = "Registration"
    _order = "priority asc, id desc"
    _inherit = ["openg2p.beneficiary"]

    def _default_stage_id(self):
        ids = self.env['openg2p.registration.stage'].search([
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
    registered_date = fields.Datetime(
        "Registration Date",
        readonly=True,
        index=True
    )
    stage_id = fields.Many2one(
        'openg2p.registration.stage',
        'Stage',
        ondelete='restrict',
        track_visibility='onchange',
        copy=False,
        index=True,
        group_expand='_read_group_stage_ids',
        default=_default_stage_id
    )
    last_stage_id = fields.Many2one(
        'openg2p.registration.stage',
        "Last Stage",
        help="Stage of the registration before being in the current stage. Used for lost cases analysis."
    )
    categ_ids = fields.Many2many(
        'openg2p.registration.category',
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
        help="Beneficiary linked to the registration."
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
    stage_action = fields.Selection(
        [('create_beneficiary', 'Create Beneficiary')],
        related='stage_id.action',
        readonly=True
    )
    duplicate_beneficiaries_ids = fields.Many2many(
        "openg2p.beneficiary",
        string='Potential Duplicates'
    )
    identities = fields.One2many(
        "openg2p.registration.identity",
        'registration_id'
    )

    org_custom_field = fields.One2many(
        'openg2p.beneficiary.orgmap',
        'registration',
    )

    def _get_default_odk_map(self):
        return {
            'SubmissionDate': 'SubmissionDate',
            'start': 'start',
            'end': 'end',
            'Enter_Today_s_date': 'date',
            'Region': 'region',
            'District': 'state_id',
            'Chiefdom': 'chiefdom',
            'Town_Village': 'city',
            'School_Name': 'school_name',
            'EMIS_Number': 'emis_number',
            'Bank_Name': 'bank_name',
            'Account_Number': 'bank_account_number',
            'BBAN': 'bban',
            'GPS_Cordinates-Latitude': 'gps_coordinates_latitude',
            'GPS_Cordinates-Longitude': 'gps_coordinates_longitude',
            'GPS_Cordinates-Altitude': 'gps_coordinates_altitude',
            'GPS_Cordinates-Accuracy': 'gps_coordinates_accuracy',
            'Is_there_a_sign_post_ly_shows_school_name': 'is_there_a_sign_post_ly_shows_school_name',
            'Take_snapshot_of_sch_ly_shows_school_name': 'snapshot_of_sch_ly_shows_school_name',
            'Head_Teacher_Name': 'head_teacher_name',
            'Head_Teacher_Mobile_Number': 'head_teacher_mobile_number',
            'Is_the_Head_Teacher_Present': 'is_the_head_teacher_present',
            'Take_a_Picture_of_the_Head_Teacher': 'picture_of_the_head_teacher',
            'Name_of_Respondant': 'name',
            'Designation_of_Respondant': 'designation_of_respondant',
            'Mobile_Number_of_Respondant': 'mobile',
            'Is_the_School_Approved': 'is_the_school_approved',
            'Are_there_students_w_ility_in_this_School': 'are_there_students_w_ility_in_this_School',
            'Was_there_an_SMC_meeting_this_term': 'was_there_an_smc_meeting_this_term',
            'Take_picture_of_minu_page_with_the_date': 'picture_of_minu_page_with_the_date',
            'was_there_a_staff_me_teacher_performance': 'was_there_a_staff_me_teacher_performance',
            'Take_picture_of_minu_page_with_the_date_001': 'picture_of_minu_page_with_the_date',
            'Does_the_School_disp_u_see_this_displayed': 'does_the_school_disp_u_see_this_displayed',
            'Take_a_picture_of_the_displayed_summary': 'picture_of_the_displayed_summary',
            'Does_the_School_have_rrent_year_s_SDP_SIP': 'does_the_School_have_rrent_year_s_sdp_sip',
            'Take_a_picture_of_SD_page_with_the_date': 'picture_of_sd_page_with_the_date',
            'Does_the_school_keep_records_and_receipts': 'does_the_school_keep_records_and_receipts',
            'Take_a_picture_of_do_page_with_the_date': 'picture_of_do_page_with_the_date',
            'How_does_the_school_ds_received_from_PBF': 'how_does_the_school_ds_received_from_pbf',
            'Enrollment': 'enrollment',
            'Total_Pupils_enrolled_in_Class_1': 'total_pupils_enrolled_in_class_1',
            'Total_Pupils_enrolled_in_Class_2': 'total_pupils_enrolled_in_class_2',
            'Total_Pupils_enrolled_in_Class_3': 'total_pupils_enrolled_in_class_3',
            'Total_Pupils_enrolled_in_Class_4': 'total_pupils_enrolled_in_class_4',
            'Total_Pupils_enrolled_in_Class_5': 'total_pupils_enrolled_in_class_5',
            'Total_Pupils_enrolled_in_Class_6': 'total_pupils_enrolled_in_class_6',
            'Total_Enrollment_in_this_Level': 'total_enrollment_in_this_Level',
            'How_many_Classes_are_in_the_School': 'how_many_classes_are_in_the_school',
            'What_Class_is_this': 'what_class_is_this',
            'How_many_people_are_resent_in_this_class': 'how_many_people_are_resent_in_this_class',
            'Are_you_sure_you_cou_present_in_the_Class': 'are_you_sure_you_cou_present_in_the_Class',
            'Number_of_Pupils_wit_in_first_class_room': 'number_of_pupils_wit_in_first_class_room',
            'Please_take_a_Photo_Books_in_this_Class': 'photo_books_in_this_class',
            'How_many_Pupils_did_se_Books_Pen_Pencil': 'how_many_pupils_did_se_books_pen_pencil',
            'Enumerator_Now_look_lk_in_the_Class_Room': 'enumerator_now_look_lk_in_the_class_room',
            'Did_you_See_Chalk_an_rd_in_this_Classroom': 'did_you_see_chalk_an_rd_in_this_classroom',
            'Enumerator_Now_Ask_His_Her_LESSON_PLAN': 'enumerator_now_ask_his_her_lesson_plan',
            'Did_the_Teacher_show_HIS_HER_Lesson_Plan': 'did_the_teacher_show_his_her_lesson_plan',
            'Enumerator_randomly_n_the_last_two_weeks': 'enumerator_randomly_n_the_last_two_weeks',
            'From_your_Observatio_n_the_last_two_weeks': 'from_your_observatio_n_the_last_two_weeks',
            'This_is_the_Reading_e_following_criteria': 'this_is_the_reading_e_following_criteria',
            'Grade': 'grade',
            'How_many_Pupils_are_the_Assessment_with': 'how_many_pupils_are_the_assessment_with',
            'What_is_the_gender_of_this_pupil': 'gender_of_this_pupil',
            'How_do_you_rate_this_he_reading_Assesment': 'how_do_you_rate_this_he_reading_assesment',
            'Enumerator_Ask_the_y_Selected_Classroom': 'enumerator_ask_the_y_selected_classroom',
            'What_Class_is_this_001': 'what_class_is_this',
            'How_many_Pupils_are_present_this_Class': 'how_many_pupils_are_present_this_class',
            'Are_you_sure_you_cou_present_in_the_Class_001': 'are_you_sure_you_cou_present_in_the_class',
            'Number_of_students_w_s_in_First_Classroom': 'number_of_students_w_s_in_first_classroom',
            'Please_take_a_Photo_Books_in_this_Class_001': 'please_take_a_photo_books_in_this_class',
            'How_many_Pupils_did_se_Books_Pen_Pencil_001': 'how_many_pupils_did_se_books_pen_pencil',
            'Enumerator_Now_look_lk_in_the_Class_Room_001': 'enumerator_now_look_lk_in_the_classroom',
            'Did_you_See_Chalk_an_rd_in_this_Classroom_001': 'did_you_see_chalk_an_rd_in_this_classroom',
            'Enumerator_Now_Ask_His_Her_LESSON_PLAN_001': 'enumerator_now_ask_his_her_lesson_plan',
            'Did_the_Teacher_show_HIS_HER_Lesson_Plan_001': 'did_the_teacher_show_his_her_lesson_plan',
            'Enumerator_randomly_n_the_last_two_weeks_001': 'enumerator_randomly_n_the_last_two_weeks',
            'From_your_Observatio_n_the_last_two_weeks_001': 'from_your_observatio_n_the_last_two_weeks',
            'This_is_the_Reading_e_following_criteria_001': 'this_is_the_reading_e_following_criteria',
            'How_many_Pupils_are_the_Assessment_with_001': 'how_many_pupils_are_the_assessment_with',
            'What_is_the_gender_of_this_pupil_001': 'what_is_the_gender_of_this_pupil',
            'How_do_you_rate_this_he_reading_Assesment_001': 'how_do_you_rate_this_he_reading_assessment',
            'Attendance_in_Class_1_at_time_of_visit': 'attendance_in_Class_1_at_time_of_visit',
            'Attendance_in_Class_2_at_time_of_visit': 'attendance_in_Class_2_at_time_of_visit',
            'Attendance_in_Class_3_at_time_of_visit': 'attendance_in_Class_3_at_time_of_visit',
            'Attendance_in_Class_4_at_time_of_visit': 'attendance_in_Class_4_at_time_of_visit',
            'Attendance_in_Class_5_at_time_of_visit': 'attendance_in_Class_5_at_time_of_visit',
            'Attendance_in_Class_6_at_time_of_visit': 'attendance_in_Class_6_at_time_of_visit',
            'Total_Student_in_Att_ndance_at_the_School': 'total_student_in_attendance_at_the_school',
            'Total_Teachers_emplo_teach_in_this_School': 'total_teachers_emplo_teach_in_this_school',
            'Number_of_teachers_f_ooms_physical_count': 'number_of_teachers_f_ooms_physical_count',
            'Enumerator_Now_ask_Signed_FEEDBACK_FORM': 'enumerator_now_ask_signed_feedback_form',
            'Enumerator_Now_coun_by_the_head_teacher': 'enumerator_now_coun_by_the_head_teacher',
            'How_many_dated_and_s_forms_did_you_count': 'how_many_dated_and_s_forms_did_you_count',
            'Do_a_headcount_of_te_d_on_school_premises': 'do_a_headcount_of_te_d_on_school_premises',
            'Take_group_photo': 'group_photo',
            # '__version__': '__version__',
            # 'meta-instanceID': 'meta-instanceID',
            # 'KEY': 'KEY',
            # 'SubmitterID': 'SubmitterID',
            # 'SubmitterName': 'SubmitterName',
            # 'AttachmentsPresent': 'AttachmentsPresent',
            # 'AttachmentsExpected': 'AttachmentsExpected',
            # 'Status': 'Status',
        }

    def create_registration_from_odk(self, odk_data):
        regd = self.create({
            'firstname': '',
            'lastname': '',
            'street': '',
            'location_id': 1,
            'city': '',
            'state_id': 1,
            'gender': 'male',
        })
        id = regd.id
        print('SUB->REG', id)
        from datetime import datetime
        data = {}
        temp = {}
        for k, v in odk_data.items():
            if k.startswith('group'):
                for k2, v2 in v.items():
                    temp[k2] = v2
        odk_data = temp
        org_data = {}
        odk_map = odk_data['odk_map'] if 'odk_map' in odk_data.keys() else self._get_default_odk_map()
        format = '%Y-%m-%dT%H:%M:%SZ'
        for k, v in odk_data.items():
            if k in ['Status', 'AttachmentsExpected', 'AttachmentsPresent',
                     'SubmitterName', 'SubmitterID', 'KEY', 'meta-instanceID',
                     '__version__']:
                continue
            if k in odk_map.keys():
                k = odk_map[k]
            if hasattr(self, k):
                if k == 'partner_id':
                    res = self.env['res.partner'].search(
                        [('partner_id', '=', v)],
                        limit=1
                    )
                    if res:
                        data[k] = res.id
                elif k == 'registered_date':
                    data['registered_date'] = datetime.strptime(v, format)
                elif k == 'categ_ids':
                    res = self.env['categ_ids'].search(
                        [('categ_ids', '=', v)],
                        limit=1
                    )
                    if res:
                        data['categ_ids'] = res.ids
                elif k == 'company_id':
                    res = self.env['company_id'].search(
                        [('company_id', '=', v)],
                        limit=1
                    )
                    if res:
                        data['company_id'] = res.id
                elif k == 'user_id':
                    res = self.env['user_id'].search(
                        [('user_id', '=', v)],
                        limit=1
                    )
                    if res:
                        data['user_id'] = res.id
                elif k == 'priority':
                    if v in [i[0] for i in AVAILABLE_PRIORITIES]:
                        data['priority'] = v
                elif k == 'beneficiary_id':
                    res = self.env['openg2p.beneficiary'].search(
                        [('beneficiary_id', '=', id)],
                        limit=1
                    )
                    if res:
                        data['beneficiary_id'] = res.id
                elif k == 'identities':
                    for vi in v:
                        self.env['openg2p.registration.identity'].create({
                            'name': list(vi.keys())[0],
                            'type': list(vi.values())[0],
                            'registration_id': id,
                        })
                    res = self.env['openg2p.registration.identity'].search(
                        [('registration_id', '=', id)]
                    )
                    if res:
                        data['identities'] = res.ids
                elif k == 'state_id':
                    state = self.env['res.country.state'].search(
                        [('name', '=', v)]
                    )
                    if state:
                        data['state_id'] = state.id
                    # else:
                else:
                    if k not in ['description', 'color', 'beneficiary_name',
                                 'identity_national', 'identity_passport',
                                 'legend_blocked', 'legend_done', 'legend_normal']:
                        if k == 'name':
                            name_parts = v.split(' ')
                            data['firstname'] = name_parts[0]
                            if len(name_parts) > 1:
                                data['lastname'] = ' '.join(name_parts[1:])
                        else:
                            org_data.update({k: v})
                    else:
                        data[k] = v
            else:
                org_data.update({k: v})
        for k, v in org_data.items():
            self.env['openg2p.beneficiary.orgmap'].create({
                'field_name': k,
                'field_value': v or '',
                'registration': id,
            })
        # res = self.env['openg2p.beneficiary.orgmap'].search(
        #     [('registration', '=', id)]
        # )
        # if res:
        #     data['org_custom_field'] = res.ids
        # regd = self.search([('id', '=', id)])
        regd.write(data)
        return regd

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
        stage = self.env['openg2p.registration.stage'].browse(stage_id)
        if stage.fold:
            return {'value': {'date_closed': fields.datetime.now()}}
        return {'value': {'date_closed': False}}

    @api.model
    @api.multi
    def create(self, vals):
        if vals.get('location_id') and not self._context.get('default_location_id'):
            self = self.with_context(default_location_id=vals.get('location_id'))
        if vals.get('user_id'):
            vals['date_open'] = fields.Datetime.now()
        if 'stage_id' in vals:
            vals.update(self._onchange_stage_id_internal(vals.get('stage_id'))['value'])
        res = super(Registration, self.with_context(mail_create_nolog=True)).create(vals)
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
            for registration in self:
                vals['last_stage_id'] = registration.stage_id.id

                next_stage = self.env['openg2p.registration.stage'].browse(vals['stage_id'])
                if not registration.stage_id.fold and next_stage.fold and next_stage.sequence > 1 and registration.active:  # ending stage
                    if not registration.beneficiary_id:
                        raise UserError(_('You need to create beneficiary before moving registration to this stage.'))
                    if not registration.beneficiary_id.program_ids:
                        raise UserError(_('Beneficiary needs to be registerd into a program before moving registration'
                                          ' to this stage.'))

                if registration.stage_id.sequence > next_stage.sequence and registration.beneficiary_id:
                    raise UserError(_('You cannot move registration back as beneficiary already created.'))

                res = super(Registration, self).write(vals)
        else:
            res = super(Registration, self).write(vals)
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
            return 'openg2p_registration.mt_registration_registered'
        elif 'stage_id' in init_values and record.stage_id and record.stage_id.sequence <= 1:
            return 'openg2p_registration.mt_registration_new'
        elif 'stage_id' in init_values and record.stage_id and record.stage_id.sequence > 1:
            return 'openg2p_registration.mt_registration_stage_changed'
        return super(Registration, self)._track_subtype(init_values)

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
    def create_beneficiary_from_registration(self):
        """ Create an openg2p.beneficiary from the openg2p.registrations """
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

        self.write({'beneficiary_id': beneficiary.id, 'registered_date': fields.Datetime.now()})
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
    def archive_registration(self):
        for registration in self:
            if registration.beneficiary_id:
                raise UserError(_("You can not archive an registration for which a beneficiary has been created"))
        self.write({'active': False})

    @api.multi
    def reset_registration(self):
        """ Reinsert the registration into the registration pipe in the first stage"""
        if self.filtered('beneficiary_id'):
            raise UserError(_("You can not reset an registration for which a beneficiary has been created"))
        default_stage_id = self._default_stage_id()
        self.write({'active': True, 'stage_id': default_stage_id})
