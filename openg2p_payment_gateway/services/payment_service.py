# -*- coding: utf-8 -*-

import logging

from odoo import _
from odoo.addons.component.core import AbstractComponent
from odoo.exceptions import UserError
from odoo.osv import expression

_logger = logging.getLogger(__name__)

try:
    from cerberus import Validator
except ImportError:
    _logger.debug("Can not import cerberus")


class PaymentService(AbstractComponent):
    _name = "payment.service"
    _description = "Payment Service"
    _collection = "openg2p.gateway.transaction"
    _usage = "gateway.provider"
    _allowed_execute_method = None
    _sync_call = True
    _webhook_method = []

    @property
    def _provider_name(self):
        return self._name.replace("payment.service.", "")

    def _get_schema_for_method(self, method_name):
        validator_method = "_validator_%s" % method_name
        if not hasattr(self, validator_method):
            raise NotImplementedError(validator_method)
        return getattr(self, validator_method)()

    def _validate_and_sanitize(self, method, params):
        """
        This internal method is used to validate and sanitize the parameters
        expected by the given method.  These parameters are validated and
        sanitized according to a schema provided by a method  following the
        naming convention: '_validator_{method_name}'.
        :param method:
        :param params:
        :return:
        """
        method_name = method.__name__
        schema = self._get_schema_for_method(method_name)
        v = Validator(schema, purge_unknown=True)
        if v.validate(params):
            return v.document
        _logger.error("BadRequest %s", v.errors)
        raise UserError(_("Invalid Form"))

    def dispatch(self, method_name, params):
        if method_name not in self._webhook_method:
            raise UserError(_("Method not allowed for service %s"), self._name)

        func = getattr(self, method_name, None)
        if not func:
            raise UserError(
                _("Method %s not found in service %s"), method_name, self._name
            )
        return func(**self._validate_and_sanitize(func, params))

    def _get_account(self):
        gateway = self.collection
        domain = []
        provider_account = gateway.bank_id.provider_account
        if provider_account:
            domain = expression.AND([domain, [("id", "=", provider_account.id)]])
        keychain = self.env["keychain.account"]
        namespace = (self._name).replace("payment.service.", "")
        domain = expression.AND([domain, [("namespace", "=", namespace)]])
        return keychain.sudo().retrieve(domain)[0]

    def get_state(self):
        """
        Note we access transaction via self.collection
        """
        raise NotImplemented

    def execute(self):
        """
        Note we access transaction via self.collection
        """
        raise NotImplemented
