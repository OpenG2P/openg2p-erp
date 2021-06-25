# -*- coding: utf-8 -*-

from odoo import _, exceptions

from requests.auth import AuthBase
import requests
import json
import logging

_logger = logging.getLogger(__name__)

# Retry mechanism that needs to be decided
_MAX_NUMBER_REQUEST = 30

# _BASE_URL = 'https://odk.tekkie.codes/'

_ODK_TYPE_URL = {
    "auth": {
        "session": "v1/sessions",
    },
    "submission": {
        "odata": "v1/projects/%s/forms/%s.svc/Submissions",
    },
}

_CODE_401 = 401
_CODE_403 = 403
_CODE_422 = 422
_CODE_200 = 200
_CODE_201 = 201


class ODK(object):
    def __init__(
        self, base_url, operation_type, user, password, max_try=_MAX_NUMBER_REQUEST
    ):
        super(ODK, self).__init__()
        self.base_url = base_url
        self.user = user
        self.operation_type = operation_type
        self.max_try = max_try
        self.auth = HTTPTokenAuth(base_url, user, password)

    # Build URL for the API call.
    # TODO: Add support for updating without calling stored data
    def _build_url(self, arguments, url_type="odata"):
        arguments = arguments and arguments or {}
        url = _ODK_TYPE_URL[self.operation_type][url_type]
        if self.operation_type not in _ODK_TYPE_URL.keys():
            raise exceptions.Warning(
                _("'%s' is not implemented.") % self.operation_type
            )
        complete_url = self.base_url + url % tuple(arguments)
        return complete_url

    # Caller function for GET method
    def get(self, arguments, params, url_type="odata"):
        url = self._build_url(arguments, url_type)
        return self.call_api(url, params, "get")

    # Function to make API calls
    def call_api(self, url, query_params, call_type, data=False):
        _logger.info("Calling %s" % url)
        query_params = query_params and query_params or {}

        for i in range(self.max_try):
            try:
                if call_type == "get":
                    response = requests.get(url, params=query_params, auth=self.auth)
                    break
                elif call_type == "post":
                    json_data = json.dumps(data)
                    response = requests.post(
                        url, params=query_params, auth=self.auth, json=json_data
                    )
                    break
            except Exception as err:
                _logger.warning(
                    "URL Call Error. %d/%d. URL: %s",
                    i,
                    self.max_try,
                    err.__str__(),
                )
        else:
            raise exceptions.Warning(_("Maximum attempts reached."))

        if response.status_code == _CODE_401:
            raise exceptions.Warning(
                _("401 - Unable to authenticate to ODK with the user '%s'.\n")
                % self.user
            )
        elif response.status_code not in [_CODE_200, _CODE_201]:
            raise exceptions.Warning(
                _(
                    "The call to '%s' failed:\n"
                    "- Status Code: %d\n"
                    "- Reason: %s\n"
                    "- Body: %s"
                )
                % (response.url, response.status_code, response.reason, response.text)
            )
        return response.json()


# Class to handle authentication
class HTTPTokenAuth(AuthBase):

    auth_header_format = "Bearer {}"

    def __init__(self, base_url, user, password):
        auth_data = {"email": user, "password": password}
        url = base_url + _ODK_TYPE_URL["auth"]["session"]
        response_data = self.auth_call(url, auth_data)
        self.token = response_data["token"]

    def __call__(self, request):
        request.headers["Authorization"] = self.auth_header_format.format(self.token)
        return request

    # Call ODK API and get token for user
    def auth_call(self, url, data):
        try:
            response = requests.post(url, json=data)
        except Exception as err:
            raise exceptions.Warning(_("Error in calling Auth URL: '%s'.\n") % url)

        if response.status_code == _CODE_401:
            raise exceptions.Warning(
                _("401 - Unable to authenticate to ODK with the user '%s'.\n")
                % self.user
            )
        elif response.status_code not in [_CODE_200, _CODE_201]:
            raise exceptions.Warning(
                _(
                    "The call to '%s' failed:\n"
                    "- Status Code: %d\n"
                    "- Reason: %s\n"
                    "- Body: %s"
                )
                % (response.url, response.status_code, response.reason, response.text)
            )
        return response.json()
