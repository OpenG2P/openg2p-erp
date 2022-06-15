from odoo import models
from odoo.exceptions import UserError, ValidationError, _logger

AVAILABLE_PRIORITIES = [("0", "Urgent"), ("1", "High"), ("2", "Normal"), ("3", "Low")]


class RegistrationService(models.Model):
    _inherit = ["openg2p.registration"]

    def create_registration_for_single_submission(self, odk_data):
        temp = {}
        self.renaming_submission_data_fields(temp, odk_data)
        self.create_fields_for_registration(temp)

    def create_fields_for_registration(self, temp):
        country_name = temp["country"] if "country" in temp.keys() else "Sierra Leone"
        state_name = temp["state"] if "state" in temp.keys() else "Freetown"
        country_id = self.env["res.country"].search([("name", "=", country_name)])[0].id
        state_id = (
            self.env["res.country.state"].search([("name", "=", state_name)])[0].id
        )
        # Creating registration in final stage
        # stage_id_default = 6
        # temp["stage_id"] = stage_id_default
        try:
            regd = self.create(
                {
                    "firstname": "_",
                    "lastname": "_",
                    "street": (temp["chiefdom"] if "chiefdom" in temp.keys() else "-"),
                    "street2": (temp["district"] if "district" in temp.keys() else "-")
                    + ", "
                    + (temp["region"] if "region" in temp.keys() else "-"),
                    "city": (
                        (temp["city"] if "city" in temp.keys() else "Freetown")
                        or "Freetown"
                    )
                    if "city" in temp.keys()
                    else "Freetown",
                    "country_id": country_id,
                    "state_id": state_id,
                    "gender": "male",
                    # "stage_id": (
                    #     temp["stage_id"]
                    #     if "stage_id" in temp.keys()
                    #     else stage_id_default
                    # ),
                }
            )
            rid = regd.id
            self.create_disbursement_fields(rid, temp, regd)
        except BaseException as e:
            _logger.error(e)
            return None

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

    def create_disbursement_fields(self, rid, temp, regd):
        from datetime import datetime

        data = {}
        odk_data = temp
        org_data = {}
        format = "%Y-%m-%dT%H:%M:%SZ"
        for k, v in odk_data.items():
            try:
                if k in [
                    "regression_and_progression",
                    "total_quality",
                    "total_equity",
                    "grand_total",
                ]:
                    org_data[k] = v
                    continue
                if (
                    k
                    in [
                        "Status",
                        "AttachmentsExpected",
                        "AttachmentsPresent",
                        "SubmitterName",
                        "SubmitterID",
                        "KEY",
                        "meta-instanceID",
                        "__version__",
                        "bank_name",
                        "city",
                        "district",
                        "chiefdom",
                        "region",
                    ]
                    or k.startswith("_")
                ):
                    continue
                if k == "bank_account_number":
                    if len(str(v) or "") != 0:
                        data["bank_account_number"] = str(v)
                        res = self.env["res.partner.bank"].search(
                            [("acc_number", "=", str(v))]
                        )
                        if res:
                            raise Exception("Duplicate Bank Account Number!")
                        if not res:
                            bank_id = self.env["res.bank"].search(
                                [("name", "=", odk_data["bank_name"])], limit=1
                            )
                            if len(bank_id) == 0:
                                bank_id = self.env["res.bank"].create(
                                    {
                                        "execute_method": "manual",
                                        "name": odk_data["bank_name"],
                                        "type": "normal",
                                    }
                                )
                            else:
                                bank_id = bank_id[0]
                            res = self.env["res.partner.bank"].create(
                                {
                                    "bank_id": bank_id.id,
                                    "acc_number": str(v),
                                    "payment_mode": "AFM",
                                    "bank_name": odk_data["bank_name"],
                                    "acc_holder_name": odk_data["name"],
                                    "partner_id": self.env.ref("base.main_partner").id,
                                }
                            )
                        data["bank_account_id"] = res.id
                elif k == "phone":
                    data["phone"] = odk_data["phone"]
                elif hasattr(self, k):
                    if k == "partner_id":
                        res = self.env["res.partner"].search(
                            [("partner_id", "=", v)], limit=1
                        )
                        if res:
                            data[k] = res.id
                    elif k == "registered_date":
                        data["registered_date"] = datetime.strptime(v, format)
                    elif k == "categ_ids":
                        res = self.env["categ_ids"].search(
                            [("categ_ids", "=", v)], limit=1
                        )
                        if res:
                            data["categ_ids"] = res.ids
                    elif k == "company_id":
                        res = self.env["company_id"].search(
                            [("company_id", "=", v)], limit=1
                        )
                        if res:
                            data["company_id"] = res.id
                    elif k == "user_id":
                        res = self.env["user_id"].search([("user_id", "=", v)], limit=1)
                        if res:
                            data["user_id"] = res.id
                    elif k == "priority":
                        if v in [i[0] for i in AVAILABLE_PRIORITIES]:
                            data["priority"] = v
                    elif k == "beneficiary_id":
                        res = self.env["openg2p.beneficiary"].search(
                            [("beneficiary_id", "=", rid)], limit=1
                        )
                        if res:
                            data["beneficiary_id"] = res.id
                    elif k == "identities":
                        for vi in v:
                            self.env["openg2p.registration.identity"].create(
                                {
                                    "name": list(vi.keys())[0],
                                    "type": list(vi.values())[0],
                                    "registration_id": rid,
                                }
                            )
                        res = self.env["openg2p.registration.identity"].search(
                            [("registration_id", "=", rid)]
                        )
                        if res:
                            data["identities"] = res.ids
                    elif k == "state_id":
                        state = self.env["res.country.state"].search([("name", "=", v)])
                        if state:
                            data["state_id"] = state.id
                    else:
                        if k == "name":
                            if v is None:
                                continue
                            name_parts = v.split(" ")
                            data["firstname"] = name_parts[0]
                            if len(name_parts) > 1:
                                data["lastname"] = " ".join(name_parts[1:])
                        else:
                            data.update({k: v})
                else:
                    org_data.update({k: v})
            except Exception as e:
                _logger.error(e)

        for k, v in org_data.items():
            try:
                self.env["openg2p.registration.orgmap"].create(
                    {
                        "field_name": k,
                        "field_value": str(v) if v else "",
                        "regd_id": rid,
                    }
                )
            except BaseException as e:
                _logger.error(e)

        try:
            regd.write(data)
            # Updating Program for Registration
            regd.program_ids = [(6, 0, temp["program_ids"])]

        except BaseException as e:
            print(e)

        return regd
