# -*- coding: utf-8 -*-
from odoo import api, models, fields, _


class Openg2pDisbursementBatch(models.Model):
    _inherit = "openg2p.disbursement.batch"

    amendment_count = fields.Integer(
        readonly=True, compute="_compute_amendment_count", store=False
    )

    unassigned_amendment_count = fields.Integer(
        readonly=True,
        compute="_compute_amendment_count",
        string="Unassigned Amendments",
        store=False,
    )

    @api.multi
    def close_slip_run(self):
        self.env["openg2p.disbursement.amendment"].search(
            [("batch_id", "=", self.ids), ("state", "=", "validate")]
        ).action_done()
        super(Openg2pDisbursementBatch, self).close_slip_run()

    @api.multi
    def _compute_amendment_count(self):
        for rec in self:
            rec.amendment_count = self.env[
                "openg2p.disbursement.amendment"
            ].search_count(
                [
                    ("batch_id", "=", rec.id),
                    ("state", "!=", "cancel"),
                    ("program_id", "=", rec.program_id.id),
                ]
            )
            x = self.env["openg2p.disbursement.amendment"].search_count(
                [
                    ("batch_id", "=", False),
                    ("date", "<=", rec.date_end),
                    ("state", "in", ("draft", "validate")),
                    ("program_id", "=", rec.program_id.id),
                ]
            )
            rec.active_deregistration_count = self.env[
                "openg2p.disbursement.amendment"
            ].search_count(
                [
                    ("batch_id", "=", False),
                    ("date", "<=", rec.date_end),
                    ("state", "in", ("draft", "validate")),
                    ("program_id", "=", rec.program_id.id),
                ]
            )

    @api.multi
    def view_batch_amendments(self):
        """Replace the static action used to call the wizard"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("View Amendments"),
            "res_model": "openg2p.disbursement.amendment",
            "domain": ("[('batch_id','=',%s)]" % (self.id)),
            "view_type": "form",
            "view_mode": "tree,form",
            "view_id": False,
            "target": "current",
        }
