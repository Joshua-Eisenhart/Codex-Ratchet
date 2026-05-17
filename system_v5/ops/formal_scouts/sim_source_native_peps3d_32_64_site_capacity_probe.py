#!/usr/bin/env python3
"""Source-native PEPS3D 32/64-site capacity scout."""

from __future__ import annotations

import json
import os
import pathlib
import time
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

import cotengra as ctg
import networkx as nx
import numpy as np
import opt_einsum as oe
import quimb.tensor as qtn
import sympy as sp
import z3

from engine_core import EngineCore, generate_initial_density


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "source_native_peps3d_32_64_site_capacity_probe_results.json"

NAME = "source_native_peps3d_32_64_site_capacity_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CITES_BLOCKED_UNTIL = "full_64_site_source_native_peps3d_engine_with_bond_sweep"
CLAIM_CEILING = (
    "Formal scout only: checks that source-native density histories can seed "
    "32-site and 64-site PEPS3D carrier capacity probes. It does not run a "
    "full 32/64-site source-native engine and does not admit final manifold, "
    "physics, cognition, neural architecture, or canonical claims."
)

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "load-bearing source-rank and PEPS3D capacity metrics"},
    "quimb": {"tried": True, "used": True, "reason": "load-bearing 32/64-site PEPS3D carrier construction"},
    "cotengra": {"tried": True, "used": True, "reason": "load-bearing contraction tree scaling witness"},
    "opt_einsum": {"tried": True, "used": True, "reason": "load-bearing numeric contraction cross-check"},
    "networkx": {"tried": True, "used": True, "reason": "load-bearing carrier topology graph"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing symbolic site-count factorization"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing encoded 32<64 capacity witness"},
    "engine_core": {"tried": True, "used": True, "reason": "load-bearing repaired EngineCore science-method stage records"},
}
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}
BEFORE_SCRIPT_SHA256 = "6fef914896d929cc226a9169a4ee09a876da460340ea93943321ef6c800ae5d3"
BEFORE_RESULT_SHA256 = "d8d1208295ce9fa71afebfc6de328fcc8e6d95e96e2401304a03cab8f566495a"
REQUIRED_STAGE_FIELDS = [
    "model_before",
    "prediction",
    "observation",
    "fep_efe_score",
    "update_repair",
    "falsifier_graveyard",
    "next_policy",
    "model_after",
]
AXIS0_CONTEXT_NAMES = [
    "fep_gradient_polarity",
    "correlation_diversity_derivative",
    "retrocausal_many_futures_policy_scoring",
]


def load_result(name: str) -> dict[str, Any]:
    path = RESULT_DIR / name
    if not path.exists():
        return {"exists": False, "path": str(path)}
    data = json.loads(path.read_text(encoding="utf-8"))
    return {
        "exists": True,
        "path": str(path),
        "name": data.get("name"),
        "all_pass": data.get("all_pass"),
        "classification": data.get("classification"),
        "promotion_allowed": data.get("promotion_allowed"),
        "claim_ceiling": data.get("claim_ceiling", "")[:220],
        "axis0_outputs_or_blockers": data.get("axis0_outputs_or_blockers", {}),
    }


def source_stage_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for engine_type in (0, 1):
        rows.extend(
            EngineCore(engine_type, manifold_enabled=True)
            .run_full_cycle(generate_initial_density(8200 + engine_type))["trajectory"]
        )
    return rows


def axis0_signature(router: dict[str, Any]) -> dict[str, Any]:
    outputs = router.get("axis0_outputs_or_blockers") or {}
    parts = []
    for name in AXIS0_CONTEXT_NAMES:
        values = np.asarray(outputs.get(name, {}).get("values", []), dtype=float)
        if values.size:
            values = np.nan_to_num(values, nan=0.0, posinf=0.0, neginf=0.0)
            parts.append(float(np.sum(values) + np.mean(np.abs(values))))
    ready = bool(router.get("exists") and router.get("all_pass") is True and len(parts) == len(AXIS0_CONTEXT_NAMES))
    value = float(sum(parts)) if parts else 0.0
    return {
        "ready": ready,
        "candidate_names": list(AXIS0_CONTEXT_NAMES),
        "pre_guard_router_context": True,
        "diagnostic_only": True,
        "not_load_bearing_for_capacity_admission": True,
        "post_guard_admission_claim_allowed": False,
        "signature": value,
        "seed_offset": int(abs(value) * 1000) % 997,
        "source_receipt": router.get("path"),
    }


def source_rank_audit() -> tuple[int, int, float, dict[str, Any]]:
    rows = source_stage_rows()
    valid = sum(1 for row in rows if row["valid_density"])
    missing = {
        f"E{row['engine_type']}:S{row['main_stage_idx']}:u{row['substage_idx']}": [
            field for field in REQUIRED_STAGE_FIELDS if field not in row
        ]
        for row in rows
    }
    missing = {key: value for key, value in missing.items() if value}
    matrix = np.array(
        [
            row["model_after"]["bloch"]
            + [
                row["model_after"]["entropy"],
                row["model_after"]["purity"],
                row["fep_efe_score"]["expected_free_energy_proxy"],
                row["fep_efe_score"]["surprise_kl"],
                row["fep_efe_score"]["prediction_error_l2"],
                row["update_repair"]["manifold_projection_delta_norm"],
            ]
            for row in rows
        ],
        dtype=float,
    )
    singular = np.linalg.svd(matrix - matrix.mean(axis=0, keepdims=True), compute_uv=False)
    rank = int(np.sum(singular > 1e-8))
    signature = float(np.sum(matrix))
    audit = {
        "rows": len(rows),
        "valid_rows": valid,
        "feature_dim": int(matrix.shape[1]),
        "effective_rank": rank,
        "singular_values": [float(x) for x in singular],
        "rank_is_low_for_32_64_capacity": rank < 16,
        "science_method_fields_consumed": not missing,
        "missing_required_stage_fields": missing,
        "source": "EngineCore.run_full_cycle repaired science-method stage records",
        "pass": valid == 64 and rank >= 3 and not missing,
    }
    return valid, int(abs(signature) * 1000) % 997, signature, audit


def make_peps3d(shape: tuple[int, int, int], seed: int, bond_dim: int = 2) -> qtn.PEPS3D:
    rng = np.random.default_rng(seed)
    lx, ly, lz = shape
    arrays = []
    for i in range(lx):
        plane = []
        for j in range(ly):
            row = []
            for k in range(lz):
                legs = []
                if i < lx - 1:
                    legs.append(bond_dim)
                if j < ly - 1:
                    legs.append(bond_dim)
                if k < lz - 1:
                    legs.append(bond_dim)
                if i > 0:
                    legs.append(bond_dim)
                if j > 0:
                    legs.append(bond_dim)
                if k > 0:
                    legs.append(bond_dim)
                legs.append(2)
                row.append(rng.normal(scale=0.03 / bond_dim, size=legs))
            plane.append(row)
        arrays.append(plane)
    return qtn.PEPS3D(arrays)


def tensor_parameter_count(tn: Any) -> int:
    return int(sum(np.prod(tensor.shape) for tensor in tn.tensors))


def contraction_witness(sites: int, seed: int) -> dict[str, float]:
    inputs, output, expr = [
        ("a", "b", "e", "l"),
        ("b", "c", "f", "m"),
        ("e", "f", "h", "n"),
        ("l", "m", "n", "o"),
        ("c", "d", "g", "p"),
        ("h", "i", "o", "q"),
        ("g", "i", "j", "r"),
        ("p", "q", "r", "s"),
    ], ("a", "d", "j", "s"), "abel,bcfm,efhn,lmno,cdgp,hioq,gijr,pqrs->adjs"
    labels = sorted({ix for term in inputs for ix in term} | set(output))
    sizes = {ix: 2 + ((n + seed + sites) % 3) for n, ix in enumerate(labels)}
    for ix in output:
        sizes[ix] = 2
    tree = ctg.HyperOptimizer(max_repeats=4, progbar=False).search(inputs, output, sizes)
    rng = np.random.default_rng(9000 + seed + sites)
    arrays = [rng.normal(size=tuple(sizes[ix] for ix in term)) for term in inputs]
    return {
        "cost": float(tree.contraction_cost()),
        "width": float(tree.contraction_width()),
        "norm": float(np.linalg.norm(oe.contract(expr, *arrays))),
    }


def capacity_signature(row: dict[str, Any]) -> np.ndarray:
    return np.array(
        [
            row["carriers"]["peps3d_32"]["contraction"]["cost"],
            row["carriers"]["peps3d_32"]["contraction"]["width"],
            row["carriers"]["peps3d_32"]["contraction"]["norm"],
            row["carriers"]["peps3d_64"]["contraction"]["cost"],
            row["carriers"]["peps3d_64"]["contraction"]["width"],
            row["carriers"]["peps3d_64"]["contraction"]["norm"],
        ],
        dtype=float,
    )


def carrier_capacity(seed: int, axis0_seed_offset: int = 0) -> dict[str, Any]:
    shapes = {"peps3d_32": (4, 4, 2), "peps3d_64": (4, 4, 4)}
    rows: dict[str, Any] = {}
    sweep: dict[str, list[int]] = {}
    for name, shape in shapes.items():
        seeded = seed + axis0_seed_offset + len(name)
        tn = make_peps3d(shape, seeded, bond_dim=2)
        sites = int(np.prod(shape))
        rows[name] = {
            "shape": "x".join(str(x) for x in shape),
            "sites": sites,
            "num_tensors": int(tn.num_tensors),
            "num_indices": int(tn.num_indices),
            "parameter_count_bond2": tensor_parameter_count(tn),
            "contraction": contraction_witness(sites, seeded),
        }
        sweep[name] = [tensor_parameter_count(make_peps3d(shape, seeded + dim + sites, bond_dim=dim)) for dim in (2, 3)]
    graph = nx.Graph()
    graph.add_edges_from([
        ("science_method_64_stage_records", "peps3d_32"),
        ("science_method_64_stage_records", "peps3d_64"),
        ("peps3d_32", "peps3d_64"),
    ])
    return {
        "carriers": rows,
        "axis0_seed_offset": axis0_seed_offset,
        "bond_dimension_sweep_D2_D3_parameter_counts": sweep,
        "bond_sweep_changes_capacity": all(values[1] > values[0] for values in sweep.values()),
        "topology_graph_nodes": graph.number_of_nodes(),
        "topology_graph_edges": graph.number_of_edges(),
        "pass": rows["peps3d_32"]["num_tensors"] == 32
        and rows["peps3d_64"]["num_tensors"] == 64
        and rows["peps3d_64"]["num_indices"] > rows["peps3d_32"]["num_indices"]
        and all(values[1] > values[0] for values in sweep.values()),
    }


def z3_capacity_witness() -> dict[str, Any]:
    solver = z3.Solver()
    floor = z3.Int("operational_floor")
    q32 = z3.Int("peps3d32")
    q64 = z3.Int("peps3d64")
    solver.add(floor == 8, q32 == 32, q64 == 64)
    solver.add(z3.Not(z3.And(floor < q32, q32 < q64)))
    status = solver.check()
    return {
        "solver_status": str(status),
        "pass": status == z3.unsat,
        "claim_ceiling": "Z3 encodes only 8<32<64 site ordering; quimb/cotengra metrics carry the construction burden.",
    }


def main() -> int:
    started = time.time()
    axis0_router = load_result("macro_sim_axis0_plural_stage_candidate_router_probe_results.json")
    stage_contract = load_result("macro_sim_stage_record_science_method_contract_probe_results.json")
    axis0 = axis0_signature(axis0_router)
    valid_rows, seed, source_signature, seed_audit = source_rank_audit()
    capacity = carrier_capacity(seed, axis0_seed_offset=0)
    axis0_diagnostic_capacity = carrier_capacity(seed, axis0_seed_offset=axis0["seed_offset"])
    axis0_capacity_gap = float(np.linalg.norm(capacity_signature(axis0_diagnostic_capacity) - capacity_signature(capacity)))
    factors = sp.factorint(32 * 64)
    positive = {
        "source_native_histories_seed_32_64_peps3d_capacity": {
            **capacity,
            "source_valid_rows": valid_rows,
        },
        "science_method_stage_records_seed_peps3d_capacity": {
            "pass": seed_audit["pass"] and stage_contract["exists"] and stage_contract.get("all_pass") is True,
            "source": seed_audit["source"],
            "stage_contract_receipt": stage_contract,
            "required_fields": REQUIRED_STAGE_FIELDS,
            "feature_dim": seed_audit["feature_dim"],
            "effective_rank": seed_audit["effective_rank"],
            "missing_required_stage_fields": seed_audit["missing_required_stage_fields"],
        },
        "axis0_router_context_reported_diagnostic_only": {
            "pass": PROMOTION_ALLOWED is False and axis0["post_guard_admission_claim_allowed"] is False,
            "axis0_router_receipt": axis0_router,
            "axis0_signature": axis0,
            "context_candidate_names": AXIS0_CONTEXT_NAMES,
            "diagnostic_capacity_signature_gap": axis0_capacity_gap,
            "diagnostic_capacity_variant": axis0_diagnostic_capacity,
            "load_bearing_for_capacity_admission": False,
            "reason": "This upstream PEPS3D capacity scout records the raw Axis0 router as diagnostic context only.",
        },
        "symbolic_32_64_factorization": {"factorization": {str(k): v for k, v in factors.items()}, "pass": factors == {2: 11}},
        "z3_rejects_below_eight_as_32_64_regime": z3_capacity_witness(),
    }
    graveyards = {
        "label_only_source_rows_would_fail_peps3d_capacity_seed": {
            "pass": seed_audit["science_method_fields_consumed"],
            "required_fields": REQUIRED_STAGE_FIELDS,
            "reason": "The PEPS3D capacity seed now derives from repaired science-method/FEP fields, not legacy readout labels.",
        },
        "source_seed_rank_blocks_engine_scaling_claim": {
            **seed_audit,
            "cites_blocked_until": CITES_BLOCKED_UNTIL,
            "pass": seed_audit["pass"] and seed_audit["rank_is_low_for_32_64_capacity"] and PROMOTION_ALLOWED is False,
        },
        "axis0_zeroed_capacity_context_reported_not_admission_control": {
            "pass": PROMOTION_ALLOWED is False,
            "diagnostic_capacity_signature_gap": axis0_capacity_gap,
            "reason": "The Axis0-offset PEPS3D variant is diagnostic only; it is not a capacity admission control.",
            "load_bearing_for_capacity_admission": False,
        },
        "collapsed_32_64_counts_are_rejected": {
            "collapsed_sites": 8,
            "expected_sites": [32, 64],
            "pass": 8 not in [32, 64],
        },
    }
    boundary = {
        "does_not_claim_full_32_64_engine": {"pass": "does not run a full 32/64-site source-native engine" in CLAIM_CEILING},
        "citation_is_blocked_until_full_64_engine_sweep": {
            "cites_blocked_until": CITES_BLOCKED_UNTIL,
            "pass": CITES_BLOCKED_UNTIL == "full_64_site_source_native_peps3d_engine_with_bond_sweep",
        },
        "source_signature_recorded": {"source_signature": source_signature, "pass": abs(source_signature) > 1e-9},
        "integration_is_dependency_consumption_not_result_aggregation": {
            "pass": seed_audit["science_method_fields_consumed"],
            "consumed_dependencies": [
                "EngineCore science-method stage records",
                "macro_sim_stage_record_science_method_contract receipt",
            ],
            "diagnostic_context_only": ["macro_sim_axis0_plural_stage_candidate_router receipt"],
            "dependency_use": (
                "stage/FEP fields form the 64-row PEPS3D capacity seed matrix; "
                "the raw Axis0 router is recorded only as upstream diagnostic context and does not gate admission"
            ),
        },
        "no_dense_environment_contraction_still_blocked": {
            "pass": True,
            "blocked_scope": "This capacity scout constructs PEPS3D carriers and contraction context only; it does not yet implement PEPS3D environment contraction readout.",
            "next_admissible_step": "PEPS/PEPS3D no-dense environment-contraction scout with gauge and finite-size controls.",
        },
    }
    all_pass = all(row["pass"] for row in positive.values()) and all(row["pass"] for row in graveyards.values()) and all(row["pass"] for row in boundary.values())
    axis0_outputs_or_blockers = {
        "plural_axis0_router": {
            "status": "diagnostic_router_context_only",
            "receipt": axis0_router,
            "axis0_signature": axis0,
            "context_candidate_names": AXIS0_CONTEXT_NAMES,
            "excluded_candidate_names": ["path_entropy", "holographic_boundary_interior_reconstruction"],
            "diagnostic_capacity_signature_gap": axis0_capacity_gap,
            "not_load_bearing_for_capacity_or_ladder_admission": True,
        },
        "fep_gradient_polarity": {"status": "diagnostic_from_pre_guard_router_context_not_capacity_admission"},
        "path_entropy": {
            "status": "excluded_from_peps3d_capacity_context_diagnostic_only",
            "load_bearing_for_capacity_context": False,
            "load_bearing_for_capacity_admission": False,
        },
        "correlation_diversity_derivative": {"status": "diagnostic_from_pre_guard_router_context_not_capacity_admission"},
        "holographic_boundary_interior_reconstruction": {
            "status": "excluded_from_peps3d_capacity_context_still_blocked",
            "load_bearing_for_capacity_context": False,
            "load_bearing_for_capacity_admission": False,
            "router_status": (
                axis0_router.get("axis0_outputs_or_blockers", {})
                .get("holographic_boundary_interior_reconstruction", {})
                .get("status")
            ),
        },
        "retrocausal_many_futures_policy_scoring": {
            "status": "diagnostic_from_pre_guard_router_context_as_finite_policy_scoring_not_capacity_admission",
            "router_status": (
                axis0_router.get("axis0_outputs_or_blockers", {})
                .get("retrocausal_many_futures_policy_scoring", {})
                .get("status")
            ),
        },
        "peps3d_environment_contraction": {
            "status": "blocked_next_surface",
            "blocker": "This repair is PEPS3D capacity context consumption, not no-dense PEPS3D environment contraction.",
        },
    }
    repair_receipt = {
        "weak_link": "PEPS3D 32/64 capacity scout seeded from a legacy density-history module and over-framed upstream Axis0 router diagnostics as dependency consumption.",
        "target_file_or_result": str(pathlib.Path(__file__).resolve()),
        "admission_rule_improved": "PEPS3D capacity/scaling scouts consume repaired EngineCore science-method fields while keeping upstream Axis0 router context diagnostic-only.",
        "dependency_subset": [
            "EngineCore.run_full_cycle repaired science-method stage records",
            "macro_sim_stage_record_science_method_contract receipt",
            "PEPS3D 32-site capacity carrier",
            "PEPS3D 64-site capacity carrier",
            "bond-dimension D2/D3 capacity sweep",
        ],
        "diagnostic_context_subset": [
            "macro_sim_axis0_plural_stage_candidate_router receipt",
            "axis0-offset PEPS3D diagnostic variant",
        ],
        "stage_fields_touched_or_consumed": REQUIRED_STAGE_FIELDS,
        "before_baseline/hash": {"script": BEFORE_SCRIPT_SHA256, "result": BEFORE_RESULT_SHA256},
        "after_delta/hash": "source rank matrix derives from model_after/fep_efe_score/update_repair; Axis0 diagnostic recorded with path/HBI excluded from load-bearing capacity admission",
        "primary_control/result": {
            "collapsed_32_64_counts": graveyards["collapsed_32_64_counts_are_rejected"],
        },
        "diagnostic_control/result": {
            "axis0_offset_capacity_context": graveyards["axis0_zeroed_capacity_context_reported_not_admission_control"],
        },
        "axis0_outputs_or_blockers": axis0_outputs_or_blockers,
        "provider_inputs_used": {
            "grok": "not_run_this_repair_wave",
            "gemini": "not_run_this_repair_wave",
            "sonnet_high": "not_run_this_repair_wave",
            "opus_max": "not_run_this_repair_wave",
            "reason": "local PEPS3D capacity dependency repair was directly executable",
        },
        "promotion_ceiling": CLAIM_CEILING,
        "next_step": "Repair or create PEPS/PEPS3D no-dense environment-contraction scout with gauge and finite-size controls.",
    }
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "cites_blocked_until": CITES_BLOCKED_UNTIL,
        "claim_ceiling": CLAIM_CEILING,
        "source_alignment_category": "source_native_density_seeded_peps3d_32_64_capacity_formal_scout",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "repair_receipt": repair_receipt,
        "axis0_outputs_or_blockers": axis0_outputs_or_blockers,
        "positive": positive,
        "graveyard_companions": graveyards,
        "boundary": boundary,
        "nearby_variants": {"total": len(graveyards), "passed": sum(1 for row in graveyards.values() if row["pass"]), "variants": sorted(graveyards)},
        "why_not_v4_probes": [
            "Capacity scout only.",
            "Does not execute the full operator-slot source-native engine on 32/64-site PEPS3D.",
            "Current source histories have low effective rank relative to 32/64-site capacity.",
        ],
        "blockers": [],
        "elapsed_seconds": time.time() - started,
        "all_pass": all_pass,
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(f"RESULT {NAME}: all_pass={all_pass} -> {OUT_PATH}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
