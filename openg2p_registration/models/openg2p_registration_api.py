import json
import asyncio
from odoo.http import Controller, route, request


class Openg2pRegistrationApi(Controller):
    @route("/registrations", type="json", auth="user", methods=["GET"])
    def get_all_registrations(self, **kwargs):
        try:
            print(kwargs)
            print(kwargs.get("page"))
            regd_objs = request.env["openg2p.registration"].search([])
            regds = []
            for r in regd_objs:
                regds.append(r.api_json())
            regds.sort(key=lambda x: x["id"])
            return {
                "count": len(regds),
                "status": 200,
                "registrations": regds,
                "message": "Success",
            }
        except BaseException as e:
            return {"status": 400, "error": str(e)}

    @route("/registration/<int:id>", type="json", auth="user", methods=["GET"])
    def get_registration_by_id(self, id):
        try:
            regd_objs = request.env["openg2p.registration"].search([("id", "=", id)])
            if len(regd_objs) > 0:
                return {
                    "status": 200,
                    "id": id,
                    "response": regd_objs[0].api_json(),
                    "message": "Success",
                }
            else:
                return {
                    "status": 404,
                    "id": id,
                    "message": "Failure! Invalid registration id!",
                }
        except BaseException as e:
            return {"status": 400, "id": id, "error": str(e)}

    @route("/registration", type="json", auth="user", methods=["POST"])
    def create_registration(self, **kwargs):
        if len(kwargs) == 0:
            return {
                "status": 200,
                "message": "Error! Properties of registration missing!",
            }
        response = {
            "status": 200,
            "message": "Success",
        }
        try:
            new_regd = request.env["openg2p.registration"].create_registration_from_odk(
                kwargs
            )
            response["id"] = new_regd.id
            return response
        except BaseException as e:
            return {"status": 400, "error": str(e)}

    @route("/duplicates/<int:id>", type="json", auth="user", methods=["GET"])
    def find_duplicates(self, id):
        try:
            data = {
                "status": 200,
                "id": id,
            }
            regd = request.env["openg2p.registration"].search([("id", "=", id)])
            if len(regd) > 0:
                regd = regd[0]
                beneficiary_list = regd.search_beneficiary()
                beneficiary_list = json.loads(beneficiary_list)
                beneficiary_ids = [li["beneficiary"] for li in beneficiary_list]
                data["duplicate_beneficiary_ids"] = beneficiary_ids
                data["message"] = "Success"
            else:
                data["status"] = 404
                data["error"] = f"Error! No registration found with id {id}!"
            return data
        except BaseException as e:
            return {"status": 400, "id": id, "error": str(e)}

    @route("/beneficiaries", type="json", auth="user", methods=["POST"])
    def convert_to_beneficiaries(self, **kwargs):
        async def convert(regd):
            return regd.create_beneficiary_from_registration()["res_id"]

        if "check_stage" not in kwargs:
            return {
                "status": 200,
                "message": "Error! Required parameter 'check_stage' missing!",
            }
        elif not isinstance(kwargs["check_stage"], bool):
            return {
                "status": 200,
                "message": f"Error! Value of 'check_stage':{kwargs['check_stage']} not bool!",
            }
        try:
            data = {
                "status": 200,
                "check_stage": kwargs["check_stage"],
                "ids": kwargs["ids"],
                "message": "Success",
            }
            ids = kwargs["ids"]
            regds = request.env["openg2p.registration"].browse(ids)
            res_ids = {}
            for regd in regds:
                if not regd.beneficiary_id:
                    if kwargs["check_stage"] and regd.stage_id != 6:
                        continue
                    b_id = asyncio.run(convert(regd))
                    res_ids[int(regd.id)] = b_id
            data["beneficiary_ids"] = res_ids
            return data
        except BaseException as e:
            return {"status": 400, "error": str(e)}

    @route("/registration/<int:id>/kyc", type="json", auth="user", methods=["PUT"])
    def update_kyc(self, id, **kwargs):
        keys = ["passport_id", "national_id", "ssn"]
        for key in keys:
            if key not in kwargs:
                return {
                    "status": 200,
                    "id": id,
                    "message": f"Error! Required parameter '{key}' missing!",
                }
        try:
            regd = request.env["openg2p.registration"].search([("id", "=", id)])
            data_kyc = {
                "identity_passport": str(kwargs["passport_id"]),
                "identity_national": str(kwargs["national_id"]),
                "ssn": str(kwargs["ssn"]),
            }
            data = {
                "status": 200,
                "id": id,
                **data_kyc,
            }
            if len(regd) > 0:
                regd.write(data_kyc)
                data["message"] = "Success"
            else:
                data["status"] = 404
                data["error"] = f"Error! No registration found with id {id}!"
            return data
        except BaseException as e:
            return {"status": 400, "id": id, "error": str(e)}

    @route("/registration/<int:id>/bank", type="json", auth="user", methods=["PUT"])
    def update_bank(self, id, **kwargs):
        keys = ["acc_number", "bank_name", "acc_holder_name"]
        for key in keys:
            if key not in kwargs:
                return {
                    "status": 200,
                    "id": id,
                    "message": f"Error! Required parameter '{key}' missing!",
                }
        try:
            regd = request.env["openg2p.registration"].search([("id", "=", id)])
            data_inp = {k: str(kwargs[k]) for k in keys}
            data = {
                "status": 200,
                "id": id,
                **data_inp,
            }
            if len(regd) > 0:
                res = request.env["res.partner.bank"].search(
                    [("acc_number", "=", data["acc_number"])]
                )
                if res:
                    raise Exception("Duplicate Bank Account Number!")
                if not res:
                    bank_id = request.env["res.bank"].search(
                        [("name", "=", data["bank_name"])], limit=1
                    )
                    if len(bank_id) == 0:
                        bank_id = request.env["res.bank"].create(
                            {
                                "execute_method": "manual",
                                "name": data["bank_name"],
                                "type": "normal",
                            }
                        )
                    else:
                        bank_id = bank_id[0]
                    res = request.env["res.partner.bank"].create(
                        {
                            "bank_id": bank_id.id,
                            "acc_number": data["acc_number"],
                            "payment_mode": "AFM",
                            "bank_name": data["bank_name"],
                            "acc_holder_name": data["acc_holder_name"],
                            "partner_id": request.env.ref("base.main_partner").id,
                        }
                    )
                regd.write({"bank_account_id": res.id})
                data["message"] = "Success"
            else:
                data["status"] = 404
                data["error"] = f"Error! No registration found with id {id}!"
            return data
        except BaseException as e:
            return {"status": 400, "id": id, "error": str(e)}
