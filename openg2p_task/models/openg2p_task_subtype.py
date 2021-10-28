from odoo import models, fields, api


class Openg2pTaskSubtype(models.Model):
    _name = "openg2p.task.subtype"
    _description = "Task subtask mapping for OpenG2P"

    task_type_id = fields.Many2one(
        comodel_name="openg2p.task.type",
        string="Task Type",
    )
    name = fields.Char(string="Task Subtype Name")
    role_id = fields.Many2one(
        comodel_name="openg2p.task.role",
        string="Task Role",
    )
    # for building url
    # entity_type_id = model.submodel, example: openg2p.registration
    entity_type_id = fields.Char(
        string="Entity Type",
    )
    # entity_view_type = kanban, list, form
    entity_view_type = fields.Char(
        string="Entity View Type",
    )
    # view's external id = model_name.view_ext_id
    entity_view_id = fields.Char(
        string="Entity View ID",
    )

    @api.onchange("task_type_id")
    def onchange_task_type(self):
        for rec in self:
            return {"domain": {"role_id": [("task_type_id", "=", rec.task_type_id.id)]}}

    def name_get(self):
        for rec in self:
            yield rec.id, rec.name

    def api_json(self):
        return {
            "task_type": self.task_type_id.id,
            "name": self.name,
            "task_role": self.role_id.id,
        }
