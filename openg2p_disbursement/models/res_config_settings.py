# -*- coding: utf-8 -*-
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    disbursement_batch_sms_template_id = fields.Many2one(
        "sms.template",
        string="SMS Template",
        related="company_id.disbursement_batch_sms_template_id",
        help="Template used to send disbursement notification SMS messages",
        readonly=False,
        domain=[("model", "=", "openg2p.disbursement.slip")],
    )
    disbursement_batch_email_template_id = fields.Many2one(
        "mail.template",
        string="Email Template",
        related="company_id.disbursement_batch_email_template_id",
        help="Template used to send disbursement notification email messages",
        readonly=False,
        domain=[("model", "=", "openg2p.disbursement.slip")],
    )
    disbursement_slip_model_id = fields.Many2one(
        "ir.model",
        default=lambda r: r.env.ref(
            "openg2p_disbursement.model_openg2p_disbursement_slip", False
        ),
    )
