# -*- coding: utf-8 -*-
# Copyright 2020 OpenG2P (https://openg2p.org)
# @author: Salton Massally <saltonmassally@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval as eval

SEVERITY = ["low", "medium", "high", "critical"]

CONDITION_HELP = """
# Available variables:
#----------------------
# slip: object containing the disbursement slip
# enrollment: openg2p.program.enrollment object
# beneficiary: openg2p.beneficiary object

# Note: returned value have to be set in the variable 'result'

result = not bool(slip.line_ids) """


class Openg2pDisbursementExceptionRule(models.Model):
    _name = "openg2p.disbursement.exception.rule"

    name = fields.Char(required=True)
    sequence = fields.Integer(default=5)
    active = fields.Boolean(default=True)
    condition_python = fields.Text(
        "Python Condition", help=CONDITION_HELP, default=None
    )
    severity = fields.Selection(
        [
            ("low", "Low"),
            ("medium", "Medium"),
            ("high", "High"),
            ("critical", "Critical"),
        ],
        "Severity",
        default="medium",
        required=True,
    )
    note = fields.Text("Description")

    @api.multi
    def check_slip(self, slip):
        exception_model = self.env["openg2p.disbursement.exception"]
        localdict = dict(
            beneficiary=slip.beneficiary_id,
            registration=slip.enrollment_id,
            slip=slip,
            result=None,
        )
        for rule in self:
            if rule.condition_python and rule.satisfy_condition(localdict):
                exception_model.create({"rule_id": rule.id, "slip_id": slip.id})

    @api.multi
    def satisfy_condition(self, localdict):
        """
        @return: returns True if the given rule matches.
                 Return False otherwise.
        """
        self.ensure_one()
        try:
            eval(self.condition_python, localdict, mode="exec", nocopy=True)
            return "result" in localdict and localdict["result"] or False
        except Exception as e:
            raise UserError(
                "Wrong python condition defined for disbursement "
                "exception rule %s. \n %s" % (self.name, str(e))
            )
