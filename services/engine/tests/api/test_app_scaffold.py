"""Wave 0 API scaffold smoke."""

from __future__ import annotations

from level2_mathmodel.api.app import create_app


def test_create_app_scaffold() -> None:
    app = create_app()
    assert app["service"] == "level2-mathmodel"
    assert app["mode"] == "scaffold"
