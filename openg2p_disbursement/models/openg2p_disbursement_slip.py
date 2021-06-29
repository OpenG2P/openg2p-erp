# -*- coding:utf-8 -*-
# Copied mostly from Odoo. See Odoo LICENSE file for full copyright and licensing details.

from datetime import date, datetime, time

import babel
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError


class Slip(models.Model):
    _name = "openg2p.disbursement.slip"
    _description = "Disbursement Slip"
    _inherit = ["mail.thread", "openg2p.mixin.no_copy"]

    struct_id = fields.Many2one(
        "openg2p.disbursement.structure",
        string="Structure",
        readonly=True,
        states={"draft": [("readonly", False)]},
        required=False,
        help="Defines rules that have to be applied to this disbursement slip, accordingly to the enrollment chosen.",
    )
    name = fields.Char(
        string="Disbursement Slip Name",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    number = fields.Char(
        string="Reference",
        readonly=True,
        copy=False,
        states={"draft": [("readonly", False)]},
    )
    beneficiary_id = fields.Many2one(
        "openg2p.beneficiary",
        string="Beneficiary",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
        index=True,
    )
    date_from = fields.Date(
        string="Date From",
        readonly=True,
        required=True,
        default=lambda self: fields.Date.to_string(date.today().replace(day=1)),
        states={"draft": [("readonly", False)]},
    )
    date_to = fields.Date(
        string="Date To",
        readonly=True,
        required=True,
        default=lambda self: fields.Date.to_string(
            (datetime.now() + relativedelta(months=+1, day=1, days=-1)).date()
        ),
        states={"draft": [("readonly", False)]},
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("confirm", "Confirm"),
            ("done", "Done"),
            ("cancel", "Rejected"),
        ],
        track_visibility="onchange",
        string="Status",
        index=True,
        readonly=True,
        copy=False,
        default="draft",
        help="""* When the disbursement slip is created the status is \'Draft\'
                \n* If the disbursement slip is under verification, the status is \'Verifying\'.
                \n* If the disbursement slip is confirmed then status is set to \'Done\'.
                \n* When user cancel disbursement slip the status is \'Rejected\'.""",
    )
    line_ids = fields.One2many(
        "openg2p.disbursement.slip.line",
        "slip_id",
        string="Slip Lines",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        readonly=True,
        copy=False,
        default=lambda self: self.env["res.company"]._company_default_get(),
        states={"draft": [("readonly", False)]},
        index=True,
    )
    input_line_ids = fields.One2many(
        "openg2p.disbursement.slip.input",
        "slip_id",
        string="Slip inputs",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    paid = fields.Boolean(
        string="Made Disbursement Order?",
        readonly=True,
        copy=False,
        states={"draft": [("readonly", False)]},
    )
    note = fields.Text(
        string="Internal Note", readonly=True, states={"draft": [("readonly", False)]}
    )
    enrollment_id = fields.Many2one(
        "openg2p.program.enrollment",
        string="Enrollment",
        readonly=True,
        required=True,
        states={"draft": [("readonly", False)]},
    )
    details_by_disbursement_rule_category = fields.One2many(
        "openg2p.disbursement.slip.line",
        compute="_compute_details_by_disbursement_rule_category",
        string="Details by Disbursement Rule Category",
    )
    batch_id = fields.Many2one(
        "openg2p.disbursement.batch",
        string="Disbursement Batch",
        index=True,
        readonly=True,
        copy=False,
        states={"draft": [("readonly", False)]},
        required=True,
    )
    program_id = fields.Many2one(
        "openg2p.program",
        string="Program",
        readonly=True,
        copy=False,
        store=True,
        related="batch_id.program_id",
    )
    slip_count = fields.Integer(
        compute="_compute_slip_stats",
        string="Disbursement Slip Computation Details",
        store=True,
    )
    currency_id = fields.Many2one(
        string="Currency", related="batch_id.currency_id", readonly=True, store=True
    )
    total = fields.Monetary(compute="_compute_slip_stats", string="Net", store=True)
    exception_ids = fields.One2many(
        "openg2p.disbursement.exception",
        "slip_id",
        "Slip Alerts",
        readonly=True,
    )

    _sql_constraints = [
        (
            "beneficiary_uniq",
            "UNIQUE (beneficiary_id, batch_id)",
            "Beneficiary can not be added multiple times to a batch.",
        )
    ]

    @api.multi
    def _compute_details_by_disbursement_rule_category(self):
        for slip in self:
            slip.details_by_disbursement_rule_category = slip.mapped(
                "line_ids"
            ).filtered(lambda line: line.category_id)

    @api.multi
    @api.depends("line_ids", "line_ids.total")
    def _compute_slip_stats(self):
        for slip in self:
            slip.slip_count = len(slip.line_ids)
            slip.total = sum(
                slip.line_ids.filtered(lambda l: l.code == "NET").mapped("total")
            )

    @api.constrains("enrollment_id", "program_id")
    def _check_beneficiary_beneficiary(self):
        for slip in self:
            if slip.program_id != slip.enrollment_id.program_id:
                raise ValidationError(
                    _(
                        "%s is not enrolled in program %s"
                        % (slip.beneficiary_id.display_name, slip.program_id.name)
                    )
                )

    @api.constrains("date_from", "date_to")
    def _check_dates(self):
        if any(self.filtered(lambda slip: slip.date_from > slip.date_to)):
            raise ValidationError(
                _("Disbursement Slip 'Date From' must be earlier 'Date To'.")
            )

    @api.multi
    def action_reset_draft(self):
        if self.filtered(lambda slip: slip.paid):
            raise UserError(_("Cannot reset a disbursement slip that is paid"))
        self.exception_ids.unlink()
        return self.write({"state": "draft"})

    @api.multi
    def action_slip_confirm(self):
        if self.filtered(lambda slip: slip.state != "draft"):
            raise UserError(
                _("Cannot confirm a disbursement slip that is not in the draft state.")
            )
        return self.write({"state": "confirm"})

    @api.multi
    def action_slip_done(self):
        if self.filtered(lambda slip: slip.state != "confirm"):
            raise UserError(_("Cannot mark as done if not in the confirmed state."))
        return self.write({"state": "done"})

    @api.multi
    def action_slip_cancel(self):
        if self.filtered(lambda slip: slip.paid):
            raise UserError(_("Cannot cancel a disbursement slip that is paid."))
        return self.write({"state": "cancel"})

    @api.multi
    def unlink(self):
        if any(self.filtered(lambda slip: slip.state not in ("draft", "cancel"))):
            raise UserError(
                _(
                    "You cannot delete a disbursement slip which is not draft or cancelled!"
                )
            )
        return super(Slip, self).unlink()

    @api.model
    def get_enrollment(self, program, beneficiary, date_from, date_to):
        """
        @param program; program we which to get enrollments for
        @param beneficiary: recordset of beneficiary
        @param date_from: date field
        @param date_to: date field
        @return: returns the ids of all the enrollments for the given beneficiary that need to be considered for the given dates
        """
        # a enrollment is valid if it ends between the given dates
        clause_1 = ["&", ("date_end", "<=", date_to), ("date_end", ">=", date_from)]
        # OR if it starts between the given dates
        clause_2 = ["&", ("date_start", "<=", date_to), ("date_start", ">=", date_from)]
        # OR if it starts before the date_from and finish after the date_end (or never finish)
        clause_3 = [
            "&",
            ("date_start", "<=", date_from),
            "|",
            ("date_end", "=", False),
            ("date_end", ">=", date_to),
        ]
        clause_final = (
            [
                ("program_id", "=", program.id),
                ("beneficiary_id", "=", beneficiary.id),
                ("state", "=", "open"),
                "|",
                "|",
            ]
            + clause_1
            + clause_2
            + clause_3
        )
        return self.env["openg2p.program.enrollment"].search(clause_final).ids

    @api.multi
    def compute_sheet(self):
        self.exception_ids.unlink()
        rules = self.env["openg2p.disbursement.exception.rule"].search([])
        for slip in self:
            number = slip.number or self.env["ir.sequence"].next_by_code(
                "disbursement.slip"
            )
            # delete old disbursement slip lines
            slip.line_ids.unlink()
            # set the list of enrollment for which the rules have to be applied
            # if we don't give the enrollment, then the rules to apply should be for all current enrollments of the beneficiary
            enrollment_ids = slip.enrollment_id.ids or self.get_enrollment(
                slip.program_id, slip.beneficiary_id, slip.date_from, slip.date_to
            )
            lines = [
                (0, 0, line) for line in self._get_slip_lines(enrollment_ids, slip.id)
            ]
            slip.write({"line_ids": lines, "number": number})
            rules.check_slip(slip)
        self.check_active_alerts()
        return True

    def check_active_alerts(self):
        batch = self[0].batch_id
        beneficiaries = self.mapped("beneficiary_id.id")
        active_alerts_beneficiaries = self.env[
            "openg2p.beneficiary.exception"
        ].search_read(
            [
                ("state", "=", "open"),
                "|",
                ("beneficiary_id", "in", beneficiaries),
                ("associated_beneficiary_ids", "in", beneficiaries),
            ],
            ["beneficiary_id"],
        )
        rule = self.env.ref("openg2p_disbursement.exception_rule_active_alert")
        for i in active_alerts_beneficiaries:
            beneficiary_id = i["beneficiary_id"][0]
            self.env["openg2p.disbursement.exception"].create(
                {
                    "rule_id": rule.id,
                    "slip_id": self.filtered(
                        lambda r: r.beneficiary_id == beneficiary_id
                    ),
                    "batch_id": batch.id,
                    "beneficiary_id": beneficiary_id,
                }
            )

    @api.model
    def get_inputs(self, enrollments, date_from, date_to):
        res = []

        structure_ids = enrollments.get_all_structures()
        rule_ids = (
            self.env["openg2p.disbursement.structure"]
            .browse(structure_ids)
            .get_all_rules()
        )
        sorted_rule_ids = [id for id, sequence in sorted(rule_ids, key=lambda x: x[1])]
        inputs = (
            self.env["openg2p.disbursement.rule"]
            .browse(sorted_rule_ids)
            .mapped("input_ids")
        )

        for enrollment in enrollments:
            for input in inputs:
                input_data = {
                    "name": input.name,
                    "code": input.code,
                    "enrollment_id": enrollment.id,
                }
                res += [input_data]
        return res

    @api.model
    def _get_slip_lines(self, enrollment_ids, slip_id):
        def _sum_disbursement_rule_category(localdict, category, amount):
            if category.parent_id:
                localdict = _sum_disbursement_rule_category(
                    localdict, category.parent_id, amount
                )

            if category.code in localdict["categories"].dict:
                localdict["categories"].dict[category.code] += amount
            else:
                localdict["categories"].dict[category.code] = amount

            return localdict

        class BrowsableObject(object):
            def __init__(self, beneficiary_id, dict, env):
                self.beneficiary_id = beneficiary_id
                self.dict = dict
                self.env = env

            def __getattr__(self, attr):
                return attr in self.dict and self.dict.__getitem__(attr) or 0.0

        class InputLine(BrowsableObject):
            """a class that will be used into the python code, mainly for usability purposes"""

            def sum(self, code, from_date, to_date=None):
                if to_date is None:
                    to_date = fields.Date.today()
                self.env.cr.execute(
                    """
                    SELECT sum(pi.amount) as sum
                    FROM openg2p_disbursement_slip as hp, openg2p_disbursement_slip_input as pi
                    WHERE hp.program_id = %s AND hp.beneficiary_id = %s AND hp.state = 'done'
                    AND hp.date_from >= %s AND hp.date_to <= %s AND hp.id = pi.slip_id AND pi.code = %s""",
                    (self.program_id, self.beneficiary_id, from_date, to_date, code),
                )
                return self.env.cr.fetchone()[0] or 0.0

        class Slips(BrowsableObject):
            """a class that will be used into the python code, mainly for usability purposes"""

            def sum(self, code, from_date, to_date=None):
                if to_date is None:
                    to_date = fields.Date.today()
                self.env.cr.execute(
                    """SELECT sum(pl.total)
                            FROM openg2p_disbursement_slip as hp, openg2p_disbursement_slip_line as pl
                            WHERE hp.program_id = %s AND hp.beneficiary_id = %s AND hp.state = 'done'
                            AND hp.date_from >= %s AND hp.date_to <= %s AND hp.id = pl.slip_id AND pl.code = %s""",
                    (self.program_id, self.beneficiary_id, from_date, to_date, code),
                )
                res = self.env.cr.fetchone()
                return res and res[0] or 0.0

        # we keep a dict with the result because a value can be overwritten by another rule with the same code
        result_dict = {}
        rules_dict = {}
        inputs_dict = {}
        blacklist = []
        slip = self.env["openg2p.disbursement.slip"].browse(slip_id)
        for input_line in slip.input_line_ids:
            inputs_dict[input_line.code] = input_line

        categories = BrowsableObject(slip.beneficiary_id.id, {}, self.env)
        inputs = InputLine(slip.beneficiary_id.id, inputs_dict, self.env)
        slips = Slips(slip.beneficiary_id.id, slip, self.env)
        rules = BrowsableObject(slip.beneficiary_id.id, rules_dict, self.env)

        baselocaldict = {
            "categories": categories,
            "rules": rules,
            "slip": slips,
            "inputs": inputs,
        }
        # get the ids of the structures on the enrollments and their parent id as well
        enrollments = self.env["openg2p.program.enrollment"].browse(enrollment_ids)
        if len(enrollments) == 1 and slip.struct_id:
            structure_ids = list(set(slip.struct_id._get_parent_structure().ids))
        else:
            structure_ids = enrollments.get_all_structures()
        # get the rules of the structure and thier children
        rule_ids = (
            self.env["openg2p.disbursement.structure"]
            .browse(structure_ids)
            .get_all_rules()
        )
        # run the rules by sequence
        sorted_rule_ids = [id for id, sequence in sorted(rule_ids, key=lambda x: x[1])]
        sorted_rules = self.env["openg2p.disbursement.rule"].browse(sorted_rule_ids)

        for enrollment in enrollments:
            beneficiary = enrollment.beneficiary_id
            localdict = dict(
                baselocaldict, beneficiary=beneficiary, enrollment=enrollment
            )
            for rule in sorted_rules:
                key = rule.code + "-" + str(enrollment.id)
                localdict["result"] = None
                localdict["result_qty"] = 1.0
                localdict["result_rate"] = 100
                # check if the rule can be applied
                if rule._satisfy_condition(localdict) and rule.id not in blacklist:
                    # compute the amount of the rule
                    amount, qty, rate = rule._compute_rule(localdict)
                    # check if there is already a rule computed with that code
                    previous_amount = (
                        rule.code in localdict and localdict[rule.code] or 0.0
                    )
                    # set/overwrite the amount computed for this rule in the localdict
                    tot_rule = amount * qty * rate / 100.0
                    localdict[rule.code] = tot_rule
                    rules_dict[rule.code] = rule
                    # sum the amount for its disbursement category
                    localdict = _sum_disbursement_rule_category(
                        localdict, rule.category_id, tot_rule - previous_amount
                    )
                    # create/overwrite the rule in the temporary results
                    result_dict[key] = {
                        "disbursement_rule_id": rule.id,
                        "enrollment_id": enrollment.id,
                        "name": rule.name,
                        "code": rule.code,
                        "category_id": rule.category_id.id,
                        "sequence": rule.sequence,
                        "appears_on_slip": rule.appears_on_slip,
                        "condition_select": rule.condition_select,
                        "condition_python": rule.condition_python,
                        "condition_range": rule.condition_range,
                        "condition_range_min": rule.condition_range_min,
                        "condition_range_max": rule.condition_range_max,
                        "amount_select": rule.amount_select,
                        "amount_fix": rule.amount_fix,
                        "amount_python_compute": rule.amount_python_compute,
                        "amount_percentage": rule.amount_percentage,
                        "amount_percentage_base": rule.amount_percentage_base,
                        "register_id": rule.register_id.id,
                        "amount": amount,
                        "beneficiary_id": enrollment.beneficiary_id.id,
                        "quantity": qty,
                        "rate": rate,
                    }
                else:
                    # blacklist this rule and its children
                    blacklist += [id for id, seq in rule._recursive_search_of_rules()]

        return list(result_dict.values())

    @api.multi
    def build_slip_data(
        self, date_from, date_to, program, beneficiary, enrollment=False
    ):
        # defaults
        res = {
            "value": {
                "line_ids": [],
                # delete old input lines
                "input_line_ids": [
                    (
                        2,
                        x,
                    )
                    for x in self.input_line_ids.ids
                ],
                "name": "",
                "enrollment_id": False,
                "struct_id": False,
            }
        }
        if not beneficiary or not date_from or not date_to:
            return res

        ttyme = datetime.combine(fields.Date.from_string(date_from), time.min)
        locale = self.env.context.get("lang") or "en_US"
        res["value"].update(
            {
                "name": _("Disbursement Slip of %s for %s - %s")
                % (
                    beneficiary.name,
                    program.name,
                    tools.ustr(
                        babel.dates.format_date(
                            date=ttyme, format="MMMM-y", locale=locale
                        )
                    ),
                ),
                "company_id": beneficiary.company_id.id,
            }
        )

        if not self.env.context.get("enrollment"):
            # fill with the first enrollment of the beneficiary
            enrollment_ids = self.get_enrollment(
                program, beneficiary, date_from, date_to
            )
        else:
            if enrollment:
                # set the list of enrollment for which the input have to be filled
                enrollment_ids = enrollment.ids
            else:
                # if we don't give the enrollment, then the input to fill should be for all current enrollments of the beneficiary
                enrollment_ids = self.get_enrollment(
                    program, beneficiary, date_from, date_to
                )

        if not enrollment_ids:
            return res
        enrollment = self.env["openg2p.program.enrollment"].browse(enrollment_ids[0])
        if not enrollment.disbursement_amount:
            raise UserError(
                "Disbursement amount needs to be set for category: "
                + enrollment.category_id.name
            )
        res["value"].update({"enrollment_id": enrollment.id})
        struct = enrollment.struct_id
        if not struct:
            return res
        res["value"].update(
            {
                "struct_id": struct.id,
            }
        )
        # computation of the disbursement input
        enrollments = self.env["openg2p.program.enrollment"].browse(enrollment_ids)
        input_line_ids = self.get_inputs(enrollments, date_from, date_to)
        res["value"].update(
            {
                "input_line_ids": input_line_ids,
            }
        )
        return res

    @api.onchange("beneficiary_id", "date_from", "date_to", "program_id")
    def onchange_beneficiary(self):

        if (not self.beneficiary_id) or (not self.date_from) or (not self.date_to):
            return
        enrollment_ids = []
        data = self.build_slip_data(
            self.date_from, self.date_to, self.program_id, self.beneficiary_id
        )["value"]
        self.name = data["name"]
        self.company_id = data["company_id"]

        if "enrollment_id" in data:
            self.enrollment_id = self.env["openg2p.program.enrollment"].browse(
                data["enrollment_id"]
            )
            self.struct_id = self.enrollment_id.struct_id

        # computation of the disbursement input
        if "input_line_ids" in data:
            input_lines = self.input_line_ids.browse([])
            for r in data["input_line_ids"]:
                input_lines += input_lines.new(r)
            self.input_line_ids = input_lines
        return

    @api.onchange("enrollment_id")
    def onchange_enrollment(self):
        if not self.enrollment_id:
            self.struct_id = False
        self.with_context(enrollment=True).onchange_beneficiary()
        return

    def get_disbursement_line_total(self, code):
        self.ensure_one()
        line = self.line_ids.filtered(lambda l: l.code == code)
        if line:
            return line[0].total
        else:
            return 0.0
