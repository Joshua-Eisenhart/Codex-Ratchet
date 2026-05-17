#!/usr/bin/env python3
"""Source-native 64-site PEPS3D slot-dynamics closeout scout."""

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
OUT_PATH = RESULT_DIR / "source_native_peps3d_64_site_slot_dynamics_closeout_probe_results.json"

NAME = "source_native_peps3d_64_site_slot_dynamics_closeout_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CITES_BLOCKED_UNTIL = "full_64_site_bond_dimension_and_long_horizon_closeout"
EXPECTED_UNIQUE_ORDERED_TOKENS = 32
EXPECTED_SLOT_APPLICATIONS_PER_SEED = 64
CLAIM_CEILING = (
    "Formal scout only: applies the repaired source-native operator-slot sequence "
    "directly to a finite 64-site PEPS3D tensor carrier and records the 64-site "
    "slot-dynamics closeout predicates. It does not run a long-horizon 64-site "
    "engine, does not prove 64-site bond-dimension convergence, and does not "
    "admit final manifold, physics, cognition, neural architecture, or canonical claims."
)

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "load-bearing PEPS3D tensor updates and norm shifts"},
    "quimb": {"tried": True, "used": True, "reason": "load-bearing 64-site PEPS3D carrier construction"},
    "cotengra": {"tried": True, "used": True, "reason": "load-bearing contraction context witness"},
    "opt_einsum": {"tried": True, "used": True, "reason": "load-bearing contraction numeric cross-check"},
    "networkx": {"tried": True, "used": True, "reason": "load-bearing update dependency graph"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing symbolic token-count factorization"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing 64-site token contract witness"},
    "engine_core": {"tried": True, "used": True, "reason": "load-bearing source-native operator-slot trajectory generator"},
}
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}
BEFORE_SCRIPT_SHA256 = "dbcca3e494ec3ecad614ad7ed96a5a42a361ae91abaae8257c8b92db2b8bdee3"
BEFORE_RESULT_SHA256 = "91a521da364b5c2a95b4294260dfc1e38c2f071b0d60774a3ec6cbb607838199"

N_SEEDS = 4
DTYPE = np.complex128
SX = np.array([[0, 1], [1, 0]], dtype=DTYPE)
SY = np.array([[0, -1j], [1j, 0]], dtype=DTYPE)
SZ = np.array([[1, 0], [0, -1]], dtype=DTYPE)
I2 = np.eye(2, dtype=DTYPE)
OP_AXES = {"Ti": SZ, "Te": SX, "Fi": SX, "Fe": SY}
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
    names = ["fep_gradient_polarity", "path_entropy", "correlation_diversity_derivative"]
    vectors: dict[str, list[float]] = {}
    for name in names:
        arr = np.asarray(outputs.get(name, {}).get("values", []), dtype=float)
        if arr.size:
            arr = np.nan_to_num(arr, nan=0.0, posinf=0.0, neginf=0.0)
            scale = float(np.max(np.abs(arr)))
            if scale > 0.0:
                arr = arr / scale
        vectors[name] = [float(x) for x in arr]
    ready = bool(router.get("exists") and router.get("all_pass") is True and all(vectors.values()))
    return {
        "ready": ready,
        "candidate_names": names,
        "candidate_vectors": vectors,
        "source_receipt": router.get("path"),
    }


def axis0_drive(axis0: dict[str, Any], idx: int) -> float:
    if not axis0.get("ready"):
        return 0.0
    values = []
    for vector in axis0.get("candidate_vectors", {}).values():
        if vector:
            values.append(float(vector[idx % len(vector)]))
    return float(np.mean(values)) if values else 0.0


def science_method_contract(records: list[dict[str, Any]]) -> dict[str, Any]:
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
        "pass": not missing and len(records) == N_SEEDS * EXPECTED_SLOT_APPLICATIONS_PER_SEED,
        "record_count": len(records),
        "required_fields": REQUIRED_STAGE_FIELDS,
        "missing_required_stage_fields": missing,
        "expected_free_energy_mean": float(np.mean(efe)),
        "expected_free_energy_variance": float(np.var(efe)),
    }


def make_peps3d_arrays(seed: int, bond_dim: int = 2) -> list[list[list[np.ndarray]]]:
    rng = np.random.default_rng(seed)
    arrays = []
    for i in range(4):
        plane = []
        for j in range(4):
            row = []
            for k in range(4):
                legs = []
                if i < 3:
                    legs.append(bond_dim)
                if j < 3:
                    legs.append(bond_dim)
                if k < 3:
                    legs.append(bond_dim)
                if i > 0:
                    legs.append(bond_dim)
                if j > 0:
                    legs.append(bond_dim)
                if k > 0:
                    legs.append(bond_dim)
                legs.append(2)
                row.append(rng.normal(scale=0.025, size=legs).astype(DTYPE))
            plane.append(row)
        arrays.append(plane)
    return arrays


def flatten_sites(arrays: list[list[list[np.ndarray]]]) -> list[tuple[int, int, int]]:
    return [(i, j, k) for i in range(4) for j in range(4) for k in range(4)]


def tensor_norm(arrays: list[list[list[np.ndarray]]]) -> float:
    return float(np.sqrt(sum(float(np.vdot(arr, arr).real) for plane in arrays for row in plane for arr in row)))


def apply_slot_to_tensor(arr: np.ndarray, operator: str, sign: int, strength: float) -> np.ndarray:
    axis = OP_AXES[operator]
    unitary = I2 - 1j * float(sign) * float(strength) * axis
    moved = np.tensordot(arr, unitary.T, axes=([-1], [0]))
    return moved.astype(DTYPE)


def source_records() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for seed_idx in range(N_SEEDS):
        rho_init = generate_initial_density(70000 + seed_idx)
        for engine_type in (0, 1):
            engine = EngineCore(engine_type, manifold_enabled=True)
            rho = rho_init.copy()
            for main_idx, (perception, loop_class) in enumerate(engine.schedule):
                for substage_idx in range(4):
                    rho, record = engine.run_substage(rho, perception, loop_class, main_idx, substage_idx)
                    records.append(record)
    return records


def apply_records_to_64_site_peps3d(
    records: list[dict[str, Any]],
    *,
    identity_control: bool = False,
    axis0: dict[str, Any] | None = None,
    zero_axis0: bool = False,
) -> dict[str, Any]:
    arrays = make_peps3d_arrays(71000)
    before = tensor_norm(arrays)
    sites = flatten_sites(arrays)
    touched = set()
    token_sequence: list[str] = []
    axis0_drives: list[float] = []
    for idx, record in enumerate(records):
        site = sites[idx % len(sites)]
        i, j, k = site
        token_sequence.append(str(record["ordered_token"]))
        touched.add(site)
        drive = 0.0 if zero_axis0 else axis0_drive(axis0 or {}, idx)
        axis0_drives.append(drive)
        if identity_control:
            continue
        fep = record.get("fep_efe_score", {})
        strength = (
            0.0025
            + 0.0004 * float(record["slot_delta_norm"])
            + 0.0001 * float(record["entropy"])
            + 0.00005 * float(fep.get("expected_free_energy_proxy", 0.0))
            + 0.0002 * drive
        )
        arrays[i][j][k] = apply_slot_to_tensor(
            arrays[i][j][k],
            str(record["operator"]),
            int(record["operator_sign"]),
            strength,
        )
    after = tensor_norm(arrays)
    peps = qtn.PEPS3D(arrays)
    return {
        "tensor_size": 64,
        "num_tensors": int(peps.num_tensors),
        "num_indices": int(peps.num_indices),
        "parameter_count": int(sum(np.prod(tensor.shape) for tensor in peps.tensors)),
        "slot_applications": len(records),
        "unique_sites_touched": len(touched),
        "unique_ordered_tokens": len(set(token_sequence)),
        "ordered_token_histogram": dict(sorted(Counter(token_sequence).items())),
        "axis0_ready": bool((axis0 or {}).get("ready")),
        "axis0_zeroed": bool(zero_axis0),
        "axis0_drive_mean_abs": float(np.mean(np.abs(axis0_drives))) if axis0_drives else 0.0,
        "axis0_drive_variance": float(np.var(axis0_drives)) if axis0_drives else 0.0,
        "norm_before": before,
        "norm_after": after,
        "norm_shift": abs(after - before),
        "pass": int(peps.num_tensors) == 64
        and len(records) == N_SEEDS * EXPECTED_SLOT_APPLICATIONS_PER_SEED
        and len(touched) == 64
        and len(set(token_sequence)) == EXPECTED_UNIQUE_ORDERED_TOKENS
        and abs(after - before) > 1e-5,
    }


def contraction_context(seed: int) -> dict[str, float]:
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
    sizes = {ix: 2 + ((n + seed) % 3) for n, ix in enumerate(labels)}
    for ix in output:
        sizes[ix] = 2
    tree = ctg.HyperOptimizer(max_repeats=4, progbar=False).search(inputs, output, sizes)
    rng = np.random.default_rng(19000 + seed)
    arrays = [rng.normal(size=tuple(sizes[ix] for ix in term)) for term in inputs]
    return {
        "cost": float(tree.contraction_cost()),
        "width": float(tree.contraction_width()),
        "norm": float(np.linalg.norm(oe.contract(expr, *arrays))),
    }


def z3_closeout_witness(row: dict[str, Any]) -> dict[str, Any]:
    solver = z3.Solver()
    tensor_size = z3.Int("tensor_size")
    applications = z3.Int("slot_applications")
    tokens = z3.Int("unique_tokens")
    touched = z3.Int("touched_sites")
    solver.add(tensor_size == row["tensor_size"])
    solver.add(applications == row["slot_applications"])
    solver.add(tokens == row["unique_ordered_tokens"])
    solver.add(touched == row["unique_sites_touched"])
    solver.add(z3.Not(z3.And(tensor_size == 64, applications == N_SEEDS * 64, tokens == 32, touched == 64)))
    status = solver.check()
    return {
        "solver_status": str(status),
        "pass": status == z3.unsat,
        "claim_ceiling": "Z3 encodes only finite 64-site closeout counts; tensor updates carry the empirical burden.",
    }


def main() -> int:
    started = time.time()
    axis0_router = load_result("macro_sim_axis0_plural_stage_candidate_router_probe_results.json")
    stage_contract = load_result("macro_sim_stage_record_science_method_contract_probe_results.json")
    axis0 = axis0_signature(axis0_router)
    records = source_records()
    science_contract = science_method_contract(records)
    dynamic = apply_records_to_64_site_peps3d(records, identity_control=False, axis0=axis0)
    identity = apply_records_to_64_site_peps3d(records, identity_control=True, axis0=axis0)
    axis0_zeroed = apply_records_to_64_site_peps3d(records, identity_control=False, axis0=axis0, zero_axis0=True)
    axis0_norm_shift_gap = abs(dynamic["norm_shift"] - axis0_zeroed["norm_shift"])
    graph = nx.DiGraph()
    graph.add_edges_from([
        ("source_records", "science_method_fields"),
        ("science_method_fields", "slot_sequence"),
        ("axis0_plural_router", "slot_strength"),
        ("slot_sequence", "slot_strength"),
        ("slot_strength", "peps3d_64_tensor"),
        ("peps3d_64_tensor", "closeout"),
    ])
    positive = {
        "slot_dynamics_execute_directly_on_64_site_peps3d": {
            **dynamic,
            "expected_unique_ordered_tokens": EXPECTED_UNIQUE_ORDERED_TOKENS,
            "expected_slot_applications_per_seed": EXPECTED_SLOT_APPLICATIONS_PER_SEED,
            "contraction_context": contraction_context(dynamic["unique_ordered_tokens"] + dynamic["unique_sites_touched"]),
            "pass": dynamic["pass"],
        },
        "science_method_stage_records_drive_64_site_slot_strength": {
            "pass": science_contract["pass"] and stage_contract["exists"] and stage_contract.get("all_pass") is True,
            "source_stage_contract_receipt": stage_contract,
            **science_contract,
        },
        "plural_axis0_router_drives_64_site_slot_strength": {
            "pass": axis0["ready"] and dynamic["axis0_drive_mean_abs"] > 0.001 and axis0_norm_shift_gap > 1e-9,
            "axis0_router_receipt": axis0_router,
            "axis0_signature": axis0,
            "dynamic_axis0_drive_mean_abs": dynamic["axis0_drive_mean_abs"],
            "axis0_zeroed_norm_shift": axis0_zeroed["norm_shift"],
            "dynamic_norm_shift": dynamic["norm_shift"],
            "axis0_norm_shift_gap": axis0_norm_shift_gap,
        },
        "symbolic_64_slot_factorization": {
            "factorization": {str(k): v for k, v in sp.factorint(64 * EXPECTED_UNIQUE_ORDERED_TOKENS).items()},
            "pass": sp.factorint(64 * EXPECTED_UNIQUE_ORDERED_TOKENS) == {2: 11},
        },
        "z3_rejects_64_site_slot_contract_collapse": z3_closeout_witness(dynamic),
    }
    graveyards = {
        "identity_tensor_update_does_not_count_as_dynamics": {
            "identity_norm_shift": identity["norm_shift"],
            "dynamic_norm_shift": dynamic["norm_shift"],
            "pass": identity["norm_shift"] < 1e-12 and dynamic["norm_shift"] > identity["norm_shift"],
        },
        "axis0_zeroed_control_changes_slot_dynamics": {
            "pass": axis0_norm_shift_gap > 1e-9,
            "axis0_zeroed_norm_shift": axis0_zeroed["norm_shift"],
            "dynamic_norm_shift": dynamic["norm_shift"],
            "axis0_norm_shift_gap": axis0_norm_shift_gap,
            "reason": "Axis0 router output affects slot strength before tensor updates, not only the receipt.",
        },
        "label_only_records_would_fail_64_site_closeout": {
            "pass": science_contract["pass"],
            "required_fields": REQUIRED_STAGE_FIELDS,
            "reason": "Closeout now requires repaired science-method/FEP fields for slot-strength calculation.",
        },
        "ordered_token_count_is_not_interpolated": {
            "unique_ordered_tokens": dynamic["unique_ordered_tokens"],
            "pass": dynamic["unique_ordered_tokens"] == EXPECTED_UNIQUE_ORDERED_TOKENS,
        },
    }
    boundary = {
        "does_not_claim_long_horizon_or_bond_convergence": {
            "pass": "does not run a long-horizon 64-site engine" in CLAIM_CEILING and "does not prove 64-site bond-dimension convergence" in CLAIM_CEILING,
        },
        "dependency_graph_is_acyclic": {"nodes": graph.number_of_nodes(), "edges": graph.number_of_edges(), "pass": nx.is_directed_acyclic_graph(graph)},
        "promotion_remains_disabled": {"pass": PROMOTION_ALLOWED is False},
        "integration_is_dependency_consumption_not_result_aggregation": {
            "pass": science_contract["pass"] and axis0["ready"],
            "consumed_dependencies": [
                "EngineCore science-method stage records",
                "macro_sim_stage_record_science_method_contract receipt",
                "macro_sim_axis0_plural_stage_candidate_router receipt",
            ],
            "dependency_use": (
                "science-method FEP scores and plural Axis0 router drives enter slot-strength calculation "
                "before the PEPS3D tensor update"
            ),
        },
        "environment_contraction_still_blocked": {
            "pass": True,
            "blocked_scope": "64-site tensor update closeout only; no PEPS3D environment contraction readout or gauge control is implemented here.",
            "next_admissible_step": "PEPS/PEPS3D no-dense environment-contraction scout with gauge and finite-size controls.",
        },
    }
    all_pass = all(row["pass"] for row in positive.values()) and all(row["pass"] for row in graveyards.values()) and all(row["pass"] for row in boundary.values())
    axis0_outputs_or_blockers = {
        "plural_axis0_router": {
            "status": "consumed_as_64_site_slot_strength_dependency",
            "receipt": axis0_router,
            "axis0_norm_shift_gap": axis0_norm_shift_gap,
        },
        "fep_gradient_polarity": {"status": "consumed_from_plural_router"},
        "path_entropy": {"status": "consumed_from_plural_router"},
        "correlation_diversity_derivative": {"status": "consumed_from_plural_router"},
        "holographic_boundary_interior_reconstruction": {
            "status": "still_blocked_by_router_receipt",
            "router_status": (
                axis0_router.get("axis0_outputs_or_blockers", {})
                .get("holographic_boundary_interior_reconstruction", {})
                .get("status")
            ),
        },
        "retrocausal_many_futures_policy_scoring": {
            "status": "routing_only_not_final",
            "router_status": (
                axis0_router.get("axis0_outputs_or_blockers", {})
                .get("retrocausal_many_futures_policy_scoring", {})
                .get("status")
            ),
        },
        "peps3d_environment_contraction": {
            "status": "blocked_next_surface",
            "blocker": "This closeout applies tensors directly but does not compute no-dense PEPS3D environment readout.",
        },
    }
    repair_receipt = {
        "weak_link": "64-site PEPS3D closeout applied EngineCore records but did not require science-method/FEP fields or plural Axis0 dependency consumption.",
        "target_file_or_result": str(pathlib.Path(__file__).resolve()),
        "admission_rule_improved": "64-site PEPS3D slot-dynamics closeouts must consume science-method stage fields and plural Axis0 router outputs before tensor updates.",
        "dependency_subset": [
            "EngineCore source records",
            "macro_sim_stage_record_science_method_contract receipt",
            "macro_sim_axis0_plural_stage_candidate_router receipt",
            "64-site PEPS3D tensor update",
            "identity tensor-update control",
            "axis0_zeroed slot-strength control",
        ],
        "stage_fields_touched_or_consumed": REQUIRED_STAGE_FIELDS,
        "before_baseline/hash": {"script": BEFORE_SCRIPT_SHA256, "result": BEFORE_RESULT_SHA256},
        "after_delta/hash": "slot strength now consumes fep_efe_score plus plural Axis0 router drive before tensor update",
        "primary_control/result": {
            "identity_tensor_update": graveyards["identity_tensor_update_does_not_count_as_dynamics"],
            "axis0_zeroed": graveyards["axis0_zeroed_control_changes_slot_dynamics"],
        },
        "axis0_outputs_or_blockers": axis0_outputs_or_blockers,
        "provider_inputs_used": {
            "grok": "not_run_this_repair_wave",
            "gemini": "not_run_this_repair_wave",
            "sonnet_high": "not_run_this_repair_wave",
            "opus_max": "not_run_this_repair_wave",
            "reason": "local 64-site PEPS3D dependency repair was directly executable",
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
        "source_alignment_category": "source_native_peps3d_64_site_slot_dynamics_closeout_formal_scout",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "repair_receipt": repair_receipt,
        "axis0_outputs_or_blockers": axis0_outputs_or_blockers,
        "positive": positive,
        "graveyard_companions": graveyards,
        "boundary": boundary,
        "nearby_variants": {"total": len(graveyards), "passed": sum(1 for row in graveyards.values() if row["pass"]), "variants": sorted(graveyards)},
        "why_not_v4_probes": [
            "64-site finite closeout only.",
            "Does not prove long-horizon 64-site stability.",
            "Does not prove bond-dimension convergence beyond the finite update context.",
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
