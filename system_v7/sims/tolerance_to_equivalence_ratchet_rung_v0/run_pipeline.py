#!/usr/bin/env python3
"""Direct code-only G0-G9 pipeline. G10 remains a separate Lev replay."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess
import sys


CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
TOOL_MANIFEST = {
    "python_stdlib": {
        "used": True,
        "reason": "The pipeline uses standard-library subprocess, hashing, and JSON to compose code-gate receipts.",
    },
}
TOOL_INTEGRATION_DEPTH = {"python_stdlib": "supportive"}

SIM_DIR = Path(__file__).resolve().parent
ROOT = SIM_DIR.parents[2]
RESULT_DIR = SIM_DIR / "results"
CONTRACT_SOURCES = [
    SIM_DIR / name
    for name in (
        "run_jax.py",
        "run_pytorch.py",
        "run_proofs.py",
        "run_controller.py",
        "run_pipeline.py",
        "semantic_audit.py",
    )
]


def execute(
    label: str,
    command: list[str],
    expected_returncodes: tuple[int, ...] = (0,),
) -> dict[str, object]:
    proc = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
    return {
        "label": label,
        "command": command,
        "returncode": proc.returncode,
        "expected_returncodes": list(expected_returncodes),
        "pass": proc.returncode in expected_returncodes,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    commands = [
        execute(
            "sim_contract_lint",
            [
                sys.executable,
                "-B",
                str(ROOT / "scripts" / "lint_sim_contract.py"),
                *[str(path) for path in CONTRACT_SOURCES],
            ],
        ),
        execute("controller", [sys.executable, "-B", str(SIM_DIR / "run_controller.py")]),
        execute(
            "independent_validator",
            [sys.executable, "-B", str(SIM_DIR / "validate_controller_envelope.py"), "--receipt", str(RESULT_DIR / "validation.json")],
        ),
        execute("mutation_tests", [sys.executable, "-B", str(SIM_DIR / "run_mutation_tests.py")]),
        execute(
            "semantic_audit_expected_hold",
            [sys.executable, "-B", str(SIM_DIR / "semantic_audit.py")],
            (2,),
        ),
    ]
    envelope = json.loads((RESULT_DIR / "controller_envelope.json").read_text(encoding="utf-8"))
    validation = json.loads((RESULT_DIR / "validation.json").read_text(encoding="utf-8"))
    mutations = json.loads((RESULT_DIR / "mutation_tests.json").read_text(encoding="utf-8"))
    semantic = json.loads((RESULT_DIR / "semantic_audit.json").read_text(encoding="utf-8"))
    g0_g8 = envelope.get("all_pass") is True and all(envelope.get("checks", {}).values())
    g9 = validation.get("ok") is True and mutations.get("all_pass") is True
    mechanical_pass = all(item["pass"] for item in commands) and g0_g8 and g9
    semantic_forcing_pass = semantic.get("semantic_forcing_pass") is True
    candidate_pass = mechanical_pass and semantic_forcing_pass
    report = {
        "schema": "codex_ratchet.tolerance_to_equivalence.g0_g9_report.v1",
        "generated_at": dt.datetime.now(dt.UTC).isoformat(),
        "sim_id": "tolerance_to_equivalence_ratchet_rung_v0",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
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
            "semantic_audit": {"path": str((RESULT_DIR / "semantic_audit.json").relative_to(ROOT)), "sha256": sha256(RESULT_DIR / "semantic_audit.json")},
        },
        "mechanical_pass": mechanical_pass,
        "sim_contract_lint_pass": commands[0]["pass"],
        "semantic_forcing_pass": semantic_forcing_pass,
        "semantic_gates": semantic["semantic_gates"],
        "candidate_pass": candidate_pass,
        "candidate_decision": "COMMIT_TOOTH_CANDIDATE" if candidate_pass else "HOLD_DESIGNED_SURROGATE",
        "final_decision": "HOLD_PENDING_LEV" if candidate_pass else "HOLD_SEMANTIC_FORCING",
        "ratchet_state": "TOOTH_1_CANDIDATE" if candidate_pass else "OPEN",
        "claim_ceiling": "G0-G9 mechanically green finite pair-collapse-loss surrogate; semantic forcing, persistent pawl, and G10 are absent",
        "blocked_consumers": ["official Ratchet launch", "canonical/scientific promotion", "terrain/operator layers", "cross-domain claims"],
    }
    path = RESULT_DIR / "g0_g9_report.json"
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    final_report = {
        "schema": "codex_ratchet.tolerance_to_equivalence.final_report.v2",
        "generated_at": dt.datetime.now(dt.UTC).isoformat(),
        "sim_id": report["sim_id"],
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "scientific_claim_proven": False,
        "release_eligible": False,
        "official_launch_allowed": False,
        "llm_verdict_used": False,
        "gates": report["gates"],
        "semantic_gates": report["semantic_gates"],
        "mechanical_code_gates_pass": mechanical_pass,
        "sim_contract_lint_pass": report["sim_contract_lint_pass"],
        "semantic_forcing_pass": semantic_forcing_pass,
        "all_code_gates_pass": False,
        "decision": "HOLD_DESIGNED_SURROGATE",
        "ratchet_state_before": "OPEN",
        "ratchet_state_after": "OPEN",
        "artifacts": {
            "g0_g9_report": {
                "path": str(path.relative_to(ROOT)),
                "sha256": sha256(path),
            },
            "semantic_audit": report["artifacts"]["semantic_audit"],
        },
        "lev_boundary": {
            "g10_run_for_current_report": False,
            "proof_backed_execution": False,
            "proof_bundle_written": False,
        },
        "replacement_preregistration": semantic["replacement_preregistration"],
        "claim_ceiling": report["claim_ceiling"],
        "blocked_consumers": report["blocked_consumers"],
    }
    (RESULT_DIR / "final_report.json").write_text(
        json.dumps(final_report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        f"TOLERANCE_RUNG_G0_G9_DONE mechanical_pass={str(mechanical_pass).lower()} "
        f"semantic_forcing_pass={str(semantic_forcing_pass).lower()} "
        f"final_decision={report['final_decision']}"
    )
    return 0 if mechanical_pass and not semantic_forcing_pass else 2


if __name__ == "__main__":
    raise SystemExit(main())
