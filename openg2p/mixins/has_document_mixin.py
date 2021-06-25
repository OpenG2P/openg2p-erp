# -*- coding: utf-8 -*-
# Copyright 2020 OpenG2P (https://openg2p.org)
# @author: Salton Massally <saltonmassally@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api


class Openg2pMixinHasDocument(models.AbstractModel):
    _name = "openg2p.mixin.has_document"
    _description = "OpenG2P Mixin: Has Document"

    document_ids = fields.One2many(
        "ir.attachment",
        compute="_compute_document_ids",
        string="Documents",
    )
    documents_count = fields.Integer(
        compute="_compute_document_ids",
        string="Document Count",
    )

    def _compute_document_ids(self):
        attachments = self.env["ir.attachment"].search(
            [
                ("res_model", "=", self._name),
                ("res_id", "in", self.ids),
            ]
        )

        result = dict.fromkeys(self.ids, self.env["ir.attachment"])
        for attachment in attachments:
            result[attachment.res_id] |= attachment

        for rec in self:
            rec.document_ids = result[rec.id]
            rec.documents_count = len(rec.document_ids)

    @api.multi
    def action_get_attachment_tree_view(self):
        action = self.env.ref("base.action_attachment").read()[0]
        action["context"] = {
            "default_res_model": self._name,
            "default_res_id": self.ids[0],
        }
        action["domain"] = str(
            [
                ("res_model", "=", self._name),
                ("res_id", "in", self.ids),
            ]
        )
        action["search_view_id"] = (self.env.ref("base.view_attachment_search").id,)
        return action
