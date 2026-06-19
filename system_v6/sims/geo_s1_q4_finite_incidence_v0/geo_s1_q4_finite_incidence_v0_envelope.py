#!/usr/bin/env python3
"""Envelope for geo_s1_q4_finite_incidence_v0."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
SIM_ID = "geo_s1_q4_finite_incidence_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_envelope.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"

CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
MODE = "julia_canon_plus_jax_diagnostic"
COMMON_VALUE_KEYS = [
    "raw_nonzero_vector_count",
    "projective_class_count",
    "point_count",
    "line_count",
    "plane_count",
    "points_per_line_min",
    "points_per_line_max",
    "lines_through_point_min",
    "lines_through_point_max",
    "points_per_plane_min",
    "points_per_plane_max",
    "lines_per_plane_min",
    "lines_per_plane_max",
    "pair_count",
    "pair_line_count_min",
    "pair_line_count_max",
    "null_graph_components",
    "null_graph_edge_count",
    "null_graph_degree_min",
    "null_graph_degree_max",
    "null_graph_clique_number",
    "null_graph_max_clique_count",
    "null_graph_max_clique_point_pencil_count",
    "null_graph_max_clique_plane_line_set_count",
    "recovered_point_count",
    "reconstruction_mismatch_count",
    "frobenius_moved_projective_point_count",
    "z3_pair_uniqueness_unsat",
]


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_leg(engine: str) -> dict[str, Any]:
    path = RESULT_DIR / f"{SIM_ID}_{engine}_results.json"
    return json.loads(path.read_text(encoding="utf-8"))


def engine_record(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "ran": True,
        "source_path": payload["source_path"],
        "source_sha256": payload["source_sha256"],
        "result_path": payload["result_path"],
        "packages_used": payload["packages_used"],
        "aligned_packages_load_bearing": payload["aligned_packages_load_bearing"],
        "reads_peer_result": payload["reads_peer_result"],
        "classification": payload["classification"],
        "promotion_allowed": payload["promotion_allowed"],
        "formal_admission_allowed": payload["formal_admission_allowed"],
        "mode": payload["mode"],
        "values": payload["values"],
        "gate_pass": payload["gate_pass"],
        "pin_block_sha256": payload["pin_block_sha256"],
        "controls_fired": {name: record.get("fired", record.get("control_fired", record.get("pass", False))) for name, record in payload["controls"].items()},
        "kill_condition_met": payload["kill_condition_met"],
        "seeds": payload["seeds"],
    }


def divergence(legs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    rows = []
    max_div = 0.0
    max_key = None
    for key in COMMON_VALUE_KEYS:
        values = {engine: float(payload["values"][key]) for engine, payload in legs.items()}
        diff = max(values.values()) - min(values.values())
        rows.append({"key": key, "values": values, "max_abs_diff": diff})
        if diff > max_div:
            max_div = diff
            max_key = key
    return {
        "julia_authoritative": True,
        "engine_values": {engine: payload["values"] for engine, payload in legs.items()},
        "max_divergence": max_div,
        "max_divergence_key": max_key,
        "comparison": {
            "common_observable_count": len(COMMON_VALUE_KEYS),
            "rows": rows,
            "same_named_observable_sets": True,
            "within_tolerance": max_div <= 1.0e-8,
        },
    }


def same_across_legs(legs: dict[str, dict[str, Any]], key: str) -> bool:
    return len({json.dumps(payload[key], sort_keys=True) for payload in legs.values()}) == 1


def maybe_validator_outcome() -> dict[str, Any]:
    if not RESULT_PATH.exists():
        return {"ran": False, "reason": "envelope_result_not_written_yet"}
    cmd = [sys.executable, "scripts/validate_three_engine_sim_result.py", str(RESULT_PATH)]
    proc = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, check=False)
    return {
        "ran": True,
        "cmd": cmd,
        "exit_code": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
        "ok": proc.returncode == 0,
    }


def build_result(include_validator: bool = False) -> dict[str, Any]:
    legs = {engine: load_leg(engine) for engine in ("julia", "jax")}
    pin_ok = len({payload["pin_block_sha256"] for payload in legs.values()}) == 1
    div = divergence(legs)
    gates = {
        "G1_pg34_counts",
        "G2_pair_line_uniqueness",
        "G3_graph_invariants",
        "G4_projective_quotient_boundary",
        "G5_reconstruction_separation",
        "G6_frobenius_boundary",
    }
    all_gates_present = all(gates <= set(payload["gates"]) for payload in legs.values())
    all_gate_acceptance = all(all(payload["gate_pass"].get(gate, False) for gate in gates) for payload in legs.values())
    ceiling_ok = all(
        payload["classification"] == CLASSIFICATION
        and payload["promotion_allowed"] is False
        and payload["formal_admission_allowed"] is False
        and payload["claim_ceiling"]["alt_math_discriminator_only"]
        and payload["claim_ceiling"]["no_spacetime_gr_physics_claim"]
        and payload["claim_ceiling"]["no_penrose_validates_language"]
        and payload["claim_ceiling"]["not_canon"]
        for payload in legs.values()
    )
    controls_ok = all(
        payload["controls"]["drop-projective-quotient"]["q4_discriminator_fired"]
        and payload["controls"]["drop-projective-quotient"]["strictly_stronger_than_q3"]
        and payload["controls"]["scramble-incidence"]["control_fired"]
        and payload["controls"]["frobenius-boundary"]["pass"]
        for payload in legs.values()
    )
    geometry_ok = all(
        payload["values"]["raw_nonzero_vector_count"] == 255
        and payload["values"]["point_count"] == 85
        and payload["values"]["line_count"] == 357
        and payload["values"]["plane_count"] == 85
        and payload["values"]["pair_line_count_min"] == payload["values"]["pair_line_count_max"] == 1
        and payload["values"]["null_graph_edge_count"] == 17850
        and payload["values"]["null_graph_degree_min"] == payload["values"]["null_graph_degree_max"] == 100
        for payload in legs.values()
    )
    clique_ok = all(payload["clique_family_check"]["computed_split_ok"] for payload in legs.values())
    recon_ok = all(payload["reconstruction"]["pass"] for payload in legs.values())
    frob_ok = all(payload["frobenius_boundary"]["pass"] for payload in legs.values())
    separation_ok = all(
        any(row["readout"] == "reconstruction_behavior" and row["separation"] and row["status_vs_q3"] == "strengthens" for row in payload["separation_table"])
        and any(row["readout"] == "projective_scalar_quotient" and row["separation"] and row["status_vs_q3"] == "strengthens" for row in payload["separation_table"])
        and any(row["readout"] == "char2_frobenius_boundary" and row["separation"] for row in payload["separation_table"])
        for payload in legs.values()
    )
    smt_ok = (
        legs["jax"]["crossover_proofs"]["z3"]["verdict"] == "unsat"
        and legs["jax"]["crossover_proofs"]["cvc5"]["verdict"] == "unsat"
        and legs["jax"]["gates"]["G2_pair_line_uniqueness"]["scrambled_controls"]["z3"]["verdict"] == "sat"
        and legs["jax"]["gates"]["G2_pair_line_uniqueness"]["scrambled_controls"]["cvc5"]["verdict"] == "sat"
        and legs["julia"]["crossover_proofs"]["julia_z3"]["verdict"] == "unsat"
        and legs["julia"]["gates"]["G2_pair_line_uniqueness"]["scrambled_controls"]["z3"]["verdict"] == "sat"
    )
    all_pass = all(
        [
            all(payload["all_pass"] for payload in legs.values()),
            pin_ok,
            all_gates_present,
            all_gate_acceptance,
            ceiling_ok,
            controls_ok,
            geometry_ok,
            clique_ok,
            recon_ok,
            frob_ok,
            separation_ok,
            smt_ok,
            div["comparison"]["within_tolerance"],
        ]
    )
    return {
        "schema_version": "three_engine_sim_result_v1",
        "sim_id": SIM_ID,
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "all_pass": all_pass,
        "source_path": str(SOURCE_PATH),
        "source_sha256": sha256_file(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "engine_contract": {
            "mode": MODE,
            "lanes": ["julia", "jax"],
            "omitted_lanes": {"pytorch": "declared diagnostic mode; no graph/network/autograd claim path"},
            "audit_order": ["combined_envelope", "julia_local", "jax_local", "controller_comparison"],
            "reads_peer_result": False,
        },
        "claim_path_tools": ["galois", "Z3", "z3", "cvc5"],
        "engines": {engine: engine_record(payload) for engine, payload in legs.items()},
        "crossover_proofs": {
            "z3": legs["jax"]["crossover_proofs"]["z3"],
            "cvc5": legs["jax"]["crossover_proofs"]["cvc5"],
            "julia_z3": legs["julia"]["crossover_proofs"]["julia_z3"],
        },
        "divergence": div,
        "pin_block_sha256": next(iter({payload["pin_block_sha256"] for payload in legs.values()})),
        "pin_identical_across_legs": pin_ok,
        "gates_present": sorted(gates),
        "gate_acceptance": all_gate_acceptance,
        "controls_fired": controls_ok,
        "pg34_exact_invariants": {
            "raw_nonzero_vectors": 255,
            "point_count": 85,
            "line_count": 357,
            "plane_count": 85,
            "pair_line_uniqueness": True,
            "line_intersection_graph": {"vertices": 357, "edges": 17850, "degree": 100, "components": 1},
            "star_plane_cliques": {"point_stars": 85, "plane_line_sets": 85, "clique_size": 21},
        },
        "frobenius_boundary": {
            "julia": legs["julia"]["frobenius_boundary"],
            "jax": legs["jax"]["frobenius_boundary"],
            "same_across_legs": same_across_legs(legs, "frobenius_boundary"),
        },
        "separation_table": legs["jax"]["separation_table"],
        "q2_anchor": legs["jax"]["q2_anchor"],
        "q3_anchor": legs["jax"]["q3_anchor"],
        "q4_discriminating_answer": {
            "reconstruction_behavior": "persists",
            "projective_scalar_quotient": "strengthens: raw/projective ratio 3.0 versus q=3 ratio 2.0 and q=2 ratio 1.0",
            "char2_frobenius_boundary": "new non-prime-field boundary: nontrivial Frobenius preserves incidence",
            "line_graph": "regular connected line-intersection graph has 357 vertices, 17850 edges, degree 100",
            "ceiling": CLASSIFICATION,
        },
        "kill_condition_met": not separation_ok,
        "summary": {
            "finite_object": "PG(3,4) exact projective incidence over GF(4)",
            "surviving_separation": "finite reconstruction persists; quotient discrimination strengthens; Frobenius boundary holds",
            "honest_status": "persist/strengthen on the like-for-like rows; no weakening observed in the emitted q=4 checks",
            "fence": "scratch diagnostic only; no physics, spacetime, GR, bridge, axis, manifold, or Penrose-validation claim",
        },
        "validator_outcome_recorded": maybe_validator_outcome() if include_validator else {"ran": False, "reason": "written after envelope construction on first pass"},
    }


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    first = build_result(include_validator=False)
    RESULT_PATH.write_text(json.dumps(first, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    final = build_result(include_validator=True)
    RESULT_PATH.write_text(json.dumps(final, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        f"GEO_S1_Q4_FINITE_INCIDENCE_V0_ENVELOPE_DONE all_pass={final['all_pass']} "
        f"mode={MODE} max_divergence={final['divergence']['max_divergence']} "
        f"validator_ok={final['validator_outcome_recorded'].get('ok')} kill={final['kill_condition_met']}"
    )
    return 0 if final["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
