import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def run_inventory(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "scripts/codex_skill_agent_inventory.py", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def test_inventory_reports_known_sections() -> None:
    result = run_inventory()

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert {
        "codex_installed",
        "agents_installed",
        "repo_codex_skills",
        "claude_skills",
        "system_v4_skill_specs",
    } <= set(payload["sections"])
    assert payload["sections"]["codex_installed"]["count"] >= 1
    assert payload["codex_primary_home"].endswith(".codex")
    assert "codex-ratchet-sim-audit-spine" not in payload["upgrade_gaps"]["missing_codex_skills"]
    assert payload["sections"]["agents_installed"]["count"] >= 1
    assert any(item["name"] == "codex-autoresearch" for item in payload["sections"]["agents_installed"]["items"])
    assert any(item["name"] == "tribunal" for item in payload["sections"]["agents_installed"]["items"])
    assert payload["hermes_installed"]["count"] >= 1
    assert payload["claude_agents"]["count"] >= 1
    assert payload["wiki_surfaces"]["hermes_current"]["count"] >= 1
    assert any(
        item["relative_path"] == "skills-and-agent-rules.md"
        for item in payload["wiki_surfaces"]["hermes_current"]["items"]
    )
    assert any(item["name"] == "three-council-wizard-v4-3" for item in payload["sections"]["repo_codex_skills"]["items"])
    repo_skill_names = {item["name"] for item in payload["sections"]["repo_codex_skills"]["items"]}
    assert {"three-engine-sim", "julia-sim", "jax-sim", "pytorch-sim"} <= repo_skill_names
    assert payload["openai_yaml"]["repo_codex_skills"]["count"] >= 1
    assert all(item["valid"] for item in payload["openai_yaml"]["repo_codex_skills"]["items"])
    for skill in [
        "three-engine-sim",
        "julia-sim",
        "jax-sim",
        "pytorch-sim",
        "codex-skill-agent-upgrader",
        "karpathy-bounded-improve",
        "three-council-wizard-v4-3",
    ]:
        assert payload["repo_active_skill_parity"][skill]["matches"], skill
        assert payload["repo_secondary_skill_parity"][skill]["matches"], skill


def test_inventory_writes_output(tmp_path: Path) -> None:
    out = tmp_path / "inventory.json"
    result = run_inventory("--out", str(out))

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(out.read_text())
    assert payload["upgrade_gaps"]["notes"]
    assert "repo_active_skill_parity" in payload
    assert "repo_secondary_skill_parity" in payload
