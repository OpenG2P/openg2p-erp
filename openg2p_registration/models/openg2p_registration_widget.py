from odoo import fields, models, api


class UpdateWizard(models.TransientModel):
    _name = "openg2p.registration.update_att"

    val = fields.Char("New Attendance")

    @api.multi
    def update_att(self):
        regd_obj = self.env["openg2p.registration"]
        # self.ensure_one()
        regds = regd_obj.browse(self.env.context.get("active_ids"))
        # print(regds)
        # print(type(regds))
        for regd in regds:
            print("REGD:", regd.id)
            att = self.env["openg2p.beneficiary.orgmap"].search(
                [
                    "&",
                    ("registration", "=", regd.id),
                    ("field_name", "=", "total_student_in_attendance_at_the_school"),
                ]
            )
            if att:
                print("ATT:", att.field_value)
                att.field_value = int(self.val)
                print("ATT:", att.field_value)
            else:
                self.env["openg2p.beneficiary.orgmap"].create(
                    {
                        "field_name": "total_student_in_attendance_at_the_school",
                        "field_value": self.val,
                        "registration": regd.id,
                    }
                )
        return {"type": "ir.actions.act_window_close"}

    @api.multi
    def update_stage(self):
        regd_obj = self.env["openg2p.registration"]
        regds = regd_obj.browse(self.env.context.get("active_ids"))
        for regd in regds:
            print("REGD:", regd.id)
            regd.stage_id = 5
        return {"type": "ir.actions.act_window_close"}
