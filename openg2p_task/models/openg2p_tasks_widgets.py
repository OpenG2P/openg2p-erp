import asyncio
from asyncio import sleep
from random import random

from odoo import fields, models, api
from odoo.exceptions import ValidationError


class RegistrationsToBeneficiariesWizard(models.TransientModel):
    _name = "openg2p.task.regd2bene.widget"

    options = fields.Selection(
        string="Options",
        selection=(
            ("all", "All not yet converted"),
            ("registering_stage", "Registrations in Registering stage"),
        ),
        default="all",
        required=True,
    )
    total_record_count = fields.Integer(
        string="Total records",
        readonly=True,
    )
    selected_record_count = fields.Integer(
        string="Selected records",
        readonly=True,
    )

    @api.onchange("options")
    def _compute_selected_fields(self):
        self.selected_record_count = len(self._records(self.options))
        if not self.total_record_count:
            self.total_record_count = len(self._records("all"))

    def _records(self, option):
        regd_obj = self.env["openg2p.registration"]
        if option == "all":
            regds = regd_obj.search([("beneficiary_id", "=", False)])
        elif option == "registering_stage":
            regds = regd_obj.search(
                ["&", ("stage_id", "=", 6), ("beneficiary_id", "=", False)]
            )
        else:
            regds = []
        return regds

    def convert(self):
        async def regd2bene(regd):
            try:
                regd.stage_id = 6
                regd.active = False
                regd.create_beneficiary_from_registration()
            except BaseException as e:
                print(e)

        for regd in self._records(self.options):
            asyncio.run(regd2bene(regd))

    def btn_regd_list(self):
        view_id = self.env.ref("openg2p_registration.crm_case_tree_view_beneficiary").id
        context = self._context.copy()
        return {
            "name": "Registrations",
            "view_type": "form",
            "view_mode": "tree",
            "views": [(view_id, "tree")],
            "res_model": "openg2p.registration",
            "view_id": view_id,
            "type": "ir.actions.act_window",
            "target": "current",
            "context": context,
        }

    def btn_bene_list(self):
        view_id = self.env.ref("openg2p.view_beneficiary_tree").id
        context = self._context.copy()
        return {
            "name": "Beneficiaries",
            "view_type": "form",
            "view_mode": "tree",
            "views": [(view_id, "tree")],
            "res_model": "openg2p.beneficiary",
            "view_id": view_id,
            "type": "ir.actions.act_window",
            "target": "current",
            "context": context,
        }


class EnrollBeneficiariesIntoProgramWidget(models.TransientModel):
    _name = "openg2p.task.enrollbene.widget"

    options = fields.Selection(
        string="Options",
        selection=(
            ("all", "All"),
            ("unenrolled", "Beneficiaries not enrolled yet"),
        ),
        default="all",
        required=True,
    )
    total_record_count = fields.Integer(
        string="Total records",
        readonly=True,
    )
    selected_record_count = fields.Integer(
        string="Selected records",
        readonly=True,
    )
    program_id = fields.Many2one(
        "openg2p.program",
        string="Program",
    )
    date_start = fields.Date(
        "Enrollment Date",
        required=True,
        default=fields.Date.context_today,
        help="Start date of the program enrollment.",
        states={"draft": [("readonly", False)]},
    )

    @api.onchange("options")
    def _compute_selected_fields(self):
        self.selected_record_count = len(self._records(self.options))
        if not self.total_record_count:
            self.total_record_count = len(self._records("all"))

    def _records(self, option):
        beneficiary_obj = self.env["openg2p.beneficiary"]
        if option == "all":
            beneficiaries = beneficiary_obj.search([])
        elif option == "unenrolled":
            beneficiaries = beneficiary_obj.search([])
            beneficiaries = list(
                filter(
                    lambda b: self.program_id.id not in b.program_ids.ids, beneficiaries
                )
            )
        else:
            beneficiaries = []
        return beneficiaries

    def enroll(self):
        async def enroll_bene(ben):
            try:
                ben.program_enroll(
                    self.program_id.id, date_start=self.date_start, confirm=True
                )
            except BaseException as e:
                print(e)
                raise ValidationError(e)

        for b in self._records(self.options):
            asyncio.run(enroll_bene(b))

    def btn_prog_list(self):
        view_id = self.env.ref("openg2p_program.view_program").id
        context = self._context.copy()
        return {
            "name": "Programs",
            "view_type": "form",
            "view_mode": "tree",
            "views": [(view_id, "tree")],
            "res_model": "openg2p.program",
            "view_id": view_id,
            "type": "ir.actions.act_window",
            "target": "current",
            "context": context,
        }

    def btn_bene_list(self):
        view_id = self.env.ref("openg2p.view_beneficiary_tree").id
        context = self._context.copy()
        return {
            "name": "Beneficiaries",
            "view_type": "form",
            "view_mode": "tree",
            "views": [(view_id, "tree")],
            "res_model": "openg2p.beneficiary",
            "view_id": view_id,
            "type": "ir.actions.act_window",
            "target": "current",
            "context": context,
        }


class ChangeStateRegistrationWidget(models.TransientModel):
    _name = "openg2p.task.regdchangestage.widget"

    src_stage_id = fields.Many2one(
        "openg2p.registration.stage",
        "Current Stage",
    )
    total_record_count = fields.Integer(
        string="Total records",
        readonly=True,
    )
    selected_record_count = fields.Integer(
        string="Selected records",
        readonly=True,
    )
    target_stage_id = fields.Many2one(
        "openg2p.registration.stage",
        "Target Stage",
    )

    @api.onchange("src_stage_id")
    def _compute_selected_fields(self):
        self.selected_record_count = len(self._records())
        if not self.total_record_count:
            self.total_record_count = len(self._records("all"))

    def _records(self, option="by_stage_id"):
        regd_obj = self.env["openg2p.registration"]
        if option == "all":
            regds = regd_obj.search([])
        elif option == "by_stage_id":
            regds = regd_obj.search([])
            regds = list(filter(lambda r: self.src_stage_id.id == r.stage_id.id, regds))
        else:
            regds = []
        return regds

    def change_stage(self):
        temp = []

        async def enroll_bene(regd):
            try:
                regd.stage_id = self.target_stage_id
                temp.append(regd.id)
            except BaseException as e:
                print(e)

        for r in self._records():
            asyncio.run(enroll_bene(r))

    def btn_regd_list(self):
        view_id = self.env.ref("openg2p_registration.crm_case_tree_view_beneficiary").id
        context = self._context.copy()
        return {
            "name": "Registrations",
            "view_type": "form",
            "view_mode": "tree",
            "views": [(view_id, "tree")],
            "res_model": "openg2p.registration",
            "view_id": view_id,
            "type": "ir.actions.act_window",
            "target": "current",
            "context": context,
        }
