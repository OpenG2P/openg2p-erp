# -*- coding: utf-8 -*-
# Copyright 2020 OpenG2P (https://openg2p.org)
# @author: Salton Massally <saltonmassally@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models, api


class Openg2pBeneficiary(models.Model):
    _inherit = 'openg2p.beneficiary'

    disenrollment_ids = fields.One2many(
        'openg2p.disenrollment',
        'beneficiary_id',
        'Disenrollment Records'
    )

    @api.multi
    def toggle_active(self):
        super(Openg2pBeneficiary, self).toggle_active()
        deactivations = self.filtered(lambda r: not r.active)

        if deactivations:
            self.env['openg2p.program.registration'].search(
                [
                    ('beneficiary_id', 'in', deactivations.ids),
                    ('state', '!=', 'close'),
                ]
            ).write({'date_end': fields.Date.today(), 'state': 'close'})
