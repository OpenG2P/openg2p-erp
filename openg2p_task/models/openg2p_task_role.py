from odoo import models, fields


class Openg2pTaskRole(models.Model):
    _name = "openg2p.task.role"
    _description = "Task roles for OpenG2P"

    name = fields.Char(string="Name")

    task_type_id = fields.Many2one(comodel_name="openg2p.task.type", string="Task Type")

    assignee_role_id = fields.Integer(
        required=True,
        string="Assignee",
    )

    def name_get(self):
        for rec in self:
            yield rec.id, rec.name
