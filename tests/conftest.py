import os

import pytest


@pytest.fixture(autouse=True)
def use_memory_store():
    """
    Ensure that the MemoryStore is used by default by the application in unit
    tests.
    """
    os.environ["STORE_BACKEND"] = "memory"
