from odoo import api, models
from odoo.exceptions import ValidationError


class ODKConfigService(models.Model):
    _inherit = "odk.config"

    def odk_button_update_form_submissions(self):
        self.call_submission()

    # Method executed by cron job to fetch submissions
    def cron_update_all_active_forms(self):
        configs = self.search([("is_active", "=", True)])
        configs.odk_button_update_all_form_submissions()
        return True

    # Method called by button to fetch submissions for all forms
    def odk_button_update_all_form_submissions(self):
        for config in self:
            print("Config: ", config.form_name)
            config.call_submission()

    # Method calling submissions call to fetch data
    def call_submission(self):
        submissions_obj = self.env["odk.submissions"]
        regd_ids = submissions_obj.update_submissions(self)
        print("Call Submission ends")

    def write(self, vals):
        res = super().write(vals)
        if self.program_enroll_date > self.program_id.date_start:
            raise ValidationError(
                "Program Enrollment start date must not be earlier  than program's start date."
            )
        return res

    @api.model
    def create(self, vals_list):
        res = super().create(vals_list)
        if res.program_enroll_date > res.program_id.date_start:
            raise ValidationError(
                "Program Enrollment start date must not be earlier  than program's start date."
            )
        return res
