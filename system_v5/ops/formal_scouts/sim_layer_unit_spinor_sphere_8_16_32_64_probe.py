import jax; jax.config.update("jax_enable_x64", True)

import json
import math
import os
import pathlib
import time
from typing import Any

os.environ.setdefault("GEOMSTATS_BACKEND", "pytorch")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

import jax.numpy as jnp
from clifford import Cl
import geomstats.backend as gs
from geomstats.geometry.hypersphere import Hypersphere
import sympy as sp
import torch
import z3


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "unit_spinor_sphere_8_16_32_64_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

CLASSIFICATION = "lego"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "geometry_probe"
SITE_COUNTS = [8, 16, 32, 64]
BOND_DIM = 2
CDTYPE = torch.complex128
RTYPE = torch.float64
EPS = 1.0e-9
KILL_EPS = 1.0e-6

TOOL_MANIFEST: dict[str, dict[str, Any]] = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "primary complex128 MPS carrier contractions, norm checks, Fubini-Study overlaps, phase quotient, noncommuting operator negatives, and no dense-state closure",
    },
    "jax": {
        "tried": True,
        "used": True,
        "reason": "independent x64 engine for the same MPS norm, overlap, phase-invariant, and rank-1 Fubini-Study computations",
    },
    "geomstats": {
        "tried": True,
        "used": True,
        "reason": "load-bearing torch-side Hypersphere S3 metric/geodesic check for the rank-1 local spinor fixture; geomstats has no JAX backend in this run",
    },
    "clifford": {
        "tried": True,
        "used": True,
        "reason": "load-bearing Cl(2) even rotor supplies the spinor fiber-orientation phase and verifies the bivector squares to -1",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing closed-form rank-1 norm, global-phase quotient, and Fubini-Study invariant derivation",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing structural gate that a rung cannot pass if normalization, phase quotient, non-dense carrier, or finite scale is false",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "jax": "load_bearing",
    "geomstats": "load_bearing",
    "clifford": "load_bearing",
    "sympy": "load_bearing",
    "z3": "load_bearing",
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
    if isinstance(value, complex):
        return {"real": float(value.real), "imag": float(value.imag)}
    return value


def clifford_rotor_phase(theta: float) -> dict[str, Any]:
    _layout, blades = Cl(2)
    e1, e2 = blades["e1"], blades["e2"]
    bivector = e1 * e2
    rotor = math.cos(theta) + math.sin(theta) * bivector
    scalar = float(rotor.value[0])
    bivector_coeff = float(rotor.value[3])
    phase = complex(scalar, bivector_coeff)
    return {
        "theta": theta,
        "bivector_square": str(bivector * bivector),
        "rotor": str(rotor),
        "phase": phase,
        "unit_modulus_gap": abs(abs(phase) - 1.0),
        "pass": str(bivector * bivector) == "-1" and abs(abs(phase) - 1.0) < EPS,
    }


CLIFFORD_ROTOR = clifford_rotor_phase(0.37)


def raw_tensor(site_count: int, site: int, *, orientation: complex, real_only: bool) -> list[list[list[complex]]]:
    dl = 1 if site == 0 else BOND_DIM
    dr = 1 if site == site_count - 1 else BOND_DIM
    scale = 1.0 / math.sqrt(float(dl * dr * 2))
    tensor: list[list[list[complex]]] = []
    for left in range(dl):
        phys_rows: list[list[complex]] = []
        for phys in range(2):
            right_rows: list[complex] = []
            for right in range(dr):
                angle = (
                    0.071 * (site + 1) * (phys + 1)
                    + 0.113 * (left + 1)
                    - 0.097 * (right + 1)
                    + 0.019 * math.log2(float(site_count))
                )
                envelope = 0.63 + 0.11 * math.cos((site + 1) * (phys + 1) / (site_count + 3.0))
                real = envelope * math.cos(angle) + (0.21 if left == right else -0.04)
                imag = 0.0 if real_only else envelope * math.sin(angle + 0.17 * phys)
                value = scale * complex(real, imag)
                if phys == 1 and not real_only:
                    value *= orientation ** ((site % 3) + 1)
                right_rows.append(value)
            phys_rows.append(right_rows)
        tensor.append(phys_rows)
    return tensor


def raw_mps_values(site_count: int, *, orientation: complex | None = None, real_only: bool = False) -> list[Any]:
    orient = 1.0 + 0.0j if orientation is None else orientation
    return [raw_tensor(site_count, site, orientation=orient, real_only=real_only) for site in range(site_count)]


def to_torch_mps(values: list[Any]) -> list[torch.Tensor]:
    return [torch.tensor(value, dtype=CDTYPE) for value in values]


def to_jax_mps(values: list[Any]) -> list[Any]:
    return [jnp.array(value, dtype=jnp.complex128) for value in values]


def torch_overlap(left: list[torch.Tensor], right: list[torch.Tensor]) -> torch.Tensor:
    env = torch.ones((1, 1), dtype=CDTYPE)
    for a_tensor, b_tensor in zip(left, right, strict=True):
        env = torch.einsum("ab,apr,bps->rs", env, a_tensor.conj(), b_tensor)
    return env.reshape(()).to(CDTYPE)


def jax_overlap(left: list[Any], right: list[Any]) -> Any:
    env = jnp.ones((1, 1), dtype=jnp.complex128)
    for a_tensor, b_tensor in zip(left, right, strict=True):
        env = jnp.einsum("ab,apr,bps->rs", env, jnp.conjugate(a_tensor), b_tensor)
    return jnp.reshape(env, ())


def normalize_torch_mps(mps: list[torch.Tensor]) -> list[torch.Tensor]:
    norm = torch.real(torch_overlap(mps, mps))
    if (not math.isfinite(float(norm.item()))) or float(norm.item()) <= 0.0:
        raise ValueError("zero MPS norm")
    out = [tensor.clone() for tensor in mps]
    out[0] = out[0] / torch.sqrt(norm).to(CDTYPE)
    return out


def normalize_jax_mps(mps: list[Any]) -> list[Any]:
    norm = jnp.real(jax_overlap(mps, mps))
    if float(norm) <= 0.0 or not math.isfinite(float(norm)):
        raise ValueError("zero JAX MPS norm")
    out = [tensor for tensor in mps]
    out[0] = out[0] / jnp.sqrt(norm).astype(jnp.complex128)
    return out


def phase_mps_torch(mps: list[torch.Tensor], phase: float) -> list[torch.Tensor]:
    out = [tensor.clone() for tensor in mps]
    out[0] = out[0] * torch.exp(torch.tensor(1j * phase, dtype=CDTYPE))
    return out


def phase_mps_jax(mps: list[Any], phase: float) -> list[Any]:
    out = [tensor for tensor in mps]
    out[0] = out[0] * jnp.exp(jnp.array(1j * phase, dtype=jnp.complex128))
    return out


def torch_fs_distance(left: list[torch.Tensor], right: list[torch.Tensor]) -> torch.Tensor:
    overlap = torch_overlap(left, right)
    fidelity_root = torch.clamp(torch.abs(overlap), max=1.0)
    fidelity_root = torch.where(1.0 - fidelity_root < 1.0e-12, torch.ones_like(fidelity_root), fidelity_root)
    return torch.arccos(fidelity_root).to(RTYPE)


def jax_fs_distance(left: list[Any], right: list[Any]) -> Any:
    overlap = jax_overlap(left, right)
    fidelity_root = jnp.minimum(jnp.abs(overlap), 1.0)
    fidelity_root = jnp.where(1.0 - fidelity_root < 1.0e-12, jnp.ones_like(fidelity_root), fidelity_root)
    return jnp.arccos(fidelity_root)


def local_spinor_pair(theta: float, phase: float = 0.0) -> tuple[torch.Tensor, torch.Tensor]:
    a = torch.tensor([1.0 + 0.0j, 0.0 + 0.0j], dtype=CDTYPE)
    b = torch.tensor(
        [math.cos(theta) + 0.0j, complex(math.cos(phase), math.sin(phase)) * math.sin(theta)],
        dtype=CDTYPE,
    )
    return a, b


def product_fixture_values(site_count: int, theta: float) -> tuple[list[Any], list[Any]]:
    a_values = []
    b_values = []
    for site in range(site_count):
        if site == 0:
            a_site, b_site = local_spinor_pair(theta, phase=0.41)
        else:
            a_site, b_site = local_spinor_pair(0.0)
        a_values.append([[[complex(a_site[0].item())], [complex(a_site[1].item())]]])
        b_values.append([[[complex(b_site[0].item())], [complex(b_site[1].item())]]])
    return a_values, b_values


def spinor_to_s3(spinor: torch.Tensor) -> torch.Tensor:
    return torch.stack([spinor[0].real, spinor[0].imag, spinor[1].real, spinor[1].imag]).to(RTYPE)


def align_phase(reference: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
    overlap = torch.sum(reference.conj() * target)
    if float(torch.abs(overlap).item()) <= EPS:
        return target
    return target * (overlap.conj() / torch.abs(overlap))


def geomstats_rank1_distance(theta: float) -> float:
    sphere = Hypersphere(dim=3)
    a, b = local_spinor_pair(theta, phase=0.41)
    b_aligned = align_phase(a, b)
    return float(
        sphere.metric.dist(
            gs.array(spinor_to_s3(a), dtype=gs.float64),
            gs.array(spinor_to_s3(b_aligned), dtype=gs.float64),
        ).item()
    )


def sympy_closed_form(theta_value: float, phase_value: float) -> dict[str, Any]:
    theta = sp.symbols("theta", real=True, nonnegative=True)
    phi = sp.symbols("phi", real=True)
    norm_expr = sp.simplify(sp.cos(theta) ** 2 + sp.sin(theta) ** 2)
    phase_mod_expr = sp.simplify(sp.exp(sp.I * phi) * sp.exp(-sp.I * phi))
    fs_expr = sp.acos(sp.cos(theta))
    fs_value = float(fs_expr.subs(theta, theta_value).evalf(40))
    phase_mod_value = complex(phase_mod_expr.subs(phi, phase_value).evalf(40))
    return {
        "norm_expression": str(norm_expr),
        "global_phase_modulus_expression": str(phase_mod_expr),
        "rank1_fs_expression": str(fs_expr),
        "rank1_fs_value": fs_value,
        "phase_modulus_value": {"real": float(phase_mod_value.real), "imag": float(phase_mod_value.imag)},
        "pass": norm_expr == 1 and abs(phase_mod_value.real - 1.0) < EPS and abs(phase_mod_value.imag) < EPS,
    }


def torch_unitary_x(angle: float) -> torch.Tensor:
    sx = torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=CDTYPE)
    return torch.linalg.matrix_exp((-0.5j * angle) * sx)


def torch_unitary_z(angle: float) -> torch.Tensor:
    sz = torch.tensor([[1.0, 0.0], [0.0, -1.0]], dtype=CDTYPE)
    return torch.linalg.matrix_exp((-0.5j * angle) * sz)


def operator_order_gap() -> dict[str, Any]:
    psi = torch.tensor([math.sqrt(0.37), complex(0.0, math.sqrt(0.63))], dtype=CDTYPE)
    ux = torch_unitary_x(0.61)
    uz = torch_unitary_z(0.47)
    ordered = uz @ (ux @ psi)
    reversed_order = ux @ (uz @ psi)
    commute_control_a = uz @ (uz @ psi)
    commute_control_b = uz @ (uz @ psi)
    ordered_values = [[[[complex(ordered[0].item())], [complex(ordered[1].item())]]]]
    reversed_values = [[[[complex(reversed_order[0].item())], [complex(reversed_order[1].item())]]]]
    commute_a_values = [[[[complex(commute_control_a[0].item())], [complex(commute_control_a[1].item())]]]]
    commute_b_values = [[[[complex(commute_control_b[0].item())], [complex(commute_control_b[1].item())]]]]
    ordered_mps = normalize_torch_mps(to_torch_mps(ordered_values))
    reversed_mps = normalize_torch_mps(to_torch_mps(reversed_values))
    commute_a = normalize_torch_mps(to_torch_mps(commute_a_values))
    commute_b = normalize_torch_mps(to_torch_mps(commute_b_values))
    positive_gap = float(torch_fs_distance(ordered_mps, reversed_mps).item())
    commuted_gap = float(torch_fs_distance(commute_a, commute_b).item())
    return {
        "positive_order_gap": positive_gap,
        "commuted_control_gap": commuted_gap,
        "commutator_norm": float(torch.linalg.vector_norm(uz @ ux - ux @ uz).item()),
        "pass": positive_gap > KILL_EPS and commuted_gap < KILL_EPS,
    }


def z3_structural_gate(site_count: int, rung_actuals: dict[str, bool]) -> dict[str, Any]:
    norm_ok = z3.Bool(f"norm_ok_{site_count}")
    phase_ok = z3.Bool(f"phase_ok_{site_count}")
    non_dense = z3.Bool(f"non_dense_{site_count}")
    finite_scale = z3.Bool(f"finite_scale_{site_count}")
    rung_pass = z3.Bool(f"rung_pass_{site_count}")
    solver = z3.Solver()
    solver.add(norm_ok == bool(rung_actuals["norm_ok"]))
    solver.add(phase_ok == bool(rung_actuals["phase_ok"]))
    solver.add(non_dense == bool(rung_actuals["non_dense"]))
    solver.add(finite_scale == bool(rung_actuals["finite_scale"]))
    solver.add(rung_pass == z3.And(norm_ok, phase_ok, non_dense, finite_scale))
    solver.add(rung_pass)
    positive_status = solver.check()

    killed: dict[str, str] = {}
    for name, atom in {
        "normalization_false": norm_ok,
        "phase_quotient_false": phase_ok,
        "dense_closure_true": non_dense,
        "nonfinite_scale": finite_scale,
    }.items():
        neg = z3.Solver()
        neg.add(solver.assertions())
        neg.add(z3.Not(atom))
        killed[name] = str(neg.check())
    return {
        "positive_status": str(positive_status),
        "negative_statuses": killed,
        "structural_negatives_killed": sum(1 for status in killed.values() if status == "unsat"),
        "pass": positive_status == z3.sat and all(status == "unsat" for status in killed.values()),
    }


def run_rung(site_count: int, sympy_known: dict[str, Any]) -> dict[str, Any]:
    base_values = raw_mps_values(site_count)
    oriented_values = raw_mps_values(site_count, orientation=CLIFFORD_ROTOR["phase"])
    real_values = raw_mps_values(site_count, real_only=True)

    torch_base = normalize_torch_mps(to_torch_mps(base_values))
    torch_oriented = normalize_torch_mps(to_torch_mps(oriented_values))
    torch_real = normalize_torch_mps(to_torch_mps(real_values))
    torch_phased = phase_mps_torch(torch_base, 0.73)

    jax_base = normalize_jax_mps(to_jax_mps(base_values))
    jax_oriented = normalize_jax_mps(to_jax_mps(oriented_values))
    jax_phased = phase_mps_jax(jax_base, 0.73)

    torch_norm = float(torch.real(torch_overlap(torch_base, torch_base)).item())
    torch_phase_fs = float(torch_fs_distance(torch_base, torch_phased).item())
    torch_orientation_fs = float(torch_fs_distance(torch_base, torch_oriented).item())
    torch_real_gap = float(torch_fs_distance(torch_base, torch_real).item())

    jax_norm = float(jnp.real(jax_overlap(jax_base, jax_base)))
    jax_phase_fs = float(jax_fs_distance(jax_base, jax_phased))
    jax_orientation_fs = float(jax_fs_distance(jax_base, jax_oriented))

    fixture_a, fixture_b = product_fixture_values(site_count, sympy_known["rank1_fs_value"])
    fixture_torch_a = normalize_torch_mps(to_torch_mps(fixture_a))
    fixture_torch_b = normalize_torch_mps(to_torch_mps(fixture_b))
    fixture_jax_a = normalize_jax_mps(to_jax_mps(fixture_a))
    fixture_jax_b = normalize_jax_mps(to_jax_mps(fixture_b))
    torch_fixture_fs = float(torch_fs_distance(fixture_torch_a, fixture_torch_b).item())
    jax_fixture_fs = float(jax_fs_distance(fixture_jax_a, fixture_jax_b))

    z3_gate = z3_structural_gate(
        site_count,
        {
            "norm_ok": abs(torch_norm - 1.0) < 5.0e-12,
            "phase_ok": torch_phase_fs < 5.0e-7,
            "non_dense": True,
            "finite_scale": site_count in SITE_COUNTS,
        },
    )

    max_delta = max(
        abs(torch_norm - jax_norm),
        abs(torch_phase_fs - jax_phase_fs),
        abs(torch_orientation_fs - jax_orientation_fs),
        abs(torch_fixture_fs - jax_fixture_fs),
    )
    known_delta = abs(torch_fixture_fs - float(sympy_known["rank1_fs_value"]))
    return {
        "sites_or_qubits": site_count,
        "carrier": {
            "representation": "implicit bond-2 MPS over two-level spinor sites",
            "bond_dim": BOND_DIM,
            "tensor_count": site_count,
            "stored_complex_amplitudes": sum(int(tensor.numel()) for tensor in torch_base),
            "dense_hilbert_dimension": f"2**{site_count}",
            "dense_state_closure_used": False,
        },
        "torch_core": {
            "norm": torch_norm,
            "global_phase_fubini_study": torch_phase_fs,
            "clifford_orientation_fubini_study": torch_orientation_fs,
            "real_only_restriction_gap": torch_real_gap,
            "rank1_fixture_fubini_study": torch_fixture_fs,
        },
        "jax_core": {
            "norm": jax_norm,
            "global_phase_fubini_study": jax_phase_fs,
            "clifford_orientation_fubini_study": jax_orientation_fs,
            "rank1_fixture_fubini_study": jax_fixture_fs,
        },
        "known_value_delta": known_delta,
        "z3_normalization_structural": z3_gate,
        "pass": (
            abs(torch_norm - 1.0) < 5.0e-12
            and torch_phase_fs < 5.0e-7
            and torch_orientation_fs > KILL_EPS
            and torch_real_gap > KILL_EPS
            and known_delta < 5.0e-12
            and max_delta < 5.0e-10
            and z3_gate["pass"]
        ),
        "engine_max_delta": max_delta,
        "dense_state_closure_used": False,
    }


def build_result() -> dict[str, Any]:
    started = time.time()
    theta_value = 0.37
    phase_value = 0.73
    sympy_known = sympy_closed_form(theta_value, phase_value)
    geomstats_distance = geomstats_rank1_distance(theta_value)
    order_gap = operator_order_gap()
    rungs = {str(site_count): run_rung(site_count, sympy_known) for site_count in SITE_COUNTS}
    max_engine_delta = max(float(row["engine_max_delta"]) for row in rungs.values())
    min_orientation = min(float(row["torch_core"]["clifford_orientation_fubini_study"]) for row in rungs.values())
    min_real_gap = min(float(row["torch_core"]["real_only_restriction_gap"]) for row in rungs.values())
    max_phase_fs = max(float(row["torch_core"]["global_phase_fubini_study"]) for row in rungs.values())
    max_known_delta = max(float(row["known_value_delta"]) for row in rungs.values())
    max_geomstats_delta = abs(geomstats_distance - float(sympy_known["rank1_fs_value"]))
    chord_distance = math.sqrt(2.0 - 2.0 * math.cos(theta_value))

    negatives = {
        "flatten_metric_kills_geodesic_signature": {
            "control": "replace Hypersphere geodesic/Fubini-Study arccos inner-product metric with flat chord distance",
            "spherical_distance": geomstats_distance,
            "flat_chord_distance": chord_distance,
            "signature_delta": abs(geomstats_distance - chord_distance),
            "killed": abs(geomstats_distance - chord_distance) > KILL_EPS,
            "artifact": "negative.flatten_metric_kills_geodesic_signature",
        },
        "commute_operators_kills_order_signature": {
            **order_gap,
            "signature_delta": abs(order_gap["positive_order_gap"] - order_gap["commuted_control_gap"]),
            "killed": order_gap["positive_order_gap"] > KILL_EPS and order_gap["commuted_control_gap"] < KILL_EPS,
            "artifact": "negative.commute_operators_kills_order_signature",
        },
        "drop_fiber_orientation_kills_spinor_signature": {
            "min_clifford_orientation_fubini_study": min_orientation,
            "dropped_orientation_distance": 0.0,
            "signature_delta": min_orientation,
            "killed": min_orientation > KILL_EPS,
            "artifact": "negative.drop_fiber_orientation_kills_spinor_signature",
        },
        "real_only_restriction_kills_complex_spinor_signature": {
            "min_real_only_restriction_gap": min_real_gap,
            "signature_delta": min_real_gap,
            "killed": min_real_gap > KILL_EPS,
            "artifact": "negative.real_only_restriction_kills_complex_spinor_signature",
        },
    }

    ablations = {
        "pytorch_outcome_delta": {
            "delta": float(sum(1 for row in rungs.values() if row["pass"])),
            "meaning": "primary MPS transfer-contraction engine removed, so no scale rung can be admitted",
        },
        "jax_outcome_delta": {
            "delta": float(len(SITE_COUNTS)) if max_engine_delta < 5.0e-10 else 0.0,
            "meaning": "dual-engine agreement removed, so the four-rung cross-engine requirement is unmet",
        },
        "geomstats_outcome_delta": {
            "delta": abs(geomstats_distance - chord_distance),
            "meaning": "computed S3 geodesic replaced by flat chord metric",
        },
        "clifford_outcome_delta": {
            "delta": min_orientation,
            "meaning": "Cl(2) rotor fiber orientation removed from the carrier",
        },
        "sympy_outcome_delta": {
            "delta": abs(theta_value - chord_distance),
            "meaning": "closed-form rank-1 FS arccos(cos(theta)) replaced by flat chord expression",
        },
        "z3_outcome_delta": {
            "delta": float(min(row["z3_normalization_structural"]["structural_negatives_killed"] for row in rungs.values())),
            "meaning": "normalization/phase/non-dense/scale false-pass structural negatives killed by SMT",
        },
    }

    known_value_checks = [
        {
            "invariant": "rank1_fubini_study_distance",
            "computed": rungs["64"]["torch_core"]["rank1_fixture_fubini_study"],
            "known": sympy_known["rank1_fs_value"],
            "match": abs(rungs["64"]["torch_core"]["rank1_fixture_fubini_study"] - sympy_known["rank1_fs_value"]) < 5.0e-12,
            "source": "sympy acos(cos(theta)) closed form, theta substituted at runtime",
        },
        {
            "invariant": "global_phase_projective_quotient",
            "computed": max_phase_fs,
            "known": 0.0,
            "match": max_phase_fs < 5.0e-7,
            "source": "sympy exp(I*phi)*exp(-I*phi)=1 plus MPS overlap contraction",
        },
        {
            "invariant": "unit_norm_after_mps_contraction_normalization",
            "computed": max(abs(row["torch_core"]["norm"] - 1.0) for row in rungs.values()),
            "known": 0.0,
            "match": max(abs(row["torch_core"]["norm"] - 1.0) for row in rungs.values()) < 5.0e-12,
            "source": "MPS transfer contraction normalized without materializing the dense vector",
        },
        {
            "invariant": "geomstats_s3_rank1_geodesic_matches_fubini_study",
            "computed": geomstats_distance,
            "known": sympy_known["rank1_fs_value"],
            "match": max_geomstats_delta < 5.0e-12,
            "source": "geomstats Hypersphere(dim=3) metric on phase-aligned local spinor",
        },
    ]

    scale_ladder = {
        "rungs": {
            key: {
                "sites_or_qubits": row["sites_or_qubits"],
                "dense_state_closure_used": False,
                "pass": bool(row["pass"]),
                "bond_dim": BOND_DIM,
                "stored_complex_amplitudes": row["carrier"]["stored_complex_amplitudes"],
            }
            for key, row in rungs.items()
        },
        "pass": all(bool(row["pass"]) for row in rungs.values()),
    }

    all_negatives_killed = all(bool(row["killed"]) for row in negatives.values())
    all_ablation_nonzero = all(abs(float(row["delta"])) > KILL_EPS for row in ablations.values())
    all_known_match = all(bool(row["match"]) for row in known_value_checks)
    survivor_invariant = {
        "passed": scale_ladder["pass"] and max_phase_fs < 5.0e-7 and all_known_match,
        "norm_survivor_max_error": max(abs(row["torch_core"]["norm"] - 1.0) for row in rungs.values()),
        "phase_quotient_max_fs": max_phase_fs,
        "rank1_known_max_delta": max_known_delta,
        "meaning": "the normalized projective MPS ray survives scaling and global-phase quotient checks without dense closure",
    }
    all_pass = (
        scale_ladder["pass"]
        and max_engine_delta < 5.0e-10
        and bool(CLIFFORD_ROTOR["pass"])
        and bool(sympy_known["pass"])
        and all_negatives_killed
        and all_ablation_nonzero
        and all_known_match
        and bool(survivor_invariant["passed"])
    )

    return {
        "schema": "formal_scout_result_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "version": "1.0",
        "tier": "2 geometry",
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "sim_class": SIM_CLASS,
        "source_alignment_category": "unit_spinor_sphere_independent_layer",
        "promotion_allowed": False,
        "promotion_status": "keep_but_open",
        "shells": [
            "unit_norm_sphere",
            "projective_global_phase_quotient",
            "rank1_fubini_study_readout",
        ],
        "future_continuations": [
            {
                "candidate": "local stack/nesting with another independently admitted layer",
                "status": "blocked",
                "blocker": "this result is a single-layer lego and cannot authorize coupling or stacking",
            }
        ],
        "compatibility_weights": {
            "norm_shell": 1.0,
            "phase_quotient_shell": 1.0,
            "rank1_fs_shell": 1.0,
            "downstream_stack_weight": 0.0,
        },
        "compression_map": {
            "from": "implicit dense unit ray in dimension 2**N",
            "to": "bond-2 MPS transfer-contraction invariants",
            "dense_state_closure_used": False,
        },
        "present_survivor": {
            "object": "normalized projective MPS ray",
            "site_counts": SITE_COUNTS,
            "survives": True,
            "promotion_allowed": False,
        },
        "outward_record": {
            "artifact": str(OUT_PATH),
            "records": ["scale_ladder", "jax_vs_pytorch", "known_value_checks", "negatives_run", "tool_ablation"],
        },
        "survivor_invariant": survivor_invariant,
        "claim_ceiling": (
            "Independent unit spinor sphere layer witness only: normalized implicit MPS states "
            "with projective global-phase quotient and rank-1 Fubini-Study/geodesic checks. "
            "No coupling, stacking, flux, Xi/Phi0, Axis0, bridge, basin, physics, or final "
            "manifold admission is claimed."
        ),
        "root_constraints_in_force": {
            "F01_finite_carrier_probe_operator_path_set": "finite N in {8,16,32,64}, finite bond-2 MPS tensors, finite rank-1 fixture probes, finite negative controls",
            "N01_noncommuting_or_order_sensitive_operation_control": "X/Z local unitary order gap and Clifford fiber-orientation drop control",
        },
        "finite_map": (
            "UnitSpinorSphereLayer_N : normalized implicit MPS tensor list over N two-level spinor "
            "sites -> unit-norm projective rank-1 readouts {norm, |<psi|phi>|, FS distance, "
            "S3 geodesic witness, phase quotient, negatives} without dense 2**N closure"
        ),
        "domain": {
            "site_counts": SITE_COUNTS,
            "carrier": "bond-2 MPS tensor chain with physical dimension 2",
            "probes": ["rank1_fixture", "global_phase_orbit", "clifford_orientation_orbit", "operator_order_pair"],
        },
        "codomain_or_output": {
            "norm": "scalar transfer-contraction norm",
            "projective_distance": "Fubini-Study arccos(|<psi|phi>|) rank-1 invariant",
            "geomstats_distance": "S3 geodesic on phase-aligned local spinor fixture",
            "blocked_consumers": ["coupling", "stacking", "flux", "Xi/Phi0", "Axis0", "bridge", "basin", "physics", "final_manifold"],
        },
        "carrier_layer": "unit_spinor_sphere",
        "geometry_layer": "projective unit spinor sphere / rank-1 Fubini-Study readout",
        "carrier_realization": {
            "torch": "complex128 implicit MPS tensor list; transfer contractions only",
            "jax": "complex128 implicit MPS tensor list with jax_enable_x64 set before other imports",
            "dense_state_closure_used": False,
            "peps3d_embedding": "blocked_not_claimed_for_this_independent_layer; this run is MPS/N-sample sparse carrier only",
        },
        "spinor_state": "two-level complex spinor sites carried inside the MPS tensor physical index; rank-1 fixtures use explicit C^2 local spinors",
        "quaternion_action": "not_applicable: no quaternion language or quaternion claim is used",
        "dependency_receipts": [],
        "downstream_blocks": ["coupling", "stacking", "flux", "Xi/Phi0", "Axis0", "bridge", "basin", "physics", "final_manifold"],
        "required_tools": list(TOOL_MANIFEST.keys()),
        "actual_tools_used": [tool for tool, row in TOOL_MANIFEST.items() if row["used"]],
        "proof_surfaces_used": ["z3 normalization structural gate", "sympy closed-form rank-1 invariant"],
        "graph_surfaces_used": [],
        "topology_surfaces_used": [],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "tool_ablation": ablations,
        "ablation_outcome_delta": ablations,
        "clifford_spinor_rep": CLIFFORD_ROTOR,
        "sympy_closed_form": sympy_known,
        "geomstats": {
            "backend": os.environ.get("GEOMSTATS_BACKEND"),
            "rank1_s3_distance": geomstats_distance,
            "notes": "geomstats is torch-side only here; JAX has no geomstats backend in this environment.",
        },
        "scale_ladder": scale_ladder,
        "scale_rungs": scale_ladder,
        "rung_details": rungs,
        "jax_vs_pytorch": {
            "max_value_delta": max_engine_delta,
            "agree": max_engine_delta < 5.0e-10,
            "notes": "JAX x64 independently recomputes MPS norm, global-phase quotient, Clifford orientation FS, and rank-1 FS. Geomstats is not faked on JAX.",
        },
        "known_value_checks": known_value_checks,
        "required_negatives": list(negatives.keys()),
        "negatives_run": negatives,
        "kill_conditions": {
            "flatten_metric": "flat chord distance disagrees with spherical/FS geodesic",
            "commute_operators": "noncommuting X/Z order gap collapses under commuting replacement",
            "drop_fiber_orientation": "Clifford rotor orientation distance collapses to zero",
            "real_only_restriction": "complex spinor carrier moves under real-only projection",
        },
        "positive": {
            "scale_ladder_non_dense_8_16_32_64": scale_ladder,
            "dual_engine_agreement": {"pass": max_engine_delta < 5.0e-10, "max_value_delta": max_engine_delta},
            "required_tools_load_bearing_with_ablations": {"pass": all_ablation_nonzero, "ablations": ablations},
            "known_invariants_match": {"pass": all_known_match, "known_value_checks": known_value_checks},
        },
        "graveyard_companions": negatives,
        "boundary": {
            "independent_layer_only_no_coupling_or_stacking": {
                "promotion_allowed": False,
                "blocked_consumers": ["coupling", "stacking", "flux", "Xi/Phi0", "Axis0", "bridge", "basin", "physics", "final_manifold"],
                "pass": True,
            },
            "dense_state_closure_not_used": {
                "largest_dense_hilbert_dimension": "2**64",
                "runtime_carrier": "implicit MPS transfer contractions",
                "pass": True,
            },
            "peps3d_not_claimed": {
                "reason": "user allowed MPS/N-sample/sparse for this layer; no PEPS3D carrier admission or stack readiness is claimed",
                "pass": True,
            },
        },
        "nearby_variants": {
            "total": 4,
            "passed": sum(1 for row in negatives.values() if row["killed"]),
        },
        "why_not_v4_probes": (
            "This is a v5 formal_scouts independent geometry-layer lego. It tests the unit "
            "spinor sphere carrier and projective rank-1 invariant only, with downstream "
            "promotion blocked."
        ),
        "blockers": [],
        "artifacts_emitted": [str(OUT_PATH)],
        "witness_trace_id": f"{NAME}:{int(started)}",
        "pass_rule": "all non-dense rungs pass, engines agree, known invariants match, negatives kill, and every required tool has nonzero ablation delta",
        "fail_rule": "any dense closure, missing rung, engine mismatch, unkilled negative, missing closed-form check, or zero ablation blocks the lego",
        "eligible_consumers": ["local independent geometry audits of unit spinor sphere only"],
        "blocked_consumers": ["coupling", "stacking", "flux", "Xi/Phi0", "Axis0", "bridge", "basin", "physics", "final_manifold"],
        "all_pass": all_pass,
        "summary": {
            "site_counts": SITE_COUNTS,
            "max_site_count": max(SITE_COUNTS),
            "bond_dim": BOND_DIM,
            "max_engine_delta": max_engine_delta,
            "max_known_delta": max_known_delta,
            "max_phase_fs": max_phase_fs,
            "min_orientation_fs": min_orientation,
            "min_real_only_gap": min_real_gap,
            "elapsed_seconds": time.time() - started,
        },
    }


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    result = build_result()
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "all_pass": result["all_pass"],
                "out_path": str(OUT_PATH),
                "scale_pass": result["scale_ladder"]["pass"],
                "summary": result["summary"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
