"""Guards for executable skill paths documented in AGENTS.md."""

from __future__ import annotations

import re
from pathlib import Path

import pytest


@pytest.mark.unit
def test_agents_md_skill_paths_reference_existing_skills(repo_root: Path) -> None:
    """Every concrete skills/<name> path in AGENTS.md must resolve locally."""

    agents = (repo_root / "AGENTS.md").read_text(encoding="utf-8")
    skill_names = sorted(set(re.findall(r"skills/([a-z0-9][a-z0-9-]*)", agents)))

    for skill_name in skill_names:
        skill_file = repo_root / "skills" / skill_name / "SKILL.md"
        assert skill_file.is_file(), (
            f"AGENTS.md referencia skills/{skill_name}, "
            f"mas {skill_file} nao existe"
        )
