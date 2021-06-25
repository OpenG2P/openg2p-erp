# -*- coding: utf-8 -*-
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    disbursement_batch_sms_template_id = fields.Many2one(
        "sms.template",
        string="SMS Template",
        help="Template used to send disbursement notification SMS messages",
        domain=[("model", "=", "openg2p.disbursement.slip")],
        default=lambda r: r.env.ref("openg2p_disbursement.slip_sms_template", False),
    )
    disbursement_batch_email_template_id = fields.Many2one(
        "mail.template",
        string="Email Template",
        help="Template used to send disbursement notification email messages",
        domain=[("model", "=", "openg2p.disbursement.slip")],
        default=lambda r: r.env.ref("openg2p_disbursement.slip_email_template", False),
    )
