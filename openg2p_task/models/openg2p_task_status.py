from odoo import models, fields


class Openg2pTaskStatus(models.Model):
    _name = "openg2p.task.status"
    _description = "Task status for OpenG2P Tasks"

    name = fields.Char(string="Name")

    def name_get(self):
        for rec in self:
            yield rec.id, rec.name
