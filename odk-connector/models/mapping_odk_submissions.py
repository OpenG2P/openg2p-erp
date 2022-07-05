from odoo import models
from odoo.exceptions import UserError, ValidationError, _logger

AVAILABLE_PRIORITIES = [("0", "Urgent"), ("1", "High"), ("2", "Normal"), ("3", "Low")]


class MappingService(models.Model):
    _inherit = "odk.submissions"

    def mapping_and_creating_registration(self, odk_data):
        temp = {}
        self.renaming_submission_data_fields(temp, odk_data)
        regd = self.mapping_core_fields(temp)
        single_regd = self.env[
            "openg2p.registration"
        ].create_registration_for_single_submission(regd, temp)
        return single_regd

    def renaming_submission_data_fields(self, temp, odk_data):
        odk_map = (
            odk_data["odk_map"]
            if "odk_map" in odk_data.keys()
            else self._get_default_odk_map()
        )

        for k, v in odk_data.items():
            if k.startswith("group"):
                for k2, v2 in v.items():
                    if k2 in odk_map.keys():
                        k2 = odk_map[k2]
                    else:
                        k2 = str(k2).replace("-", "_").lower()
                    if not str(k2).startswith("_"):
                        temp[k2] = v2
            else:
                if not str(k).startswith("_"):
                    temp[str(k).replace("-", "_").lower()] = v

    def _get_default_odk_map(self):
        odk_map_data = {
            "Enter_Today_s_date": "date",
            "Town_Village": "city",
            "Account_Number": "bank_account_number",
            "School_Name": "name",
            "Mobile_Number_of_Respondant": "phone",
        }

        return odk_map_data

    def mapping_core_fields(self, temp):
        country_name = temp["country"] if "country" in temp.keys() else "Sierra Leone"
        state_name = temp["state"] if "state" in temp.keys() else "Freetown"
        country_id = self.env["res.country"].search([("name", "=", country_name)])[0].id
        state_id = (
            self.env["res.country.state"].search([("name", "=", state_name)])[0].id
        )

        regd = {
            "firstname": "_",
            "lastname": "_",
            "street": (temp["chiefdom"] if "chiefdom" in temp.keys() else "-"),
            "street2": (temp["district"] if "district" in temp.keys() else "-")
            + ", "
            + (temp["region"] if "region" in temp.keys() else "-"),
            "city": (
                (temp["city"] if "city" in temp.keys() else "Freetown") or "Freetown"
            )
            if "city" in temp.keys()
            else "Freetown",
            "country_id": country_id,
            "state_id": state_id,
            "gender": "male",
            "external_id": (
                temp["new_emis_code"] if "new_emis_code" in temp.keys() else None
            ),
            "phone": temp["phone"],
            # TODO correct submission field to be mapped for kyc_id
            "kyc_id": temp["bban"],
        }
        return regd
