import json

from odoo import models


class QueueJobBatch(models.Model):
    _inherit = 'queue.job.batch'

    def write(self, vals):
        super(QueueJobBatch, self).write(vals)
        if 'state' in vals and vals['state'] == 'finished':
            batch = self.env['openg2p.disbursement.batch'].search([('job_batch_id', 'in', self.ids)])
            batch.ensure_one()
            if batch.job_failed_count:
                batch.write({'state': 'failed'})
            else:
                batch.write({'state': 'draft'})
                batch.post_generate_run(json.loads(batch.intended_beneficiaries))
