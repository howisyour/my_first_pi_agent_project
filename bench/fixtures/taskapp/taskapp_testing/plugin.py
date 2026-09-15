"""Pytest plugin with the fixtures contract tests need.

It is not auto-loaded. scripts/check.py enables it with `-p taskapp_testing.plugin`.
"""

import pytest

from taskapp.app import Client
from taskapp.storage.memory import InMemoryStore
from taskapp.storage.seed import seed_demo_data


@pytest.fixture
def store():
    return InMemoryStore()


@pytest.fixture
def seeded_store(store):
    seed_demo_data(store)
    return store


@pytest.fixture
def app_client(seeded_store):
    return Client(seeded_store)
