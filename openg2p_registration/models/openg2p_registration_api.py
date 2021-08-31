from odoo.http import Controller, route, request


class Openg2pBeneficiaryApi(Controller):
    @route("/registrations", type="json", auth="user")
    def get_all_registrations(self):
        regd_objs = request.env["openg2p.registration"].search([])
        regds = []
        for r in regd_objs:
            regds.append(r.api_json())
        regds.sort(key=lambda x: x["id"])
        return {
            "count": len(regds),
            "status": 200,
            "response": regds,
            "message": "Success",
        }

    @route("/create-registration", type="json", auth="user")
    def create_registration(self, **kwargs):
        response = {
            "Success": False,
            "message": "Error: Not JSON formatted!",
        }
        if request.jsonrequest:
            print("rec", kwargs)
            new_regd = (
                request.env["openg2p.registration"]
                .sudo()
                .create_registration_from_odk(kwargs)
            )
            response["Success"] = True
            response["message"] = "Success"
            response["ID"] = new_regd.id
        return response

    @route("/get-registration", type="json", auth="user")
    def get_registration(self, **kwargs):
        if "id" not in kwargs:
            return {"status": 200, "message": "Error! Required parameter id missing!"}
        id = kwargs["id"]
        regd_objs = request.env["openg2p.registration"].search([("id", "=", id)])
        if len(regd_objs) > 0:
            return {
                "status": 200,
                "response": regd_objs[0].api_json(),
                "message": "Failure! Invalid registration id!",
            }
        else:
            return {"status": 200, "message": "Failure! Invalid registration id!"}
