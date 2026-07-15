#!/usr/bin/env python3
"""Fail-closed check of the direct G0-G9 report before Lev may finish."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


SIM_DIR = Path(__file__).resolve().parent
ROOT = SIM_DIR.parents[2]
REPORT = SIM_DIR / "results" / "g0_g9_report.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    checks = []
    for name, record in report["artifacts"].items():
        path = ROOT / record["path"]
        checks.append(path.is_file() and sha256(path) == record["sha256"])
    gates = report["gates"]
    checks.extend(
        [
            len(gates) == 11,
            all(gates[f"G{i}_{suffix}"] for i, suffix in [
                (0, "preregistered_object"),
                (1, "exact_census"),
                (2, "three_engine_closure_parity"),
                (3, "dual_smt"),
                (4, "coface_drive"),
                (5, "tooth_and_hold_controls"),
                (6, "plural_mss"),
                (7, "closed_engine_lanes"),
                (8, "source_runtime_ceiling_binding"),
                (9, "independent_validator_and_mutations"),
            ]),
            gates["G10_deterministic_lev_replay"] is False,
            report["mechanical_pass"] is True,
            report["sim_contract_lint_pass"] is True,
            any(
                command.get("label") == "sim_contract_lint"
                and command.get("pass") is True
                and '"violation_total": 0' in command.get("stdout", "")
                for command in report.get("commands", [])
            ),
            report["semantic_forcing_pass"] is False,
            report["candidate_pass"] is False,
            report["candidate_decision"] == "HOLD_DESIGNED_SURROGATE",
            report["final_decision"] == "HOLD_SEMANTIC_FORCING",
            report["ratchet_state"] == "OPEN",
            report["semantic_gates"]["S1_controls_same_code_path"] is True,
            report["semantic_gates"]["S2_independent_drive_mss_reconstruction"] is True,
            not all(report["semantic_gates"].values()),
            report["llm_verdict_used"] is False,
            report["promotion_allowed"] is False,
            report["formal_admission_allowed"] is False,
        ]
    )
    ok = all(checks)
    print(json.dumps({"schema": "codex_ratchet.g0_g9_validation.v1", "ok": ok, "check_count": len(checks)}, sort_keys=True))
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
