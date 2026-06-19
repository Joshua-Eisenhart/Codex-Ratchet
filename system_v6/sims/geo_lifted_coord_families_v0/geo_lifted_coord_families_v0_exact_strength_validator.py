#!/usr/bin/env python3
"""Packet-local validator for geo_lifted_coord_families_v0."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "geo_lifted_coord_families_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT = SIM_DIR / "results" / f"{SIM_ID}_envelope_results.json"
RUNG_KEYS = {str(n) for n in range(3, 9)}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    payload = json.loads(RESULT.read_text(encoding="utf-8"))
    errors: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    require(payload["schema_version"] == "three_engine_sim_result_v1", "schema drift")
    require(payload["all_pass"] is True, "all_pass is not true")
    require(payload["mode"] == "QUOTIENTED", "declared mode drift")
    require(payload["classification"] == "scratch_diagnostic", "classification drift")
    require(payload["promotion_allowed"] is False, "promotion_allowed drift")
    require(payload["formal_admission_allowed"] is False, "formal admission drift")
    require(all(payload["gate_pass"].values()), "one or more gate_pass rows failed")
    require(set(payload["lifted_source_exports"]) == RUNG_KEYS, "missing lifted rung source")

    for n, source in payload["lifted_source_exports"].items():
        path = ROOT / source["result_path"]
        require(path.exists(), f"lifted n{n} source missing")
        require(sha256(path) == source["result_sha256"], f"lifted n{n} source hash mismatch")
        require(f"stage_lifted_spinor_shell_n{n}_v0" in source["result_path"], f"n{n} source path drift")
        require(source["json_pointer"] == "/rows/P2_support_object/sites", f"n{n} does not point at exported sites")
        require(len(source["sites"]) == int(n), f"n{n} site count mismatch")

    for n, family in payload["families"].items():
        curve = family["w_site_weighted_family"]["site_entropy_curve"]
        require(len(curve) == int(n), f"n{n} entropy curve count mismatch")
        require(abs(family["w_site_weighted_family"]["probability_sum_numeric"] - 1.0) <= 1.0e-12, f"n{n} probabilities do not sum to one")
        require(payload["equal_eta_anchors"][n]["committed_rung_anchor_recovered"] is True, f"n{n} equal eta anchor failed")
        require(payload["density_quotient_rows"][n]["phase_erased"] is True, f"n{n} phase erased row missing")
        require(payload["density_quotient_rows"][n]["weights_survive"] is True, f"n{n} weights survive row missing")
        for site_id, control in payload["mutation_controls"][n].items():
            require(control["rerun_under_mutation"] is True, f"n{n} {site_id} mutation was not a rerun")
            require(control["changed_eta_sites"] == [site_id], f"n{n} {site_id} changed wrong eta sites")
            require(control["entropy_responds_at_mutated_site"] is True, f"n{n} {site_id} entropy did not respond")
            require(control["full_rerun_not_json_edit"] is True, f"n{n} {site_id} missing full-rerun marker")
        permutation = payload["permutation_controls"][n]
        require(permutation["rerun_under_site_permutation"] is True, f"n{n} permutation was not a rerun")
        require(permutation["probability_vector_permuted_accordingly"] is True, f"n{n} probability vector did not permute")
        require(permutation["entropy_vector_permuted_accordingly"] is True, f"n{n} entropy vector did not permute")
        require(permutation["full_rerun_not_json_edit"] is True, f"n{n} permutation missing full-rerun marker")
        require(bool(permutation["failure_semantics"]), f"n{n} permutation missing failure semantics")
        flat = payload["flat_family_controls"][n]
        require(flat["rerun_under_flat_family"] is True, f"n{n} flat-family was not a rerun")
        require(flat["coordinate_independent_family_detected"] is True, f"n{n} flat family was not detected")
        require(flat["detected_as_uncoupled"] is True, f"n{n} flat family was not marked uncoupled")
        require(flat["full_rerun_not_json_edit"] is True, f"n{n} flat-family missing full-rerun marker")
        require(bool(flat["failure_semantics"]), f"n{n} flat-family missing failure semantics")

    for solver in ("z3", "cvc5"):
        rows = payload["separability_boundary"][solver]
        require(set(rows) == RUNG_KEYS, f"{solver} missing rung boundary rows")
        for n, row in rows.items():
            require(row["actual_exported_eta_on_product_boundary"] == "unsat", f"{solver} n{n} actual boundary verdict drift")
            require(row["positive_product_boundary_control"] == "sat", f"{solver} n{n} positive control drift")
            require(row["invalid_zero_weight_vector_control"] == "unsat", f"{solver} n{n} invalid zero control drift")

    for name, record in payload["engines"].items():
        source = ROOT / record["source_path"]
        require(source.exists(), f"{name} source missing")
        require(sha256(source) == record["source_sha256"], f"{name} source hash mismatch")
        require(record["ran"] is True, f"{name} did not run")
        require(record["reads_peer_result"] is False, f"{name} reads peer result")
        require(record["classification"] == "scratch_diagnostic", f"{name} classification drift")
        require(record["promotion_allowed"] is False, f"{name} promotion drift")
        require(record["formal_admission_allowed"] is False, f"{name} formal admission drift")
        require(record["tool_calls"], f"{name} missing function-level tool_calls")
        load_bearing_tools = {tool for tool, level in record["tool_integration_depth"].items() if level == "load_bearing"}
        tool_call_tools = {call.get("tool") for call in record["tool_calls"]}
        require(tool_call_tools == load_bearing_tools, f"{name} tool_calls are not one-to-one with load-bearing tools")
        for call in record["tool_calls"]:
            for key in (
                "tool",
                "qualified_api",
                "input_object",
                "output_object",
                "positive_case",
                "negative_control",
                "boundary_case",
                "demotion_condition",
                "gates",
            ):
                require(key in call and call[key], f"{name} tool_call {call.get('tool')} missing {key}")

    require(payload["divergence"]["comparison"]["within_tolerance"] is True, "divergence not within tolerance")
    require(payload["crossover_proofs"]["z3"]["verdict"] == "unsat", "z3 crossover drift")
    require(payload["crossover_proofs"]["cvc5"]["verdict"] == "unsat", "cvc5 crossover drift")

    print(json.dumps({"ok": not errors, "errors": errors, "result_json": str(RESULT.relative_to(ROOT))}, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
