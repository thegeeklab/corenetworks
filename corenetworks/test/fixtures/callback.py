"""Requests mock callback functions."""

import json

from requests import ConnectionError
from six.moves.urllib.parse import parse_qs  # noqa
from six.moves.urllib.parse import unquote  # noqa


def records_get_callback(request, context):
    records = [{
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

    if "missing" in request.path:
        context.status_code = 404
        return "[]"

    if "dict" in request.path:
        return "{}"

    query_raw = parse_qs(request.query)
    if query_raw:
        query = dict((k.replace("[]", ""), v) for k, v in query_raw.items())

        res = [d for d in records if d["type"].lower() in query["type"]]
        return "{}".format(json.dumps(res))
    else:
        return "{}".format(json.dumps(records))


def records_post_callback(request, context):
    return "[]"


def records_error_callback(request, context):
    raise ConnectionError
