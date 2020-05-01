# -*- coding: utf-8 -*-
from odoo import _, api, SUPERUSER_ID
from odoo.exceptions import UserError


def post_init(cr, registry):
    _post_init_hook_add_trgm_indexes(cr, registry)


def _post_init_hook_add_trgm_indexes(cr, registry):
    with cr.savepoint():
        env = api.Environment(cr, SUPERUSER_ID, {})
        trgm_mod = env['trgm.index']

        if trgm_mod._trgm_extension_exists() != 'installed':
            raise UserError(_(
                'TRGM extension has not been installed on your database. '
                'Follow the config instructions from base_search_fuzzy before '
                'installing this module.'
            ))

        if not trgm_mod.index_exists('openg2p.applicant', 'firstname'):
            field_name = env.ref('openg2p_enrollment.field_openg2p_applicant__firstname')
            trgm_mod.create({
                'field_id': field_name.id,
                'index_name': 'openg2p_applicant_firstname',
                'index_type': 'gin',
            })

        if not trgm_mod.index_exists('openg2p.applicant', 'lastname'):
            field_name = env.ref('openg2p_enrollment.field_openg2p_applicant__lastname')
            trgm_mod.create({
                'field_id': field_name.id,
                'index_name': 'openg2p_applicant_lastname',
                'index_type': 'gin',
            })
