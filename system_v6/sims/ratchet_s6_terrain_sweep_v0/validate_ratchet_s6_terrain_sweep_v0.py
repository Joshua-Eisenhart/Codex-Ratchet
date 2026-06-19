#!/usr/bin/env python3
"""Validate ratchet_s6_terrain_sweep_v0 result shape and build gates."""

from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
SIM_ID = "ratchet_s6_terrain_sweep_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
DEFAULT_RESULT = SIM_DIR / "results" / f"{SIM_ID}_envelope_results.json"
VALIDATOR_RESULT = SIM_DIR / "results" / f"{SIM_ID}_validator_results.json"

sys.path.insert(0, str(ROOT))
from scripts.builder_audit_boundary import builder_audit_boundary_errors  # noqa: E402

TERRAIN_ORDER = [
    "Ne_Spiral_R",
    "Ne_Vortex_L",
    "Ni_Pit_L",
    "Ni_Source_R",
    "Se_Cannon_R",
    "Se_Funnel_L",
    "Si_Citadel_R",
    "Si_Hill_L",
]

EXPECTED_TERRAIN_HASHES = {
    "Ne_Spiral_R": "890ac6990ff4158d0f2f7bf9c786aac832837bd9b84530219b763576e18214b4",
    "Ne_Vortex_L": "f7a01b371cb290c49e911ac477a244e29d9ae489ef0aec3c17c935c2f0c66218",
    "Ni_Pit_L": "6eff3605086c785fa80db6f2c56f258685a500249bb41d34cc8bdc048ebfa13e",
    "Ni_Source_R": "53103e38a21a630ef160a17355a2b55bedbc1faff74918bf1d8c8b47a08cc086",
    "Se_Cannon_R": "82eaa9e60bea7754402e70442c041a467b3546199fae3af0ddd013a2a5763433",
    "Se_Funnel_L": "25f78fc755e37729771e46eef26f6d80358dbcee06891917e2ebe82dcee5128a",
    "Si_Citadel_R": "059b6cbfe868456e2478a802252ed543c3bd046d4e2cd4f4d3d79a4cbf50c4be",
    "Si_Hill_L": "63c4862cc0414923ac5f4918f32a9c704f0050cb8d7e48830560b7b06b841676",
}

EXPECTED_PARENTS = {
    "ratchet_s6_terrain_operator_shell_v0",
    "ratchet_s1_single_shell_pilot_v0",
    "geo_disintegration_machinery_v0",
    "geo_s5_terrain_flows_v0",
    "geo_s4_operator_stage_v0",
    "geo_s2_s5_mode_sweep_v0",
}


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
    require(payload.get("classification") == "scratch_diagnostic", errors, "classification must be scratch_diagnostic")
    require(payload.get("promotion_allowed") is False, errors, "promotion_allowed must be false")
    require(payload.get("formal_admission_allowed") is False, errors, "formal_admission_allowed must be false")
    require(payload.get("all_pass") is True, errors, "all_pass must be true")

    parents = as_dict(payload.get("parent_lineage"), "parent_lineage", errors)
    require(set(parents) == EXPECTED_PARENTS, errors, "parent_lineage must contain the expected committed parents")
    for name in EXPECTED_PARENTS:
        parent = as_dict(parents.get(name), f"parent_lineage.{name}", errors)
        require(bool(parent.get("committed_tree")), errors, f"{name} committed_tree missing")
        require(bool(parent.get("envelope_sha256")), errors, f"{name} envelope_sha256 missing")
        require(bool(parent.get("top_source_sha256")), errors, f"{name} top_source_sha256 missing")

    fences = as_dict(payload.get("scope_fences"), "scope_fences", errors)
    require(fences.get("single_shell_only") is True, errors, "single_shell_only fence missing")
    require(fences.get("audit_verdict_emitted") is False, errors, "audit_verdict_emitted must be false")

    terrain_sweep = as_dict(payload.get("terrain_sweep"), "terrain_sweep", errors)
    require(list(terrain_sweep) == TERRAIN_ORDER, errors, "terrain_sweep order mismatch")
    for terrain_id in TERRAIN_ORDER:
        row = as_dict(terrain_sweep.get(terrain_id), f"terrain_sweep.{terrain_id}", errors)
        require(row.get("terrain_ab_sha256") == EXPECTED_TERRAIN_HASHES[terrain_id], errors, f"{terrain_id} hash mismatch")
        require("field_on_conditioned_leaf" in row, errors, f"{terrain_id} field missing")
        require("fixed_points" in row, errors, f"{terrain_id} fixed_points missing")
        require("order_gap_vs_Fi_R_x" in row, errors, f"{terrain_id} gap row missing")

    leakage = payload.get("leakage_table")
    survival = payload.get("fixed_point_survival_table")
    gaps = payload.get("order_gap_table")
    require(isinstance(leakage, list) and len(leakage) == 8, errors, "leakage_table must contain 8 rows")
    require(isinstance(survival, list) and len(survival) == 8, errors, "fixed_point_survival_table must contain 8 rows")
    require(isinstance(gaps, list) and len(gaps) == 8, errors, "order_gap_table must contain 8 rows")
    if isinstance(survival, list):
        require(all(row.get("survives_conditioning") is False for row in survival), errors, "no fixed point should survive conditioning")
    if isinstance(gaps, list):
        by_terrain = {row.get("terrain_id"): row for row in gaps}
        require(by_terrain.get("Se_Funnel_L", {}).get("norm_squared") == "4/25", errors, "Se_Funnel_L gap anchor mismatch")
        require(by_terrain.get("Se_Funnel_L", {}).get("delta") == ["2*sin(theta)/5", "0", "-2*cos(theta)/5"], errors, "Se_Funnel_L delta mismatch")
        require(by_terrain.get("Si_Citadel_R", {}).get("zero_for_all_theta") is True, errors, "Si_Citadel_R should be the zero R_x gap row")

    deliverable = as_dict(payload.get("sweep_deliverable"), "sweep_deliverable", errors)
    matrix = deliverable.get("matrix_8x_leakage_survival_gap")
    require(isinstance(matrix, list) and len(matrix) == 8, errors, "8x matrix must contain 8 like-for-like rows")
    compat = as_dict(deliverable.get("shell_compatible_vs_shell_breaking"), "shell_compatible_vs_shell_breaking", errors)
    require(compat.get("pure_shell_compatible") == [], errors, "no terrain should be pure-shell compatible")
    require(compat.get("density_z_leaf_preserved_but_pure_shell_breaking") == ["Si_Hill_L"], errors, "Si_Hill_L density-leaf row mismatch")
    require("shell_breaking" in compat and len(compat["shell_breaking"]) == 7, errors, "shell_breaking list must contain 7 rows")

    controls = as_dict(payload.get("controls"), "controls", errors)
    require(controls.get("nothing_excluded", {}).get("byte_exact") is True, errors, "nothing-excluded control must be byte-exact")
    require(controls.get("naive_conditioning_failure_refired", {}).get("pass") is True, errors, "naive-conditioning control must pass")
    require(controls.get("permuted_generator_control", {}).get("pass") is True, errors, "permuted-generator control must pass")
    require(controls.get("erased_skew_gap_control", {}).get("control_fired") is True, errors, "erased skew control must fire")
    require(controls.get("commuting_pair_kills_gap", {}).get("norm_squared") == "0", errors, "D_z/R_z anchor must be zero")

    template = as_dict(payload.get("template_anchor_reproduction"), "template_anchor_reproduction", errors)
    require(template.get("byte_exact") is True, errors, "template anchor must reproduce byte-exact")
    require(template.get("current_anchor", {}).get("order_gap_norm_squared") == "4/25", errors, "current anchor gap mismatch")

    proofs = as_dict(payload.get("crossover_proofs"), "crossover_proofs", errors)
    for solver in ("z3", "cvc5"):
        row = as_dict(proofs.get(solver), f"crossover_proofs.{solver}", errors)
        require(row.get("ran") is True, errors, f"{solver} must run")
        require(row.get("load_bearing") is True, errors, f"{solver} must be load-bearing")
        require(row.get("verdict") == "unsat", errors, f"{solver} positive verdict must be unsat")
        require(row.get("erased_flip_verdict") == "sat", errors, f"{solver} erased flip must be sat")
        require(row.get("commuting_control_verdict") == "unsat", errors, f"{solver} commuting control verdict must be unsat")
    julia_z3 = as_dict(proofs.get("julia_z3"), "crossover_proofs.julia_z3", errors)
    require(julia_z3.get("verdict") == "unsat", errors, "julia_z3 positive verdict must be unsat")
    require(julia_z3.get("erased_flip_verdict") == "sat", errors, "julia_z3 erased flip must be sat")

    calls = payload.get("tool_calls")
    require(isinstance(calls, list) and len(calls) == 4, errors, "tool_calls must contain exactly four rows")
    if isinstance(calls, list):
        require([call.get("tool") for call in calls] == ["sympy", "z3", "cvc5", "Z3"], errors, "tool call order mismatch")
        require(all(call.get("load_bearing") is True for call in calls), errors, "all tool calls must be load-bearing")
    require(payload.get("claim_path_tools") == ["sympy", "z3", "cvc5", "Z3"], errors, "claim_path_tools mismatch")

    gates = as_dict(payload.get("build_gates"), "build_gates", errors)
    for gate in (
        "mode_declared_ratcheted",
        "ceilings_preserved",
        "all_8_terrain_rows_present",
        "all_8_terrain_hashes_present",
        "leakage_table_8_rows",
        "fixed_survival_table_8_rows",
        "order_gap_table_8_rows",
        "no_fixed_points_survive_conditioning",
        "se_funnel_anchor_byte_exact",
        "commuting_controls_include_dz_rz_anchor",
        "natural_commuting_controls_zero",
        "naive_conditioning_failure_refired",
        "permuted_generator_breaks_anchor",
        "smt_positive_and_erased_flip",
        "smt_commuting_control_zero",
        "julia_result_loaded",
        "julia_source_hash_matches",
        "julia_reads_no_peer_result",
        "julia_engine_values_match_python_exact_rows",
        "julia_z3_load_bearing",
        "julia_z3_positive_and_erased_flip",
        "one_to_one_tool_calls",
    ):
        require(gates.get(gate) is True, errors, f"gate {gate} must be true")

    divergence = as_dict(payload.get("divergence"), "divergence", errors)
    require(divergence.get("julia_authoritative") is True, errors, "divergence.julia_authoritative must be true")
    require(divergence.get("max_divergence") == 0.0, errors, "max_divergence must be 0.0")
    engine_values = as_dict(divergence.get("engine_values"), "divergence.engine_values", errors)
    require(set(engine_values) == {"julia", "jax"}, errors, "engine_values must contain julia and jax")
    if set(engine_values) == {"julia", "jax"}:
        require(engine_values["julia"] == engine_values["jax"], errors, "julia and jax engine values must match")

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
        "validated_mode": payload.get("mode"),
        "errors": errors,
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }
    VALIDATOR_RESULT.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
