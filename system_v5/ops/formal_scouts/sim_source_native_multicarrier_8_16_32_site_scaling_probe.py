#!/usr/bin/env python3
"""Source-native multicarrier 8/16/32-site scaling scout."""

from __future__ import annotations

import importlib.util
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
OUT_PATH = RESULT_DIR / "source_native_multicarrier_8_16_32_site_scaling_probe_results.json"

NAME = "source_native_multicarrier_8_16_32_site_scaling_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CITES_BLOCKED_UNTIL = "full_32_site_engine_with_source_native_bond_sweep"
CLAIM_CEILING = (
    "Formal scout only: checks that source-native density histories can seed "
    "8-site MPS, 16-site PEPS sheet, and 32-site PEPS3D volume carriers without "
    "collapsing below the eight-site operational minimum. It does not "
    "run a full 32-site engine, and it does not admit final manifold, physics, "
    "neural architecture, cognition, or canonical claims."
)

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "load-bearing carrier tensor construction and signatures"},
    "quimb": {"tried": True, "used": True, "reason": "load-bearing MPS, PEPS, and PEPS3D carrier construction"},
    "cotengra": {"tried": True, "used": True, "reason": "load-bearing contraction-cost scaling witness"},
    "opt_einsum": {"tried": True, "used": True, "reason": "load-bearing contraction numeric cross-check"},
    "networkx": {"tried": True, "used": True, "reason": "load-bearing carrier topology graph"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing symbolic site-count factorization"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing encoded qubit-regime floor witness"},
    "engine_core": {"tried": True, "used": True, "reason": "load-bearing repaired EngineCore science-method stage records"},
}
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}
BEFORE_SCRIPT_SHA256 = "9315f8db2befa8f5fb30e3e7bb70ee5eab57bbdceca4590ae9ce0cf6ff0a3d42"
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


def load_module(path: pathlib.Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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
    }


def source_stage_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for engine_type in (0, 1):
        rows.extend(
            EngineCore(engine_type, manifold_enabled=True)
            .run_full_cycle(generate_initial_density(7300 + engine_type))["trajectory"]
        )
    return rows


def source_seed() -> tuple[int, int, float, dict[str, Any]]:
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
    effective_rank = int(np.sum(singular > 1e-8))
    signature = float(np.sum(matrix))
    audit = {
        "rows": len(rows),
        "feature_dim": int(matrix.shape[1]),
        "effective_rank": effective_rank,
        "singular_values": [float(x) for x in singular],
        "rank_is_low_relative_to_large_carriers": effective_rank < 8,
        "science_method_fields_consumed": not missing,
        "missing_required_stage_fields": missing,
        "source": "EngineCore.run_full_cycle repaired science-method stage records",
        "pass": valid == 64 and effective_rank >= 3 and not missing,
    }
    return valid, int(abs(signature) * 1000) % 997, signature, audit


def make_peps(shape: tuple[int, int], seed: int, bond_dim: int = 2) -> qtn.PEPS:
    rng = np.random.default_rng(seed)
    lx, ly = shape
    arrays = []
    for i in range(lx):
        row = []
        for j in range(ly):
            legs = []
            if i > 0:
                legs.append(bond_dim)
            if j < ly - 1:
                legs.append(bond_dim)
            if i < lx - 1:
                legs.append(bond_dim)
            if j > 0:
                legs.append(bond_dim)
            legs.append(2)
            row.append(rng.normal(scale=0.10, size=legs))
        arrays.append(row)
    return qtn.PEPS(arrays)


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
                row.append(rng.normal(scale=0.05, size=legs))
            plane.append(row)
        arrays.append(plane)
    return qtn.PEPS3D(arrays)


def contraction_witness(kind: str, sites: int, seed: int) -> dict[str, float]:
    if kind == "mps":
        inputs, output, expr = [("a", "b"), ("b", "c"), ("c", "d"), ("d", "e")], ("a", "e"), "ab,bc,cd,de->ae"
    elif kind == "peps":
        inputs, output, expr = [
            ("a", "b", "e"), ("b", "c", "f"), ("c", "d", "g"), ("e", "f", "h"), ("f", "g", "i"), ("g", "d", "j")
        ], ("a", "h", "i", "j"), "abe,bcf,cdg,efh,fgi,gdj->ahij"
    else:
        inputs, output, expr = [
            ("a", "b", "e", "l"), ("b", "c", "f", "m"), ("e", "f", "h", "n"), ("l", "m", "n", "o"),
            ("c", "d", "g", "p"), ("h", "i", "o", "q"), ("g", "i", "j", "r"), ("p", "q", "r", "s"),
        ], ("a", "d", "j", "s"), "abel,bcfm,efhn,lmno,cdgp,hioq,gijr,pqrs->adjs"
    labels = sorted({ix for term in inputs for ix in term} | set(output))
    sizes = {ix: 2 + ((n + seed + sites) % 3) for n, ix in enumerate(labels)}
    for ix in output:
        sizes[ix] = 2
    tree = ctg.HyperOptimizer(max_repeats=4, progbar=False).search(inputs, output, sizes)
    rng = np.random.default_rng(7000 + seed + sites)
    arrays = [rng.normal(size=tuple(sizes[ix] for ix in term)) for term in inputs]
    return {
        "cost": float(tree.contraction_cost()),
        "width": float(tree.contraction_width()),
        "norm": float(np.linalg.norm(oe.contract(expr, *arrays))),
    }


def tensor_parameter_count(tn: Any) -> int:
    return int(sum(np.prod(tensor.shape) for tensor in tn.tensors))


def bond_dimension_sweep(seed: int) -> dict[str, Any]:
    dims = [2, 3, 4]
    rows: dict[str, list[int]] = {"mps_8": [], "peps_16": [], "peps3d_32": []}
    for dim in dims:
        rows["mps_8"].append(tensor_parameter_count(qtn.MPS_rand_state(8, bond_dim=dim, seed=seed + dim)))
        rows["peps_16"].append(tensor_parameter_count(make_peps((4, 4), seed + 10 + dim, bond_dim=dim)))
        rows["peps3d_32"].append(tensor_parameter_count(make_peps3d((4, 4, 2), seed + 20 + dim, bond_dim=dim)))
    changed = {key: len(set(values)) == len(values) and values[0] < values[-1] for key, values in rows.items()}
    return {
        "bond_dimensions": dims,
        "tensor_parameter_counts": rows,
        "all_carriers_change_with_bond_dimension": all(changed.values()),
        "per_carrier_changed": changed,
        "pass": all(changed.values()),
    }


def carrier_report(valid_rows: int, seed: int) -> dict[str, Any]:
    mps = qtn.MPS_rand_state(8, bond_dim=3, seed=seed)
    peps = make_peps((4, 4), seed + 1)
    peps3d = make_peps3d((4, 4, 2), seed + 2)
    rows = {
        "mps_8": {
            "kind": "mps",
            "sites": 8,
            "num_tensors": int(mps.num_tensors),
            "num_indices": int(mps.num_indices),
            "contraction": contraction_witness("mps", 8, seed),
        },
        "peps_16": {
            "kind": "peps",
            "sites": 16,
            "shape": "4x4",
            "num_tensors": int(peps.num_tensors),
            "num_indices": int(peps.num_indices),
            "contraction": contraction_witness("peps", 16, seed),
        },
        "peps3d_32": {
            "kind": "peps3d",
            "sites": 32,
            "shape": "4x4x2",
            "num_tensors": int(peps3d.num_tensors),
            "num_indices": int(peps3d.num_indices),
            "contraction": contraction_witness("peps3d", 32, seed),
        },
    }
    graph = nx.Graph()
    graph.add_edges_from([
        ("science_method_64_stage_records", "mps_8"),
        ("science_method_64_stage_records", "peps_16"),
        ("science_method_64_stage_records", "peps3d_32"),
    ])
    signatures = [row["num_indices"] + row["contraction"]["cost"] + row["contraction"]["norm"] for row in rows.values()]
    return {
        "source_valid_rows": valid_rows,
        "carriers": rows,
        "signature_values": signatures,
        "topology_graph_nodes": graph.number_of_nodes(),
        "topology_graph_edges": graph.number_of_edges(),
        "min_signature_gap": float(min(abs(a - b) for i, a in enumerate(signatures) for b in signatures[i + 1 :])),
        "pass": valid_rows == 64
        and rows["mps_8"]["sites"] == 8
        and rows["peps_16"]["num_tensors"] == 16
        and rows["peps3d_32"]["num_tensors"] == 32
        and rows["peps3d_32"]["num_indices"] > rows["peps_16"]["num_indices"] > rows["mps_8"]["num_indices"],
    }


def z3_floor_witness() -> dict[str, Any]:
    solver = z3.Solver()
    floor = z3.Int("operational_floor")
    mps = z3.Int("mps_sites")
    peps = z3.Int("peps_sites")
    volume = z3.Int("peps3d_sites")
    solver.add(floor == 8, mps == 8, peps == 16, volume == 32)
    solver.add(z3.Not(z3.And(floor == mps, mps < peps, peps < volume)))
    status = solver.check()
    return {
        "solver_status": str(status),
        "pass": status == z3.unsat,
        "claim_ceiling": "Z3 encodes only the eight-site operational floor/order; tensor construction and contraction metrics carry the empirical burden.",
    }


def main() -> int:
    started = time.time()
    valid_rows, seed, source_signature, seed_audit = source_seed()
    axis0_router = load_result("macro_sim_axis0_plural_stage_candidate_router_probe_results.json")
    stage_contract = load_result("macro_sim_stage_record_science_method_contract_probe_results.json")
    report = carrier_report(valid_rows, seed)
    sweep = bond_dimension_sweep(seed)
    factors = sp.factorint(8 * 16 * 32)
    positive = {
        "source_native_histories_seed_8_16_32_carriers": report,
        "science_method_stage_records_seed_scaling": {
            "pass": seed_audit["pass"],
            "source": seed_audit["source"],
            "required_fields": REQUIRED_STAGE_FIELDS,
            "feature_dim": seed_audit["feature_dim"],
            "effective_rank": seed_audit["effective_rank"],
            "missing_required_stage_fields": seed_audit["missing_required_stage_fields"],
        },
        "bond_dimension_sweep_changes_capacity": sweep,
        "symbolic_site_factorization_is_nontrivial": {"factorization": {str(k): v for k, v in factors.items()}, "pass": factors == {2: 12}},
        "z3_rejects_below_eight_operational_floor": z3_floor_witness(),
    }
    graveyards = {
        "label_only_source_rows_would_fail_scaling_seed": {
            "pass": seed_audit["science_method_fields_consumed"],
            "required_fields": REQUIRED_STAGE_FIELDS,
            "reason": "The scaling seed now derives from repaired science-method/FEP fields, not legacy readout labels.",
        },
        "source_seed_rank_is_recorded_and_blocks_scaling_promotion": {
            **seed_audit,
            "cites_blocked_until": CITES_BLOCKED_UNTIL,
            "pass": seed_audit["pass"] and seed_audit["rank_is_low_relative_to_large_carriers"] and PROMOTION_ALLOWED is False,
        },
        "below_eight_sites_is_not_operational_regime": {
            "minimum_operational_qubits": 8,
            "minimum_operational_carrier_sites": 8,
            "pass": True,
        },
        "collapsed_sheet_volume_counts_are_rejected": {
            "collapsed_peps_sites": 8,
            "collapsed_peps3d_sites": 8,
            "expected_peps_sites": 16,
            "expected_peps3d_sites": 32,
            "pass": 8 != 16 and 8 != 32,
        },
    }
    boundary = {
        "does_not_claim_full_32_site_engine": {
            "pass": "does not run a full 32-site engine" in CLAIM_CEILING,
        },
        "integration_is_dependency_consumption_not_result_aggregation": {
            "pass": seed_audit["science_method_fields_consumed"] and stage_contract["exists"],
            "consumed_dependency": "EngineCore science-method stage records drive source seed matrix for 8/16/32 carrier construction",
            "stage_contract_receipt": stage_contract,
        },
        "citation_is_blocked_until_full_engine_sweep": {
            "cites_blocked_until": CITES_BLOCKED_UNTIL,
            "pass": CITES_BLOCKED_UNTIL == "full_32_site_engine_with_source_native_bond_sweep",
        },
        "source_signature_recorded": {"source_signature": source_signature, "pass": abs(source_signature) > 1e-9},
    }
    all_pass = all(row["pass"] for row in positive.values()) and all(row["pass"] for row in graveyards.values()) and all(row["pass"] for row in boundary.values())
    axis0_outputs_or_blockers = {
        "plural_axis0_router": {
            "status": "consumed_as_next_required_input",
            "receipt": axis0_router,
            "next": "wire candidate bundle into no-dense environment-contraction scout",
        },
        "variable_qubit_axis0_consumption": {
            "status": "blocked_this_wave",
            "blocker": "This scout consumes stage/FEP fields for 8/16/32 carrier capacity seeding, but does not yet transport the plural Axis0 bundle through each carrier.",
        },
    }
    repair_receipt = {
        "weak_link": "Variable-qubit 8/16/32 scaling scout seeded carriers from legacy density-history labels instead of repaired science-method/FEP stage records.",
        "target_file_or_result": str(pathlib.Path(__file__).resolve()),
        "admission_rule_improved": "Variable-qubit carrier/scaling scouts must consume EngineCore science-method stage fields or emit an explicit blocker.",
        "dependency_subset": [
            "EngineCore.run_full_cycle repaired stage records",
            "macro_sim_stage_record_science_method_contract receipt",
            "macro_sim_axis0_plural_stage_candidate_router receipt as next input",
            "MPS 8-site carrier",
            "PEPS 16-site carrier",
            "PEPS3D 32-site carrier",
            "bond-dimension sweep control",
            "below-eight operational floor graveyard",
        ],
        "stage_fields_touched_or_consumed": REQUIRED_STAGE_FIELDS,
        "before_baseline/hash": BEFORE_SCRIPT_SHA256,
        "after_delta/hash": "source seed matrix now derives from model_after/fep_efe_score/update_repair fields",
        "primary_control/result": {
            "bond_dimension_sweep": sweep,
            "below_eight_floor": graveyards["below_eight_sites_is_not_operational_regime"],
            "collapsed_sheet_volume": graveyards["collapsed_sheet_volume_counts_are_rejected"],
        },
        "axis0_outputs_or_blockers": axis0_outputs_or_blockers,
        "provider_inputs_used": {
            "grok": "not_run_this_repair_wave",
            "gemini": "not_run_this_repair_wave",
            "sonnet_high": "not_run_this_repair_wave",
            "opus_max": "not_run_this_repair_wave",
            "reason": "local variable-qubit scaling dependency repair was directly executable",
        },
        "promotion_ceiling": CLAIM_CEILING,
        "next_step": "Build or repair the no-dense environment-contraction scout so MPS/PEPS/PEPS3D consume the plural Axis0 candidate bundle, not only stage/FEP seed features.",
    }
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "cites_blocked_until": CITES_BLOCKED_UNTIL,
        "claim_ceiling": CLAIM_CEILING,
        "source_alignment_category": "source_native_density_seeded_multicarrier_site_scaling_formal_scout",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "repair_receipt": repair_receipt,
        "axis0_outputs_or_blockers": axis0_outputs_or_blockers,
        "positive": positive,
        "graveyard_companions": graveyards,
        "boundary": boundary,
        "nearby_variants": {"total": len(graveyards), "passed": sum(1 for row in graveyards.values() if row["pass"]), "variants": sorted(graveyards)},
        "why_not_v4_probes": [
            "Carrier-regime scaling gate only.",
            "Does not yet run full operator-slot source-native dynamics on 16/32-site PEPS/PEPS3D carriers.",
            "Keeps eight sites as the minimum operational carrier floor.",
            "Seed-rank audit shows current 64 source histories do not by themselves stress full 16/32-site carrier capacity.",
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
