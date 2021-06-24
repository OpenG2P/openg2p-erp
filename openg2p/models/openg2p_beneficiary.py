# -*- coding: utf-8 -*-
# Copyright 2020 OpenG2P (https://openg2p.org)
# @author: Salton Massally <saltonmassally@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64
import copy
import logging
import random
import string
import requests
from dateutil.relativedelta import relativedelta
from odoo.addons.component.core import WorkContext

from odoo import api, fields, models
from odoo import tools, _
from odoo.addons.base.models.res_partner import ADDRESS_FIELDS
from odoo.exceptions import ValidationError, UserError
from odoo.modules.module import get_module_resource
from odoo.addons.openg2p.services.matching_service import MATCH_MODE_NORMAL

_logger = logging.getLogger(__name__)


@api.model
def _lang_get(self):
    return self.env["res.lang"].get_installed()


_PARTNER_FIELDS = ['firstname', 'lastname', 'street', 'street2', 'zip', 'state', 'city', 'country_id']



class Beneficiary(models.Model):
    _name = "openg2p.beneficiary"
    _description = "Beneficiary"
    _order = "name"
    _inherit = [
        "format.address.mixin",
        "mail.thread",
        "mail.activity.mixin",
        "generic.mixin.no.unlink",
        "phone.validation.mixin",
        "openg2p.mixin.has_document",
        "openg2p.mixin.no_copy",
        "openg2p.mixin.no_name_create",
    ]

    @api.model
    def _default_image(self):
        image_path = get_module_resource(
            "openg2p", "static/src/img", "default_image.png"
        )
        return tools.image_resize_image_big(
            base64.b64encode(open(image_path, "rb").read())
        )

    partner_id = fields.Many2one(
        "res.partner",
        required=True,
        ondelete="restrict",
        string="Related Partner",
        help="Partner-related data of the beneficiary",
    )
    firstname = fields.Char(
        track_visibility="onchange", index=True, required=True, string="First Name"
    )
    lastname = fields.Char(
        track_visibility="onchange", index=True, required=True, string="Last Name"
    )
    othernames = fields.Char(
        track_visibility="onchange", index=True, string="Other Names"
    )
    name = fields.Char(
        compute="_compute_full_name", store=True, index=True, readonly=True
    )
    comment = fields.Text(string="Notes")
    title = fields.Many2one("res.partner.title")
    display_name = fields.Char(compute="_compute_display_name", store=True, index=True)
    lang = fields.Selection(
        _lang_get,
        string="Language",
        default=lambda self: self.env.lang,
        help="All the emails and documents sent to this contact will be translated in this language.",
    )
    ref = fields.Char(string="Internal Reference", index=True)
    street = fields.Char(track_visibility="onchange", required=True)
    street2 = fields.Char(track_visibility="onchange")
    zip = fields.Char(track_visibility="onchange", change_default=True, index=True)
    city = fields.Char(track_visibility="onchange", required=True, string="City/Town")
    state_id = fields.Many2one(
        "res.country.state",
        string="State/District",
        ondelete="restrict",
        domain="[('country_id', '=', country_id)]",
        track_visibility="onchange",
        required=True,
    )
    country_id = fields.Many2one(
        "res.country",
        string="Country",
        ondelete="restrict",
        track_visibility="onchange",
        required=True,
        default=lambda self: self.env.user.company_id.country_id.id,
    )
    email = fields.Char(track_visibility="onchange")
    email_formatted = fields.Char(
        "Formatted Email",
        compute="_compute_email_formatted",
        help='Format email address "Name <email@domain>"',
    )
    phone = fields.Char(track_visibility="onchange", string="Primary Phone", index=True)
    mobile = fields.Char(
        track_visibility="onchange", string="Secondary Phone", index=True
    )
    active = fields.Boolean(
        default=True,
        readonly=True,
        track_visibility="onchange",
    )
    display_address = fields.Char(
        compute="_compute_display_address", store=True, readonly=True, index=True
    )
    marital = fields.Selection(
        [
            ("single", "Single"),
            ("married", "Married"),
            ("cohabitant", "Legal Cohabitant"),
            ("widower", "Widower"),
            ("divorced", "Divorced"),
        ],
        string="Marital Status",
        default="single",
        track_visibility="onchange",
    )
    gender = fields.Selection(
        [("male", "Male"), ("female", "Female"), ("other", "Other")],
        track_visibility="onchange",
        required=True,
    )
    birth_city = fields.Char(track_visibility="onchange")
    birth_state_id = fields.Many2one(
        comodel_name="res.country.state",
        string="Birth State/District",
        domain="[('country_id', '=', birth_country_id)]",
        ondelete="restrict",
        track_visibility="onchange",
    )
    birth_country_id = fields.Many2one(
        comodel_name="res.country",
        string="Birth Country",
        ondelete="restrict",
        default=lambda self: self.env.user.company_id.country_id.id,
        track_visibility="onchange"
    )
    birthday = fields.Date(
        "Birth Date",
        track_visibility='onchange'
    )
    age = fields.Integer(
        string="Age",
        readonly=True,
        compute="_compute_age",
        store=False,
        search='_search_age'
    )
    identities = fields.One2many(
        comodel_name="openg2p.beneficiary.id_number",
        inverse_name="beneficiary_id",
        string="Identifications",
        track_visibility="onchange",
        index=True,
    )
    national_id = fields.Char(
        string="National ID",
        track_visibility="onchange",
        compute=lambda s: s._compute_identification(
            "national_id",
            "NIN",
        ),
        inverse=lambda s: s._inverse_identification(
            "national_id",
            "NIN",
        ),
        search=lambda s, *a: s._search_identification("NIN", *a),
        readonly=True,
        index=True,
    )
    passport_id = fields.Char(
        string="Passport No",
        track_visibility="onchange",
        compute=lambda s: s._compute_identification(
            "passport_id",
            "PASSPORT",
        ),
        inverse=lambda s: s._inverse_identification(
            "passport_id",
            "PASSPORT",
        ),
        search=lambda s, *a: s._search_identification("PASSPORT", *a),
        readonly=True,
        index=True,
    )
    ssn = fields.Char(
        string="Social Security #",
        track_visibility="onchange",
        compute=lambda s: s._compute_identification(
            "ssn",
            "SSN",
        ),
        inverse=lambda s: s._inverse_identification(
            "ssn",
            "SSN",
        ),
        search=lambda s, *a: s._search_identification("SSN", *a),
        readonly=True,
        index=True,
    )
    emergency_contact = fields.Char("Emergency Contact", track_visibility="onchange")
    emergency_phone = fields.Char("Emergency Phone", track_visibility="onchange")
    # image: all image fields are base64 encoded and PIL-supported
    image = fields.Binary(
        "Image",
        default=_default_image,
        track_visibility="onchange",
        attachment=True,
        help="This field holds the image used as avatar for this beneficiary, limited to 1024x1024px",
    )
    image_medium = fields.Binary(
        "Medium-sized image",
        attachment=True,
        help="Medium-sized image of this beneficiary. It is automatically "
        "resized as a 128x128px image, with aspect ratio preserved. "
        "Use this field in form views or some kanban views.",
    )
    image_small = fields.Binary(
        "Small-sized image",
        attachment=True,
        help="Small-sized image of this beneficiary. It is automatically "
        "resized as a 64x64px image, with aspect ratio preserved. "
        "Use this field anywhere a small image is required.",
    )
    location_id = fields.Many2one(
        "openg2p.location",
        "Location",
        index=True,
        track_visibility="onchange",
        ondelete="restrict",
        required=True,
    )
    category_id = fields.Many2many(
        "openg2p.beneficiary.category",
        string="Tags",
        track_visibility="onchange",
        index=True,
    )
    search_no_category_id = fields.Many2one(
        "openg2p.beneficiary.category",
        string="Without This Tag",
        search="_search_no_tag_id",
        compute="_compute_search_no_category",
        store=False,
        readonly=True,
        help="Find all records without this tag",
    )
    company_id = fields.Many2one(
        "res.company",
        "Company",
        required=True,
        readonly=True,
        ondelete="restrict",
        default=lambda self: self.env.user.company_id,
    )
    merged_beneficiary_ids = fields.Many2many(
        "openg2p.beneficiary",
        "merged_beneficiary_rel",
        "retained_id",
        "merged_id",
        string="Merged Duplicates",
        index=True,
        context={"active_test": False},
        help="Duplicate records that have been merged with this."
        " Primary function is to allow to reference of merged records ",
    )

    _sql_constraints = [
        ("ref_id_uniq", "unique(ref)", "The Beneficiary reference must be unique."),
    ]

    def _search_age(self, operator, val):
        res = []
        bs = self.env['openg2p.beneficiary'].search([])
        for b in bs:
            print(b.age, operator, val)
            if operator == '=':
                if b.age == val:
                    res.append(b)
            elif operator == '!=':
                if b.age != val:
                    res.append(b)
            elif operator == '<':
                if b.age < val:
                    res.append(b)
            elif operator == '>':
                if b.age > val:
                    res.append(b)
            elif operator == '>=':
                if b.age >= val:
                    res.append(b)
            elif operator == '<=':
                if b.age <= val:
                    res.append(b)
        return [('id', 'in', [rec.id for rec in res])]

    @api.onchange('phone', 'country_id')
    def _onchange_phone_validation(self):
        if self.phone:
            self.phone = self.phone_format(self.phone)

    @api.onchange("mobile", "country_id")
    def _onchange_mobile_validation(self):
        if self.mobile:
            self.mobile = self.phone_format(self.mobile)

    def _partner_create(self, vals):
        partner_vals = {}
        for i in _PARTNER_FIELDS:
            if i in vals:
                partner_vals[i] = vals[i]
        partner_vals["name"] = vals["firstname"] + " " + vals["lastname"]
        partner = self.env["res.partner"].create(partner_vals)
        vals["partner_id"] = partner.id

    def _partner_update(self, vals):
        self.ensure_one()
        partner_vals = {}
        for i in _PARTNER_FIELDS:
            if i in vals:
                partner_vals[i] = vals[i]
        if partner_vals:
            partner_vals["name"] = self.name
        self.partner_id.write(partner_vals)

    @api.model
    def create(self, vals):
        if not vals.get("ref"):
            vals["ref"] = self._generate_ref()
        tools.image_resize_images(vals)
        if not vals.get("phone") and vals.get("mobile"):
            vals["phone"] = vals.get("mobile")
        self._partner_create(vals)
        return super(Beneficiary, self).create(vals)

    @api.multi
    def write(self, vals):
        tools.image_resize_images(vals)
        res = super(Beneficiary, self).write(vals)
        for i in self:
            i._partner_update(vals)
        return res

    @api.onchange("country_id")
    def _onchange_country_id(self):
        if self.country_id and self.country_id != self.state_id.country_id:
            self.state_id = False

    @api.onchange("state_id")
    def _onchange_state(self):
        if self.state_id.country_id:
            self.country_id = self.state_id.country_id

    @api.depends("name", "email")
    def _compute_email_formatted(self):
        for beneficiary in self:
            if beneficiary.email:
                beneficiary.email_formatted = tools.formataddr(
                    (beneficiary.name or u"False", beneficiary.email or u"False")
                )
            else:
                beneficiary.email_formatted = ""

    @api.model
    def _address_fields(self):
        """Returns the list of address fields that are synced from the parent."""
        return list(ADDRESS_FIELDS)

    @api.model
    def _formatting_address_fields(self):
        """Returns the list of address fields usable to format addresses."""
        return self._address_fields()

    @api.multi
    def update_address(self, vals):
        addr_vals = {key: vals[key] for key in self._address_fields() if key in vals}
        if addr_vals:
            return super(Beneficiary, self).write(addr_vals)

    @api.depends("firstname", "lastname")
    def _compute_full_name(self):
        for rec in self:
            if rec.othernames:
                rec.name = "%s %s %s" % (rec.firstname, rec.othernames, rec.lastname)
            else:
                rec.name = "%s %s" % (rec.firstname, rec.lastname)

    @api.depends("name")
    def _compute_display_name(self):
        names = dict(self.name_get())
        for beneficiary in self:
            beneficiary.display_name = names.get(beneficiary.id)

    @api.multi
    @api.depends("birthday")
    def _compute_age(self):
        for record in self:
            age = 0
            if record.birthday:
                age = relativedelta(
                    fields.Date.today(),
                    record.birthday,
                ).years
            record.age = age

    def _search_no_tag_id(self, operator, value):
        with_tags = self.search([("category_id", operator, value)])
        return [("id", "not in", with_tags.mapped("id"))]

    def _compute_search_no_category(self):
        """
        simply here to provide scaffolding for _search_no_tag_id
        """
        for rec in self:
            rec.search_no_category_id = False

    @api.multi
    @api.depends(
        "street",
        "street2",
        "zip",
        "city",
        "state_id",
        "country_id",
        "country_id.address_format",
        "country_id.code",
        "country_id.name",
        "state_id.code",
        "state_id.name",
    )
    def _compute_display_address(self):
        for rec in self:
            rec.display_address = self._display_address()

    @api.model
    def _get_default_address_format(self):
        return (
            "%(street)s\n%(street2)s\n%(city)s %(state_code)s %(zip)s\n%(country_name)s"
        )

    @api.model
    def _get_address_format(self):
        return self.country_id.address_format or self._get_default_address_format()

    @api.multi
    def _display_address(self):
        """
        The purpose of this function is to build and return an address formatted accordingly to the
        standards of the country where it belongs.

        :param address: browse record of the res.beneficiary to format
        :returns: the address formatted in a display that fit its country habits (or the default ones
            if not country is specified)
        :rtype: string
        """
        # get the information that will be injected into the display format
        # get the address format
        address_format = self._get_address_format()
        args = {
            "state_code": self.state_id.code or "",
            "state_name": self.state_id.name or "",
            "country_code": self.country_id.code or "",
            "country_name": self._get_country_name(),
        }
        for field in self._formatting_address_fields():
            args[field] = getattr(self, field) or ""
        return address_format % args

    def _display_address_depends(self):
        # field dependencies of method _display_address()
        return self._formatting_address_fields() + [
            "country_id.address_format",
            "country_id.code",
            "country_id.name",
            "state_id.code",
            "state_id.name",
        ]

    @api.model
    def _check_import_consistency(self, vals_list):
        """
        The values created by an import are generated by a name search, field by field.
        As a result there is no check that the field values are consistent with each others.
        We check that if the state is given a value, it does belong to the given country, or we remove it.
        """
        States = self.env["res.country.state"]
        states_ids = {vals["state_id"] for vals in vals_list if vals.get("state_id")}
        state_to_country = States.search([("id", "in", list(states_ids))]).read(
            ["country_id"]
        )
        for vals in vals_list:
            if vals.get("state_id"):
                country_id = next(
                    c["country_id"][0]
                    for c in state_to_country
                    if c["id"] == vals.get("state_id")
                )
                state = States.browse(vals["state_id"])
                if state.country_id.id != country_id:
                    state_domain = [
                        ("code", "=", state.code),
                        ("country_id", "=", country_id),
                    ]
                    state = States.search(state_domain, limit=1)
                    # replace state or remove it if not found
                    vals["state_id"] = state.id

    @api.multi
    def _get_country_name(self):
        return self.country_id.name or ""

    @api.multi
    def name_get(self):
        return [(record.id, record.name + " (" + record.ref + ")") for record in self]

    @api.model
    def get_import_templates(self):
        return [
            {
                "label": _("Import Template for Beneficiaries"),
                "template": "/openg2p/static/xls/openg2p_beneficiary.xls",
            }
        ]

    @api.multi
    @api.depends("identities", "identities.name", "identities.category_id.code.")
    def _compute_identification(self, field_name, category_code):
        """Compute a field that indicates a certain ID type.

        Use this on a field that represents a certain ID type. It will compute
        the desired field as that ID(s).

        This ID can be worked with as if it were a Char field, but it will
        be relating back to a ``openg2p.beneficiary.id_number`` instead.

        Example:

            .. code-block:: python

            social_security = fields.Char(
                compute=lambda s: s._compute_identification(
                    'social_security', 'SSN',
                ),
                inverse=lambda s: s._inverse_identification(
                    'social_security', 'SSN',
                ),
                search=lambda s, *a: s._search_identification(
                    'SSN', *a
                ),
            )

        Args:
            field_name (str): Name of field to set.
            category_code (str): Category code of the Identification type.
        """
        for record in self:
            identities = record.identities.filtered(
                lambda r: r.category_id.code == category_code
            )
            if not identities:
                continue
            value = identities[0].name
            record[field_name] = value

    @api.multi
    def _inverse_identification(self, field_name, category_code):
        """Inverse for an identification field.

        This method will create a new record, or modify the existing one
        in order to allow for the associated field to work like a Char.

        If a category does not exist of the correct code, it will be created
        using `category_code` as both the `name` and `code` values.

        If the value of the target field is unset, the associated ID will
        be deactivated in order to preserve history.

        Example:

            .. code-block:: python

            social_security = fields.Char(
                compute=lambda s: s._compute_identification(
                    'social_security', 'SSN',
                ),
                inverse=lambda s: s._inverse_identification(
                    'social_security', 'SSN',
                ),
                search=lambda s, *a: s._search_identification(
                    'SSN', *a
                ),
            )

        Args:
            field_name (str): Name of field to set.
            category_code (str): Category code of the Identification type.
        """
        for record in self:
            id_number = record.identities.filtered(
                lambda r: r.category_id.code == category_code
            )
            record_len = len(id_number)
            # Record for category is not existent.
            if record_len == 0:
                name = record[field_name]
                if not name:
                    # No value to set
                    continue
                category = self.env["openg2p.beneficiary.id_category"].search(
                    [
                        ("code", "=", category_code),
                    ]
                )
                if not category:
                    category = self.env["openg2p.beneficiary.id_category"].create(
                        {
                            "code": category_code,
                            "name": category_code,
                        }
                    )
                self.env["openg2p.beneficiary.id_number"].create(
                    {
                        "beneficiary_id": record.id,
                        "category_id": category.id,
                        "name": name,
                    }
                )
            # There was an identification record singleton found.
            elif record_len == 1:
                value = record[field_name]
                if value:
                    id_number.name = value
                else:
                    id_number.active = False
            # Guard against writing wrong records.
            else:
                raise ValidationError(
                    _(
                        "This %s has multiple IDs of this type (%s), so a write "
                        "via the %s field is not possible. In order to fix this, "
                        "please use the IDs tab.",
                    )
                    % (record._name, category_code, field_name)
                )

    @api.model
    def _search_identification(self, category_code, operator, value):
        """Search method for an identification field.

        Example:

            .. code-block:: python

            social_security = fields.Char(
                compute=lambda s: s._compute_identification(
                    'social_security', 'SSN',
                ),
                inverse=lambda s: s._inverse_identification(
                    'social_security', 'SSN',
                ),
                search=lambda s, *a: s._search_identification(
                    'SSN', *a
                ),
            )

        Args:
            category_code (str): Category code of the Identification type.
            operator (str): Operator of domain.
            value (str): Value to search for.

        Returns:
            list: Domain to search with.
        """
        identities = self.env["openg2p.beneficiary.id_number"].search(
            [
                ("name", operator, value),
                ("category_id.code", "=", category_code),
            ]
        )
        return [
            ("identities.id", "in", identities.ids),
        ]

    @api.model
    def _generate_ref(self):
        """Generate a random beneficiary identification number"""
        company = self.env.user.company_id

        for retry in range(50):
            ref = False
            if company.beneficiary_id_gen_method == "sequence":
                if not company.beneficiary_id_sequence:
                    _logger.warning(
                        "No sequence configured for beneficiary ID generation"
                    )
                    return ref
                ref = company.beneficiary_id_sequence.next_by_id()
            elif company.beneficiary_id_gen_method == "random":
                beneficiary_id_random_digits = company.beneficiary_id_random_digits
                rnd = random.SystemRandom()
                ref = "".join(
                    rnd.choice(string.digits)
                    for x in range(beneficiary_id_random_digits)
                )

            if self.search_count([("ref", "=", ref)]):
                continue

            return ref

        raise UserError(
            _("Unable to generate unique Beneficiary ID in %d steps.") % (retry,)
        )

    def get_identities(self):
        self.ensure_one()
        return [(i.category_id.code, i.name) for i in self.identities]

    @api.model
    def matches(
        self, query, mode=MATCH_MODE_NORMAL, stop_on_first=False, threshold=None
    ):
        """
        Given an query find recordset that is strongly similar
        @TODO implement threshold
        """
        matches = self.env["openg2p.beneficiary"]
        work = WorkContext(
            model_name=self._name, collection=self.with_context(active_test=False)
        )
        matchers = [
            matcher
            for matcher in work.many_components(usage="beneficiary.matcher")
            if matcher.mode <= mode
        ]
        matchers.sort(key=lambda r: r.sequence)

        for matcher in matchers:
            res = matcher.match(query)
            if res:
                matches += res
                if stop_on_first:
                    break

        return matches if len(matches) else False

    def cron_deduplicate(self):
        """
        Identifies potential duplicates and send to investigation bin
        @TODO
        """
        pass

    @api.multi
    def merge(self, merges, copy_data={}):
        """
        @param merges - A recordset of beneficiaries we want to merge
        @param {dict} copy_data - data to be written to the record we are merging with. usually will come from UI and is
        data contained in the records we want to merge that is absent in self
        @TODO what do we do if contract is on a different timeline or category
        """
        self.ensure_one()
        merge_ids = []
        for m in merges:
            merge_ids.append((4, m.id))

        if merge_ids:
            data = copy.deepcopy(copy_data)
            data["merged_beneficiary_ids"] = merge_ids
            merges.toggle_active()
            self.write(data)
