"""Wave 0: pinned Level2 OpenAPI + fixtures exist and load."""

from __future__ import annotations

import json
from pathlib import Path

import yaml


def test_pinned_level2_openapi_exists_and_loads(level2_openapi_path: Path) -> None:
    assert level2_openapi_path.is_file(), f"missing pinned OpenAPI: {level2_openapi_path}"
    text = level2_openapi_path.read_text(encoding="utf-8")
    assert "openapi:" in text
    doc = yaml.safe_load(text)
    assert doc["openapi"].startswith("3.")
    assert doc["info"]["version"] == "1.4.0"
    assert "paths" in doc
    assert "/healthz" in doc["paths"]
    assert "/api/v1/integration/tag-catalog" in doc["paths"]
    assert "TagCatalog" in doc["components"]["schemas"]


def test_level2_version_note_mentions_pin() -> None:
    version_path = Path(__file__).resolve().parents[3] / "contracts" / "level2" / "VERSION"
    assert version_path.is_file()
    body = version_path.read_text(encoding="utf-8")
    assert "1.4.0" in body


def test_fixture_tags_list_loads(level2_fixtures_dir: Path) -> None:
    path = level2_fixtures_dir / "tags_list.json"
    assert path.is_file()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(data, list)
    assert len(data) >= 1
    assert "tag" in data[0]
    assert data[0]["tag"]["id"]


def test_fixture_tag_catalog_loads(level2_fixtures_dir: Path) -> None:
    path = level2_fixtures_dir / "tag_catalog.json"
    assert path.is_file()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["level2_api_version"] == "1.4.0"
    assert isinstance(data["devices"], list)
    assert isinstance(data["tags"], list)
    assert data["tags"][0]["tag_id"]
    assert data["tags"][0]["device_id"]


def test_mathmodel_openapi_draft_exists(repo_root: Path) -> None:
    path = repo_root / "contracts" / "mathmodel" / "openapi.yaml"
    assert path.is_file()
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert "/api/v1/local-vars" in doc["paths"]
    assert "/api/v1/plan" in doc["paths"]
