# -*- coding: utf-8 -*-
"""Custom authenticators."""

import json

from requests import ConnectionError
from requests import HTTPError
from requests import Request
from requests import Session
from requests.auth import AuthBase

from .exceptions import AuthError


class CoreNetworksBasicAuth(AuthBase):
    """Define login based auth."""

    def __init__(self, user, password, endpoint):
        self.user = user
        self.password = password
        self.endpoint = endpoint
        self.token = self._login()

    def __eq__(self, other):  # noqa
        return all([
            self.user == getattr(other, "user", None),
            self.password == getattr(other, "password", None),
        ])

    def __ne__(self, other):  # noqa
        return not self == other

    def __call__(self, r):  # noqa
        r.headers["Authorization"] = "Bearer {0!s}".format(self.token)
        return r

    def _login(self):
        data = {}
        data["login"] = self.user
        data["password"] = self.password

        json_data = json.dumps(data)
        url = "{endpoint}/auth/token".format(endpoint=self.endpoint)

        request = Request(method="POST", url=url, data=json_data)
        prepared_request = request.prepare()

        try:
            session = Session()
            handle = session.send(prepared_request)
            handle.raise_for_status()
        except HTTPError as e:
            raise AuthError(
                "Login failed: {code} {reason}".format(
                    code=e.response.status_code, reason=e.response.reason
                ),
                payload=e
            )
        except ConnectionError:
            raise

        response = handle.json()

        return response["token"]


class CoreNetworksTokenAuth(AuthBase):
    """Define token based auth."""

    def __init__(self, token):
        self.token = token

    def __eq__(self, other):  # noqa
        return all([
            self.token == getattr(other, "api_token", None),
        ])

    def __ne__(self, other):  # noqa
        return not self == other

    def __call__(self, r):  # noqa
        r.headers["Authorization"] = "Bearer {0!s}".format(self.token)
        return r
