# -*- coding: utf-8 -*-
from odoo import api, models, fields


class Openg2pDisbursementSlip(models.Model):
    _inherit = "openg2p.disbursement.slip"

    amendment_count = fields.Integer(readonly=True, compute="_compute_amendment_count")

    @api.multi
    def _compute_amendment_count(self):
        for rec in self:
            rec.amendment_count = self.env[
                "openg2p.disbursement.amendment"
            ].search_count([("slip_id", "=", rec.id)])

    @api.multi
    def compute_sheet(self):
        """
        let's add amendments
        """
        for slip in self:
            for input in slip.input_line_ids:
                input_rule = self.env["openg2p.disbursement.rule.input"].search(
                    [("code", "=", input.code)]
                )
                amendments = self.env["openg2p.disbursement.amendment"].search(
                    [
                        ("state", "=", "validate"),
                        ("program_id", "=", slip.batch_id.program_id.id),
                        ("beneficiary_id", "=", slip.beneficiary_id.id),
                        ("input_id", "=", input_rule.id),
                        ("date", "<=", slip.batch_id.date_end),
                        "|",
                        ("slip_id", "=", False),
                        ("slip_id", "=", slip.id),
                    ]
                )
                if not amendments:
                    input.amount = 0.0
                input.amount = sum(
                    amendments.mapped(
                        lambda r: r.category_id.type == "add"
                        and abs(r.amount)
                        or -(abs(r.amount))
                    )
                )
                amendments.write({"slip_id": slip.id})
        return super(Openg2pDisbursementSlip, self).compute_sheet()

    @api.multi
    def reset_amendments(self):
        self.env["openg2p.disbursement.amendment"].search(
            [("slip_id", "in", self.ids)]
        ).action_reset()

    @api.multi
    def unlink(self):
        self.reset_amendments()
        return super(Openg2pDisbursementSlip, self).unlink()

    @api.multi
    def cancel_sheet(self):
        self.reset_amendments()
        return super(Openg2pDisbursementSlip, self).cancel_sheet()
