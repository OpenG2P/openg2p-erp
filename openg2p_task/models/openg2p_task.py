from odoo import models, fields, api


class Openg2pTask(models.Model):
    _name = "openg2p.task"
    _description = "Task Management for OpenG2P"

    type_id = fields.Many2one(
        "openg2p.task.type",
        store=False,
        compute="_compute_task_type",
        readonly=True,
        string="Task Type",
    )

    subtype_id = fields.Many2one("openg2p.task.subtype", string="Task Subtype")

    # for building url
    entity_type_id = fields.Integer(
        string="Entity Type",
    )

    # for building url
    entity_id = fields.Integer(
        string="Entity ID",
    )

    eta = fields.Datetime(
        string="ETA",
    )

    context = fields.Text(
        string="Context",
    )

    assignee_id = fields.Many2one(
        "res.users",
        string="Assignee",
        default=lambda self: self.env.uid,
    )

    workflow_pid = fields.Integer(string="Workflow Process")

    description = fields.Text(string="Description")

    target_url = fields.Char(string="Target URL")

    status = fields.Selection(
        selection=(
            ("todo", "To-Do"),
            ("done", "Done"),
        ),
        string="Task Status",
    )

    createdby_id = fields.Many2one(
        "res.users",
        string="Created by",
        default=lambda self: self.env.uid,
    )

    lastmodifiedby_id = fields.Many2one(
        "res.users",
        string="Last modified by",
        default=lambda self: self.env.uid,
    )

    @api.depends("subtype_id")
    def _compute_task_type(self):
        for rec in self:
            rec.type_id = rec.subtype_id.task_type_id.id

    @api.multi
    def _create_history(self):
        self.env["openg2p.task.history"].create(
            {
                "task_id": self.id,
                "task_type_id": self.type_id.id,
                "task_subtype_id": self.subtype_id.id,
                "task_status": self.status,
                "task_entity_type_id": self.entity_type_id,
                "task_entity_id": self.entity_id,
                "task_assignee_id": self.assignee_id.id,
                "task_modifiedby_id": self.lastmodifiedby_id.id,
            }
        )

    @api.model
    def create(self, vals):
        res = super(Openg2pTask, self).create(vals)
        assert isinstance(res, Openg2pTask)
        res._create_history()
        return res

    @api.multi
    @api.model
    def write(self, vals):
        res = super(Openg2pTask, self).write(vals)
        if res:
            self._create_history()
        return res

    def name_get(self):
        return [
            (rec.id, f"{rec.type_id.name}/{rec.subtype_id.name} ({rec.id})")
            for rec in self
        ]

    # created_date of this entity = create_date
    # lastmodifiedby_date of this entity = write_date
