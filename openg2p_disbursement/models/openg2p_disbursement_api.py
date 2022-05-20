from odoo.http import Controller, route, request


class Openg2pDisbursementApi(Controller):
    @route("/batches", type="json", auth="user", methods=["GET"])
    def all_batches(self):
        try:
            batches_list = request.env["openg2p.disbursement.batch.transaction"].search(
                []
            )
            res = []
            for batch in batches_list:
                res.append(batch.api_json())
            return {
                "status": 200,
                "message": "Success",
                "count": len(res),
                "batches": res,
            }
        except BaseException as e:
            return {"status": 400, "error": str(e)}

    @route("/batch/<int:id>", type="json", auth="user", method=["GET"])
    def get_batch_by_id(self, id):
        try:
            batch = request.env["openg2p.disbursement.batch.transaction"].search(
                [("id", "=", id)]
            )
            if len(batch) > 0:
                batch = batch[0]
                return {
                    "status": 200,
                    "message": "Success",
                    "id": id,
                    "batch": batch.api_json(),
                }
            else:
                return {
                    "status": 404,
                    "id": id,
                    "message": f"Error! Batch with id {id} not found!",
                }
        except BaseException as e:
            return {"status": 400, "error": str(e)}

    @route("/batches", type="json", auth="user", method=["POST"])
    def create_batch(self, **kwargs):
        try:
            batch = request.env["openg2p.disbursement.batch.transaction"].create(kwargs)
            return {"status": 200, "message": "Success", "id": batch.id or None}
        except BaseException as e:
            return {"status": 400, "error": str(e)}

    @route("/map-beneficiaries", type="json", auth="user", method=["POST"])
    def map_beneficiaries(self, **kwargs):
        try:
            ids = []
            for beneficiary in kwargs["beneficiaries"]:
                beneficiary = request.env["openg2p.disbursement.main"].create(kwargs)
                ids.append(beneficiary.id)

            return {
                "status": 200,
                "message": "Success",
                "id": ids or None,
            }
        except BaseException as e:
            return {"status": 400, "error": str(e)}

    @route("/transaction/<int:id>", type="json", auth="user", method=["POST"])
    def create_transaction(self, id):
        try:
            batch = request.env["openg2p.disbursement.batch.transaction"].search(
                [("id", "=", id)]
            )
            batch.create_bulk_transfer()

            return {
                "status": 200,
                "message": "Success",
                "transaction_status": batch.transaction_status or None,
            }

        except BaseException as e:
            return {"status": 400, "error": str(e)}

    @route("/transaction/<int:id>", type="json", auth="user", method=["GET"])
    def get_transaction(self, id):
        try:
            batch = request.env["openg2p.disbursement.batch.transaction"].search(
                [("id", "=", id)]
            )
            batch.bulk_transfer_status()

            return {
                "status": 200,
                "message": "Success",
                "transaction_status": batch.transaction_status or None,
                "total": batch.total or None,
                "successful": batch.successful or None,
                "failed": batch.failed or None,
            }

        except BaseException as e:
            return {"status": 400, "error": str(e)}
