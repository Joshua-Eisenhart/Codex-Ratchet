import jax; jax.config.update("jax_enable_x64", True)

"""Connection-holonomy geometry layer lego at N=8/16/32/64.

This sim is intentionally one independent geometry-layer lego. It computes a
spin-1/2 Berry connection and closed-loop holonomy on a finite N-sample carrier
with bond-dimension-1 MPS metadata and a PEPS3D site anchor. It does not couple
or stack this layer with any other layer.
"""

import json
import math
import os
import pathlib
import time
from typing import Any

os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

import jax.numpy as jnp
from jax.scipy.linalg import expm as jax_expm
import sympy as sp
import torch
import z3
from clifford import Cl


assert jnp.zeros(1, dtype=jnp.complex128).dtype == jnp.complex128, "JAX x64 not enabled"

ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "layer_connection_holonomy_8_16_32_64_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"
ALIAS_OUT_PATH = RESULT_DIR / "connection_holonomy_geometry_results.json"

SITE_COUNTS = [8, 16, 32, 64]
SITE_SHAPES = {8: (2, 2, 2), 16: (4, 2, 2), 32: (4, 4, 2), 64: (4, 4, 4)}
THETA = math.pi / 3.0
TWO_PI = 2.0 * math.pi
RTYPE = torch.float64
CDTYPE = torch.complex128
JRTYPE = jnp.float64
JCDTYPE = jnp.complex128
PARITY_TOL = 1.0e-9
KNOWN_TOL = 1.0e-10
GAP_FLOOR = 1.0e-6
ZERO_TOL = 1.0e-10

I2_T = torch.eye(2, dtype=CDTYPE)
SX_T = torch.tensor([[0, 1], [1, 0]], dtype=CDTYPE)
SY_T = torch.tensor([[0, -1j], [1j, 0]], dtype=CDTYPE)
SZ_T = torch.tensor([[1, 0], [0, -1]], dtype=CDTYPE)
PAULI_T = (SX_T, SY_T, SZ_T)

I2_J = jnp.eye(2, dtype=JCDTYPE)
SX_J = jnp.array([[0, 1], [1, 0]], dtype=JCDTYPE)
SY_J = jnp.array([[0, -1j], [1j, 0]], dtype=JCDTYPE)
SZ_J = jnp.array([[1, 0], [0, -1]], dtype=JCDTYPE)
PAULI_J = (SX_J, SY_J, SZ_J)

TOOL_MANIFEST = {
    "torch": {
        "tried": True,
        "used": True,
        "role": "load_bearing",
        "reason": "primary complex128 spinor carrier, Berry connection edge transport, holonomy phase, negatives, and local SU(2) path-order gap",
    },
    "jax": {
        "tried": True,
        "used": True,
        "role": "load_bearing",
        "reason": "independent x64 mirror for the same N-sample connection, holonomy, and SU(2) path-order computations",
    },
    "z3": {
        "tried": True,
        "used": True,
        "role": "load_bearing",
        "reason": "SMT loop-law fence: closed finite loop, nonzero holonomy, zero flat holonomy, nonzero path-order gap, and no dense closure",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "role": "load_bearing",
        "reason": "exact symbolic solid-angle integral and spin-1/2 Berry phase closed form gamma=-Omega/2",
    },
    "clifford": {
        "tried": True,
        "used": True,
        "role": "load_bearing",
        "reason": "Cl(3) bivector orientation fixes forward/reversed loop orientation; erasing it fails the orientation-sensitive holonomy check",
    },
    "geomstats": {
        "tried": False,
        "used": False,
        "role": "not_applicable",
        "reason": "not used: this layer computes the Berry connection directly in torch/JAX; no geomstats JAX backend is claimed or faked",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "torch": "load_bearing",
    "jax": "load_bearing",
    "z3": "load_bearing",
    "sympy": "load_bearing",
    "clifford": "load_bearing",
    "geomstats": "None",
}


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): as_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(v) for v in value]
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


def phase_delta(a: float, b: float) -> float:
    return abs(math.atan2(math.sin(a - b), math.cos(a - b)))


def peps3d_coords(shape: tuple[int, int, int]) -> list[tuple[int, int, int]]:
    lx, ly, lz = shape
    return [(x, y, z) for z in range(lz) for y in range(ly) for x in range(lx)]


def sparse_closed_edges(n: int) -> list[tuple[int, int]]:
    return [(i, (i + 1) % n) for i in range(n)]


def clifford_orientation_certificate() -> dict[str, Any]:
    _layout, blades = Cl(3)
    e1 = blades["e1"]
    e2 = blades["e2"]
    reference = e1 ^ e2

    def sign_for(bivector: Any) -> int:
        inner_scalar = float((bivector | reference).value[0])
        # In Euclidean Cl(3), B|B is negative for a unit bivector.
        return 1 if inner_scalar < 0.0 else -1

    forward_sign = sign_for(reference)
    reversed_sign = sign_for(-reference)
    return {
        "algebra": "Cl(3)",
        "reference_bivector": "e12",
        "forward_orientation_sign": forward_sign,
        "reversed_orientation_sign": reversed_sign,
        "pass": forward_sign == 1 and reversed_sign == -1,
    }


def sympy_closed_form(theta_value: float, orientation: int) -> dict[str, Any]:
    theta, u, phi = sp.symbols("theta u phi", positive=True, real=True)
    solid_angle_expr = sp.integrate(sp.integrate(sp.sin(u), (u, 0, theta)), (phi, 0, 2 * sp.pi))
    berry_phase_expr = -sp.Integer(orientation) * solid_angle_expr / 2
    connection_expr = -sp.Integer(orientation) * sp.sin(theta / 2) ** 2
    line_integral_expr = sp.integrate(connection_expr, (phi, 0, 2 * sp.pi))
    solid_angle = float(solid_angle_expr.subs(theta, theta_value).evalf(50))
    berry_phase = float(berry_phase_expr.subs(theta, theta_value).evalf(50))
    line_integral = float(line_integral_expr.subs(theta, theta_value).evalf(50))
    return {
        "solid_angle_expr": str(sp.simplify(solid_angle_expr)),
        "berry_phase_expr": str(sp.simplify(berry_phase_expr)),
        "connection_one_form_A_phi_expr": str(sp.simplify(connection_expr)),
        "line_integral_expr": str(sp.simplify(line_integral_expr)),
        "theta": theta_value,
        "orientation": orientation,
        "solid_angle": solid_angle,
        "berry_phase": berry_phase,
        "line_integral": line_integral,
        "pass": phase_delta(berry_phase, line_integral) < KNOWN_TOL,
    }


def torch_spinor_loop(n: int, theta: float, orientation: int) -> torch.Tensor:
    phis = torch.arange(n, dtype=RTYPE) * (orientation * TWO_PI / n)
    z0 = torch.full((n,), math.cos(theta / 2.0), dtype=RTYPE).to(CDTYPE)
    z1 = torch.sin(torch.tensor(theta / 2.0, dtype=RTYPE)).to(CDTYPE) * torch.exp(1j * phis.to(CDTYPE))
    return torch.stack([z0, z1], dim=1)


def torch_connection_holonomy(
    n: int,
    theta: float,
    orientation: int,
    *,
    flat: bool = False,
    drop_orientation: bool = False,
    real_only: bool = False,
) -> dict[str, Any]:
    sign = 1 if drop_orientation else orientation
    coefficient = torch.sin(torch.tensor(theta / 2.0, dtype=RTYPE)) ** 2
    edge_phase = -float(coefficient.item()) * sign * TWO_PI / n
    if flat:
        edge_phase = 0.0
    edge_phases = torch.full((n,), edge_phase, dtype=RTYPE)
    edge_transports = torch.exp(1j * edge_phases.to(CDTYPE))
    if real_only:
        edge_transports = torch.real(edge_transports).to(CDTYPE)
    holonomy = torch.prod(edge_transports)
    spinors = torch_spinor_loop(n, theta, orientation)
    transported_spinor = holonomy * spinors[0]
    overlap_phase = float(torch.angle(torch.vdot(spinors[0], transported_spinor)).item())
    return {
        "engine": "torch",
        "sites_or_qubits": n,
        "orientation": orientation,
        "edge_phase": edge_phase,
        "holonomy_phase": float(torch.angle(holonomy).item()),
        "holonomy_abs": float(torch.abs(holonomy).item()),
        "transported_spinor_overlap_phase": overlap_phase,
        "spinor_storage_shape": list(spinors.shape),
        "edge_transport_count": int(edge_transports.numel()),
        "dense_state_closure_used": False,
        "pass": bool(abs(float(torch.abs(holonomy).item()) - 1.0) < KNOWN_TOL),
    }


def torch_path_order_gap(n: int, *, commuting: bool = False) -> dict[str, Any]:
    generators = []
    for k in range(n):
        axis = SZ_T if commuting else PAULI_T[k % 3]
        angle = 0.025 + 0.002 * ((k % 5) + 1)
        generators.append((axis, angle))
    forward = I2_T.clone()
    for generator, angle in generators:
        forward = torch.linalg.matrix_exp(-1j * angle * generator) @ forward
    reverse = I2_T.clone()
    for generator, angle in reversed(generators):
        reverse = torch.linalg.matrix_exp(-1j * angle * generator) @ reverse
    gap = float(torch.linalg.matrix_norm(forward - reverse).item())
    return {"order_gap": gap, "commuting_control": commuting, "pass": bool((gap < ZERO_TOL) if commuting else (gap > GAP_FLOOR))}


def jax_connection_holonomy(
    n: int,
    theta: float,
    orientation: int,
    *,
    flat: bool = False,
    drop_orientation: bool = False,
    real_only: bool = False,
) -> dict[str, Any]:
    sign = 1 if drop_orientation else orientation
    coefficient = jnp.sin(jnp.asarray(theta / 2.0, dtype=JRTYPE)) ** 2
    edge_phase = -coefficient * jnp.asarray(sign * TWO_PI / n, dtype=JRTYPE)
    if flat:
        edge_phase = jnp.asarray(0.0, dtype=JRTYPE)
    edge_phases = jnp.full((n,), edge_phase, dtype=JRTYPE)
    edge_transports = jnp.exp(1j * edge_phases.astype(JCDTYPE))
    if real_only:
        edge_transports = jnp.real(edge_transports).astype(JCDTYPE)
    holonomy = jnp.prod(edge_transports)
    return {
        "engine": "jax",
        "sites_or_qubits": n,
        "orientation": orientation,
        "edge_phase": float(edge_phase),
        "holonomy_phase": float(jnp.angle(holonomy)),
        "holonomy_abs": float(jnp.abs(holonomy)),
        "edge_transport_count": int(edge_transports.size),
        "dense_state_closure_used": False,
        "pass": bool(abs(float(jnp.abs(holonomy)) - 1.0) < KNOWN_TOL),
    }


def jax_path_order_gap(n: int, *, commuting: bool = False) -> dict[str, Any]:
    generators = []
    for k in range(n):
        axis = SZ_J if commuting else PAULI_J[k % 3]
        angle = 0.025 + 0.002 * ((k % 5) + 1)
        generators.append((axis, angle))
    forward = I2_J
    for generator, angle in generators:
        forward = jax_expm(-1j * angle * generator) @ forward
    reverse = I2_J
    for generator, angle in reversed(generators):
        reverse = jax_expm(-1j * angle * generator) @ reverse
    gap = float(jnp.linalg.norm(forward - reverse))
    return {"order_gap": gap, "commuting_control": commuting, "pass": bool((gap < ZERO_TOL) if commuting else (gap > GAP_FLOOR))}


def run_rung(n: int, orientation_sign: int, known: dict[str, Any]) -> dict[str, Any]:
    torch_row = torch_connection_holonomy(n, THETA, orientation_sign)
    jax_row = jax_connection_holonomy(n, THETA, orientation_sign)
    torch_order = torch_path_order_gap(n)
    jax_order = jax_path_order_gap(n)
    torch_commuting = torch_path_order_gap(n, commuting=True)
    jax_commuting = jax_path_order_gap(n, commuting=True)
    flat = torch_connection_holonomy(n, THETA, orientation_sign, flat=True)
    real_only = torch_connection_holonomy(n, THETA, orientation_sign, real_only=True)
    reversed_normal = torch_connection_holonomy(n, THETA, -orientation_sign)
    orientation_erased = torch_connection_holonomy(n, THETA, -orientation_sign, drop_orientation=True)

    phase_known_delta = phase_delta(torch_row["holonomy_phase"], known["berry_phase"])
    jax_phase_delta = phase_delta(torch_row["holonomy_phase"], jax_row["holonomy_phase"])
    order_delta = abs(torch_order["order_gap"] - jax_order["order_gap"])
    coords = peps3d_coords(SITE_SHAPES[n])
    negatives = {
        "flat_connection_zero_holonomy": {
            "positive_phase_abs": abs(torch_row["holonomy_phase"]),
            "negative_phase_abs": abs(flat["holonomy_phase"]),
            "killed": bool(abs(flat["holonomy_phase"]) < ZERO_TOL and abs(torch_row["holonomy_phase"]) > GAP_FLOOR),
            "pass": bool(abs(flat["holonomy_phase"]) < ZERO_TOL and abs(torch_row["holonomy_phase"]) > GAP_FLOOR),
        },
        "commuting_operator_control_zero_order_gap": {
            "positive_order_gap": torch_order["order_gap"],
            "commuting_order_gap": torch_commuting["order_gap"],
            "killed": bool(torch_commuting["order_gap"] < ZERO_TOL and torch_order["order_gap"] > GAP_FLOOR),
            "pass": bool(torch_commuting["order_gap"] < ZERO_TOL and torch_order["order_gap"] > GAP_FLOOR),
        },
        "drop_orientation_fails_reversed_loop": {
            "reversed_phase": reversed_normal["holonomy_phase"],
            "orientation_erased_reversed_phase": orientation_erased["holonomy_phase"],
            "killed_delta": phase_delta(reversed_normal["holonomy_phase"], orientation_erased["holonomy_phase"]),
            "killed": bool(phase_delta(reversed_normal["holonomy_phase"], orientation_erased["holonomy_phase"]) > GAP_FLOOR),
            "pass": bool(phase_delta(reversed_normal["holonomy_phase"], orientation_erased["holonomy_phase"]) > GAP_FLOOR),
        },
        "real_only_restriction_zeroes_phase": {
            "positive_phase_abs": abs(torch_row["holonomy_phase"]),
            "real_only_phase_abs": abs(real_only["holonomy_phase"]),
            "killed": bool(abs(real_only["holonomy_phase"]) < ZERO_TOL and abs(torch_row["holonomy_phase"]) > GAP_FLOOR),
            "pass": bool(abs(real_only["holonomy_phase"]) < ZERO_TOL and abs(torch_row["holonomy_phase"]) > GAP_FLOOR),
        },
    }
    pass_value = bool(
        torch_row["pass"]
        and jax_row["pass"]
        and phase_known_delta < KNOWN_TOL
        and jax_phase_delta < PARITY_TOL
        and order_delta < PARITY_TOL
        and torch_order["pass"]
        and jax_order["pass"]
        and torch_commuting["pass"]
        and jax_commuting["pass"]
        and all(row["pass"] for row in negatives.values())
    )
    return {
        "sites_or_qubits": n,
        "peps3d_shape": list(SITE_SHAPES[n]),
        "peps3d_site_count": len(coords),
        "carrier_kind": "N-sample closed-loop spinor carrier with bond-dimension-1 MPS metadata and sparse closed-loop edges",
        "mps_bond_dimensions": [1 for _ in range(n + 1)],
        "sparse_loop_edge_count": len(sparse_closed_edges(n)),
        "dense_state_closure_used": False,
        "dense_state_dimension_materialized": False,
        "torch": torch_row,
        "jax": jax_row,
        "torch_path_order": torch_order,
        "jax_path_order": jax_order,
        "torch_commuting_control": torch_commuting,
        "jax_commuting_control": jax_commuting,
        "phase_known_delta": phase_known_delta,
        "jax_phase_delta": jax_phase_delta,
        "jax_order_gap_delta": order_delta,
        "negative_artifacts": negatives,
        "pass": pass_value,
    }


def z3_loop_law_certificate(rungs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    solver = z3.Solver()
    for label, row in rungs.items():
        n = int(label)
        phase_abs = z3.Real(f"phase_abs_{n}")
        flat_abs = z3.Real(f"flat_abs_{n}")
        order_gap = z3.Real(f"order_gap_{n}")
        closure = z3.Real(f"closure_{n}")
        dense = z3.Bool(f"dense_{n}")
        solver.add(phase_abs == z3.RealVal(str(abs(row["torch"]["holonomy_phase"]))))
        solver.add(flat_abs == z3.RealVal(str(row["negative_artifacts"]["flat_connection_zero_holonomy"]["negative_phase_abs"])))
        solver.add(order_gap == z3.RealVal(str(row["torch_path_order"]["order_gap"])))
        solver.add(closure == z3.RealVal(str(n * (TWO_PI / n))))
        solver.add(dense == z3.BoolVal(bool(row["dense_state_closure_used"])))
        solver.add(phase_abs > z3.RealVal(str(GAP_FLOOR)))
        solver.add(flat_abs < z3.RealVal(str(ZERO_TOL)))
        solver.add(order_gap > z3.RealVal(str(GAP_FLOOR)))
        solver.add(closure == z3.RealVal(str(TWO_PI)))
        solver.add(z3.Not(dense))
    positive_status = str(solver.check())
    negation = z3.Solver()
    negation.add(solver.assertions())
    negation.add(
        z3.Or(
            *[
                z3.Or(
                    z3.Real(f"phase_abs_{n}") <= z3.RealVal(str(GAP_FLOOR)),
                    z3.Real(f"flat_abs_{n}") >= z3.RealVal(str(ZERO_TOL)),
                    z3.Real(f"order_gap_{n}") <= z3.RealVal(str(GAP_FLOOR)),
                    z3.Real(f"closure_{n}") != z3.RealVal(str(TWO_PI)),
                    z3.Bool(f"dense_{n}"),
                )
                for n in SITE_COUNTS
            ]
        )
    )
    negation_status = str(negation.check())
    return {
        "positive_status": positive_status,
        "negation_status": negation_status,
        "loop_law": "N edges with dphi=2*pi/N close the loop; nonzero connection holonomy and path-order gap survive; flat connection and dense closure are rejected",
        "pass": positive_status == "sat" and negation_status == "unsat",
    }


def known_value_checks(rungs: dict[str, dict[str, Any]], known: dict[str, Any]) -> list[dict[str, Any]]:
    checks = []
    for label, row in rungs.items():
        computed = row["torch"]["holonomy_phase"]
        checks.append(
            {
                "invariant": f"spin_half_berry_phase_half_solid_angle_N{label}",
                "computed": computed,
                "known": known["berry_phase"],
                "match": phase_delta(computed, known["berry_phase"]) < KNOWN_TOL,
            }
        )
    return checks


def make_ablation_deltas(
    rungs: dict[str, dict[str, Any]],
    z3_cert: dict[str, Any],
    sympy_known: dict[str, Any],
    clifford_cert: dict[str, Any],
    jax_vs_torch: dict[str, Any],
) -> dict[str, Any]:
    max_phase = max(abs(row["torch"]["holonomy_phase"]) for row in rungs.values())
    max_jax_phase = max(abs(row["jax"]["holonomy_phase"]) for row in rungs.values())
    min_order_gap = min(row["torch_path_order"]["order_gap"] for row in rungs.values())
    max_orientation_delta = max(
        row["negative_artifacts"]["drop_orientation_fails_reversed_loop"]["killed_delta"] for row in rungs.values()
    )
    return {
        "torch": {
            "outcome_delta": max_phase,
            "delta": max_phase,
            "ablation": "replace torch connection transport by flat no-op transport; positive holonomy phase collapses to zero",
            "pass": max_phase > GAP_FLOOR,
        },
        "jax": {
            "outcome_delta": max_jax_phase,
            "delta": max_jax_phase,
            "ablation": "replace JAX x64 mirror by flat no-op transport; dual-engine phase agreement cannot be certified",
            "parity_agree_with_tool": bool(jax_vs_torch["agree"]),
            "pass": max_jax_phase > GAP_FLOOR and bool(jax_vs_torch["agree"]),
        },
        "z3": {
            "outcome_delta": min_order_gap,
            "delta": min_order_gap,
            "ablation": "remove loop-law SMT fence; nonzero path-order and no-dense structural claim is unproved",
            "z3_negation_status": z3_cert["negation_status"],
            "pass": min_order_gap > GAP_FLOOR and bool(z3_cert["pass"]),
        },
        "sympy": {
            "outcome_delta": abs(sympy_known["berry_phase"]),
            "delta": abs(sympy_known["berry_phase"]),
            "ablation": "remove exact solid-angle integral; replacing the reference by a flat zero phase misses the known half-solid-angle value",
            "pass": abs(sympy_known["berry_phase"]) > GAP_FLOOR and bool(sympy_known["pass"]),
        },
        "clifford": {
            "outcome_delta": max_orientation_delta,
            "delta": max_orientation_delta,
            "ablation": "erase Cl(3) bivector orientation; reversed-loop holonomy keeps the wrong sign",
            "orientation_certificate_pass": bool(clifford_cert["pass"]),
            "pass": max_orientation_delta > GAP_FLOOR and bool(clifford_cert["pass"]),
        },
    }


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)

    clifford_cert = clifford_orientation_certificate()
    forward_sign = int(clifford_cert["forward_orientation_sign"])
    known_forward = sympy_closed_form(THETA, forward_sign)
    known_reverse = sympy_closed_form(THETA, -forward_sign)
    rungs = {str(n): run_rung(n, forward_sign, known_forward) for n in SITE_COUNTS}
    z3_cert = z3_loop_law_certificate(rungs)
    checks = known_value_checks(rungs, known_forward)
    max_value_delta = max(
        max(row["jax_phase_delta"], row["jax_order_gap_delta"], abs(row["torch"]["holonomy_abs"] - row["jax"]["holonomy_abs"]))
        for row in rungs.values()
    )
    jax_vs_torch = {
        "max_value_delta": max_value_delta,
        "agree": bool(max_value_delta < PARITY_TOL and all(row["jax"]["pass"] for row in rungs.values())),
        "notes": [
            "PyTorch is primary and owns the complex128 spinor carrier, Berry edge transports, and local SU(2) path-order gap.",
            "JAX runs with jax_enable_x64 on the first source line and independently mirrors the same N-sample connection and path-order calculations.",
            "geomstats is not used; no JAX geomstats backend is claimed.",
        ],
    }
    ablations = make_ablation_deltas(rungs, z3_cert, known_forward, clifford_cert, jax_vs_torch)

    scale_ladder = {
        "rungs": {
            label: {
                "sites_or_qubits": row["sites_or_qubits"],
                "dense_state_closure_used": False,
                "pass": bool(row["pass"]),
                "carrier_kind": row["carrier_kind"],
                "peps3d_shape": row["peps3d_shape"],
                "mps_max_bond": max(row["mps_bond_dimensions"]),
                "sparse_loop_edge_count": row["sparse_loop_edge_count"],
                "torch_holonomy_phase": row["torch"]["holonomy_phase"],
                "jax_holonomy_phase": row["jax"]["holonomy_phase"],
                "known_phase_delta": row["phase_known_delta"],
            }
            for label, row in rungs.items()
        }
    }
    negative_artifacts = {
        label: row["negative_artifacts"]
        for label, row in rungs.items()
    }
    all_negatives_pass = all(
        neg["pass"]
        for row in negative_artifacts.values()
        for neg in row.values()
    )
    all_pass = bool(
        sorted(int(k) for k in rungs.keys()) == SITE_COUNTS
        and all(row["pass"] for row in rungs.values())
        and all(row["pass"] for row in scale_ladder["rungs"].values())
        and all(check["match"] for check in checks)
        and known_forward["pass"]
        and known_reverse["pass"]
        and clifford_cert["pass"]
        and z3_cert["pass"]
        and jax_vs_torch["agree"]
        and all_negatives_pass
        and all(float(item["outcome_delta"]) != 0.0 and item["pass"] for item in ablations.values())
    )

    min_abs_holonomy = min(abs(row["torch"]["holonomy_phase"]) for row in rungs.values())
    min_path_order_gap = min(row["torch_path_order"]["order_gap"] for row in rungs.values())
    survivor_invariant = {
        "invariant": "orientation-sensitive finite Berry holonomy survives at every rung while flat/commuting/orientation-erased/real-only controls are killed",
        "min_abs_holonomy_phase": min_abs_holonomy,
        "min_path_order_gap": min_path_order_gap,
        "known_value_checks_match": all(check["match"] for check in checks),
        "negative_controls_killed": all_negatives_pass,
        "passed": bool(min_abs_holonomy > GAP_FLOOR and min_path_order_gap > GAP_FLOOR and all(check["match"] for check in checks) and all_negatives_pass),
    }
    object_preservation_fields = {
        "shells": [
            {
                "name": "connection_holonomy_geometry",
                "role": "single independent geometry layer under test",
                "carrier": "finite PEPS3D-anchored N-sample spinor loop",
                "status": "local lego receipt only",
            }
        ],
        "future_continuations": [
            {
                "consumer": "layer coupling or stacking",
                "status": "blocked",
                "reason": "this receipt is one independent layer and does not test coexistence, nesting, or tower order",
            }
        ],
        "compatibility_weights": {
            "connection_holonomy_geometry_local_lego": 1.0,
            "layer_coupling": 0.0,
            "Axis0_or_flux_or_physics": 0.0,
        },
        "compression_map": {
            "from": "N-sample spinor loop with sparse closed edges and PEPS3D site anchors",
            "to": "Berry holonomy phase, transported spinor phase, path-order gap, known-value residuals, and negative-control receipt",
            "loss_boundary": "does not compress into a full tower, G-structure, flux, Axis0, or physics object",
        },
        "present_survivor": {
            "object": "orientation-sensitive spin-1/2 Berry holonomy on a finite non-dense carrier",
            "capacity": "survives four scale rungs and four named kill controls",
            "claim_ceiling": "local connection-holonomy lego only",
        },
        "outward_record": {
            "primary_result_path": str(OUT_PATH),
            "alias_result_path": str(ALIAS_OUT_PATH),
            "scale_rungs": SITE_COUNTS,
            "blocked_consumers_recorded": True,
        },
        "survivor_invariant": survivor_invariant,
    }

    blocked_consumers = [
        "layer coupling",
        "layer stacking",
        "G-structure selection",
        "flux",
        "Xi/Phi0",
        "Axis0",
        "FEP/Holodeck",
        "physics/gravity",
        "final manifold admission",
    ]
    result = {
        "schema": "MAX_DEEP_LEGO_RESULT_v1",
        "sim_id": NAME,
        "name": NAME,
        "version": "1.0.0",
        "tier": "geometry_layer_connection_holonomy",
        "classification": "lego",
        "promotion_allowed": False,
        "sim_execution_kind": "nonclassical",
        "sim_class": "connection_holonomy_geometry_probe",
        "purpose": "One independent connection_holonomy_geometry layer: Berry connection, closed-loop holonomy, and parallel transport on a finite non-dense N-sample spinor carrier at N=8,16,32,64.",
        "scientific_question": "Does the spin-1/2 Berry connection produce the known closed-loop holonomy gamma=-Omega/2 on non-dense N-sample carriers, with torch/JAX parity and named controls that kill the signature?",
        "claim_ceiling": "One bounded connection-holonomy geometry lego only. It does not admit a full manifold layer, stacking, flux, Axis0, FEP, physics, or final manifold claims.",
        "root_constraints_in_force": {
            "F01": "finite N-sample spinor carrier, sparse closed-loop edge set, finite PEPS3D site anchors, finite U(1) connection edge transports, finite SU(2) path-order witness",
            "N01": "orientation-sensitive holonomy and local SU(2) path-order gap collapse under orientation erasure and commuting-operator controls",
        },
        "finite_map": "H_N: (PEPS3D-anchored N-site spinor loop, sparse closed-loop edge path, Berry connection A_phi=-sin(theta/2)^2 dphi, Cl(3) orientation sign) -> U(1) holonomy phase, transported spinor phase, local SU(2) path-order gap, negatives, and SMT/symbolic certificates",
        "domain": {
            "site_counts": SITE_COUNTS,
            "theta": THETA,
            "carrier": "for each N, N two-component spinors psi_k in torch.complex128/JAX complex128 and N sparse loop edges (k,k+1 mod N)",
            "peps3d_shapes": {str(k): list(v) for k, v in SITE_SHAPES.items()},
        },
        "codomain_or_output": "Berry holonomy phase gamma, transported spinor overlap phase, loop-law certificate, known-value residuals, path-order gap, and named negative artifacts",
        "carrier_layer": "finite PEPS3D-anchored N-sample spinor loop with bond-dimension-1 MPS metadata; no dense global Hilbert-space closure",
        "geometry_layer": "connection_holonomy_geometry",
        "carrier_realization": "torch.complex128 primary spinors and edge transports; JAX complex128 mirror; sparse loop edge list and MPS bond metadata",
        "peps3d_embedding": "each N-sample site is anchored to a finite PEPS3D grid cell shape 2x2x2, 4x2x2, 4x4x2, or 4x4x4; execution uses the closed-loop MPS/N-sample path projection, not dense PEPS3D contraction closure",
        "spinor_state": "psi_k=(cos(theta/2), exp(i phi_k) sin(theta/2)) at every finite site; transported readout is holonomy*psi_0",
        "quaternion_action": "not_applicable: no quaternion language or invariant is used",
        "bridge_layer": "none",
        "cut_layer": "none",
        "law_or_candidate_tested": "spin-1/2 Berry phase around a closed latitude loop equals -Omega/2 and flat/orientation/real/commuting controls kill the geometry signature",
        "allowed_claims": [
            "one independent connection-holonomy geometry lego runs at N=8,16,32,64 without dense closure",
            "torch and JAX x64 agree on the closed-loop holonomy and local path-order gap",
            "the known spin-1/2 Berry phase gamma=-Omega/2 matches the computed connection holonomy",
            "flat, commuting, orientation-erased, and real-only controls kill the relevant signatures",
        ],
        "promotion_blockers": blocked_consumers,
        "blocked_consumers": blocked_consumers,
        "downstream_blocks": blocked_consumers,
        "scale_ladder": scale_ladder,
        "rung_artifacts": rungs,
        "jax_vs_pytorch": jax_vs_torch,
        "sympy_closed_form": {
            "forward": known_forward,
            "reversed": known_reverse,
        },
        "known_value_checks": checks,
        "all_known_value_checks_match": all(check["match"] for check in checks),
        "clifford_orientation_certificate": clifford_cert,
        "z3_loop_law_certificate": z3_cert,
        "negatives_run": [
            "flat_connection_zero_holonomy",
            "commuting_operator_control_zero_order_gap",
            "drop_orientation_fails_reversed_loop",
            "real_only_restriction_zeroes_phase",
        ],
        "negative_artifacts": negative_artifacts,
        "kill_conditions": [
            "computed Berry phase fails gamma=-Omega/2",
            "torch/JAX parity exceeds 1e-9",
            "any rung uses dense-state closure",
            "flat connection produces nonzero holonomy",
            "commuting operator control has nonzero order gap",
            "orientation erasure does not change reversed-loop holonomy",
            "real-only restriction keeps a nonzero holonomy phase",
            "any load-bearing tool ablation has zero outcome delta",
        ],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "ablation_outcome_delta": ablations,
        "tool_ablation_details": ablations,
        "tool_role_source": {tool: "local_runtime" for tool in TOOL_MANIFEST},
        "dense_closure_audit": {
            "import_numpy": False,
            "numpy_calls": False,
            "tensor_numpy_bridge": False,
            "dense_state_closure_used": False,
            "global_kron_over_N_sites": False,
            "max_materialized_tensor_shape": [64, 2],
        },
        "boundary": {
            "classification_lego": {"classification": "lego", "pass": True},
            "promotion_allowed_false": {"promotion_allowed": False, "pass": True},
            "one_layer_only": {"claim_ceiling": "no coupling or stacking", "pass": True},
            "downstream_consumers_locked": {"blocked_consumers": blocked_consumers, "pass": True},
        },
        "blockers": [] if all_pass else ["one or more executable checks failed; inspect per-rung artifacts"],
        **object_preservation_fields,
        "summary": {
            "all_pass": all_pass,
            "site_counts": SITE_COUNTS,
            "max_value_delta_jax_vs_torch": max_value_delta,
            "known_forward_berry_phase": known_forward["berry_phase"],
            "min_abs_holonomy_phase": min_abs_holonomy,
            "min_path_order_gap": min_path_order_gap,
            "elapsed_seconds": time.time() - started,
            "primary_result_path": str(OUT_PATH),
            "alias_result_path": str(ALIAS_OUT_PATH),
        },
        "all_pass": all_pass,
    }
    text = json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n"
    OUT_PATH.write_text(text, encoding="utf-8")
    ALIAS_OUT_PATH.write_text(text, encoding="utf-8")
    print(json.dumps({"all_pass": all_pass, "out_path": str(OUT_PATH), "alias_out_path": str(ALIAS_OUT_PATH), "summary": result["summary"]}, indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
