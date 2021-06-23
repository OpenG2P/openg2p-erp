# -*- coding: utf-8 -*-
# Copyright 2020 OpenG2P (https://openg2p.org)
# @author: Salton Massally <saltonmassally@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class Openg2pDisbursementReconciliation(models.TransientModel):
    _name = "openg2p.disbursement.reconciliation"
    _description = "Print Reconciliation Report"

    def _default_previous_batch(self):
        batch_obj = self.env["openg2p.disbursement.batch"]
        current_batch = batch_obj.browse(self.env.context["active_id"])
        previous_batch = batch_obj.search(
            [
                ("date_start", "<", current_batch.date_start),
                ("program_id", "=", current_batch.program_id.id),
            ],
            order="date_start desc, id desc",
            limit=1,
        )
        if previous_batch:
            return previous_batch.id

    current_batch_id = fields.Many2one(
        "openg2p.disbursement.batch",
        "Current Batch",
        required=True,
        default=lambda self: self.env.context["active_id"],
    )
    program_id = fields.Many2one(
        "openg2p.program",
        "Program",
        related="current_batch_id.program_id",
        readonly=True,
    )
    previous_batch_id = fields.Many2one(
        "openg2p.disbursement.batch",
        "Previous Batch",
        required=True,
        default=_default_previous_batch,
    )

    @api.constrains("current_batch_id", "previous_batch_id")
    @api.multi
    def _constraint_program(self):
        for rec in self:
            if rec.current_batch_id.program_id != self.previous_batch_id.program_id:
                raise ValidationError(
                    _("Batches being compared should be of the same program")
                )

            if rec.current_batch_id == rec.previous_batch_id:
                raise ValidationError("Current and Previous Batch cannot be the same")

    @api.multi
    def _get_modifications(self):
        # @TODO performance improvements needed here
        self.ensure_one()
        modifications = []
        previous_batch_ee = self.previous_batch_id.slip_ids.mapped("beneficiary_id")
        current_batch_ee = self.current_batch_id.slip_ids.mapped("beneficiary_id")

        additions = current_batch_ee - previous_batch_ee
        removals = previous_batch_ee - current_batch_ee
        retained = current_batch_ee & previous_batch_ee

        # let's get difference in GROSS between both batchs
        previous_lines = self.previous_batch_id.slip_ids.mapped("line_ids")
        previous_net_lines = previous_lines.filtered(
            lambda r: r.disbursement_rule_id.code == "GROSS"
        )
        current_lines = self.current_batch_id.slip_ids.mapped("line_ids")
        current_net_lines = current_lines.filtered(
            lambda r: r.disbursement_rule_id.code == "GROSS"
        )
        previous_net = sum(previous_net_lines.mapped("amount"))
        current_net = sum(current_net_lines.mapped("amount"))

        for beneficiary in additions:
            line = self.current_batch_id.slip_ids.filtered(
                lambda r: r.beneficiary_id == beneficiary
            ).line_ids.filtered(lambda r: r.disbursement_rule_id.code == "GROSS")
            modifications.append(
                (
                    "Addition",
                    beneficiary.display_name,
                    beneficiary.ref,
                    beneficiary.location_id.display_name,
                    "GROSS",
                    line.amount,
                    0.0,
                )
            )
        for beneficiary in removals:
            line = self.previous_batch_id.slip_ids.filtered(
                lambda r: r.beneficiary_id == beneficiary
            ).line_ids.filtered(lambda r: r.disbursement_rule_id.code == "GROSS")
            modifications.append(
                (
                    "Removal",
                    beneficiary.display_name,
                    beneficiary.ref,
                    beneficiary.location_id.display_name,
                    "GROSS",
                    0.0,
                    line.amount,
                )
            )

        disbursement_rules = self.previous_batch_id.slip_ids.mapped(
            "line_ids.disbursement_rule_id"
        ) | self.current_batch_id.slip_ids.mapped("line_ids.disbursement_rule_id")
        disbursement_rules = disbursement_rules.filtered(
            lambda r: r.category_id.code in ("BASE", "ADD")
        )

        for beneficiary in retained:
            prev_slip = self.previous_batch_id.slip_ids.filtered(
                lambda r: r.beneficiary_id == beneficiary
            )
            current_slip = self.current_batch_id.slip_ids.filtered(
                lambda r: r.beneficiary_id == beneficiary
            )

            for rule in disbursement_rules:
                previous_line = prev_slip.line_ids.filtered(
                    lambda r: r.disbursement_rule_id == rule
                )
                current_line = current_slip.line_ids.filtered(
                    lambda r: r.disbursement_rule_id == rule
                )
                prev_amount = previous_line and previous_line.amount or 0.0
                current_amount = current_line and current_line.amount or 0.0
                if abs(prev_amount - current_amount) > 0.5:
                    modifications.append(
                        (
                            "Modification",
                            beneficiary.display_name,
                            beneficiary.ref,
                            beneficiary.location_id.display_name,
                            rule.code,
                            current_amount,
                            prev_amount,
                        )
                    )
        return previous_net, current_net, modifications

    @api.multi
    def print_report(self):
        self.ensure_one()
        previous_net, current_net, modifications = self._get_modifications()
        data = {
            "current_batch": self.current_batch_id.name,
            "previous_batch": self.previous_batch_id.name,
            "modifications": modifications,
            "current_net": current_net,
            "previous_net": previous_net,
            "difference_net": current_net - previous_net,
            "current_id": self.current_batch_id.id,
            "previous_id": self.previous_batch_id.id,
        }
        return self.env.ref(
            "openg2p_disbursement_reconciliation.action_report_reconcile"
        ).report_action(self.current_batch_id, data=data)
