from odoo import fields
from odoo.http import Controller, route, request


class Openg2pBeneficiaryApi(Controller):
    # categories
    @route("/program-categories", type="json", auth="user", methods=["GET"])
    def categories(self):
        try:
            category_list = request.env["openg2p.program.enrollment_category"].search(
                []
            )
            res = []
            for category in category_list:
                res.append(category.api_json())
            return {
                "status": 200,
                "message": "Success",
                "count": len(res),
                "categories": res,
            }
        except BaseException as e:
            return {"status": 400, "error": str(e)}

    @route("/program-category/<int:id>", type="json", auth="user", methods=["GET"])
    def get_category_by_id(self, id):
        try:
            category = request.env["openg2p.program.enrollment_category"].search(
                [("id", "=", id)]
            )
            if len(category) > 0:
                category = category[0]
                return {
                    "status": 200,
                    "message": "Success",
                    "id": id,
                    "category": category.api_json(),
                }
            else:
                return {
                    "status": 404,
                    "id": id,
                    "error": f"Error! No program with id {id} exists!",
                }
        except BaseException as e:
            return {"status": 400, "id": id, "error": str(e)}

    @route("/program-category", type="json", auth="user", methods=["POST"])
    def create_category(self, **kwargs):
        try:
            category = request.env["openg2p.program.enrollment_category"].create(kwargs)
            return {
                "status": 200,
                "message": "Success",
                "id": category.id,
            }
        except BaseException as e:
            return {"status": 400, "error": str(e)}

    # programs
    @route("/programs", type="json", auth="user", methods=["GET"])
    def programs(self):
        try:
            programs = request.env["openg2p.program"].search([])
            res = []
            for program in programs:
                res.append(program.api_json())
            return {
                "status": 200,
                "message": "Success",
                "count": len(res),
                "programs": res,
            }
        except BaseException as e:
            return {"status": 400, "error": str(e)}

    @route("/program/<int:id>", type="json", auth="user", methods=["GET"])
    def get_program_by_id(self, id):
        try:
            program = request.env["openg2p.program"].search([("id", "=", id)])
            if len(program) > 0:
                program = program[0]
                return {
                    "status": 200,
                    "message": "Success",
                    "id": id,
                    "program": program.api_json(),
                }
            else:
                return {
                    "status": 404,
                    "id": id,
                    "error": f"Error! No program with id {id} exists!",
                }
        except BaseException as e:
            return {"status": 400, "id": id, "error": str(e)}

    @route("/program", type="json", auth="user", methods=["POST"])
    def create_program(self, **kwargs):
        # date format: "yyyy-mm-dd"
        try:
            program = request.env["openg2p.program"].create(kwargs)
            return {
                "status": 200,
                "message": "Success",
                "id": program.id,
            }
        except BaseException as e:
            return {"status": 400, "error": str(e)}

    # beneficiaries
    @route("/beneficiaries", type="json", auth="user", methods=["GET"])
    def beneficiaries(self):
        try:
            beneficiary_list = request.env["openg2p.beneficiary"].search([])
            res = []
            for b in beneficiary_list:
                res.append(b.api_json())
            return {
                "status": 200,
                "message": "Success",
                "count": len(res),
                "beneficiaries": res,
            }
        except BaseException as e:
            return {"status": 400, "error": str(e)}

    @route("/beneficiary/<int:id>", type="json", auth="user", methods=["GET"])
    def get_beneficiary(self, id):
        try:
            beneficiary = request.env["openg2p.beneficiary"].search([("id", "=", id)])
            if len(beneficiary) > 0:
                return {
                    "status": 200,
                    "id": id,
                    "message": "Success",
                    "beneficiary": beneficiary[0].api_json(),
                }
            else:
                return {
                    "status": 404,
                    "id": id,
                    "error": f"Error! No beneficiary with id {id} exists!",
                }
        except BaseException as e:
            return {"status": 400, "id": id, "error": str(e)}

    @route("/beneficiary/<int:id>/kyc", type="json", auth="user", methods=["PUT"])
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
            regd = request.env["openg2p.beneficiary"].search([("id", "=", id)])
            data_kyc = {
                "passport_id": str(kwargs["passport_id"]),
                "national_id": str(kwargs["national_id"]),
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

    @route("/beneficiary/<int:id>/bank", type="json", auth="user", methods=["PUT"])
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
            beneficiary = request.env["openg2p.beneficiary"].search([("id", "=", id)])
            data_inp = {k: str(kwargs[k]) for k in keys}
            data = {
                "status": 200,
                "id": id,
                **data_inp,
            }
            if len(beneficiary) > 0:
                res = request.env["res.partner.bank"].search(
                    [("acc_number", "=", data["acc_number"])]
                )
                if res:
                    raise Exception("Duplicate Bank Account Number!")
                else:
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
                beneficiary.write({"bank_account_id": res.id})
                data["message"] = "Success"
            else:
                data["status"] = 404
                data["error"] = f"Error! No registration found with id {id}!"
            return data
        except BaseException as e:
            return {"status": 400, "id": id, "error": str(e)}

    @route("/enroll-into-program", type="json", auth="user", methods=["POST"])
    def enroll_into_programs(self, **kwargs):
        try:
            keys = ["beneficiary_ids", "program_id", "category_id", "date_start"]
            for key in keys:
                if key not in kwargs:
                    return {
                        "status": 200,
                        "message": f"Error! Required parameter '{key}' missing!",
                    }
            ids = kwargs["beneficiary_ids"]
            program_id = kwargs["program_id"]
            category_id = kwargs["category_id"]
            date_start = kwargs["date_start"]
            beneficiaries = request.env["openg2p.beneficiary"].browse(ids)
            beneficiaries.program_enroll(
                program_id=program_id,
                category_id=category_id,
                date_start=date_start or fields.Date.today(),
                confirm=True,
            )
            return {
                "count": len(beneficiaries),
                "status": 200,
                "beneficiary_ids": ids,
                "message": "Success",
            }
        except BaseException as e:
            return {"status": 400, "error": str(e)}
