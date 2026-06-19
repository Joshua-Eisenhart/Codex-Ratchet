#!/usr/bin/env python3
"""Validate ratchet_s1_single_shell_pilot_v0 result shape and gates."""

from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "ratchet_s1_single_shell_pilot_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
DEFAULT_RESULT = SIM_DIR / "results" / f"{SIM_ID}_envelope_results.json"
VALIDATOR_RESULT = SIM_DIR / "results" / f"{SIM_ID}_validator_results.json"


def rel(path: Path) -> str:
    if not path.is_absolute():
        path = ROOT / path
    return str(path.relative_to(ROOT))


def require(condition: bool, errors: list[str], message: str) -> None:
    if not condition:
        errors.append(message)


def as_dict(value: Any, name: str, errors: list[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        errors.append(f"{name} must be an object")
        return {}
    return value


def validate(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    require(payload.get("schema_version") == "three_engine_sim_result_v1", errors, "schema_version mismatch")
    require(payload.get("mode") == "RATCHETED", errors, "mode must be RATCHETED")
    require(payload.get("engine_contract", {}).get("mode") == "RATCHETED", errors, "engine_contract.mode must be RATCHETED")
    require(payload.get("engine_contract", {}).get("lanes") == ["julia", "jax"], errors, "engine_contract lanes must be julia,jax")
    require("pytorch" in payload.get("engine_contract", {}).get("omitted_lanes", {}), errors, "pytorch omission reason must be declared")
    engines = as_dict(payload.get("engines"), "engines", errors)
    require(set(engines) == {"julia", "jax"}, errors, "engines must contain scoped julia and jax lanes only")
    for engine_name in ("julia", "jax"):
        engine = as_dict(engines.get(engine_name), f"engines.{engine_name}", errors)
        require(engine.get("ran") is True, errors, f"{engine_name} must be marked ran")
        require(engine.get("reads_peer_result") is False, errors, f"{engine_name} must not read peer result")
        require(bool(engine.get("source_path")), errors, f"{engine_name} source_path required")
    require(payload.get("classification") == "scratch_diagnostic", errors, "classification must be scratch_diagnostic")
    require(payload.get("promotion_allowed") is False, errors, "promotion_allowed must be false")
    require(payload.get("formal_admission") is False, errors, "formal_admission must be false")
    require(payload.get("formal_admission_allowed") is False, errors, "formal_admission_allowed must be false")
    require(payload.get("all_pass") is True, errors, "all_pass must be true")

    gates = as_dict(payload.get("build_gates"), "build_gates", errors)
    for gate in (
        "mode_declared_ratcheted",
        "single_shell_only",
        "nested_multi_shell_conditioning_fenced",
        "ceilings_preserved",
        "disintegration_rule_cited",
        "naive_conditioning_failure_refired",
        "narrowing_computed",
        "alteration_computed",
        "path_pair_honestly_marked_commuting",
        "noncommuting_extension_present",
        "path_specificity_kind_reworded",
        "controls_fired",
        "smt_positive_and_erased_flip",
        "julia_z3_positive_and_erased_flip",
        "one_to_one_tool_calls",
        "capability_receipts_present",
        "julia_result_loaded",
        "julia_source_hash_matches",
        "julia_reads_no_peer_result",
        "julia_engine_values_match_python_exact_rows",
        "julia_z3_load_bearing",
    ):
        require(gates.get(gate) is True, errors, f"gate {gate} must be true")

    fences = as_dict(payload.get("scope_fences"), "scope_fences", errors)
    require(fences.get("single_shell_only") is True, errors, "single_shell_only fence missing")
    require(fences.get("nested_multi_shell_conditioning") is False, errors, "nested multi-shell fence must be false")
    require(fences.get("trend_claims") is False, errors, "trend claims must be false")

    sequence = as_dict(payload.get("ratchet_sequence"), "ratchet_sequence", errors)
    require(sequence.get("step1", {}).get("committed_prerequisite", "").endswith("geo_disintegration_machinery_v0"), errors, "step1 must cite disintegration prerequisite")
    require(sequence.get("step2", {}).get("committed_prerequisite", "").endswith("geo_s1_finite_phase_lens_v0"), errors, "step2 must cite committed lens tower")
    require(
        sequence.get("step1", {})
        .get("exact_geometry", {})
        .get("conditional_measure", {})
        .get("conditional_chart_density")
        == "1/(4*pi^2) d_phi d_chi",
        errors,
        "conditional chart density must match committed rule",
    )

    signatures = as_dict(payload.get("ratchet_signatures"), "ratchet_signatures", errors)
    require(signatures.get("narrowing", {}).get("computed") is True, errors, "narrowing must be computed")
    require(signatures.get("alteration", {}).get("altered") is True, errors, "alteration must be true")
    path_specificity = signatures.get("path_specificity", {})
    require(
        path_specificity.get("requested_two_constraint_pair", {}).get("same_pair_commutes") is True,
        errors,
        "requested two-constraint pair must be honestly marked commuting",
    )
    require(
        path_specificity.get("noncommuting_extension", {}).get("noncommuting") is True,
        errors,
        "noncommuting extension must be present",
    )
    require(
        path_specificity.get("noncommuting_extension", {}).get("nested_multi_shell_conditioning") is False,
        errors,
        "noncommuting extension must not use nested multi-shell conditioning",
    )
    require(
        path_specificity.get("noncommuting_extension", {}).get("claim_kind")
        == "quotient_well_definedness_equivariance_failure",
        errors,
        "noncommuting extension must be restated as quotient well-definedness/equivariance failure",
    )
    require(
        path_specificity.get("noncommuting_extension", {}).get("not_numeric_order_gap_family") is True,
        errors,
        "noncommuting extension must not be claimed as a numeric order-gap family",
    )

    controls = as_dict(payload.get("controls"), "controls", errors)
    require(
        controls.get("identity_constraint_excludes_nothing", {}).get("byte_exact_on_exact_rows") is True,
        errors,
        "identity constraint must be byte-exact",
    )
    require(
        controls.get("naive_conditioning_failure_refired", {}).get("pass") is True,
        errors,
        "naive conditioning failure must be refired",
    )
    require(
        controls.get("shuffled_wrong_order_control", {}).get("control_fired") is True,
        errors,
        "wrong-order control must fire",
    )

    proofs = as_dict(payload.get("crossover_proofs"), "crossover_proofs", errors)
    for solver in ("z3", "cvc5"):
        row = proofs.get(solver, {})
        require(row.get("ran") is True, errors, f"{solver} must run")
        require(row.get("load_bearing") is True, errors, f"{solver} must be load-bearing")
        require(row.get("verdict") == "unsat", errors, f"{solver} positive verdict must be unsat")
        require(row.get("erased_flip_detected") is True, errors, f"{solver} erased flip must be detected")
    julia_z3 = proofs.get("julia_z3", {})
    require(julia_z3.get("ran") is True, errors, "julia_z3 must run")
    require(julia_z3.get("load_bearing") is True, errors, "julia_z3 must be load-bearing")
    require(julia_z3.get("verdict") == "unsat", errors, "julia_z3 positive verdict must be unsat")
    require(julia_z3.get("erased_flip_detected") is True, errors, "julia_z3 erased flip must be detected")

    calls = payload.get("tool_calls")
    require(isinstance(calls, list) and len(calls) == 4, errors, "tool_calls must contain exactly four rows")
    if isinstance(calls, list):
        require([call.get("tool") for call in calls] == ["sympy", "z3", "cvc5", "Z3"], errors, "tool call order must be sympy,z3,cvc5,Z3")
        require(all(call.get("load_bearing") is True for call in calls), errors, "all declared tool calls must be load-bearing")

    claim_tools = payload.get("claim_path_tools")
    require(claim_tools == ["sympy", "z3", "cvc5", "Z3"], errors, "claim_path_tools mismatch")

    hashes = as_dict(payload.get("computed_subtree_hashes"), "computed_subtree_hashes", errors)
    require(hashes.get("kind") == "shape_only_repair_hash_receipt", errors, "G2 hash receipt missing")
    preservation = as_dict(hashes.get("preservation_checks"), "computed_subtree_hashes.preservation_checks", errors)
    require(preservation.get("ratchet_sequence") is True, errors, "ratchet_sequence hash must match audited receipt")
    require(preservation.get("controls") is True, errors, "controls hash must match audited receipt")
    require(
        preservation.get("crossover_proofs_python_z3_cvc5") is True,
        errors,
        "original Python solver proof hash must match audited receipt",
    )
    require(
        preservation.get("ratchet_signatures_whole_subtree_changed_by_G3_language_repair") is True,
        errors,
        "ratchet_signatures hash should change only because G3 language was repaired",
    )

    hardening = as_dict(payload.get("hardening_addendum"), "hardening_addendum", errors)
    closed = as_dict(hardening.get("closed_caveats"), "hardening_addendum.closed_caveats", errors)
    for caveat in ("G1_SOURCE_BACKED_LANES", "G2_MISSING_PRE_FIX_HASH_NOTE", "G3_PATH_GAP_KIND"):
        require(closed.get(caveat, {}).get("closed") is True, errors, f"{caveat} must be closed in builder addendum")

    divergence = as_dict(payload.get("divergence"), "divergence", errors)
    require(divergence.get("julia_authoritative") is True, errors, "divergence.julia_authoritative must be true")
    require(divergence.get("max_divergence") == 0.0, errors, "max_divergence must be 0.0")
    engine_values = as_dict(divergence.get("engine_values"), "divergence.engine_values", errors)
    require(set(engine_values) == {"julia", "jax"}, errors, "divergence.engine_values must contain julia and jax")
    per_observable = as_dict(divergence.get("per_observable"), "divergence.per_observable", errors)
    require(bool(per_observable), errors, "divergence.per_observable must be populated")
    if set(engine_values) == {"julia", "jax"}:
        require(engine_values["julia"] == engine_values["jax"], errors, "scoped julia and jax observable values must match exactly")

    return errors


def main(argv: list[str]) -> int:
    result_path = Path(argv[1]) if len(argv) > 1 else DEFAULT_RESULT
    if not result_path.is_absolute():
        result_path = ROOT / result_path
    payload = json.loads(result_path.read_text(encoding="utf-8"))
    errors = validate(payload)
    out = {
        "ok": not errors,
        "result_json": rel(result_path),
        "validator": rel(Path(__file__)),
        "validated_mode": payload.get("mode"),
        "errors": errors,
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }
    VALIDATOR_RESULT.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
