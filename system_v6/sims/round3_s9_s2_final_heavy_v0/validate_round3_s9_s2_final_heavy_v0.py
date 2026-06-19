#!/usr/bin/env python3
"""Packet-local validator for round3_s9_s2_final_heavy_v0."""

from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "round3_s9_s2_final_heavy_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
ENVELOPE = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
JAX = RESULT_DIR / f"{SIM_ID}_jax_results.json"
JULIA = RESULT_DIR / f"{SIM_ID}_julia_results.json"
PYTORCH = RESULT_DIR / f"{SIM_ID}_pytorch_results.json"
VALIDATOR_RESULT = RESULT_DIR / f"{SIM_ID}_validator_results.json"

sys.path.insert(0, str(ROOT))
from scripts.builder_audit_boundary import builder_audit_boundary_errors  # noqa: E402


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def main() -> int:
    errors: list[str] = []
    for path in [ENVELOPE, JAX, JULIA, PYTORCH, SIM_DIR / "build_card.md", SIM_DIR / "builder_self_assessment.md"]:
        require(errors, path.exists(), f"missing required file: {path.relative_to(ROOT)}")
    payload = load(ENVELOPE) if ENVELOPE.exists() else {}
    jax = load(JAX) if JAX.exists() else {}
    errors.extend(builder_audit_boundary_errors(payload, SIM_DIR / "audit_verdict.md"))
    julia = load(JULIA) if JULIA.exists() else {}
    pytorch = load(PYTORCH) if PYTORCH.exists() else {}
    if payload:
        require(errors, payload.get("schema_version") == "three_engine_sim_result_v1", "schema_version mismatch")
        require(errors, payload.get("sim_id") == SIM_ID, "sim_id mismatch")
        require(errors, payload.get("classification") == "scratch_diagnostic", "classification mismatch")
        require(errors, payload.get("promotion_allowed") is False, "promotion_allowed must be false")
        require(errors, payload.get("formal_admission_allowed") is False, "formal_admission_allowed must be false")
        require(errors, payload.get("all_pass") is True, "all_pass must be true")
        require(errors, set(payload.get("engines", {})) == {"julia", "jax", "pytorch"}, "all three lanes must be present")
        require(errors, payload.get("row_verdict_table", [{}])[0].get("verdict") == "excluded-under-pinned-path-ordered-transport-convention", "S9 verdict mismatch")
        require(errors, "valid-cover-family" in payload.get("row_verdict_table", [{}, {}])[1].get("verdict", ""), "S2 verdict mismatch")
        for gate, value in payload.get("build_gates", {}).items():
            require(errors, value is True, f"gate failed: {gate}")
        proofs = payload.get("crossover_proofs", {})
        require(errors, proofs.get("z3", {}).get("verdict") == "unsat", "z3 must be unsat")
        require(errors, proofs.get("cvc5", {}).get("verdict") == "unsat", "cvc5 must be unsat")
        require(errors, proofs.get("z3", {}).get("flip_control_verdict") == "sat", "z3 flip must be sat")
        require(errors, proofs.get("cvc5", {}).get("flip_control_verdict") == "sat", "cvc5 flip must be sat")
        require(errors, proofs.get("julia_z3", {}).get("verdict") == "unsat", "julia_z3 must be unsat")
    for name, lane in [("jax", jax), ("julia", julia), ("pytorch", pytorch)]:
        if lane:
            require(errors, lane.get("all_pass") is True, f"{name} all_pass false")
            require(errors, lane.get("reads_peer_result") is False, f"{name} peer read")
            require(errors, lane.get("classification") == "scratch_diagnostic", f"{name} classification mismatch")
    if jax:
        require(errors, jax.get("s9", {}).get("gauge_reparameterization_alias", {}).get("alias_pass") is True, "S9 alias control failed")
        require(errors, jax.get("s2", {}).get("invalid_cover_control", {}).get("valid") is False, "S2 invalid cover must fail")
        require(errors, len(jax.get("s2", {}).get("valid_union_rows", [])) == 3, "S2 valid union count mismatch")
    result = {
        "ok": not errors,
        "validator_ok": not errors,
        "sim_id": SIM_ID,
        "result_json": str(ENVELOPE.relative_to(ROOT)),
        "errors": errors,
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    VALIDATOR_RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())

