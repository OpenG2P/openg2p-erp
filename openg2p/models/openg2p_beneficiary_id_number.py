# Copyright 2004-2010 Tiny SPRL http://tiny.be
# Copyright 2010-2012 ChriCar Beteiligungs- und Beratungs- GmbH
#             http://www.camptocamp.at
# Copyright 2015 Antiun Ingenieria, SL (Madrid, Spain)
#        http://www.antiun.com
#        Antonio Espinosa <antonioea@antiun.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import api, models, fields


class OpenG2PBeneficiaryIdNumber(models.Model):
    _name = "openg2p.beneficiary.id_number"
    _description = "Beneficiary ID Number"
    _order = "name"

    @api.constrains("name", "category_id")
    def validate_id_number(self):
        for rec in self:
            rec.category_id.validate_id_number(self)

    name = fields.Char(
        string="ID Number",
        required=True,
        index=True,
        help="The ID itself. For example, Driver License number of this " "person",
    )
    category_id = fields.Many2one(
        string="Type",
        required=True,
        comodel_name="openg2p.beneficiary.id_category",
        help="ID type defined in configuration. For example, Driver License",
        ondelete="restrict",
    )
    beneficiary_id = fields.Many2one(
        string="Beneficiary",
        required=True,
        comodel_name="openg2p.beneficiary",
        ondelete="cascade",
    )
    date_issued = fields.Date(
        string="Issued on",
        help="Issued date. For example, date when person approved his driving "
        "exam, 21/10/2009",
    )
    valid_from = fields.Date(
        string="Valid from", help="Validation period stating date."
    )
    valid_until = fields.Date(
        string="Valid until",
        help="Expiration date. For example, date when person needs to renew "
        "his driver license, 21/10/2019",
    )
    comment = fields.Text(string="Notes")
    active = fields.Boolean(string="Active", default=True)

    _sql_constraints = [
        (
            "uniq_identification",
            "unique (category_id, name)",
            "Beneficiary with this ID already exists.",
        )
    ]
