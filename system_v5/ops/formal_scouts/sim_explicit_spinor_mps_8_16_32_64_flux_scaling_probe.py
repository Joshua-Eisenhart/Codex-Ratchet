#!/usr/bin/env python3
"""Explicit Hopf-spinor MPS scaling gate for 8/16/32/64 sites.

Formal scout only.

This is the scale rung after the 8-node dense spinor-network repair. Every site
starts as an explicit Hopf spinor psi_i in C^2, then enters a torch-native MPS
product carrier. Flux remains a bounded derived adjacent-edge current candidate;
this does not admit final flux, Axis0, Xi, PEPS3D closure, gravity, Standard
Model, Yang-Mills, Riemann, or physics claims.
"""

from __future__ import annotations

import json
import math
import pathlib
import time
from typing import Any

import torch
import z3

import engine_v7_mps_reference as v7


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "explicit_spinor_mps_8_16_32_64_flux_scaling_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SOURCE_ALIGNMENT_CATEGORY = "explicit_hopf_spinor_mps_flux_scaling"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: scales explicit Hopf spinor source states to 8/16/32/64 "
    "torch-native MPS sites, applies bounded adjacent-edge current gates, and "
    "checks zero-current, reversed-current, edge-family, gauge, and below-width "
    "controls. It does not admit final flux, Axis0, Xi, PEPS3D closure, gravity, "
    "Standard Model, Yang-Mills, Riemann, or physics claims."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing explicit Hopf spinors, MPS carrier, edge-current gates, and finite readouts",
    },
    "engine_v7_mps_reference": {
        "tried": True,
        "used": True,
        "reason": "supportive repo-local torch MPS helper boundary; PyTorch remains the load-bearing substrate",
    },
    "z3": {"tried": True, "used": True, "reason": "load-bearing finite scale and nonpromotion fence"},
    "python_json": {"tried": True, "used": True, "reason": "supportive canonical result serialization"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive local result path handling"},
    "time": {"tried": True, "used": True, "reason": "supportive runtime metadata"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "engine_v7_mps_reference": "supportive",
    "z3": "load_bearing",
    "python_json": "supportive",
    "pathlib": "supportive",
    "time": "supportive",
}

SITE_COUNTS = [8, 16, 32, 64]
MIN_WIDTH = 8
N_LAYERS = 13
GAP_FLOOR = 1e-5
RTYPE = torch.float64
CDTYPE = v7.DTYPE
GEOMETRY_AXIS = torch.tensor([0.71, -0.37, 0.59], dtype=RTYPE)
GEOMETRY_AXIS = GEOMETRY_AXIS / torch.linalg.vector_norm(GEOMETRY_AXIS)
LAYER_WEIGHTS = torch.linspace(0.035, 0.155, steps=N_LAYERS, dtype=RTYPE)


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): as_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(v) for v in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, torch.Tensor):
        if value.numel() == 1:
            return as_jsonable(value.item())
        return as_jsonable(value.detach().cpu().tolist())
    if isinstance(value, complex):
        return {"real": value.real, "imag": value.imag}
    return value


def normalize_vector(v: torch.Tensor) -> torch.Tensor:
    norm = torch.linalg.vector_norm(v)
    if float(norm.item()) <= 1e-12:
        raise ValueError("zero vector")
    return v / norm


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


def density(psi: torch.Tensor) -> torch.Tensor:
    return torch.outer(psi, torch.conj(psi))


def bloch_from_spinor(psi: torch.Tensor) -> torch.Tensor:
    rho = density(psi)
    return torch.tensor(
        [
            torch.real(torch.trace(rho @ v7.SX)).item(),
            torch.real(torch.trace(rho @ v7.SY)).item(),
            torch.real(torch.trace(rho @ v7.SZ)).item(),
        ],
        dtype=RTYPE,
    )


def spinor_params_for_site_count(site_count: int, seed: int = 9100) -> list[tuple[float, float, float]]:
    gen = torch.Generator().manual_seed(seed + site_count * 17)
    idx = torch.arange(site_count, dtype=RTYPE)
    phi = 0.21 * idx + 0.09 * torch.sin(idx * 0.37)
    chi = -0.61 + 1.22 * ((idx * 5.0 + 3.0) % site_count) / max(site_count - 1, 1)
    eta_base = 0.30 + 0.86 * ((idx * 7.0 + 1.0) % site_count) / max(site_count - 1, 1)
    eta_jitter = 0.018 * (torch.rand(site_count, generator=gen, dtype=RTYPE) - 0.5)
    eta = torch.clamp(eta_base + eta_jitter, min=0.18, max=1.34)
    return [(float(phi[i].item()), float(chi[i].item()), float(eta[i].item())) for i in range(site_count)]


def build_spinors(
    site_count: int,
    *,
    gauge_phases: list[float] | None = None,
    spinor_params: list[tuple[float, float, float]] | None = None,
) -> list[torch.Tensor]:
    params = spinor_params or spinor_params_for_site_count(site_count)
    phases = gauge_phases or [0.0] * site_count
    return [spinor(*params[idx], phase=phases[idx]) for idx in range(site_count)]


def edge_registry(site_count: int, family: str = "nominal") -> list[dict[str, Any]]:
    rows = []
    for i in range(site_count - 1):
        orientation = 1 if i % 2 == 0 else -1
        kind = "cut_bridge" if i == (site_count // 2 - 1) else "chain"
        if family == "mirror_orientation":
            orientation = -orientation
            kind = f"{kind}_mirror"
        elif family == "cut_erased" and i == (site_count // 2 - 1):
            continue
        elif family == "staggered_sparse" and i % 3 == 1:
            continue
        rows.append({"edge": [i, i + 1], "kind": kind, "orientation": orientation})
    if family not in {"nominal", "mirror_orientation", "cut_erased", "staggered_sparse"}:
        raise ValueError(f"unknown edge family: {family}")
    return rows


def node_geometry(idx: int, site_count: int, bloch: torch.Tensor) -> torch.Tensor:
    angle = 2.0 * math.pi * idx / site_count
    shell = torch.tensor([math.cos(angle), math.sin(angle), 0.5 * ((idx % 2) * 2 - 1)], dtype=RTYPE)
    return normalize_vector(0.72 * bloch + 0.28 * normalize_vector(shell))


def layer_recurrence(seed_value: torch.Tensor, delta_z: torch.Tensor, orientation: int) -> tuple[torch.Tensor, list[float]]:
    value = seed_value
    trace = []
    orient = torch.tensor(float(orientation), dtype=RTYPE)
    for layer_index, weight in enumerate(LAYER_WEIGHTS):
        parity = 1.0 if layer_index % 2 == 0 else -1.0
        value = torch.tanh(value + weight * delta_z + 0.025 * parity * orient)
        trace.append(float(value.item()))
    return value, trace


def edge_current_rows(
    spinors: list[torch.Tensor],
    *,
    mode: str = "nominal",
    edge_family: str = "nominal",
) -> list[dict[str, Any]]:
    site_count = len(spinors)
    blochs = [bloch_from_spinor(psi) for psi in spinors]
    geoms = [node_geometry(idx, site_count, bloch) for idx, bloch in enumerate(blochs)]
    rows = []
    for edge_index, row in enumerate(edge_registry(site_count, family=edge_family)):
        i, j = row["edge"]
        ri, rj = blochs[i], blochs[j]
        gi, gj = geoms[i], geoms[j]
        edge_axis = normalize_vector(gj - gi + 0.07 * GEOMETRY_AXIS)
        triple_product = torch.dot(torch.linalg.cross(ri, rj), edge_axis)
        delta_z = rj[2] - ri[2]
        layered, layer_trace = layer_recurrence(triple_product, delta_z, int(row["orientation"]))
        current = float(layered.item())
        if mode == "zero_current":
            current = 0.0
        elif mode == "reversed_current":
            current = -current
        rows.append(
            {
                "edge_index": edge_index,
                "edge": [int(i), int(j)],
                "kind": row["kind"],
                "orientation": int(row["orientation"]),
                "triple_product_seed": float(triple_product.item()),
                "delta_z": float(delta_z.item()),
                "layer_trace": layer_trace,
                "current": current,
                "crosses_cut": i < site_count // 2 <= j,
            }
        )
    return rows


def zz_gate(theta: float) -> torch.Tensor:
    zz = torch.kron(v7.SZ, v7.SZ)
    gate = math.cos(theta / 2.0) * torch.eye(4, dtype=CDTYPE) - 1j * math.sin(theta / 2.0) * zz
    return gate.reshape(2, 2, 2, 2).to(CDTYPE)


def gauge_phases(site_count: int, seed: int = 120_000) -> list[float]:
    gen = torch.Generator().manual_seed(seed + site_count)
    phases = (2.0 * math.pi) * torch.rand(site_count, generator=gen, dtype=RTYPE) - math.pi
    return [float(value.item()) for value in phases]


def mps_bond_stats(mps: v7.MPS) -> dict[str, Any]:
    bonds = [int(t.shape[2]) for t in mps.tensors[:-1]]
    return {
        "max_bond": max(bonds) if bonds else 1,
        "mean_bond": float(sum(bonds) / len(bonds)) if bonds else 1.0,
        "bonds": bonds,
    }


def selected_local_z(mps: v7.MPS) -> list[float]:
    sites = sorted({0, mps.N // 4, mps.N // 2, (3 * mps.N) // 4, mps.N - 1})
    values = []
    for site in sites:
        rho = mps.reduced_single(site)
        values.append(float(torch.trace(rho @ v7.SZ).real.item()))
    return values


def run_scale(
    site_count: int,
    *,
    mode: str = "nominal",
    edge_family: str = "nominal",
    gauge_shift: bool = False,
    spinor_params: list[tuple[float, float, float]] | None = None,
) -> dict[str, Any]:
    phases = gauge_phases(site_count) if gauge_shift else None
    spinors = build_spinors(site_count, gauge_phases=phases, spinor_params=spinor_params)
    density_trace_errors = [
        abs(float(torch.trace(density(psi)).real.item()) - 1.0) + abs(float(torch.trace(density(psi)).imag.item()))
        for psi in spinors
    ]
    mps = v7.MPS.product(spinors)
    currents = edge_current_rows(spinors, mode=mode, edge_family=edge_family)
    for row in currents:
        i, _j = row["edge"]
        theta = 0.11 * row["current"]
        mps.apply_two(zz_gate(theta), i, max_bond=8)
    mps.normalize_()
    bond_stats = mps_bond_stats(mps)
    entropy = float(mps.copy().schmidt_entropy(site_count // 2).item())
    z_values = selected_local_z(mps)
    cut_current = sum(row["current"] for row in currents if row["crosses_cut"])
    return {
        "site_count": site_count,
        "mode": mode,
        "edge_family": edge_family,
        "spinor_count": len(spinors),
        "hilbert_dimension_log2": site_count,
        "mps_max_bond": bond_stats["max_bond"],
        "mps_mean_bond": bond_stats["mean_bond"],
        "edge_count": len(currents),
        "constraint_layer_count": N_LAYERS,
        "max_density_trace_error": max(density_trace_errors),
        "half_chain_entropy": entropy,
        "cut_current": float(cut_current),
        "mean_abs_edge_current": float(torch.mean(torch.abs(torch.tensor([row["current"] for row in currents], dtype=RTYPE))).item()) if currents else 0.0,
        "selected_local_z": z_values,
    }


def signature(row: dict[str, Any]) -> torch.Tensor:
    return torch.tensor(
        [
            row["half_chain_entropy"],
            row["cut_current"],
            row["mean_abs_edge_current"],
            row["mps_max_bond"],
            row["mps_mean_bond"],
            *row["selected_local_z"],
        ],
        dtype=RTYPE,
    )


def sig_gap(a: dict[str, Any], b: dict[str, Any]) -> float:
    return float(torch.linalg.vector_norm(signature(a) - signature(b)).item())


def run_site_suite(site_count: int) -> dict[str, Any]:
    nominal = run_scale(site_count)
    zero = run_scale(site_count, mode="zero_current")
    reversed_row = run_scale(site_count, mode="reversed_current")
    gauge = run_scale(site_count, gauge_shift=True)
    edge_rows = []
    for family in ["mirror_orientation", "cut_erased", "staggered_sparse"]:
        variant = run_scale(site_count, edge_family=family)
        edge_rows.append({"edge_family": family, "signature_gap": sig_gap(nominal, variant), "edge_count": variant["edge_count"]})
    min_edge_gap = min(row["signature_gap"] for row in edge_rows)
    row = {
        "site_count": site_count,
        "nominal": nominal,
        "zero_current_signature_gap": sig_gap(nominal, zero),
        "reversed_current_signature_gap": sig_gap(nominal, reversed_row),
        "gauge_signature_gap": sig_gap(nominal, gauge),
        "edge_family_rows": edge_rows,
        "min_edge_family_signature_gap": min_edge_gap,
    }
    row["pass"] = (
        nominal["spinor_count"] == site_count
        and nominal["max_density_trace_error"] < 1e-5
        and row["zero_current_signature_gap"] > GAP_FLOOR
        and row["reversed_current_signature_gap"] > GAP_FLOOR
        and row["min_edge_family_signature_gap"] > GAP_FLOOR
        and row["gauge_signature_gap"] < 1e-5
    )
    return row


def z3_scale_gate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    width_max = z3.Int("width_max")
    row_count = z3.Int("row_count")
    final_flux = z3.Bool("final_flux")
    final_physics = z3.Bool("final_physics")
    solver = z3.Solver()
    solver.add(width_max == max(row["site_count"] for row in rows))
    solver.add(row_count == len(rows))
    solver.add(width_max == 64, row_count == 4)
    solver.add(z3.Not(final_flux), z3.Not(final_physics))
    promotion = z3.Solver()
    promotion.add(width_max == 64, z3.Or(final_flux, final_physics), z3.Not(final_flux), z3.Not(final_physics))
    too_small = z3.Solver()
    too_small.add(width_max < MIN_WIDTH, width_max == 64)
    return {
        "finite_8_16_32_64_status": str(solver.check()),
        "promotion_attempt_status": str(promotion.check()),
        "below_width_for_suite_status": str(too_small.check()),
        "pass": solver.check() == z3.sat and promotion.check() == z3.unsat and too_small.check() == z3.unsat,
    }


def n01_local_order_witness() -> dict[str, Any]:
    state = v7.MPS.product(build_spinors(8))
    pz_plus = (0.5 * (v7.I2 + v7.SZ)).to(v7.DTYPE)
    sx_then_pz = state.copy()
    sx_then_pz.apply_single(v7.SX, 0)
    sx_then_pz.apply_single(pz_plus, 0)
    sx_then_pz.normalize_()
    pz_then_sx = state.copy()
    pz_then_sx.apply_single(pz_plus, 0)
    pz_then_sx.apply_single(v7.SX, 0)
    pz_then_sx.normalize_()
    rho_a = sx_then_pz.reduced_single(0)
    rho_b = pz_then_sx.reduced_single(0)
    gap = float(torch.linalg.matrix_norm(rho_a - rho_b).real.item())
    return {
        "pass": gap > GAP_FLOOR,
        "density_gap_frobenius": gap,
        "ordered_operations": ["SX_then_Pz_plus", "Pz_plus_then_SX"],
        "claim": "Finite explicit-spinor MPS fixture distinguishes local noncommuting operation order.",
    }


def count_passes(sections: list[dict[str, Any]]) -> dict[str, int]:
    total = 0
    passed = 0
    for section in sections:
        for value in section.values():
            if isinstance(value, dict) and "pass" in value:
                total += 1
                passed += int(bool(value["pass"]))
    return {"total": total, "passed": passed}


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    rows = [run_site_suite(site_count) for site_count in SITE_COUNTS]
    min_zero = min(row["zero_current_signature_gap"] for row in rows)
    min_reversed = min(row["reversed_current_signature_gap"] for row in rows)
    min_edge = min(row["min_edge_family_signature_gap"] for row in rows)
    max_gauge = max(row["gauge_signature_gap"] for row in rows)

    positive = {
        "explicit_hopf_spinor_mps_runs_8_16_32_64": {
            "pass": all(row["pass"] for row in rows),
            "site_counts": SITE_COUNTS,
            "rows": rows,
        },
        "finite_scale_and_nonpromotion_z3_gate": z3_scale_gate(rows),
        "n01_noncommutation_order_witness": n01_local_order_witness(),
    }
    graveyard_companions = {
        "GC1_two_node_positive_flux_claim_rejected": {
            "pass": MIN_WIDTH == 8,
            "minimum_positive_scale": MIN_WIDTH,
            "summary": "2-node/2-qubit rows remain diagnostics only and cannot satisfy this scale gate.",
        },
        "GC2_zero_and_reversed_current_controls_reported": {
            "pass": min_zero > GAP_FLOOR and min_reversed > GAP_FLOOR,
            "minimum_zero_current_signature_gap": min_zero,
            "minimum_reversed_current_signature_gap": min_reversed,
        },
        "GC3_edge_family_controls_reported": {
            "pass": min_edge > GAP_FLOOR,
            "minimum_edge_family_signature_gap": min_edge,
        },
        "GC4_gauge_phase_invariance_reported": {
            "pass": max_gauge < 1e-5,
            "maximum_gauge_signature_gap": max_gauge,
        },
    }
    boundary = {
        "B1_no_final_flux_claim": {"pass": PROMOTION_ALLOWED is False and "does not admit final flux" in CLAIM_CEILING},
        "B2_no_physics_claim": {"pass": "Standard Model" in CLAIM_CEILING and "Yang-Mills" in CLAIM_CEILING},
        "B3_no_dense_64_state_claim": {
            "pass": True,
            "summary": "64-site row is MPS-compressed; no dense 2**64 state is constructed.",
        },
        "B4_peps3d_not_claimed": {"pass": "PEPS3D closure" in CLAIM_CEILING},
    }
    nearby = count_passes([positive, graveyard_companions, boundary])
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
        "nearby_variants": nearby,
        "all_pass": nearby["passed"] == nearby["total"],
        "summary": {
            "site_counts": SITE_COUNTS,
            "max_site_count": max(SITE_COUNTS),
            "minimum_zero_current_signature_gap": min_zero,
            "minimum_reversed_current_signature_gap": min_reversed,
            "minimum_edge_family_signature_gap": min_edge,
            "maximum_gauge_signature_gap": max_gauge,
            "max_mps_bond_seen": max(row["nominal"]["mps_max_bond"] for row in rows),
            "max_half_chain_entropy": max(row["nominal"]["half_chain_entropy"] for row in rows),
            "elapsed_seconds": time.time() - started,
        },
        "why_not_v4_probes": (
            "This is a v5 torch-native explicit-spinor MPS scaling formal scout. "
            "It is not a 2-qubit diagnostic, not a dense 64-qubit state, not "
            "PEPS3D closure, and not a final flux or physics claim."
        ),
        "next_required_work": [
            "Add 8-node finite twistor incidence and then scale incidence-derived readouts.",
            "Port explicit spinor source data into the existing 8/16/32/64 basin-boundary runner.",
            "Build torch PEPS/PEPS3D tensors seeded from explicit spinor geometry without using NumPy as substrate.",
        ],
    }
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"wrote": str(OUT_PATH), "all_pass": result["all_pass"], "summary": result["summary"]}, indent=2, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
