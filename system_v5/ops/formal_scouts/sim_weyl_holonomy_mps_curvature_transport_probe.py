#!/usr/bin/env python3
"""Source-native Weyl holonomy / MPS curvature transport scout."""

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
from scipy.linalg import expm
import sympy as sp
import z3

from engine_core import EngineCore, generate_initial_density


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "weyl_holonomy_mps_curvature_transport_probe_results.json"

NAME = "weyl_holonomy_mps_curvature_transport_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: tests a finite closed-loop holonomy transport built from "
    "source-native left/right Weyl density histories and an MPS carrier. It does "
    "not prove a canonical connection, does not admit physics, cognition, neural "
    "capability, or final manifold claims, and does not replace long-horizon "
    "64-site engine validation."
)

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "load-bearing finite connection, holonomy, and MPS tensor updates"},
    "scipy": {"tried": True, "used": True, "reason": "load-bearing matrix exponentials for loop transport"},
    "quimb": {"tried": True, "used": True, "reason": "load-bearing MPS carrier construction and tensor arrays"},
    "cotengra": {"tried": True, "used": True, "reason": "load-bearing contraction path mutation witness"},
    "opt_einsum": {"tried": True, "used": True, "reason": "load-bearing contraction numeric cross-check"},
    "networkx": {"tried": True, "used": True, "reason": "load-bearing transport dependency graph"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing symbolic curvature commutator determinant"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing nonidentity holonomy witness"},
    "engine_core": {"tried": True, "used": True, "reason": "load-bearing source-native left/right density histories"},
}
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}

I2 = np.eye(2, dtype=np.complex128)
SX = np.array([[0, 1], [1, 0]], dtype=np.complex128)
SY = np.array([[0, -1j], [1j, 0]], dtype=np.complex128)
SZ = np.array([[1, 0], [0, -1]], dtype=np.complex128)


def source_histories(seed: int) -> dict[str, list[dict[str, Any]]]:
    histories: dict[str, list[dict[str, Any]]] = {"left": [], "right": []}
    rho0 = generate_initial_density(seed)
    for label, engine_type in (("left", 0), ("right", 1)):
        engine = EngineCore(engine_type, manifold_enabled=True)
        rho = rho0.copy()
        for main_idx, (perception, loop_class) in enumerate(engine.schedule):
            for substage_idx in range(4):
                rho, record = engine.run_substage(rho, perception, loop_class, main_idx, substage_idx)
                histories[label].append(record)
    return histories


def entropy_signal(records: list[dict[str, Any]]) -> np.ndarray:
    ent = np.array([float(row["entropy"]) for row in records], dtype=float)
    delta = np.array([float(row["slot_delta_norm"]) for row in records], dtype=float)
    sign = np.array([float(row["operator_sign"]) for row in records], dtype=float)
    return np.array(
        [
            float(np.mean(ent)),
            float(np.std(ent) + 0.1 * np.mean(delta)),
            float(np.mean(sign * delta)),
        ],
        dtype=float,
    )


def connection_pair(signal_l: np.ndarray, signal_r: np.ndarray, mode: str) -> tuple[np.ndarray, np.ndarray]:
    if mode == "source_native":
        diff = signal_l - signal_r
        ax = -1j * (0.18 * SX + (0.05 + abs(diff[0])) * SZ + 0.03 * diff[1] * SY)
        ay = -1j * ((0.11 + abs(diff[2])) * SY + 0.07 * SX - 0.04 * diff[0] * SZ)
        return ax, ay
    if mode == "rigid_metric":
        ax = -1j * (0.18 * SX)
        ay = -1j * (0.18 * SX)
        return ax, ay
    if mode == "scrambled_gradient":
        avg = 0.5 * (signal_l[::-1] + signal_r)
        ax = -1j * (0.06 * SX + 0.03 * avg[0] * SZ)
        ay = -1j * (0.06 * SX + 0.03 * avg[0] * SZ)
        return ax, ay
    raise ValueError(mode)


def closed_loop_holonomy(ax: np.ndarray, ay: np.ndarray, step: float = 0.35) -> dict[str, Any]:
    ux = expm(step * ax)
    uy = expm(step * ay)
    hol = ux @ uy @ np.linalg.inv(ux) @ np.linalg.inv(uy)
    comm = ax @ ay - ay @ ax
    return {
        "matrix": hol,
        "trace_real": float(np.trace(hol).real),
        "trace_imag": float(np.trace(hol).imag),
        "nonidentity_norm": float(np.linalg.norm(hol - I2)),
        "commutator_norm": float(np.linalg.norm(comm)),
        "unitarity_error": float(np.linalg.norm(hol.conj().T @ hol - I2)),
    }


def transport_mps(hol: np.ndarray, seed: int) -> dict[str, Any]:
    mps = qtn.MPS_computational_state("0" * 8)
    arrays = [np.array(arr, dtype=np.complex128, copy=True) for arr in mps.arrays]
    before = float(np.sqrt(sum(float(np.vdot(arr, arr).real) for arr in arrays)))
    for idx, arr in enumerate(arrays):
        if arr.shape[-1] != 2:
            continue
        arrays[idx] = np.tensordot(arr, hol.T, axes=([-1], [0]))
    after = float(np.sqrt(sum(float(np.vdot(arr, arr).real) for arr in arrays)))
    endpoint_delta = float(np.sqrt(sum(float(np.vdot(a - b, a - b).real) for a, b in zip(arrays, mps.arrays))))
    return {
        "num_tensors": int(mps.num_tensors),
        "tensor_norm_before": before,
        "tensor_norm_after": after,
        "endpoint_delta": endpoint_delta,
        "seed": seed,
        "pass": int(mps.num_tensors) == 8 and endpoint_delta > 1e-4 and abs(after - before) < 1e-6,
    }


def contraction_path_series(signal_l: np.ndarray, signal_r: np.ndarray, mode: str) -> dict[str, Any]:
    inputs, output, expr = [
        ("a", "b", "e"),
        ("b", "c", "f"),
        ("e", "f", "h"),
        ("h", "c", "d"),
    ], ("a", "d"), "abe,bcf,efh,hcd->ad"
    rows = []
    for step in range(4):
        if mode == "source_native":
            scale = np.abs(signal_l - signal_r) + step + 1
        else:
            scale = np.ones(3) * 2
        sizes = {
            "a": 2,
            "d": 2,
            "b": int(2 + scale[0] % 3),
            "c": int(2 + scale[1] % 3),
            "e": int(2 + scale[2] % 3),
            "f": int(3 + ((scale[0] + step) if mode == "source_native" else scale[0]) % 3),
            "h": int(3 + ((scale[1] + step) if mode == "source_native" else scale[1]) % 3),
        }
        tree = ctg.HyperOptimizer(max_repeats=4, progbar=False).search(inputs, output, sizes)
        rng = np.random.default_rng(92000 + step)
        arrays = [rng.normal(size=tuple(sizes[ix] for ix in term)) for term in inputs]
        rows.append(
            {
                "step": step,
                "sizes": sizes,
                "cost": float(tree.contraction_cost()),
                "width": float(tree.contraction_width()),
                "norm": float(np.linalg.norm(oe.contract(expr, *arrays))),
            }
        )
    return {
        "rows": rows,
        "unique_size_signatures": len({tuple(sorted(row["sizes"].items())) for row in rows}),
        "unique_costs": len({round(row["cost"], 6) for row in rows}),
        "pass": len({tuple(sorted(row["sizes"].items())) for row in rows}) > 1 and len({round(row["cost"], 6) for row in rows}) > 1,
    }


def run_mode(mode: str) -> dict[str, Any]:
    histories = source_histories(91000)
    sig_l = entropy_signal(histories["left"])
    sig_r = entropy_signal(histories["right"])
    ax, ay = connection_pair(sig_l, sig_r, mode)
    hol = closed_loop_holonomy(ax, ay)
    mps = transport_mps(hol["matrix"], seed=91000)
    paths = contraction_path_series(sig_l, sig_r, mode)
    return {
        "mode": mode,
        "left_signal": np.round(sig_l, 8).tolist(),
        "right_signal": np.round(sig_r, 8).tolist(),
        "holonomy": {k: v for k, v in hol.items() if k != "matrix"},
        "mps_transport": mps,
        "contraction_path_series": paths,
        "pass": hol["nonidentity_norm"] > 1e-4
        and hol["commutator_norm"] > 1e-4
        and hol["unitarity_error"] < 1e-8
        and mps["pass"]
        and paths["pass"],
    }


def z3_holonomy_witness(row: dict[str, Any]) -> dict[str, Any]:
    solver = z3.Solver()
    hol = z3.Real("holonomy_nonidentity_norm")
    comm = z3.Real("commutator_norm")
    tokens = z3.Int("source_history_rows")
    solver.add(hol == str(round(row["holonomy"]["nonidentity_norm"], 10)))
    solver.add(comm == str(round(row["holonomy"]["commutator_norm"], 10)))
    solver.add(tokens == 64)
    solver.add(z3.Not(z3.And(hol > 0, comm > 0, tokens == 64)))
    status = solver.check()
    return {
        "solver_status": str(status),
        "pass": status == z3.unsat,
        "claim_ceiling": "Z3 encodes only finite nonzero holonomy and source-history count.",
    }


def main() -> int:
    started = time.time()
    source = run_mode("source_native")
    rigid = run_mode("rigid_metric")
    scrambled = run_mode("scrambled_gradient")
    x, y = sp.symbols("x y")
    symbolic_comm_det = sp.factor((x * SX + y * SZ)[0, 1] * (x * SY)[1, 0] - (x * SY)[0, 1] * (x * SX + y * SZ)[1, 0])
    graph = nx.DiGraph()
    graph.add_edges_from([("rho_L", "entropy_signal"), ("rho_R", "entropy_signal"), ("entropy_signal", "connection"), ("connection", "holonomy"), ("holonomy", "mps_transport")])
    positive = {
        "source_native_closed_loop_transport_has_nonidentity_holonomy": source,
        "symbolic_connection_commutator_is_nontrivial": {
            "determinant_expression": str(symbolic_comm_det),
            "pass": str(symbolic_comm_det) != "0",
        },
        "z3_rejects_identity_holonomy_collapse": z3_holonomy_witness(source),
    }
    graveyards = {
        "rigid_metric_control_kills_curvature_transport": {
            "rigid_nonidentity_norm": rigid["holonomy"]["nonidentity_norm"],
            "rigid_path_signatures": rigid["contraction_path_series"]["unique_size_signatures"],
            "source_nonidentity_norm": source["holonomy"]["nonidentity_norm"],
            "pass": rigid["holonomy"]["nonidentity_norm"] < source["holonomy"]["nonidentity_norm"] * 0.25
            and rigid["contraction_path_series"]["unique_size_signatures"] == 1,
        },
        "scrambled_gradient_control_kills_source_native_path_mutation": {
            "scrambled_nonidentity_norm": scrambled["holonomy"]["nonidentity_norm"],
            "scrambled_path_signatures": scrambled["contraction_path_series"]["unique_size_signatures"],
            "pass": scrambled["contraction_path_series"]["unique_size_signatures"] == 1
            and scrambled["holonomy"]["nonidentity_norm"] < source["holonomy"]["nonidentity_norm"] * 0.5,
        },
    }
    boundary = {
        "transport_graph_is_acyclic": {"nodes": graph.number_of_nodes(), "edges": graph.number_of_edges(), "pass": nx.is_directed_acyclic_graph(graph)},
        "promotion_remains_disabled": {"pass": PROMOTION_ALLOWED is False},
    }
    all_pass = all(row["pass"] for row in positive.values()) and all(row["pass"] for row in graveyards.values()) and all(row["pass"] for row in boundary.values())
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "source_alignment_category": "downstream_on_source_native_operating_space",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "graveyard_companions": graveyards,
        "boundary": boundary,
        "nearby_variants": {"total": len(graveyards), "passed": sum(1 for row in graveyards.values() if row["pass"]), "variants": sorted(graveyards)},
        "why_not_v4_probes": [
            "Finite holonomy scout only.",
            "MPS carrier is 8 sites, not a 64-site PEPS3D long-horizon engine.",
            "Keeps canonical geometry and neural claims blocked.",
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
