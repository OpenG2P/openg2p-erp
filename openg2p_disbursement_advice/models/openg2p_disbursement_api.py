from odoo import fields
from odoo.http import Controller, route, request

class Openg2pDisbursementApi(Controller):

    @route("/all-batches",type="json",auth="user",methods=["GET"])
    def all_batches(self):
        try:
            batches_list=request.env["openg2p.disbursement.batch.transaction"].search([])

            res=[]

            for batch in batches_list:
                res.append({
                    "id":batch.id,
                    "name":batch.name
                    })
            
            return {
                "status":200,
                "message":"Success",
                "count":len(res),
                "batches":res
            }
        except BaseException as e:
            return{
                "status":200,
                "error":str(e)
            }
    
    @route("/batch-details/<int:id>",type="json",auth="user",method=["GET"])
    def get_batch_details(self,id):
        try:
            batch=request.env["openg2p.disbursement.batch.transaction"].search([("id","=",id)])

            if len(batch) > 0:
                batch=batch[0]

                return {
                    "status":200,
                    "message":"Success",
                    "id":batch.id,
                    "batch-details":batch.api_json()
                }
        except BaseException as e:
            return {
                "status":200,
                "error":str(e)
            }

    @route("/beneficiaries-batch/<int:id>",type="json",auth="user",method=["GET"])
    def beneficiaries_under_batch(self,id):
        #id refers to batch_id
        try:
            beneficiaries=request.env["openg2p.disbursement.main"].search([("batch_id","=",id)])
            
            res=[]

            for b in beneficiaries:
                res.append(b.api_json())

            return {
                "status":200,
                "message":"Success",
                "count":len(res),
                "program":beneficiaries[0].program_id.name,
                "batches":res
            }
        except BaseException as e:
            return {
                "status":200,
                "error":str(e)
            }

    @route("/createbatch",type="json",auth="user",method=["POST"])
    def create_batch(self,**kwargs):
        try:
            batch=request.env["openg2p.disbursement.batch.transaction"].create(kwargs)

            return{
                "status":200,
                "message":"Success",
                "id":batch.id or None
            }
        except BaseException as e:
            return {"status": 200, "error": str(e)}

    @route("/map-beneficiaries",type="json",auth="user",method=["POST"])
    def map_beneficiaries(self,**kwargs):
        try:
            ids=[]
            for beneficiary in kwargs["beneficiaries"]:
                beneficiary=request.env["openg2p.disbursement.main"].create(kwargs)
                ids.append(beneficiary.id)

            return{
                "status":200,
                "message":"Success",
                "id":ids or None,
            }
        except BaseException as e:
            return {"status": 200, "error": str(e)}
    
    @route("/create-transaction/<int:id>",type="json",auth="user",method=["POST"])
    def create_transaction(self,id):
        try:
            batch=request.env["openg2p.disbursement.batch.transaction"].search([("id","=",id)])
            batch.create_bulk_transfer()

            return{
                "status":200,
                "message":"Success",
                "status":batch.transaction_status or None
            }

        except BaseException as e:
            return {"status": 200, "error": str(e)}
    
    @route("/transaction-status/<int:id>",type="json",auth="user",method=["GET"])
    def create_transaction(self,id):
        try:
            batch=request.env["openg2p.disbursement.batch.transaction"].search([("id","=",id)])
            batch.bulk_transfer_status()

            return{
                "status":200,
                "message":"Success",
                "status":batch.transaction_status or None,
                "total":batch.total or None,
                "successful":batch.successful or None,
                "failed":batch.failed or None
            }

        except BaseException as e:
            return {"status": 200, "error": str(e)}