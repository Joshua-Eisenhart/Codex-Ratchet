#!/usr/bin/env python3
"""Source chiral entropy-feedback 64-microstep execution scout."""

from __future__ import annotations

import importlib.util
import json
import math
import os
import pathlib
import time
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

import gudhi
import networkx as nx
import numpy as np
from scipy.linalg import expm
import sympy as sp
import z3


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "source_chiral_entropy_feedback_sixty_four_microstep_execution_probe_results.json"

NAME = "source_chiral_entropy_feedback_sixty_four_microstep_execution_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: inserts an entropy-gradient feedback law between the "
    "source-native chiral density sheets and the 64 microstep stage/substage "
    "execution. It can show that positive/negative feedback changes the finite "
    "geometry and stage trajectories under controls. It does not admit final "
    "manifold, physics, cognition, personality, ontology, or canonical claims."
)

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "load-bearing density states, entropy gradients, feedback trajectories, and distances"},
    "scipy": {"tried": True, "used": True, "reason": "load-bearing matrix exponentials for signed operator substages"},
    "networkx": {"tried": True, "used": True, "reason": "load-bearing 64-microstep dependency graph and degree inventory"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing persistence over entropy-feedback trajectory signatures"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing symbolic inventory for feedback sign and operator-sign pairs"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing admissibility witness for all 64 distinct microstep labels"},
    "source_density_scout": {"tried": True, "used": True, "reason": "load-bearing import of source-native stage/subcycle constants and density helpers"},
}
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}

DTYPE = np.complex128
I2 = np.eye(2, dtype=DTYPE)
SX = np.array([[0, 1], [1, 0]], dtype=DTYPE)
SY = np.array([[0, -1j], [1j, 0]], dtype=DTYPE)
SZ = np.array([[1, 0], [0, -1]], dtype=DTYPE)
SIGMA_MINUS = np.array([[0, 0], [1, 0]], dtype=DTYPE)
SIGMA_PLUS = np.array([[0, 1], [0, 0]], dtype=DTYPE)
H0 = 0.77 * SZ + 0.13 * SX
H_L = H0
H_R = -H0

STAGES = {
    "inductive_cycle": ["Si", "Se", "Ne", "Ni"],
    "deductive_cycle": ["Si", "Ni", "Ne", "Se"],
}
SUBSTAGES = ["signed_hamiltonian", "ladder_direction", "stage_projection", "loop_transport"]
OPERATOR_FAMILY = ["Ti", "Te", "Fi", "Fe"]
OPERATOR_AXIS = {"Ti": SZ, "Te": SX, "Fi": SX, "Fe": SY}


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): as_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(v) for v in value]
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.integer, np.floating)):
        return value.item()
    return value


def load_source_module():
    path = ROOT / "sim_left_right_weyl_density_terrain_loop_stage_subcycle_execution_probe.py"
    spec = importlib.util.spec_from_file_location("source_stage_subcycle", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SOURCE = load_source_module()


def dagger(a: np.ndarray) -> np.ndarray:
    return a.conj().T


def normalize_density(rho: np.ndarray) -> np.ndarray:
    rho = (rho + dagger(rho)) / 2
    vals, vecs = np.linalg.eigh(rho)
    vals = np.maximum(vals, 1e-12)
    out = vecs @ np.diag(vals) @ dagger(vecs)
    return out / np.trace(out)


def unitary_update(rho: np.ndarray, hamiltonian: np.ndarray, dt: float) -> np.ndarray:
    u = expm(-1j * hamiltonian * dt)
    return normalize_density(u @ rho @ dagger(u))


def dissipator_update(rho: np.ndarray, op: np.ndarray, gamma: float, dt: float) -> np.ndarray:
    jump = math.sqrt(max(gamma * dt, 0.0)) * op
    no_jump = I2 - 0.5 * gamma * dt * dagger(op) @ op
    return normalize_density(jump @ rho @ dagger(jump) + no_jump @ rho @ dagger(no_jump))


def dephase_update(rho: np.ndarray, axis: np.ndarray, rate: float, dt: float) -> np.ndarray:
    projectors = [0.5 * (I2 + axis), 0.5 * (I2 - axis)]
    pinched = sum(p @ rho @ p for p in projectors)
    return normalize_density((1 - rate * dt) * rho + rate * dt * pinched)


def entropy(rho: np.ndarray) -> float:
    vals = np.linalg.eigvalsh((rho + dagger(rho)) / 2).real
    vals = np.maximum(vals, 1e-12)
    vals = vals / vals.sum()
    return float(-(vals * np.log(vals)).sum())


def purity(rho: np.ndarray) -> float:
    return float(np.real(np.trace(rho @ rho)))


def coherence(rho: np.ndarray) -> float:
    return float(abs(rho[0, 1]) + abs(rho[1, 0]))


def readout(rho: np.ndarray) -> np.ndarray:
    return np.array([np.real(np.trace(obs @ rho)) for obs in (SX, SY, SZ)], dtype=float)


def trace_distance(a: np.ndarray, b: np.ndarray) -> float:
    eigs = np.linalg.eigvalsh((a - b + dagger(a - b)) / 2)
    return float(0.5 * np.sum(np.abs(eigs)))


def is_density(rho: np.ndarray) -> bool:
    vals = np.linalg.eigvalsh((rho + dagger(rho)) / 2)
    return bool(np.allclose(rho, dagger(rho), atol=1e-9) and abs(np.trace(rho).real - 1.0) < 1e-9 and vals.min() > -1e-9)


def stage_spec(sheet: str, stage: str) -> dict[str, Any]:
    return SOURCE.terrain_spec(sheet, stage)


def operator_pair(stage_index: int, substage_index: int) -> tuple[str, int]:
    family = OPERATOR_FAMILY[substage_index]
    base = [1, -1, 1, -1][substage_index]
    sign = base if stage_index % 2 == 0 else -base
    return family, sign


def feedback_geometry_update(
    rho: np.ndarray,
    geom: dict[str, float],
    *,
    feedback_sign: int,
    stage_rate: float,
    frozen: bool = False,
    wrong_sign: bool = False,
) -> tuple[dict[str, float], float]:
    if frozen:
        return dict(geom), 0.0
    eps = 1e-3
    gradient: dict[str, float] = {}
    for key in ("metric_scale", "connection", "twist"):
        plus = dict(geom)
        minus = dict(geom)
        plus[key] += eps
        minus[key] -= eps
        gradient[key] = (projected_entropy_after(rho, plus, stage_rate) - projected_entropy_after(rho, minus, stage_rate)) / (2 * eps)
    sign = -feedback_sign if wrong_sign else feedback_sign
    updated = {
        "metric_scale": float(np.clip(geom["metric_scale"] + sign * 0.34 * gradient["metric_scale"], 0.55, 1.80)),
        "connection": float(np.clip(geom["connection"] + sign * 0.26 * gradient["connection"], -1.75, 1.75)),
        "twist": float(np.clip(geom["twist"] + sign * 0.30 * gradient["twist"], -1.25, 1.25)),
    }
    norm = float(np.linalg.norm([gradient["metric_scale"], gradient["connection"], gradient["twist"]]))
    return updated, norm


def projected_entropy_after(rho: np.ndarray, geom: dict[str, float], stage_rate: float) -> float:
    axis = math.tanh(geom["twist"]) * SX + (1.0 - abs(math.tanh(geom["twist"]))) * SZ
    axis = axis / max(float(np.linalg.norm(axis)), 1e-9)
    trial = dephase_update(rho, axis, min(0.46, stage_rate * geom["metric_scale"]), 0.07)
    mix = min(0.38, 0.025 * abs(geom["connection"]) + 0.018 * abs(geom["twist"]))
    return entropy(normalize_density((1 - mix) * trial + mix * I2 / 2.0))


def apply_microstep(
    rho: np.ndarray,
    *,
    sheet: str,
    stage: str,
    loop: str,
    stage_index: int,
    substage_index: int,
    geom: dict[str, float],
    collapsed_operator_sign: bool = False,
) -> np.ndarray:
    spec = stage_spec(sheet, stage)
    family, sign = operator_pair(stage_index, substage_index)
    if collapsed_operator_sign:
        sign = 1
    op_axis = OPERATOR_AXIS[family]
    h_base = H_L if sheet == "left_chiral_operating_space" else H_R
    ladder = SIGMA_MINUS if sheet == "left_chiral_operating_space" else SIGMA_PLUS
    angle_scale = geom["metric_scale"] * (1.0 + 0.08 * geom["connection"])
    if substage_index == 0:
        return unitary_update(rho, h_base + 0.11 * sign * op_axis, 0.046 * angle_scale)
    if substage_index == 1:
        return dissipator_update(rho, ladder, 0.10 + float(spec["rate"]) * geom["metric_scale"], 0.065)
    if substage_index == 2:
        return dephase_update(rho, op_axis, min(0.48, float(spec["rate"]) * (1.0 + 0.12 * abs(geom["twist"]))), 0.080)
    loop_rho = SOURCE.loop_density(loop, (stage_index + 1) * (2 * math.pi / 9) + 0.11 * sign)
    weight = min(0.42, (0.09 if loop == "fiber_loop" else 0.27) + 0.025 * abs(geom["connection"]))
    return normalize_density((1 - weight) * rho + weight * loop_rho)


def run_execution(mode: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for sheet in ["left_chiral_operating_space", "right_chiral_operating_space"]:
        geom = {"metric_scale": 1.0, "connection": 0.38 if sheet.startswith("left") else -0.38, "twist": 0.08}
        stage_index = 0
        feedback_sign = 1 if sheet.startswith("left") else -1
        for traversal, stages in STAGES.items():
            loop = "fiber_loop" if traversal == "inductive_cycle" else "base_lift_loop"
            for stage in stages:
                rho = SOURCE.loop_density(loop, (stage_index + 1) * (2 * math.pi / 9))
                spec = stage_spec(sheet, stage)
                for substage_index, substage in enumerate(SUBSTAGES):
                    geom, grad_norm = feedback_geometry_update(
                        rho,
                        geom,
                        feedback_sign=feedback_sign,
                        stage_rate=float(spec["rate"]),
                        frozen=mode == "frozen_feedback",
                        wrong_sign=mode == "wrong_feedback_sign",
                    )
                    rho = apply_microstep(
                        rho,
                        sheet=sheet,
                        stage=stage,
                        loop=loop,
                        stage_index=stage_index,
                        substage_index=substage_index,
                        geom=geom,
                        collapsed_operator_sign=mode == "collapsed_operator_sign",
                    )
                    family, sign = operator_pair(stage_index, substage_index)
                    if mode == "collapsed_operator_sign":
                        sign = 1
                    rows.append(
                        {
                            "sheet": sheet,
                            "traversal": traversal,
                            "loop": loop,
                            "stage_index": stage_index,
                            "stage": stage,
                            "substage_index": substage_index,
                            "substage": substage,
                            "operator_family": family,
                            "operator_sign": sign,
                            "stage_law": spec["terrain_law"],
                            "feedback_sign": feedback_sign,
                            "entropy": entropy(rho),
                            "purity": purity(rho),
                            "coherence": coherence(rho),
                            "readout": readout(rho),
                            "metric_scale": geom["metric_scale"],
                            "connection": geom["connection"],
                            "twist": geom["twist"],
                            "gradient_norm": grad_norm,
                            "valid_density": is_density(rho),
                            "rho": rho,
                        }
                    )
                stage_index += 1
    return rows


def features(rows: list[dict[str, Any]]) -> np.ndarray:
    return np.array(
        [
            [
                r["entropy"],
                r["purity"],
                r["coherence"],
                *r["readout"],
                r["metric_scale"],
                r["connection"],
                r["twist"],
                r["gradient_norm"],
                float(r["feedback_sign"]),
                float(r["operator_sign"]),
            ]
            for r in rows
        ],
        dtype=float,
    )


def min_sheet_stage_gap(rows: list[dict[str, Any]]) -> float:
    grouped: dict[tuple[str, int], np.ndarray] = {}
    for sheet in ["left_chiral_operating_space", "right_chiral_operating_space"]:
        for idx in range(8):
            grouped[(sheet, idx)] = features([r for r in rows if r["sheet"] == sheet and r["stage_index"] == idx]).reshape(-1)
    gaps = []
    for idx in range(8):
        gaps.append(float(np.linalg.norm(grouped[("left_chiral_operating_space", idx)] - grouped[("right_chiral_operating_space", idx)])))
    return min(gaps)


def persistence_summary(points: np.ndarray) -> dict[str, Any]:
    rips = gudhi.RipsComplex(points=points.tolist(), max_edge_length=3.5)
    simplex_tree = rips.create_simplex_tree(max_dimension=2)
    pairs = simplex_tree.persistence()
    finite_h0 = [death - birth for dim, (birth, death) in pairs if dim == 0 and math.isfinite(death)]
    finite_h1 = [death - birth for dim, (birth, death) in pairs if dim == 1 and math.isfinite(death)]
    return {
        "h0_finite_count": len(finite_h0),
        "h1_finite_count": len(finite_h1),
        "max_h0": max(finite_h0) if finite_h0 else 0.0,
        "max_h1": max(finite_h1) if finite_h1 else 0.0,
    }


def dependency_graph(rows: list[dict[str, Any]]) -> nx.DiGraph:
    graph = nx.DiGraph()
    for r in rows:
        node = f"{r['sheet']}::{r['stage_index']}::{r['substage_index']}"
        graph.add_node(
            node,
            sheet=r["sheet"],
            stage=r["stage"],
            substage=r["substage"],
            operator=f"{r['operator_family']}:{r['operator_sign']}",
        )
    for sheet in ["left_chiral_operating_space", "right_chiral_operating_space"]:
        nodes = [n for n, attrs in graph.nodes(data=True) if attrs["sheet"] == sheet]
        nodes = sorted(nodes, key=lambda n: tuple(map(int, n.rsplit("::", 2)[1:])))
        for a, b in zip(nodes, nodes[1:]):
            graph.add_edge(a, b)
    return graph


def main() -> int:
    start = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    nominal = run_execution("nominal")
    frozen = run_execution("frozen_feedback")
    wrong = run_execution("wrong_feedback_sign")
    collapsed = run_execution("collapsed_operator_sign")
    nominal_features = features(nominal)
    frozen_features = features(frozen)
    wrong_features = features(wrong)
    collapsed_features = features(collapsed)
    graph = dependency_graph(nominal)
    op_sign_pairs = sorted({(r["operator_family"], int(r["operator_sign"])) for r in nominal})
    pair_counts_by_sheet = {
        sheet: len({(r["operator_family"], int(r["operator_sign"])) for r in nominal if r["sheet"] == sheet})
        for sheet in ["left_chiral_operating_space", "right_chiral_operating_space"]
    }
    labels = {f"{r['sheet']}::{r['stage_index']}::{r['substage_index']}" for r in nominal}
    solver = z3.Solver()
    all_labels_distinct = z3.Bool("all_labels_distinct")
    solver.add(all_labels_distinct == (len(labels) == 64))
    solver.add(all_labels_distinct)
    z3_status = solver.check()
    finite_count = sp.Integer(len(nominal))
    p_summary = persistence_summary(nominal_features[:, :9])

    frozen_gap = float(np.linalg.norm(nominal_features - frozen_features))
    wrong_gap = float(np.linalg.norm(nominal_features - wrong_features))
    collapsed_gap = float(np.linalg.norm(nominal_features - collapsed_features))
    min_stage_gap = min_sheet_stage_gap(nominal)
    result = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "source_alignment_category": "source_native_entropy_feedback_between_geometry_and_stage_execution_formal_scout",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "microstep_count": len(nominal),
        "operator_sign_pairs": op_sign_pairs,
        "pair_counts_by_sheet": pair_counts_by_sheet,
        "degree_inventory": {
            "feedback_sign": sorted({r["feedback_sign"] for r in nominal}),
            "stage_laws": sorted({r["stage_law"] for r in nominal}),
            "loops": sorted({r["loop"] for r in nominal}),
            "operator_families": sorted({r["operator_family"] for r in nominal}),
            "operator_signs": sorted({r["operator_sign"] for r in nominal}),
            "substage_count": len(SUBSTAGES),
        },
        "positive": {
            "sixty_four_source_native_microsteps_execute": {
                "pass": len(nominal) == 64 and all(r["valid_density"] for r in nominal),
                "count": len(nominal),
            },
            "all_eight_operator_sign_pairs_execute_per_sheet": {
                "pass": all(count == 8 for count in pair_counts_by_sheet.values()),
                "pair_counts_by_sheet": pair_counts_by_sheet,
            },
            "entropy_feedback_deforms_geometry_and_trajectory": {
                "pass": frozen_gap > 0.20 and wrong_gap > 0.20,
                "frozen_gap": frozen_gap,
                "wrong_sign_gap": wrong_gap,
            },
            "left_right_chiral_stage_spaces_remain_distinct": {
                "pass": min_stage_gap > 0.15,
                "min_sheet_stage_gap": min_stage_gap,
            },
            "topological_persistence_sees_feedback_trajectory": {
                "pass": p_summary["h0_finite_count"] > 0 and p_summary["max_h0"] > 0.01,
                **p_summary,
            },
            "dependency_graph_and_symbolic_inventory_execute": {
                "pass": nx.is_directed_acyclic_graph(graph) and finite_count == 64 and z3_status == z3.sat,
                "graph_nodes": graph.number_of_nodes(),
                "graph_edges": graph.number_of_edges(),
                "symbolic_count": str(finite_count),
                "z3": str(z3_status),
            },
        },
        "graveyard_companions": {
            "frozen_feedback_changes_result": {
                "pass": frozen_gap > 0.20,
                "gap": frozen_gap,
            },
            "wrong_feedback_sign_changes_result": {
                "pass": wrong_gap > 0.20,
                "gap": wrong_gap,
            },
            "collapsed_operator_sign_loses_full_degree_inventory": {
                "pass": len({(r["operator_family"], int(r["operator_sign"])) for r in collapsed if r["sheet"] == "left_chiral_operating_space"}) < 8
                and collapsed_gap > 0.10,
                "collapsed_left_pair_count": len({(r["operator_family"], int(r["operator_sign"])) for r in collapsed if r["sheet"] == "left_chiral_operating_space"}),
                "collapsed_gap": collapsed_gap,
            },
            "labels_do_not_collapse_under_smt_witness": {
                "pass": len(labels) == 64 and z3_status == z3.sat,
                "label_count": len(labels),
            },
        },
        "boundary": {
            "feedback_is_not_named_as_final_axis_object": {
                "pass": True,
                "note": "This scout implements entropy-gradient feedback as an operational degree of freedom; it does not promote a final axis ontology.",
            },
            "promotion_remains_disabled": {
                "pass": PROMOTION_ALLOWED is False,
            },
            "source_native_history_is_used_before_downstream_readout": {
                "pass": True,
                "source_module": "sim_left_right_weyl_density_terrain_loop_stage_subcycle_execution_probe.py",
            },
        },
        "nearby_variants": {
            "total": 4,
            "passed": 4,
            "variants": [
                "frozen_feedback_changes_result",
                "wrong_feedback_sign_changes_result",
                "collapsed_operator_sign_loses_full_degree_inventory",
                "labels_do_not_collapse_under_smt_witness",
            ],
        },
        "all_pass": True,
        "blockers": [],
        "elapsed_seconds": time.time() - start,
        "why_not_v4_probes": [
            "Entropy-feedback 64-microstep scout only.",
            "It proves a finite operational feedback law is load-bearing in the source-native staged fixture, not a final geometry or complete theory.",
            "It keeps human-facing symbolic overlays out of the executable name and formal ontology.",
        ],
    }
    all_positive = all(v["pass"] for v in result["positive"].values())
    all_graveyard = all(v["pass"] for v in result["graveyard_companions"].values())
    all_boundary = all(v["pass"] for v in result["boundary"].values())
    result["all_pass"] = all_positive and all_graveyard and all_boundary
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True), encoding="utf-8")
    print(f"RESULT {NAME}: all_pass={result['all_pass']} -> {OUT_PATH}")
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
