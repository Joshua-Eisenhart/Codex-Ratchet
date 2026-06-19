#!/usr/bin/env python3
"""Validate geo_s3_alternative_probe_families_v0 builder packet."""

from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "geo_s3_alternative_probe_families_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
DEFAULT_RESULT = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
JULIA_RESULT = RESULT_DIR / f"{SIM_ID}_julia_results.json"
VALIDATOR_RESULT = RESULT_DIR / f"{SIM_ID}_validator_results.json"

sys.path.insert(0, str(ROOT))
from scripts.builder_audit_boundary import builder_audit_boundary_errors  # noqa: E402


def rel(path: Path) -> str:
    if not path.is_absolute():
        path = ROOT / path
    return str(path.relative_to(ROOT))


def as_dict(value: Any, name: str, errors: list[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        errors.append(f"{name} must be an object")
        return {}
    return value


def require(condition: bool, errors: list[str], message: str) -> None:
    if not condition:
        errors.append(message)


def validate(payload: dict[str, Any], julia: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    require(payload.get("schema_version") == "three_engine_sim_result_v1", errors, "schema_version mismatch")
    require(payload.get("sim_id") == SIM_ID, errors, "sim_id mismatch")
    require(payload.get("classification") == "scratch_diagnostic", errors, "classification must be scratch_diagnostic")
    require(payload.get("promotion_allowed") is False, errors, "promotion_allowed must be false")
    require(payload.get("formal_admission_allowed") is False, errors, "formal_admission_allowed must be false")
    require(payload.get("all_pass") is True, errors, "all_pass must be true")
    contract = as_dict(payload.get("engine_contract"), "engine_contract", errors)
    require(contract.get("mode") == "julia_canon_plus_jax_diagnostic", errors, "engine_contract.mode mismatch")
    engines = as_dict(payload.get("engines"), "engines", errors)
    for engine in ("julia", "jax"):
        lane = as_dict(engines.get(engine), f"engines.{engine}", errors)
        for field in ("source_path", "source_sha256", "result_path", "result_sha256", "packages_used", "aligned_packages_load_bearing", "reads_peer_result"):
            require(field in lane, errors, f"engines.{engine}.{field} required")

    matrix = as_dict(payload.get("survival_matrix"), "survival_matrix", errors)
    expected = {"committed_pauli_xyz", "A_sic_tetrahedron", "B_mub_xyz", "C_single_axis_z", "D_random_frame_null"}
    require(set(matrix) == expected, errors, "survival_matrix family coverage mismatch")
    require(matrix.get("A_sic_tetrahedron", {}).get("frame_rank") == 4, errors, "SIC rank must be 4")
    require(matrix.get("B_mub_xyz", {}).get("frame_rank") == 4, errors, "MUB rank must be 4")
    require(matrix.get("C_single_axis_z", {}).get("frame_rank") == 2, errors, "single-axis rank must be 2")
    require(matrix.get("C_single_axis_z", {}).get("distinguished_pair_count", 99) < payload.get("battery", {}).get("total_pair_count", 0), errors, "single-axis must fail separation")
    require(matrix.get("D_random_frame_null", {}).get("null_deficiency", 0) > 0, errors, "null deficiency must be positive")

    answer = as_dict(payload.get("structural_answer"), "structural_answer", errors)
    require(answer.get("committed_pattern_unique_or_shared") == "shared_on_IC_rank_and_separation_unique_on_z_quotient_coarsening", errors, "structural answer mismatch")
    require(sorted(answer.get("ic_co_survivors", [])) == ["A_sic_tetrahedron", "B_mub_xyz", "committed_pauli_xyz"], errors, "IC co-survivors mismatch")
    require(answer.get("families_reproducing_committed_z_probe_classes") == ["C_single_axis_z"], errors, "z quotient reproducer mismatch")

    controls = as_dict(payload.get("controls"), "controls", errors)
    require(as_dict(controls.get("single_axis_fails_separation"), "controls.single_axis_fails_separation", errors).get("fires") is True, errors, "single-axis control must fire")
    require(as_dict(controls.get("rank_checks_exact"), "controls.rank_checks_exact", errors).get("pass") is True, errors, "exact rank control must pass")

    proofs = as_dict(payload.get("crossover_proofs"), "crossover_proofs", errors)
    for solver in ("z3", "cvc5"):
        proof = as_dict(proofs.get(solver), f"crossover_proofs.{solver}", errors)
        require(proof.get("ran") is True, errors, f"{solver} must run")
        require(proof.get("load_bearing") is True, errors, f"{solver} must be load-bearing")
        require(proof.get("verdict") == "sat", errors, f"{solver} verdict must be sat")
        require(proof.get("erased_verdict") == "unsat", errors, f"{solver} erased verdict must be unsat")
        require(proof.get("erased_flip_detected") is True, errors, f"{solver} erased flip must be detected")
        require(proof.get("asserted_precomputed_boolean") is False, errors, f"{solver} must not assert a precomputed boolean")

    gates = as_dict(payload.get("build_gates"), "build_gates", errors)
    for gate in (
        "classification_ceiling",
        "parent_lineage_hash_bound",
        "committed_anchor_reproduces_parent",
        "all_alternatives_evaluated",
        "single_axis_failure_fires",
        "rank_checks_exact",
        "quotient_classes_computed",
        "smt_positive_and_erased_flip",
        "julia_sidecar_pass",
        "julia_reads_no_peer_result",
        "julia_python_survival_hash_match",
        "one_to_one_tool_calls",
        "no_audit_verdict_written",
    ):
        require(gates.get(gate) is True, errors, f"build gate failed: {gate}")

    calls = payload.get("tool_calls")
    require(isinstance(calls, list), errors, "tool_calls must be a list")
    if isinstance(calls, list):
        require(sorted(call.get("tool") for call in calls) == sorted(payload.get("claim_path_tools", [])), errors, "tool_calls must match claim_path_tools")
        require(all(call.get("load_bearing") is True for call in calls), errors, "all tool_calls must be load-bearing")

    require(julia.get("all_pass") is True, errors, "julia all_pass must be true")
    require(julia.get("reads_peer_result") is False, errors, "julia must not read peer result")
    divergence = as_dict(payload.get("divergence"), "divergence", errors)
    require(divergence.get("python_engine_values_hash") == divergence.get("julia_engine_values_hash"), errors, "python/julia engine hash mismatch")
    return errors


def main(argv: list[str]) -> int:
    result_path = Path(argv[1]) if len(argv) > 1 else DEFAULT_RESULT
    if not result_path.is_absolute():
        result_path = ROOT / result_path
    payload = json.loads(result_path.read_text(encoding="utf-8"))
    julia = json.loads(JULIA_RESULT.read_text(encoding="utf-8")) if JULIA_RESULT.exists() else {}
    errors = validate(payload, julia)
    errors.extend(builder_audit_boundary_errors(payload, SIM_DIR / "audit_verdict.md"))
    out = {
        "ok": not errors,
        "validator_ok": not errors,
        "declared_mode": "julia_canon_plus_jax_diagnostic",
        "declared_modes_ok": True,
        "sim_id": SIM_ID,
        "result_path": rel(result_path),
        "validator": rel(Path(__file__)),
        "errors": errors,
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    VALIDATOR_RESULT.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
