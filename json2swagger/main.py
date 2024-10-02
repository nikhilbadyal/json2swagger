"""Main func."""
from __future__ import annotations

import ast
import json
import os
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from loguru import logger

from json2swagger.utils import Documentation, JSONDict, Method

load_dotenv()


def get_servers() -> list[dict[str, str]]:
    """Return servers."""
    servers_string = os.getenv("SERVERS", "")
    if servers_string.startswith("[") and servers_string.endswith("]"):
        # Input is a string representation of a list
        servers = ast.literal_eval(servers_string)
    elif "," in servers_string:
        # Input is a comma-separated string
        servers = servers_string.split(",")
    else:
        # Handle other cases or raise an error
        msg = "Invalid input format"
        raise ValueError(msg)
    return [{"url": server, "description": "Server Description"} for server in servers]


def _add_description(endpoint) -> Documentation:
    """Add description to the schema."""
    logger.debug("Addig description")
    return {
        "summary": endpoint["name"],
        "description": endpoint["description"],
        "operationId": endpoint.get("docId", ""),
    }


def _add_resppnse() -> dict[str, Any]:
    """Add resppnse."""
    logger.debug("Adding response")
    return {}


def _add_requst_body() -> dict[str, Any]:
    """Add resppnse."""
    return {}


type_hits = {}


def _get_types(name: str, namespace: str):
    """Get Type for name and namespace."""
    for response_type in api_schema_types:
        if response_type["name"]["name"] == name and response_type["name"]["namespace"] == namespace:
            return response_type
    msg = "Cannot find type."
    raise ValueError(msg)


type_mapping = {
    "_builtins.boolean": "boolean",
    "_builtins.number": "number",
    "_builtins.string": "string",
    "_builtins.null": "null",
    "_builtins.undefined": "undefined",
    "_builtins.void": "void",
    "_builtins.binary": "binary",
    "_types.long": "number",
    "_types.integer": "number",
    "_types.Field": "string",
    "_types.SequenceNumber": "number",
    "_types.AggregateName": "string",
    "_types.SuggestionName": "string",
    "_types.ScrollId": "string",
    "_types.CategoryId": "string",
    "_types.Id": "string",
    "_types.NodeId": "string",
    "_types.IndexName": "string",
    "_types.IndexAlias": "string",
    "_types.IndexPattern": "string",
    "_types.Routing": "string",
    "_types.LongId": "string",
    "_types.IndexMetrics": "string",
    "_types.ClusterAlias": "string",
    "_types.Name": "string",
    "_types.Namespace": "string",
    "_types.Service": "string",
    "_types.NodeName": "string",
    "_types.DataStreamName": "string",
    "_types.Username": "string",
    "_types.Password": "string",
}
seen = []

def resolve_type(type_info):
    """Resolves type."""
    kind = type_info["kind"]
    if kind == "instance_of":
        print(f"Instance of {JSONDict(type_info)}")
        type_namespace = type_info["type"]["namespace"]
        type_name = type_info["type"]["name"]
        full_type_name = f"{type_namespace}.{type_name}"
        if full_type_name in seen and full_type_name not in type_mapping:
            return "self"
        seen.append(full_type_name)
        if full_type_name in type_mapping:
            return type_mapping[full_type_name]
        else:
            for item in api_schema_types:
                item_name = item["name"]
                item_namespace = item["name"]
                if item_name["name"] == type_name and item_namespace["namespace"] == type_namespace:
                    return resolve_type(item)
            return ValueError()
    elif kind == "union_of":
        params = []
        for kind in type_info["items"]:
            params.append(resolve_type(kind))
        return params
    elif kind == "type_alias":
        if "items" in type_info["type"]:
            for kind in type_info["type"]["items"]:
                return resolve_type(kind)
        return resolve_type(type_info["type"])
    elif kind == "array_of":
        return resolve_type(type_info["value"])
    elif kind == "enum":
        return "string"
    elif kind == "interface":
        params = []
        for param in type_info["properties"]:
            param_type_info = param["type"]
            if "type" in param_type_info:
                if (
                    param_type_info["type"]["name"] == type_info["name"]["name"]
                    and param_type_info["type"]["namespace"] == type_info["name"]["namespace"]
                ):
                    print("Found recursion")
                    continue
            result = resolve_type(param_type_info)
            params.append(result)

        return params
    elif kind == "dictionary_of":
        return "string"
    elif kind == "user_defined_value":
        return "string"
    raise ValueError(JSONDict(type_info))


def _get_request_path_params(type_name, type_namespace):
    """Get Request Path Params."""
    print(f"Finding type for {type_name} {type_namespace}")
    for item in api_schema_types:
        item_name = item["name"]
        item_namespace = item["name"]
        kind = item["kind"]
        if (
            item_name["name"] == type_name
            and item_namespace["namespace"] == type_namespace
            and kind.upper() == type_name.upper()
        ):
            paths = item["path"]
            response = []
            for path in paths:
                type_data = path["type"]
                path_param_type = resolve_type(type_data)
                dummy = {
                    "name": path["name"],
                    "in": "path",
                    "description": path["description"],
                    "required": path["required"],
                    "schema": {
                        "type": path_param_type,
                    },
                }
                response.append(dummy)
            return response
    raise ValueError


def _get_request_body(type_name, type_namespace):
    """Get Request Path Params."""
    print(f"Finding type for request body {type_name} {type_namespace}")
    for item in api_schema_types:
        item_name = item["name"]
        item_namespace = item["name"]
        kind = item["kind"]
        if (
            item_name["name"] == type_name
            and item_namespace["namespace"] == type_namespace
            and kind.upper() == type_name.upper()
        ):
            kind = item["body"]["kind"]
            if kind == "properties":
                print("Got properties.")
                body_params = item["body"]["properties"]
                response = {}
                for body in body_params:
                    print(f"Solving {body}")
                    print("XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX")
                    type_data = body["type"]
                    query_param_type = resolve_type(type_data)
                    dummy = {
                        body["name"]: {"type": query_param_type},
                    }

                    response.update(dummy)
                return response
            return []
    raise ValueError


def _get_request_query_params(type_name, type_namespace):
    """Get Request query Params."""
    print(f"Finding type for {type_name} {type_namespace}")
    for item in api_schema_types:
        item_name = item["name"]
        item_namespace = item["name"]
        kind = item["kind"]
        if (
            item_name["name"] == type_name
            and item_namespace["namespace"] == type_namespace
            and kind.upper() == type_name.upper()
        ):
            queries = item["query"]
            response = []
            for query in queries:
                type_data = query["type"]
                query_param_type = resolve_type(type_data)
                dummy = {
                    "name": query["name"],
                    "in": "query",
                    "description": query.get("description", "No Description"),
                    "required": query["required"],
                    "schema": {
                        "type": query_param_type,
                    },
                }
                response.append(dummy)
            return response
    raise ValueError


def _add_path_params(endpoint):
    """Added request params."""
    logger.debug("Adding path params.")
    if endpoint["request"]:
        name = endpoint["request"]["name"]
        namespace = endpoint["request"]["namespace"]
        logger.debug("Added path params.")
        return _get_request_path_params(name, namespace)
    logger.warning("Not request name.")
    return []


def _add_request_body(endpoint):
    """Added request body."""
    logger.debug("Adding request bodys.")
    if endpoint["request"]:
        name = endpoint["request"]["name"]
        namespace = endpoint["request"]["namespace"]
        response_body = _get_request_body(name, namespace)
        logger.debug("Added requesy body.")
        # for resp in response_body:
        return {
            "description": "Request body.",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": response_body,
                    },
                },
            },
        }
    logger.warning("Not request name.")
    return []


def _add_query_params(endpoint):
    """Added query request params."""
    logger.debug("Adding query params.")
    if endpoint["request"]:
        name = endpoint["request"]["name"]
        namespace = endpoint["request"]["namespace"]
        logger.debug("Added query params.")
        return _get_request_query_params(name, namespace)
    logger.warning("Not request name.")
    return []


def _add_methods(endpoint, method: str) -> dict[str, Method]:
    """Added methods."""
    logger.debug(f"Adding metadata for {method}")
    description = _add_description(endpoint)
    request_params = _add_path_params(endpoint) + _add_query_params(endpoint)
    request_body = _add_request_body(endpoint)
    method_data: Method = {
        "summary": description["summary"],
        "description": description["description"],
        "operationId": description["operationId"],
    }
    if request_params:
        method_data.update({"parameters": request_params})
    if request_body:
        method_data.update({"requestBody": request_body})
    method_data.update({"responses": {}})
    return {method.lower(): method_data}


def _add_paths(endpoint, url_obj) -> dict[str, Any]:
    """Added paths to sceham."""
    openapi_schema: dict[str, Any] = {}
    methods = url_obj["methods"]
    url = url_obj["path"]
    openapi_schema[url] = {}
    for method in methods:
        logger.debug(f"Adding {method} for path {url}.")
        method_info = _add_methods(endpoint, method)
        openapi_schema[url].update(method_info)
    return openapi_schema[url]


def add_api_to_openapi() -> None:
    """Extract relevant information from the API schema."""
    openapi_schema: dict[str, Any] = {
        "openapi": "3.1.0",
        "info": {
            "title": "Elastic API",
            "version": "1.0.0",
            "description": "Elastic APIs into in OPENAPI form",
        },
        "servers": get_servers(),
        "paths": {},
        "security": [
            {
                "BasicAuth": [],
            },
        ],
    }
    for endpoint in api_schema_data:
        try:
            try:
                if endpoint["visibility"] != "public":
                    continue
            except Exception:
                logger.error(JSONDict(endpoint))
                continue
            urls = endpoint["urls"]
            for url_obj in urls:
                logger.info(f"Starting for \n {JSONDict(url_obj)}")
                url = url_obj["path"]
                data = {"url": _add_paths(endpoint, url_obj)}
                openapi_schema["paths"][url] = data["url"]
                logger.info(f"Added for {url}")
        except Exception as e:
            logger.error(JSONDict(endpoint))
            with open("data.json", "w") as out_file:
                json.dump(openapi_schema, out_file, indent=4)
            logger.exception(e)
            sys.exit(1)
    with open("data.json", "w") as out_file:
        json.dump(openapi_schema, out_file, indent=4)


api_schema = "schema.json"
types = "types.json"
with Path(api_schema).open() as schema_file:
    schema_data = JSONDict(json.load(schema_file))
    api_schema_data = schema_data["endpoints"]
    with Path(types).open() as types_file:
        types_data = JSONDict(json.load(types_file))
        api_schema_types = types_data["types"]
    # add_api_to_openapi()
    data = {
            'kind': 'instance_of',
            'type': {
                'name': 'FieldCollapse',
                'namespace': '_global.search._types'
                }
            }
    resolve_type(data)

#
