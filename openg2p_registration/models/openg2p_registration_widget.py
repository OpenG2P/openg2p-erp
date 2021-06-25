from odoo import fields, models, api


class UpdateWizard(models.TransientModel):
    _name = 'openg2p.registration.update_att'

    @api.multi
    def _default_stage_id(self):
        ids = self.env['openg2p.registration.stage'].search([
            ('fold', '=', False)
        ], order='sequence asc', limit=1).ids
        if ids:
            return ids[0]
        return False

    val = fields.Char('New Attendance')
    stage_id = fields.Many2one(
        'openg2p.registration.stage',
        'Stage',
        ondelete='restrict',
        track_visibility='onchange',
        copy=False,
        index=True,
        group_expand='_read_group_stage_ids',
        default=_default_stage_id
    )

    @api.multi
    def update_att(self):
        regd_obj = self.env['openg2p.registration']
        regds = regd_obj.browse(self.env.context.get('active_ids'))
        for regd in regds:
            print('REGD:', regd.id)
            att = self.env['openg2p.beneficiary.orgmap'].search(
                ['&', ('registration', '=', regd.id),
                 ('field_name', '=', 'total_student_in_attendance_at_the_school')]
            )
            if att:
                print('ATT:', att.field_value)
                att.field_value = int(self.val)
                print('ATT:', att.field_value)
            else:
                self.env['openg2p.beneficiary.orgmap'].create({
                    'field_name': 'total_student_in_attendance_at_the_school',
                    'field_value': self.val,
                    'registration': regd.id,
                })
        return {'type': 'ir.actions.act_window_close'}

    @api.multi
    def update_stage(self):
        regd_obj = self.env['openg2p.registration']
        regds = regd_obj.browse(self.env.context.get('active_ids'))
        for regd in regds:
            print('REGD:', regd.id)
            print('REGD:', regd.stage_id, self.stage_id)
            regd.stage_id = self.stage_id
        return {'type': 'ir.actions.act_window_close'}
