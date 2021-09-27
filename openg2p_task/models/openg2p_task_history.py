from odoo import models, fields


class Openg2pTaskHistory(models.Model):
    _name = "openg2p.task.history"
    _description = "Task History for OpenG2P"

    task_id = fields.Many2one(
        comodel_name="openg2p.task",
        string="Task ID",
    )

    task_type_id = fields.Many2one("openg2p.task.type", string="Task Type")

    task_subtype_id = fields.Many2one("openg2p.task.subtype", string="Task Subtype")

    task_status = fields.Selection(
        selection=(
            ("todo", "To-Do"),
            ("done", "Done"),
        ),
        string="Task Status",
    )

    # for building url
    task_entity_type_id = fields.Integer(
        string="Entity Type",
    )

    # for building url
    task_entity_id = fields.Integer(
        string="Entity ID",
    )

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
        return [
            (rec.id, f"{rec.task_type_id.name}/{rec.task_subtype_id.name} (H{rec.id})")
            for rec in self
        ]

    # create_date of this entity = modifiedby_date of task
