# -*- coding:utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models


class SlipDetailsReport(models.AbstractModel):
    _name = "report.openg2p_disbursement.report_slipdetails"
    _description = "Disbursement Slip Details Report"

    def get_details_by_rule_category(self, slip_lines):
        SlipLine = self.env["openg2p.disbursement.slip.line"]
        RuleCateg = self.env["openg2p.disbursement.rule.category"]

        def get_recursive_parent(current_rule_category, rule_categories=None):
            if rule_categories:
                rule_categories = current_rule_category | rule_categories
            else:
                rule_categories = current_rule_category

            if current_rule_category.parent_id:
                return get_recursive_parent(
                    current_rule_category.parent_id, rule_categories
                )
            else:
                return rule_categories

        res = {}
        result = {}

        if slip_lines:
            self.env.cr.execute(
                """
                SELECT pl.id, pl.category_id, pl.slip_id FROM openg2p_disbursement_slip_line as pl
                LEFT JOIN openg2p_disbursement_rule_category AS rc on (pl.category_id = rc.id)
                WHERE pl.id in %s
                GROUP BY rc.parent_id, pl.sequence, pl.id, pl.category_id
                ORDER BY pl.sequence, rc.parent_id""",
                (tuple(slip_lines.ids),),
            )
            for x in self.env.cr.fetchall():
                result.setdefault(x[2], {})
                result[x[2]].setdefault(x[1], [])
                result[x[2]][x[1]].append(x[0])
            for slip_id, lines_dict in result.items():
                res.setdefault(slip_id, [])
                for rule_categ_id, line_ids in lines_dict.items():
                    rule_categories = RuleCateg.browse(rule_categ_id)
                    lines = SlipLine.browse(line_ids)
                    level = 0
                    for parent in get_recursive_parent(rule_categories):
                        res[slip_id].append(
                            {
                                "rule_category": parent.name,
                                "name": parent.name,
                                "code": parent.code,
                                "level": level,
                                "total": sum(lines.mapped("total")),
                            }
                        )
                        level += 1
                    for line in lines:
                        res[slip_id].append(
                            {
                                "rule_category": line.name,
                                "name": line.name,
                                "code": line.code,
                                "total": line.total,
                                "level": level,
                            }
                        )
        return res

    def get_lines_by_contribution_register(self, slip_lines):
        result = {}
        res = {}
        for line in slip_lines.filtered("register_id"):
            result.setdefault(line.slip_id.id, {})
            result[line.slip_id.id].setdefault(line.register_id, line)
            result[line.slip_id.id][line.register_id] |= line
        for slip_id, lines_dict in result.items():
            res.setdefault(slip_id, [])
            for register, lines in lines_dict.items():
                res[slip_id].append(
                    {
                        "register_name": register.name,
                        "total": sum(lines.mapped("total")),
                    }
                )
                for line in lines:
                    res[slip_id].append(
                        {
                            "name": line.name,
                            "code": line.code,
                            "quantity": line.quantity,
                            "amount": line.amount,
                            "total": line.total,
                        }
                    )
        return res

    @api.model
    def _get_report_values(self, docids, data=None):
        slips = self.env["openg2p.disbursement.slip"].browse(docids)
        return {
            "doc_ids": docids,
            "doc_model": "openg2p.disbursement.slip",
            "docs": slips,
            "data": data,
            "get_details_by_rule_category": self.get_details_by_rule_category(
                slips.mapped("details_by_disbursement_rule_category").filtered(
                    lambda r: r.appears_on_slip
                )
            ),
            "get_lines_by_contribution_register": self.get_lines_by_contribution_register(
                slips.mapped("line_ids").filtered(lambda r: r.appears_on_slip)
            ),
        }
