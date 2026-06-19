#!/usr/bin/env python3
"""Packet-local validator for axis0_amendment_light_sweep_v0."""

from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any


SIM_ID = "axis0_amendment_light_sweep_v0"
ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
ENVELOPE = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
PYTHON = RESULT_DIR / f"{SIM_ID}_python_results.json"
VALIDATOR_RESULT = RESULT_DIR / f"{SIM_ID}_validator_results.json"

sys.path.insert(0, str(ROOT / "scripts"))
import validate_three_engine_sim_result as generic_validator  # noqa: E402


EXPECTED_CANDIDATES = ["A0.CP.11", "A0.CP.12", "A0.CP.13", "A0.CP.14"]


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def validate_payload() -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    for path in [ENVELOPE, PYTHON, SIM_DIR / "build_card.md"]:
        require(errors, path.exists(), f"missing required file: {path.relative_to(ROOT)}")
    payload = load(ENVELOPE) if ENVELOPE.exists() else {}
    lane = load(PYTHON) if PYTHON.exists() else {}
    if payload:
        require(errors, payload.get("schema_version") == "three_engine_sim_result_v1", "schema_version mismatch")
        require(errors, payload.get("sim_id") == SIM_ID, "sim_id mismatch")
        require(errors, payload.get("classification") == "scratch_diagnostic", "classification mismatch")
        require(errors, payload.get("promotion_allowed") is False, "promotion_allowed must be false")
        require(errors, payload.get("formal_admission_allowed") is False, "formal_admission_allowed must be false")
        require(errors, payload.get("all_pass") is True, "all_pass must be true")
        require(errors, payload.get("envelope_built_with_helper") is True, "helper-built flag missing")
        require(errors, payload.get("build_helper_path") == "scripts/build_three_engine_envelope.py", "helper path mismatch")
        require(errors, sorted(payload.get("per_candidate_verdicts", {})) == EXPECTED_CANDIDATES, "candidate set mismatch")
        generic_errors = generic_validator.validate(payload, require_pytorch=False, require_tool_intent=True)
        errors.extend([f"generic validator: {error}" for error in generic_errors])
        for row in payload.get("candidate_verdict_table", []):
            if row.get("vector_status") == "computed_33_cell":
                require(errors, len(row.get("sign_vector", [])) == 33, f"{row.get('candidate')} vector length mismatch")
                require(errors, bool(row.get("canonical_alias_form_sha256")), f"{row.get('candidate')} missing alias form")
                require(errors, "distinction_boundary_check" in row, f"{row.get('candidate')} missing boundary check")
                require(errors, "owner_chirality_guard" in row, f"{row.get('candidate')} missing owner guard")
                require(errors, "cell_level_disagreement_table" in row, f"{row.get('candidate')} missing disagreement table")
        controls = {row["id"]: row["verdict"] for row in payload.get("control_verdicts", [])}
        require(errors, controls.get("control.anchor_self") == "alias", "anchor control mismatch")
        require(errors, controls.get("control.deliberate_alias") == "alias", "alias control mismatch")
        require(
            errors,
            controls.get("control.deliberate_chirality_tracker") == "excluded-by-owner-type1-type2-chirality-guard",
            "chirality guard control mismatch",
        )
        regressions = {row["candidate"]: row["still_excluded"] for row in payload.get("light_regression_verdicts", [])}
        require(errors, all(regressions.values()) and len(regressions) == 3, "prior light regressions not all excluded")
        require(errors, payload.get("fork_row", {}).get("outcome") in {"disagrees", "aliases_anchor"}, "fork row missing")
        require(errors, "A0.CP.12" in payload.get("queued_heavy", []), "CP.12 must be queued heavy")
        require(errors, "A0.CP.13" in payload.get("queued_heavy", []), "CP.13 global row must be queued heavy")
        proofs = payload.get("crossover_proofs", {})
        require(errors, proofs.get("z3", {}).get("verdict") == "unsat", "z3 positive proof mismatch")
        require(errors, proofs.get("z3", {}).get("flip_control_verdict") == "sat", "z3 flip mismatch")
        require(errors, proofs.get("cvc5", {}).get("verdict") == "unsat", "cvc5 positive proof mismatch")
        require(errors, proofs.get("cvc5", {}).get("flip_control_verdict") == "sat", "cvc5 flip mismatch")
    if lane:
        require(errors, lane.get("all_pass") is True, "python lane all_pass false")
        require(errors, sorted(lane.get("per_candidate_verdicts", {})) == EXPECTED_CANDIDATES, "lane candidate mismatch")
    return errors, {"payload": payload, "lane": lane}


def main() -> int:
    errors, summary = validate_payload()
    result = {
        "ok": not errors,
        "validator_ok": not errors,
        "sim_id": SIM_ID,
        "result_json": str(ENVELOPE.relative_to(ROOT)),
        "errors": errors,
        "verdicts": summary["payload"].get("per_candidate_verdicts", {}) if summary.get("payload") else {},
        "fork_row": summary["payload"].get("fork_row", {}) if summary.get("payload") else {},
        "queued_heavy": summary["payload"].get("queued_heavy", []) if summary.get("payload") else [],
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    VALIDATOR_RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())

