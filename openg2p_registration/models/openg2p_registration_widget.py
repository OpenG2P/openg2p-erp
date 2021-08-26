from odoo import fields, models, api


class UpdateWizard(models.TransientModel):
    _name = "openg2p.registration.update_regd"

    def _default_stage_id(self):
        ids = (
            self.env["openg2p.registration.stage"]
            .search([("fold", "=", False)], order="sequence asc", limit=1)
            .ids
        )
        if ids:
            return ids[0]
        return False

    stage_id = fields.Many2one(
        "openg2p.registration.stage",
        "Stage",
        ondelete="restrict",
        track_visibility="onchange",
        copy=False,
        index=True,
        group_expand="_read_group_stage_ids",
        default=_default_stage_id,
    )

    @api.multi
    def update_stage(self):
        regd_obj = self.env["openg2p.registration"]
        regds = regd_obj.browse(self.env.context.get("active_ids"))
        for regd in regds:
            regd.stage_id = self.stage_id
        return {"type": "ir.actions.act_window_close"}

    @api.multi
    def registration_to_beneficiary(self):
        regd_obj = self.env["openg2p.registration"]
        regds = regd_obj.browse(self.env.context.get("active_ids"))
        for regd in regds:
            regd.create_beneficiary_from_registration()
