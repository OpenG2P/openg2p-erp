# -*- coding: utf-8 -*-
from odoo.addons.queue_job.job import job
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class BatchNotificationWiz(models.TransientModel):
    _name = "batch.notification.wiz"
    _description = "Batch Notification Wizard"

    send_sms = fields.Boolean("Via SMS", default=True)
    send_email = fields.Boolean("Via Email", default=True)
    sms_template = fields.Many2one(
        "sms.template",
        string="SMS Template",
        domain=[("model", "=", "openg2p.disbursement.slip")],
        default=lambda self: self.env.user.company_id.disbursement_batch_sms_template_id,
    )
    email_template = fields.Many2one(
        "mail.template",
        string="Email Template",
        domain=[("model", "=", "openg2p.disbursement.slip")],
        default=lambda self: self.env.user.company_id.disbursement_batch_email_template_id,
    )

    @api.constrains("send_sms", "send_email")
    def _constraint_selection(self):
        self.ensure_one()
        if not self.send_email and not self.send_sms:
            raise ValidationError(_("At least one method needs to be selected"))

        if self.send_sms:
            # TODO let us ensure sms gateway is setup
            pass

        if self.send_email:
            # TODO let us ensure email gateway is setup
            pass

    @api.multi
    def execute(self):
        self.ensure_one()
        active_id = self.env.context.get("active_id")
        batch = self.env["openg2p.disbursement.batch"].browse(active_id)
        if batch.state != "done":
            raise ValidationError
        self.sudo().with_delay(priority=10)._execute_delay(batch)
        return {"type": "ir.actions.act_window_close"}

    @job
    def _execute_delay(self, batch):
        # TODO send sms and email here filtering by beneficiaries that have them also visual vfeedback?
        email_count = 0
        sms_count = 0
        if self.send_email:
            for slip in batch.slip_ids.filtered("beneficiary_id.email"):
                self.email_template.send_mail(slip.id, force_send=True)
                email_count += 1

        if self.send_sms:
            for slip in batch.slip_ids.filtered("beneficiary_id.phone"):
                self.sms_template.send_sms(self.sms_template.id, slip.id)
                sms_count += 1
