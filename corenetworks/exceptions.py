#!/usr/bin/env python
"""Custom package exceptions."""


class CoreNetworksException(Exception):
    """The main exception class."""

    def __init__(self, message, payload=None):
        self.message = message
        self.payload = payload

    def __str__(self):  # noqa
        return str(self.message)


class CorenetworksError(CoreNetworksException):
    """Authentication errors exception class."""

    pass


class ValidationError(CoreNetworksException):
    """Authentication errors exception class."""

    pass


class AuthError(CoreNetworksException):
    """Authentication errors exception class."""

    pass
