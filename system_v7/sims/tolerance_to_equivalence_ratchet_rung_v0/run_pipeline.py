#!/usr/bin/env python3
"""Direct code-only G0-G9 pipeline. G10 remains a separate Lev replay."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess
import sys


SIM_DIR = Path(__file__).resolve().parent
ROOT = SIM_DIR.parents[2]
RESULT_DIR = SIM_DIR / "results"


def execute(label: str, command: list[str]) -> dict[str, object]:
    proc = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
    return {
        "label": label,
        "command": command,
        "returncode": proc.returncode,
        "pass": proc.returncode == 0,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    commands = [
        execute("controller", [sys.executable, "-B", str(SIM_DIR / "run_controller.py")]),
        execute(
            "independent_validator",
            [sys.executable, "-B", str(SIM_DIR / "validate_controller_envelope.py"), "--receipt", str(RESULT_DIR / "validation.json")],
        ),
        execute("mutation_tests", [sys.executable, "-B", str(SIM_DIR / "run_mutation_tests.py")]),
    ]
    envelope = json.loads((RESULT_DIR / "controller_envelope.json").read_text(encoding="utf-8"))
    validation = json.loads((RESULT_DIR / "validation.json").read_text(encoding="utf-8"))
    mutations = json.loads((RESULT_DIR / "mutation_tests.json").read_text(encoding="utf-8"))
    g0_g8 = envelope.get("all_pass") is True and all(envelope.get("checks", {}).values())
    g9 = validation.get("ok") is True and mutations.get("all_pass") is True
    candidate_pass = all(item["pass"] for item in commands) and g0_g8 and g9
    report = {
        "schema": "codex_ratchet.tolerance_to_equivalence.g0_g9_report.v1",
        "generated_at": dt.datetime.now(dt.UTC).isoformat(),
        "sim_id": "tolerance_to_equivalence_ratchet_rung_v0",
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "llm_verdict_used": False,
        "commands": commands,
        "gates": {
            **envelope["checks"],
            "G9_independent_validator_and_mutations": g9,
            "G10_deterministic_lev_replay": False,
        },
        "artifacts": {
            "controller_envelope": {"path": str((RESULT_DIR / "controller_envelope.json").relative_to(ROOT)), "sha256": sha256(RESULT_DIR / "controller_envelope.json")},
            "validation": {"path": str((RESULT_DIR / "validation.json").relative_to(ROOT)), "sha256": sha256(RESULT_DIR / "validation.json")},
            "mutations": {"path": str((RESULT_DIR / "mutation_tests.json").relative_to(ROOT)), "sha256": sha256(RESULT_DIR / "mutation_tests.json")},
        },
        "candidate_pass": candidate_pass,
        "candidate_decision": "COMMIT_TOOTH_CANDIDATE" if candidate_pass else "HOLD",
        "final_decision": "HOLD_PENDING_LEV" if candidate_pass else "HOLD",
        "ratchet_state": "TOOTH_1_CANDIDATE" if candidate_pass else "HOLD",
        "claim_ceiling": "G0-G9 code-green candidate only; no official tooth or launch until G10 Lev replay is validated",
        "blocked_consumers": ["official Ratchet launch", "canonical/scientific promotion", "terrain/operator layers", "cross-domain claims"],
    }
    path = RESULT_DIR / "g0_g9_report.json"
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"TOLERANCE_RUNG_G0_G9_DONE candidate_pass={str(candidate_pass).lower()} final_decision={report['final_decision']}")
    return 0 if candidate_pass else 2


if __name__ == "__main__":
    raise SystemExit(main())
