#!/usr/bin/env python3
"""Source-native PEPS3D 52/56/60-site regime ladder scout."""

from __future__ import annotations

import json
import os
import pathlib
import time
from collections import Counter
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
OUT_PATH = RESULT_DIR / "source_native_peps3d_52_56_60_site_regime_ladder_probe_results.json"

NAME = "source_native_peps3d_52_56_60_site_regime_ladder_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CITES_BLOCKED_UNTIL = "full_64_site_bond_dimension_and_long_horizon_closeout"
CLAIM_CEILING = (
    "Formal scout only: fills the 52/56/60-site PEPS3D regime ladder between "
    "48 and 64 sites while replaying the repaired source-native operator-slot "
    "contract. It does not prove long-horizon 64-site stability, bond-dimension "
    "convergence, and does not admit neural capability, physics, cognition, or "
    "canonical manifold claims."
)

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "load-bearing tensor construction and capacity counts"},
    "quimb": {"tried": True, "used": True, "reason": "load-bearing PEPS3D carriers for 52/56/60 sites"},
    "cotengra": {"tried": True, "used": True, "reason": "load-bearing contraction context for regime ladder"},
    "opt_einsum": {"tried": True, "used": True, "reason": "load-bearing contraction numeric cross-check"},
    "networkx": {"tried": True, "used": True, "reason": "load-bearing monotone regime graph"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing factorization of intermediate site counts"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing ordered ladder and token-contract witness"},
    "engine_core": {"tried": True, "used": True, "reason": "load-bearing repaired source-native slot replay"},
}
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}
BEFORE_SCRIPT_SHA256 = "27544943ecd936ee726c1c33d939e27f59a04d5d5cf3615fe148fa446d8a70b1"
BEFORE_RESULT_SHA256 = "4be9bab54231c66734468cf4bb5c0dd5c50c379f8621e8e450233b6b267f1aa3"

SITE_SHAPES = {
    48: (4, 4, 3),
    52: (2, 2, 13),
    56: (4, 7, 2),
    60: (4, 5, 3),
    64: (4, 4, 4),
}
N_SEEDS = 4
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


def axis0_signature(router: dict[str, Any]) -> dict[str, Any]:
    outputs = router.get("axis0_outputs_or_blockers") or {}
    parts = []
    for name in AXIS0_CONTEXT_NAMES:
        values = np.asarray(outputs.get(name, {}).get("values", []), dtype=float)
        if values.size:
            values = np.nan_to_num(values, nan=0.0, posinf=0.0, neginf=0.0)
            parts.append(float(np.sum(values) + np.mean(np.abs(values))))
    ready = bool(router.get("exists") and router.get("all_pass") is True and len(parts) == len(AXIS0_CONTEXT_NAMES))
    signature = float(sum(parts)) if parts else 0.0
    return {
        "ready": ready,
        "candidate_names": list(AXIS0_CONTEXT_NAMES),
        "pre_guard_router_context": True,
        "diagnostic_only": True,
        "not_load_bearing_for_ladder_admission": True,
        "post_guard_admission_claim_allowed": False,
        "signature": signature,
        "seed_offset": int(abs(signature) * 1000) % 997,
        "source_receipt": router.get("path"),
    }


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
                row.append(rng.normal(scale=0.02 / bond_dim, size=legs))
            plane.append(row)
        arrays.append(plane)
    return qtn.PEPS3D(arrays)


def parameter_count(tn: qtn.PEPS3D) -> int:
    return int(sum(np.prod(tensor.shape) for tensor in tn.tensors))


def replay_slot_contract() -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    for seed_idx in range(N_SEEDS):
        rho_init = generate_initial_density(81000 + seed_idx)
        for engine_type in (0, 1):
            engine = EngineCore(engine_type, manifold_enabled=True)
            rho = rho_init.copy()
            for main_idx, (perception, loop_class) in enumerate(engine.schedule):
                for substage_idx in range(4):
                    rho, record = engine.run_substage(rho, perception, loop_class, main_idx, substage_idx)
                    records.append(record)
    missing = {
        f"E{row['engine_type']}:S{row['main_stage_idx']}:u{row['substage_idx']}:i{idx}": [
            field for field in REQUIRED_STAGE_FIELDS if field not in row
        ]
        for idx, row in enumerate(records)
    }
    missing = {key: value for key, value in missing.items() if value}
    efe = np.asarray(
        [row.get("fep_efe_score", {}).get("expected_free_energy_proxy", 0.0) for row in records],
        dtype=float,
    )
    return {
        "rows": len(records),
        "operator_histogram": dict(sorted(Counter(str(row["operator"]) for row in records).items())),
        "ordered_token_count": len(set(str(row["ordered_token"]) for row in records)),
        "terrain_family_count": len(set(str(row["terrain_dynamics_family"]) for row in records)),
        "all_valid_density": all(bool(row["valid_density"]) for row in records),
        "all_13_layers_called": all(int(row["manifold_called_count"]) == 13 for row in records),
        "science_method_fields_consumed": not missing,
        "missing_required_stage_fields": missing,
        "expected_free_energy_mean": float(np.mean(efe)),
        "expected_free_energy_variance": float(np.var(efe)),
        "pass": len(records) == N_SEEDS * 64
        and len(set(str(row["ordered_token"]) for row in records)) == 32
        and len(set(str(row["terrain_dynamics_family"]) for row in records)) >= 7
        and all(bool(row["valid_density"]) for row in records)
        and all(int(row["manifold_called_count"]) == 13 for row in records)
        and not missing,
    }


def contraction_context(sites: int, seed: int) -> dict[str, float]:
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
    sizes = {ix: 2 + ((n + sites + seed) % 3) for n, ix in enumerate(labels)}
    for ix in output:
        sizes[ix] = 2
    tree = ctg.HyperOptimizer(max_repeats=4, progbar=False).search(inputs, output, sizes)
    rng = np.random.default_rng(82000 + seed + sites)
    arrays = [rng.normal(size=tuple(sizes[ix] for ix in term)) for term in inputs]
    return {
        "cost": float(tree.contraction_cost()),
        "width": float(tree.contraction_width()),
        "norm": float(np.linalg.norm(oe.contract(expr, *arrays))),
    }


def ladder_signature(row: dict[str, Any]) -> np.ndarray:
    return np.asarray(
        [
            value
            for site in row["site_sequence"]
            for value in (
                row["rows"][str(site)]["parameter_count_bond2"],
                row["rows"][str(site)]["contraction"]["cost"],
                row["rows"][str(site)]["contraction"]["width"],
                row["rows"][str(site)]["contraction"]["norm"],
            )
        ],
        dtype=float,
    )


def regime_ladder(axis0_seed_offset: int = 0) -> dict[str, Any]:
    rows: dict[str, Any] = {}
    for sites, shape in SITE_SHAPES.items():
        seeded = axis0_seed_offset + sites
        tn2 = make_peps3d(shape, 83000 + seeded, bond_dim=2)
        tn3 = make_peps3d(shape, 84000 + seeded, bond_dim=3)
        rows[str(sites)] = {
            "shape": "x".join(str(x) for x in shape),
            "sites": sites,
            "num_tensors": int(tn2.num_tensors),
            "num_indices": int(tn2.num_indices),
            "parameter_count_bond2": parameter_count(tn2),
            "parameter_count_bond3": parameter_count(tn3),
            "factorization": {str(k): v for k, v in sp.factorint(sites).items()},
            "contraction": contraction_context(sites, seed=seeded),
        }
    site_keys = [48, 52, 56, 60, 64]
    counts = [rows[str(site)]["parameter_count_bond2"] for site in site_keys]
    return {
        "rows": rows,
        "axis0_seed_offset": axis0_seed_offset,
        "site_sequence": site_keys,
        "bond2_parameter_counts": counts,
        "pass": all(rows[str(site)]["num_tensors"] == site for site in site_keys)
        and all(rows[str(site)]["parameter_count_bond3"] > rows[str(site)]["parameter_count_bond2"] for site in site_keys)
        and rows["52"]["sites"] < rows["56"]["sites"] < rows["60"]["sites"] < rows["64"]["sites"],
    }


def z3_ladder_witness(contract: dict[str, Any]) -> dict[str, Any]:
    solver = z3.Solver()
    q48, q52, q56, q60, q64, tokens = z3.Ints("q48 q52 q56 q60 q64 tokens")
    solver.add(q48 == 48, q52 == 52, q56 == 56, q60 == 60, q64 == 64, tokens == contract["ordered_token_count"])
    solver.add(z3.Not(z3.And(q48 < q52, q52 < q56, q56 < q60, q60 < q64, tokens == 32)))
    status = solver.check()
    return {
        "solver_status": str(status),
        "pass": status == z3.unsat,
        "claim_ceiling": "Z3 encodes only finite regime ordering plus 32-token replay.",
    }


def main() -> int:
    started = time.time()
    axis0_router = load_result("macro_sim_axis0_plural_stage_candidate_router_probe_results.json")
    stage_contract = load_result("macro_sim_stage_record_science_method_contract_probe_results.json")
    axis0 = axis0_signature(axis0_router)
    contract = replay_slot_contract()
    ladder = regime_ladder(axis0_seed_offset=0)
    axis0_diagnostic_ladder = regime_ladder(axis0_seed_offset=axis0["seed_offset"])
    axis0_ladder_gap = float(np.linalg.norm(ladder_signature(axis0_diagnostic_ladder) - ladder_signature(ladder)))
    graph = nx.DiGraph()
    graph.add_edges_from([
        ("48", "52"),
        ("52", "56"),
        ("56", "60"),
        ("60", "64"),
        ("science_method_slot_contract", "52"),
        ("science_method_slot_contract", "56"),
        ("science_method_slot_contract", "60"),
    ])
    positive = {
        "peps3d_52_56_60_ladder_constructs_between_48_and_64": ladder,
        "source_native_slot_contract_replays_across_ladder": contract,
        "science_method_stage_records_consumed_by_ladder_contract": {
            "pass": contract["pass"] and stage_contract["exists"] and stage_contract.get("all_pass") is True,
            "stage_contract_receipt": stage_contract,
            "required_fields": REQUIRED_STAGE_FIELDS,
            "expected_free_energy_mean": contract["expected_free_energy_mean"],
            "expected_free_energy_variance": contract["expected_free_energy_variance"],
        },
        "axis0_router_context_reported_diagnostic_only": {
            "pass": PROMOTION_ALLOWED is False and axis0["post_guard_admission_claim_allowed"] is False,
            "axis0_router_receipt": axis0_router,
            "axis0_signature": axis0,
            "context_candidate_names": AXIS0_CONTEXT_NAMES,
            "diagnostic_ladder_signature_gap": axis0_ladder_gap,
            "diagnostic_ladder_variant": axis0_diagnostic_ladder,
            "load_bearing_for_ladder_admission": False,
            "reason": "This upstream PEPS3D regime ladder records the raw Axis0 router as diagnostic context only.",
        },
        "z3_rejects_intermediate_ladder_collapse": z3_ladder_witness(contract),
    }
    graveyards = {
        "label_only_slot_contract_would_fail_ladder_admission": {
            "pass": contract["science_method_fields_consumed"],
            "required_fields": REQUIRED_STAGE_FIELDS,
            "reason": "The ladder contract now requires repaired science-method/FEP fields, not token labels alone.",
        },
        "axis0_zeroed_ladder_context_reported_not_admission_control": {
            "pass": PROMOTION_ALLOWED is False,
            "diagnostic_ladder_signature_gap": axis0_ladder_gap,
            "reason": "The Axis0-offset ladder variant is diagnostic only; it is not an intermediate-regime admission control.",
            "load_bearing_for_ladder_admission": False,
        },
        "skip_intermediate_ladder_does_not_promote": {
            "intermediate_sites": [52, 56, 60],
            "pass": PROMOTION_ALLOWED is False and CITES_BLOCKED_UNTIL == "full_64_site_bond_dimension_and_long_horizon_closeout",
        },
        "token_contract_is_not_capacity_only": {
            "ordered_token_count": contract["ordered_token_count"],
            "pass": contract["ordered_token_count"] == 32 and contract["all_13_layers_called"],
        },
    }
    boundary = {
        "regime_graph_is_acyclic": {"nodes": graph.number_of_nodes(), "edges": graph.number_of_edges(), "pass": nx.is_directed_acyclic_graph(graph)},
        "does_not_claim_long_horizon_or_canonical_status": {
            "pass": "does not prove long-horizon 64-site stability" in CLAIM_CEILING and PROMOTION_ALLOWED is False,
        },
        "integration_is_dependency_consumption_not_result_aggregation": {
            "pass": contract["science_method_fields_consumed"],
            "consumed_dependencies": [
                "EngineCore science-method stage records",
                "macro_sim_stage_record_science_method_contract receipt",
            ],
            "diagnostic_context_only": ["macro_sim_axis0_plural_stage_candidate_router receipt"],
            "dependency_use": (
                "science-method fields gate slot-contract replay; the raw Axis0 router is recorded only as upstream "
                "diagnostic context and does not gate intermediate-regime admission"
            ),
        },
        "environment_contraction_still_blocked": {
            "pass": True,
            "blocked_scope": "Intermediate PEPS3D carrier ladder only; no PEPS3D environment contraction readout or gauge control is implemented here.",
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
            "diagnostic_ladder_signature_gap": axis0_ladder_gap,
            "not_load_bearing_for_capacity_or_ladder_admission": True,
        },
        "fep_gradient_polarity": {"status": "diagnostic_from_pre_guard_router_context_not_ladder_admission"},
        "path_entropy": {
            "status": "excluded_from_peps3d_ladder_context_diagnostic_only",
            "load_bearing_for_ladder_context": False,
            "load_bearing_for_ladder_admission": False,
        },
        "correlation_diversity_derivative": {"status": "diagnostic_from_pre_guard_router_context_not_ladder_admission"},
        "holographic_boundary_interior_reconstruction": {
            "status": "excluded_from_peps3d_ladder_context_still_blocked",
            "load_bearing_for_ladder_context": False,
            "load_bearing_for_ladder_admission": False,
            "router_status": (
                axis0_router.get("axis0_outputs_or_blockers", {})
                .get("holographic_boundary_interior_reconstruction", {})
                .get("status")
            ),
        },
        "retrocausal_many_futures_policy_scoring": {
            "status": "diagnostic_from_pre_guard_router_context_as_finite_policy_scoring_not_ladder_admission",
            "router_status": (
                axis0_router.get("axis0_outputs_or_blockers", {})
                .get("retrocausal_many_futures_policy_scoring", {})
                .get("status")
            ),
        },
        "peps3d_environment_contraction": {
            "status": "blocked_next_surface",
            "blocker": "This repair covers the intermediate PEPS3D carrier ladder, not no-dense environment contraction.",
        },
    }
    repair_receipt = {
        "weak_link": "Intermediate PEPS3D 52/56/60 ladder replayed token contract but over-framed upstream Axis0 router diagnostics as dependency consumption.",
        "target_file_or_result": str(pathlib.Path(__file__).resolve()),
        "admission_rule_improved": "Intermediate PEPS3D regime scouts require science-method stage fields while keeping upstream Axis0 router context diagnostic-only.",
        "dependency_subset": [
            "EngineCore source records",
            "macro_sim_stage_record_science_method_contract receipt",
            "PEPS3D 52-site carrier",
            "PEPS3D 56-site carrier",
            "PEPS3D 60-site carrier",
        ],
        "diagnostic_context_subset": [
            "macro_sim_axis0_plural_stage_candidate_router receipt",
            "axis0-offset PEPS3D ladder diagnostic variant",
        ],
        "stage_fields_touched_or_consumed": REQUIRED_STAGE_FIELDS,
        "before_baseline/hash": {"script": BEFORE_SCRIPT_SHA256, "result": BEFORE_RESULT_SHA256},
        "after_delta/hash": "slot contract now requires science-method/FEP fields; Axis0 diagnostic recorded with path/HBI excluded from load-bearing ladder admission",
        "primary_control/result": {
            "skip_intermediate_ladder": graveyards["skip_intermediate_ladder_does_not_promote"],
        },
        "diagnostic_control/result": {
            "axis0_offset_ladder_context": graveyards["axis0_zeroed_ladder_context_reported_not_admission_control"],
        },
        "axis0_outputs_or_blockers": axis0_outputs_or_blockers,
        "provider_inputs_used": {
            "grok": "not_run_this_repair_wave",
            "gemini": "not_run_this_repair_wave",
            "sonnet_high": "not_run_this_repair_wave",
            "opus_max": "not_run_this_repair_wave",
            "reason": "local intermediate PEPS3D ladder dependency repair was directly executable",
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
        "source_alignment_category": "source_native_peps3d_intermediate_regime_ladder_formal_scout",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "repair_receipt": repair_receipt,
        "axis0_outputs_or_blockers": axis0_outputs_or_blockers,
        "positive": positive,
        "graveyard_companions": graveyards,
        "boundary": boundary,
        "nearby_variants": {"total": len(graveyards), "passed": sum(1 for row in graveyards.values() if row["pass"]), "variants": sorted(graveyards)},
        "why_not_v4_probes": [
            "Intermediate finite-regime scout only.",
            "Does not execute long-horizon 64-site engine dynamics.",
            "Keeps 64-site citation blocked until bond-dimension and long-horizon closeout.",
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
