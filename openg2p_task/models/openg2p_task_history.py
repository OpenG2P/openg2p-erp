from odoo import models, fields


class Openg2pTaskHistory(models.Model):
    _name = "openg2p.task.history"
    _description = "Task History for OpenG2P"
    _order = "id desc"

    task_id = fields.Many2one(
        comodel_name="openg2p.task",
        string="Task ID",
    )

    task_type_id = fields.Many2one("openg2p.task.type", string="Task Type")

    task_subtype_id = fields.Many2one("openg2p.task.subtype", string="Task Subtype")

    task_status_id = fields.Many2one(
        "openg2p.task.status",
        string="Task Status",
    )

    # for building url
    task_entity_type_id = fields.Char(
        string="Entity Type",
    )

    # for building url
    task_entity_id = fields.Integer(
        string="Entity ID",
    )
    process_id = fields.Integer(string="Process")
    program_id = fields.Integer(
        string="Program",
    )

    task_assignee_id = fields.Many2one(
        "res.users",
        string="Task Assignee ID",
        default=lambda self: self.env.uid,
    )

    task_modifiedby_id = fields.Many2one(
        "res.users",
        string="Last modified by",
        default=lambda self: self.env.uid,
    )

    def name_get(self):
        for rec in self:
            yield rec.id, f"{rec.task_type_id.name}/{rec.task_subtype_id.name} (H{rec.id})"

    # create_date of this entity = modifiedby_date of task
