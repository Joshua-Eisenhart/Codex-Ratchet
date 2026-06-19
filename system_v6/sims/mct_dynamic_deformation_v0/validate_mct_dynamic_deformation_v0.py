#!/usr/bin/env python3
"""Packet-local validator for mct_dynamic_deformation_v0."""

from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "mct_dynamic_deformation_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
DEFAULT_RESULT = SIM_DIR / "results" / f"{SIM_ID}_envelope_results.json"
VALIDATOR_RESULT = SIM_DIR / "results" / f"{SIM_ID}_validator_results.json"

sys.path.insert(0, str(ROOT))
from scripts.builder_audit_boundary import builder_audit_boundary_errors  # noqa: E402


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def require(condition: bool, errors: list[str], message: str) -> None:
    if not condition:
        errors.append(message)


def as_dict(value: Any, errors: list[str], name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        errors.append(f"{name} must be an object")
        return {}
    return value


def validate(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    require(payload.get("schema_version") == "three_engine_sim_result_v1", errors, "schema_version mismatch")
    require(payload.get("sim_id") == SIM_ID, errors, "sim_id mismatch")
    require(payload.get("classification") == "scratch_diagnostic", errors, "classification mismatch")
    require(payload.get("promotion_allowed") is False, errors, "promotion_allowed must be false")
    require(payload.get("formal_admission_allowed") is False, errors, "formal_admission_allowed must be false")
    require(payload.get("all_pass") is True, errors, "all_pass must be true")

    engines = as_dict(payload.get("engines"), errors, "engines")
    require(set(engines) == {"julia", "jax"}, errors, "engines must be exactly julia and jax")
    for name in ("julia", "jax"):
        engine = as_dict(engines.get(name), errors, f"engines.{name}")
        require(engine.get("ran") is True, errors, f"{name}.ran must be true")
        require(engine.get("reads_peer_result") is False, errors, f"{name}.reads_peer_result must be false")
        require(engine.get("reads_parent_results") is True, errors, f"{name}.reads_parent_results must be true")
        require(bool(engine.get("source_sha256")), errors, f"{name}.source_sha256 required")
        require(bool(engine.get("aligned_packages_load_bearing")), errors, f"{name}.aligned load-bearing tools required")
        require(bool(engine.get("capability_receipts")), errors, f"{name}.capability_receipts required")

    mct = as_dict(payload.get("M_C_t_object"), errors, "M_C_t_object")
    finite = as_dict(mct.get("finite_representation"), errors, "M_C_t_object.finite_representation")
    require(finite.get("support_size") == 384, errors, "support size must be 384")
    require(finite.get("q_without_phase") == 24.0, errors, "q_without_phase must cite parent 24")
    require(finite.get("q_with_phase") == 192.0, errors, "q_with_phase must cite parent 192")
    require(len(mct.get("M_t_sequence", [])) == 4, errors, "M_t_sequence must have four rows")

    ledger = as_dict(payload.get("deformation_mode_ledger"), errors, "deformation_mode_ledger")
    compression = ledger.get("compression", [])
    expansion = ledger.get("expansion", [])
    warp = as_dict(ledger.get("warp"), errors, "deformation_mode_ledger.warp")
    require(len(compression) == 2, errors, "two compression rows required")
    require(compression[0].get("adm_before") == 384 and compression[0].get("adm_after") == 256, errors, "F01 compression count drift")
    require(compression[1].get("adm_before") == 256 and compression[1].get("adm_after") == 206, errors, "N01 compression count drift")
    require(len(expansion) == 2, errors, "two expansion rows required")
    require(expansion[0].get("adm_before") == 206 and expansion[0].get("adm_after") == 256, errors, "release expansion count drift")
    require(warp.get("adm_before") == warp.get("adm_after") == 206, errors, "warp must keep admissible count")
    require(warp.get("support_before") == warp.get("support_after") == 384, errors, "warp must keep support count")
    require(warp.get("shape_changed") is True, errors, "warp shape invariant must change")

    rigidity = as_dict(payload.get("rigidity_rows"), errors, "rigidity_rows")
    mono = as_dict(rigidity.get("monotonicity_pure_addition_excludes_expansion"), errors, "rigidity.monotonicity")
    require(mono.get("status") == "STRUCTURALLY_EXCLUDED", errors, "monotonicity status drift")
    for solver in ("z3", "cvc5"):
        row = as_dict(mono.get(solver), errors, f"monotonicity.{solver}")
        require(row.get("ran") is True, errors, f"{solver} monotonicity did not run")
        require(row.get("load_bearing") is True, errors, f"{solver} monotonicity not load-bearing")
        require(row.get("verdict") == "unsat", errors, f"{solver} monotonicity must be UNSAT")
        require(row.get("erased_release_control_verdict") == "sat", errors, f"{solver} release control must be SAT")
    quotient = as_dict(rigidity.get("quotient_readout_irreversibility"), errors, "rigidity.quotient")
    require(quotient.get("status") == "STRUCTURALLY_EXCLUDED", errors, "quotient irreversibility status drift")
    for solver in ("z3", "cvc5"):
        row = as_dict(quotient.get(solver), errors, f"quotient.{solver}")
        require(row.get("verdict") == "unsat", errors, f"{solver} quotient recovery must be UNSAT")
        require(row.get("phase_refined_control_verdict") == "sat", errors, f"{solver} phase refined control must be SAT")
    pinned = as_dict(rigidity.get("pinned_shape_invariants"), errors, "rigidity.pinned")
    require(pinned.get("c1_abs", {}).get("c1_abs") == "1", errors, "c1_abs must be pinned to 1")
    require(pinned.get("chain_additivity_defect") == "0", errors, "chain additivity defect must be zero")
    require(pinned.get("cover_factor") == 2, errors, "cover factor must be 2")
    require(bool(rigidity.get("open_rows")), errors, "open rows required")

    controls = as_dict(payload.get("controls"), errors, "controls")
    jax_controls = as_dict(controls.get("jax"), errors, "controls.jax")
    for name in ("constraint_release_expands", "pure_addition_never_expands", "shape_invariant_control_changes_under_warp", "quotient_erased_flip"):
        require(jax_controls.get(name, {}).get("fired") is True, errors, f"control {name} must fire")

    proofs = as_dict(payload.get("crossover_proofs"), errors, "crossover_proofs")
    for name in ("z3", "cvc5", "julia_z3"):
        row = as_dict(proofs.get(name), errors, f"proofs.{name}")
        require(row.get("ran") is True, errors, f"{name} did not run")
        require(row.get("load_bearing") is True, errors, f"{name} not load-bearing")
        require(row.get("verdict") == "unsat", errors, f"{name} must be unsat")
        require(row.get("erased_release_control_verdict") == "sat", errors, f"{name} release control must be sat")

    claim_tools = payload.get("claim_path_tools")
    tool_calls = payload.get("tool_calls")
    capability_receipts = as_dict(payload.get("capability_receipts"), errors, "capability_receipts")
    require(set(capability_receipts) == {"julia", "jax"}, errors, "top-level capability_receipts must cover julia and jax")
    require(claim_tools == ["jax", "sympy", "z3", "cvc5", "Graphs", "Z3"], errors, "claim_path_tools order/content drift")
    require(isinstance(tool_calls, list) and len(tool_calls) == 6, errors, "six one-to-one tool_calls required")
    if isinstance(tool_calls, list):
        require(sorted(call.get("tool") for call in tool_calls) == sorted(claim_tools), errors, "tool_calls not one-to-one with claim_path_tools")
        require(all(call.get("load_bearing") is True for call in tool_calls), errors, "all tool_calls must be load-bearing")

    div = as_dict(payload.get("divergence"), errors, "divergence")
    require(div.get("julia_authoritative") is True, errors, "julia_authoritative required")
    require(div.get("max_divergence") == 0.0, errors, "max_divergence must be 0.0")
    gates = as_dict(payload.get("build_gates"), errors, "build_gates")
    for gate in ("ceilings_exact", "all_controls_fired", "proofs_load_bearing", "divergence_zero", "one_to_one_tool_calls", "capability_receipts_present", "no_audit_verdict_written"):
        require(gates.get(gate) is True, errors, f"build gate {gate} must be true")

    return errors


def main(argv: list[str]) -> int:
    result_path = Path(argv[1]) if len(argv) > 1 else DEFAULT_RESULT
    if not result_path.is_absolute():
        result_path = ROOT / result_path
    payload = json.loads(result_path.read_text(encoding="utf-8"))
    errors = validate(payload)
    errors.extend(builder_audit_boundary_errors(payload, SIM_DIR / "audit_verdict.md"))
    out = {
        "ok": not errors,
        "result_json": rel(result_path),
        "validator": rel(Path(__file__)),
        "errors": errors,
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }
    VALIDATOR_RESULT.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
