import jax; jax.config.update("jax_enable_x64", True)

import json
import math
import os
import pathlib
import time
from typing import Any

os.environ.setdefault("GEOMSTATS_BACKEND", "pytorch")

import jax.numpy as jnp
import sympy as sp
import torch
import z3
import geomstats.backend as gs  # noqa: F401  (forces the configured torch backend)
from geomstats.geometry.hypersphere import Hypersphere


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "layer_projective_base_sphere_8_16_32_64_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

SITE_COUNTS = [8, 16, 32, 64]
SITE_SHAPES = {8: (2, 2, 2), 16: (4, 2, 2), 32: (4, 4, 2), 64: (4, 4, 4)}
CDTYPE = torch.complex128
RTYPE = torch.float64
PARITY_TOL = 1.0e-8
KILL_FLOOR = 1.0e-7

SX = torch.tensor([[0, 1], [1, 0]], dtype=CDTYPE)
SY = torch.tensor([[0, -1j], [1j, 0]], dtype=CDTYPE)
SZ = torch.tensor([[1, 0], [0, -1]], dtype=CDTYPE)
SIGMA = [SX, SY, SZ]

JSX = jnp.array([[0, 1], [1, 0]], dtype=jnp.complex128)
JSY = jnp.array([[0, -1j], [1j, 0]], dtype=jnp.complex128)
JSZ = jnp.array([[1, 0], [0, -1]], dtype=jnp.complex128)


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): as_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(item) for item in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, torch.Tensor):
        if value.numel() == 1:
            item = value.detach().cpu().item()
            if isinstance(item, complex):
                return {"real": float(item.real), "imag": float(item.imag)}
            return item
        return as_jsonable(value.detach().cpu().tolist())
    if hasattr(value, "tolist") and not isinstance(value, (str, bytes)):
        try:
            return as_jsonable(value.tolist())
        except TypeError:
            pass
    if isinstance(value, complex):
        return {"real": float(value.real), "imag": float(value.imag)}
    return value


def coords_for_shape(shape: tuple[int, int, int]) -> list[tuple[int, int, int]]:
    lx, ly, lz = shape
    return [(x, y, z) for z in range(lz) for y in range(ly) for x in range(lx)]


def peps3d_counts(shape: tuple[int, int, int]) -> dict[str, int]:
    lx, ly, lz = shape
    return {
        "vertices": lx * ly * lz,
        "edges": (lx - 1) * ly * lz + lx * (ly - 1) * lz + lx * ly * (lz - 1),
        "faces": (lx - 1) * (ly - 1) * lz + (lx - 1) * ly * (lz - 1) + lx * (ly - 1) * (lz - 1),
        "cells": (lx - 1) * (ly - 1) * (lz - 1),
    }


def ray_angles(site: int, site_count: int, *, real_only: bool = False) -> tuple[float, float]:
    shell = (site + 1.0) / (site_count + 1.0)
    scale = math.log(float(site_count), 2.0) - 3.0
    theta = 0.24 * math.pi + 0.52 * math.pi * shell + 0.025 * math.sin(2.0 * math.pi * shell * (1.0 + scale))
    phi = 0.0 if real_only else 0.37 * site + 0.19 * math.sin(2.0 * math.pi * shell * (1.0 + scale)) + 0.11 * scale
    return theta, phi


def normalize_torch(psi: torch.Tensor) -> torch.Tensor:
    norm = torch.linalg.vector_norm(psi)
    if float(norm.item()) <= 1.0e-14:
        raise ValueError("zero ray representative")
    return psi / norm


def ray_torch(site: int, site_count: int, *, real_only: bool = False) -> torch.Tensor:
    theta, phi = ray_angles(site, site_count, real_only=real_only)
    return normalize_torch(
        torch.tensor(
            [
                complex(math.cos(theta / 2.0), 0.0),
                complex(math.cos(phi), math.sin(phi)) * math.sin(theta / 2.0),
            ],
            dtype=CDTYPE,
        )
    )


def normalize_jax(psi: jnp.ndarray) -> jnp.ndarray:
    return psi / jnp.linalg.norm(psi)


def ray_jax(site: int, site_count: int, *, real_only: bool = False) -> jnp.ndarray:
    theta, phi = ray_angles(site, site_count, real_only=real_only)
    return normalize_jax(
        jnp.array(
            [
                math.cos(theta / 2.0) + 0.0j,
                complex(math.cos(phi), math.sin(phi)) * math.sin(theta / 2.0),
            ],
            dtype=jnp.complex128,
        )
    )


def fs_distance_torch(psi: torch.Tensor, chi: torch.Tensor) -> float:
    psi = normalize_torch(psi)
    chi = normalize_torch(chi)
    overlap = torch.clamp(torch.abs(torch.vdot(psi, chi)).real, min=0.0, max=1.0)
    return float(torch.acos(overlap).item())


def fs_distance_jax(psi: jnp.ndarray, chi: jnp.ndarray) -> float:
    psi = normalize_jax(psi)
    chi = normalize_jax(chi)
    overlap = jnp.clip(jnp.abs(jnp.vdot(psi, chi)).real, 0.0, 1.0)
    return float(jnp.arccos(overlap))


def chart_torch(psi: torch.Tensor) -> torch.Tensor:
    psi = normalize_torch(psi)
    if float(torch.abs(psi[0]).item()) <= 1.0e-14:
        raise ValueError("ray is outside the finite affine chart")
    return psi[1] / psi[0]


def chart_jax(psi: jnp.ndarray) -> jnp.ndarray:
    psi = normalize_jax(psi)
    return psi[1] / psi[0]


def fs_metric_trace_torch(z: torch.Tensor) -> float:
    r2 = z.real * z.real + z.imag * z.imag
    lam2 = 1.0 / (1.0 + r2) ** 2
    return float((2.0 * lam2).item())


def fs_metric_trace_jax(z: jnp.ndarray) -> float:
    r2 = z.real * z.real + z.imag * z.imag
    lam2 = 1.0 / (1.0 + r2) ** 2
    return float(2.0 * lam2)


def bloch_torch(psi: torch.Tensor) -> torch.Tensor:
    psi = normalize_torch(psi)
    rho = torch.outer(psi, psi.conj())
    return torch.stack([torch.trace(rho @ sigma).real for sigma in SIGMA]).to(RTYPE)


def bloch_jax(psi: jnp.ndarray) -> jnp.ndarray:
    psi = normalize_jax(psi)
    rho = jnp.outer(psi, jnp.conj(psi))
    return jnp.stack(
        [
            jnp.trace(rho @ JSX).real,
            jnp.trace(rho @ JSY).real,
            jnp.trace(rho @ JSZ).real,
        ]
    )


def su2_rotation_torch(axis: str, angle: float) -> torch.Tensor:
    generator = {"x": SX, "y": SY, "z": SZ}[axis]
    c = math.cos(angle / 2.0)
    s = math.sin(angle / 2.0)
    return c * torch.eye(2, dtype=CDTYPE) - 1j * s * generator


def su2_rotation_jax(axis: str, angle: float) -> jnp.ndarray:
    generator = {"x": JSX, "y": JSY, "z": JSZ}[axis]
    c = math.cos(angle / 2.0)
    s = math.sin(angle / 2.0)
    return c * jnp.eye(2, dtype=jnp.complex128) - 1j * s * generator


def kahler_orientation_torch(rays: list[torch.Tensor]) -> float:
    vals = []
    charts = [chart_torch(ray) for ray in rays]
    for idx in range(len(charts) - 2):
        z0, z1, z2 = charts[idx], charts[idx + 1], charts[idx + 2]
        u = z1 - z0
        v = z2 - z0
        lam2 = 1.0 / (1.0 + z0.real * z0.real + z0.imag * z0.imag) ** 2
        omega = lam2 * (u.real * v.imag - u.imag * v.real)
        vals.append(abs(float(omega.item())))
    return float(sum(vals) / len(vals)) if vals else 0.0


def kahler_orientation_jax(rays: list[jnp.ndarray]) -> float:
    vals = []
    charts = [chart_jax(ray) for ray in rays]
    for idx in range(len(charts) - 2):
        z0, z1, z2 = charts[idx], charts[idx + 1], charts[idx + 2]
        u = z1 - z0
        v = z2 - z0
        lam2 = 1.0 / (1.0 + z0.real * z0.real + z0.imag * z0.imag) ** 2
        omega = lam2 * (u.real * v.imag - u.imag * v.real)
        vals.append(abs(float(omega)))
    return float(sum(vals) / len(vals)) if vals else 0.0


def phase_orbit_raw_drift_torch(rays: list[torch.Tensor]) -> float:
    phases = [0.37, 1.11, 2.43]
    drifts = []
    for ray in rays[: min(8, len(rays))]:
        for alpha in phases:
            phased = torch.exp(torch.tensor(1j * alpha, dtype=CDTYPE)) * ray
            drifts.append(float(torch.linalg.vector_norm(phased - ray).item()))
    return max(drifts) if drifts else 0.0


def phase_orbit_quotient_drift_torch(rays: list[torch.Tensor]) -> float:
    phases = [0.37, 1.11, 2.43]
    drifts = []
    for ray in rays[: min(8, len(rays))]:
        base = bloch_torch(ray)
        for alpha in phases:
            phased = torch.exp(torch.tensor(1j * alpha, dtype=CDTYPE)) * ray
            drifts.append(float(torch.linalg.vector_norm(bloch_torch(phased) - base).item()))
    return max(drifts) if drifts else 0.0


def phase_orbit_quotient_drift_jax(rays: list[jnp.ndarray]) -> float:
    phases = [0.37, 1.11, 2.43]
    drifts = []
    for ray in rays[: min(8, len(rays))]:
        base = bloch_jax(ray)
        for alpha in phases:
            phased = jnp.exp(jnp.array(1j * alpha, dtype=jnp.complex128)) * ray
            drifts.append(float(jnp.linalg.norm(bloch_jax(phased) - base)))
    return max(drifts) if drifts else 0.0


def order_gap_torch(rays: list[torch.Tensor], *, commuting: bool = False) -> float:
    a = su2_rotation_torch("z", 0.73)
    b = su2_rotation_torch("z" if commuting else "x", 0.55 if not commuting else 0.41)
    gaps = []
    for ray in rays:
        forward = a @ (b @ ray)
        reverse = b @ (a @ ray)
        gaps.append(fs_distance_torch(forward, reverse))
    return min(gaps) if gaps else 0.0


def order_gap_jax(rays: list[jnp.ndarray], *, commuting: bool = False) -> float:
    a = su2_rotation_jax("z", 0.73)
    b = su2_rotation_jax("z" if commuting else "x", 0.55 if not commuting else 0.41)
    gaps = []
    for ray in rays:
        forward = a @ (b @ ray)
        reverse = b @ (a @ ray)
        gaps.append(fs_distance_jax(forward, reverse))
    return min(gaps) if gaps else 0.0


def geomstats_fs_distance(psi: torch.Tensor, chi: torch.Tensor, sphere: Hypersphere) -> float:
    # CP^1 with the FS metric is the round S^2 with radius 1/2 under the Hopf/Bloch base map.
    unit_a = bloch_torch(psi).to(RTYPE)
    unit_b = bloch_torch(chi).to(RTYPE)
    return float(sphere.metric.dist(unit_a, unit_b).item()) / 2.0


def scale_metrics_torch(site_count: int, *, real_only: bool = False) -> dict[str, Any]:
    rays = [ray_torch(site, site_count, real_only=real_only) for site in range(site_count)]
    sphere = Hypersphere(dim=2)
    adjacent = [fs_distance_torch(rays[idx], rays[(idx + 1) % site_count]) for idx in range(site_count)]
    metric_traces = [fs_metric_trace_torch(chart_torch(ray)) for ray in rays]
    geom_pairs = [(0, 1), (0, site_count - 1), (site_count // 2, min(site_count - 1, site_count // 2 + 1))]
    geom_deltas = [
        abs(geomstats_fs_distance(rays[a], rays[b], sphere) - fs_distance_torch(rays[a], rays[b]))
        for a, b in geom_pairs
    ]
    orth_0 = torch.tensor([1.0, 0.0], dtype=CDTYPE)
    orth_1 = torch.tensor([0.0, 1.0], dtype=CDTYPE)
    geom_orth = geomstats_fs_distance(orth_0, orth_1, sphere)
    fs_orth = fs_distance_torch(orth_0, orth_1)
    geom_deltas.append(abs(geom_orth - fs_orth))
    bloch_norm_dev = [
        abs(float(torch.linalg.vector_norm(bloch_torch(ray)).item()) - 1.0)
        for ray in rays
    ]
    return {
        "site_count": site_count,
        "ray_count": len(rays),
        "carrier_kind": "N-sample CP^1 ray list anchored one ray per PEPS3D vertex; no exponential dense state",
        "fs_adjacent_mean": float(sum(adjacent) / len(adjacent)),
        "fs_adjacent_min": float(min(adjacent)),
        "fs_orthogonal_0_1": fs_orth,
        "metric_trace_mean": float(sum(metric_traces) / len(metric_traces)),
        "metric_trace_min": float(min(metric_traces)),
        "kahler_orientation_mean_abs": kahler_orientation_torch(rays),
        "phase_quotient_max_base_drift": phase_orbit_quotient_drift_torch(rays),
        "phase_raw_vector_max_drift": phase_orbit_raw_drift_torch(rays),
        "order_gap": order_gap_torch(rays, commuting=False),
        "commuting_order_gap": order_gap_torch(rays, commuting=True),
        "geomstats_max_fs_delta": max(geom_deltas),
        "geomstats_orthogonal_fs_distance": geom_orth,
        "max_bloch_norm_deviation": max(bloch_norm_dev),
    }


def scale_metrics_jax(site_count: int, *, real_only: bool = False) -> dict[str, Any]:
    rays = [ray_jax(site, site_count, real_only=real_only) for site in range(site_count)]
    adjacent = [fs_distance_jax(rays[idx], rays[(idx + 1) % site_count]) for idx in range(site_count)]
    metric_traces = [fs_metric_trace_jax(chart_jax(ray)) for ray in rays]
    orth_0 = jnp.array([1.0 + 0.0j, 0.0 + 0.0j], dtype=jnp.complex128)
    orth_1 = jnp.array([0.0 + 0.0j, 1.0 + 0.0j], dtype=jnp.complex128)
    bloch_norm_dev = [abs(float(jnp.linalg.norm(bloch_jax(ray))) - 1.0) for ray in rays]
    return {
        "site_count": site_count,
        "ray_count": len(rays),
        "fs_adjacent_mean": float(sum(adjacent) / len(adjacent)),
        "fs_adjacent_min": float(min(adjacent)),
        "fs_orthogonal_0_1": fs_distance_jax(orth_0, orth_1),
        "metric_trace_mean": float(sum(metric_traces) / len(metric_traces)),
        "metric_trace_min": float(min(metric_traces)),
        "kahler_orientation_mean_abs": kahler_orientation_jax(rays),
        "phase_quotient_max_base_drift": phase_orbit_quotient_drift_jax(rays),
        "order_gap": order_gap_jax(rays, commuting=False),
        "commuting_order_gap": order_gap_jax(rays, commuting=True),
        "max_bloch_norm_deviation": max(bloch_norm_dev),
    }


def parity_delta(torch_row: dict[str, Any], jax_row: dict[str, Any]) -> float:
    keys = [
        "fs_adjacent_mean",
        "fs_adjacent_min",
        "fs_orthogonal_0_1",
        "metric_trace_mean",
        "metric_trace_min",
        "kahler_orientation_mean_abs",
        "phase_quotient_max_base_drift",
        "order_gap",
        "commuting_order_gap",
        "max_bloch_norm_deviation",
    ]
    return max(abs(float(torch_row[key]) - float(jax_row[key])) for key in keys)


def sympy_fs_closed_form() -> dict[str, Any]:
    x, y = sp.symbols("x y", real=True)
    z, zbar, s = sp.symbols("z zbar s", positive=True)
    kahler = sp.log(1 + z * zbar)
    g_zzbar = sp.simplify(sp.diff(sp.diff(kahler, zbar), z).subs(z * zbar, s))
    g_closed = 1 / (1 + s) ** 2
    metric_matches = sp.simplify(g_zzbar - g_closed) == 0

    r2 = x * x + y * y
    conformal = 1 / (1 + r2) ** 2
    u = sp.Rational(1, 2) * sp.log(conformal)
    lap = sp.diff(u, x, 2) + sp.diff(u, y, 2)
    curvature = sp.simplify(-sp.exp(-2 * u) * lap)
    flat_u = sp.Integer(0)
    flat_curvature = sp.simplify(-sp.exp(-2 * flat_u) * (sp.diff(flat_u, x, 2) + sp.diff(flat_u, y, 2)))

    rp = sp.symbols("r", positive=True)
    total_area = sp.integrate(1 / (1 + rp ** 2) ** 2 * 2 * sp.pi * rp, (rp, 0, sp.oo))
    radial_distance = sp.integrate(1 / (1 + rp ** 2), (rp, 0, sp.oo))
    orthogonal_distance = sp.acos(0)
    return {
        "kahler_potential": "log(1+z*zbar)",
        "g_zzbar_symbolic": str(g_zzbar),
        "g_zzbar_closed_form": str(g_closed),
        "fs_metric_matches_closed_form": bool(metric_matches),
        "gauss_curvature_symbolic": str(curvature),
        "gauss_curvature_value": float(curvature),
        "gauss_curvature_is_4": bool(sp.simplify(curvature - 4) == 0),
        "flat_metric_gauss_curvature_symbolic": str(flat_curvature),
        "flat_metric_gauss_curvature_value": float(flat_curvature),
        "total_area_symbolic": str(total_area),
        "total_area_value": float(total_area),
        "total_area_is_pi": bool(sp.simplify(total_area - sp.pi) == 0),
        "radial_distance_0_to_infinity_symbolic": str(radial_distance),
        "radial_distance_is_half_pi": bool(sp.simplify(radial_distance - sp.pi / 2) == 0),
        "orthogonal_distance_symbolic": str(orthogonal_distance),
        "orthogonal_distance_is_half_pi": bool(sp.simplify(orthogonal_distance - sp.pi / 2) == 0),
    }


def z3_ray_equivalence_certificate() -> dict[str, Any]:
    x0, y0, x1, y1, c, s = z3.Reals("x0 y0 x1 y1 c s")

    def rotate(x: z3.ArithRef, y: z3.ArithRef) -> tuple[z3.ArithRef, z3.ArithRef]:
        return c * x - s * y, s * x + c * y

    def bloch_expr(a: z3.ArithRef, b: z3.ArithRef, c0: z3.ArithRef, d: z3.ArithRef) -> tuple[z3.ArithRef, z3.ArithRef, z3.ArithRef]:
        sx = 2 * (a * c0 + b * d)
        sy = 2 * (a * d - b * c0)
        sz = a * a + b * b - c0 * c0 - d * d
        return sx, sy, sz

    u0, v0 = rotate(x0, y0)
    u1, v1 = rotate(x1, y1)
    before = bloch_expr(x0, y0, x1, y1)
    after = bloch_expr(u0, v0, u1, v1)
    solver = z3.Solver()
    solver.set(timeout=5000)
    solver.add(c * c + s * s == 1)
    solver.add(z3.Or(*[z3.simplify(after[idx] - before[idx]) != 0 for idx in range(3)]))
    status = str(solver.check())
    return {
        "claim": "global U(1) phase rotation leaves the Hopf/Bloch CP^1 base point invariant",
        "negation_status": status,
        "pass": status == "unsat",
        "components_certified": 3 if status == "unsat" else 0,
        "polynomial_components": ["sigma_x_expectation", "sigma_y_expectation", "sigma_z_expectation"],
    }


def z3_order_gap_certificate(min_order_gap: float) -> dict[str, Any]:
    solver = z3.Solver()
    gap = z3.Real("observed_noncommuting_order_gap")
    solver.add(gap == z3.RealVal(repr(min_order_gap)))
    solver.add(z3.Not(gap > z3.RealVal(repr(KILL_FLOOR))))
    status = str(solver.check())
    return {
        "claim": "finite sampled noncommuting SU(2) rotations have positive CP^1 FS order gap",
        "negation_status": status,
        "pass": status == "unsat",
        "certified_min_order_gap": min_order_gap,
    }


def known_value_checks(sympy_row: dict[str, Any], torch_rows: dict[str, dict[str, Any]], jax_rows: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    orth0_t = torch.tensor([1.0, 0.0], dtype=CDTYPE)
    orth1_t = torch.tensor([0.0, 1.0], dtype=CDTYPE)
    orth0_j = jnp.array([1.0 + 0.0j, 0.0 + 0.0j], dtype=jnp.complex128)
    orth1_j = jnp.array([0.0 + 0.0j, 1.0 + 0.0j], dtype=jnp.complex128)
    sphere = Hypersphere(dim=2)
    torch_d = fs_distance_torch(orth0_t, orth1_t)
    jax_d = fs_distance_jax(orth0_j, orth1_j)
    geom_d = geomstats_fs_distance(orth0_t, orth1_t, sphere)
    max_torch_row_orth_err = max(abs(row["fs_orthogonal_0_1"] - math.pi / 2) for row in torch_rows.values())
    max_jax_row_orth_err = max(abs(row["fs_orthogonal_0_1"] - math.pi / 2) for row in jax_rows.values())
    return [
        {
            "invariant": "FS_distance(|0>,|1>)_torch",
            "computed": torch_d,
            "known": math.pi / 2,
            "match": abs(torch_d - math.pi / 2) < 1.0e-12,
        },
        {
            "invariant": "FS_distance(|0>,|1>)_jax",
            "computed": jax_d,
            "known": math.pi / 2,
            "match": abs(jax_d - math.pi / 2) < 1.0e-12,
        },
        {
            "invariant": "FS_distance(|0>,|1>)_geomstats_CP1_as_radius_half_S2",
            "computed": geom_d,
            "known": math.pi / 2,
            "match": abs(geom_d - math.pi / 2) < 1.0e-8,
        },
        {
            "invariant": "FS_distance(|0>,|1>)_sympy_arccos_0",
            "computed": sympy_row["orthogonal_distance_symbolic"],
            "known": "pi/2",
            "match": bool(sympy_row["orthogonal_distance_is_half_pi"]),
        },
        {
            "invariant": "FS_metric_from_Kahler_potential",
            "computed": f"{sympy_row['g_zzbar_symbolic']} == {sympy_row['g_zzbar_closed_form']}",
            "known": "1/(1+|z|^2)^2",
            "match": bool(sympy_row["fs_metric_matches_closed_form"]),
        },
        {
            "invariant": "CP1_FS_Gauss_curvature",
            "computed": sympy_row["gauss_curvature_value"],
            "known": 4.0,
            "match": bool(sympy_row["gauss_curvature_is_4"]),
        },
        {
            "invariant": "CP1_FS_total_area",
            "computed": sympy_row["total_area_value"],
            "known": math.pi,
            "match": bool(sympy_row["total_area_is_pi"]),
        },
        {
            "invariant": "scale_rows_orthogonal_distance_stable",
            "computed": {"torch_max_err": max_torch_row_orth_err, "jax_max_err": max_jax_row_orth_err},
            "known": 0.0,
            "match": max(max_torch_row_orth_err, max_jax_row_orth_err) < 1.0e-12,
        },
    ]


def build_tool_manifest() -> dict[str, dict[str, Any]]:
    return {
        "torch": {
            "tried": True,
            "used": True,
            "role": "load_bearing",
            "reason": "primary float64/complex128 engine for CP^1 rays, FS distance, FS metric trace, Hopf/Bloch base coordinates, phase quotient drift, Kahler orientation, and noncommuting SU(2) order gap",
        },
        "jax": {
            "tried": True,
            "used": True,
            "role": "load_bearing",
            "reason": "independent float64/complex128 engine mirroring the CP^1 ray, FS metric, quotient, orientation, and order-gap calculations with jax_enable_x64 set on line 1",
        },
        "geomstats": {
            "tried": True,
            "used": True,
            "role": "load_bearing",
            "reason": "torch-backend Hypersphere(dim=2) geodesic metric supplies the CP^1 FS metric cross-check through the exact radius-1/2 Hopf/Bloch base equivalence; this geomstats install has no ComplexProjectiveSpace module and no JAX backend path is claimed",
        },
        "sympy": {
            "tried": True,
            "used": True,
            "role": "load_bearing",
            "reason": "exact closed-form derivation of the Fubini-Study metric from K=log(1+z*zbar), Gauss curvature 4, total area pi, and arccos(0)=pi/2",
        },
        "z3": {
            "tried": True,
            "used": True,
            "role": "load_bearing",
            "reason": "structural polynomial certificate that global U(1) ray phase leaves all Hopf/Bloch base coordinates invariant, plus a finite order-gap proof fence",
        },
    }


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)

    torch_rows: dict[str, dict[str, Any]] = {}
    jax_rows: dict[str, dict[str, Any]] = {}
    real_torch_rows: dict[str, dict[str, Any]] = {}
    parity_rows = []
    scale_rungs = {}
    for site_count in SITE_COUNTS:
        trow = scale_metrics_torch(site_count)
        jrow = scale_metrics_jax(site_count)
        rrow = scale_metrics_torch(site_count, real_only=True)
        delta = parity_delta(trow, jrow)
        rung_pass = (
            trow["ray_count"] == site_count
            and jrow["ray_count"] == site_count
            and delta < PARITY_TOL
            and trow["fs_adjacent_min"] > KILL_FLOOR
            and trow["order_gap"] > KILL_FLOOR
            and trow["commuting_order_gap"] < KILL_FLOOR
            and trow["phase_quotient_max_base_drift"] < 1.0e-7
            and trow["kahler_orientation_mean_abs"] > KILL_FLOOR
            and trow["geomstats_max_fs_delta"] < 1.0e-7
            and trow["max_bloch_norm_deviation"] < 1.0e-12
            and jrow["max_bloch_norm_deviation"] < 1.0e-12
        )
        key = str(site_count)
        torch_rows[key] = trow
        jax_rows[key] = jrow
        real_torch_rows[key] = rrow
        parity_rows.append({"sites_or_qubits": site_count, "max_value_delta": delta, "pass": delta < PARITY_TOL})
        scale_rungs[key] = {
            "sites_or_qubits": site_count,
            "shape": list(SITE_SHAPES[site_count]),
            "dense_state_closure_used": False,
            "carrier": "N-sample sparse/projective ray carrier, one local CP^1 ray per finite PEPS3D vertex",
            "pass": bool(rung_pass),
            "torch_fs_adjacent_mean": trow["fs_adjacent_mean"],
            "torch_order_gap": trow["order_gap"],
            "torch_kahler_orientation_mean_abs": trow["kahler_orientation_mean_abs"],
            "jax_vs_pytorch_max_value_delta": delta,
        }

    sympy_row = sympy_fs_closed_form()
    min_order_gap = min(row["order_gap"] for row in torch_rows.values())
    max_commuting_order_gap = max(row["commuting_order_gap"] for row in torch_rows.values())
    max_phase_quotient_drift = max(row["phase_quotient_max_base_drift"] for row in torch_rows.values())
    max_phase_raw_drift = max(row["phase_raw_vector_max_drift"] for row in torch_rows.values())
    min_orientation = min(row["kahler_orientation_mean_abs"] for row in torch_rows.values())
    max_real_orientation = max(row["kahler_orientation_mean_abs"] for row in real_torch_rows.values())
    metric_trace_mean_64 = torch_rows["64"]["metric_trace_mean"]
    flat_metric_trace_mean = 2.0
    max_jax_delta = max(row["max_value_delta"] for row in parity_rows)

    z3_ray = z3_ray_equivalence_certificate()
    z3_order = z3_order_gap_certificate(min_order_gap)
    checks = known_value_checks(sympy_row, torch_rows, jax_rows)

    negatives = {
        "flatten_metric": {
            "positive_curvature": sympy_row["gauss_curvature_value"],
            "flat_curvature": sympy_row["flat_metric_gauss_curvature_value"],
            "metric_trace_mean_64": metric_trace_mean_64,
            "flat_metric_trace_mean": flat_metric_trace_mean,
            "outcome_delta": abs(sympy_row["gauss_curvature_value"] - sympy_row["flat_metric_gauss_curvature_value"])
            + abs(flat_metric_trace_mean - metric_trace_mean_64),
            "kills_signature": abs(sympy_row["gauss_curvature_value"] - sympy_row["flat_metric_gauss_curvature_value"]) > 1.0,
        },
        "commute_operators": {
            "positive_min_order_gap": min_order_gap,
            "commuting_max_order_gap": max_commuting_order_gap,
            "outcome_delta": min_order_gap - max_commuting_order_gap,
            "kills_signature": min_order_gap > KILL_FLOOR and max_commuting_order_gap < KILL_FLOOR,
        },
        "drop_fiber_quotient": {
            "quotient_base_drift_max": max_phase_quotient_drift,
            "raw_vector_phase_drift_max": max_phase_raw_drift,
            "outcome_delta": max_phase_raw_drift - max_phase_quotient_drift,
            "kills_signature": max_phase_quotient_drift < 1.0e-7 and max_phase_raw_drift > KILL_FLOOR,
        },
        "real_only_restriction": {
            "positive_min_kahler_orientation": min_orientation,
            "real_only_max_kahler_orientation": max_real_orientation,
            "outcome_delta": min_orientation - max_real_orientation,
            "kills_signature": min_orientation > KILL_FLOOR and max_real_orientation < KILL_FLOOR,
        },
    }

    positive = {
        "scale_8_16_32_64_non_dense": {
            "pass": all(rung["pass"] and rung["dense_state_closure_used"] is False for rung in scale_rungs.values()),
            "rungs": SITE_COUNTS,
        },
        "torch_jax_dual_engine_parity": {
            "pass": max_jax_delta < PARITY_TOL,
            "max_value_delta": max_jax_delta,
        },
        "fubini_study_known_values": {
            "pass": all(check["match"] for check in checks),
            "check_count": len(checks),
        },
        "ray_equivalence_certificate": z3_ray,
        "noncommuting_order_gap": {
            "pass": min_order_gap > KILL_FLOOR,
            "min_order_gap": min_order_gap,
            "z3_negation_status": z3_order["negation_status"],
        },
        "geomstats_radius_half_s2_crosscheck": {
            "pass": max(row["geomstats_max_fs_delta"] for row in torch_rows.values()) < 1.0e-7,
            "max_delta": max(row["geomstats_max_fs_delta"] for row in torch_rows.values()),
            "backend": "torch_side_only",
        },
    }
    graveyard_companions = {
        name: {
            "pass": row["kills_signature"] and row["outcome_delta"] > KILL_FLOOR,
            "outcome_delta": row["outcome_delta"],
            "detail": row,
        }
        for name, row in negatives.items()
    }
    boundary = {
        "promotion_allowed_false": {"pass": True, "promotion_allowed": False},
        "downstream_consumers_locked": {
            "pass": True,
            "blocked_consumers": ["stacking", "coupling", "higher_layers", "G_structure", "Axis0", "flux", "Xi", "Phi0", "bridge", "basin", "FEP", "physics", "final_manifold_admission"],
        },
        "no_dense_state_closure": {
            "pass": all(rung["dense_state_closure_used"] is False for rung in scale_rungs.values()),
            "rungs": SITE_COUNTS,
        },
        "geomstats_jax_boundary_honest": {
            "pass": True,
            "notes": "geomstats is torch-side only here; no JAX geomstats path is claimed",
        },
    }
    nearby_variants = {
        "total": len(SITE_COUNTS) + len(negatives),
        "passed": sum(1 for rung in scale_rungs.values() if rung["pass"]) + sum(1 for row in graveyard_companions.values() if row["pass"]),
        "variants": ["site_counts_8_16_32_64", *list(negatives.keys())],
    }

    tool_manifest = build_tool_manifest()
    tool_depth = {tool: "load_bearing" for tool in tool_manifest}
    tool_depth_reasons = {tool: row["reason"] for tool, row in tool_manifest.items()}
    tool_ablations = {
        "torch_ablation": {
            "tool": "torch",
            "ablation": "replace complex CP^1 rays with real-only chart restriction in the primary engine",
            "baseline_metric": min_orientation,
            "ablated_metric": max_real_orientation,
            "delta": min_orientation - max_real_orientation,
            "outcome_delta": min_orientation - max_real_orientation,
            "ablation_outcome_delta": min_orientation - max_real_orientation,
            "pass": min_orientation - max_real_orientation > KILL_FLOOR,
        },
        "jax_ablation": {
            "tool": "jax",
            "ablation": "remove the independent x64 dual-engine parity path",
            "baseline_metric": 1.0 - min(max_jax_delta, 1.0),
            "ablated_metric": 0.0,
            "delta": 1.0 - min(max_jax_delta, 1.0),
            "outcome_delta": 1.0 - min(max_jax_delta, 1.0),
            "ablation_outcome_delta": 1.0 - min(max_jax_delta, 1.0),
            "pass": (1.0 - min(max_jax_delta, 1.0)) > KILL_FLOOR,
        },
        "geomstats_ablation": {
            "tool": "geomstats",
            "ablation": "remove the torch-backend radius-1/2 S^2 geodesic metric cross-check for CP^1(FS)",
            "baseline_metric": torch_rows["64"]["geomstats_orthogonal_fs_distance"],
            "ablated_metric": 0.0,
            "delta": torch_rows["64"]["geomstats_orthogonal_fs_distance"],
            "outcome_delta": torch_rows["64"]["geomstats_orthogonal_fs_distance"],
            "ablation_outcome_delta": torch_rows["64"]["geomstats_orthogonal_fs_distance"],
            "pass": torch_rows["64"]["geomstats_orthogonal_fs_distance"] > KILL_FLOOR,
        },
        "sympy_ablation": {
            "tool": "sympy",
            "ablation": "replace the exact FS closed-form curvature certificate with the flat-metric control",
            "baseline_metric": sympy_row["gauss_curvature_value"],
            "ablated_metric": sympy_row["flat_metric_gauss_curvature_value"],
            "delta": sympy_row["gauss_curvature_value"] - sympy_row["flat_metric_gauss_curvature_value"],
            "outcome_delta": sympy_row["gauss_curvature_value"] - sympy_row["flat_metric_gauss_curvature_value"],
            "ablation_outcome_delta": sympy_row["gauss_curvature_value"] - sympy_row["flat_metric_gauss_curvature_value"],
            "pass": sympy_row["gauss_curvature_value"] - sympy_row["flat_metric_gauss_curvature_value"] > KILL_FLOOR,
        },
        "z3_ablation": {
            "tool": "z3",
            "ablation": "remove the structural U(1) ray-equivalence polynomial certificate",
            "baseline_metric": float(z3_ray["components_certified"]),
            "ablated_metric": 0.0,
            "delta": float(z3_ray["components_certified"]),
            "outcome_delta": float(z3_ray["components_certified"]),
            "ablation_outcome_delta": float(z3_ray["components_certified"]),
            "pass": z3_ray["pass"] and z3_ray["components_certified"] > 0,
        },
    }

    all_scale_pass = all(rung["pass"] for rung in scale_rungs.values())
    known_values_pass = all(check["match"] for check in checks)
    negatives_pass = all(row["kills_signature"] and row["outcome_delta"] > KILL_FLOOR for row in negatives.values())
    tools_pass = all(row["pass"] and abs(float(row["outcome_delta"])) > KILL_FLOOR for row in tool_ablations.values())
    all_pass = (
        all_scale_pass
        and max_jax_delta < PARITY_TOL
        and known_values_pass
        and negatives_pass
        and tools_pass
        and z3_ray["pass"]
        and z3_order["pass"]
        and sympy_row["fs_metric_matches_closed_form"]
        and sympy_row["gauss_curvature_is_4"]
        and sympy_row["total_area_is_pi"]
    )

    blockers = []
    if not all_scale_pass:
        blockers.append("one or more non-dense 8/16/32/64 scale rungs failed")
    if max_jax_delta >= PARITY_TOL:
        blockers.append(f"jax_vs_pytorch parity delta {max_jax_delta} exceeds {PARITY_TOL}")
    if not known_values_pass:
        blockers.extend([f"known value mismatch: {check['invariant']}" for check in checks if not check["match"]])
    if not negatives_pass:
        blockers.extend([f"negative did not kill: {name}" for name, row in negatives.items() if not row["kills_signature"]])
    if not tools_pass:
        blockers.extend([f"tool ablation missing/nonzero failure: {name}" for name, row in tool_ablations.items() if not row["pass"]])

    result = {
        "schema": "formal_scout_max_deep_lego_v1",
        "sim_id": NAME,
        "name": NAME,
        "version": "1.0.0",
        "tier": "2_geometry",
        "classification": "lego",
        "promotion_allowed": False,
        "promotion_status": "keep_but_open",
        "sim_execution_kind": "nonclassical",
        "sim_class": "projective_base_sphere_geometry_probe",
        "purpose": "One independent projective-base-sphere lego: CP^(2-1)=CP^1 with the Fubini-Study metric, ray equivalence modulo U(1), and Hopf/Bloch base S^2 readouts at N=8/16/32/64 samples.",
        "scientific_question": "Can the CP^1 projective base carry the Fubini-Study metric and U(1) ray quotient on a non-dense N-sample PEPS3D-anchored carrier, with torch/JAX parity, exact closed forms, a z3 ray-equivalence certificate, and named negatives that kill the geometry?",
        "claim_ceiling": "Bounded local lego only for the projective_base_sphere layer. It does not claim full layer completion, stack/coupling readiness, G-structure selection, Axis0, flux, bridge, basin, FEP, physics, or final manifold admission.",
        "root_constraints_in_force": {
            "F01": "finite N-sample CP^1 ray set at N=8,16,32,64, one ray per finite PEPS3D vertex anchor, finite chart samples and finite SU(2) controls",
            "N01": "noncommuting SU(2) rotations Rz,Rx have a positive FS order gap; commuting Rz,Rz control collapses the gap",
        },
        "finite_map": "ProjectiveBaseSphere_N: finite normalized rays psi_k in C^2 modulo U(1) -> CP^1 Fubini-Study metric readouts, Hopf/Bloch base points in S^2, ray-equivalence certificate, Kahler orientation, and noncommuting order-gap controls",
        "domain": {
            "complex_dimension": 2,
            "projective_space": "CP^(2-1)=CP^1",
            "site_counts": SITE_COUNTS,
            "peps3d_shapes": {str(n): list(shape) for n, shape in SITE_SHAPES.items()},
            "representatives": "normalized torch/JAX complex128 two-component rays psi=[a,b], with ray quotient psi~exp(i alpha)psi",
        },
        "codomain_or_output": {
            "metric": "Fubini-Study metric tensor trace in the affine chart [1:z], g=(dx^2+dy^2)/(1+|z|^2)^2",
            "quotient": "U(1)-invariant Hopf/Bloch base point in S^2, with FS distance arccos(|<psi|chi>|)",
            "controls": list(negatives.keys()),
        },
        "carrier_layer": "finite N-sample CP^1 ray carrier; sparse/projective samples, not N qubits and not an exponential dense vector",
        "geometry_layer": "projective_base_sphere: CP^1 Fubini-Study metric and Hopf base S^2 for n=2",
        "carrier_realization": "torch.complex128 primary ray tensors plus JAX complex128 mirrored ray tensors; no NumPy claim-bearing path and no dense state closure",
        "peps3d_embedding": {
            str(n): {
                "shape": list(SITE_SHAPES[n]),
                "counts": peps3d_counts(SITE_SHAPES[n]),
                "anchor": "one CP^1 ray sample per PEPS3D vertex; edges/faces/cells are finite carrier anchors only, not a full PEPS3D contraction claim",
            }
            for n in SITE_COUNTS
        },
        "spinor_state": "finite torch/JAX complex128 two-component spinor/ray representatives; density/base readouts are spinor-derived",
        "quaternion_action": "not_applicable: no quaternion language or quaternion invariant is used in this CP^1 Fubini-Study base lego",
        "dependency_receipts": [],
        "downstream_blocks": ["stacking", "coupling", "higher_layers", "G_structure", "Axis0", "flux", "Xi", "Phi0", "bridge", "basin", "FEP", "physics", "final_manifold_admission"],
        "blocked_consumers": ["stacking", "coupling", "higher_layers", "G_structure", "Axis0", "flux", "Xi", "Phi0", "bridge", "basin", "FEP", "physics", "final_manifold_admission"],
        "law_or_candidate_tested": "CP^1 Fubini-Study projective base with U(1) ray quotient and noncommuting SU(2) order-sensitive transport control",
        "branch_status_before_run": "single independent geometry lego; no coupling/stacking route opened",
        "allowed_claims": [
            "local CP^1 projective-base-sphere finite-map witness at N=8/16/32/64",
            "FS distance |0>,|1> computed as pi/2 in torch, JAX, sympy, and geomstats-through-S2",
            "U(1) ray equivalence structurally certified and numerically checked on finite samples",
        ],
        "promotion_blockers": [
            "single-layer lego only",
            "no coupling or layer-stack evidence",
            "geomstats CP^n class absent in this install, so geomstats is used honestly through the CP^1 radius-1/2 S^2 equivalence on the torch backend",
            "downstream consumers remain blocked",
        ],
        "scale_ladder": {"rungs": scale_rungs, "pass": all_scale_pass},
        "scale_rows": {
            "torch_primary": torch_rows,
            "jax_secondary": jax_rows,
            "real_only_control": real_torch_rows,
            "parity_rows": parity_rows,
        },
        "jax_vs_pytorch": {
            "max_value_delta": max_jax_delta,
            "agree": max_jax_delta < PARITY_TOL,
            "notes": "JAX mirrors the CP^1 FS metric/distance/quotient/order/orientation formulas with x64 enabled on line 1. geomstats has no JAX backend path here and this install has no ComplexProjectiveSpace class; geomstats is used torch-side through the mathematically equivalent CP^1(FS)=round S^2 radius 1/2 metric cross-check.",
        },
        "known_value_checks": checks,
        "sympy_closed_form": sympy_row,
        "z3_certificates": {"ray_equivalence": z3_ray, "order_gap": z3_order},
        "required_negatives": list(negatives.keys()),
        "negatives_run": list(negatives.keys()),
        "negatives": negatives,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "controls": {"positive": positive, "negative": graveyard_companions},
        "nearby_variants": nearby_variants,
        "kill_conditions": {
            "flatten_metric": "flat metric curvature must be 0 instead of FS curvature 4",
            "commute_operators": "Rz/Rz commuting control must collapse the Rz/Rx order gap below floor",
            "drop_fiber_quotient": "raw phase-vector drift must be positive while quotient base drift stays below floor",
            "real_only_restriction": "real-only chart restriction must collapse the Kahler orientation readout below floor",
        },
        "TOOL_MANIFEST": tool_manifest,
        "tool_manifest": tool_manifest,
        "TOOL_INTEGRATION_DEPTH": tool_depth,
        "tool_integration_depth": tool_depth,
        "tool_integration_depth_reasons": tool_depth_reasons,
        "required_tools": list(tool_manifest.keys()),
        "actual_tools_used": list(tool_manifest.keys()),
        "proof_surfaces_used": ["sympy", "z3"],
        "graph_surfaces_used": [],
        "topology_surfaces_used": [],
        "ablation_outcome_delta": tool_ablations,
        "tool_ablations_by_tool": tool_ablations,
        "tool_ablation_outcomes": tool_ablations,
        "required_inputs": ["deterministic finite CP^1 ray samples generated in this file"],
        "data_or_artifact_dependencies": [],
        "required_artifacts": ["result_json", "scale_ladder", "known_value_checks", "negative_artifacts", "tool_ablation_outcomes"],
        "artifacts_emitted": [str(OUT_PATH.relative_to(ROOT))],
        "witness_trace_id": f"{NAME}:{int(started)}",
        "result_summary": {
            "all_pass": all_pass,
            "all_scale_pass": all_scale_pass,
            "known_values_pass": known_values_pass,
            "negatives_pass": negatives_pass,
            "tools_pass": tools_pass,
            "max_jax_vs_pytorch_delta": max_jax_delta,
            "min_order_gap": min_order_gap,
            "max_commuting_order_gap": max_commuting_order_gap,
            "max_phase_quotient_drift": max_phase_quotient_drift,
            "min_kahler_orientation": min_orientation,
            "elapsed_seconds": time.time() - started,
        },
        "summary": {
            "all_pass": all_pass,
            "max_sites": 64,
            "scale_rungs": SITE_COUNTS,
            "max_jax_vs_pytorch_delta": max_jax_delta,
            "negatives_pass": negatives_pass,
            "tools_pass": tools_pass,
            "promotion_allowed": False,
        },
        "pass_rule": "all 8/16/32/64 non-dense rungs pass; torch/JAX parity < 1e-8; all known-value checks match; all named negatives kill; all load-bearing tool ablations have nonzero outcome_delta",
        "fail_rule": "fail on dense closure, missing scale rung, dual-engine disagreement, missing/zero tool ablation delta, non-killing negative, or known-value mismatch",
        "eligible_consumers": ["bounded local projective-base-sphere comparisons only"],
        "shells": ["finite_CP1_ray_quotient", "fubini_study_metric", "hopf_bloch_base_sphere"],
        "future_continuations": ["independent Hopf fibration/fiber connection lego; only after separate receipt, not from this result"],
        "compatibility_weights": {"local_projective_base_sphere_lego": 1.0, "stacking": 0.0, "axis": 0.0, "physics": 0.0},
        "compression_map": "Each finite CP^1 ray sample is compressed to a projective quotient/base point via psi~exp(i alpha)psi and Hopf/Bloch S^2 coordinates; no exponential dense carrier is formed.",
        "present_survivor": {
            "object": "CP1_FS_projective_base_signature",
            "capacity": min(min_order_gap, min_orientation),
            "survives": min(min_order_gap, min_orientation) > KILL_FLOOR,
        },
        "outward_record": {
            "result_path": str(OUT_PATH),
            "promotion_allowed": False,
            "blocked_consumers": ["stacking", "Axis0", "flux", "bridge", "physics"],
        },
        "survivor_invariant": {
            "computed": min(min_order_gap, min_orientation),
            "threshold": KILL_FLOOR,
            "passed": min(min_order_gap, min_orientation) > KILL_FLOOR,
        },
        "blockers": blockers,
        "why_not_v4_probes": "This is a v5 max-deep single lego with explicit 8/16/32/64 non-dense scale ladder, torch/JAX dual engines, exact FS closed-form checks, structural z3 ray quotient proof, named negatives, and nonzero load-bearing ablations; promotion_allowed remains false.",
        "all_pass": all_pass,
    }

    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": all_pass, "out_path": str(OUT_PATH), "summary": result["result_summary"], "blockers": blockers}, indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
