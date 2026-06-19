#!/usr/bin/env python3
"""Envelope for twistor_incidence_finite_packet_v0."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
SIM_ID = "twistor_incidence_finite_packet_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_envelope.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"

CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
MODE = "julia_canon_plus_jax_diagnostic"
COMMON_VALUE_KEYS = [
    "point_count",
    "line_count",
    "projective_class_count",
    "raw_nonzero_vector_count",
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
    "z3_no_two_point_line_intersection_unsat",
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
        "controls_fired": {name: record.get("fired", False) for name, record in payload["controls"].items()},
        "kill_condition_met": payload["kill_condition_met"],
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
        "schema_mismatch_reported_not_worked_around": proc.returncode != 0,
    }


def build_result(include_validator: bool = False) -> dict[str, Any]:
    legs = {engine: load_leg(engine) for engine in ("julia", "jax")}
    pin_ok = len({payload["pin_block_sha256"] for payload in legs.values()}) == 1
    gates = {f"G{i}" for i in range(1, 8)}
    all_gates_present = all(gates <= set(payload["gates"]) for payload in legs.values())
    all_gate_acceptance = all(all(payload["gate_pass"].get(gate, False) for gate in gates) for payload in legs.values())
    controls_required = {"scramble-incidence", "random-bipartite-graph", "drop-projective-quotient", "orientation-reversal", "label-shuffle"}
    controls_fired = all(all(payload["controls"].get(name, {}).get("fired", False) for name in controls_required) for payload in legs.values())
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
    baseline_ok = all(payload["baseline"]["sample_sizes"] == {"probe_rows": 15, "relation_nodes": 35} for payload in legs.values())
    separation_rows = legs["jax"]["separation_table"]
    separation_ok = any(row["separation"] for row in separation_rows)
    non_separating_rows_ok = all(
        {row["readout"]: row["separation"] for row in payload["separation_table"]}.get(readout) is False
        for payload in legs.values()
        for readout in ("quotient_classes", "relation_components", "pencil_structure")
    )
    clique_explanation_ok = all(payload["max_clique_structural_explanation"]["computed_split_ok"] for payload in legs.values())
    label_shuffle_ok = all(
        payload["controls"]["label-shuffle"]["unlabeled_invariants_survive_shuffle"] is True
        and payload["controls"]["label-shuffle"]["graph_invariants_survive_labeled_comparison_superseded"] is False
        for payload in legs.values()
    )
    kill_condition_met = not separation_ok
    smt_ok = (
        legs["jax"]["crossover_proofs"]["z3"]["verdict"] == "unsat"
        and legs["jax"]["crossover_proofs"]["cvc5"]["verdict"] == "unsat"
        and legs["jax"]["gates"]["G6"]["scrambled_controls"]["z3"]["verdict"] == "sat"
        and legs["jax"]["gates"]["G6"]["scrambled_controls"]["cvc5"]["verdict"] == "sat"
        and legs["julia"]["crossover_proofs"]["julia_z3"]["verdict"] == "unsat"
    )
    div = divergence(legs)
    all_pass = all(
        [
            all(payload["all_pass"] for payload in legs.values()),
            pin_ok,
            all_gates_present,
            all_gate_acceptance,
            controls_fired,
            ceiling_ok,
            baseline_ok,
            separation_ok,
            non_separating_rows_ok,
            clique_explanation_ok,
            label_shuffle_ok,
            not kill_condition_met,
            smt_ok,
            div["comparison"]["within_tolerance"],
        ]
    )
    result = {
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
            "omitted_lanes": {"pytorch": "declared diagnostic mode per system_v6/README.md:11; no graph/network/autograd claim path"},
            "audit_order": ["combined_envelope", "julia_local", "jax_local", "controller_comparison"],
            "reads_peer_result": False,
        },
        "claim_path_tools": ["Z3", "z3", "cvc5"],
        "engines": {engine: engine_record(payload) for engine, payload in legs.items()},
        "crossover_proofs": {
            "z3": legs["jax"]["crossover_proofs"]["z3"],
            "cvc5": legs["jax"]["crossover_proofs"]["cvc5"],
            "julia_z3": legs["julia"]["crossover_proofs"]["julia_z3"],
        },
        "divergence": div,
        "pin_block_sha256": next(iter({payload["pin_block_sha256"] for payload in legs.values()})),
        "pin_identical_across_legs": pin_ok,
        "controls_fired": controls_fired,
        "gates_present": sorted(gates),
        "gate_acceptance": all_gate_acceptance,
        "strict_gate_notes": {
            "G4": "q=2 scalar quotient ablation is identity; packet reports q2 limitation and flags q=3 as the discriminating scalar-quotient case",
        },
        "baseline_like_for_like": legs["jax"]["baseline"],
        "separation_table": separation_rows,
        "non_separating_rows_ok": non_separating_rows_ok,
        "max_clique_structural_explanation": {
            "julia": legs["julia"]["max_clique_structural_explanation"],
            "jax": legs["jax"]["max_clique_structural_explanation"],
            "same_across_legs": same_across_legs(legs, "max_clique_structural_explanation"),
            "computed_split_ok": clique_explanation_ok,
        },
        "label_shuffle_invariance": {
            "julia": legs["julia"]["controls"]["label-shuffle"],
            "jax": legs["jax"]["controls"]["label-shuffle"],
            "corrected_field": "unlabeled_invariants_survive_shuffle",
            "superseded_field": "graph_invariants_survive_labeled_comparison_superseded",
            "corrected_invariants_survive": label_shuffle_ok,
        },
        "q3_next_discriminator": legs["jax"]["q3_next_discriminator"],
        "kill_condition_met": kill_condition_met,
        "summary": {
            "finite_object": "PG(3,2) projective points and lines with twistor-style incidence dictionary",
            "non_separating_rows": ["quotient_classes", "relation_components", "pencil_structure"],
            "surviving_separation": "finite reconstruction behavior only",
            "surviving_separation_rows": [row["readout"] for row in separation_rows if row["separation"]],
            "ceiling": CLASSIFICATION,
            "promotion_allowed": False,
            "formal_admission_allowed": False,
            "fences": ["alt math discriminator only", "no spacetime/GR/physics claim", "no Penrose-validates language", "not canon"],
            "fence": "finite reconstruction behavior only; no physics, no spacetime manifold, no GR, no Penrose-validates claim",
            "q3_next_discriminator": legs["jax"]["q3_next_discriminator"],
        },
        "validator_outcome_recorded": maybe_validator_outcome() if include_validator else {"ran": False, "reason": "written after envelope construction on first pass"},
    }
    return result


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    first = build_result(include_validator=False)
    RESULT_PATH.write_text(json.dumps(first, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    final = build_result(include_validator=True)
    RESULT_PATH.write_text(json.dumps(final, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        f"TWISTOR_INCIDENCE_FINITE_PACKET_V0_ENVELOPE_DONE all_pass={final['all_pass']} "
        f"mode={MODE} max_divergence={final['divergence']['max_divergence']} "
        f"kill={final['kill_condition_met']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
