# -*- coding: utf-8 -*-
from odoo.addons.openg2p.services.matching_service import (
    MATCH_MODE_COMPREHENSIVE,
    MATCH_MODE_NORMAL,
)

from odoo.addons.queue_job.job import job

from odoo import api, fields, models, SUPERUSER_ID
from odoo.exceptions import UserError, ValidationError
from odoo.tools.translate import _

AVAILABLE_PRIORITIES = [("0", "Urgent"), ("1", "High"), ("2", "Normal"), ("3", "Low")]


class Registration(models.Model):
    _name = "openg2p.registration"
    _description = "Registration"
    _order = "priority asc, id desc"
    _inherit = ["openg2p.beneficiary"]

    def _default_stage_id(self):
        ids = (
            self.env["openg2p.registration.stage"]
            .search([("fold", "=", False)], order="sequence asc", limit=1)
            .ids
        )
        if ids:
            return ids[0]
        return False

    def _default_company_id(self):
        return self.env["res.company"]._company_default_get()

    partner_id = fields.Many2one(
        "res.partner",
        required=False,
    )
    description = fields.Text()
    create_date = fields.Datetime(
        "Creation Date", readonly=True, index=True, default=fields.Datetime.now
    )
    registered_date = fields.Datetime("Registration Date", readonly=True, index=True)
    stage_id = fields.Many2one(
        "openg2p.registration.stage",
        "Stage",
        ondelete="restrict",
        track_visibility="onchange",
        copy=False,
        index=True,
        group_expand="_read_group_stage_ids",
        default=_default_stage_id,
    )
    last_stage_id = fields.Many2one(
        "openg2p.registration.stage",
        "Last Stage",
        help="Stage of the registration before being in the current stage. Used for lost cases analysis.",
    )
    categ_ids = fields.Many2many("openg2p.registration.category", string="Tags")
    company_id = fields.Many2one("res.company", "Company", default=_default_company_id)
    user_id = fields.Many2one(
        "res.users",
        "Responsible",
        track_visibility="onchange",
        default=lambda self: self.env.uid,
    )
    date_closed = fields.Datetime("Closed", readonly=True, index=True)
    date_open = fields.Datetime("Assigned", readonly=True, index=True)
    date_last_stage_update = fields.Datetime(
        "Last Stage Update", index=True, default=fields.Datetime.now
    )
    priority = fields.Selection(AVAILABLE_PRIORITIES, default="1")
    day_open = fields.Float(compute="_compute_day", string="Days to Open")
    day_close = fields.Float(compute="_compute_day", string="Days to Close")
    delay_close = fields.Float(
        compute="_compute_day",
        string="Delay to Close",
        readonly=True,
        group_operator="avg",
        help="Number of days to close",
        store=True,
    )
    color = fields.Integer("Color Index", default=0)
    beneficiary_name = fields.Char(
        related="beneficiary_id.name", store=True, readonly=True
    )
    beneficiary_id = fields.Many2one(
        "openg2p.beneficiary",
        string="Beneficiary",
        track_visibility="onchange",
        help="Beneficiary linked to the registration.",
    )
    identity_national = fields.Char(
        string="National ID",
        track_visibility="onchange",
    )
    identity_passport = fields.Char(
        string="Passport No",
        track_visibility="onchange",
    )
    kanban_state = fields.Selection(
        [("normal", "Grey"), ("done", "Green"), ("blocked", "Red")],
        string="Kanban State",
        copy=False,
        default="normal",
        required=True,
    )
    legend_blocked = fields.Char(
        related="stage_id.legend_blocked", string="Kanban Blocked", readonly=False
    )
    legend_done = fields.Char(
        related="stage_id.legend_done", string="Kanban Valid", readonly=False
    )
    legend_normal = fields.Char(
        related="stage_id.legend_normal", string="Kanban Ongoing", readonly=False
    )
    stage_action = fields.Selection(
        [("create_beneficiary", "Create Beneficiary")],
        related="stage_id.action",
        readonly=True,
    )
    duplicate_beneficiaries_ids = fields.Many2many(
        "openg2p.beneficiary", string="Potential Duplicates"
    )
    identities = fields.One2many("openg2p.registration.identity", "registration_id")

    org_custom_field = fields.One2many(
        "openg2p.registration.orgmap",
        "regd_id",
    )

    # example for filtering on org custom fields
    attendance = fields.Integer(
        string="Attendance",
        store=False,
        required=False,
        compute="_compute_att",
        search="_search_att",
    )

    error_verification = fields.Selection(
        string="Error in Verification",
        selection=[
            ("none", "None"),
            ("error_name", "Error in name"),
            ("error_addr", "Error in address"),
        ],
        default="none",
    )

    # example for filtering on org custom fields
    def _search_att(self, operator, val2):
        res = []
        regds = self.env["openg2p.registration"].search([])
        for rec in regds:
            att = self.env["openg2p.registration.orgmap"].search(
                [
                    "&",
                    ("regd_id", "=", rec.id),
                    ("field_name", "=", "total_student_in_attendance_at_the_school"),
                ]
            )
            if not att:
                continue
            try:
                val = int(att.field_value)
            except BaseException as e:
                continue
            if operator == ">":
                if val > val2:
                    res.append(rec)
            elif operator == "<":
                if val < val2:
                    res.append(rec)
            elif operator == "=":
                if val == val2:
                    res.append(rec)
            elif operator == "!=":
                if val != val2:
                    res.append(rec)
            elif operator == ">=":
                if val >= val2:
                    res.append(rec)
            elif operator == "<=":
                if val <= val2:
                    res.append(rec)
        return [("id", "in", [rec.id for rec in res])]

    # example for filtering on org custom fields
    @api.depends("org_custom_field")
    def _compute_att(self):
        for rec in self:
            att = self.env["openg2p.registration.orgmap"].search(
                [
                    "&",
                    ("regd_id", "=", rec.id),
                    ("field_name", "=", "total_student_in_attendance_at_the_school"),
                ]
            )
            try:
                rec.attendance = int(att.field_value) if att else 0
            except BaseException as e:
                rec.attendance = 0

    def _get_default_odk_map(self):
        from .openg2p_submission_registration_map import odk_map_data

        return odk_map_data

    def create_registration_from_odk(self, odk_data):
        regd = self.create(
            {
                "firstname": "",
                "lastname": "",
                "street": "",
                "location_id": 1,
                "city": "",
                "state_id": 1,
                "gender": "male",
            }
        )
        id = regd.id
        from datetime import datetime

        data = {}
        temp = {}
        odk_map = (
            odk_data["odk_map"]
            if "odk_map" in odk_data.keys()
            else self._get_default_odk_map()
        )
        for k, v in odk_data.items():
            if k.startswith("group"):
                for k2, v2 in v.items():
                    if k2 in odk_map.keys():
                        k2 = odk_map[k2]
                    temp[k2] = v2
        odk_data = temp
        org_data = {}
        format = "%Y-%m-%dT%H:%M:%SZ"
        for k, v in odk_data.items():
            try:
                if k in [
                    "Status",
                    "AttachmentsExpected",
                    "AttachmentsPresent",
                    "SubmitterName",
                    "SubmitterID",
                    "KEY",
                    "meta-instanceID",
                    "__version__",
                    "bank_name",
                ]:
                    continue
                if k == "bank_account_number":
                    if len(v or "") != 0:
                        data["bank_account_number"] = odk_data["bank_account_number"]
                        res = self.env["res.partner.bank"].search(
                            [("acc_number", "=", str(odk_data["bank_account_number"]))]
                        )
                        if res:
                            raise Exception("Duplicate Bank Account Number!")
                        if not res:
                            res = self.env["res.partner.bank"].create(
                                {
                                    "acc_number": odk_data["bank_account_number"],
                                    "partner_id": self.env.ref("base.main_partner").id,
                                }
                            )
                        data["bank_account_id"] = res.id
                elif k == "phone":
                    data["phone"] = odk_data["phone"]
                elif hasattr(self, k):
                    if k == "partner_id":
                        res = self.env["res.partner"].search(
                            [("partner_id", "=", v)], limit=1
                        )
                        if res:
                            data[k] = res.id
                    elif k == "registered_date":
                        data["registered_date"] = datetime.strptime(v, format)
                    elif k == "categ_ids":
                        res = self.env["categ_ids"].search(
                            [("categ_ids", "=", v)], limit=1
                        )
                        if res:
                            data["categ_ids"] = res.ids
                    elif k == "company_id":
                        res = self.env["company_id"].search(
                            [("company_id", "=", v)], limit=1
                        )
                        if res:
                            data["company_id"] = res.id
                    elif k == "user_id":
                        res = self.env["user_id"].search([("user_id", "=", v)], limit=1)
                        if res:
                            data["user_id"] = res.id
                    elif k == "priority":
                        if v in [i[0] for i in AVAILABLE_PRIORITIES]:
                            data["priority"] = v
                    elif k == "beneficiary_id":
                        res = self.env["openg2p.beneficiary"].search(
                            [("beneficiary_id", "=", id)], limit=1
                        )
                        if res:
                            data["beneficiary_id"] = res.id
                    elif k == "identities":
                        for vi in v:
                            self.env["openg2p.registration.identity"].create(
                                {
                                    "name": list(vi.keys())[0],
                                    "type": list(vi.values())[0],
                                    "registration_id": id,
                                }
                            )
                        res = self.env["openg2p.registration.identity"].search(
                            [("registration_id", "=", id)]
                        )
                        if res:
                            data["identities"] = res.ids
                    elif k == "state_id":
                        state = self.env["res.country.state"].search([("name", "=", v)])
                        if state:
                            data["state_id"] = state.id
                    else:
                        if k == "name":
                            if v is None:
                                continue
                            name_parts = v.split(" ")
                            data["firstname"] = name_parts[0]
                            if len(name_parts) > 1:
                                data["lastname"] = " ".join(name_parts[1:])
                        else:
                            org_data.update({k: v})

                else:
                    org_data.update({k: v})
            except Exception as e:
                print(e)
        for k, v in org_data.items():
            self.env["openg2p.registration.orgmap"].create(
                {
                    "field_name": k,
                    "field_value": v or "",
                    "regd_id": id,
                }
            )
        regd.write(data)
        return regd

    @api.depends("date_open", "date_closed")
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

    @api.onchange("stage_id")
    def onchange_stage_id(self):
        vals = self._onchange_stage_id_internal(self.stage_id.id)
        if vals["value"].get("date_closed"):
            self.date_closed = vals["value"]["date_closed"]

    def _onchange_stage_id_internal(self, stage_id):
        if not stage_id:
            return {"value": {}}
        stage = self.env["openg2p.registration.stage"].browse(stage_id)
        if stage.fold:
            return {"value": {"date_closed": fields.datetime.now()}}
        return {"value": {"date_closed": False}}

    @api.model
    @api.multi
    def create(self, vals):
        if vals.get("location_id") and not self._context.get("default_location_id"):
            self = self.with_context(default_location_id=vals.get("location_id"))
        if vals.get("user_id"):
            vals["date_open"] = fields.Datetime.now()
        if "stage_id" in vals:
            vals.update(self._onchange_stage_id_internal(vals.get("stage_id"))["value"])
        res = super(Registration, self.with_context(mail_create_nolog=True)).create(
            vals
        )
        res.sudo().with_delay().ensure_unique(
            mode=MATCH_MODE_COMPREHENSIVE
        )  # let's queue uniqueness check
        return res

    @api.multi
    def write(self, vals):
        # user_id change: update date_open
        if vals.get("user_id"):
            vals["date_open"] = fields.Datetime.now()
        # stage_id: track last stage before update
        if "stage_id" in vals:
            vals["date_last_stage_update"] = fields.Datetime.now()
            vals.update(self._onchange_stage_id_internal(vals.get("stage_id"))["value"])
            if "kanban_state" not in vals:
                vals["kanban_state"] = "normal"
            for registration in self:
                vals["last_stage_id"] = registration.stage_id.id

                next_stage = self.env["openg2p.registration.stage"].browse(
                    vals["stage_id"]
                )
                if (
                    not registration.stage_id.fold
                    and next_stage.fold
                    and next_stage.sequence > 1
                    and registration.active
                ):  # ending stage
                    if not registration.beneficiary_id:
                        raise UserError(
                            _(
                                "You need to create beneficiary before moving registration to this stage."
                            )
                        )
                    if not registration.beneficiary_id.program_ids:
                        raise UserError(
                            _(
                                "Beneficiary needs to be registerd into a program before moving registration"
                                " to this stage."
                            )
                        )

                if (
                    registration.stage_id.sequence > next_stage.sequence
                    and registration.beneficiary_id
                ):
                    raise UserError(
                        _(
                            "You cannot move registration back as beneficiary already created."
                        )
                    )

                res = super(Registration, self).write(vals)
        else:
            res = super(Registration, self).write(vals)
        return res

    @api.multi
    def action_get_created_beneficiary(self):
        self.ensure_one()
        context = dict(self.env.context)
        return {
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "form",
            "res_model": "openg2p.beneficiary",
            "res_id": self.mapped("beneficiary_id").ids[0],
            "context": context,
        }

    @api.multi
    def _track_subtype(self, init_values):
        record = self[0]
        if (
            "beneficiary_id" in init_values
            and record.beneficiary_id
            and record.beneficiary_id.active
        ):
            return "openg2p_registration.mt_registration_registered"
        elif (
            "stage_id" in init_values
            and record.stage_id
            and record.stage_id.sequence <= 1
        ):
            return "openg2p_registration.mt_registration_new"
        elif (
            "stage_id" in init_values
            and record.stage_id
            and record.stage_id.sequence > 1
        ):
            return "openg2p_registration.mt_registration_stage_changed"
        return super(Registration, self)._track_subtype(init_values)

    def cron_check_uniqueness(self):
        self.search(
            [("beneficiary_id", "=", None), ("duplicate_beneficiaries_ids", "=", None)]
        ).sudo().with_delay().ensure_unique(MATCH_MODE_COMPREHENSIVE)

    @api.multi
    def get_identities(self):
        self.ensure_one()
        return [(i.type, i.name) for i in self.identities]

    @job
    def ensure_unique(self, mode):
        for rec in self:
            self.env["openg2p.beneficiary"].matches(rec, mode, stop_on_first=False)

    @api.multi
    def create_beneficiary_from_registration(self):
        """Create an openg2p.beneficiary from the openg2p.registrations"""
        self.ensure_one()

        if (
            not self.duplicate_beneficiaries_ids
        ):  # last chance to make sure no duplicates
            self.ensure_unique(mode=MATCH_MODE_COMPREHENSIVE)

        if (
            self.duplicate_beneficiaries_ids
        ):  # TODO ability to force create if maanger... pass via context
            raise ValidationError(
                _("Potential duplicates exists for this record and so can not be added")
            )

        data = {
            "firstname": self.firstname,
            "lastname": self.lastname,
            "othernames": self.othernames,
            "location_id": self.location_id.id,
            "street": self.street,
            "street2": self.street2,
            "city": self.city,
            "state_id": self.state_id.id,
            "zip": self.zip,
            "country_id": self.country_id.id,
            "phone": self.phone,
            "mobile": self.mobile,
            "email": self.email,
            "title": self.title.id,
            "lang": self.lang,
            "gender": self.gender,
            "birthday": self.birthday,
            "image": self.image,
            "marital": self.marital,
            "national_id": self.identity_national,
            "passport_id": self.identity_passport,
            "emergency_contact": self.emergency_contact,
            "emergency_phone": self.emergency_phone,
        }
        beneficiary = self.env["openg2p.beneficiary"].create(data)
        org_fields = self.env["openg2p.registration.orgmap"].search(
            [("regd_id", "=", self.id)]
        )
        for org_field in org_fields:
            self.env["openg2p.beneficiary.orgmap"].create(
                {
                    "field_name": org_field.field_name,
                    "field_value": org_field.field_value,
                    "beneficiary_id": beneficiary.id,
                }
            )
        for code, number in self.get_identities():
            category = self.env["openg2p.beneficiary.id_category"].search(
                [("type", "=", code)]
            )
            self.env["openg2p.beneficiary.id_number"].create(
                {
                    "category_id": category.id,
                    "name": number,
                    "beneficiary_id": beneficiary.id,
                }
            )

        self.write(
            {"beneficiary_id": beneficiary.id, "registered_date": fields.Datetime.now()}
        )
        context = dict(self.env.context)
        context["form_view_initial_mode"] = "edit"
        return {
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "form",
            "res_model": "openg2p.beneficiary",
            "res_id": beneficiary.id,
            "context": context,
        }

    @api.multi
    def archive_registration(self):
        for registration in self:
            if registration.beneficiary_id:
                raise UserError(
                    _(
                        "You can not archive an registration for which a beneficiary has been created"
                    )
                )
        self.write({"active": False})

    @api.multi
    def reset_registration(self):
        """Reinsert the registration into the registration pipe in the first stage"""
        if self.filtered("beneficiary_id"):
            raise UserError(
                _(
                    "You can not reset an registration for which a beneficiary has been created"
                )
            )
        default_stage_id = self._default_stage_id()
        self.write({"active": True, "stage_id": default_stage_id})
