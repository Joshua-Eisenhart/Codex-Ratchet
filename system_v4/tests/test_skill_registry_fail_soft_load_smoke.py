"""
Smoke test for fail-soft skill registry loading.

This guards the loading seam against a single malformed row collapsing the
entire registry to zero and checks that repaired rows are recorded in the load
audit.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from system_v4.skills.skill_registry import SkillRegistry


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _build_skill(skill_id: str, description: str) -> dict[str, object]:
    return {
        "skill_id": skill_id,
        "name": skill_id,
        "description": description,
        "skill_type": "operator",
        "source_type": "operator_module",
        "source_path": f"system_v4/skills/{skill_id.replace('-', '_')}.py",
        "applicable_trust_zones": ["A2_LOW_CONTROL"],
        "applicable_graphs": [],
        "inputs": [],
        "outputs": [],
        "related_skills": [],
        "adapters": {"shell": f"system_v4/skills/{skill_id.replace('-', '_')}.py"},
        "capabilities": {"is_phase_runner": True},
        "tool_dependencies": [],
        "provenance": "smoke-test",
        "status": "active",
        "last_verified_utc": "2026-03-21T00:00:00Z",
        "tags": ["smoke"],
    }


def main() -> None:
    reg = SkillRegistry(".")
    _assert(len(reg.skills) == 123, f"expected 123 live skills, got {len(reg.skills)}")
    _assert(reg.load_issues == [], f"expected clean live load, got {reg.load_issues!r}")

    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        registry_path = root / "system_v4" / "a1_state" / "skill_registry_v1.json"
        registry_path.parent.mkdir(parents=True, exist_ok=True)
        registry_path.write_text(
            json.dumps(
                {
                    "good-skill": _build_skill("good-skill", "A valid skill row"),
                    "bad-skill": {
                        "skill_id": "bad-skill",
                        "skill_type": "operator",
                        "source_path": "system_v4/skills/bad_skill.py",
                        "adapters": {
                            "shell": "system_v4/skills/bad_skill.py",
                            "dispatch_binding": "python_module",
                        },
                        "status": "active",
                    },
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )

        temp_reg = SkillRegistry(str(root))
        _assert(len(temp_reg.skills) == 2, f"expected 2 loaded skills, got {len(temp_reg.skills)}")

        repaired = temp_reg.get("bad-skill")
        _assert(repaired is not None, "expected repaired bad-skill to load")
        _assert(repaired.name == "bad-skill", f"expected repaired name, got {repaired.name!r}")
        _assert(
            repaired.source_type == "operator_module",
            f"expected inferred source_type, got {repaired.source_type!r}",
        )
        _assert(
            any(issue.get("skill_id") == "bad-skill" and issue.get("action") == "repaired" for issue in temp_reg.load_issues),
            f"expected a recorded repair issue, got {temp_reg.load_issues!r}",
        )
        _assert(
            temp_reg.load_stats["loaded"] == 2,
            f"expected 2 loaded rows, got {temp_reg.load_stats!r}",
        )
        _assert(
            temp_reg.load_stats["repaired"] == 1,
            f"expected 1 repaired row, got {temp_reg.load_stats!r}",
        )
        _assert(
            temp_reg.load_stats["skipped"] == 0,
            f"expected 0 skipped rows, got {temp_reg.load_stats!r}",
        )


if __name__ == "__main__":
    main()
