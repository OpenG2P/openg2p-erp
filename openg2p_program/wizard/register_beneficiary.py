# -*- coding: utf-8 -*-
from odoo import fields, models, api


class RegisterWizard(models.TransientModel):
    """
        A wizard to manage the creation/removal of register users.
    """

    _name = 'beneficiary.register.wizard'
    _description = 'Register Into Program'

    program_id = fields.Many2one(
        'openg2p.program',
        string="Program",
        required=True,
    )
    category_id = fields.Many2one(
        'openg2p.program.registration_category',
        string="Classification",
        required=True,
    )
    date_start = fields.Date(
        'Registration Date',
        required=True,
        default=fields.Date.context_today,
        help="Start date of the program registration.",
    )
    use_active_domain = fields.Boolean('Use active domain')
    auto_confirm = fields.Boolean(
        'Auto Confirm Registrations',
        default=True
    )

    @api.multi
    def action_apply(self):
        beneficiary_obj = self.env['openg2p.beneficiary']
        self.ensure_one()
        if self.use_active_domain:
            beneficiaries = beneficiary_obj.search(self.env.context.get('active_domain'))
        else:
            beneficiaries = beneficiary_obj.browse(self.env.context.get('active_ids'))

        if len(beneficiaries) > 1000:
            beneficiaries = beneficiaries.sudo().with_delay()

        beneficiaries.program_register(
            program_id=self.program_id.id,
            category_id=self.category_id.id, date_start=self.date_start, confirm=self.auto_confirm
        )
        return {'type': 'ir.actions.act_window_close'}
