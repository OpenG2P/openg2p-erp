# -*- coding:utf-8 -*-

from odoo import api, models, _
from odoo.exceptions import UserError


class ContributionRegisterReport(models.AbstractModel):
    _name = "report.openg2p_disbursement.report_contributionregister"
    _description = "Disbursement Contribution Register Report"

    def _get_slip_lines(self, register_ids, batch_ids):
        result = {}
        self.env.cr.execute(
            """
            SELECT pl.id from openg2p_disbursement_slip_line as pl
            LEFT JOIN openg2p_disbursement_slip AS hp on (pl.slip_id = hp.id)
            WHERE hp.batch_id in %s
            AND pl.register_id in %s
            AND hp.state = 'done'
            ORDER BY pl.slip_id, pl.sequence""",
            (tuple(batch_ids), tuple(register_ids)),
        )
        line_ids = [x[0] for x in self.env.cr.fetchall()]
        for line in self.env["openg2p.disbursement.slip.line"].browse(line_ids):
            result.setdefault(
                line.register_id.id, self.env["openg2p.disbursement.slip.line"]
            )
            result[line.register_id.id] += line
        return result

    @api.model
    def _get_report_values(self, docids, data=None):
        if not data.get("form"):
            raise UserError(
                _("Form content is missing, this report cannot be printed.")
            )

        register_ids = self.env.context.get("active_ids", [])
        contrib_registers = self.env[
            "openg2p.disbursement.contribution.register"
        ].browse(register_ids)
        batch = data["form"].get("batch_id")

        if not batch:
            UserError(_("Batch needs to be specified"))

        batch = self.env["openg2p.disbursement.batch"].browse(batch)
        lines_data = self._get_slip_lines(register_ids, batch.ids)
        lines_total = {}
        for register in contrib_registers:
            lines = lines_data.get(register.id)
            lines_total[register.id] = lines and sum(lines.mapped("total")) or 0.0

        data["form"]["program_name"] = batch.program_id.name
        data["form"]["batch_name"] = batch.name
        data["form"]["date_from"] = batch.date_start
        data["form"]["date_to"] = batch.date_end
        return {
            "doc_ids": register_ids,
            "doc_model": "openg2p.disbursement.contribution.register",
            "docs": contrib_registers,
            "data": data,
            "lines_data": lines_data,
            "lines_total": lines_total,
        }
