# -*- coding: utf-8 -*-
import json
import uuid
import logging
import requests
from datetime import datetime
from odoo.addons.openg2p.services.matching_service import (
    MATCH_MODE_COMPREHENSIVE,
)
# from odoo.addons.queue_job.job import job

from odoo import api, fields, models, SUPERUSER_ID
from odoo.exceptions import UserError, ValidationError
from odoo.tools.translate import _

_logger = logging.getLogger(__name__)

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
        return self.env.user.company_id

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
        tracking=True,
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
        tracking=True,
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
        tracking=True,
        help="Beneficiary linked to the registration.",
    )
    identity_national = fields.Char(
        string="National ID",
        tracking=True,
    )
    identity_passport = fields.Char(
        string="Passport No",
        tracking=True,
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
    retained_id = fields.Integer(string="Retained_ID")

    org_custom_field = fields.One2many(
        "openg2p.registration.orgmap",
        "regd_id",
    )

    # example for filtering on org custom fields
    attendance = fields.Integer(
        string="Attendance",
        store=False,
        required=False,
        compute="_compute_org_fields",
        search="_search_att",
    )

    # example for another filter
    school_approved = fields.Selection(
        string="Is School Approved",
        required=False,
        store=False,
        selection=[
            ("yes", "Yes"),
            ("no", "No"),
        ],
        compute="_compute_org_fields",
        search="_search_approved",
    )

    regression_and_progression = fields.Integer(
        string="Regression and Progression",
        stored=False,
        required=False,
        compute="_compute_org_fields",
        search="_search_r_and_p",
    )

    total_quality = fields.Integer(
        string="Total Quality",
        stored=False,
        required=False,
        compute="_compute_org_fields",
        search="_search_tot_quality",
    )

    total_equity = fields.Integer(
        string="Total Equity",
        stored=False,
        required=False,
        compute="_compute_org_fields",
        search="_search_tot_equity",
    )

    grand_total = fields.Integer(
        string="Grand Total",
        stored=False,
        required=False,
        compute="_compute_org_fields",
        search="_search_grand_tot",
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

    odk_batch_id = fields.Char(default=lambda *args: uuid.uuid4().hex)

    program_ids = fields.Many2many(
        comodel_name="openg2p.program",
        relation="regd_programs",
        string="Active Programs",
        help="Active programs enrolled to",
        store=True,
        required=False,
    )
    merged_beneficiary_ids = fields.Many2many(
        'openg2p.beneficiary',
        'merged_beneficiary_rel_regd',
        'retained_id',
        'merged_id',
        string="Merged Duplicates",
        index=True,
        context={'active_test': False},
        help="Duplicate records that have been merged with this."
             " Primary function is to allow to reference of merged records "
    )

    # will be return registration details on api call
    def api_json(self):
        data = {
            "id": self.id,
            "firstname": self.firstname,
            "lastname": self.lastname,
            "email": self.email or "",
            "phone": self.phone or "",
            "mobile": self.mobile or "",
            "stage_id": {
                "id": self.stage_id.id,
                "name": self.stage_id.name,
            },
            "bank_account_id": {
                "id": self.bank_account_id.id or "",
                "acc_holder_name": self.bank_account_id.acc_holder_name or "",
                "acc_number": self.bank_account_id.acc_number or "",
                "acc_type": self.bank_account_id.acc_type or "",
                "bank_id": self.bank_account_id.bank_id.id or "",
                "bank_name": self.bank_account_id.bank_name or "",
                "company_id": self.bank_account_id.company_id.id or "",
                "display_name": self.bank_account_id.display_name or "",
                "name": self.bank_account_id.name or "",
                "partner_id": self.bank_account_id.partner_id.id or "",
                "sequence": self.bank_account_id.sequence or "",
            },
            "address": {
                "city": self.city or "",
                "country_id": {
                    "id": self.country_id.id or "",
                    "name": self.country_id.name or "",
                },
                "state_id": {
                    "id": self.state_id.id or "",
                    "name": self.state_id.name or "",
                },
                "street": self.street or "",
                "street2": self.street2 or "",
                "zip": self.zip or "",
            },
            "kyc": {
                "passport_id": self.passport_id or "",
                "identity_passport": self.identity_passport or "",
                "national_id": self.national_id or "",
                "identity_national": self.identity_national or "",
                "ssn": self.ssn or "",
            },
            "identities": {i.type: i.name for i in self.identities},
            "org_custom_field": {
                i.field_name: i.field_value for i in self.org_custom_field
            },
        }
        return data

    # example for filtering on org custom fields
    @api.depends("org_custom_field")
    def _compute_org_fields(self):
        for rec in self:
            field = self.env["openg2p.registration.orgmap"].search(
                [
                    "&",
                    ("regd_id", "=", rec.id),
                    ("field_name", "=", "total_student_in_attendance_at_the_school"),
                ]
            )
            try:
                rec.attendance = int(field.field_value) if field else 0
            except BaseException as e:
                rec.attendance = 0

            field = self.env["openg2p.registration.orgmap"].search(
                [
                    "&",
                    ("regd_id", "=", rec.id),
                    ("field_name", "=", "regression_and_progression"),
                ]
            )
            try:
                rec.regression_and_progression = int(field.field_value) if field else 0
            except BaseException as e:
                rec.regression_and_progression = 0

            field = self.env["openg2p.registration.orgmap"].search(
                ["&", ("regd_id", "=", rec.id), ("field_name", "=", "total_quality")]
            )
            try:
                rec.total_quality = int(field.field_value) if field else 0
            except BaseException as e:
                rec.total_quality = 0

            field = self.env["openg2p.registration.orgmap"].search(
                ["&", ("regd_id", "=", rec.id), ("field_name", "=", "total_equity")]
            )
            try:
                rec.total_equity = int(field.field_value) if field else 0
            except BaseException as e:
                rec.total_equity = 0

            field = self.env["openg2p.registration.orgmap"].search(
                ["&", ("regd_id", "=", rec.id), ("field_name", "=", "grand_total_le")]
            )
            try:
                rec.grand_total = int(field.field_value) if field else 0
            except BaseException as e:
                rec.grand_total = 0

            field = self.env["openg2p.registration.orgmap"].search(
                [
                    "&",
                    ("regd_id", "=", rec.id),
                    ("field_name", "=", "is_the_school_approved"),
                ]
            )
            try:
                if field.field_value != "yes":
                    rec.school_approved = "no"
                else:
                    rec.school_approved = "yes"
            except BaseException as e:
                _logger.error(e)
                rec.school_approved = "no"

    # example for filtering on org custom fields
    def _search_att(self, operator, val2):
        res = []
        regds = self.env["openg2p.registration"].search([])
        for rec in regds:
            val = rec.attendance
            if operator == ">":
                if val > val2:
                    res.append(rec.id)
            elif operator == "<":
                if val < val2:
                    res.append(rec.id)
            elif operator == "=":
                if val == val2:
                    res.append(rec.id)
            elif operator == "!=":
                if val != val2:
                    res.append(rec.id)
            elif operator == ">=":
                if val >= val2:
                    res.append(rec.id)
            elif operator == "<=":
                if val <= val2:
                    res.append(rec.id)
        return [("id", "in", res)]

    # example for filtering on org custom fields
    def _search_r_and_p(self, operator, val2):
        res = []
        regds = self.env["openg2p.registration"].search([])
        for rec in regds:
            val = rec.regression_and_progression
            if operator == ">":
                if val > val2:
                    res.append(rec.id)
            elif operator == "<":
                if val < val2:
                    res.append(rec.id)
            elif operator == "=":
                if val == val2:
                    res.append(rec.id)
            elif operator == "!=":
                if val != val2:
                    res.append(rec.id)
            elif operator == ">=":
                if val >= val2:
                    res.append(rec.id)
            elif operator == "<=":
                if val <= val2:
                    res.append(rec.id)
        return [("id", "in", res)]

    # example for filtering on org custom fields
    def _search_tot_quality(self, operator, val2):
        res = []
        regds = self.env["openg2p.registration"].search([])
        for rec in regds:
            val = rec.total_quality
            if operator == ">":
                if val > val2:
                    res.append(rec.id)
            elif operator == "<":
                if val < val2:
                    res.append(rec.id)
            elif operator == "=":
                if val == val2:
                    res.append(rec.id)
            elif operator == "!=":
                if val != val2:
                    res.append(rec.id)
            elif operator == ">=":
                if val >= val2:
                    res.append(rec.id)
            elif operator == "<=":
                if val <= val2:
                    res.append(rec.id)
        return [("id", "in", res)]

    # example for filtering on org custom fields
    def _search_tot_equity(self, operator, val2):
        res = []
        regds = self.env["openg2p.registration"].search([])
        for rec in regds:
            val = rec.total_equity
            if operator == ">":
                if val > val2:
                    res.append(rec.id)
            elif operator == "<":
                if val < val2:
                    res.append(rec.id)
            elif operator == "=":
                if val == val2:
                    res.append(rec.id)
            elif operator == "!=":
                if val != val2:
                    res.append(rec.id)
            elif operator == ">=":
                if val >= val2:
                    res.append(rec.id)
            elif operator == "<=":
                if val <= val2:
                    res.append(rec.id)
        return [("id", "in", res)]

    # example for filtering on org custom fields
    def _search_grand_tot(self, operator, val2):
        res = []
        regds = self.env["openg2p.registration"].search([])
        for rec in regds:
            val = rec.grand_total
            if operator == ">":
                if val > val2:
                    res.append(rec.id)
            elif operator == "<":
                if val < val2:
                    res.append(rec.id)
            elif operator == "=":
                if val == val2:
                    res.append(rec.id)
            elif operator == "!=":
                if val != val2:
                    res.append(rec.id)
            elif operator == ">=":
                if val >= val2:
                    res.append(rec.id)
            elif operator == "<=":
                if val <= val2:
                    res.append(rec.id)
        return [("id", "in", res)]

    # example for another filtering on org custom fields
    def _search_approved(self, operator, val2):
        res = []
        regds = self.env["openg2p.registration"].search([])
        for rec in regds:
            if isinstance(val2, bool):
                continue
            try:
                val = rec.school_approved
            except BaseException as e:
                _logger.error(e)
                continue
            if operator == "=":
                if val == val2:
                    res.append(rec.id)
            elif operator == "!=":
                if val != val2:
                    res.append(rec.id)
        return [("id", "in", res)]

    def _get_default_odk_map(self):
        from .openg2p_submission_registration_map import odk_map_data

        return odk_map_data

    def create_registration_from_odk(self, odk_data):
        odk_map = (
            odk_data["odk_map"]
            if "odk_map" in odk_data.keys()
            else self._get_default_odk_map()
        )
        temp = {}
        for k, v in odk_data.items():
            if k.startswith("group"):
                for k2, v2 in v.items():
                    if k2 in odk_map.keys():
                        k2 = odk_map[k2]
                    else:
                        k2 = str(k2).replace("-", "_").lower()
                    if not str(k2).startswith("_"):
                        temp[k2] = v2
            else:
                if not str(k).startswith("_"):
                    temp[str(k).replace("-", "_").lower()] = v

        # Required fields to create registration
        country_name = (
            temp["country"] if "country" in temp.keys() else "Sierra Leone"
        )
        state_name = temp["state"] if "state" in temp.keys() else "Freetown"

        country_id = self.env["res.country"].search([("name", "=", country_name)])[0].id
        state_id = (
            self.env["res.country.state"].search([("name", "=", state_name)])[0].id
        )
        regd_info = {
            "firstname": "_",
            "lastname": "_",
            "street": (temp["chiefdom"] if "chiefdom" in temp.keys() else "-"),
            "street2": (temp["district"] if "district" in temp.keys() else "-")
                       + ", "
                       + (temp["region"] if "region" in temp.keys() else "-"),
            "city": (
                    (temp["city"] if "city" in temp.keys() else "Freetown")
                    or "Freetown"
            )
            if "city" in temp.keys()
            else "Freetown",
            "country_id": country_id,
            "state_id": state_id,
            "gender": "male",
        }
        try:
            regd = self.create(regd_info)
            idr = regd.id
        except BaseException as e:
            _logger.error(e)
            return None

        data = {}
        odk_data = temp
        org_data = {}
        format = "%Y-%m-%d %H:%M:%S"
        for k, v in odk_data.items():
            try:
                if k in [
                    "regression_and_progression",
                    "total_quality",
                    "total_equity",
                    "grand_total",
                ]:
                    org_data[k] = v
                    continue
                if (
                        k
                        in [
                    "Status",
                    "AttachmentsExpected",
                    "AttachmentsPresent",
                    "SubmitterName",
                    "SubmitterID",
                    "KEY",
                    "meta-instanceID",
                    "__version__",
                    "bank_name",
                    "city",
                    "district",
                    "chiefdom",
                    "region",
                ]
                        or k.startswith("_")
                ):
                    continue
                if k == "bank_account_number":
                    if len(str(v) or "") != 0:
                        data["bank_account_number"] = str(v)
                        res = self.env["res.partner.bank"].search(
                            [("acc_number", "=", str(v))]
                        )
                        if res:
                            raise Exception("Duplicate Bank Account Number!")
                        if not res:
                            bank_id = self.env["res.bank"].search(
                                [("name", "=", odk_data["bank_name"])], limit=1
                            )
                            if len(bank_id) == 0:
                                bank_id = self.env["res.bank"].create(
                                    {
                                        "execute_method": "manual",
                                        "name": odk_data["bank_name"],
                                        "type": "normal",
                                    }
                                )
                            else:
                                bank_id = bank_id[0]
                            res = self.env["res.partner.bank"].create(
                                {
                                    "bank_id": bank_id.id,
                                    "acc_number": str(v),
                                    "payment_mode": "AFM",
                                    "bank_name": odk_data["bank_name"],
                                    "acc_holder_name": odk_data["name"],
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
                            [("beneficiary_id", "=", idr)], limit=1
                        )
                        if res:
                            data["beneficiary_id"] = res.id
                    elif k == "identities":
                        for vi in v:
                            self.env["openg2p.registration.identity"].create(
                                {
                                    "name": list(vi.keys())[0],
                                    "type": list(vi.values())[0],
                                    "registration_id": idr,
                                }
                            )
                        res = self.env["openg2p.registration.identity"].search(
                            [("registration_id", "=", idr)]
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
                            data.update({k: v})
                else:
                    org_data.update({k: v})
            except Exception as e:
                _logger.error(e)
        for k, v in org_data.items():
            try:
                self.env["openg2p.registration.orgmap"].create(
                    {
                        "field_name": k,
                        "field_value": str(v) if v else "",
                        "regd_id": idr,
                    }
                )
            except BaseException as e:
                _logger.error(e)
        try:
            regd.write(data)
            # Updating Program for Registration
            regd.program_ids = [(6, 0, temp["program_ids"])]
        except BaseException as e:
            _logger.error(e)
        return regd

    @api.depends("date_open", "date_closed")
    def _compute_day(self):
        for record in self:
            if record.date_open:
                date_create = record.create_date
                date_open = record.date_open
                record.day_open = (date_open - date_create).total_seconds() / (24.0 * 3600)

            if record.date_closed:
                date_create = record.create_date
                date_closed = record.date_closed
                record.day_close = (date_closed - date_create).total_seconds() / (24.0 * 3600)
                record.delay_close = record.day_close - record.day_open

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

    def _track_subtype_val(self, init_values):
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
        return super(Registration, self)._track_subtype_val(init_values)

    def cron_check_uniqueness(self):
        self.search(
            [("beneficiary_id", "=", None), ("duplicate_beneficiaries_ids", "=", None)]
        ).sudo().with_delay().ensure_unique(MATCH_MODE_COMPREHENSIVE)

    def get_identities(self):
        self.ensure_one()
        return [(i.type, i.name) for i in self.identities]

    # @job
    def ensure_unique(self, mode):
        for rec in self:
            self.env["openg2p.beneficiary"].matches(rec, mode, stop_on_first=False)

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
            # "image": self.image,
            "marital": self.marital,
            "national_id": self.identity_national,
            "passport_id": self.identity_passport,
            "bank_account_id": self.bank_account_id.id,
            "emergency_contact": self.emergency_contact,
            "emergency_phone": self.emergency_phone,
            "odk_batch_id": self.odk_batch_id,
        }
        beneficiary = self.env["openg2p.beneficiary"].create(data)

        # Updating Program for beneficiary
        beneficiary.program_ids = [(6, 0, self.program_ids.ids)]

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

        # Indexing the beneficiary
        self.index_beneficiary()
        return {
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "form",
            "res_model": "openg2p.beneficiary",
            "res_id": beneficiary.id,
            "context": context,
        }

    def task_convert_registration_to_beneficiary(self):
        self.stage_id = 6
        self.active = False
        return self.create_beneficiary_from_registration()["res_id"]

    def archive_registration(self):
        for registration in self:
            if registration.beneficiary_id:
                raise UserError(
                    _(
                        "You can not archive an registration for which a beneficiary has been created"
                    )
                )
        self.write({"active": False})

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
