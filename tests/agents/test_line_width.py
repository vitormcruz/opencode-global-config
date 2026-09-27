from pathlib import Path

import pytest


@pytest.mark.unit
def test_agent_instruction_files_have_no_lines_over_120_columns(
    repo_root: Path,
) -> None:
    agents_dir = repo_root / "harness-conf" / "agents"
    instruction_files = [
        *sorted(agents_dir.glob("*.md")),
        repo_root / "harness-conf" / "AGENTS.base.md",
    ]
    violations = []

    for path in instruction_files:
        for line_number, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(),
            start=1,
        ):
            if len(line) > 120:
                relative_path = path.relative_to(repo_root)
                violations.append(f"{relative_path}:{line_number}")

    assert violations == [], (
        "Linhas acima de 120 colunas em instruções de agentes:\n"
        + "\n".join(violations)
    )
