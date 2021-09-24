from odoo import models, fields


class Openg2pTaskHistory(models.Model):
    _name = "openg2p.task.history"
    _description = "Task History"

    task_id = fields.One2many(
        comodel_name='openg2p.task',
        string="Task ID",
        inverse_name="id"
    )

    task_status = fields.Selection(
        selection=(
            ("todo", "To-Do"),
            ("done", "Done"),
        ),
        string="Task Status",
    )

    task_assignee_id = fields.Many2one(
        "res.users",
        string="Task Assignee ID",
        default=lambda self: self.env.uid,
    )

    task_name = fields.Selection(
        string="Task Name",
        selection=(
            ("approve_payment_list", "Approve Payment List"),
            ("send_payment_list", "Send Payment List"),
            ("review_settlement_report", "Review Settlement Report"),
            ("beneficiary_from_registrations", "Create Beneficiary List from Processed Registrations"),
            ("odk_to_registrations", "Pull Registrations from Data Collection Source"),
            ("complete_reconciliation", "Complete Reconciliation"),
        )
    )

    task_modifiedby_id = fields.Many2one(
        "res.users",
        string="Last modified by",
        default=lambda self: self.env.uid,
    )

    # create_date of this entity = modifiedby_date of task
