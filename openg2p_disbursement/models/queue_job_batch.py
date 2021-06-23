import json

from odoo import models


class QueueJobBatch(models.Model):
    _inherit = "queue.job.batch"

    def write(self, vals):
        super(QueueJobBatch, self).write(vals)
        if "state" in vals and vals["state"] == "finished":
            batch = self.env["openg2p.disbursement.batch"].search(
                [("job_batch_id", "in", self.ids)]
            )
            batch.ensure_one()
            if batch.job_failed_count:
                batch.batch_notify_failed()
            else:
                batch.batch_notify_success()
