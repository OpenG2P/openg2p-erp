# -*- coding: utf-8 -*-
# Copyright 2020 OpenG2P (https://openg2p.org)
# @author: Salton Massally <saltonmassally@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import re

import phonenumbers

from odoo import api, fields, models, _
from odoo.addons.base_iban.models.res_partner_bank import (
    validate_iban,
    pretty_iban,
    normalize_iban,
)
from odoo.exceptions import ValidationError


def validate_mobile_money(number):
    try:
        return phonenumbers.is_valid_number((phonenumbers.parse(number)))
    except:
        raise ValidationError(
            _("Supplied mobile money account %s is invalid" % (number,))
        )


class ResPartnerBank(models.Model):
    _name = "res.partner.bank"
    _rec_name = "name"
    _inherit = ["res.partner.bank", "mail.thread", "generic.mixin.no.unlink"]

    _allow_unlink_domain = [("state", "=", "draft")]

    name = fields.Char(store=True, compute="_compute_name", readonly=True)
    acc_number = fields.Char(
        index=True,
        required=True,
        track_visibility="onchange",
    )
    partner_id = fields.Many2one(related="beneficiary_id.partner_id")
    beneficiary_id = fields.Many2one(
        "openg2p.beneficiary",
        "Account Holder",
        index=True,
        track_visibility="onchange",
    )
    bank_id = fields.Many2one(
        index=True,
        required=True,
        track_visibility="onchange",
    )
    currency_id = fields.Many2one(
        default=lambda self: self.env.user.company_id.currency_id, readonly=True
    )

    @api.model
    def create(self, vals):
        if "acc_type" in vals and vals["acc_type"] == "iban":
            vals["acc_number"] = pretty_iban(normalize_iban(vals["acc_number"]))
        if "beneficiary_id" in vals and not "partner_id" in vals:
            vals["partner_id"] = (
                self.env["openg2p.beneficiary"]
                .browse(vals["beneficiary_id"])
                .partner_id
            )
        return super(ResPartnerBank, self).create(vals)

    @api.multi
    def write(self, vals):
        if vals.get("acc_number"):
            for rec in self:
                if rec.acc_type == "iban":
                    vals["acc_number"] = pretty_iban(normalize_iban(vals["acc_number"]))
        return super(ResPartnerBank, self).write(vals)

    @api.multi
    @api.depends("sanitized_acc_number", "acc_number", "bank_name")
    def _compute_name(self):
        for record in self:
            if record.bank_name:
                record.name = "%s (%s)" % (
                    record.sanitized_acc_number or record.acc_number,
                    record.bank_name,
                )
            else:
                record.name = record.sanitized_acc_number or record.acc_number

    @api.onchange("beneficiary_id")
    def onchange_beneficiary_id(self):
        self.ensure_one()
        if not self.acc_holder_name and self.beneficiary_id:
            self.acc_holder_name = self.beneficiary_id.name

        if self.beneficiary_id:
            self.partner_id = self.beneficiary_id.partner_id

    @api.constrains("beneficiary_id", "partner_id")
    def _constraint_acc_number(self):
        for acc in self:
            if (
                acc.beneficiary_id
                and not acc.beneficiary_id.partner_id == acc.partner_id
            ):
                raise ValidationError(
                    _("Account partner has not be the same as beneficiary")
                )

    @api.constrains("acc_number", "bank_id")
    def _constraint_acc_number(self):
        for acc in self:
            if acc.bank_id.validation_regex and not re.compile(
                acc.bank_id.validation_regex, re.IGNORECASE
            ).match(acc.acc_number):
                raise ValidationError(
                    _(
                        "Account number does not meet the expected pattern for "
                        + acc.bank_id.name
                    )
                )

            if acc.acc_type == "iban":
                validate_iban(acc.acc_number)
            elif acc.acc_type == "mobile":
                validate_mobile_money(acc.acc_number)

    @api.depends("acc_number")
    def _compute_acc_type(self):
        for bank in self:
            bank.acc_type = self.retrieve_acc_type(bank.acc_number, bank_account=bank)

    @api.model
    def retrieve_acc_type(self, acc_number, bank_account=None):
        if bank_account:
            bank_type = bank_account.bank_id.type
            if bank_type != "normal":
                return bank_type
        try:  # if normal we want iban and others to run
            validate_iban(acc_number)
            return "iban"
        except ValidationError:
            return super(ResPartnerBank, self).retrieve_acc_type(acc_number)

    @api.model
    def _get_supported_account_types(self):
        rslt = super(ResPartnerBank, self)._get_supported_account_types()
        rslt.append(("iban", _("IBAN")))
        rslt.append(("mobile", _("Mobile Money")))
        return rslt
