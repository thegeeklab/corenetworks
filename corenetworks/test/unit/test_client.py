"""Test client class."""

import pytest
import requests
from six.moves.urllib.parse import parse_qs  # noqa
from six.moves.urllib.parse import unquote  # noqa

from corenetworks import CoreNetworks
from corenetworks.authenticators import CoreNetworksBasicAuth
from corenetworks.exceptions import AuthError
from corenetworks.exceptions import CorenetworksError
from corenetworks.exceptions import ValidationError
from corenetworks.test.fixtures.callback import records_error_callback
from corenetworks.test.fixtures.callback import records_get_callback
from corenetworks.test.fixtures.callback import records_post_callback


@pytest.fixture
def client(mocker):
    mocker.patch.object(CoreNetworksBasicAuth, "_login", return_value="testtoken")
    client = CoreNetworks(user="testuser", password="testpass")

    return client


def test_auth_error(requests_mock):
    with pytest.raises(AuthError) as e:
        assert CoreNetworks(user="test")
    assert str(e.value) == "Insufficient authentication details provided"


def test_request_error(requests_mock, client):
    requests_mock.post(
        "https://beta.api.core-networks.de/dnszones/example.com/records/commit",
        text=records_error_callback,
    )

    with pytest.raises(requests.ConnectionError):
        assert client.commit(zone="example.com")


def test_zones(requests_mock, client):
    requests_mock.get(
        "https://beta.api.core-networks.de/dnszones/",
        text='[{"name":"example.com","type":"master"}]'
    )

    resp = client.zones()
    assert resp == [{"name": "example.com", "type": "master"}]


def test_zone(requests_mock, client):
    requests_mock.get(
        "https://beta.api.core-networks.de/dnszones/example.com",
        json={
            "active": True,
            "dnssec": True,
            "name": "example.com",
            "type": "master"
        }
    )

    resp = client.zone("example.com")
    assert resp == [{"active": True, "dnssec": True, "name": "example.com", "type": "master"}]


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
        "https://beta.api.core-networks.de/dnszones/missing/records/",
        text=records_get_callback,
    )

    with pytest.raises(CorenetworksError) as e:
        assert client.records(zone="missing")
    assert str(e.value) == "Invalid response: 404 None"


def test_type_records(requests_mock, client):

    requests_mock.get(
        "https://beta.api.core-networks.de/dnszones/dict/records/",
        text=records_get_callback,
    )

    dictresp = client.records(zone="dict")
    assert dictresp == [{}]


def test_filter_records(requests_mock, client):
    requests_mock.get(
        "https://beta.api.core-networks.de/dnszones/example.com/records/",
        text=records_get_callback,
    )

    resp = client.records(zone="example.com", params={"type": ["A"]})
    assert resp == [{"type": "A", "ttl": 1800, "name": "test", "data": "127.0.0.1"}]


def test_add_record(requests_mock, client, mocker):
    requests_mock.post(
        "https://beta.api.core-networks.de/dnszones/example.com/records/",
        text=records_post_callback,
    )
    requests_mock.get(
        "https://beta.api.core-networks.de/dnszones/example.com/records/",
        text=records_get_callback,
    )

    record = {"type": "A", "ttl": 1800, "name": "test", "data": "127.0.0.1"}

    resp = client.add_record(zone="example.com", params=record)
    assert resp == [{"type": "A", "ttl": 1800, "name": "test", "data": "127.0.0.1"}]

    mocker.patch.object(client, "commit")
    client.config["auto_commit"] = True
    client.add_record(zone="example.com", params=record)
    client.commit.assert_called_once_with(zone="example.com")


def test_delete_record(requests_mock, client, mocker):
    requests_mock.post(
        "https://beta.api.core-networks.de/dnszones/example.com/records/delete",
        text=records_post_callback,
    )

    filtered = client.delete_record(zone="example.com", params={
        "type": "A",
    })
    assert filtered == []

    forced = client.delete_record(zone="example.com", params={
        "force_all": True,
    })
    assert forced == []

    mocker.patch.object(client, "commit")
    client.config["auto_commit"] = True
    client.delete_record(zone="example.com", params={
        "type": "A",
    })
    client.commit.assert_called_once_with(zone="example.com")


def test_delete_record_invalid(requests_mock, client):
    requests_mock.post(
        "https://beta.api.core-networks.de/dnszones/example.com/records/delete",
        text=records_post_callback,
    )

    with pytest.raises(ValidationError) as wrong:
        assert client.delete_record(zone="example.com", params={"wrong": "attr"})
    assert str(wrong.value).startswith("Dataset invalid:")

    with pytest.raises(ValidationError) as ntype:
        assert client.delete_record(zone="example.com", params={"type": 1})
    assert str(ntype.value).startswith("Dataset invalid:")

    with pytest.raises(ValidationError) as empty:
        assert client.delete_record(zone="example.com", params={})
    assert str(empty.value).startswith("Dataset invalid:")


def test_commit(requests_mock, client):
    requests_mock.post(
        "https://beta.api.core-networks.de/dnszones/example.com/records/commit",
        text=records_post_callback,
    )

    resp = client.commit(zone="example.com")
    assert resp == []
