# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, _
from odoo.exceptions import AccessError


class Digest(models.Model):
    _inherit = "digest.digest"

    kpi_openg2p_registration_new_beneficiaries = fields.Boolean("Beneficiaries")
    kpi_openg2p_registration_new_beneficiaries_value = fields.Integer(
        compute="_compute_kpi_openg2p_registration_new_beneficiaries_value"
    )

    def _compute_kpi_openg2p_registration_new_beneficiaries_value(self):
        if not self.env.user.has_group(
            "openg2p_registration.group_openg2p_registration_user"
        ):
            raise AccessError(
                _("Do not have access, skip this data for user's digest email")
            )
        for record in self:
            start, end, company = record._get_kpi_compute_parameters()
            new_beneficiaries = self.env["openg2p.beneficiary"].search_count(
                [
                    ("registered_date", ">=", start),
                    ("registered_date", "<", end),
                    ("company_id", "=", company.id),
                ]
            )
            record.kpi_openg2p_registration_new_beneficiaries_value = new_beneficiaries

    def compute_kpis_actions(self, company, user):
        res = super(Digest, self).compute_kpis_actions(company, user)
        res["kpi_openg2p_registration_new_beneficiaries"] = (
            "openg2p.open_view_beneficiary_list_my&menu_id=%s"
            % self.env.ref("openg2p.menu_openg2p_root").id
        )
        return res
