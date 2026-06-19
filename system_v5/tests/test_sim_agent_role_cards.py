import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CARDS = ROOT / "system_v5/codex_skills/three-engine-sim/references/sim_agent_role_cards.md"


def test_sim_agent_role_cards_validate() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/validate_sim_agent_role_cards.py", str(CARDS)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout)["ok"] is True
    text = CARDS.read_text(encoding="utf-8")
    for role_id in (
        "three_engine_sim_controller",
        "julia_authoritative_sim_builder",
        "jax_rich_mirror_sim_builder",
        "pytorch_support_sim_builder",
        "smt_crossover_proof_engineer",
        "result_envelope_gatekeeper",
        "hollow_mirror_fabrication_auditor",
    ):
        assert f"role_id: {role_id}" in text
