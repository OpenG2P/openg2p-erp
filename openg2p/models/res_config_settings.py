# -*- coding: utf-8 -*-
# Copyright 2020 OpenG2P (https://openg2p.org)
# @author: Salton Massally <saltonmassally@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models, api, _


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    module_openg2p_beneficiary_relative = fields.Boolean(
        string="Record Beneficiaries Relatives Data"
    )
    module_openg2p_registration = fields.Boolean(
        string="Track Beneficiary Registrations"
    )
    module_openg2p_security = fields.Boolean(string="Advanced User Security Measures")
    module_openg2p_disbursement = fields.Boolean(
        string="Manage Disbursements to Beneficiaries"
    )
    module_openg2p_disbursement_advice = fields.Boolean(
        string="Manage Digital Payments to Beneficiaries"
    )
    module_openg2p_redressal = fields.Boolean(
        string="Record and Track issues reported by Beneficiaries"
    )
    beneficiary_id_gen_method = fields.Selection(
        related="company_id.beneficiary_id_gen_method", readonly=False
    )
    beneficiary_id_random_digits = fields.Integer(
        related="company_id.beneficiary_id_random_digits", readonly=False
    )
    beneficiary_id_sequence = fields.Many2one(
        "ir.sequence", related="company_id.beneficiary_id_sequence", readonly=False
    )
    country_id = fields.Many2one(
        "res.country", related="company_id.country_id", readonly=False
    )
    currency_id = fields.Many2one(
        "res.currency", related="company_id.currency_id", readonly=False
    )

    @api.onchange("country_id")
    def onchange_country(self):
        self.ensure_one()
        if self.country_id:
            self.currency_id = self.country_id.currency_id

    @api.multi
    def open_main_company(self):
        context = dict(self.env.context)
        context["form_view_initial_mode"] = "edit"
        return {
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "form",
            "res_model": "res.company",
            "res_id": self.env.ref("base.main_company").id,
            "context": context,
        }

    @api.multi
    def open_banks(self):
        return {
            "name": _("Financial Service Providers"),
            "type": "ir.actions.act_window",
            "res_model": "res.bank",
            "view_type": "form",
            "view_mode": "tree,form",
            "context": dict(self.env.context),
        }

    @api.multi
    def open_locations(self):
        return {
            "name": _("Beneficiary Locations"),
            "type": "ir.actions.act_window",
            "res_model": "openg2p.location",
            "view_type": "form",
            "view_mode": "tree,form",
            "context": dict(self.env.context),
        }

    @api.multi
    def open_external_ids(self):
        return {
            "name": _("External Identifications"),
            "type": "ir.actions.act_window",
            "res_model": "openg2p.beneficiary.id_category",
            "view_type": "form",
            "view_mode": "tree,form",
            "context": dict(self.env.context),
        }

    @api.multi
    def open_states(self):
        context = dict(self.env.context)
        country = self.env.ref("base.main_company").country_id
        context["default_country_id"] = country.id
        return {
            "name": _("States/Districts"),
            "type": "ir.actions.act_window",
            "res_model": "res.country.state",
            "view_type": "form",
            "view_mode": "tree,form",
            "domain": [("country_id", "=", country.id)],
            "context": context,
        }
