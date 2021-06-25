# -*- coding: utf-8 -*-
# Copyright 2020 OpenG2P (https://openg2p.org)
# @author: Salton Massally <saltonmassally@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging

from odoo import models

_logger = logging.getLogger(__name__)


class BatchExportXlsx(models.AbstractModel):
    _inherit = "report.openg2p_disbursement.batch_export_xlsx"

    def _batch_report_colspec(self):
        colspec = super(BatchExportXlsx, self)._batch_report_colspec()
        colspec.update(
            {
                "bank": {
                    "header": {
                        "value": "Bank",
                    },
                    "data": {
                        "value": self._render(
                            "beneficiary.bank_account_id.bank_id.name or ''"
                        ),
                    },
                    "width": 20,
                    "sequence": 5,
                },
                "account": {
                    "header": {
                        "value": "Account Number",
                    },
                    "data": {
                        "value": self._render(
                            "beneficiary.bank_account_id.acc_number or ''"
                        ),
                    },
                    "width": 20,
                    "sequence": 6,
                },
            }
        )
        return colspec
