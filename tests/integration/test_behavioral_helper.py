"""Unit tests for the OpenCode behavioral client contract."""

from __future__ import annotations

import inspect
import json

import pytest

import behavioral_helper
from behavioral_helper import OpenCodeClient


pytestmark = pytest.mark.unit


class FakeResponse:
    """Context manager response double for standard-library HTTP calls."""

    status = 200

    def __enter__(self) -> FakeResponse:
        return self

    def __exit__(self, *args: object) -> bool:
        return False

    def read(self) -> bytes:
        return json.dumps({"parts": []}).encode("utf-8")


def test_requests_allow_time_for_bonsai_wake_up(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    timeouts: list[float] = []

    def fake_urlopen(request: object, *, timeout: float) -> FakeResponse:
        timeouts.append(timeout)
        return FakeResponse()

    monkeypatch.setattr(behavioral_helper, "urlopen", fake_urlopen)

    OpenCodeClient().get("/")

    assert timeouts == [120]


def test_send_message_does_not_expose_model_selection() -> None:
    parameters = inspect.signature(OpenCodeClient.send_message).parameters

    assert "model" not in parameters
