"""Helpers for the non-Docker OpenCode integration suites."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import pytest


@dataclass(frozen=True)
class OpenCodeResponse:
    """Response returned by the OpenCode HTTP API."""

    status_code: int
    text: str

    def json(self) -> Any:
        """Decode the response body as JSON."""

        try:
            return json.loads(self.text)
        except json.JSONDecodeError as error:
            pytest.fail(f"OpenCode returned invalid JSON: {error}")


@dataclass(frozen=True)
class CommandResult:
    """Small equivalent of the result exposed by BATS ``run``."""

    returncode: int
    stdout: str = ""
    stderr: str = ""
    status_code: int | None = None

    def json(self) -> Any:
        """Decode command output as JSON, matching the BATS ``jq`` assertion."""

        try:
            return json.loads(self.stdout)
        except json.JSONDecodeError as error:
            pytest.fail(f"OpenCode returned invalid JSON: {error}")


class OpenCodeClient:
    """Minimal standard-library client replacing the BATS behavioral helper."""

    def __init__(self) -> None:
        port = os.environ.get("OPENCODE_PORT", "4196")
        self.base_url = f"http://127.0.0.1:{port}"

    @property
    def service_error(self) -> str:
        """Return the actionable message used when OpenCode is unavailable."""

        return (
            f"OpenCode serve não está disponível em {self.base_url}. Execute: "
            "python3 tests/integration/docker/container_test_opencode.py --up"
        )

    def require_available(self) -> None:
        """Fail the test when the OpenCode service cannot answer its root URL."""

        response = self._request("GET", "/")
        if response.status_code >= 400:
            pytest.fail(self.service_error)

    @staticmethod
    def require_model() -> None:
        """Fail with the same instruction as the BATS helper when no model exists."""

        if not os.environ.get("OPENCODE_TEST_MODEL"):
            pytest.fail(
                "ERRO: OPENCODE_TEST_MODEL não definido. "
                "Defina o modelo antes de rodar testes."
            )

    def get(self, path: str) -> CommandResult:
        """Run a GET request and expose a BATS-like success result."""

        return self._command_result(self._request("GET", path))

    def get_status(self, path: str) -> CommandResult:
        """Run a GET request and return its HTTP status as command output."""

        response = self._request("GET", path)
        return CommandResult(
            returncode=0 if response.status_code < 400 else 1,
            stdout=str(response.status_code),
            status_code=response.status_code,
        )

    def create_session(self) -> CommandResult:
        """Create an OpenCode session and return its ID as command output."""

        response = self._request("POST", "/session", {})
        if response.status_code >= 400:
            return CommandResult(
                returncode=1,
                stderr="Não foi possível criar sessão OpenCode",
                status_code=response.status_code,
            )

        try:
            payload = json.loads(response.text)
        except json.JSONDecodeError as error:
            return CommandResult(returncode=1, stderr=str(error))

        session_id = payload.get("id") if isinstance(payload, dict) else None
        if session_id is None or session_id == "":
            return CommandResult(returncode=1, stderr="Resposta sem ID de sessão")
        return CommandResult(returncode=0, stdout=str(session_id), status_code=response.status_code)

    def send_message(
        self,
        session_id: str,
        text: str,
        model: str = "",
        agent: str = "",
    ) -> CommandResult:
        """Send a message and return concatenated text parts as command output."""

        payload: dict[str, Any] = {"parts": [{"type": "text", "text": text}]}
        if model:
            provider_id, separator, model_id = model.partition("/")
            payload["model"] = {
                "providerID": provider_id,
                "modelID": model_id if separator else provider_id,
            }
        if agent:
            payload["agent"] = agent

        response = self._request("POST", f"/session/{session_id}/message", payload)
        if response.status_code >= 400:
            return CommandResult(
                returncode=1,
                stderr=f"ERRO: curl falhou ao enviar mensagem para sessao {session_id}",
                status_code=response.status_code,
            )

        try:
            result = json.loads(response.text)
        except json.JSONDecodeError as error:
            return CommandResult(returncode=1, stderr=str(error))

        if isinstance(result, dict) and ("_tag" in result or "error" in result):
            return CommandResult(returncode=1, stderr=f"ERRO: {response.text}")

        parts = result.get("parts", []) if isinstance(result, dict) else []
        text_parts = [
            str(part["text"])
            for part in parts
            if isinstance(part, dict)
            and part.get("type") == "text"
            and part.get("text") is not None
        ]
        return CommandResult(
            returncode=0,
            stdout="".join(text_parts).replace("\n", ""),
            status_code=response.status_code,
        )

    def _request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
    ) -> OpenCodeResponse:
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        request = Request(
            f"{self.base_url}{path}",
            data=data,
            headers={"Content-Type": "application/json"} if data is not None else {},
            method=method,
        )
        try:
            with urlopen(request, timeout=10) as response:
                body = response.read().decode("utf-8", errors="replace")
                return OpenCodeResponse(response.status, body)
        except HTTPError as error:
            body = error.read().decode("utf-8", errors="replace")
            return OpenCodeResponse(error.code, body)
        except (OSError, TimeoutError, URLError):
            pytest.fail(self.service_error)

    @staticmethod
    def _command_result(response: OpenCodeResponse) -> CommandResult:
        return CommandResult(
            returncode=0 if response.status_code < 400 else 1,
            stdout=response.text,
            status_code=response.status_code,
        )
