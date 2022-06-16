# Copyright 2004-2010 Tiny SPRL http://tiny.be
# Copyright 2010-2012 ChriCar Beteiligungs- und Beratungs- GmbH
#             http://www.camptocamp.at
# Copyright 2015 Antiun Ingenieria, SL (Madrid, Spain)
#        http://www.antiun.com
#        Antonio Espinosa <antonioea@antiun.com>
# Copyright  2016 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import api, models, fields, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools.safe_eval import safe_eval


class HrBeneficiaryIdCategory(models.Model):
    _name = "openg2p.beneficiary.id_category"
    _description = "Beneficiary ID Type"
    _order = "name"

    code = fields.Char(
        string="Code",
        size=16,
        required=True,
        help="Abbreviation or acronym of this ID type. For example, "
        "'driver_license'. NOTE: DO NOT CHANGE AFTER CREATED",
    )
    name = fields.Char(
        string="ID Name",
        required=True,
        translate=True,
        help="Name of this ID type. For example, 'Driver License'",
    )
    active = fields.Boolean(string="Active", default=True)
    validation_code = fields.Text(
        "Python validation code",
        help="Python code called to validate an id number.",
        default=lambda self: self._default_validation_code(),
    )

    def _default_validation_code(self):
        return _(
            "\n# Python code. Use failed = True to specify that the id "
            "number is not valid.\n"
            "# You can use the following variables :\n"
            "#  - self: browse_record of the current ID Category "
            "browse_record\n"
            "#  - id_number: browse_record of ID number to validate"
        )

    def _validation_eval_context(self, id_number):
        self.ensure_one()
        return {
            "self": self,
            "id_number": id_number,
        }

    def validate_id_number(self, id_number):
        """Validate the given ID number
        The method raises an odoo.exceptions.ValidationError if the eval of
        python validation code fails
        """
        self.ensure_one()
        if self.env.context.get("id_no_validate"):
            return
        eval_context = self._validation_eval_context(id_number)
        try:
            safe_eval(self.validation_code, eval_context, mode="exec", nocopy=True)
        except Exception as e:
            raise UserError(
                _(
                    "Error when evaluating the id_category validation code:"
                    ":\n %s \n(%s)"
                )
                % (self.name, e)
            )
        if eval_context.get("failed", False):
            raise ValidationError(
                _("%s is not a valid %s identifier") % (id_number.name, self.name)
            )
