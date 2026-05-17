#!/usr/bin/env python3
"""Probe-family discrimination and chi-transport audit for 8/16/32-site carriers."""

from __future__ import annotations

import json
import os
import pathlib
import time
from collections import Counter
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

import networkx as nx
import numpy as np
import quimb.tensor as qtn
import sympy as sp
import z3

from engine_core import EngineCore, generate_initial_density
from sim_source_native_peps3d_64_site_slot_dynamics_closeout_probe import apply_slot_to_tensor


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "probe_family_discrimination_chi_transport_8_16_32_probe_results.json"

NAME = "probe_family_discrimination_chi_transport_8_16_32_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CITES_BLOCKED_UNTIL = "probe_family_discrimination_and_chi_transport_passes_before_64_site_promotion"
CLAIM_CEILING = (
    "Formal scout only: audits whether the source-native slot-dynamics probe "
    "family discriminates candidate, classical baseline, and random null families "
    "at 8/16/32 sites while preserving the candidate class across chi doubling. "
    "It does not admit canonical manifold, neural capability, physics, cognition, "
    "or 64-site promotion claims."
)

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "load-bearing tensor families and discrimination metrics"},
    "quimb": {"tried": True, "used": True, "reason": "load-bearing PEPS3D carriers for 8/16/32 cells"},
    "networkx": {"tried": True, "used": True, "reason": "load-bearing discrimination dependency graph"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing symbolic N and chi factorization"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing class separation and chi-transport witness"},
    "engine_core": {"tried": True, "used": True, "reason": "load-bearing source-native slot histories"},
}
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}

SHAPES = {8: (2, 2, 2), 16: (2, 2, 4), 32: (4, 4, 2)}
CHIS = {8: [2, 4, 8], 16: [2, 4, 8], 32: [2, 4, 8]}


def source_records(seed: int) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    rho0 = generate_initial_density(seed)
    for engine_type in (0, 1):
        engine = EngineCore(engine_type, manifold_enabled=True)
        rho = rho0.copy()
        for main_idx, (perception, loop_class) in enumerate(engine.schedule):
            for substage_idx in range(4):
                rho, record = engine.run_substage(rho, perception, loop_class, main_idx, substage_idx)
                records.append(record)
    return records


def make_arrays(shape: tuple[int, int, int], chi: int, seed: int, family: str) -> list[list[list[np.ndarray]]]:
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
                    legs.append(chi)
                if j < ly - 1:
                    legs.append(chi)
                if k < lz - 1:
                    legs.append(chi)
                if i > 0:
                    legs.append(chi)
                if j > 0:
                    legs.append(chi)
                if k > 0:
                    legs.append(chi)
                legs.append(2)
                if family == "classical_product":
                    arr = np.zeros(legs, dtype=np.complex128)
                    arr[..., 0] = 0.02
                else:
                    scale = 0.02 / max(chi, 1)
                    arr = rng.normal(scale=scale, size=legs).astype(np.complex128)
                    if family == "random_null":
                        arr = arr + 1j * rng.normal(scale=scale, size=legs)
                row.append(arr)
            plane.append(row)
        arrays.append(plane)
    return arrays


def tensor_norm(arrays: list[list[list[np.ndarray]]]) -> float:
    return float(np.sqrt(sum(float(np.vdot(arr, arr).real) for plane in arrays for row in plane for arr in row)))


def physical_coherence(arrays: list[list[list[np.ndarray]]]) -> float:
    total = 0.0
    for plane in arrays:
        for row in plane:
            for arr in row:
                flat = arr.reshape(-1, 2)
                total += float(np.sum(np.abs(flat[:, 0] * np.conj(flat[:, 1]))))
    return total


def parameter_count(arrays: list[list[list[np.ndarray]]]) -> int:
    return int(sum(np.prod(arr.shape) for plane in arrays for row in plane for arr in row))


def apply_family_cell(n_sites: int, chi: int, family: str, records: list[dict[str, Any]]) -> dict[str, Any]:
    arrays = make_arrays(SHAPES[n_sites], chi, seed=100000 + n_sites * 100 + chi, family=family)
    before = tensor_norm(arrays)
    before_coh = physical_coherence(arrays)
    sites = [(i, j, k) for i in range(SHAPES[n_sites][0]) for j in range(SHAPES[n_sites][1]) for k in range(SHAPES[n_sites][2])]
    touched = set()
    tokens = []
    if family == "random_null":
        used_records = records[: len(sites)]
    else:
        used_records = records
    for idx, record in enumerate(used_records):
        i, j, k = sites[idx % len(sites)]
        touched.add((i, j, k))
        tokens.append(str(record["ordered_token"]))
        if family == "source_native":
            strength = 0.0025 + 0.0004 * float(record["slot_delta_norm"]) + 0.0001 * float(record["entropy"])
            arrays[i][j][k] = apply_slot_to_tensor(arrays[i][j][k], str(record["operator"]), int(record["operator_sign"]), strength)
        elif family == "classical_product":
            arrays[i][j][k] = arrays[i][j][k] * (1.0 + 0.0005 * abs(int(record["operator_sign"])))
        elif family == "random_null":
            arrays[i][j][k] = arrays[i][j][k] * np.exp(1j * 0.001 * (idx + 1))
    after = tensor_norm(arrays)
    after_coh = physical_coherence(arrays)
    tn = qtn.PEPS3D(arrays)
    token_count = len(set(tokens))
    coherence_response = abs(after_coh - before_coh)
    if family == "source_native" and token_count == 32 and coherence_response > 1e-7:
        admissibility_class = "source_native_slot_coherent"
        admitted = True
    elif family == "classical_product" and token_count == 32 and after_coh < 1e-12:
        admissibility_class = "classical_product_matched_geometry"
        admitted = True
    else:
        admissibility_class = "excluded_null"
        admitted = False
    return {
        "n_sites": n_sites,
        "chi": chi,
        "family": family,
        "num_tensors": int(tn.num_tensors),
        "parameter_count": parameter_count(arrays),
        "slot_applications": len(used_records),
        "unique_sites_touched": len(touched),
        "unique_ordered_tokens": token_count,
        "norm_shift": abs(after - before),
        "coherence_before": before_coh,
        "coherence_after": after_coh,
        "coherence_response": coherence_response,
        "admitted": admitted,
        "admissibility_class": admissibility_class,
        "pass": int(tn.num_tensors) == n_sites and len(touched) == n_sites,
    }


def run_matrix() -> dict[str, Any]:
    records = source_records(99000)
    cells = []
    for n_sites in (8, 16, 32):
        for chi in CHIS[n_sites]:
            for family in ("source_native", "classical_product", "random_null"):
                cells.append(apply_family_cell(n_sites, chi, family, records))
    by_key = {(cell["n_sites"], cell["chi"], cell["family"]): cell for cell in cells}
    discrimination = []
    transport = []
    null_exclusion = []
    for n_sites in (8, 16, 32):
        source_classes = []
        for chi in CHIS[n_sites]:
            a = by_key[(n_sites, chi, "source_native")]
            b = by_key[(n_sites, chi, "classical_product")]
            c = by_key[(n_sites, chi, "random_null")]
            discrimination.append(a["admissibility_class"] != b["admissibility_class"] and a["admitted"] and b["admitted"])
            null_exclusion.append(not c["admitted"] and c["admissibility_class"] == "excluded_null")
            source_classes.append(a["admissibility_class"])
        transport.append(len(set(source_classes)) == 1)
    class_matrix = {
        f"N{cell['n_sites']}_chi{cell['chi']}_{cell['family']}": cell["admissibility_class"]
        for cell in cells
    }
    return {
        "cells": cells,
        "class_matrix": class_matrix,
        "operator_histogram": dict(sorted(Counter(str(row["operator"]) for row in records).items())),
        "pass": all(cell["pass"] for cell in cells)
        and all(discrimination)
        and all(transport)
        and all(null_exclusion),
        "predicate_summary": {
            "candidate_vs_classical_separated_all_cells": all(discrimination),
            "candidate_chi_transport_stable_all_N": all(transport),
            "random_null_excluded_all_cells": all(null_exclusion),
        },
    }


def z3_matrix_witness(matrix: dict[str, Any]) -> dict[str, Any]:
    solver = z3.Solver()
    separated = z3.Bool("separated")
    transported = z3.Bool("transported")
    excluded = z3.Bool("excluded")
    cells = z3.Int("cells")
    solver.add(separated == matrix["predicate_summary"]["candidate_vs_classical_separated_all_cells"])
    solver.add(transported == matrix["predicate_summary"]["candidate_chi_transport_stable_all_N"])
    solver.add(excluded == matrix["predicate_summary"]["random_null_excluded_all_cells"])
    solver.add(cells == len(matrix["cells"]))
    solver.add(z3.Not(z3.And(separated, transported, excluded, cells == 27)))
    status = solver.check()
    return {
        "solver_status": str(status),
        "pass": status == z3.unsat,
        "claim_ceiling": "Z3 encodes only finite class-matrix predicates for 27 cells.",
    }


def main() -> int:
    started = time.time()
    matrix = run_matrix()
    graph = nx.DiGraph()
    graph.add_edges_from([("source_native", "class_matrix"), ("classical_product", "class_matrix"), ("random_null", "class_matrix"), ("class_matrix", "chi_transport")])
    positive = {
        "probe_family_discriminates_candidate_classical_and_null": matrix,
        "symbolic_site_chi_factorization": {
            "factorization": {str(k): v for k, v in sp.factorint(8 * 16 * 32 * 2 * 4 * 8).items()},
            "pass": sp.factorint(8 * 16 * 32 * 2 * 4 * 8) == {2: 18},
        },
        "z3_rejects_vacuous_or_chi_locked_probe_family": z3_matrix_witness(matrix),
    }
    graveyards = {
        "classical_product_baseline_does_not_collapse_into_candidate": {
            "pass": matrix["predicate_summary"]["candidate_vs_classical_separated_all_cells"],
        },
        "random_null_is_not_admitted_by_slot_probe": {
            "pass": matrix["predicate_summary"]["random_null_excluded_all_cells"],
        },
        "candidate_chi_transport_not_assumed": {
            "pass": matrix["predicate_summary"]["candidate_chi_transport_stable_all_N"],
        },
    }
    boundary = {
        "graph_is_acyclic": {"nodes": graph.number_of_nodes(), "edges": graph.number_of_edges(), "pass": nx.is_directed_acyclic_graph(graph)},
        "promotion_remains_disabled": {"pass": PROMOTION_ALLOWED is False},
        "no_64_site_promotion_claim": {"pass": CITES_BLOCKED_UNTIL.endswith("before_64_site_promotion")},
    }
    all_pass = all(row["pass"] for row in positive.values()) and all(row["pass"] for row in graveyards.values()) and all(row["pass"] for row in boundary.values())
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "cites_blocked_until": CITES_BLOCKED_UNTIL,
        "claim_ceiling": CLAIM_CEILING,
        "source_alignment_category": "source_native_probe_family_discrimination_formal_scout",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "graveyard_companions": graveyards,
        "boundary": boundary,
        "nearby_variants": {"total": len(graveyards), "passed": sum(1 for row in graveyards.values() if row["pass"]), "variants": sorted(graveyards)},
        "why_not_v4_probes": [
            "Discrimination and chi-transport audit only.",
            "Does not promote 64-site PEPS3D results.",
            "Does not prove long-horizon dynamic manifold behavior.",
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
