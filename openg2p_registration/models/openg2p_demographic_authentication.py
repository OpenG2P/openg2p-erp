import requests
import json
import logging
from odoo import models

_logger = logging.getLogger(__name__)

UN_SUCCESS_WITH_ERRORS = "Unsuccessful with Errors"
SUCCESS_WITH_ERRORS = "Successful with Errors"
SUCCESS = "Successful"


class Openg2pDemographicAuthentication(models.Model):
    _inherit = "openg2p.registration"

    def demo_auth(self, data):
        import os
        DEMO_AUTHENTICATE_URL = os.getenv("DEMO_AUTHENTICATE_URL", "http://openg2p-mosip-auth-mediator.openg2p-mosip/demoAuth")
        response = requests.post(DEMO_AUTHENTICATE_URL, json=data)
        _logger.info("Demo Auth Response: " + str(response.content))
        return json.loads(response.content)

    def demo_auth_merge(self, data):
        auth_res = self.demo_auth(data)
        should_merge = False
        should_create_beneficiary = False
        stage_id = 0
        if auth_res["authIdStatus"] == SUCCESS:
            stage_id = 6
            should_merge = self.post_auth_find_duplicate_beneficiary(
                auth_res["authId"], auth_res["authIdType"])
            if not should_merge:
                should_create_beneficiary = True
        elif auth_res["authIdStatus"] == SUCCESS_WITH_ERRORS:
            stage_id = 2
        elif auth_res["authIdStatus"] == UN_SUCCESS_WITH_ERRORS:
            stage_id = 2
        return {
            "stage_id": stage_id,
            "should_merge": should_merge,
            "should_create_beneficiary": should_create_beneficiary,
            "auth_id": auth_res["authId"],
            "auth_id_type": auth_res["authIdType"],
            "auth_id_status": auth_res["authIdStatus"],
            "auth_id_message": auth_res["authIdMessage"]
        }

    def post_auth_create_id(self, response):
        return self.env["openg2p.registration.identity"].create({
            "name": response["auth_id"],
            "type": response["auth_id_type"],
            "status": response["auth_id_status"],
            "message": response["auth_id_message"],
            "registration_id": self.id
        })
        res = self.env["openg2p.registration.identity"].search(
            [("registration_id", "=", self.id)]
        )
        if res:
            self.write({"identities": res.ids})

    def post_auth_find_duplicate_beneficiary(self, auth_id, auth_id_type):
        type_code_id = self.env["openg2p.beneficiary.id_category"].search(
            [("code", "=", auth_id_type)], limit=1).id
        length = len(self.env["openg2p.beneficiary.id_number"].search(
            [("name", "=", auth_id), ("category_id", "=", type_code_id)]))
        _logger.info(f"auth_id : {auth_id}. Post Auth. Size of duplicates: {length}")
        return length > 0

    def post_auth_merge(self, response):
        auth_id = response["auth_id"]
        auth_id_type = response["auth_id_type"]

        type_code_id = self.env["openg2p.beneficiary.id_category"].search(
            [("code", "=", auth_id_type)], limit=1).id
        auth_id_object = self.env["openg2p.beneficiary.id_number"].search(
            [("name", "=", auth_id), ("category_id", "=", type_code_id)])
        existing_beneficiary = auth_id_object.beneficiary_id
        _logger.info(f"auth_id: {auth_id}. Entered Post Auth Merge.")
        # Fields to be merged
        overwrite_data = {
            "firstname": self.firstname,
            "lastname": self.lastname,
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
            "image": self.image,
            "marital": self.marital,
            "bank_account_id": self.bank_account_id.id,
            "emergency_contact": self.emergency_contact,
            "emergency_phone": self.emergency_phone
        }
        program_ids=self.program_ids.ids
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
            "image": existing_beneficiary.image,
            "marital": existing_beneficiary.marital,
            "bank_account_id": existing_beneficiary.bank_account_id.id,
            "emergency_contact": existing_beneficiary.emergency_contact,
            "emergency_phone": existing_beneficiary.emergency_phone,
            "program_ids": [(4,program)for program in existing_beneficiary.program_ids.ids ]
        }

        cleaned_existing_data = self.del_none(existing_data)

        # Merging specfic fields to beneficiary
        existing_beneficiary.write(cleaned_overwrite_data)

        # Creating new beneficiary whose active=False
        new_beneficiary = self.env["openg2p.beneficiary"].create(cleaned_existing_data)
        # Create new registration with existing data
        self.write({"beneficiary_id": existing_beneficiary.id })

        # Storing merged id's in fields
        existing_beneficiary.write(
            {"merged_beneficiary_ids": [(4, new_beneficiary.id)]}
        )
        existing_beneficiary.write(
            {
                "program_ids":[(4,program)for program in program_ids ]
            }
        )

        # Setting active false
        new_beneficiary.active = False

        # self.clear_beneficiaries()

        # Archiving the current Registration
        # self.archive_registration()
