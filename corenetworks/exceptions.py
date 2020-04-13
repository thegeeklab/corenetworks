# -*- coding: utf-8 -*-
"""Custom package exceptions."""


class CoreNetworksException(Exception):
    """The main exception class."""

    def __init__(self, msg, payload=None):
        super(CoreNetworksException, self).__init__(msg)
        self.payload = payload


class CorenetworksError(CoreNetworksException):
    """Authentication errors exception class."""

    pass


class ValidationError(CoreNetworksException):
    """Authentication errors exception class."""

    pass


class AuthError(CoreNetworksException):
    """Authentication errors exception class."""

    pass
