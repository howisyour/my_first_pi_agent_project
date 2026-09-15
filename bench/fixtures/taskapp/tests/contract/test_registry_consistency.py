import importlib

from taskapp import schemas
from taskapp.registry import ROUTE_REGISTRY


def test_every_route_schema_is_exported():
    assert [route.schema for route in ROUTE_REGISTRY if route.schema not in schemas.__all__] == []


def test_every_route_handler_resolves():
    for route in ROUTE_REGISTRY:
        module_name, func_name = route.handler.split(":")
        assert hasattr(importlib.import_module(module_name), func_name), route.handler


def test_routes_are_unique():
    keys = [(route.method, route.path) for route in ROUTE_REGISTRY]
    assert len(keys) == len(set(keys))
