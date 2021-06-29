# -*- coding: utf-8 -*-
# Copyright 2020 OpenG2P (https://openg2p.org)
# @author: Salton Massally <saltonmassally@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging

from odoo import models, _
from odoo.exceptions import ValidationError
from odoo.tools import formatLang

_logger = logging.getLogger(__name__)


class BatchExportXlsx(models.AbstractModel):
    _name = "report.openg2p_disbursement.batch_export_xlsx"
    _inherit = "report.report_xlsx.abstract"

    def _batch_report_colspec(self):
        colspec = {
            "name": {
                "header": {
                    "value": "Name",
                },
                "data": {
                    "value": self._render("beneficiary.name"),
                },
                "width": 40,
                "sequence": 1,
            },
            "ref": {
                "header": {
                    "value": "ID #",
                },
                "data": {
                    "value": self._render("beneficiary.ref"),
                },
                "width": 10,
                "sequence": 2,
            },
            "location": {
                "header": {
                    "value": "Location",
                },
                "data": {
                    "value": self._render("beneficiary.location_id.display_name"),
                },
                "width": 30,
                "sequence": 3,
            },
        }
        colspec.update(self._get_columns())
        return colspec

    def _get_ws_params(self, wb, data, batch):
        if len(batch) > 1:
            raise ValidationError(
                _(
                    "This report can only be generated with one disbursement batch at a time"
                )
            )

        spec = self._batch_report_colspec()
        cols = [
            i[0]
            for i in sorted(
                [(key, value["sequence"]) for key, value in spec.items()],
                key=lambda x: x[1],
            )
        ]

        return [
            {
                "ws_name": (batch.name[:28] + "..")
                if len(batch.name) > 30
                else batch.name,
                "generate_ws_method": "_batch_report",
                "title": "Disbursement Report- " + batch.name,
                "wanted_list": cols,
                "col_specs": spec,
            }
        ]

    def _get_columns(self):
        """
        returns the number of columns
        """
        template = {}
        # we want to get our sequence right so we are doing this
        sequence = 100
        for rule in self.env["openg2p.disbursement.rule"].search(
            [("appears_on_slip", "=", True)]
        ):
            template[rule.code] = {
                "header": {
                    "value": rule.name,
                },
                "data": {
                    "value": self._render("slip_lines['%s']" % (rule.code,)),
                },
                "width": max(20, len(rule.name)),
                "sequence": sequence,
            }
            sequence += 1
        return template

    def _batch_report(self, workbook, ws, ws_params, data, batch):

        ws.set_portrait()
        ws.fit_to_pages(1, 0)
        ws.set_header(self.xls_headers["standard"])
        ws.set_footer(self.xls_footers["standard"])

        self._set_column_width(ws, ws_params)

        row_pos = 0
        if len(batch) == 1:
            ws_params["title"] = (
                batch.name + " - Draft Report" if batch.state_approved else "Report"
            )
        row_pos = self._write_ws_title(ws, row_pos, ws_params)
        row_pos = self._write_line(
            ws,
            row_pos,
            ws_params,
            col_specs_section="header",
            default_format=self.format_theader_blue_center,
        )
        ws.freeze_panes(row_pos, 0)

        wl = ws_params["wanted_list"]
        batch_totals = {}
        batch_lines = {}
        for slip in batch.slip_ids:
            slip_data = {}
            for line in slip.details_by_disbursement_rule_category:
                slip_data[line.disbursement_rule_id.code] = formatLang(
                    self.env, line.total, currency_obj=slip.currency_id
                )
                if line.disbursement_rule_id.code not in batch_totals:
                    batch_totals[line.disbursement_rule_id.code] = line.total
                else:
                    batch_totals[line.disbursement_rule_id.code] += line.total
            batch_lines[slip.id] = slip_data
            row_pos = self._write_line(
                ws,
                row_pos,
                ws_params,
                col_specs_section="data",
                render_space={
                    "beneficiary": slip.beneficiary_id,
                    "slip": slip,
                    "slip_lines": slip_data,
                },
                default_format=self.format_tcell_left,
            )
