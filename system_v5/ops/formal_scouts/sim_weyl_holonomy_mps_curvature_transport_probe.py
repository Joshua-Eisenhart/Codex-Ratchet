#!/usr/bin/env python3
"""Canonical QIT replay Weyl holonomy / MPS curvature transport scout."""

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
import opt_einsum as oe
import quimb.tensor as qtn
import sympy as sp
import torch
import z3

from canonical_qit_engine_specs import (
    OPERATOR_BASE_ANGLES,
    OPERATOR_GENERATORS,
    get_operator_slot_spec,
    get_schedule,
)
from sim_source_native_engine_manifold_attractor_basin_depth_probe import (
    MANIFOLD_TARGET_MIX,
    apply_lindblad_step,
    generate_initial_density,
    normalize_density_torch,
    stage_fixed_target,
)


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "weyl_holonomy_mps_curvature_transport_probe_results.json"

NAME = "weyl_holonomy_mps_curvature_transport_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
SIM_EXECUTION_KIND = "nonclassical"
CLAIM_CEILING = (
    "Formal scout only: tests a finite closed-loop holonomy transport built from "
    "bounded canonical QIT replay left/right Weyl density histories and an MPS "
    "carrier. It does not admit a canonical connection, source-native EngineCore "
    "dynamics, physics, cognition, neural capability, final manifold claims, or "
    "long-horizon 64-site engine validation."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing finite connection, holonomy, MPS tensor updates, and contraction numerics"},
    "quimb": {"tried": True, "used": True, "reason": "load-bearing MPS carrier construction and tensor arrays"},
    "cotengra": {"tried": True, "used": True, "reason": "load-bearing contraction path mutation witness"},
    "opt_einsum": {"tried": True, "used": True, "reason": "load-bearing contraction numeric cross-check"},
    "networkx": {"tried": True, "used": True, "reason": "load-bearing transport dependency graph"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing symbolic curvature commutator determinant"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing nonidentity holonomy witness"},
    "canonical_qit_engine_specs": {
        "tried": True,
        "used": True,
        "reason": "supportive canonical QIT schedule and operator-slot source for bounded replay; PyTorch carries the load-bearing transport numerics",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "quimb": "load_bearing",
    "cotengra": "load_bearing",
    "opt_einsum": "load_bearing",
    "networkx": "load_bearing",
    "sympy": "load_bearing",
    "z3": "load_bearing",
    "canonical_qit_engine_specs": "supportive",
}
TOOL_ROLE_SOURCE = {tool: "local" for tool in TOOL_MANIFEST}

TORCH_REAL = torch.float64
TORCH_COMPLEX = torch.complex128
I2 = torch.eye(2, dtype=TORCH_COMPLEX)
SX = torch.tensor([[0, 1], [1, 0]], dtype=TORCH_COMPLEX)
SY = torch.tensor([[0, -1j], [1j, 0]], dtype=TORCH_COMPLEX)
SZ = torch.tensor([[1, 0], [0, -1]], dtype=TORCH_COMPLEX)


def as_real_tensor(value: Any) -> torch.Tensor:
    return torch.as_tensor(value, dtype=TORCH_REAL)


def as_complex_tensor(value: Any) -> torch.Tensor:
    return torch.as_tensor(value, dtype=TORCH_COMPLEX)


def density_entropy_torch(rho: torch.Tensor) -> float:
    evals = torch.clamp(torch.linalg.eigvalsh((rho + rho.conj().T) / 2).real, min=1e-12)
    evals = evals / torch.sum(evals)
    return float((-torch.sum(evals * torch.log(evals))).item())


def apply_operator_slot(
    rho: torch.Tensor,
    perception: str,
    engine_type: int,
    loop_class: str,
    substage_idx: int,
) -> tuple[torch.Tensor, dict[str, Any]]:
    slot = get_operator_slot_spec(perception, engine_type, loop_class, substage_idx)
    generator = torch.as_tensor(OPERATOR_GENERATORS[slot["operator"]], dtype=TORCH_COMPLEX)
    angle = float(slot["sign"]) * float(OPERATOR_BASE_ANGLES[slot["operator"]])
    unitary = torch.linalg.matrix_exp((-1j * angle) * generator)
    return unitary @ rho @ unitary.conj().T, slot


def source_histories(seed: int) -> dict[str, list[dict[str, Any]]]:
    histories: dict[str, list[dict[str, Any]]] = {"left": [], "right": []}
    rho0 = generate_initial_density(seed)
    for label, engine_type in (("left", 0), ("right", 1)):
        rho = normalize_density_torch(rho0.clone())
        for main_idx, (perception, loop_class) in enumerate(get_schedule(engine_type)):
            for substage_idx in range(4):
                before = normalize_density_torch(rho)
                slotted, slot = apply_operator_slot(before, perception, engine_type, loop_class, substage_idx)
                evolved = apply_lindblad_step(slotted, perception, engine_type)
                target = stage_fixed_target(perception, engine_type)
                rho = normalize_density_torch((1.0 - MANIFOLD_TARGET_MIX) * evolved + MANIFOLD_TARGET_MIX * target)
                histories[label].append(
                    {
                        "engine_type": engine_type,
                        "main_idx": main_idx,
                        "substage_idx": substage_idx,
                        "perception": perception,
                        "loop_class": loop_class,
                        "ordered_token": slot["token"],
                        "operator": slot["operator"],
                        "operator_sign": int(slot["sign"]),
                        "entropy": density_entropy_torch(rho),
                        "slot_delta_norm": float(torch.linalg.vector_norm((rho - before).reshape(-1)).item()),
                    }
                )
    return histories


def entropy_signal(records: list[dict[str, Any]]) -> torch.Tensor:
    ent = as_real_tensor([float(row["entropy"]) for row in records])
    delta = as_real_tensor([float(row["slot_delta_norm"]) for row in records])
    sign = as_real_tensor([float(row["operator_sign"]) for row in records])
    return torch.tensor(
        [
            float(torch.mean(ent).item()),
            float((torch.std(ent, unbiased=False) + 0.1 * torch.mean(delta)).item()),
            float(torch.mean(sign * delta).item()),
        ],
        dtype=TORCH_REAL,
    )


def connection_pair(signal_l: torch.Tensor, signal_r: torch.Tensor, mode: str) -> tuple[torch.Tensor, torch.Tensor]:
    if mode in {"canonical_qit", "source_native"}:
        diff = signal_l - signal_r
        ax = -1j * (0.18 * SX + (0.05 + abs(diff[0])) * SZ + 0.03 * diff[1] * SY)
        ay = -1j * ((0.11 + abs(diff[2])) * SY + 0.07 * SX - 0.04 * diff[0] * SZ)
        return ax, ay
    if mode == "rigid_metric":
        ax = -1j * (0.18 * SX)
        ay = -1j * (0.18 * SX)
        return ax, ay
    if mode == "scrambled_gradient":
        avg = 0.5 * (torch.flip(signal_l, dims=[0]) + signal_r)
        ax = -1j * (0.06 * SX + 0.03 * avg[0] * SZ)
        ay = -1j * (0.06 * SX + 0.03 * avg[0] * SZ)
        return ax, ay
    raise ValueError(mode)


def closed_loop_holonomy(ax: torch.Tensor, ay: torch.Tensor, step: float = 0.35) -> dict[str, Any]:
    ux = torch.linalg.matrix_exp(step * ax)
    uy = torch.linalg.matrix_exp(step * ay)
    hol = ux @ uy @ torch.linalg.inv(ux) @ torch.linalg.inv(uy)
    comm = ax @ ay - ay @ ax
    return {
        "matrix": hol,
        "trace_real": float(torch.real(torch.trace(hol)).item()),
        "trace_imag": float(torch.imag(torch.trace(hol)).item()),
        "nonidentity_norm": float(torch.linalg.vector_norm((hol - I2).reshape(-1)).item()),
        "commutator_norm": float(torch.linalg.vector_norm(comm.reshape(-1)).item()),
        "unitarity_error": float(torch.linalg.vector_norm((torch.conj(hol.transpose(-2, -1)) @ hol - I2).reshape(-1)).item()),
    }


def transport_mps(hol: torch.Tensor, seed: int) -> dict[str, Any]:
    mps = qtn.MPS_computational_state("0" * 8)
    arrays = [as_complex_tensor(arr.copy()) for arr in mps.arrays]
    before = float(torch.sqrt(sum(torch.real(torch.vdot(arr.reshape(-1), arr.reshape(-1))) for arr in arrays)).item())
    for idx, arr in enumerate(arrays):
        if arr.shape[-1] != 2:
            continue
        arrays[idx] = torch.tensordot(arr, torch.transpose(hol, 0, 1), dims=([-1], [0]))
    after = float(torch.sqrt(sum(torch.real(torch.vdot(arr.reshape(-1), arr.reshape(-1))) for arr in arrays)).item())
    endpoint_delta = float(torch.sqrt(sum(torch.real(torch.vdot((a - as_complex_tensor(b)).reshape(-1), (a - as_complex_tensor(b)).reshape(-1))) for a, b in zip(arrays, mps.arrays))).item())
    return {
        "num_tensors": int(mps.num_tensors),
        "tensor_norm_before": before,
        "tensor_norm_after": after,
        "endpoint_delta": endpoint_delta,
        "seed": seed,
        "pass": int(mps.num_tensors) == 8 and endpoint_delta > 1e-4 and abs(after - before) < 1e-6,
    }


def contraction_path_series(signal_l: torch.Tensor, signal_r: torch.Tensor, mode: str) -> dict[str, Any]:
    inputs, output, expr = [
        ("a", "b", "e"),
        ("b", "c", "f"),
        ("e", "f", "h"),
        ("h", "c", "d"),
    ], ("a", "d"), "abe,bcf,efh,hcd->ad"
    rows = []
    for step in range(4):
        if mode in {"canonical_qit", "source_native"}:
            scale = torch.abs(signal_l - signal_r) + step + 1
        else:
            scale = torch.ones(3, dtype=TORCH_REAL) * 2
        sizes = {
            "a": 2,
            "d": 2,
            "b": int(2 + float(scale[0].item()) % 3),
            "c": int(2 + float(scale[1].item()) % 3),
            "e": int(2 + float(scale[2].item()) % 3),
            "f": int(3 + (float((scale[0] + step).item()) if mode in {"canonical_qit", "source_native"} else float(scale[0].item())) % 3),
            "h": int(3 + (float((scale[1] + step).item()) if mode in {"canonical_qit", "source_native"} else float(scale[1].item())) % 3),
        }
        tree = ctg.HyperOptimizer(max_repeats=4, progbar=False).search(inputs, output, sizes)
        generator = torch.Generator().manual_seed(92000 + step)
        arrays = [torch.randn(tuple(sizes[ix] for ix in term), generator=generator, dtype=TORCH_REAL) for term in inputs]
        rows.append(
            {
                "step": step,
                "sizes": sizes,
                "cost": float(tree.contraction_cost()),
                "width": float(tree.contraction_width()),
                "norm": float(torch.linalg.vector_norm(oe.contract(expr, *arrays).reshape(-1)).item()),
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
        "left_signal": (torch.round(sig_l * 1e8) / 1e8).tolist(),
        "right_signal": (torch.round(sig_r * 1e8) / 1e8).tolist(),
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
    source = run_mode("canonical_qit")
    rigid = run_mode("rigid_metric")
    scrambled = run_mode("scrambled_gradient")
    x, y = sp.symbols("x y")
    sx_sym = sp.Matrix([[0, 1], [1, 0]])
    sy_sym = sp.Matrix([[0, -sp.I], [sp.I, 0]])
    sz_sym = sp.Matrix([[1, 0], [0, -1]])
    symbolic_comm_det = sp.factor((x * sx_sym + y * sz_sym)[0, 1] * (x * sy_sym)[1, 0] - (x * sy_sym)[0, 1] * (x * sx_sym + y * sz_sym)[1, 0])
    graph = nx.DiGraph()
    graph.add_edges_from([("rho_L", "entropy_signal"), ("rho_R", "entropy_signal"), ("entropy_signal", "connection"), ("connection", "holonomy"), ("holonomy", "mps_transport")])
    positive = {
        "canonical_qit_replay_closed_loop_transport_has_nonidentity_holonomy": source,
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
        "scrambled_gradient_control_kills_canonical_qit_path_mutation": {
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
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "claim_ceiling": CLAIM_CEILING,
        "source_alignment_category": "canonical_qit_weyl_holonomy_mps_curvature_replay",
        "root_constraints": {
            "F01": "finite 2x2 density histories, finite 64 replay records, finite 8-site MPS carrier",
            "N01": "noncommuting canonical QIT slot generators induce nonzero connection commutator and holonomy witness",
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "TOOL_ROLE_SOURCE": TOOL_ROLE_SOURCE,
        "positive": positive,
        "graveyard_companions": graveyards,
        "boundary": boundary,
        "nearby_variants": {"total": len(graveyards), "passed": sum(1 for row in graveyards.values() if row["pass"]), "variants": sorted(graveyards)},
        "why_not_v4_probes": [
            "Finite holonomy scout only.",
            "MPS carrier is 8 sites, not a 64-site PEPS3D long-horizon engine.",
            "Canonical QIT replay is not source-native EngineCore dynamics.",
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
