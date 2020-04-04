"""Test client class."""

import pytest
from six.moves.urllib.parse import parse_qs  # noqa
from six.moves.urllib.parse import unquote  # noqa

from corenetworks import CoreNetworks
from corenetworks.exceptions import CorenetworksError
from corenetworks.tests.fixtures.callback import records_get_callback
from corenetworks.tests.fixtures.callback import records_post_callback


@pytest.fixture
def client(mocker):
    client = CoreNetworks(api_token="secure")

    return client


def test_records(requests_mock, client):
    requests_mock.get(
        "https://beta.api.core-networks.de/dnszones/example.com/records/",
        text=records_get_callback
    )

    exp = [{
        "type": "A",
        "ttl": 1800,
        "name": "test",
        "data": "127.0.0.1"
    }, {
        "type": "AAAA",
        "ttl": 1800,
        "name": "test",
        "data": "::1"
    }]

    resp = client.records(zone="example.com")

    assert resp == exp


def test_no_records(requests_mock, client):

    requests_mock.get(
        "https://beta.api.core-networks.de/dnszones/missing.com/records/",
        text=records_get_callback,
    )

    with pytest.raises(CorenetworksError) as e:
        assert client.records(zone="missing.com")
    assert str(e.value) == "Invalid response: 404 None"


def test_filter_records(requests_mock, client):
    requests_mock.get(
        "https://beta.api.core-networks.de/dnszones/example.com/records/",
        text=records_get_callback,
    )

    resp = client.records(zone="example.com", params={"type": ["A"]})
    assert resp == [{"type": "A", "ttl": 1800, "name": "test", "data": "127.0.0.1"}]


def test_add_record(requests_mock, client):
    requests_mock.post(
        "https://beta.api.core-networks.de/dnszones/example.com/records/",
        text=records_post_callback,
    )
    requests_mock.get(
        "https://beta.api.core-networks.de/dnszones/example.com/records/",
        text=records_get_callback,
    )

    resp = client.add_record(
        zone="example.com", params={
            "type": "A",
            "ttl": 1800,
            "name": "test",
            "data": "127.0.0.1"
        }
    )
    assert resp == [{"type": "A", "ttl": 1800, "name": "test", "data": "127.0.0.1"}]
