# -*- coding: utf-8 -*-
# Copyright 2020 OpenG2P (https://openg2p.org)
# @author: Salton Massally <saltonmassally@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError


class Openg2pDisbursementBatch(models.Model):
    _inherit = "openg2p.disbursement.batch"

    advice_count = fields.Integer(
        compute="_compute_advice_status",
        readonly=True,
    )
    advice_ids = fields.One2many(
        "openg2p.disbursement.advice", "batch_id", "Bank Advices"
    )
    advice_line_ids = fields.One2many(
        "openg2p.disbursement.advice.line", "batch_id", "Bank Advices Instructions"
    )
    count_advised_slips = fields.Integer(
        _compute="_compute_advice_status",
        readonly=True,
    )
    count_not_advised_slips = fields.Integer(
        _compute="_compute_advice_status",
        readonly=True,
    )
    no_advice_bank = fields.Many2one(
        "res.bank",
        string="No Account Beneficiaries",
        help="This bank will handle beneficiaries without any payment account on their record",
    )

    @api.depends("advice_line_ids", "advice_line_ids.state")
    @api.multi
    def _compute_advice_status(self):
        for batch in self:
            batch.advice_count = len(batch.advice_ids)
            count_advised_slips = len(
                batch.advice_line_ids.filtered(lambda r: r.state != "cancel")
            )
            batch.count_advised_slips = count_advised_slips
            batch.count_not_advised_slips = len(batch.slip_ids) - count_advised_slips

    @api.multi
    def start_disbursing_slip_run(self):
        self.ensure_one()
        super(Openg2pDisbursementBatch, self).start_disbursing_slip_run()
        self.create_advice()

    @api.multi
    def action_view_exempted(self):
        self.ensure_one()
        exempted = self.slip_ids - self.advice_line_ids.filtered(
            lambda r: r.state != "cancel"
        ).mapped("slip_id")
        return {
            "name": "Slips Not Included in Advice",
            "view_type": "form",
            "view_mode": "tree,form",
            "res_model": "openg2p.disbursement.slip",
            "type": "ir.actions.act_window",
            "domain": [("id", "in", exempted.ids)],
            "context": self.env.context,
        }

    @api.multi
    def close_slip_run(self):
        if self.advice_ids.filtered(lambda r: r.state not in ("done", "cancel")):
            raise ValidationError(
                _(
                    "All advices should be either in the done or canceled state before batch can be"
                    " closed"
                )
            )
        super(Openg2pDisbursementBatch, self).close_slip_run()

    @api.multi
    def create_advice(self):
        self.ensure_one()
        advice_pool = self.env["openg2p.disbursement.advice"]
        if self.advice_ids.filtered(lambda r: r.state != "draft"):
            raise UserWarning(
                _("Cannot regenerate of an advice in a batch is past the draft stage")
                % self.name
            )

        self.advice_ids.unlink()

        # let's get all the banks in this run. We use plain sql for optimizationr easons
        query = """SELECT DISTINCT(account.bank_id) AS bank
        FROM openg2p_disbursement_slip AS slip
        LEFT JOIN openg2p_beneficiary AS beneficiary ON slip.beneficiary_id = beneficiary.id
        LEFT JOIN res_partner_bank AS account ON beneficiary.bank_account_id = account.id
        WHERE slip.batch_id = %s""" % (
            self.id,
        )

        self.env.cr.execute(query)
        banks = [x[0] for x in self.env.cr.fetchall() if x[0]]

        if not banks:
            raise UserError("No bank accounts attached to beneficiaries in this batch")

        banks = self.env["res.bank"].browse(banks)

        advices = self.env["openg2p.disbursement.advice"]
        for bank in banks:
            # let's find the company bank
            company = self.company_id

            advices += advice_pool.create(
                {
                    "batch_id": self.id,
                    "company_id": company.id,
                    "name": "%s - %s Advice" % (self.name, bank.name),
                    "date": self.date_end,
                    "bank_id": bank.id,
                }
            )
        if self.no_advice_bank:
            bank = self.no_advice_bank
            advices += advice_pool.create(
                {
                    "batch_id": self.id,
                    "company_id": company.id,
                    "name": "%s - %s Advice" % (self.name, bank.name),
                    "date": self.date_end,
                    "bank_id": bank.id,
                }
            )
        return advices.compute_advice()
