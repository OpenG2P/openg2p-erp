from odoo import api, models
import logging


_logger = logging.getLogger(__name__)


class Openg2pRegistrationOrgFunctions(models.Model):
    _inherit = "openg2p.registration"

    # example for filtering on org custom fields
    @api.depends("org_custom_field")
    def _compute_org_fields(self):
        for rec in self:
            field = self.env["openg2p.registration.orgmap"].search(
                [
                    "&",
                    ("regd_id", "=", rec.id),
                    ("field_name", "=", "total_student_in_attendance_at_the_school"),
                ]
            )
            try:
                rec.attendance = int(field.field_value) if field else 0
            except BaseException as e:
                rec.attendance = 0

            field = self.env["openg2p.registration.orgmap"].search(
                [
                    "&",
                    ("regd_id", "=", rec.id),
                    ("field_name", "=", "regression_and_progression"),
                ]
            )
            try:
                rec.regression_and_progression = int(field.field_value) if field else 0
            except BaseException as e:
                rec.regression_and_progression = 0

            field = self.env["openg2p.registration.orgmap"].search(
                ["&", ("regd_id", "=", rec.id), ("field_name", "=", "total_quality")]
            )
            try:
                rec.total_quality = int(field.field_value) if field else 0
            except BaseException as e:
                rec.total_quality = 0

            field = self.env["openg2p.registration.orgmap"].search(
                ["&", ("regd_id", "=", rec.id), ("field_name", "=", "total_equity")]
            )
            try:
                rec.total_equity = int(field.field_value) if field else 0
            except BaseException as e:
                rec.total_equity = 0

            field = self.env["openg2p.registration.orgmap"].search(
                ["&", ("regd_id", "=", rec.id), ("field_name", "=", "grand_total")]
            )
            try:
                rec.grand_total = int(field.field_value) if field else 0
            except BaseException as e:
                rec.grand_total = 0

            field = self.env["openg2p.registration.orgmap"].search(
                [
                    "&",
                    ("regd_id", "=", rec.id),
                    ("field_name", "=", "is_the_school_approved"),
                ]
            )
            try:
                if field.field_value != "yes":
                    rec.school_approved = "no"
                else:
                    rec.school_approved = "yes"
            except BaseException as e:
                _logger.error(e)
                rec.school_approved = "no"

    # example for filtering on org custom fields
    def _search_att(self, operator, val2):
        res = []
        regds = self.env["openg2p.registration"].search([])
        for rec in regds:
            val = rec.attendance
            if operator == ">":
                if val > val2:
                    res.append(rec.id)
            elif operator == "<":
                if val < val2:
                    res.append(rec.id)
            elif operator == "=":
                if val == val2:
                    res.append(rec.id)
            elif operator == "!=":
                if val != val2:
                    res.append(rec.id)
            elif operator == ">=":
                if val >= val2:
                    res.append(rec.id)
            elif operator == "<=":
                if val <= val2:
                    res.append(rec.id)
        return [("id", "in", res)]

    # example for filtering on org custom fields
    def _search_r_and_p(self, operator, val2):
        res = []
        regds = self.env["openg2p.registration"].search([])
        for rec in regds:
            val = rec.regression_and_progression
            if operator == ">":
                if val > val2:
                    res.append(rec.id)
            elif operator == "<":
                if val < val2:
                    res.append(rec.id)
            elif operator == "=":
                if val == val2:
                    res.append(rec.id)
            elif operator == "!=":
                if val != val2:
                    res.append(rec.id)
            elif operator == ">=":
                if val >= val2:
                    res.append(rec.id)
            elif operator == "<=":
                if val <= val2:
                    res.append(rec.id)
        return [("id", "in", res)]

    # example for filtering on org custom fields
    def _search_tot_quality(self, operator, val2):
        res = []
        regds = self.env["openg2p.registration"].search([])
        for rec in regds:
            val = rec.total_quality
            if operator == ">":
                if val > val2:
                    res.append(rec.id)
            elif operator == "<":
                if val < val2:
                    res.append(rec.id)
            elif operator == "=":
                if val == val2:
                    res.append(rec.id)
            elif operator == "!=":
                if val != val2:
                    res.append(rec.id)
            elif operator == ">=":
                if val >= val2:
                    res.append(rec.id)
            elif operator == "<=":
                if val <= val2:
                    res.append(rec.id)
        return [("id", "in", res)]

    # example for filtering on org custom fields
    def _search_tot_equity(self, operator, val2):
        res = []
        regds = self.env["openg2p.registration"].search([])
        for rec in regds:
            val = rec.total_equity
            if operator == ">":
                if val > val2:
                    res.append(rec.id)
            elif operator == "<":
                if val < val2:
                    res.append(rec.id)
            elif operator == "=":
                if val == val2:
                    res.append(rec.id)
            elif operator == "!=":
                if val != val2:
                    res.append(rec.id)
            elif operator == ">=":
                if val >= val2:
                    res.append(rec.id)
            elif operator == "<=":
                if val <= val2:
                    res.append(rec.id)
        return [("id", "in", res)]

    # example for filtering on org custom fields
    def _search_grand_tot(self, operator, val2):
        res = []
        regds = self.env["openg2p.registration"].search([])
        for rec in regds:
            val = rec.grand_total
            if operator == ">":
                if val > val2:
                    res.append(rec.id)
            elif operator == "<":
                if val < val2:
                    res.append(rec.id)
            elif operator == "=":
                if val == val2:
                    res.append(rec.id)
            elif operator == "!=":
                if val != val2:
                    res.append(rec.id)
            elif operator == ">=":
                if val >= val2:
                    res.append(rec.id)
            elif operator == "<=":
                if val <= val2:
                    res.append(rec.id)
        return [("id", "in", res)]

    # example for another filtering on org custom fields
    def _search_approved(self, operator, val2):
        res = []
        regds = self.env["openg2p.registration"].search([])
        for rec in regds:
            if isinstance(val2, bool):
                continue
            try:
                val = rec.school_approved
            except BaseException as e:
                _logger.error(e)
                continue
            if operator == "=":
                if val == val2:
                    res.append(rec.id)
            elif operator == "!=":
                if val != val2:
                    res.append(rec.id)
        return [("id", "in", res)]

    def _get_default_odk_map(self):
        from .openg2p_submission_registration_map import odk_map_data

        return odk_map_data
