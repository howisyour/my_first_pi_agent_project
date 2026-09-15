"""Minimal request dispatcher. Routes are looked up in taskapp.registry.ROUTE_REGISTRY."""

from __future__ import annotations

import importlib
from dataclasses import dataclass, field
from typing import Any

from taskapp import schemas
from taskapp.constants import HTTP_INTERNAL_ERROR, HTTP_NOT_FOUND
from taskapp.errors import AppError
from taskapp.registry import ROUTE_REGISTRY, Route


@dataclass
class Request:
    method: str
    path: str
    body: dict[str, Any] = field(default_factory=dict)
    query: dict[str, str] = field(default_factory=dict)


@dataclass
class Response:
    status: int
    body: Any


def _match(pattern: str, path: str) -> dict[str, str] | None:
    pattern_parts = pattern.strip("/").split("/")
    path_parts = path.strip("/").split("/")
    if len(pattern_parts) != len(path_parts):
        return None
    params: dict[str, str] = {}
    for expected, actual in zip(pattern_parts, path_parts, strict=True):
        if expected.startswith("{") and expected.endswith("}"):
            params[expected[1:-1]] = actual
        elif expected != actual:
            return None
    return params


def _resolve_handler(route: Route):
    module_name, func_name = route.handler.split(":")
    return getattr(importlib.import_module(module_name), func_name)


def _error(status: int, code: str, message: str) -> Response:
    return Response(status, {"error": {"code": code, "message": message}})


def dispatch(store, request: Request) -> Response:
    for route in ROUTE_REGISTRY:
        if route.method != request.method:
            continue
        params = _match(route.path, request.path)
        if params is None:
            continue
        if route.schema not in schemas.__all__:
            return _error(HTTP_INTERNAL_ERROR, "SCHEMA_NOT_EXPORTED", route.schema)
        schema = getattr(schemas, route.schema)
        handler = _resolve_handler(route)
        try:
            status, payload = handler(store, request, **params)
        except AppError as exc:
            return _error(exc.status, exc.code, str(exc))
        except Exception as exc:
            return _error(HTTP_INTERNAL_ERROR, "INTERNAL_ERROR", type(exc).__name__)
        return Response(status, schema.render(payload))
    return _error(HTTP_NOT_FOUND, "ROUTE_NOT_FOUND", f"{request.method} {request.path}")


class Client:
    """In-process client used by tests."""

    def __init__(self, store) -> None:
        self.store = store

    def request(self, method: str, path: str, body=None, query=None) -> Response:
        return dispatch(self.store, Request(method, path, body or {}, query or {}))

    def get(self, path: str, query=None) -> Response:
        return self.request("GET", path, query=query)

    def post(self, path: str, body=None) -> Response:
        return self.request("POST", path, body=body)

    def patch(self, path: str, body=None) -> Response:
        return self.request("PATCH", path, body=body)
