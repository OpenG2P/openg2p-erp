from odoo import models, fields


class Openg2pTaskType(models.Model):
    _name = "openg2p.task.type"
    _description = "Task types for OpenG2P"

    name = fields.Char(string="Name")

    def name_get(self):
        for rec in self:
            yield rec.id, rec.name
