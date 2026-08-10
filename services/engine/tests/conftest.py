"""Shared pytest fixtures for engine tests."""

from __future__ import annotations

from pathlib import Path

import pytest

# services/engine/tests -> repo root is parents[3]
REPO_ROOT = Path(__file__).resolve().parents[3]
CONTRACTS_LEVEL2 = REPO_ROOT / "contracts" / "level2"
FIXTURES = CONTRACTS_LEVEL2 / "fixtures"


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return REPO_ROOT


@pytest.fixture(scope="session")
def level2_openapi_path() -> Path:
    return CONTRACTS_LEVEL2 / "openapi.yaml"


@pytest.fixture(scope="session")
def level2_fixtures_dir() -> Path:
    return FIXTURES
