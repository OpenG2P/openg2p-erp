# -*- coding: utf-8 -*-
from odoo import models, fields, api


class EmploymentInactivate(models.TransientModel):
    _name = "wiz.deregistration"
    _description = "Beneficiary Deregistration Wizard"

    date = fields.Date(
        "Effective Date",
        required=True,
    )
    reason_id = fields.Many2one(
        "openg2p.deregistration.reason", "Reason", required=True
    )
    program_id = fields.Many2one(
        "openg2p.program",
        string="Program",
    )
    notes = fields.Text(
        "Notes",
    )
    type = fields.Selection(
        [
            ("program", "Disenroll from a Program"),
            ("database", "End all Programs and Archive"),
        ],
        required=True,
    )

    @api.multi
    def apply(self):
        self.ensure_one()
        res = self.env["openg2p.deregistration"]
        for rec in self.env.context.get("active_ids"):
            vals = {
                "date": self.date,
                "beneficiary_id": rec,
                "reason_id": self.reason_id.id,
                "notes": self.notes,
                "type": self.type,
                "program_id": self.program_id.id,
            }
            res += self.env["openg2p.deregistration"].create(vals)
        action = self.env.ref(
            "openg2p_deregistration.open_openg2p_deregistration"
        ).read()[0]
        action["domain"] = str(
            [
                ("id", "in", res.ids),
            ]
        )
        return action
