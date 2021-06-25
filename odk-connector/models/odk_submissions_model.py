# -*- coding: utf-8 -*-

from odoo import _
from odoo import api, fields, models
from .odk import ODK


class ODKSubmissions(models.Model):
    _name = "odk.submissions"
    _description = "ODK Form Submissions"
    _order = "submission_date desc"

    # Columns
    odk_submission_id = fields.Char(
        string="ODK Submission Instance ID", required=True, index=True, readonly=True
    )
    submission_date = fields.Datetime(
        string="Submission Date Time in ODK", required=True, readonly=True
    )
    odk_config_id = fields.Many2one(
        "odk.config", string="Configuration", required=True, readonly=True
    )
    submission_response = fields.Char(
        string="Form Response", required=True, readonly=True
    )
    odoo_corresponding_id = fields.Many2one(
        "openg2p.registration",
        string="OpenG2P Registration",
        help="Registration linked to the submission.",
        readonly=True,
    )

    # Method to update/sync submissions from a specific config
    def update_submissions(self, odk_config):
        updated_submissions_count = self.get_data_from_odk(odk_config)

        config = self.odk_update_configuration(
            {
                "odk_last_sync_date": fields.Datetime.now(),
                "odk_submissions_count": updated_submissions_count,
            },
            odk_config.id,
        )
        print("Successfully update config:", config)

    # Method responsible for getting new data from ODK
    def get_data_from_odk(self, odk_config):
        odk = ODK(
            odk_config.odk_endpoint,
            "submission",
            odk_config.odk_email,
            odk_config.odk_password,
        )
        count_response = odk.get(
            (odk_config.odk_project_id, odk_config.odk_form_id),
            {"$top": 0, "$count": "true"},
        )  # Call ODK API for new count

        last_count = odk_config.odk_submissions_count
        new_count = count_response["@odata.count"]
        remaining_count = new_count - last_count

        # Over here 100 is the batch size we're considering. And 5 is the offset for additional margin.
        while remaining_count > 100:
            top_count = 100 + 5  # $top
            skip_count = remaining_count - 100  # $skip

            # In case of high submission rate we can use '@odata.count' to check if new_count is still the same in the
            # subsequent calls. If the count goes up in the next calls we would need to offset that with $top and $skip
            submission_response = odk.get(
                (odk_config.odk_project_id, odk_config.odk_form_id),
                {"$top": top_count, "$skip": skip_count, "$count": "true"},
            )
            self.save_data_into_all(submission_response["value"], odk_config)

            last_count = last_count + 100
            remaining_count = new_count - last_count
        else:
            top_count = remaining_count + 5  # $top
            submission_response = odk.get(
                (odk_config.odk_project_id, odk_config.odk_form_id),
                {"$top": top_count, "$count": "true"},
            )
            self.save_data_into_all(submission_response["value"], odk_config)
        return new_count

    # Umbrella method to save data in odk.submissions and openg2p.registration
    def save_data_into_all(self, odk_response_data, odk_config):
        for value in odk_response_data:
            # Add check if the record already exists in the database
            existing_object = self.search(
                [("odk_submission_id", "=", value.get("__id"))]
            )

            if len(existing_object) >= 1:
                print(
                    "Submissions with Id: ",
                    value.get("__id"),
                    " already exists. Skipping.",
                )

            else:
                registration = self.create_registration_from_submission(value)
                self.odk_create_submissions_data(
                    value,
                    {
                        "odk_config_id": odk_config.id,
                        "odoo_corresponding_id": registration.id,
                    },
                )

    # Method to add registration record from ODK submission
    def create_registration_from_submission(self, data, extra_data=None):
        # extra_data = extra_data and extra_data or {}
        # map_dict = self.get_conversion_dict()
        # res = {}

        # for k, v in map_dict.items():
        #     if hasattr(self.env['openg2p.registration'], k) and data.get(v, False):
        #         res.update({k: data[v]})

        # res.update(extra_data)
        # registration = self.env['openg2p.registration'].create(res)
        registration = self.env["openg2p.registration"].create_registration_from_odk(
            data
        )
        return registration

    # Store submissions data in odk.submissions
    # Need to pass odoo_corresponding_id and odk_config_id in extra_data
    def odk_create_submissions_data(self, data, extra_data=None):
        extra_data = extra_data and extra_data or {}
        res = {}
        res.update(
            {
                "odk_submission_id": data.get("__id"),
                "submission_date": data.get("__system").get("submissionDate"),
                "submission_response": data,
            }
        )
        res.update(extra_data)
        self.create(res)

    # Wrapper function to update config
    def odk_update_configuration(self, data, odk_config_id):
        return self.env["odk.config"].search([("id", "=", odk_config_id)]).write(data)

    # Mappings between openg2p.registration and odk form fields
    def get_conversion_dict(self):
        return {
            "firstname": "firstname",
            "lastname": "lastname",
            "location_id": "location_id",
            "street": "street",
            "city": "city",
            "state_id": "state_id",
            "country_id": "country_id",
            "gender": "gender",
        }
