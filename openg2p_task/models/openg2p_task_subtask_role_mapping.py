from odoo import api, models, fields


class Openg2pTaskRole(models.Model):
    _name = "openg2p.taskrole"
    _description = "Task roles for OPENG2P"

    task_type_id = fields.Integer(
        required=True
    )
    task_sub_type_id = fields.Integer(
        required=True
    )
    role_id = fields.Integer(
        required=True
    )


