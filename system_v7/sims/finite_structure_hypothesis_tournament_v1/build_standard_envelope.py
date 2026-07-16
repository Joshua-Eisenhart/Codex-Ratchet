#!/usr/bin/env python3
"""Build the supplemental standard envelope from the green strict controller."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


BASE = Path(__file__).resolve().parent
REPO = BASE.parents[2]
RESULTS = BASE / "results"
OUT = RESULTS / "standard_engine_envelope.json"
sys.path.insert(0, str(REPO / "scripts"))

from build_three_engine_envelope import build_envelope


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict:
    def unique(pairs: list[tuple[str, object]]) -> dict:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate key in {path}: {key}")
            result[key] = value
        return result

    def finite(token: str) -> None:
        raise ValueError(f"non-finite value in {path}: {token}")

    value = json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=unique,
        parse_constant=finite,
    )
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain an object")
    return value


def main() -> int:
    spec_path = BASE / "spec.json"
    controller_path = RESULTS / "controller_result.json"
    julia_result_path = RESULTS / "julia_result.json"
    jax_result_path = RESULTS / "jax_result.json"
    smt_result_path = RESULTS / "smt_result.json"
    spec = load(spec_path)
    controller = load(controller_path)
    julia = load(julia_result_path)
    jax = load(jax_result_path)
    smt = load(smt_result_path)
    if controller.get("all_pass") is not True or controller["cross_runtime_comparison"]["mismatch_count"] != 0:
        raise ValueError("strict controller is not green and exact")
    if any(result.get("all_pass") is not True for result in (julia, jax, smt)):
        raise ValueError("one or more source receipts are red")

    append_ids = [
        "append_subgroup_A0_A1",
        "append_subgroup_A1_A2",
        "append_subgroup_A2_A3",
    ]
    append_rows = {row["id"]: row for row in smt["queries"] if row["id"] in append_ids}
    if set(append_rows) != set(append_ids):
        raise ValueError("missing append-subgroup composite member")
    if not all(
        append_rows[query_id][solver]["status"] == "unsat"
        for query_id in append_ids
        for solver in ("z3", "cvc5")
    ):
        raise ValueError("append-subgroup composite is not uniformly UNSAT")

    envelope = build_envelope(
        sim_id="finite_structure_hypothesis_tournament_v1",
        lanes={
            "julia": {
                "source_path": str((BASE / "run_julia.jl").relative_to(REPO)),
                "result_path": str(julia_result_path.relative_to(REPO)),
                "role_id": "julia_semantic_canon",
                "reads_peer_result": False,
                "packages_used": julia["packages_used"],
                "aligned_packages_load_bearing": ["Graphs"],
                "package_observables": {
                    "Graphs": "SCC partitions and directed-cycle membership gate V_persistent_support, V_exploratory_support, and MSS frontiers",
                },
                "tool_calls": julia["tool_receipts"],
                "tool_integration_depth": "load_bearing_with_independent_transitive_closure_ablation",
            },
            "jax": {
                "source_path": str((BASE / "run_jax.py").relative_to(REPO)),
                "result_path": str(jax_result_path.relative_to(REPO)),
                "role_id": "jax_batched_workhorse",
                "reads_peer_result": False,
                "packages_used": jax["packages_used"],
                "aligned_packages_load_bearing": ["jraph"],
                "package_observables": {
                    "jraph": "segment_sum outdegrees gate V_serial, V_branching, V_exploratory_support, and MSS frontiers",
                },
                "tool_calls": jax["tool_receipts"],
                "tool_integration_depth": "load_bearing_batched_recompute_with_edge_erasure_ablation",
            },
        },
        mode="julia_canon_jax_workhorse_smt_crossover",
        claim_path_tools=["Graphs", "jraph", "z3", "cvc5"],
        crossover_proofs={
            "scope": "append_subgroup_all_three_adjacent_pairs_only",
            "aggregation": "unsat iff every exact member query is unsat",
            "z3": {
                "ran": True,
                "verdict": "unsat",
                "load_bearing": True,
                "query_ids": append_ids,
            },
            "cvc5": {
                "ran": True,
                "verdict": "unsat",
                "load_bearing": True,
                "query_ids": append_ids,
            },
        },
        divergence={
            "metric": "exact_cross_lane_mismatch_count",
            "units": "canonical observable rows",
            "julia_authoritative": True,
            "engine_values": {"julia": 0, "jax": 0},
            "max_divergence": 0,
        },
        classification="scratch_diagnostic",
        promotion_allowed=False,
        formal_admission_allowed=False,
        parent_lineage={
            "spec_sha256": sha256(spec_path),
            "controller_sha256": sha256(controller_path),
            "preregistration_sha256": sha256(BASE / "preregistration_receipt.json"),
        },
        omitted_lanes={"pytorch": spec["engine_mode"]["pytorch"]},
        expected_lanes=("julia", "jax", "pytorch"),
        stability_pairs=[
            {"subtree": "strict_controller", "hash": sha256(controller_path)},
            {"subtree": "full_smt_receipt", "hash": sha256(smt_result_path)},
        ],
        generated_at="2026-07-15T07:56:37Z",
        lane_evidence={
            "julia": "independent_recompute",
            "jax": "independent_recompute",
        },
        extra_fields={
            "all_pass": True,
            "claim_ceiling": controller["claim_ceiling"],
            "source_spec_claim_ceiling": spec["claim_ceiling"],
            "blocked_consumers": spec["blocked_consumers"],
            "controls": controller["controls"],
            "scope_checks": controller["scope_checks"],
            "tool_intent": {
                "claim_classes": ["bounded typed finite-structure census"],
                "engine_tool_intent": {
                    "julia": {
                        "Graphs": "SCC/cycle viability and downstream MSS gating",
                    },
                    "jax": {
                        "jraph": "outdegree viability and downstream MSS gating",
                    },
                },
            },
            "tournament_controller": {
                "authoritative": True,
                "path": str(controller_path.relative_to(REPO)),
                "sha256": sha256(controller_path),
                "all_pass": True,
                "mismatch_count": 0,
                "controller_schema": controller["schema_version"],
                "corruption_control_count": len(controller["controls"]),
                "spec_engine_mode": spec["engine_mode"]["name"],
                "engines_not_innately_independent": True,
                "specific_recompute_lanes_independent": True,
            },
            "full_smt_crossover": {
                "authoritative_path": str(smt_result_path.relative_to(REPO)),
                "sha256": sha256(smt_result_path),
                "query_count": len(smt["queries"]),
                "mixed_status_vector_preserved": True,
                "warning": "crossover_proofs is only the three-query append-subgroup composite, not the verdict of the full mixed SAT/UNSAT campaign",
            },
        },
    )
    OUT.write_text(json.dumps(envelope, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": envelope["all_pass"], "output": str(OUT), "sha256": sha256(OUT)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
