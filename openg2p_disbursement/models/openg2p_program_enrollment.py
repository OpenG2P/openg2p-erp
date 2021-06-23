# -*- coding:utf-8 -*-

from odoo import api, fields, models


class HrEnrollment(models.Model):
    """
    Beneficiary enrollment based on the visa, work permits
    allows to configure different Disbursement structure
    """

    _inherit = "openg2p.program.enrollment"
    _description = "Beneficiary Enrollment"

    struct_id = fields.Many2one(
        "openg2p.disbursement.structure",
        string="Disbursement Structure",
        readonly=True,
        related="category_id.struct_id",
    )
    disbursement_amount = fields.Monetary(
        "Disbursement Amount",
        digits=(16, 2),
        readonly=True,
        store=False,  # we keep this as false because it potentially slows down writes
        related="category_id.disbursement_amount",
        track_visibility="onchange",
        help="Basic amount disbursed.",
    )

    @api.multi
    def get_all_structures(self):
        """
        @return: the structures linked to the given enrollments, ordered by hierachy (parent=False first,
                 then first level children and so on) and without duplicata
        """
        structures = self.mapped("struct_id")
        if not structures:
            return []
        return list(set(structures._get_parent_structure().ids))
