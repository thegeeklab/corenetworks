"""Test authenticator classes."""

from corenetworks.authenticators import CoreNetworksBasicAuth
from corenetworks.authenticators import CoreNetworksTokenAuth


def test_basic_auth(requests_mock):
    requests_mock.post(
        "https://beta.api.core-networks.de/auth/token",
        json={"token": "mytoken"},
    )

    auth = CoreNetworksBasicAuth(
        user="test", password="test", endpoint="https://beta.api.core-networks.de"
    )

    assert auth.token == "mytoken"


def test_token_auth(requests_mock):
    auth = CoreNetworksTokenAuth(token="mytoken")

    assert auth.token == "mytoken"
