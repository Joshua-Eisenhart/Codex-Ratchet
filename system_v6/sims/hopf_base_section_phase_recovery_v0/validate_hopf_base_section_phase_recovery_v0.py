#!/usr/bin/env python3
"""Packet-local validator for hopf_base_section_phase_recovery_v0."""

from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "hopf_base_section_phase_recovery_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
ENVELOPE = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
JULIA = RESULT_DIR / f"{SIM_ID}_julia_results.json"
VALIDATOR_RESULT = RESULT_DIR / f"{SIM_ID}_validator_results.json"

sys.path.insert(0, str(ROOT / "scripts"))
from builder_audit_boundary import builder_audit_boundary_errors  # noqa: E402


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def main() -> int:
    errors: list[str] = []
    for path in [ENVELOPE, JULIA, SIM_DIR / "build_card.md", SIM_DIR / f"{SIM_ID}.py", SIM_DIR / f"{SIM_ID}_julia.jl"]:
        require(errors, path.exists(), f"missing required file: {path.relative_to(ROOT)}")
    payload = load(ENVELOPE) if ENVELOPE.exists() else {}
    julia = load(JULIA) if JULIA.exists() else {}
    if payload:
        errors.extend(builder_audit_boundary_errors(payload, SIM_DIR / "audit_verdict.md"))
        require(errors, payload.get("schema_version") == "three_engine_sim_result_v1", "schema_version mismatch")
        require(errors, payload.get("sim_id") == SIM_ID, "sim_id mismatch")
        require(errors, payload.get("classification") == "scratch_diagnostic", "classification mismatch")
        require(errors, payload.get("promotion_allowed") is False, "promotion_allowed must be false")
        require(errors, payload.get("formal_admission_allowed") is False, "formal_admission_allowed must be false")
        require(errors, payload.get("all_pass") is True, "all_pass must be true")
        require(errors, payload.get("no_builder_audit_verdict") is True, "no_builder_audit_verdict must be true")
        engines = payload.get("engines", {})
        require(errors, set(engines) == {"julia", "jax"}, "expected julia+jax lanes only")
        require(errors, payload.get("engine_contract", {}).get("omitted_lanes", {}).get("pytorch") == "omitted: no graph/network/autograd claim path", "pytorch omission reason mismatch")
        require(errors, payload.get("build_gates", {}).get("anchor_spectrum_recomputed") is True, "anchor spectrum gate failed")
        require(errors, payload.get("build_gates", {}).get("section_change_gauge_computed") is True, "section-change gate failed")
        require(errors, payload.get("build_gates", {}).get("smt_flips_fire") is True, "SMT flips gate failed")
        require(errors, payload.get("exact_rows", {}).get("anchor_spectrum_values") == ["-2*pi", "-sqrt(3)*pi", "-pi", "0", "pi", "2*pi"], "holonomy spectrum mismatch")
        controls = payload.get("exact_rows", {}).get("controls", {})
        require(errors, controls.get("contractible_loop", {}).get("computed_phase") == "0", "contractible phase mismatch")
        require(errors, controls.get("area_degenerate_boundary", {}).get("pass") is True, "area-degenerate boundary failed")
        proofs = payload.get("crossover_proofs", {})
        for name in ["z3", "cvc5", "julia_z3"]:
            proof = proofs.get(name, {})
            require(errors, proof.get("verdict") == "unsat", f"{name} verdict must be unsat")
            require(errors, proof.get("wrong_sign_flip_verdict") == "sat", f"{name} wrong sign flip must be sat")
        require(errors, payload.get("divergence", {}).get("max_divergence") == 0.0, "engine divergence must be zero")
    if julia:
        require(errors, julia.get("all_pass") is True, "julia all_pass false")
        require(errors, julia.get("reads_peer_result") is False, "julia peer read")
        require(errors, julia.get("classification") == "scratch_diagnostic", "julia classification mismatch")
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
