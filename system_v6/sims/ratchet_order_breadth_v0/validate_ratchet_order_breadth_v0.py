#!/usr/bin/env python3
"""Validate ratchet_order_breadth_v0 result shape and bounded gates."""

from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "ratchet_order_breadth_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
DEFAULT_RESULT = SIM_DIR / "results" / f"{SIM_ID}_envelope_results.json"
VALIDATOR_RESULT = SIM_DIR / "results" / f"{SIM_ID}_validator_results.json"
EXPECTED_PARENTS = {
    "ratchet_deep_chain_v0",
    "ratchet_s1_single_shell_pilot_v0",
    "ratchet_s2_two_shell_flux_v0",
    "ratchet_s6_terrain_operator_shell_v0",
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
    require(payload.get("sim_id") == SIM_ID, errors, "sim_id mismatch")
    require(payload.get("mode") == "RATCHETED", errors, "mode must be RATCHETED")
    require(payload.get("classification") == "scratch_diagnostic", errors, "classification must be scratch_diagnostic")
    require(payload.get("promotion_allowed") is False, errors, "promotion_allowed must be false")
    require(payload.get("formal_admission_allowed") is False, errors, "formal_admission_allowed must be false")
    require(payload.get("all_pass") is True, errors, "all_pass must be true")

    parents = as_dict(payload.get("parent_lineage"), "parent_lineage", errors)
    require(set(parents) == EXPECTED_PARENTS, errors, "parent_lineage must contain exactly the requested committed parents")
    for name in EXPECTED_PARENTS:
        parent = as_dict(parents.get(name), f"parent_lineage.{name}", errors)
        for key in ("committed_tree", "committed_commit", "envelope_sha256", "top_source_sha256", "allowed_use"):
            require(bool(parent.get(key)), errors, f"{name}.{key} missing")

    table = as_dict(payload.get("ratchet_order_breadth"), "ratchet_order_breadth", errors)
    rows = table.get("orderings")
    require(isinstance(rows, list) and len(rows) == 24, errors, "order table must contain all 24 orderings")
    if isinstance(rows, list):
        require(len({row.get("ordering") for row in rows}) == 24, errors, "orderings must be unique")
        require(all(set(row.get("tokens", [])) == {"L", "Z", "W", "T"} for row in rows), errors, "each row must use L/Z/W/T exactly")
    summary = as_dict(table.get("summary"), "summary", errors)
    require(summary.get("orderings_total") == 24, errors, "summary.orderings_total must be 24")
    require(summary.get("live_orderings") == 5, errors, "summary.live_orderings must be 5")
    require(summary.get("mortality_orderings") == 19, errors, "summary.mortality_orderings must be 19")
    require(summary.get("distinct_live_outcomes") == 2, errors, "distinct_live_outcomes must be 2")
    require(summary.get("distinct_mortality_classes") == 3, errors, "distinct_mortality_classes must be 3")
    require(summary.get("total_equivalence_classes_including_mortality") == 5, errors, "total class count must be 5")

    classes = as_dict(table.get("equivalence_classes"), "equivalence_classes", errors)
    live = as_dict(classes.get("live"), "equivalence_classes.live", errors)
    mortality = as_dict(classes.get("mortality"), "equivalence_classes.mortality", errors)
    require(classes.get("relation") == "order_blind_object_signature_sha256", errors, "live equivalence relation must use order-blind object signatures")
    require(len(live) == 2, errors, "live order-blind class count mismatch")
    require(set(mortality) == {"M1_phase_without_leaf", "M2_terrain_without_leaf", "M3_raw_window_then_Z4"}, errors, "mortality class ids mismatch")
    live_ordering_sets = [set(value.get("orderings", [])) for value in live.values() if isinstance(value, dict)]
    require({"LZWT", "ZLWT"} in live_ordering_sets, errors, "L/Z commuting pair must collapse to one order-blind class")
    require({"LZTW", "LTZW", "ZLTW"} in live_ordering_sets, errors, "T/W precedence survivor class mismatch")
    live_rows = [row for row in rows or [] if row.get("status") == "survived"] if isinstance(rows, list) else []
    require(len({row.get("class_signature_sha256") for row in live_rows}) == 2, errors, "live order-blind signatures must collapse to two classes")
    lz_signatures = {row.get("class_signature_sha256") for row in live_rows if row.get("ordering") in {"LZWT", "ZLWT"}}
    require(len(lz_signatures) == 1, errors, "L/Z commuting anchor must be same order-blind signature")
    require(len(mortality.get("M1_phase_without_leaf", {}).get("orderings", [])) == 8, errors, "M1 count mismatch")
    require(len(mortality.get("M2_terrain_without_leaf", {}).get("orderings", [])) == 8, errors, "M2 count mismatch")
    require(len(mortality.get("M3_raw_window_then_Z4", {}).get("orderings", [])) == 3, errors, "M3 count mismatch")

    structural = as_dict(payload.get("structural_answer"), "structural_answer", errors)
    require(structural.get("k_distinct_live_outcomes") == 2, errors, "k must be 2")
    require(structural.get("m_mortality_orderings") == 19, errors, "m mortality ordering count must be 19")
    require(structural.get("m_distinct_mortality_classes") == 3, errors, "m distinct mortality class count must be 3")
    require(structural.get("total_equivalence_classes_including_mortality") == 5, errors, "structural total class count must be 5")

    anchors = as_dict(payload.get("anchors"), "anchors", errors)
    projection = as_dict(anchors.get("committed_chain_projection_byte_exact"), "committed_chain_projection_byte_exact", errors)
    require(projection.get("byte_exact") is True, errors, "committed-chain projection must be byte-exact")
    require(anchors.get("commuting_pair_swap", {}).get("gap") == 0, errors, "commuting pair gap must be zero")
    require(anchors.get("commuting_pair_swap", {}).get("coarse_class_same") is True, errors, "commuting pair coarse class anchor missing")
    require(anchors.get("commuting_pair_swap", {}).get("order_blind_same") is True, errors, "commuting pair must collapse order-blind signatures")
    require(anchors.get("known_noncommuting_swap", {}).get("mortality_class") == "M3_raw_window_then_Z4", errors, "noncommuting anchor mismatch")
    terrain = as_dict(anchors.get("terrain_gap_anchor"), "terrain_gap_anchor", errors)
    require(terrain.get("order_gap_norm_squared") == "4/25", errors, "terrain gap must be 4/25")
    require(terrain.get("commuting_control_gap_norm_squared") == "0", errors, "terrain commuting control must be 0")

    proofs = as_dict(payload.get("crossover_proofs"), "crossover_proofs", errors)
    for solver in ("z3", "cvc5"):
        proof = as_dict(proofs.get(solver), f"crossover_proofs.{solver}", errors)
        require(proof.get("ran") is True, errors, f"{solver} must run")
        require(proof.get("load_bearing") is True, errors, f"{solver} must be load-bearing")
        require(proof.get("verdict") == "unsat", errors, f"{solver} positive verdict must be unsat")
        require(proof.get("erased_flip_verdict") == "sat", errors, f"{solver} erased flip must be sat")
        require(proof.get("erased_flip_detected") is True, errors, f"{solver} erased flip missing")
        require(proof.get("identity") == "live_classes + mortality_classes = 5 with order-blind table counts bound as context", errors, f"{solver} identity must be corrected")
        bound = as_dict(proof.get("bound_values"), f"{solver}.bound_values", errors)
        require(bound.get("live_classes") == 2, errors, f"{solver} live class binding must be 2")
        require(bound.get("mortality_classes") == 3, errors, f"{solver} mortality class binding must be 3")
    julia_z3 = as_dict(proofs.get("julia_z3"), "julia_z3", errors)
    require(julia_z3.get("verdict") == "unsat", errors, "Julia Z3 verdict must be unsat")
    require(julia_z3.get("erased_flip_verdict") == "sat", errors, "Julia Z3 erased flip must be sat")
    require(julia_z3.get("identity") == "live_classes + mortality_classes = 5 with order-blind table counts bound as context", errors, "Julia Z3 identity must be corrected")

    calls = payload.get("tool_calls")
    require(isinstance(calls, list) and len(calls) == 4, errors, "tool_calls must contain exactly four rows")
    if isinstance(calls, list):
        require([call.get("tool") for call in calls] == ["sympy", "z3", "cvc5", "Z3"], errors, "tool call order mismatch")
        require(all(call.get("load_bearing") is True for call in calls), errors, "all tool calls must be load-bearing")
    require(payload.get("claim_path_tools") == ["sympy", "z3", "cvc5", "Z3"], errors, "claim_path_tools mismatch")

    engines = as_dict(payload.get("engines"), "engines", errors)
    require(set(engines) == {"julia", "jax"}, errors, "engines must contain scoped julia and jax")
    for engine_name in ("julia", "jax"):
        engine = as_dict(engines.get(engine_name), f"engines.{engine_name}", errors)
        require(engine.get("ran") is True, errors, f"{engine_name}.ran must be true")
        require(engine.get("reads_peer_result") is False, errors, f"{engine_name}.reads_peer_result must be false")
        require(bool(engine.get("source_path")), errors, f"{engine_name}.source_path required")
        require(bool(engine.get("aligned_packages_load_bearing")), errors, f"{engine_name}.aligned load-bearing required")

    divergence = as_dict(payload.get("divergence"), "divergence", errors)
    require(divergence.get("julia_authoritative") is True, errors, "julia_authoritative must be true")
    require(divergence.get("max_divergence") == 0.0, errors, "max_divergence must be zero")
    engine_values = as_dict(divergence.get("engine_values"), "divergence.engine_values", errors)
    if set(engine_values) == {"julia", "jax"}:
        require(engine_values["julia"] == engine_values["jax"], errors, "Julia and Python rows must match")
    else:
        errors.append("engine_values must contain julia and jax")

    gates = as_dict(payload.get("build_gates"), "build_gates", errors)
    for gate in (
        "mode_declared_ratcheted",
        "ceilings_preserved",
        "parent_lineage_present",
        "all_24_orderings_present",
        "order_class_table_present",
        "committed_chain_projection_byte_exact",
        "commuting_pair_anchor_recovered",
        "live_order_blind_class_count_is_2",
        "commuting_pair_order_blind_same",
        "known_noncommuting_anchor_recovered",
        "terrain_gap_anchor_recovered",
        "smt_positive_and_erased_flip",
        "julia_result_loaded",
        "julia_reads_no_peer_result",
        "julia_source_hash_matches",
        "julia_engine_values_match_python_exact_rows",
        "one_to_one_tool_calls",
        "audit_verdict_md_builder_fix_addendum_allowed",
        "geo_s9_alternative_connections_v0_untouched",
    ):
        require(gates.get(gate) is True, errors, f"gate {gate} must be true")
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
    VALIDATOR_RESULT.parent.mkdir(parents=True, exist_ok=True)
    VALIDATOR_RESULT.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
