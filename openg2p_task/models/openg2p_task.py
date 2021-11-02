from odoo import models, fields, api


class Openg2pTask(models.Model):
    _name = "openg2p.task"
    _description = "Task Management for OpenG2P"
    _order = "id desc"

    type_id = fields.Many2one(
        "openg2p.task.type",
        store=False,
        compute="_compute_task_details",
        readonly=True,
        string="Task Type",
    )

    subtype_id = fields.Many2one("openg2p.task.subtype", string="Task Subtype")

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

    process_id = fields.Integer(string="Process")

    description = fields.Text(string="Description")

    status_id = fields.Many2one(
        "openg2p.task.status",
        string="Task Status",
        group_expand="_read_group_status_ids",
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
    def _compute_task_details(self):
        for rec in self:
            rec.type_id = rec.subtype_id.task_type_id.id

    def target_url_button(self):
        data = {
            "name": "Complete Task",
            "res_model": self.subtype_id.entity_type_id,
            "type": "ir.actions.act_window",
            "context": {},
            "view_mode": self.subtype_id.entity_view_type,
            "view_type": "form",
            "view_id": self.env.ref(self.subtype_id.entity_view_id).id,
            "target": "fullscreen",
        }
        if self.entity_id:
            data["res_id"] = self.entity_id
            data["flags"] = {"mode": "readonly"}
        return data

    @api.multi
    def _create_history(self):
        self.env["openg2p.task.history"].create(
            {
                "task_id": self.id,
                "task_type_id": self.type_id.id,
                "task_subtype_id": self.subtype_id.id,
                "task_status_id": self.status_id.id,
                "task_entity_id": self.entity_id,
                "task_assignee_id": self.assignee_id.id,
                "task_modifiedby_id": self.lastmodifiedby_id.id,
                "process_id": self.process_id,
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
        for rec in self:
            yield rec.id, f"{rec.type_id.name}/{rec.subtype_id.name} ({rec.id})"

    # created_date of this entity = create_date
    # lastmodifiedby_date of this entity = write_date

    @api.model
    def _read_group_status_ids(self, status, domain, order):
        return self.env["openg2p.task.status"].search([])

    def api_json(self):
        return {
            "id": self.id,
            "assignee_id": self.assignee_id.id,
            "description": self.description,
            "context": self.context,
            "created_by_id": self.createdby_id.id,
            "last_modified_by_id": self.lastmodifiedby_id.id,
            "status_id": self.status_id.id,
            "task_type": self.type_id.id,
            "entity_id": self.entity_id,
            "estimated_time_allotment": self.eta,
        }
