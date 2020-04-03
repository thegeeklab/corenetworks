"""Test client class."""

import pytest

from corenetworks import CoreNetworks
from corenetworks.exceptions import CorenetworksError


@pytest.fixture
def client(mocker):
    client = CoreNetworks(api_token="secure")

    return client


def test_records(requests_mock, client):
    requests_mock.get(
        "https://beta.api.core-networks.de/dnszones/example.com/records/",
        text='[{"test": "test"}]'
    )

    resp = client.records(zone="example.com")
    assert resp == [{"test": "test"}]


def test_no_records(requests_mock, client):

    def failure_callback(request, context):
        context.status_code = 404
        return "[]"

    requests_mock.get(
        "https://beta.api.core-networks.de/dnszones/missing.com/records/",
        text=failure_callback,
    )

    with pytest.raises(CorenetworksError) as e:
        assert client.records(zone="missing.com")
    assert str(e.value) == "Invalid response: 404 None"
