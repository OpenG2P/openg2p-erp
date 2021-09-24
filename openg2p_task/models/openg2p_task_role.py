from odoo import api, models, fields


class Openg2pTaskRole(models.Model):
    _name = "openg2p.taskrole"
    _description = "Task roles for OPENG2P"

    assign_role_id = fields.Integer(
        required=True
    )

    
