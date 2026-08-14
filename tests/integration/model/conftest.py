"""Pytest fixtures for the local Bonsai model server."""

from __future__ import annotations

from collections.abc import Iterator

import pytest

from bonsai_server import BonsaiServer, BonsaiServerError


@pytest.fixture(scope="session")
def bonsai_server() -> Iterator[BonsaiServer]:
    """Start or reuse Bonsai once and keep it alive after the suite."""

    server = BonsaiServer()
    try:
        server.ensure_up()
    except BonsaiServerError as error:
        pytest.fail(
            f"{error}\n"
            "Instale o llama-server, confirme que ele esta no PATH e execute "
            "novamente:\n"
            "  python3 tests/integration/model/bonsai_server.py --up",
            pytrace=False,
        )

    yield server
