# -*- coding:utf-8 -*-
# Copied entirely from Odoo. See Odoo LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, ValidationError
from odoo.tools.safe_eval import safe_eval


class Openg2pDisbursementRule(models.Model):
    _name = "openg2p.disbursement.rule"
    _order = "sequence, id"
    _description = "Disbursement Rule"
    _inherit = ["generic.mixin.name_with_code"]

    name = fields.Char(translate=True)
    code = fields.Char(
        help="The code of disbursement rules can be used as reference in computation of other rules. "
        "In that case, it is case sensitive."
    )
    sequence = fields.Integer(
        required=True, index=True, default=5, help="Use to arrange calculation sequence"
    )
    quantity = fields.Char(
        default="1.0",
        help="It is used in computation for percentage and fixed amount. "
        "For e.g. A rule for Meal Voucher having fixed amount of "
        u"1€ per worked day can have its quantity defined in expression "
        "like days.WORK100.number_of_days.",
        required=True,
    )
    category_id = fields.Many2one(
        "openg2p.disbursement.rule.category", string="Category", required=True
    )
    active = fields.Boolean(
        default=True,
        help="If the active field is set to false, it will allow you to hide the disbursement rule without removing it.",
    )
    appears_on_slip = fields.Boolean(
        string="Appears on Slip",
        default=True,
        help="Used to display the disbursement rule on slip.",
    )
    parent_rule_id = fields.Many2one(
        "openg2p.disbursement.rule", string="Parent Disbursement Rule", index=True
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env["res.company"]._company_default_get(),
    )
    condition_select = fields.Selection(
        [("none", "Always True"), ("range", "Range"), ("python", "Python Expression")],
        string="Condition Based on",
        default="none",
        required=True,
    )
    condition_range = fields.Char(
        string="Range Based on",
        default="enrollment.disbursement_amount",
        help="This will be used to compute the % fields values; in general it is on basic, "
        "but you can also use categories code fields in lowercase as a variable names "
        "(hra, ma, lta, etc.) and the variable basic.",
    )
    condition_python = fields.Text(
        string="Python Condition",
        required=True,
        default="""
                    # Available variables:
                    #----------------------
                    # slip: object containing the slips
                    # beneficiary: openg2p.beneficiary object
                    # enrollment: openg2p.program.enrollment object
                    # rules: object containing the rules code (previously computed)
                    # categories: object containing the computed disbursement rule categories (sum of amount of all rules belonging to that category).
                    # inputs: object containing the computed inputs

                    # Note: returned value have to be set in the variable 'result'

                    result = rules.NET > categories.NET * 0.10""",
        help="Applied this rule for calculation if condition is true. You can specify condition like basic > 1000.",
    )
    condition_range_min = fields.Float(
        string="Minimum Range", help="The minimum amount, applied for this rule."
    )
    condition_range_max = fields.Float(
        string="Maximum Range", help="The maximum amount, applied for this rule."
    )
    amount_select = fields.Selection(
        [
            ("percentage", "Percentage (%)"),
            ("fix", "Fixed Amount"),
            ("code", "Python Code"),
        ],
        string="Amount Type",
        index=True,
        required=True,
        default="fix",
        help="The computation method for the rule amount.",
    )
    amount_fix = fields.Float(
        string="Fixed Amount", digits=dp.get_precision("Disbursement")
    )
    amount_percentage = fields.Float(
        string="Percentage (%)",
        digits=dp.get_precision("Disbursement Rate"),
        help="For example, enter 50.0 to apply a percentage of 50%",
    )
    amount_python_compute = fields.Text(
        string="Python Code",
        default="""
                    # Available variables:
                    #----------------------
                    # slip: object containing the slips
                    # beneficiary: openg2p.beneficiary object
                    # enrollment: openg2p.program.enrollment object
                    # rules: object containing the rules code (previously computed)
                    # categories: object containing the computed disbursement rule categories (sum of amount of all rules belonging to that category).
                    # inputs: object containing the computed inputs.

                    # Note: returned value have to be set in the variable 'result'

                    result = enrollment.disbursement_amount * 0.10""",
    )
    amount_percentage_base = fields.Char(
        string="Percentage based on", help="result will be affected to a variable"
    )
    child_ids = fields.One2many(
        "openg2p.disbursement.rule",
        "parent_rule_id",
        string="Child Disbursement Rule",
        copy=True,
    )
    register_id = fields.Many2one(
        "openg2p.disbursement.contribution.register",
        string="Contribution Register",
        help="Eventual third party involved in the disbursement disbursement of the beneficiaries. "
        "e.g. payment for mobile money transfer",
    )
    input_ids = fields.One2many(
        "openg2p.disbursement.rule.input", "input_id", string="Inputs", copy=True
    )
    note = fields.Text(string="Description")

    @api.constrains("parent_rule_id")
    def _check_parent_rule_id(self):
        if not self._check_recursion(parent="parent_rule_id"):
            raise ValidationError(
                _("Error! You cannot create recursive hierarchy of Disbursement Rules.")
            )

    @api.multi
    def _recursive_search_of_rules(self):
        """
        @return: returns a list of tuple (id, sequence) which are all the children of the passed rule_ids
        """
        children_rules = []
        for rule in self.filtered(lambda rule: rule.child_ids):
            children_rules += rule.child_ids._recursive_search_of_rules()
        return [(rule.id, rule.sequence) for rule in self] + children_rules

    # TODO should add some checks on the type of result (should be float)
    @api.multi
    def _compute_rule(self, localdict):
        """
        :param localdict: dictionary containing the environement in which to compute the rule
        :return: returns a tuple build as the base/amount computed, the quantity and the rate
        :rtype: (float, float, float)
        """
        self.ensure_one()
        if self.amount_select == "fix":
            try:
                return (
                    self.amount_fix,
                    float(safe_eval(self.quantity, localdict)),
                    100.0,
                )
            except:
                raise UserError(
                    _("Wrong quantity defined for disbursement rule %s (%s).")
                    % (self.name, self.code)
                )
        elif self.amount_select == "percentage":
            try:
                return (
                    float(safe_eval(self.amount_percentage_base, localdict)),
                    float(safe_eval(self.quantity, localdict)),
                    self.amount_percentage,
                )
            except:
                raise UserError(
                    _(
                        "Wrong percentage base or quantity defined for disbursement rule %s (%s)."
                    )
                    % (self.name, self.code)
                )
        else:
            try:
                safe_eval(
                    self.amount_python_compute, localdict, mode="exec", nocopy=True
                )
                return (
                    float(localdict["result"]),
                    "result_qty" in localdict and localdict["result_qty"] or 1.0,
                    "result_rate" in localdict and localdict["result_rate"] or 100.0,
                )
            except:
                raise UserError(
                    _("Wrong python code defined for disbursement rule %s (%s).")
                    % (self.name, self.code)
                )

    @api.multi
    def _satisfy_condition(self, localdict):
        """
        @param enrollment_id: id of openg2p.program.enrollment to be tested
        @return: returns True if the given rule match the condition for the given enrollment. Return False otherwise.
        """
        self.ensure_one()

        if self.condition_select == "none":
            return True
        elif self.condition_select == "range":
            try:
                result = safe_eval(self.condition_range, localdict)
                return (
                    self.condition_range_min <= result
                    and result <= self.condition_range_max
                    or False
                )
            except:
                raise UserError(
                    _("Wrong range condition defined for disbursement rule %s (%s).")
                    % (self.name, self.code)
                )
        else:  # python code
            try:
                safe_eval(self.condition_python, localdict, mode="exec", nocopy=True)
                return "result" in localdict and localdict["result"] or False
            except:
                raise UserError(
                    _("Wrong python condition defined for disbursement rule %s (%s).")
                    % (self.name, self.code)
                )
