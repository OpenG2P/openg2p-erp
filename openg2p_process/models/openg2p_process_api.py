from odoo.http import Controller, route, request


class Openg2pProcessApi(Controller):
    @route("/processes", type="json", auth="user", methods=["GET"])
    def get_processes(self):
        process_list = request.env["openg2p.process"].search([])

        try:
            processes = []
            for wf in process_list:
                processes.append(wf.api_json())

            return {"status": 200, "message": "Success", "processes": processes}

        except BaseException as e:
            return {"status": 400, "error": str(e)}

    @route("/process/<int:id>", type="json", auth="user", methods=["GET"])
    def get_process_by_id(self, id):
        process_list = request.env["openg2p.process"].search([("id", "=", id)])

        try:
            processes = []
            for wf in process_list:
                processes.append(wf.api_json())

            return {"status": 200, "message": "Success", "processes": processes}

        except BaseException as e:
            return {"status": 400, "error": str(e)}
