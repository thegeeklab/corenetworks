# -*- coding: utf-8 -*-
"""API  client."""

import copy
import json

import jsonschema
from requests import ConnectionError
from requests import HTTPError
from requests import Request
from requests import Session
from six import iteritems

import corenetworks

from .authenticators import CoreNetworksBasicAuth
from .authenticators import CoreNetworksTokenAuth
from .exceptions import AuthError
from .exceptions import CorenetworksError
from .exceptions import ValidationError


class CoreNetworks():
    """Create authenticated API client."""

    def __init__(self, user=None, password=None, api_token=None):
        self.__endpoint = "https://beta.api.core-networks.de"
        self.__user_agent = "Core Networks Python API {version}".format(
            version=corenetworks.__version__
        )

        self._schema = {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string"
                },
                "ttl": {
                    "type": "number"
                },
                "type": {
                    "type": "string"
                },
                "data": {
                    "type": "string"
                },
            },
        }

        if api_token:
            self._auth = CoreNetworksTokenAuth(api_token)
        else:
            if not user or not password:
                raise AuthError("Insufficient authentication details provided")

            self._auth = CoreNetworksBasicAuth(user, password, self.__endpoint)

    # RECORDS

    def records(self, zone, data={}):
        """
        Get the list of records for the specific domain.

        Args:
            zone (str): Name of the target DNS zone.
            params (dict): Dictionary of filter parameters.
                See https://beta.api.core-networks.de/doc/#functon_dnszones_records
                but keep in mind that you have to pass a dict not a string. The required
                filter string will be created automatically.

                Example: params={"type": ["NS", "SOA"]} will result in filter=?type[]=NS&type[]=SOA

        Returns:
            list: List of entry dicts.

        """
        schema = copy.deepcopy(self._schema)
        self.__validate(data, schema)

        filter_string = self.__json_to_filter(data)
        result = self.__rest_helper(
            "/dnszones/{zone}/records/{filter}".format(zone=zone, filter=filter_string),
            method="GET"
        )

        return self.__normalize(result)

    def add_record(self, zone, data):
        """
        Create a record for the given domain.

        Args:
            param1: The first parameter.
            param2: The second parameter.

        Returns:
            True if successful, False otherwise.

        """
        schema = copy.deepcopy(self._schema)
        schema["required"] = ["name", "type", "data"]
        self.__validate(data, schema)

        result = self.__rest_helper(
            "/dnszones/{zone}/records/".format(zone=zone), data=data, method="POST"
        )

        return self.__normalize(result)

    def delete_record(self, zone, data):
        """
        Delete all DNS records of a zone that match the data.

        Args:

        """
        schema = copy.deepcopy(self._schema)
        schema["properties"]["force_all"] = {"type": "boolean"}
        schema["oneOf"] = [{
            "required": ["name"]
        }, {
            "required": ["type"]
        }, {
            "required": ["data"]
        }, {
            "required": ["force_all"]
        }]
        self.__validate(data, schema)

        if data.get("force_all"):
            data = {}

        print(data)

        # result = self.__rest_helper(
        #     "/dnszones/{zone}/records/delete/".format(zone=zone), data=data, method="POST"
        # )

        # return self.__normalize(result)

    def __rest_helper(self, url, data=None, params=None, method="GET"):
        """Handle requests to the Core Networks API."""
        url = self.__endpoint + url
        headers = {
            "User-Agent": self.__user_agent,
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        if data:
            json_data = json.dumps(data)
        else:
            json_data = None

        request = Request(
            method=method,
            url=url,
            headers=headers,
            data=json_data,
            params=params,
            auth=self._auth
        )

        prepared_request = request.prepare()

        r_json, r_headers = self.__request_helper(prepared_request)

        return r_json

    @staticmethod
    def __request_helper(request):
        """Handle firing off requests and exception raising."""
        try:
            session = Session()
            handle = session.send(request)

            handle.raise_for_status()
        except ConnectionError as e:
            raise CorenetworksError(
                "Server unreachable: {reason}".format(reason=e.message.reason), payload=e
            )
        except HTTPError as e:
            raise CorenetworksError(
                "Invalid response: {code} {reason}".format(
                    code=e.response.status_code, reason=e.response.reason
                ),
                payload=e
            )

        if handle.status_code == 200:
            response = handle.json()
        else:
            response = []

        return response, handle.headers

    @staticmethod
    def __normalize(result):
        if isinstance(result, list):
            return [el for el in result]
        elif isinstance(result, dict):
            return result
        else:
            raise CorenetworksError("Unknown type: {}".format(type(result)))

    @staticmethod
    def __json_to_filter(data):
        filter_list = []

        for (key, value) in iteritems(data):
            if isinstance(value, list):
                for item in value:
                    filter_list.append("{key}[]={value}".format(key=key, value=item))
            elif isinstance(value, str):
                filter_list.append("{key}={value}".format(key=key, value=value))
            else:
                raise CorenetworksError("Unknown type: {}".format(type(value)))

        filter_string = "&".join(filter_list)

        if filter_string:
            filter_string = "?{filter}".format(filter=filter_string)

        return filter_string

    @staticmethod
    def __validate(data, schema):
        try:
            jsonschema.validate(data, schema)
        except jsonschema.exceptions.ValidationError as e:
            raise ValidationError("Dataset invalid: {reason}".format(reason=e.message), payload=e)
