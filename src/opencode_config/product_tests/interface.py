"""Contrato JSON comum das suites de testes-produto."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import TextIO

VALID_SEVERITIES = frozenset({"bloqueante", "melhoria"})
VALID_STATUSES = frozenset({"pass", "fail"})


class ReportFormatError(ValueError):
    """Indica que um relatorio nao segue o contrato publico."""


@dataclass(frozen=True)
class Finding:
    """Problema observavel produzido por uma ferramenta."""

    severity: str
    tool: str
    message: str

    def __post_init__(self) -> None:
        if self.severity not in VALID_SEVERITIES:
            raise ValueError(f"severity invalida: {self.severity}")
        if not self.tool.strip():
            raise ValueError("tool nao pode ser vazio")
        if not self.message.strip():
            raise ValueError("message nao pode ser vazio")

    def to_dict(self) -> dict[str, str]:
        return {
            "severity": self.severity,
            "tool": self.tool,
            "message": self.message,
        }


@dataclass(frozen=True)
class ProductReport:
    """Relatorio com veredito derivado dos findings e status declarado."""

    findings: tuple[Finding, ...]
    declared_status: str | None = None

    def __post_init__(self) -> None:
        if self.declared_status is not None and (
            self.declared_status not in VALID_STATUSES
        ):
            raise ValueError(f"status invalido: {self.declared_status}")

    @classmethod
    def from_findings(
        cls,
        findings: list[Finding] | tuple[Finding, ...],
    ) -> ProductReport:
        return cls(tuple(findings))

    @property
    def status(self) -> str:
        if self.declared_status == "fail":
            return "fail"
        if any(finding.severity == "bloqueante" for finding in self.findings):
            return "fail"
        return "pass"

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "findings": [finding.to_dict() for finding in self.findings],
        }


def emit_report(report: ProductReport, output: TextIO) -> None:
    """Emite uma unica linha JSON, sem texto auxiliar no stdout."""

    reconfigure = getattr(output, "reconfigure", None)
    if reconfigure is not None:
        reconfigure(encoding="utf-8", errors="replace")
    json.dump(report.to_dict(), output, ensure_ascii=False, separators=(",", ":"))
    output.write("\n")
    output.flush()


def decode_report(payload: str) -> ProductReport:
    """Valida e converte o JSON produzido por uma suite filha."""

    try:
        document = json.loads(payload)
    except json.JSONDecodeError as error:
        raise ReportFormatError(f"JSON invalido: {error.msg}") from error

    if not isinstance(document, dict):
        raise ReportFormatError("relatorio JSON deve ser um objeto")
    if set(document) != {"status", "findings"}:
        raise ReportFormatError("relatorio deve conter status e findings")

    status = document["status"]
    findings_data = document["findings"]
    if status not in VALID_STATUSES:
        raise ReportFormatError("status invalido")
    if not isinstance(findings_data, list):
        raise ReportFormatError("findings deve ser uma lista")

    findings: list[Finding] = []
    for item in findings_data:
        if not isinstance(item, dict) or set(item) != {
            "severity",
            "tool",
            "message",
        }:
            raise ReportFormatError("finding deve conter severity, tool e message")
        try:
            findings.append(
                Finding(
                    severity=item["severity"],
                    tool=item["tool"],
                    message=item["message"],
                )
            )
        except (TypeError, ValueError) as error:
            raise ReportFormatError(f"finding invalido: {error}") from error

    return ProductReport(tuple(findings), declared_status=status)
