from odoo import models, fields, api


class Openg2pTask(models.Model):
    _name = "openg2p.task"
    _description = "Task Management for OpenG2P"

    name = fields.Selection(
        string="Name",
        selection=(
            ("approve_payment_list", "Approve Payment List"),
            ("send_payment_list", "Send Payment List"),
            ("review_settlement_report", "Review Settlement Report"),
            ("beneficiary_from_registrations", "Create Beneficiary List from Processed Registrations"),
            ("odk_to_registrations", "Pull Registrations from Data Collection Source"),
            ("complete_reconciliation", "Complete Reconciliation"),
        )
    )

    assignee_id = fields.Many2one(
        "res.users",
        string="Assignee ID",
        default=lambda self: self.env.uid,
    )

    workflow_pid = fields.Integer(string="Workflow Process ID")

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

    @api.multi
    def _create_history(self):
        print("creating history")
        self.env["openg2p.task.history"].create({
            "task_id": self.id,
            "task_status": self.status,
            "task_assignee_id": self.assignee_id,
            "task_name": self.name,
            "task_modifiedby_id": self.lastmodifiedby_id,
        })

    @api.multi
    @api.model
    def create(self, vals):
        res = super(Openg2pTask, self).create(vals)
        res._create_history()
        return res

    @api.multi
    @api.model
    def write(self, vals):
        res = super(Openg2pTask, self).write(vals)
        res._create_history()
        return res

    # created_date of this entity = create_date
    # lastmodifiedby_date of this entity = write_date
