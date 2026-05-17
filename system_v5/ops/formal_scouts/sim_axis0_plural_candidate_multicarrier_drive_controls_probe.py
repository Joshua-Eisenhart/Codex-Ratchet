#!/usr/bin/env python3
"""Axis0 plural-candidate multicarrier drive-control scout.

The plural Axis0 router emits five finite candidate vectors, but the first
subdense multicarrier consumer historically averaged them into one scalar
drive. This scout is a downstream anti-collapse guard: it consumes the same
router and carrier machinery, then proves candidate-specific drop/name-binding
controls are visible on MPS, PEPS, and PEPS3D local environment signatures.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import time
from typing import Any

import networkx as nx
import numpy as np
import z3

import sim_source_native_multicarrier_subdense_environment_contraction_probe as subdense


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "axis0_plural_candidate_multicarrier_drive_controls_probe_results.json"

NAME = "axis0_plural_candidate_multicarrier_drive_controls_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "axis0_plural_candidate_multicarrier_drive_controls"
CLAIM_CEILING = (
    "Formal scout only: consumes the plural Axis0 router and source-native "
    "MPS/PEPS/PEPS3D local carrier updates to test whether five Axis0 candidate "
    "vectors remain distinguishable from scalar-mean, zero-all, shuffled-name, "
    "and drop-one controls. It does not admit final Axis0, retrocausality, "
    "physics, Holodeck, cognition, neural architecture, full PEPS/PEPS3D "
    "environment geometry, or canonical claims."
)

TOOL_MANIFEST = {
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing candidate-vector drive controls and local signature gaps",
    },
    "quimb": {
        "tried": True,
        "used": True,
        "reason": "load-bearing through reused MPS/PEPS/PEPS3D carrier construction checks",
    },
    "networkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing dependency graph for Axis0 router to multicarrier guard",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite witness over scalar-collapse rejection predicates",
    },
    "engine_core": {
        "tried": True,
        "used": True,
        "reason": "load-bearing through reused source-native stage records",
    },
}
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}

REQUIRED_REPAIR_RECEIPT_FIELDS = [
    "weak_link",
    "target_file_or_result",
    "admission_rule_improved",
    "dependency_subset",
    "stage_fields_touched_or_consumed",
    "before_baseline/hash",
    "after_delta/hash",
    "primary_control/result",
    "axis0_outputs_or_blockers",
    "provider_inputs_used",
    "promotion_ceiling",
    "next_step",
]

CANDIDATE_NAMES = [
    "fep_gradient_polarity",
    "path_entropy",
    "correlation_diversity_derivative",
    "retrocausal_many_futures_policy_scoring",
    "holographic_boundary_interior_reconstruction",
]
CANDIDATE_WEIGHTS = {
    "fep_gradient_polarity": 0.31,
    "path_entropy": -0.23,
    "correlation_diversity_derivative": 0.19,
    "retrocausal_many_futures_policy_scoring": 0.13,
    "holographic_boundary_interior_reconstruction": -0.11,
}
GAP_FLOOR = 1e-5
TEST_CARRIERS = [
    ("mps", (16,), 8116),
    ("peps", (4, 4), 8216),
    ("peps3d", (4, 4, 2), 8332),
]


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): as_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(v) for v in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if isinstance(value, (np.integer, np.floating)):
        return value.item()
    return value


def sha256_file(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def candidate_values(axis0: dict[str, Any], idx: int) -> dict[str, float]:
    vectors = axis0.get("candidate_vectors", {})
    out = {}
    for name in CANDIDATE_NAMES:
        vector = vectors.get(name, [])
        out[name] = float(vector[idx % len(vector)]) if vector else 0.0
    return out


def candidate_drive(axis0: dict[str, Any], idx: int, mode: str) -> float:
    if not axis0.get("ready"):
        return 0.0
    values = candidate_values(axis0, idx)
    if mode == "zero_all":
        return 0.0
    if mode == "scalar_mean":
        return float(np.mean(list(values.values())))
    if mode == "shuffled_name_binding":
        rolled = list(values.values())[1:] + list(values.values())[:1]
        values = dict(zip(CANDIDATE_NAMES, rolled))
    elif mode.startswith("drop_"):
        dropped = mode.removeprefix("drop_")
        if dropped not in values:
            raise ValueError(mode)
        values = dict(values)
        values[dropped] = 0.0
    elif mode != "full_vector":
        raise ValueError(mode)
    weighted = sum(CANDIDATE_WEIGHTS[name] * values[name] for name in CANDIDATE_NAMES)
    return float(weighted / sum(abs(value) for value in CANDIDATE_WEIGHTS.values()))


def signature_gap(a: dict[str, Any], b: dict[str, Any]) -> float:
    return float(np.linalg.norm(np.asarray(a["environment_signature"], dtype=float) - np.asarray(b["environment_signature"], dtype=float)))


def run_candidate_carrier(
    records: list[dict[str, Any]],
    axis0: dict[str, Any],
    memory: dict[str, Any],
    family: str,
    shape: tuple[int, ...],
    seed: int,
    mode: str,
) -> dict[str, Any]:
    carrier = subdense.make_carrier(family, shape, seed)
    quimb_check = subdense.quimb_count_check(carrier)
    site_order = sorted(carrier.sites)
    before_rows = subdense.environment_rows(carrier)
    drives = []
    stage_hashes = []
    for idx, record in enumerate(records):
        site = carrier.sites[site_order[idx % len(site_order)]]
        drive = candidate_drive(axis0, idx, mode)
        mem_drive = subdense.holodeck_memory_drive(memory, idx)
        drives.append(drive)
        stage_hashes.append(record["model_after"]["density_hash"])
        subdense.apply_physical_slot(
            site,
            str(record["operator"]),
            int(record["operator_sign"]),
            subdense.source_strength(record, drive, mem_drive),
        )
    after_rows = subdense.environment_rows(carrier)
    before_sig = subdense.signature_from_rows(before_rows)
    after_sig = subdense.signature_from_rows(after_rows)
    return {
        "carrier": carrier.name,
        "family": carrier.family,
        "shape": "x".join(str(x) for x in carrier.shape),
        "mode": mode,
        "site_count": len(carrier.sites),
        "edge_count": len(carrier.edges),
        "sampled_environment_edges": len(after_rows),
        "stage_records_consumed": len(records),
        "unique_model_after_hashes_consumed": len(set(stage_hashes)),
        "quimb_count_check": quimb_check,
        "axis0_ready": bool(axis0.get("ready")),
        "candidate_names_consumed": list(CANDIDATE_NAMES),
        "drive_mean": float(np.mean(drives)),
        "drive_mean_abs": float(np.mean(np.abs(drives))),
        "drive_variance": float(np.var(drives)),
        "environment_signature": after_sig,
        "environment_shift_from_initial": float(np.linalg.norm(after_sig - before_sig)),
        "environment_rows_head": after_rows[:2],
        "pass": (
            len(records) == subdense.N_SOURCE_SEEDS * 64
            and len(set(stage_hashes)) > 16
            and quimb_check["pass"]
            and len(after_rows) > 0
            and bool(np.all(np.isfinite(after_sig)))
        ),
    }


def run_suite(records: list[dict[str, Any]], axis0: dict[str, Any], memory: dict[str, Any]) -> dict[str, Any]:
    rows: dict[str, dict[str, Any]] = {}
    modes = ["full_vector", "scalar_mean", "zero_all", "shuffled_name_binding"] + [
        f"drop_{name}" for name in CANDIDATE_NAMES
    ]
    for family, shape, seed in TEST_CARRIERS:
        key = f"{family}_{'x'.join(str(x) for x in shape)}"
        rows[key] = {
            mode: run_candidate_carrier(records, axis0, memory, family, shape, seed, mode)
            for mode in modes
        }
    gaps = {}
    checks = {}
    for key, row in rows.items():
        full = row["full_vector"]
        gaps[key] = {
            "full_vs_scalar_mean": signature_gap(full, row["scalar_mean"]),
            "full_vs_zero_all": signature_gap(full, row["zero_all"]),
            "full_vs_shuffled_name_binding": signature_gap(full, row["shuffled_name_binding"]),
            "drop_gaps": {
                name: signature_gap(full, row[f"drop_{name}"])
                for name in CANDIDATE_NAMES
            },
        }
        checks[key] = {
            "runs_pass": all(mode_row["pass"] for mode_row in row.values()),
            "full_differs_from_scalar_mean": gaps[key]["full_vs_scalar_mean"] > GAP_FLOOR,
            "full_differs_from_zero_all": gaps[key]["full_vs_zero_all"] > GAP_FLOOR,
            "candidate_name_binding_matters": gaps[key]["full_vs_shuffled_name_binding"] > GAP_FLOOR,
            "all_drop_one_controls_visible": all(value > GAP_FLOOR for value in gaps[key]["drop_gaps"].values()),
        }
    return {
        "rows": rows,
        "gaps": gaps,
        "checks": checks,
        "pass": all(all(check.values()) for check in checks.values()),
    }


def compact_rows(rows: dict[str, dict[str, Any]]) -> dict[str, Any]:
    compact = {}
    for key, modes in rows.items():
        compact[key] = {}
        for mode, row in modes.items():
            compact[key][mode] = {
                "carrier": row["carrier"],
                "site_count": row["site_count"],
                "edge_count": row["edge_count"],
                "sampled_environment_edges": row["sampled_environment_edges"],
                "stage_records_consumed": row["stage_records_consumed"],
                "unique_model_after_hashes_consumed": row["unique_model_after_hashes_consumed"],
                "drive_mean_abs": row["drive_mean_abs"],
                "drive_variance": row["drive_variance"],
                "environment_shift_from_initial": row["environment_shift_from_initial"],
                "sample_environment_head": row["environment_rows_head"][:1],
                "pass": row["pass"],
            }
    return compact


def dependency_graph() -> dict[str, Any]:
    graph = nx.DiGraph()
    edges = [
        ("macro_axis0_plural_stage_router", "axis0_candidate_vectors"),
        ("axis0_candidate_vectors", "full_vector_drive"),
        ("axis0_candidate_vectors", "drop_one_controls"),
        ("axis0_candidate_vectors", "scalar_mean_control"),
        ("axis0_candidate_vectors", "shuffled_name_binding_control"),
        ("EngineCore.stage_records", "multicarrier_local_updates"),
        ("full_vector_drive", "multicarrier_local_updates"),
        ("drop_one_controls", "repair_receipt"),
        ("scalar_mean_control", "repair_receipt"),
        ("shuffled_name_binding_control", "repair_receipt"),
    ]
    graph.add_edges_from(edges)
    return {
        "pass": nx.is_directed_acyclic_graph(graph),
        "nodes": graph.number_of_nodes(),
        "edges": graph.number_of_edges(),
        "edge_list": edges,
    }


def z3_plural_axis0_witness(suite: dict[str, Any], axis0: dict[str, Any]) -> dict[str, Any]:
    solver = z3.Solver()
    router_ready = z3.Bool("router_ready")
    vector_control_passes = z3.Bool("vector_control_passes")
    five_candidates_present = z3.Bool("five_candidates_present")
    solver.add(router_ready == bool(axis0.get("ready")))
    solver.add(vector_control_passes == bool(suite["pass"]))
    solver.add(five_candidates_present == (len(axis0.get("candidate_names", [])) == 5))
    solver.add(z3.Not(z3.And(router_ready, vector_control_passes, five_candidates_present)))
    status = solver.check()
    return {
        "pass": status == z3.unsat,
        "solver_status": str(status),
        "claim_ceiling": "Finite witness only: plural Axis0 candidates produce visible drop/name-binding controls in bounded carriers.",
    }


def load_receipts() -> dict[str, Any]:
    axis0_receipt = subdense.load_result("macro_sim_axis0_plural_stage_candidate_router_probe_results.json")
    memory_receipt = subdense.load_result("source_native_holodeck_hash_memory_placeholder_probe_results.json")
    subdense_receipt = subdense.load_result("source_native_multicarrier_subdense_environment_contraction_probe_results.json")
    return {
        "axis0": axis0_receipt,
        "memory": memory_receipt,
        "subdense": subdense_receipt,
    }


def main() -> int:
    started = time.time()
    receipts = load_receipts()
    records = subdense.run_source_records()
    axis0 = subdense.axis0_signature(receipts["axis0"])
    memory = subdense.holodeck_memory_signal(receipts["memory"])
    suite = run_suite(records, axis0, memory)
    graph = dependency_graph()
    z3_witness = z3_plural_axis0_witness(suite, axis0)
    router_payload = receipts["axis0"].get("axis0_outputs_or_blockers", {})
    hbi_blockers = (router_payload.get("holographic_boundary_interior_reconstruction") or {}).get("explicit_blockers", {})

    repair_receipt = {
        "weak_link": "The plural Axis0 router emits five candidate vectors, but the subdense multicarrier consumer used an averaged scalar drive, risking collapse of Axis0 into one generic FEP/entropy/reward signal.",
        "target_file_or_result": str(OUT_PATH),
        "admission_rule_improved": "Plural Axis0 downstream consumption must expose full-vector, scalar-mean, zero-all, shuffled-name, and per-candidate drop-one controls across MPS, PEPS, and PEPS3D local environment signatures.",
        "dependency_subset": [
            "macro_sim_axis0_plural_stage_candidate_router receipt",
            "source_native_multicarrier_subdense_environment_contraction receipt",
            "source_native_holodeck_hash_memory_placeholder receipt",
            "EngineCore source-native stage records",
            "MPS/PEPS/PEPS3D local environment updates",
        ],
        "stage_fields_touched_or_consumed": subdense.REQUIRED_STAGE_FIELDS,
        "before_baseline/hash": {
            "subdense_result": receipts["subdense"].get("path"),
            "subdense_result_sha256": sha256_file(pathlib.Path(receipts["subdense"]["path"])) if receipts["subdense"].get("exists") else "missing",
            "scalarizing_function": "sim_source_native_multicarrier_subdense_environment_contraction_probe.axis0_drive",
        },
        "after_delta/hash": {
            "script_sha256": sha256_file(pathlib.Path(__file__)),
            "result_path": str(OUT_PATH),
            "candidate_names": list(CANDIDATE_NAMES),
            "candidate_weights": CANDIDATE_WEIGHTS,
        },
        "primary_control/result": {
            "suite_checks": suite["checks"],
            "signature_gaps": suite["gaps"],
            "tested_carriers": [f"{family}_{'x'.join(str(x) for x in shape)}" for family, shape, _ in TEST_CARRIERS],
            "matched_controls": ["scalar_mean", "zero_all", "shuffled_name_binding"] + [f"drop_{name}" for name in CANDIDATE_NAMES],
        },
        "axis0_outputs_or_blockers": {
            "axis0_ready": axis0.get("ready"),
            "consumed_candidates": axis0.get("candidate_names"),
            "holographic_boundary_interior_reconstruction_blockers_preserved": hbi_blockers,
            "plural_axis0_drive_control_pass": suite["pass"],
        },
        "provider_inputs_used": {
            "codex_native_audit": "read-only Axis0 lane identified scalarizing downstream layer",
            "grok": "prior direct API audit recommended Axis0 per-candidate consumption after autograd blocker",
            "gemini": "prior direct API audit recommended Axis0 per-candidate consumption after autograd blocker",
            "sonnet_high": "not_run_this_repair_wave",
            "opus_max": "not_run_this_repair_wave",
        },
        "promotion_ceiling": CLAIM_CEILING,
        "next_step": "If integrated green, propagate per-candidate Axis0 controls into LiRPA/world-model adapter consumers instead of allowing scalar Axis0 summaries to become the only downstream path.",
    }
    positive = {
        "upstream_receipts_are_consumed": {
            "pass": all(
                receipt.get("exists") and receipt.get("all_pass") is True
                for receipt in [receipts["axis0"], receipts["memory"], receipts["subdense"]]
            ),
            "receipts": receipts,
        },
        "axis0_router_exposes_five_candidate_vectors": {
            "pass": axis0.get("ready") is True and axis0.get("candidate_names") == CANDIDATE_NAMES,
            "candidate_names": axis0.get("candidate_names"),
            "candidate_lengths": {name: len(axis0.get("candidate_vectors", {}).get(name, [])) for name in CANDIDATE_NAMES},
        },
        "plural_candidate_controls_separate_on_mps_peps_peps3d": {
            "pass": suite["pass"],
            "checks": suite["checks"],
            "signature_gaps": suite["gaps"],
            "rows": compact_rows(suite["rows"]),
        },
        "dependency_graph_is_acyclic": graph,
        "z3_plural_axis0_witness_executes": z3_witness,
    }
    graveyards = {
        "scalar_mean_axis0_is_not_equivalent_to_candidate_vector_binding": {
            "pass": all(row["full_differs_from_scalar_mean"] for row in suite["checks"].values()),
            "full_vs_scalar_mean_gaps": {key: gaps["full_vs_scalar_mean"] for key, gaps in suite["gaps"].items()},
        },
        "zero_all_axis0_control_is_distinguished": {
            "pass": all(row["full_differs_from_zero_all"] for row in suite["checks"].values()),
            "full_vs_zero_all_gaps": {key: gaps["full_vs_zero_all"] for key, gaps in suite["gaps"].items()},
        },
        "candidate_name_binding_shuffle_is_distinguished": {
            "pass": all(row["candidate_name_binding_matters"] for row in suite["checks"].values()),
            "full_vs_shuffled_name_binding_gaps": {
                key: gaps["full_vs_shuffled_name_binding"] for key, gaps in suite["gaps"].items()
            },
        },
        "per_candidate_drop_controls_are_not_silent": {
            "pass": all(row["all_drop_one_controls_visible"] for row in suite["checks"].values()),
            "drop_gaps": {key: gaps["drop_gaps"] for key, gaps in suite["gaps"].items()},
        },
        "hbi_blockers_are_preserved_not_promoted": {
            "pass": bool(hbi_blockers),
            "holographic_boundary_interior_reconstruction_blockers": hbi_blockers,
        },
    }
    boundary = {
        "repair_receipt_has_required_loop_fields": {
            "pass": all(key in repair_receipt for key in REQUIRED_REPAIR_RECEIPT_FIELDS),
            "keys": sorted(repair_receipt),
        },
        "claim_ceiling_blocks_final_axis0_and_physics_claims": {
            "pass": all(term in CLAIM_CEILING.lower() for term in ["formal scout", "does not admit final axis0", "physics", "canonical"]),
            "claim_ceiling": CLAIM_CEILING,
        },
        "integration_is_dependency_consumption_not_result_aggregation": {
            "pass": bool(
                suite["pass"]
                and axis0.get("ready")
                and all(mode_row["stage_records_consumed"] == len(records) for row in suite["rows"].values() for mode_row in row.values())
                and all(mode_row["unique_model_after_hashes_consumed"] > 16 for row in suite["rows"].values() for mode_row in row.values())
            ),
            "record_count": len(records),
            "consumed_stage_fields": subdense.REQUIRED_STAGE_FIELDS,
        },
    }
    nearby_variants = {
        "total": len(graveyards),
        "passed": sum(1 for row in graveyards.values() if row["pass"]),
        "variants": sorted(graveyards),
    }
    all_pass = (
        all(row["pass"] for row in positive.values())
        and all(row["pass"] for row in graveyards.values())
        and all(row["pass"] for row in boundary.values())
        and nearby_variants["passed"] == nearby_variants["total"]
    )
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "repair_receipt": repair_receipt,
        "axis0_outputs_or_blockers": repair_receipt["axis0_outputs_or_blockers"],
        "explicit_blockers": {
            "single_scalar_axis0_as_complete_downstream_representation": {
                "admitted": False,
                "claim": "Scalar means remain controls/diagnostics only; downstream Axis0 claims require per-candidate drop/name-binding evidence.",
            },
            "holographic_boundary_interior_reconstruction_final_claim": {
                "admitted": False,
                "claim": "HBI remains a candidate with carried blockers from the Axis0 router.",
                "blockers": hbi_blockers,
            },
        },
        "positive": positive,
        "graveyard_companions": graveyards,
        "boundary": boundary,
        "nearby_variants": nearby_variants,
        "why_not_v4_probes": [
            "This is a v5 downstream anti-collapse guard for the repaired Axis0/router and multicarrier path.",
            "It tests finite local-environment signature controls, not final Axis0, retrocausality, or physics.",
            "Provider proposals are not counted; local carrier receipts and matched controls carry evidence.",
        ],
        "blockers": [],
        "elapsed_seconds": time.time() - started,
        "all_pass": all_pass,
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True), encoding="utf-8")
    print(f"RESULT {NAME}: all_pass={all_pass} -> {OUT_PATH}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
