# -*- coding: utf-8 -*-
"""API  client."""

import copy
import json
import os
from collections import defaultdict

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

    def __init__(self, user=None, password=None, api_token=None, auto_commit=None):
        self.__endpoint = "https://beta.api.core-networks.de"
        self.__user_agent = "Core Networks Python API {version}".format(
            version=corenetworks.__version__
        )
        self.config = self._config(user, password, api_token, auto_commit)

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

        self._filter_schema = {
            "type": "object",
            "properties": {
                "name": {
                    "anyOf": [{
                        "type": "string",
                    }, {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                    }],
                },
                "ttl": {
                    "anyOf": [{
                        "type": "number",
                    }, {
                        "type": "array",
                        "items": {
                            "type": "number"
                        },
                    }],
                },
                "type": {
                    "anyOf": [{
                        "type": "string",
                    }, {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                    }],
                },
                "data": {
                    "anyOf": [{
                        "type": "string",
                    }, {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                    }],
                },
            },
        }

        if self.config["api_token"]:
            self._auth = CoreNetworksTokenAuth(api_token)
        else:
            self._auth = CoreNetworksBasicAuth(user, password, self.__endpoint)

    @staticmethod
    def _config(user, password, api_token, auto_commit):
        cfg = defaultdict(
            dict, {
                "user": None,
                "password": None,
                "api_token": None,
                "auto_commit": False
            }
        )

        cfg["user"] = os.getenv("CN_API_USER")
        cfg["password"] = os.getenv("CN_API_PASSWORD")
        cfg["api_token"] = os.getenv("CN_API_TOKEN")

        cfg["user"] = user or cfg["user"]
        cfg["password"] = password or cfg["password"]
        cfg["api_token"] = api_token or cfg["api_token"]
        cfg["auto_commit"] = auto_commit or cfg["auto_commit"]

        if not (cfg["user"] and cfg["password"]) and not cfg["api_token"]:
            raise AuthError("Insufficient authentication details provided")

        return cfg

    # ZONES

    def zones(self):
        """
        Get the list of DNS zones.

        Returns:
            list: List of zones.

        """
        result = self.__rest_helper("/dnszones/", method="GET")

        return self.__normalize(result)

    def zone(self, zone):
        """
        Get details about a DNS zone.

        Args:
            zone (str): Name of the target DNS zone.

        Returns:
            list: List of zones.

        """
        result = self.__rest_helper("/dnszones/{zone}".format(zone=zone), method="GET")

        return self.__normalize(result)

    # RECORDS

    def records(self, zone, params={}):
        """
        Get the list of records for the specific domain.

        Args:
            zone (str): Name of the target DNS zone.
            params (dict): Dictionary of filter parameters.
                See https://beta.api.core-networks.de/doc/#functon_dnszones_records
                but keep in mind that you have to pass a dict not a string. The required
                filter string will be created automatically.

                Example: `params={"type": ["NS", "SOA"]}` will result in
                `filter=?type[]=NS&type[]=SOA`

        Returns:
            list: List of matching records.

        """
        schema = copy.deepcopy(self._filter_schema)
        self.__validate(params, schema)

        filter_string = self.__json_to_filter(params)
        result = self.__rest_helper(
            "/dnszones/{zone}/records/{filter}".format(zone=zone, filter=filter_string),
            method="GET"
        )

        return self.__normalize(result)

    def add_record(self, zone, params):
        """
        Create a record for the given domain.

        Args:
            zone (str): Name of the target DNS zone.
            params (dict): Dictionary of record parameters.
                See https://beta.api.core-networks.de/doc/#functon_dnszones_records_add

        Returns:
            list: List of added records.

        """
        schema = copy.deepcopy(self._schema)
        schema["required"] = ["name", "type", "data"]
        self.__validate(params, schema)

        self.__rest_helper(
            "/dnszones/{zone}/records/".format(zone=zone), data=params, method="POST"
        )

        result = self.records(zone=zone, params=params)

        if self.config["auto_commit"]:
            self.commit(zone=zone)

        return self.__normalize(result)

    def delete_record(self, zone, params):
        """
        Delete all DNS records of a zone that match the data.

        Args:
            zone (str): Name of the target DNS zone.
            params (dict): Dictionary of record parameters.
                See https://beta.api.core-networks.de/doc/#functon_dnszones_records_add

        Returns:
            list: Empty list.

        """
        schema = copy.deepcopy(self._schema)
        schema["properties"]["force_all"] = {"type": "boolean"}
        schema["anyOf"] = [{
            "required": ["name"]
        }, {
            "required": ["type"]
        }, {
            "required": ["data"]
        }, {
            "required": ["force_all"]
        }]
        self.__validate(params, schema)

        if params.get("force_all"):
            params = {}

        result = self.__rest_helper(
            "/dnszones/{zone}/records/delete".format(zone=zone), data=params, method="POST"
        )

        if self.config["auto_commit"]:
            self.commit(zone=zone)

        return self.__normalize(result)

    def commit(self, zone):
        """
        Commit changed records to the given DNS zone.

        Args:
            zone (str): Name of the target DNS zone.

        Returns:
            list: Empty list.

        """
        result = self.__rest_helper(
            "/dnszones/{zone}/records/commit".format(zone=zone), method="POST"
        )

        return self.__normalize(result)

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
        except HTTPError as e:
            raise CorenetworksError(
                "Invalid response: {code} {reason}".format(
                    code=e.response.status_code, reason=e.response.reason
                ),
                payload=e
            )
        except ConnectionError:
            raise

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
            return [result]
        else:
            raise CorenetworksError("Unknown type: {}".format(type(result)))

    @staticmethod
    def __json_to_filter(data):
        filter_list = []

        for (key, value) in iteritems(data):
            if isinstance(value, list):
                for item in value:
                    filter_list.append("{key}[]={value}".format(key=key, value=item))
            elif isinstance(value, str) or isinstance(value, int):
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
