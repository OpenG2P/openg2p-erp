# -*- coding: utf-8 -*-
# Copyright 2020 OpenG2P (https://openg2p.org)
# @author: Salton Massally <saltonmassally@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, models


class ReconcillationReport(models.AbstractModel):
    _name = "report.openg2p_disbursement_reconciliation.report_reconcile"

    @api.model
    def _get_report_values(self, docids, data=None):
        current = self.env["openg2p.disbursement.batch"].browse(data["current_id"])
        docargs = {
            "doc_ids": current.ids,
            "doc_model": "openg2p.disbursement.batch",
            "docs": current,
            "data": data,
            "currency": current.currency_id,
        }
        return docargs
