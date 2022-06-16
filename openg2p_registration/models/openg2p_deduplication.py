import requests, json

from odoo import api, fields, models

BASE_URL = "http://3.139.225.16:9080"


class Openg2pDeduplication(models.Model):
    _inherit = "openg2p.registration"

    def search_beneficiary(self):
        search_data = {
            "attributes": {
                "first_name": str(self.firstname),
                "last_name": str(self.lastname),
                "email": str(self.email),
                "phone": str(self.phone),
                "street": str(self.street),
                "street2": str(self.street2),
                "city": str(self.city),
                "postal_code": str(self.zip),
                "dob": str(self.birthday),
                "identity": str(self.identity_passport),
                "bank": str(self.bank_account_id.bank_id.name),
                "bank_account": str(self.bank_account_id.sanitized_acc_number),
                "emergency_contact_name": str(self.emergency_contact),
                "emergency_contact_phone": str(self.emergency_phone),
            }
        }
        beneficiary_new_data = self.del_none(search_data)

        search_url = BASE_URL + "/index/search"
        try:
            r = requests.post(search_url, json=beneficiary_new_data)
            return r.text
        except requests.exceptions.RequestException as e:
            return e

    def find_duplicates(self):
        beneficiary_list = self.search_beneficiary()

        if beneficiary_list:
            beneficiary_list = json.loads(beneficiary_list)
            beneficiary_ids = [li["beneficiary"] for li in beneficiary_list]

            self.update(
                {"duplicate_beneficiaries_ids": [(6, 0, list(beneficiary_ids))]}
            )

    def merge_beneficiaries(self):
        # ID to be retained
        idr = self.retained_id

        # Browsing that existing beneficiary
        existing_beneficiary = self.env["openg2p.beneficiary"].browse(idr)

        # Fields to be merged
        overwrite_data = {
            "location_id": self.location_id.id,
            "street": self.street,
            "street2": self.street2,
            "city": self.city,
            "state_id": self.state_id.id,
            "zip": self.zip,
            "country_id": self.country_id.id,
            "phone": self.phone,
            "mobile": self.mobile,
            "email": self.email,
            "lang": self.lang,
            # "image": self.image,
            "marital": self.marital,
            "bank_account_id": self.bank_account_id.id,
            "emergency_contact": self.emergency_contact,
            "emergency_phone": self.emergency_phone,
        }

        # Removing None fields
        cleaned_overwrite_data = self.del_none(overwrite_data)

        # Deriving existing fields to create new beneficiary
        existing_data = {
            "firstname": existing_beneficiary.firstname,
            "lastname": existing_beneficiary.lastname,
            "othernames": existing_beneficiary.othernames,
            "location_id": existing_beneficiary.location_id.id,
            "street": existing_beneficiary.street,
            "street2": existing_beneficiary.street2,
            "city": existing_beneficiary.city,
            "state_id": existing_beneficiary.state_id.id,
            "zip": existing_beneficiary.zip,
            "country_id": existing_beneficiary.country_id.id,
            "phone": existing_beneficiary.phone,
            "mobile": existing_beneficiary.mobile,
            "email": existing_beneficiary.email,
            "title": existing_beneficiary.title.id,
            "lang": existing_beneficiary.lang,
            "gender": existing_beneficiary.gender,
            "birthday": existing_beneficiary.birthday,
            # "image": existing_beneficiary.image,
            "marital": existing_beneficiary.marital,
            "bank_account_id": existing_beneficiary.bank_account_id.id,
            "emergency_contact": existing_beneficiary.emergency_contact,
            "emergency_phone": existing_beneficiary.emergency_phone,
        }

        cleaned_existing_data = self.del_none(existing_data)

        # Merging specfic fields to beneficiary
        existing_beneficiary.write(cleaned_overwrite_data)

        # Creating new beneficiary whose active=False
        new_beneficiary = self.env["openg2p.beneficiary"].create(cleaned_existing_data)

        # Storing merged id's in fields
        existing_beneficiary.write(
            {"merged_beneficiary_ids": [(4, new_beneficiary.id)]}
        )

        # Setting active false
        new_beneficiary.active = False

        self.clear_beneficiaries()

        # Archiving the current Registration
        self.archive_registration()
        self.retained_id = 0

    def clear_beneficiaries(self):
        self.write({"duplicate_beneficiaries_ids": [(5, 0, 0)]})

    def index_beneficiary(self):
        data = {
            "id": str(self.beneficiary_id.id),
            "first_name": str(self.firstname),
            "last_name": str(self.lastname),
            "email": str(self.email),
            "phone": str(self.phone),
            "street": str(self.street),
            "street2": str(self.street2),
            "city": str(self.city),
            "postal_code": str(self.zip),
            "dob": str(self.birthday),
            "identity": str(self.identity_passport),
            "bank": str(self.bank_account_id.bank_id.name),
            "bank_account": str(self.bank_account_id.sanitized_acc_number),
            "emergency_contact_name": str(self.emergency_contact),
            "emergency_contact_phone": str(self.emergency_phone),
        }
        # Deleting null fields
        index_data = self.del_none(data)

        url_endpoint = BASE_URL + "/index"
        try:
            r = requests.post(url_endpoint, json=index_data)
            return r
        except BaseException as e:
            return e

    def del_none(self, d):
        for key, value in list(d.items()):
            if value == "False":
                del d[key]
            elif isinstance(value, dict):
                self.del_none(value)
        return d
