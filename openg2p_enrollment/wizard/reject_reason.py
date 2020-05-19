# -*- coding: utf-8 -*-

from odoo import fields, models, api


class WizRejectReason(models.TransientModel):

    _name = "wiz.openg2p.applicant.reject.reason"
    _description = "Add Reject Reason For Application "

    reject_reason_id = fields.Many2one('openg2p.applicant.reject.reason', "Reject Reason", required=1)


    @api.multi
    def action_reject(self):
        active_rec = self.env['openg2p.applicant'].browse(self.env.context.get('active_id'))
        active_rec.write({'active': False, "reject_reason_id": self.reject_reason_id.id})
