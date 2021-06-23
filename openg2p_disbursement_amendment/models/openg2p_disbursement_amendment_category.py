# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError, Warning as UserWarning


class Openg2pDisbursementAmendmentCategory(models.Model):
    _name = "openg2p.disbursement.amendment.category"
    _inherit = ["generic.mixin.name_with_code", "generic.mixin.uniq_name_code"]

    type = fields.Selection(
        [("add", "Addition"), ("subtract", "Deduction")], required=True, default="add"
    )
    struct_id = fields.Many2one(
        "openg2p.disbursement.structure",
        "Disbursement Structure",
        required=True,
        help="Disbursement structure to add amendment category rule to",
        default=lambda self: self.env.ref("openg2p_disbursement.structure_base", False),
    )
    in_report = fields.Boolean("Show in Reports")
    rule_id = fields.Many2one(
        "openg2p.disbursement.rule", "Disbursement Rule", readonly=True
    )
    input_rule_id = fields.Many2one(
        "openg2p.disbursement.rule.input",
        "Input Rule",
        readonly=True,
    )
    active = fields.Boolean("Active", default=True)
    note = fields.Text("Description")

    @api.constrains("code")
    @api.multi
    def _check_code(self):
        # let's ensure that we do not already have disbursement rule with this code
        for rec in self:
            domain = []
            domain.append(("code", "=", rec.code))
            if rec.rule_id:
                domain.append(("id", "not in", (rec.rule_id.id,)))
            if self.env["openg2p.disbursement.rule"].search_count(domain) > 0:
                raise ValidationError(
                    "Amendment category code  %s conflicts with a disbursement rule code."
                    % (rec.code,)
                )

            # let's ensure that we do not already have input rule with this code
            domain = []
            domain.append(("code", "=", rec.code))
            if rec.input_rule_id:
                domain.append(("id", "not in", (rec.input_rule_id.id,)))
            if self.env["openg2p.disbursement.rule.input"].search_count(domain) > 0:
                raise ValidationError(
                    "Amendment category code %s conflicts with an input rule code."
                    % (rec.code,)
                )
        return True

    @api.model
    def create(self, vals):
        res = super(Openg2pDisbursementAmendmentCategory, self).create(vals)
        rule_obj = self.env["openg2p.disbursement.rule"]
        struct_obj = self.env["openg2p.disbursement.structure"]
        input_rule_obj = self.env["openg2p.disbursement.rule.input"]

        update = {}
        # creating payroll fields
        note = vals.get("note", False)
        if note:
            note += " - Auto created via payroll amendments"
        else:
            note = "Auto created via payroll amendments"

        # let's create a payroll rule for category
        if res.type == "add":
            rule_category = self.env.ref("openg2p_disbursement.ADD")
            sequence = 80
        else:
            rule_category = self.env.ref("openg2p_disbursement.DED")
            sequence = 102
        rule_data = {
            "code": vals["code"].upper(),
            "name": vals["name"],
            "category_id": rule_category.id,
            "condition_select": "python",
            "amount_select": "code",
            "amount_python_compute": "result = inputs.%s.amount"
            % (vals["code"].upper()),
            "sequence": sequence,
            "note": note,
            "condition_python": "result = inputs.%s and inputs.%s.amount"
            % (vals["code"].upper(), vals["code"].upper()),
        }
        rule = rule_obj.create(rule_data)
        update["rule_id"] = rule.id

        # let's create input rule for this category
        input_rule_data = {
            "code": vals["code"].upper(),
            "name": vals["name"],
            "input_id": rule.id,
        }
        input_rule = input_rule_obj.create(input_rule_data)
        update["input_rule_id"] = input_rule.id

        # let's assign to disbursement structure
        struct = struct_obj.browse(vals["struct_id"])
        struct.write(
            {
                "rule_ids": [
                    (4, rule.id),
                ],
            }
        )

        # lets update the category
        res.write(update)
        return res

    @api.multi
    def write(self, data):
        for category in self:
            if "code" in data and data["code"] != category.code:
                raise UserWarning(
                    "Sorry, you can't edit the code once it " "has been created"
                )
            # let's handle inactivation
            if "active" in data:
                category.rule_id.active = data["active"]

            # let's handle changes to type
            if "type" in data and category.rule_id:
                if data["type"] == "add":
                    rule_category = self.env.ref("openg2p_disbursement.ADD")
                    sequence = 80
                else:
                    rule_category = self.env.ref("openg2p_disbursement.DED")
                    sequence = 102
                category.rule_id.write(
                    {
                        "category_id": rule_category.id,
                        "sequence": sequence,
                    }
                )

            # let's handl cases in which we change the base structur
            if "struct_id" in data:
                category.struct_id.write(
                    {
                        "rule_ids": [
                            (3, category.rule_id.id),
                        ],
                    }
                )
                struct = self.env["openg2p.disbursement.structure"].browse(
                    data["struct_id"]
                )
                struct.write(
                    {
                        "rule_ids": [
                            (4, category.rule_id.id),
                        ],
                    }
                )

        return super(Openg2pDisbursementAmendmentCategory, self).write(data)

    @api.multi
    def copy(self):
        raise UserWarning("Disbursement category does not support duplication!")

    @api.multi
    def unlink(self):
        for category in self:
            category.rule_id.input_ids.unlink()
            category.rule_id.unlink()
            category.input_rule_id.unlink()
        return super(Openg2pDisbursementAmendmentCategory, self).unlink()
