# -*- coding: utf-8 -*-
# Copyright 2020 OpenG2P (https://openg2p.org)
# @author: Salton Massally <saltonmassally@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from contextlib import contextmanager
from datetime import datetime

import odoo.addons.decimal_precision as dp
from odoo import _, api, fields, models
from odoo.addons.component.core import WorkContext
from odoo.addons.queue_job.job import job
from odoo.exceptions import UserError


class GatewayTransaction(models.Model):
    _name = "openg2p.gateway.transaction"
    _description = "Gateway Transaction"
    _order = "create_date desc"

    @property
    def get_provider(self):
        self.ensure_one()
        work = WorkContext(model_name=self._name, collection=self)
        return work.component_by_name("payment.service.%s" % self.provider)

    @property
    def get_all_providers(self):
        work = WorkContext(model_name=self._name, collection=self)
        return [provider for provider in work.many_components(usage="gateway.provider")]

    @api.model
    def _selection_execute_method(self):
        return self.env["res.bank"]._selection_execute_method()

    name = fields.Char()
    bank_account_id = fields.Many2one(
        "res.partner.bank", "Account", required=True, index=True
    )
    bank_id = fields.Many2one("res.bank", "Bank", required=True, index=True)
    provider = fields.Char(
        required=True,
    )
    partner_id = fields.Many2one(
        "res.partner",
        "Partner",
        required=True,
    )
    external_id = fields.Char(index=True)
    execute_method = fields.Selection(
        selection="_selection_execute_method", required=True
    )
    meta = fields.Serialized()
    amount = fields.Float(dp=dp.get_precision("Transaction"))
    currency_id = fields.Many2one("res.currency", "Currency", required=True)
    origin_id = fields.Reference(selection=[])
    res_model = fields.Char(
        compute="_compute_origin",
        store=True,
        index=True,
    )
    res_id = fields.Integer(
        compute="_compute_origin",
        store=True,
        index=True,
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("requested", "Requested"),  # request sent to provider
            ("done", "Succeeded"),
            ("cancel", "Cancel"),
            ("failed", "Failed"),
        ],
        required=True,
        default="draft",
    )
    receipt_confirmed = fields.Boolean()
    data = fields.Text()
    error = fields.Text()
    date_processed = fields.Datetime("Processed On")
    date_succeeded = fields.Datetime("Succeeded On")
    date_receipt_confirmed = fields.Datetime("Receipt Confirmed On")

    @api.multi
    @api.depends("origin_id")
    def _compute_origin(self):
        for record in self:
            record.res_id = record.origin_id.id
            record.res_model = record.origin_id._name

    @api.multi
    def _get_amount_to_execute(self):
        """
        Return the amount to execute depending on the target model
        :return: float
        """
        self.ensure_one()
        return self.origin_id._transaction_execution_amount()

    @api.multi
    def cancel(self):
        if self.filtered(lambda r: r.state in ("requested", "done")):
            raise UserError(_("Cannot cancel requested or done transaction"))
        return self.write({"state": "cancel"})

    def create(self, vals):
        res = super(GatewayTransaction, self).create(vals)
        if res.execute_method == "server2server":
            res._execute()

    @api.multi
    def reset(self):
        if self.filtered(lambda r: r.state in ("requested", "done")):
            raise UserError(_("Cannot reset transaction requested or done to execute"))
        self.write({"state": "draft", "date_processed": None, "error": None})
        self.filtered(lambda r: r.execute_method == "server2server")._execute()

    @api.multi
    def write(self, vals):
        result = super(GatewayTransaction, self).write(vals)
        if vals.get("state") == "draft":
            self.filtered(lambda r: r.execute_method == "server2server")._execute()
        return result

    def _prepare_transaction(self, origin, **kwargs):
        return {
            "name": origin._get_transaction_name(),
            "bank_account_id": origin.bank_account_id.id,
            "bank_id": origin.bank_account_id.bank_id.id,
            "execute_method": origin.bank_account_id.bank_id.execute_method,
            "currency_id": origin.currency_id.id,
            "origin_id": "%s,%s" % (origin._name, origin.id),
            "partner_id": origin.partner_id.id,
            "amount": origin._transaction_execution_amount(),
            "provider": origin.bank_account_id.bank_id.provider,
        }

    @api.model
    def register(self, origin, **kwargs):
        """
        creates transaction record
        """
        return self.create(self._prepare_transaction(origin, **kwargs))

    @api.multi
    def _execute(self):
        """
        sends transaction to the backend for processing
        :return: bool
        """
        for transaction in self:
            if transaction.state == "done":
                pass

            provider = transaction.get_provider
            vals = {"date_processed": datetime.now()}
            try:
                provider.execute()
                vals["state"] = "done" if provider.__sync_call else "requested"

                if provider.__sync_call:
                    vals["date_succeeded"] = vals["date_processed"]
            except Exception as e:
                vals["state"] = "failed"
                vals["error"] = str(e)
            transaction.write(vals)

    @api.multi
    def check_state(self):
        # @TODO let's have a cron here?
        for record in self:
            if record.state == "requested":
                record.write({"state": record.get_provider.get_state()})

    @job
    def process_webhook(self, provider_name, method_name, params):
        return self.get_provider.dispatch(method_name, params)
