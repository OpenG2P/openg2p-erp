# -*- coding: utf-8 -*-
from odoo import models, fields, api


class EmploymentInactivate(models.TransientModel):
    _name = 'wiz.disenrollment'
    _description = 'Beneficiary Disenrollment Wizard'

    date = fields.Date(
        'Effective Date',
        required=True,
    )
    reason_id = fields.Many2one(
        'openg2p.disenrollment.reason',
        'Reason',
        required=True
    )
    program_id = fields.Many2one(
        'openg2p.program',
        string="Program",
    )
    notes = fields.Text(
        'Notes',
    )
    type = fields.Selection(
        [('program', 'Disenroll from a Program'), ('database', 'End all Programs and Archive')],
        required=True
    )

    @api.multi
    def apply(self):
        self.ensure_one()
        res = self.env['openg2p.disenrollment']
        for rec in self.env.context.get('active_ids'):
            vals = {
                'date': self.date,
                'beneficiary_id': rec,
                'reason_id': self.reason_id.id,
                'notes': self.notes,
                'type': self.type,
                'program_id': self.program_id.id
            }
            res += self.env['openg2p.disenrollment'].create(vals)
        action = self.env.ref('openg2p_disenrollment.open_openg2p_disenrollment').read()[0]
        action['domain'] = str([
            ('id', 'in', res.ids),
        ])
        return action
