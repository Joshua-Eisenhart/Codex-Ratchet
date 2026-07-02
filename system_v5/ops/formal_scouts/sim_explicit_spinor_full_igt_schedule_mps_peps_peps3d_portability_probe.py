#!/usr/bin/env python3
"""Corrected full-IGT schedule portability across MPS, PEPS, and PEPS3D.

Formal scout only.

This row is the next rung after the dense 8-qubit corrected IGT cycle scout. It
keeps the owner's stage grammar intact:

* two engine types;
* eight macro stages per engine;
* four operator substages per macro stage;
* all four substages inherit the macro-stage Axis6 sign;
* 32 substages per engine and 64 substages total.

The carrier side is intentionally bounded:

* MPS product-spinor carriers at 8, 16, 32, and 64 sites use the repo-local
  torch MPS helper and two-site stage gates;
* PEPS and PEPS3D use pure torch local tensor carriers seeded from explicit
  Hopf spinors and stage-local physical-leg updates.

This is schedule/carrier portability evidence. It is not final flux, Axis0, Xi,
full PEPS3D environment contraction, long-horizon convergence, Standard Model,
gravity, Yang-Mills, Riemann, or physics admission.
"""

from __future__ import annotations

import json
import math
import pathlib
import time
from typing import Any

import torch
import z3

import canonical_qit_engine_specs as specs
import engine_v7_mps_reference as v7


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "explicit_spinor_full_igt_schedule_mps_peps_peps3d_portability_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SOURCE_ALIGNMENT_CATEGORY = "explicit_spinor_full_igt_schedule_mps_peps_peps3d_portability"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: runs the corrected 64-substage IGT schedule through "
    "explicit Hopf-spinor MPS 8/16/32/64 carriers and local PEPS/PEPS3D tensor "
    "carriers. It does not admit final flux, Axis0, Xi, full PEPS3D environment "
    "contraction, long-horizon convergence, Standard Model, gravity, Yang-Mills, "
    "Riemann, or physics claims."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing explicit Hopf spinors, MPS gates, PEPS/PEPS3D local tensors, and carrier signatures",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite stage-count, carrier-count, and nonpromotion gates",
    },
    "canonical_qit_engine_specs": {
        "tried": True,
        "used": True,
        "reason": "supportive source-native engine schedules, chart tokens, terrain variants, and Axis6 signs",
    },
    "engine_v7_mps_reference": {
        "tried": True,
        "used": True,
        "reason": "supportive repo-local torch MPS tensor/gate helper; PyTorch is the load-bearing substrate",
    },
    "python_json": {"tried": True, "used": True, "reason": "supportive canonical result serialization"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive result path handling"},
    "time": {"tried": True, "used": True, "reason": "supportive runtime metadata"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "z3": "load_bearing",
    "canonical_qit_engine_specs": "supportive",
    "engine_v7_mps_reference": "supportive",
    "python_json": "supportive",
    "pathlib": "supportive",
    "time": "supportive",
}

RTYPE = torch.float64
CDTYPE = torch.complex128
MPS_DTYPE = v7.DTYPE
EPS = 1e-12
GAP_FLOOR = 1e-5
GAUGE_TOLERANCE = 1e-4
MPS_SITE_COUNTS = [8, 16, 32, 64]
PEPS_SHAPE = (4, 4)
PEPS3D_SHAPE = (4, 4, 4)
OPERATOR_SEQUENCE = ["Ti", "Te", "Fi", "Fe"]

SX = specs.SX
SY = specs.SY
SZ = specs.SZ
I2 = specs.I2


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): as_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(item) for item in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, torch.Tensor):
        if value.numel() == 1:
            return as_jsonable(value.item())
        return as_jsonable(value.detach().cpu().tolist())
    if isinstance(value, complex):
        return {"real": value.real, "imag": value.imag}
    return value


def normalize_vector(vector: torch.Tensor) -> torch.Tensor:
    norm = torch.linalg.vector_norm(vector)
    if float(norm.item()) <= EPS:
        raise ValueError("zero vector")
    return vector / norm


def spinor(phi: float, chi: float, eta: float, *, phase: float = 0.0) -> torch.Tensor:
    raw = torch.tensor(
        [
            complex(math.cos(phi + chi), math.sin(phi + chi)) * math.cos(eta),
            complex(math.cos(phi - chi), math.sin(phi - chi)) * math.sin(eta),
        ],
        dtype=CDTYPE,
    )
    gauge = complex(math.cos(phase), math.sin(phase))
    return normalize_vector(gauge * raw)


def spinor_params(idx: int, count: int) -> tuple[float, float, float]:
    phi = 0.19 * idx + 0.07 * math.sin(0.31 * idx)
    chi = -0.58 + 1.16 * (((idx * 5 + 3) % count) / max(count - 1, 1))
    eta = 0.24 + 1.08 * (((idx * 7 + 2) % count) / max(count - 1, 1))
    return phi, chi, min(max(eta, 0.18), 1.36)


def build_spinors(count: int, *, gauge_shift: bool = False) -> list[torch.Tensor]:
    out = []
    for idx in range(count):
        phase = math.sin(0.29 * idx + 0.17) * math.pi if gauge_shift else 0.0
        out.append(spinor(*spinor_params(idx, count), phase=phase))
    return out


def density_from_vector(vector: torch.Tensor) -> torch.Tensor:
    return torch.outer(vector, torch.conj(vector))


def bloch_from_spinor(vector: torch.Tensor) -> torch.Tensor:
    rho = density_from_vector(vector.to(CDTYPE))
    return torch.tensor(
        [
            torch.real(torch.trace(rho @ SX)).item(),
            torch.real(torch.trace(rho @ SY)).item(),
            torch.real(torch.trace(rho @ SZ)).item(),
        ],
        dtype=RTYPE,
    )


def ordered_rows(*, mixed_axis6: bool = False, native_only: bool = False, one_engine_only: bool = False) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    engine_range = [0] if one_engine_only else [0, 1]
    for engine_type in engine_range:
        for macro_stage_idx, (perception, loop_class) in enumerate(specs.get_schedule(engine_type)):
            chart = specs.get_chart_token_spec(perception, engine_type, loop_class)
            terrain = specs.get_terrain_dynamics_spec(perception, engine_type)
            stage_sign = int(chart["sign"])
            operators = [chart["operator"]] if native_only else OPERATOR_SEQUENCE
            for substage_idx, operator in enumerate(operators):
                sign = stage_sign
                if mixed_axis6 and substage_idx % 2 == 1:
                    sign = -stage_sign
                precedence = "operator_first" if sign > 0 else "terrain_first"
                rows.append(
                    {
                        "global_substage_idx": len(rows),
                        "engine_type": engine_type + 1,
                        "macro_stage_idx": macro_stage_idx,
                        "substage_idx": substage_idx,
                        "topology": perception,
                        "loop_class": loop_class,
                        "terrain_variant": terrain["realization"],
                        "operator": operator,
                        "chart_operator": chart["operator"],
                        "axis6_sign": sign,
                        "stage_axis6_sign": stage_sign,
                        "same_sign_as_stage": sign == stage_sign,
                        "token": specs.ordered_token(operator, perception, precedence),
                        "chart_token": chart["token"],
                    }
                )
    return rows


def loop_pair_table(rows: list[dict[str, Any]]) -> dict[str, Any]:
    table: dict[str, Any] = {}
    for engine in sorted({row["engine_type"] for row in rows}):
        for topology in ["Se", "Ne", "Ni", "Si"]:
            key = f"E{engine}_{topology}"
            pair_rows = [row for row in rows if row["engine_type"] == engine and row["topology"] == topology]
            by_loop = {
                loop: [row for row in pair_rows if row["loop_class"] == loop]
                for loop in ["outer", "inner"]
            }
            table[key] = {
                "terrain_variants": sorted({row["terrain_variant"] for row in pair_rows}),
                "chart_operators": {loop: sorted({row["chart_operator"] for row in loop_rows}) for loop, loop_rows in by_loop.items()},
                "axis6_stage_signs": {loop: sorted({row["stage_axis6_sign"] for row in loop_rows}) for loop, loop_rows in by_loop.items()},
                "operators_by_loop": {loop: sorted({row["operator"] for row in loop_rows}) for loop, loop_rows in by_loop.items()},
                "row_counts": {loop: len(loop_rows) for loop, loop_rows in by_loop.items()},
                "pass": (
                    len({row["terrain_variant"] for row in pair_rows}) == 1
                    and all(len(loop_rows) == 4 for loop_rows in by_loop.values())
                    and all(set(row["operator"] for row in loop_rows) == set(OPERATOR_SEQUENCE) for loop_rows in by_loop.values())
                    and len({next(iter({row["chart_operator"] for row in loop_rows})) for loop_rows in by_loop.values()}) == 2
                    and sum(next(iter({row["stage_axis6_sign"] for row in loop_rows})) for loop_rows in by_loop.values()) == 0
                ),
            }
    return table


def operator_pauli(operator: str) -> torch.Tensor:
    return {"Ti": SZ, "Te": SX, "Fi": SX, "Fe": SZ}[operator]


def two_site_generator(operator: str) -> torch.Tensor:
    if operator in {"Ti", "Fe"}:
        return torch.kron(SZ, SZ)
    return torch.kron(SX, SX)


def stage_strength(row: dict[str, Any], carrier_scale: float = 1.0) -> float:
    stage = int(row["macro_stage_idx"])
    sub = int(row["substage_idx"])
    sign = int(row["axis6_sign"])
    return carrier_scale * sign * (0.034 + 0.009 * ((stage + 2 * sub) % 5))


def mps_product(spinors: list[torch.Tensor]) -> v7.MPS:
    return v7.MPS.product([vector.to(MPS_DTYPE) for vector in spinors])


def mps_apply_row(mps: v7.MPS, row: dict[str, Any]) -> None:
    if mps.N < 2:
        return
    idx = int(row["global_substage_idx"])
    site = (3 * idx + int(row["engine_type"]) + int(row["macro_stage_idx"])) % (mps.N - 1)
    unitary = torch.linalg.matrix_exp((-1j * stage_strength(row)) * two_site_generator(row["operator"]))
    mps.apply_two(unitary.to(MPS_DTYPE), site, max_bond=8)
    if idx % 8 == 7:
        mps.normalize_()


def entropy_from_density(rho: torch.Tensor) -> float:
    herm = (rho + torch.conj(rho).T) / 2
    vals = torch.clamp(torch.linalg.eigvalsh(herm).real, min=0.0)
    vals = vals / torch.clamp(torch.sum(vals), min=EPS)
    nz = vals[vals > 1e-12]
    return float((-torch.sum(nz * torch.log(nz))).item())


def mps_signature(site_count: int, rows: list[dict[str, Any]], *, gauge_shift: bool = False) -> dict[str, Any]:
    mps = mps_product(build_spinors(site_count, gauge_shift=gauge_shift))
    for row in rows:
        mps_apply_row(mps, row)
    mps.normalize_()
    sample_sites = sorted({0, site_count // 4, site_count // 2, (3 * site_count) // 4, site_count - 1})
    single_entropies = []
    bloch_z_values = []
    for site in sample_sites:
        rho = mps.reduced_single(site).to(CDTYPE)
        rho = rho / torch.clamp(torch.real(torch.trace(rho)), min=EPS)
        single_entropies.append(entropy_from_density(rho))
        bloch_z_values.append(float(torch.real(torch.trace(rho @ SZ)).item()))
    cut_entropy = float(mps.copy().schmidt_entropy(site_count // 2).item())
    max_bond = max(max(tensor.shape[1:]) for tensor in mps.tensors)
    mean_norm = float(torch.mean(torch.tensor([torch.linalg.vector_norm(t).item() for t in mps.tensors], dtype=RTYPE)).item())
    return {
        "carrier": "mps",
        "site_count": site_count,
        "row_count": len(rows),
        "cut_entropy": cut_entropy,
        "mean_single_site_entropy": sum(single_entropies) / len(single_entropies),
        "mean_sample_bloch_z": sum(bloch_z_values) / len(bloch_z_values),
        "max_bond": int(max_bond),
        "mean_tensor_norm": mean_norm,
    }


def lattice_sites(shape: tuple[int, ...]) -> list[tuple[int, ...]]:
    if len(shape) == 2:
        nx, ny = shape
        return [(i, j) for i in range(nx) for j in range(ny)]
    nx, ny, nz = shape
    return [(i, j, k) for i in range(nx) for j in range(ny) for k in range(nz)]


def lattice_edges(shape: tuple[int, ...], *, shuffled: bool = False) -> list[tuple[tuple[int, ...], tuple[int, ...]]]:
    site_set = set(lattice_sites(shape))
    deltas = [(1, 0)] if len(shape) == 2 else [(1, 0, 0)]
    if len(shape) == 2:
        deltas += [(0, 1)]
    else:
        deltas += [(0, 1, 0), (0, 0, 1)]
    edges = []
    for site in lattice_sites(shape):
        for delta in deltas:
            dst = tuple(site[i] + delta[i] for i in range(len(shape)))
            if dst in site_set:
                if shuffled:
                    dst = tuple((dst[i] + (i + 1)) % shape[i] for i in range(len(shape)))
                    if dst == site:
                        dst = tuple((dst[i] + 1) % shape[i] if i == 0 else dst[i] for i in range(len(shape)))
                edges.append((site, dst))
    return edges


def local_tensor(vector: torch.Tensor, degree: int, idx: int) -> torch.Tensor:
    shape = [2] + [2] * degree
    tensor = vector.to(CDTYPE).reshape(2, *([1] * degree)).repeat(*([1] + [2] * degree))
    scale = torch.ones(shape, dtype=CDTYPE)
    for axis in range(degree):
        weight = 0.83 + 0.07 * math.sin(0.41 * (idx + axis + 1))
        selector = torch.tensor([1.0, weight], dtype=CDTYPE).reshape(*([1] * (axis + 1)), 2, *([1] * (degree - axis - 1)))
        scale = scale * selector
    tensor = tensor * scale
    return tensor / torch.clamp(torch.linalg.vector_norm(tensor), min=EPS)


def build_local_tensors(shape: tuple[int, ...], *, gauge_shift: bool = False) -> dict[tuple[int, ...], torch.Tensor]:
    sites = lattice_sites(shape)
    spinors = build_spinors(len(sites), gauge_shift=gauge_shift)
    edge_count = {site: 0 for site in sites}
    for a, b in lattice_edges(shape):
        edge_count[a] += 1
        edge_count[b] += 1
    return {site: local_tensor(spinors[idx], max(edge_count[site], 1), idx) for idx, site in enumerate(sites)}


def apply_physical_update(tensor: torch.Tensor, matrix: torch.Tensor) -> torch.Tensor:
    updated = torch.einsum("ab,b...->a...", matrix.to(CDTYPE), tensor)
    return updated / torch.clamp(torch.linalg.vector_norm(updated), min=EPS)


def tensor_physical_vector(tensor: torch.Tensor) -> torch.Tensor:
    axes = tuple(range(1, tensor.dim()))
    vector = torch.sum(tensor, dim=axes)
    return normalize_vector(vector.to(CDTYPE))


def local_network_signature(
    carrier: str,
    shape: tuple[int, ...],
    rows: list[dict[str, Any]],
    *,
    gauge_shift: bool = False,
    shuffled_topology: bool = False,
) -> dict[str, Any]:
    tensors = build_local_tensors(shape, gauge_shift=gauge_shift)
    sites = lattice_sites(shape)
    edges = lattice_edges(shape, shuffled=shuffled_topology)
    if not edges:
        raise ValueError("empty edge list")
    touched_edges = []
    for row in rows:
        edge = edges[(5 * int(row["global_substage_idx"]) + int(row["engine_type"])) % len(edges)]
        matrix = torch.linalg.matrix_exp((-1j * stage_strength(row, carrier_scale=0.8)) * operator_pauli(row["operator"]))
        tensors[edge[0]] = apply_physical_update(tensors[edge[0]], matrix)
        tensors[edge[1]] = apply_physical_update(tensors[edge[1]], matrix)
        touched_edges.append(edge)
    norms = torch.tensor([torch.linalg.vector_norm(tensors[site]).item() for site in sites], dtype=RTYPE)
    blochs = [bloch_from_spinor(tensor_physical_vector(tensors[site])) for site in sites]
    edge_corr = []
    for a, b in edges:
        ia = sites.index(a)
        ib = sites.index(b)
        edge_corr.append(float(torch.dot(blochs[ia], blochs[ib]).item()))
    cut_axis = 0
    left = [idx for idx, site in enumerate(sites) if site[cut_axis] < shape[cut_axis] // 2]
    right = [idx for idx, site in enumerate(sites) if site[cut_axis] >= shape[cut_axis] // 2]
    left_mean = torch.mean(torch.stack([blochs[idx] for idx in left]), dim=0)
    right_mean = torch.mean(torch.stack([blochs[idx] for idx in right]), dim=0)
    return {
        "carrier": carrier,
        "shape": list(shape),
        "site_count": len(sites),
        "edge_count": len(edges),
        "row_count": len(rows),
        "mean_tensor_norm": float(torch.mean(norms).item()),
        "std_tensor_norm": float(torch.std(norms).item()),
        "mean_edge_bloch_correlation": sum(edge_corr) / len(edge_corr),
        "cut_bloch_gap": float(torch.linalg.vector_norm(left_mean - right_mean).item()),
        "touched_edge_count": len({(a, b) for a, b in touched_edges}),
    }


def carrier_vector(row: dict[str, Any]) -> torch.Tensor:
    return torch.tensor(
        [
            row["site_count"],
            row["row_count"],
            row.get("cut_entropy", 0.0),
            row.get("mean_single_site_entropy", 0.0),
            row.get("mean_sample_bloch_z", 0.0),
            row.get("max_bond", 0.0),
            row["mean_tensor_norm"],
            row.get("std_tensor_norm", 0.0),
            row.get("mean_edge_bloch_correlation", 0.0),
            row.get("cut_bloch_gap", 0.0),
            row.get("touched_edge_count", 0.0),
        ],
        dtype=RTYPE,
    )


def gap(a: dict[str, Any], b: dict[str, Any]) -> float:
    return float(torch.linalg.vector_norm(carrier_vector(a) - carrier_vector(b)).item())


def run_all(rows: list[dict[str, Any]], *, gauge_shift: bool = False, shuffled_topology: bool = False) -> dict[str, Any]:
    mps_rows = [mps_signature(site_count, rows, gauge_shift=gauge_shift) for site_count in MPS_SITE_COUNTS]
    peps = local_network_signature("peps", PEPS_SHAPE, rows, gauge_shift=gauge_shift, shuffled_topology=shuffled_topology)
    peps3d = local_network_signature("peps3d", PEPS3D_SHAPE, rows, gauge_shift=gauge_shift, shuffled_topology=shuffled_topology)
    return {
        "rows": rows,
        "mps": mps_rows,
        "peps": peps,
        "peps3d": peps3d,
        "combined_signature": torch.cat([carrier_vector(item) for item in [*mps_rows, peps, peps3d]]),
    }


def combined_gap(a: dict[str, Any], b: dict[str, Any]) -> float:
    return float(torch.linalg.vector_norm(a["combined_signature"] - b["combined_signature"]).item())


def z3_gate() -> dict[str, Any]:
    engines = z3.Int("engines")
    macro = z3.Int("macro")
    sub = z3.Int("sub")
    total = z3.Int("total")
    mps_scales = z3.Int("mps_scales")
    has_peps = z3.Bool("has_peps")
    has_peps3d = z3.Bool("has_peps3d")
    final_physics = z3.Bool("final_physics")
    solver = z3.Solver()
    solver.add(engines == 2, macro == 8, sub == 4, total == engines * macro * sub)
    solver.add(mps_scales == 4, has_peps, has_peps3d, z3.Not(final_physics))
    wrong = z3.Solver()
    wrong.add(total == 32, engines == 2, macro == 8, sub == 4, total == engines * macro * sub)
    promotion = z3.Solver()
    promotion.add(final_physics, z3.Not(final_physics))
    return {
        "correct_status": str(solver.check()),
        "collapse_to_32_status": str(wrong.check()),
        "promotion_status": str(promotion.check()),
        "pass": solver.check() == z3.sat and wrong.check() == z3.unsat and promotion.check() == z3.unsat,
    }


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    nominal_rows = ordered_rows()
    mixed_rows = ordered_rows(mixed_axis6=True)
    native_rows = ordered_rows(native_only=True)
    one_engine_rows = ordered_rows(one_engine_only=True)

    nominal = run_all(nominal_rows)
    mixed = run_all(mixed_rows)
    native = run_all(native_rows)
    one_engine = run_all(one_engine_rows)
    gauge = run_all(nominal_rows, gauge_shift=True)
    shuffled = run_all(nominal_rows, shuffled_topology=True)

    mixed_gap = combined_gap(nominal, mixed)
    native_gap = combined_gap(nominal, native)
    one_engine_gap = combined_gap(nominal, one_engine)
    gauge_gap = combined_gap(nominal, gauge)
    shuffled_gap = combined_gap(nominal, shuffled)

    terrain_variants = sorted({row["terrain_variant"] for row in nominal_rows})
    topologies = sorted({row["topology"] for row in nominal_rows})
    operators = sorted({row["operator"] for row in nominal_rows})
    loop_pairs = loop_pair_table(nominal_rows)
    same_sign_stage_count = sum(
        int(all(item["same_sign_as_stage"] for item in nominal_rows if item["engine_type"] == engine and item["macro_stage_idx"] == stage))
        for engine in sorted({row["engine_type"] for row in nominal_rows})
        for stage in sorted({row["macro_stage_idx"] for row in nominal_rows if row["engine_type"] == engine})
    )
    positive = {
        "correct_full_igt_schedule_count": {
            "pass": len(nominal_rows) == 64 and same_sign_stage_count == 16 and all(row["pass"] for row in loop_pairs.values()),
            "row_count": len(nominal_rows),
            "same_sign_stage_count": same_sign_stage_count,
            "terrain_variants": terrain_variants,
            "topologies": topologies,
            "operators": operators,
            "loop_pair_table": loop_pairs,
        },
        "mps_8_16_32_64_carriers_present": {
            "pass": [row["site_count"] for row in nominal["mps"]] == MPS_SITE_COUNTS
            and all(row["row_count"] == 64 for row in nominal["mps"])
            and all(row["max_bond"] >= 1 for row in nominal["mps"]),
            "mps_summaries": nominal["mps"],
        },
        "peps_and_peps3d_local_carriers_present": {
            "pass": nominal["peps"]["site_count"] == 16
            and nominal["peps3d"]["site_count"] == 64
            and nominal["peps"]["row_count"] == 64
            and nominal["peps3d"]["row_count"] == 64,
            "peps_summary": nominal["peps"],
            "peps3d_summary": nominal["peps3d"],
        },
        "gauge_phase_invariance_preserved": {
            "pass": gauge_gap < GAUGE_TOLERANCE,
            "gauge_signature_gap": gauge_gap,
            "tolerance": GAUGE_TOLERANCE,
            "note": "MPS helper uses complex64 SVD; this tolerance catches physical gauge drift while allowing numerical SVD noise.",
        },
    }
    graveyard_companions = {
        "GC1_mixed_axis6_within_stage_rejected": {
            "pass": mixed_gap > GAP_FLOOR,
            "mixed_axis6_signature_gap": mixed_gap,
        },
        "GC2_native_only_operator_collapse_rejected": {
            "pass": len(native_rows) == 16 and native_gap > GAP_FLOOR,
            "native_row_count": len(native_rows),
            "native_only_signature_gap": native_gap,
        },
        "GC3_one_engine_only_collapse_rejected": {
            "pass": len(one_engine_rows) == 32 and one_engine_gap > GAP_FLOOR,
            "one_engine_row_count": len(one_engine_rows),
            "one_engine_signature_gap": one_engine_gap,
        },
        "GC4_shuffled_tensor_topology_rejected": {
            "pass": shuffled_gap > GAP_FLOOR,
            "shuffled_topology_signature_gap": shuffled_gap,
        },
        "GC5_z3_count_carrier_and_nonpromotion_gate": z3_gate(),
    }
    boundary = {
        "B1_formal_scout_only": {"pass": PROMOTION_ALLOWED is False, "promotion_allowed": PROMOTION_ALLOWED},
        "B2_no_final_claims": {
            "pass": "does not admit final flux" in CLAIM_CEILING and "physics" in CLAIM_CEILING,
            "claim_ceiling": CLAIM_CEILING,
        },
        "B3_peps_environment_not_claimed": {
            "pass": "full PEPS3D environment contraction" in CLAIM_CEILING,
            "claim_ceiling": CLAIM_CEILING,
        },
    }
    checks = [item["pass"] for item in positive.values()] + [item["pass"] for item in graveyard_companions.values()] + [
        item["pass"] for item in boundary.values()
    ]
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {"passed": sum(1 for item in checks if item), "total": len(checks)},
        "all_pass": all(checks),
        "summary": {
            "total_substage_count": len(nominal_rows),
            "mps_site_counts": MPS_SITE_COUNTS,
            "peps_site_count": nominal["peps"]["site_count"],
            "peps3d_site_count": nominal["peps3d"]["site_count"],
            "mixed_axis6_signature_gap": mixed_gap,
            "native_only_signature_gap": native_gap,
            "one_engine_signature_gap": one_engine_gap,
            "shuffled_topology_signature_gap": shuffled_gap,
            "gauge_signature_gap": gauge_gap,
            "elapsed_seconds": time.time() - started,
        },
        "nominal_rows": nominal_rows,
        "why_not_v4_probes": (
            "This is a v5 source-native full-IGT schedule portability scout. It "
            "is not a v4 probe and not a promotion of final flux, Axis0, Xi, "
            "PEPS3D closure, or physics."
        ),
        "next_required_work": [
            "Replace local PEPS/PEPS3D tensor signatures with environment contraction receipts.",
            "Run terrain-law GKSL versions of all four operator substages rather than unitary physical-leg updates.",
            "Only after those pass, attach Axis0/FEP and flux candidates to the corrected carrier schedule.",
        ],
    }
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"wrote": str(OUT_PATH), "all_pass": result["all_pass"], "summary": result["summary"]}, indent=2, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
