# -*- coding: utf-8 -*-
from odoo import _, api, SUPERUSER_ID
from odoo.exceptions import UserError


def post_init(cr, registry):
    _post_init_hook_add_trgm_indexes(cr, registry)
    _post_init_hook_create_mass_editing_actions(cr, registry)


def _post_init_hook_add_trgm_indexes(cr, registry):
    with cr.savepoint():
        env = api.Environment(cr, SUPERUSER_ID, {})
        trgm_mod = env["trgm.index"]

        if trgm_mod._trgm_extension_exists() != "installed":
            raise UserError(
                _(
                    "TRGM extension has not been installed on your database. "
                    "Follow the config instructions from base_search_fuzzy before "
                    "installing this module."
                )
            )

        if not trgm_mod.index_exists("openg2p.beneficiary", "firstname"):
            field_name = env.ref("openg2p.field_openg2p_beneficiary__firstname")
            trgm_mod.create(
                {
                    "field_id": field_name.id,
                    "index_name": "openg2p_beneficiary_firstname",
                    "index_type": "gin",
                }
            )

        if not trgm_mod.index_exists("openg2p.beneficiary", "lastname"):
            field_name = env.ref("openg2p.field_openg2p_beneficiary__lastname")
            trgm_mod.create(
                {
                    "field_id": field_name.id,
                    "index_name": "openg2p_beneficiary_lastname",
                    "index_type": "gin",
                }
            )

        if not trgm_mod.index_exists("openg2p.beneficiary", "name"):
            field_name = env.ref("openg2p.field_openg2p_beneficiary__name")
            trgm_mod.create(
                {
                    "field_id": field_name.id,
                    "index_name": "openg2p_beneficiary_name",
                    "index_type": "gin",
                }
            )

        if not trgm_mod.index_exists("openg2p.beneficiary", "display_address"):
            field_name = env.ref("openg2p.field_openg2p_beneficiary__display_address")
            trgm_mod.create(
                {
                    "field_id": field_name.id,
                    "index_name": "openg2p_beneficiary_display_address",
                    "index_type": "gin",
                }
            )

        if not trgm_mod.index_exists("openg2p.location", "name"):
            field_name = env.ref("openg2p.field_openg2p_location__name")
            trgm_mod.create(
                {
                    "field_id": field_name.id,
                    "index_name": "openg2p_location_name",
                    "index_type": "gin",
                }
            )


def _post_init_hook_create_mass_editing_actions(cr, registry):
    with cr.savepoint():
        env = api.Environment(cr, SUPERUSER_ID, {})
        env.ref("openg2p.openg2p_mass_edit_beneficiary_tag").create_action()
        env.ref("openg2p.openg2p_mass_edit_beneficiary_location").create_action()
