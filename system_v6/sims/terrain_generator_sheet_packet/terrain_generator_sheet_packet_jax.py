#!/usr/bin/env python3
"""JAX leg for the source-locked terrain generator sheet packet."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Callable

import cvc5
from cvc5 import Kind
import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp
import jax.scipy.linalg as jsp_linalg
import z3


ROOT = Path(__file__).resolve().parents[3]
SIM_ID = "terrain_generator_sheet_packet"
OBJECT_ID = f"{SIM_ID}_jax"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_jax.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_jax_results.json"

CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
READS_PEER_RESULT = False
TOL = 1.0e-8
SMT_SCALE = 10**9
T_CHANNEL = 0.4
EPS = 0.2
SE_LAMBDA = 0.2
GAMMA_NI = 0.5
KAPPA_SI = 0.4
OMEGA_SI = EPS
ETA0 = math.pi / 8.0
PHI0 = 0.3
CHI0 = 0.2

SOURCE_LINE_REFS = {
    "terrain_math_sigma": "system_v5/READ ONLY Reference Docs/terrain math.md:23-24",
    "terrain_math_loops": "system_v5/READ ONLY Reference Docs/terrain math.md:30-33",
    "terrain_math_generators": "system_v5/READ ONLY Reference Docs/terrain math.md:76-83",
    "terrain_math_projectors": "system_v5/READ ONLY Reference Docs/terrain math.md:89-90",
    "terrain_math_placements": "system_v5/READ ONLY Reference Docs/terrain math.md:122-150",
    "rosetta_lk_projectors": "system_v5/READ ONLY Reference Docs/terrain rosetta strong math.md:53-58",
    "rosetta_stage_channel": "system_v5/READ ONLY Reference Docs/terrain rosetta strong math.md:63-71",
    "rosetta_placements": "system_v5/READ ONLY Reference Docs/terrain rosetta strong math.md:151-183",
    "scaffold_terrain_section": "system_v6/foundations/working_math_scaffold_20260609.md:77-101",
    "operator_state_matrix": "system_v5/READ ONLY Reference Docs/operator math explicit.md:8-30",
}

SOURCE_LOCK_LINE_RANGES = {
    "terrain_math_generators_78_83": ("system_v5/READ ONLY Reference Docs/terrain math.md", 78, 83),
    "terrain_math_placements_122_137": ("system_v5/READ ONLY Reference Docs/terrain math.md", 122, 137),
    "rosetta_si_projectors_57_58": ("system_v5/READ ONLY Reference Docs/terrain rosetta strong math.md", 57, 58),
    "rosetta_stage_channel_71": ("system_v5/READ ONLY Reference Docs/terrain rosetta strong math.md", 71, 71),
    "rosetta_placements_151_183": ("system_v5/READ ONLY Reference Docs/terrain rosetta strong math.md", 151, 183),
}

SOURCE_LOCK_EXPECTED_SHA256 = {
    "terrain_math_generators_78_83": "1c2041062a386ac505aa1d18f2fdc85a304a1f99515e5ad67c56b7a6aed9a1c8",
    "terrain_math_placements_122_137": "0a890e6a0363eae5e96ac85793655d2222456ddba4d0380bdb36fbb0c8df3c53",
    "rosetta_si_projectors_57_58": "fdb1447de960e2dabc406777b939018b7a15bfa135083be62a7145c248d75a83",
    "rosetta_stage_channel_71": "85d126c9ffeea7ea2babe2a3764252a177530e974c20a81715b6514839799545",
    "rosetta_placements_151_183": "251b15eb6f7623c5ccb9ddbd4757e111649801322a768c884379d3bf3c61365c",
}

PIN_SPEC = {
    "H_0": "(sigma_x + sigma_y + sigma_z) / sqrt(3)",
    "H_L": "+H_0",
    "H_R": "-H_0",
    "eps_all": EPS,
    "se_lambda": {
        "value": SE_LAMBDA,
        "status": "PINNED-CHOICE",
        "reason": "source gives a Se dissipator family but no numeric lambda in the requested line refs",
    },
    "gamma_Ni": GAMMA_NI,
    "kappa_Si": KAPPA_SI,
    "omega_Si": {
        "value": OMEGA_SI,
        "status": "PINNED-CHOICE",
        "reason": "source leaves omega/K frame magnitude free; set equal to eps for this bounded packet",
    },
    "Si_frames": {
        "m_L": "z-axis",
        "m_R": "x-axis",
        "status": "PINNED-CHOICE not source-forced",
    },
    "Phi": "expm(0.4 * X)",
    "rho_0_rho_1": {
        "status": "PINNED-FALLBACK",
        "reason": "source_locked_operator_base_packet is not present in this checkout; states instantiate the operator packet density constraints",
    },
}

PAULI_EXPANSION_FAMILY_PIN_METADATA = {
    "Se_Funnel_L": {
        "status": "PINNED-CHOICE not source-forced",
        "reason": "source fixes the Se dissipator family shape but not this finite Pauli coefficient set",
        "source_refs": [
            "system_v5/READ ONLY Reference Docs/terrain math.md:76",
            "system_v5/READ ONLY Reference Docs/terrain rosetta strong math.md:53",
        ],
    },
    "Se_Cannon_R": {
        "status": "PINNED-CHOICE not source-forced",
        "reason": "source fixes the Se dissipator family shape but not this finite Pauli coefficient set",
        "source_refs": [
            "system_v5/READ ONLY Reference Docs/terrain math.md:77",
            "system_v5/READ ONLY Reference Docs/terrain rosetta strong math.md:54",
        ],
    },
    "Ne_Vortex_L": {
        "status": "PINNED-CHOICE not source-forced",
        "reason": "pure Ne is source-forced; weak-dissipator Ne uses this exploratory coefficient set as a pinned variant",
        "source_refs": [
            "system_v5/READ ONLY Reference Docs/terrain math.md:78",
            "system_v5/READ ONLY Reference Docs/terrain rosetta strong math.md:55",
        ],
    },
    "Ne_Spiral_R": {
        "status": "PINNED-CHOICE not source-forced",
        "reason": "pure Ne is source-forced; weak-dissipator Ne uses this exploratory coefficient set as a pinned variant",
        "source_refs": [
            "system_v5/READ ONLY Reference Docs/terrain math.md:79",
            "system_v5/READ ONLY Reference Docs/terrain rosetta strong math.md:56",
        ],
    },
}

AXIS0_DELTA_VECTOR = jnp.asarray([0.90, -0.33, 0.30], dtype=jnp.float64)
AXIS0_DELTA_VECTOR = AXIS0_DELTA_VECTOR / jnp.linalg.norm(AXIS0_DELTA_VECTOR)
AXIS0_DELTA_SCALE = 0.01
AXIS0_TIMES = [0.0, 0.1, 0.2, T_CHANNEL]
AXIS0_DOCTRINE_PATTERN = {"Ne": "+", "Ni": "+", "Se": "-", "Si": "-"}
PINNED_BIPARTITE_LAMBDA = 0.37
PINNED_BIPARTITE_PHASE = 0.41

TOOL_MANIFEST = {
    "jax": {
        "tried": True,
        "used": True,
        "reason": "supportive x64 finite channel, Choi, projector, placement, and pair-separation arithmetic; substrate demoted under capability-probe doctrine",
    },
    "jax.numpy": {
        "tried": True,
        "used": True,
        "reason": "supportive 2x2 density, Bloch, superoperator, entropy, and trace-norm calculations; substrate demoted under capability-probe doctrine",
    },
    "jax.scipy.linalg": {
        "tried": True,
        "used": True,
        "reason": "load-bearing matrix exponential for Phi=expm(0.4 X)",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing in-solver equality/inequality check over bound Pit/Source generator entries",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent SMT check over the same bound Pit/Source generator entries",
    },
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive paths, timestamps, hashing, and JSON receipt serialization",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "jax": "supportive",
    "jax.numpy": "supportive",
    "jax.scipy.linalg": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "python_stdlib": "supportive",
}

I2 = jnp.asarray([[1.0, 0.0], [0.0, 1.0]], dtype=jnp.complex128)
SX = jnp.asarray([[0.0, 1.0], [1.0, 0.0]], dtype=jnp.complex128)
SY = jnp.asarray([[0.0, -1.0j], [1.0j, 0.0]], dtype=jnp.complex128)
SZ = jnp.asarray([[1.0, 0.0], [0.0, -1.0]], dtype=jnp.complex128)
SIGMA_MINUS = jnp.asarray([[0.0, 0.0], [1.0, 0.0]], dtype=jnp.complex128)
SIGMA_PLUS = jnp.asarray([[0.0, 1.0], [0.0, 0.0]], dtype=jnp.complex128)
H0 = (SX + SY + SZ) / jnp.sqrt(jnp.asarray(3.0, dtype=jnp.float64))
PZ_PLUS = 0.5 * (I2 + SZ)
PZ_MINUS = 0.5 * (I2 - SZ)
PX_PLUS = 0.5 * (I2 + SX)
PX_MINUS = 0.5 * (I2 - SX)

# The locked sigma matrices make D[sigma_-] attract the second matrix basis
# projector. The task names that side |0><0|; keep the source matrix and record
# the label mapping instead of swapping the source definitions.
TERRAIN_KET0 = PZ_MINUS
TERRAIN_KET1 = PZ_PLUS

RHO_0 = jnp.asarray([[0.65, 0.21 - 0.13j], [0.21 + 0.13j, 0.35]], dtype=jnp.complex128)
RHO_1 = jnp.asarray([[0.42, -0.18 + 0.16j], [-0.18 - 0.16j, 0.58]], dtype=jnp.complex128)
SENSITIVE_RHO = jnp.asarray([[0.50, 0.23 - 0.17j], [0.23 + 0.17j, 0.50]], dtype=jnp.complex128)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_line_range(relative_path: str, start_line: int, end_line: int) -> str:
    lines = (ROOT / relative_path).read_text(encoding="utf-8").splitlines()
    payload = "\n".join(lines[start_line - 1 : end_line]) + "\n"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def source_lock_freshness() -> dict[str, Any]:
    rows = {}
    for name, (relative_path, start_line, end_line) in SOURCE_LOCK_LINE_RANGES.items():
        current = sha256_line_range(relative_path, start_line, end_line)
        expected = SOURCE_LOCK_EXPECTED_SHA256[name]
        rows[name] = {
            "path": relative_path,
            "start_line": start_line,
            "end_line": end_line,
            "expected_sha256": expected,
            "current_sha256": current,
            "fresh": current == expected,
            "stale_red": current != expected,
        }
    return {
        "lock_kind": "exact_source_line_range_sha256",
        "rows": rows,
        "all_fresh": all(row["fresh"] for row in rows.values()),
        "stale_red": any(row["stale_red"] for row in rows.values()),
    }


def to_builtin(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): to_builtin(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_builtin(v) for v in value]
    if hasattr(value, "shape"):
        arr = jax.device_get(value)
        if arr.shape == ():
            if jnp.iscomplexobj(value):
                return {"real": float(jnp.real(arr)), "imag": float(jnp.imag(arr))}
            return float(arr)
        if jnp.iscomplexobj(value):
            return {"real": jnp.real(arr).tolist(), "imag": jnp.imag(arr).tolist()}
        return arr.tolist()
    if isinstance(value, (bool, int, float, str)) or value is None:
        return value
    return str(value)


def real_float(value: Any) -> float:
    return float(jax.device_get(jnp.real(value)))


def complex_pair(value: Any) -> dict[str, float]:
    scalar = jax.device_get(value)
    return {"real": float(jnp.real(scalar)), "imag": float(jnp.imag(scalar))}


def hermitize(rho: jax.Array) -> jax.Array:
    return 0.5 * (rho + jnp.conjugate(rho.T))


def density_valid(rho: jax.Array) -> dict[str, Any]:
    herm = hermitize(rho)
    eigs = jnp.linalg.eigvalsh(herm)
    return {
        "trace_residual": abs(real_float(jnp.trace(rho)) - 1.0),
        "hermitian_residual": real_float(jnp.max(jnp.abs(rho - jnp.conjugate(rho.T)))),
        "min_eigenvalue": real_float(jnp.min(eigs)),
        "pass": bool(abs(real_float(jnp.trace(rho)) - 1.0) <= TOL and real_float(jnp.min(eigs)) >= -TOL),
    }


def entropy_vn(rho: jax.Array) -> float:
    vals = jnp.clip(jnp.real(jnp.linalg.eigvalsh(hermitize(rho))), 0.0, 1.0)
    ent = -jnp.sum(jnp.where(vals > 1.0e-14, vals * jnp.log(vals), 0.0))
    return real_float(ent)


def purity(rho: jax.Array) -> float:
    return real_float(jnp.trace(rho @ rho))


def trace_norm(mat: jax.Array) -> float:
    return real_float(jnp.sum(jnp.linalg.svd(mat, compute_uv=False)))


def trace_distance(a: jax.Array, b: jax.Array) -> float:
    return 0.5 * trace_norm(a - b)


def fro_norm(mat: jax.Array) -> float:
    return real_float(jnp.linalg.norm(mat))


def bloch(rho: jax.Array) -> jax.Array:
    return jnp.asarray(
        [
            jnp.real(jnp.trace(rho @ SX)),
            jnp.real(jnp.trace(rho @ SY)),
            jnp.real(jnp.trace(rho @ SZ)),
        ],
        dtype=jnp.float64,
    )


def dissipator(op: jax.Array, rho: jax.Array) -> jax.Array:
    od = jnp.conjugate(op.T)
    odo = od @ op
    return op @ rho @ od - 0.5 * (odo @ rho + rho @ odo)


def dephase_projectors(projectors: list[jax.Array], rho: jax.Array) -> jax.Array:
    return sum((p @ rho @ p for p in projectors), jnp.zeros((2, 2), dtype=jnp.complex128)) - rho


def comm(h: jax.Array, rho: jax.Array) -> jax.Array:
    return h @ rho - rho @ h


def pauli_from_coeffs(coeffs: dict[str, complex]) -> jax.Array:
    return (
        complex(coeffs.get("I", 0.0)) * I2
        + complex(coeffs.get("sx", 0.0)) * SX
        + complex(coeffs.get("sy", 0.0)) * SY
        + complex(coeffs.get("sz", 0.0)) * SZ
    )


SQRT_SE = math.sqrt(SE_LAMBDA)
SE_FUNNEL_COEFFS = [
    {"I": 0.0, "sx": SQRT_SE, "sy": 0.0, "sz": 0.0},
    {"I": 0.0, "sx": 0.0, "sy": SQRT_SE, "sz": 0.0},
]
SE_CANNON_COEFFS = [
    {"I": 0.0, "sx": -SQRT_SE, "sy": 0.0, "sz": 0.0},
    {"I": 0.0, "sx": 0.0, "sy": 1j * SQRT_SE, "sz": 0.0},
]
NE_VORTEX_COEFFS = [
    {"I": 0.0, "sx": 1.0, "sy": 0.0, "sz": 0.0},
    {"I": 0.0, "sx": 0.0, "sy": 0.0, "sz": 1.0},
]
NE_SPIRAL_COEFFS = [
    {"I": 0.0, "sx": -1.0, "sy": 0.0, "sz": 0.0},
    {"I": 0.0, "sx": 0.0, "sy": 0.0, "sz": 1j},
]


def dissipator_family(coeff_rows: list[dict[str, complex]], rho: jax.Array) -> jax.Array:
    out = jnp.zeros((2, 2), dtype=jnp.complex128)
    for coeffs in coeff_rows:
        out = out + dissipator(pauli_from_coeffs(coeffs), rho)
    return out


def generator_fn(
    terrain: str,
    *,
    ne_variant: str = "pure_hamiltonian",
    erased_weyl: bool = False,
    commuting_si_frame: bool = False,
    sigma_swap_source_side: bool = False,
    sigma_only_swap: bool = False,
) -> Callable[[jax.Array], jax.Array]:
    h_l = H0
    h_r = H0 if erased_weyl else -H0
    if terrain == "Funnel":
        return lambda rho: dissipator_family(SE_FUNNEL_COEFFS, rho) - 1j * EPS * comm(h_l, rho)
    if terrain == "Cannon":
        return lambda rho: dissipator_family(SE_CANNON_COEFFS, rho) - 1j * EPS * comm(h_r, rho)
    if terrain == "Vortex":
        def vortex(rho: jax.Array) -> jax.Array:
            base = -1j * comm(h_l, rho)
            if ne_variant == "weak_dissipator":
                base = base + EPS * dissipator_family(NE_VORTEX_COEFFS, rho)
            return base
        return vortex
    if terrain == "Spiral":
        def spiral(rho: jax.Array) -> jax.Array:
            base = -1j * comm(h_r, rho)
            if ne_variant == "weak_dissipator":
                base = base + EPS * dissipator_family(NE_SPIRAL_COEFFS, rho)
            return base
        return spiral
    if terrain == "Pit":
        if sigma_swap_source_side:
            jump = SIGMA_PLUS
            h = h_r
        elif sigma_only_swap:
            jump = SIGMA_PLUS
            h = h_l
        else:
            jump = SIGMA_MINUS
            h = h_l
        return lambda rho: GAMMA_NI * dissipator(jump, rho) - 1j * EPS * comm(h, rho)
    if terrain == "Source":
        return lambda rho: GAMMA_NI * dissipator(SIGMA_PLUS, rho) - 1j * EPS * comm(h_r, rho)
    if terrain == "Hill":
        return lambda rho: -1j * comm(OMEGA_SI * SZ, rho) + KAPPA_SI * dephase_projectors([PZ_PLUS, PZ_MINUS], rho)
    if terrain == "Citadel":
        if commuting_si_frame:
            return lambda rho: -1j * comm(OMEGA_SI * SZ, rho) + KAPPA_SI * dephase_projectors([PZ_PLUS, PZ_MINUS], rho)
        return lambda rho: -1j * comm(OMEGA_SI * SX, rho) + KAPPA_SI * dephase_projectors([PX_PLUS, PX_MINUS], rho)
    raise ValueError(terrain)


def basis_matrix(i: int, j: int) -> jax.Array:
    return jnp.zeros((2, 2), dtype=jnp.complex128).at[i, j].set(1.0 + 0.0j)


def vec(mat: jax.Array) -> jax.Array:
    return mat.reshape((4,))


def unvec(values: jax.Array) -> jax.Array:
    return values.reshape((2, 2))


def superoperator(gen: Callable[[jax.Array], jax.Array]) -> jax.Array:
    cols = []
    for i in range(2):
        for j in range(2):
            cols.append(vec(gen(basis_matrix(i, j))))
    return jnp.stack(cols, axis=1)


def channel_from_generator(gen: Callable[[jax.Array], jax.Array]) -> jax.Array:
    return jsp_linalg.expm(T_CHANNEL * superoperator(gen))


def channel_from_generator_at(gen: Callable[[jax.Array], jax.Array], time_value: float) -> jax.Array:
    return jsp_linalg.expm(time_value * superoperator(gen))


def apply_channel_linear(channel: jax.Array, mat: jax.Array) -> jax.Array:
    return unvec(channel @ vec(mat))


def apply_channel(channel: jax.Array, rho: jax.Array) -> jax.Array:
    out = unvec(channel @ vec(rho))
    return hermitize(out) / jnp.trace(out)


def unitality_column(channels: dict[str, jax.Array]) -> dict[str, Any]:
    rows = {}
    for name, channel in channels.items():
        e_identity = apply_channel_linear(channel, I2)
        residual = fro_norm(e_identity - I2)
        rows[name] = {
            "E_I": to_builtin(e_identity),
            "E_I_minus_I_fro_norm": residual,
            "unital_within_tolerance": residual <= 1.0e-7,
            "expected_non_unital": name in {"Pit", "Source"},
        }
    ni_values = [rows[name]["E_I_minus_I_fro_norm"] for name in ("Pit", "Source")]
    non_ni_values = [row["E_I_minus_I_fro_norm"] for name, row in rows.items() if name not in {"Pit", "Source"}]
    return {
        "definition": "unital iff E(I)=I for the finite channel exp(tX)",
        "rows": rows,
        "ni_pair_non_unital": all(value > 1.0e-4 for value in ni_values),
        "non_ni_unital": all(value <= 1.0e-7 for value in non_ni_values),
        "max_non_ni_E_I_minus_I_fro_norm": max(non_ni_values),
        "min_ni_E_I_minus_I_fro_norm": min(ni_values),
        "pass": all(value > 1.0e-4 for value in ni_values) and all(value <= 1.0e-7 for value in non_ni_values),
    }


def pauli_coefficients(delta: jax.Array) -> jax.Array:
    return jnp.asarray(
        [
            jnp.real(jnp.trace(delta @ SX)),
            jnp.real(jnp.trace(delta @ SY)),
            jnp.real(jnp.trace(delta @ SZ)),
        ],
        dtype=jnp.float64,
    )


def pauli_diversity_metrics(delta: jax.Array) -> dict[str, Any]:
    coeffs = pauli_coefficients(delta)
    weights = coeffs * coeffs
    weight_sum = real_float(jnp.sum(weights))
    if weight_sum <= 1.0e-14:
        participation = 0.0
        entropy = 0.0
    else:
        probs = weights / weight_sum
        participation = real_float((jnp.sum(weights) * jnp.sum(weights)) / jnp.sum(weights * weights))
        entropy = real_float(-jnp.sum(jnp.where(probs > 1.0e-14, probs * jnp.log(probs), 0.0)))
    return {
        "pauli_coefficients": {"sx": real_float(coeffs[0]), "sy": real_float(coeffs[1]), "sz": real_float(coeffs[2])},
        "pauli_weight_sum": weight_sum,
        "pauli_participation_ratio": participation,
        "observable_spread_entropy": entropy,
        "trace_norm": trace_norm(delta),
    }


def sign_label(value: float, *, tol: float = 1.0e-8) -> str:
    if value > tol:
        return "+"
    if value < -tol:
        return "-"
    return "0"


def axis0_generator_specs() -> list[dict[str, Any]]:
    return [
        {"name": "Vortex:pure_hamiltonian", "terrain": "Vortex", "kwargs": {"ne_variant": "pure_hamiltonian"}, "family": "Ne", "group": "Ne:pure_hamiltonian"},
        {"name": "Spiral:pure_hamiltonian", "terrain": "Spiral", "kwargs": {"ne_variant": "pure_hamiltonian"}, "family": "Ne", "group": "Ne:pure_hamiltonian"},
        {"name": "Vortex:weak_dissipator", "terrain": "Vortex", "kwargs": {"ne_variant": "weak_dissipator"}, "family": "Ne", "group": "Ne:weak_dissipator"},
        {"name": "Spiral:weak_dissipator", "terrain": "Spiral", "kwargs": {"ne_variant": "weak_dissipator"}, "family": "Ne", "group": "Ne:weak_dissipator"},
        {"name": "Pit", "terrain": "Pit", "kwargs": {}, "family": "Ni", "group": "Ni"},
        {"name": "Source", "terrain": "Source", "kwargs": {}, "family": "Ni", "group": "Ni"},
        {"name": "Funnel", "terrain": "Funnel", "kwargs": {}, "family": "Se", "group": "Se"},
        {"name": "Cannon", "terrain": "Cannon", "kwargs": {}, "family": "Se", "group": "Se"},
        {"name": "Hill", "terrain": "Hill", "kwargs": {}, "family": "Si", "group": "Si"},
        {"name": "Citadel", "terrain": "Citadel", "kwargs": {}, "family": "Si", "group": "Si"},
    ]


def axis0_delta_rho() -> jax.Array:
    return AXIS0_DELTA_SCALE * (
        AXIS0_DELTA_VECTOR[0] * SX + AXIS0_DELTA_VECTOR[1] * SY + AXIS0_DELTA_VECTOR[2] * SZ
    )


def axis0_response() -> dict[str, Any]:
    delta0 = axis0_delta_rho()
    initial = pauli_diversity_metrics(delta0)
    functionals = ["pauli_participation_ratio", "trace_norm", "observable_spread_entropy"]
    rows = {}
    for spec in axis0_generator_specs():
        gen = generator_fn(spec["terrain"], **spec["kwargs"])
        series = []
        for time_value in AXIS0_TIMES:
            channel = channel_from_generator_at(gen, time_value)
            delta_t = apply_channel_linear(channel, delta0)
            series.append({"time": time_value, **pauli_diversity_metrics(delta_t)})
        final = series[-1]
        rows[spec["name"]] = {
            "family": spec["family"],
            "group": spec["group"],
            "series": series,
            "responses": {functional: final[functional] - initial[functional] for functional in functionals},
            "signs": {functional: sign_label(final[functional] - initial[functional]) for functional in functionals},
        }

    aggregate_groups = {
        "Ne:pure_hamiltonian": ["Vortex:pure_hamiltonian", "Spiral:pure_hamiltonian"],
        "Ne:weak_dissipator": ["Vortex:weak_dissipator", "Spiral:weak_dissipator"],
        "Ne": ["Vortex:pure_hamiltonian", "Spiral:pure_hamiltonian", "Vortex:weak_dissipator", "Spiral:weak_dissipator"],
        "Ni": ["Pit", "Source"],
        "Se": ["Funnel", "Cannon"],
        "Si": ["Hill", "Citadel"],
    }
    group_rows = {}
    for group, names in aggregate_groups.items():
        responses = {
            functional: sum(rows[name]["responses"][functional] for name in names) / len(names)
            for functional in functionals
        }
        group_rows[group] = {
            "members": names,
            "responses": responses,
            "signs": {functional: sign_label(value) for functional, value in responses.items()},
        }
    sign_table = {
        functional: {group: group_rows[group]["signs"][functional] for group in ["Ne:pure_hamiltonian", "Ne:weak_dissipator", "Ni", "Se", "Si"]}
        for functional in functionals
    }
    doctrine_sign_table = {
        functional: {family: group_rows[family]["signs"][functional] for family in ["Ne", "Ni", "Se", "Si"]}
        for functional in functionals
    }
    doctrine_pattern_match = {
        functional: doctrine_sign_table[functional] == AXIS0_DOCTRINE_PATTERN for functional in functionals
    }
    return {
        "spec_ref": "system_v6/foundations/working_math_scaffold_20260609.md:270-276",
        "delta_rho": {
            "definition": "0.01 * normalized(0.90*sigma_x - 0.33*sigma_y + 0.30*sigma_z)",
            "pin_status": "PINNED-CHOICE not source-forced",
            "pauli_vector_normalized": to_builtin(AXIS0_DELTA_VECTOR),
            "matrix": to_builtin(delta0),
        },
        "primary_functional": "pauli_participation_ratio",
        "functional_definitions": {
            "pauli_participation_ratio": "(sum_i c_i^2)^2 / sum_i c_i^4 for c_i=Tr(delta_rho(t) sigma_i)",
            "trace_norm": "||delta_rho(t)||_1",
            "observable_spread_entropy": "Shannon entropy of normalized c_i^2 over {sigma_x,sigma_y,sigma_z}",
        },
        "initial_metrics": initial,
        "rows": rows,
        "groups": group_rows,
        "sign_table": sign_table,
        "doctrine_family_sign_table": doctrine_sign_table,
        "doctrine_prediction": AXIS0_DOCTRINE_PATTERN,
        "doctrine_pattern_match": doctrine_pattern_match,
        "pass": all(row["series"] for row in rows.values()),
    }


def choi_matrix(channel: jax.Array) -> jax.Array:
    choi = jnp.zeros((4, 4), dtype=jnp.complex128)
    for i in range(2):
        for j in range(2):
            block = unvec(channel @ vec(basis_matrix(i, j)))
            choi = choi.at[i * 2 : (i + 1) * 2, j * 2 : (j + 1) * 2].set(block)
    return hermitize(choi)


def channel_certificate(channel: jax.Array) -> dict[str, Any]:
    choi = choi_matrix(channel)
    eigs = jnp.linalg.eigvalsh(choi)
    tp_residual = 0.0
    for i in range(2):
        for j in range(2):
            expected = 1.0 if i == j else 0.0
            got = real_float(jnp.trace(unvec(channel @ vec(basis_matrix(i, j)))))
            tp_residual = max(tp_residual, abs(got - expected))
    min_choi = real_float(jnp.min(eigs))
    return {
        "choi_min_eigenvalue": min_choi,
        "choi_trace": real_float(jnp.trace(choi)),
        "tp_residual": tp_residual,
        "choi_psd": min_choi >= -1.0e-7,
        "tp": tp_residual <= 1.0e-7,
        "pass": min_choi >= -1.0e-7 and tp_residual <= 1.0e-7,
    }


def pinned_bipartite_state() -> jax.Array:
    amp0 = math.sqrt(PINNED_BIPARTITE_LAMBDA)
    amp1 = math.sqrt(1.0 - PINNED_BIPARTITE_LAMBDA)
    phase = jnp.exp(1j * PINNED_BIPARTITE_PHASE)
    psi = jnp.asarray([amp0, 0.0, 0.0, phase * amp1], dtype=jnp.complex128)
    return jnp.outer(psi, jnp.conjugate(psi))


def partial_trace_ancilla(rho_ab: jax.Array) -> jax.Array:
    rho_b = jnp.zeros((2, 2), dtype=jnp.complex128)
    for b in range(2):
        for bp in range(2):
            value = 0.0 + 0.0j
            for a in range(2):
                value = value + rho_ab[2 * a + b, 2 * a + bp]
            rho_b = rho_b.at[b, bp].set(value)
    return rho_b


def apply_channel_to_system(channel: jax.Array, rho_ab: jax.Array) -> jax.Array:
    out = jnp.zeros((4, 4), dtype=jnp.complex128)
    for b in range(2):
        for bp in range(2):
            block = jnp.zeros((2, 2), dtype=jnp.complex128)
            for a in range(2):
                for ap in range(2):
                    block = block.at[a, ap].set(rho_ab[2 * a + b, 2 * ap + bp])
            block_out = apply_channel_linear(channel, block)
            for a in range(2):
                for ap in range(2):
                    out = out.at[2 * a + b, 2 * ap + bp].set(block_out[a, ap])
    out = hermitize(out)
    return out / jnp.trace(out)


def conditional_entropy_a_given_b(rho_ab: jax.Array) -> float:
    return entropy_vn(rho_ab) - entropy_vn(partial_trace_ancilla(rho_ab))


def generator_hamiltonian(name: str) -> jax.Array:
    if name in {"Funnel", "Vortex:pure_hamiltonian", "Vortex:weak_dissipator", "Pit"}:
        return H0
    if name in {"Cannon", "Spiral:pure_hamiltonian", "Spiral:weak_dissipator", "Source"}:
        return -H0
    if name == "Hill":
        return OMEGA_SI * SZ
    if name == "Citadel":
        return OMEGA_SI * SX
    raise ValueError(name)


def dissipative_component_present(name: str) -> bool:
    return name not in {"Vortex:pure_hamiltonian", "Spiral:pure_hamiltonian"}


def entropy_columns(channels: dict[str, jax.Array]) -> dict[str, Any]:
    rho_ab = pinned_bipartite_state()
    conditional_before = conditional_entropy_a_given_b(rho_ab)
    rows = {}
    for name, channel in channels.items():
        hamiltonian = generator_hamiltonian(name)
        state_rows = {}
        for state_name, rho in {"rho_0": RHO_0, "rho_1": RHO_1}.items():
            out = apply_channel(channel, rho)
            energy_before = real_float(jnp.trace(hamiltonian @ rho))
            energy_after = real_float(jnp.trace(hamiltonian @ out))
            state_rows[state_name] = {
                "Delta_S_system_von_neumann": entropy_vn(out) - entropy_vn(rho),
                "system_entropy_before": entropy_vn(rho),
                "system_entropy_after": entropy_vn(out),
                "bath_exchange_energy_delta_TrHrho": energy_after - energy_before,
                "energy_before_TrHrho": energy_before,
                "energy_after_TrHrho": energy_after,
            }
        out_ab = apply_channel_to_system(channel, rho_ab)
        conditional_after = conditional_entropy_a_given_b(out_ab)
        rows[name] = {
            "dissipative_component_present": dissipative_component_present(name),
            "hamiltonian_for_energy_bookkeeping": to_builtin(hamiltonian),
            "system_entropy": state_rows,
            "pinned_bipartite_extension": {
                "state": "sqrt(lambda)|00> + exp(i phase)*sqrt(1-lambda)|11>",
                "lambda": PINNED_BIPARTITE_LAMBDA,
                "phase": PINNED_BIPARTITE_PHASE,
                "S_A_given_B_before": conditional_before,
                "S_A_given_B_after": conditional_after,
                "Delta_S_A_given_B": conditional_after - conditional_before,
            },
        }
    return {
        "definition": "Delta-S_system is von Neumann entropy after-before; bath exchange is Delta Tr[H rho]; Delta-S(A|B) applies E tensor I to a pinned partially entangled system-ancilla state.",
        "rows": rows,
    }


def state_deltas(channel: jax.Array) -> dict[str, Any]:
    rows = {}
    for name, rho in {"rho_0": RHO_0, "rho_1": RHO_1}.items():
        out = apply_channel(channel, rho)
        rows[name] = {
            "entropy_before": entropy_vn(rho),
            "entropy_after": entropy_vn(out),
            "entropy_delta": entropy_vn(out) - entropy_vn(rho),
            "purity_before": purity(rho),
            "purity_after": purity(out),
            "purity_delta": purity(out) - purity(rho),
            "trace_distance_from_input": trace_distance(out, rho),
        }
    return rows


def projector_coherence(rho: jax.Array, projectors: list[jax.Array]) -> float:
    return sum(fro_norm(projectors[i] @ rho @ projectors[j]) for i in range(2) for j in range(2) if i != j)


def spinor(phi: float, chi: float, eta: float) -> jax.Array:
    return jnp.asarray(
        [
            jnp.exp(1j * (phi + chi)) * math.cos(eta),
            jnp.exp(1j * (phi - chi)) * math.sin(eta),
        ],
        dtype=jnp.complex128,
    )


def loop_spinor(loop: str, u: float, *, sheet: str) -> jax.Array:
    phi = PHI0
    chi = CHI0 if sheet == "L" else -CHI0
    if loop == "inner":
        phi = phi + u
    elif loop == "outer":
        phi = phi - math.cos(2.0 * ETA0) * u
        chi = chi + u
    else:
        raise ValueError(loop)
    psi = spinor(phi, chi, ETA0)
    return psi / jnp.linalg.norm(psi)


def density(psi: jax.Array) -> jax.Array:
    return jnp.outer(psi, jnp.conjugate(psi))


PLACEMENTS = [
    (1, "Se / Funnel / inner", "L", "Funnel", "inner", "system_v5/READ ONLY Reference Docs/terrain math.md:122"),
    (2, "Se / Funnel / outer", "L", "Funnel", "outer", "system_v5/READ ONLY Reference Docs/terrain math.md:123"),
    (3, "Ne / Vortex / inner", "L", "Vortex", "inner", "system_v5/READ ONLY Reference Docs/terrain math.md:124"),
    (4, "Ne / Vortex / outer", "L", "Vortex", "outer", "system_v5/READ ONLY Reference Docs/terrain math.md:125"),
    (5, "Ni / Pit / inner", "L", "Pit", "inner", "system_v5/READ ONLY Reference Docs/terrain math.md:126"),
    (6, "Ni / Pit / outer", "L", "Pit", "outer", "system_v5/READ ONLY Reference Docs/terrain math.md:127"),
    (7, "Si / Hill / inner", "L", "Hill", "inner", "system_v5/READ ONLY Reference Docs/terrain math.md:128"),
    (8, "Si / Hill / outer", "L", "Hill", "outer", "system_v5/READ ONLY Reference Docs/terrain math.md:129"),
    (9, "Se / Cannon / inner", "R", "Cannon", "inner", "system_v5/READ ONLY Reference Docs/terrain math.md:130"),
    (10, "Se / Cannon / outer", "R", "Cannon", "outer", "system_v5/READ ONLY Reference Docs/terrain math.md:131"),
    (11, "Ne / Spiral / inner", "R", "Spiral", "inner", "system_v5/READ ONLY Reference Docs/terrain math.md:132"),
    (12, "Ne / Spiral / outer", "R", "Spiral", "outer", "system_v5/READ ONLY Reference Docs/terrain math.md:133"),
    (13, "Ni / Source / inner", "R", "Source", "inner", "system_v5/READ ONLY Reference Docs/terrain math.md:134"),
    (14, "Ni / Source / outer", "R", "Source", "outer", "system_v5/READ ONLY Reference Docs/terrain math.md:135"),
    (15, "Si / Citadel / inner", "R", "Citadel", "inner", "system_v5/READ ONLY Reference Docs/terrain math.md:136"),
    (16, "Si / Citadel / outer", "R", "Citadel", "outer", "system_v5/READ ONLY Reference Docs/terrain math.md:137"),
]


def placement_table(channels: dict[str, jax.Array]) -> list[dict[str, Any]]:
    rows = []
    sample_us = [0.0, math.pi / 2.0, math.pi, 3.0 * math.pi / 2.0, 2.0 * math.pi]
    for idx, label, sheet, terrain, loop, line_ref in PLACEMENTS:
        rho_start = density(loop_spinor(loop, 0.0, sheet=sheet))
        loop_deltas = [trace_distance(density(loop_spinor(loop, u, sheet=sheet)), rho_start) for u in sample_us]
        channel = channels[f"{terrain}:pure_hamiltonian" if terrain in {"Vortex", "Spiral"} else terrain]
        rho_end = apply_channel(channel, rho_start)
        row = {
            "index": idx,
            "label": label,
            "sheet": sheet,
            "terrain": terrain,
            "loop": loop,
            "source_line_ref": line_ref,
            "placement": f"(X_{terrain},{'gamma_in' if loop == 'inner' else 'gamma_out'})",
            "density_delta": trace_distance(rho_end, rho_start),
            "loop_coordinate_density_delta_max": max(loop_deltas),
            "loop_class": "fiber_density_stationary" if loop == "inner" else "base_density_visible",
        }
        if terrain in {"Vortex", "Spiral"}:
            weak = channels[f"{terrain}:weak_dissipator"]
            row["density_delta_weak_dissipator"] = trace_distance(apply_channel(weak, rho_start), rho_start)
        rows.append(row)
    return rows


def scaled_superop_entries(channel_or_generator: jax.Array) -> list[tuple[int, int]]:
    arr = jax.device_get(channel_or_generator).reshape((-1,))
    out = []
    for value in arr:
        out.append((int(round(float(jnp.real(value)) * SMT_SCALE)), int(round(float(jnp.imag(value)) * SMT_SCALE))))
    return out


def z3_bind_entries(solver: z3.Solver, prefix: str, values: list[tuple[int, int]]) -> tuple[list[z3.ArithRef], list[z3.ArithRef]]:
    reals = []
    imags = []
    for idx, (real_value, imag_value) in enumerate(values):
        rv = z3.Int(f"{prefix}_re_{idx}")
        iv = z3.Int(f"{prefix}_im_{idx}")
        solver.add(rv == z3.IntVal(real_value))
        solver.add(iv == z3.IntVal(imag_value))
        reals.append(rv)
        imags.append(iv)
    return reals, imags


def z3_smt_suite(pit: jax.Array, source: jax.Array, swapped: jax.Array) -> dict[str, Any]:
    pit_values = scaled_superop_entries(pit)
    source_values = scaled_superop_entries(source)
    swapped_values = scaled_superop_entries(swapped)

    forced = z3.Solver()
    pit_re, pit_im = z3_bind_entries(forced, "pit", pit_values)
    source_re, source_im = z3_bind_entries(forced, "source", source_values)
    for a, b in zip(pit_re + pit_im, source_re + source_im):
        forced.add(a == b)
    forced_status = str(forced.check())

    eq = z3.Solver()
    sw_re, sw_im = z3_bind_entries(eq, "swapped", swapped_values)
    src_re, src_im = z3_bind_entries(eq, "source_eq", source_values)
    for a, b in zip(sw_re + sw_im, src_re + src_im):
        eq.add(a == b)
    eq_status = str(eq.check())

    neq = z3.Solver()
    sw2_re, sw2_im = z3_bind_entries(neq, "swapped_neq", swapped_values)
    src2_re, src2_im = z3_bind_entries(neq, "source_neq", source_values)
    neq.add(z3.Or([a != b for a, b in zip(sw2_re + sw2_im, src2_re + src2_im)]))
    neq_status = str(neq.check())
    return {
        "solver": "z3",
        "verdict": forced_status,
        "claim": "Pit and Source full generator entries are not equal under entry-binding SMT; forced equality is UNSAT.",
        "proof_kind": "entry_binding_smt",
        "symbolic_derivation_in_solver": False,
        "entry_binding_honesty_label": "ENTRY-BINDING SMT: generator formulas are constructed outside the solver; the solver binds scaled generator entries and checks equality/inequality.",
        "sigma_swapped_pit_source_convention_equality": eq_status,
        "sigma_swapped_pit_source_convention_inequality": neq_status,
        "binds_generator_entries": len(pit_values),
        "scale": SMT_SCALE,
        "asserted_precomputed_boolean": False,
        "pass": forced_status == "unsat" and eq_status == "sat" and neq_status == "unsat",
    }


def cvc5_int(solver: cvc5.Solver, value: int) -> Any:
    return solver.mkInteger(int(value))


def cvc5_status(result: Any) -> str:
    if result.isSat():
        return "sat"
    if result.isUnsat():
        return "unsat"
    return str(result)


def cvc5_bind_entries(solver: cvc5.Solver, prefix: str, values: list[tuple[int, int]]) -> tuple[list[Any], list[Any]]:
    integer = solver.getIntegerSort()
    reals = []
    imags = []
    for idx, (real_value, imag_value) in enumerate(values):
        rv = solver.mkConst(integer, f"{prefix}_re_{idx}")
        iv = solver.mkConst(integer, f"{prefix}_im_{idx}")
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, rv, cvc5_int(solver, real_value)))
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, iv, cvc5_int(solver, imag_value)))
        reals.append(rv)
        imags.append(iv)
    return reals, imags


def cvc5_or(solver: cvc5.Solver, terms: list[Any]) -> Any:
    if len(terms) == 1:
        return terms[0]
    return solver.mkTerm(Kind.OR, *terms)


def cvc5_smt_suite(pit: jax.Array, source: jax.Array, swapped: jax.Array) -> dict[str, Any]:
    pit_values = scaled_superop_entries(pit)
    source_values = scaled_superop_entries(source)
    swapped_values = scaled_superop_entries(swapped)

    forced = cvc5.Solver()
    forced.setLogic("QF_NIA")
    pit_re, pit_im = cvc5_bind_entries(forced, "pit", pit_values)
    source_re, source_im = cvc5_bind_entries(forced, "source", source_values)
    for a, b in zip(pit_re + pit_im, source_re + source_im):
        forced.assertFormula(forced.mkTerm(Kind.EQUAL, a, b))
    forced_status = cvc5_status(forced.checkSat())

    eq = cvc5.Solver()
    eq.setLogic("QF_NIA")
    sw_re, sw_im = cvc5_bind_entries(eq, "swapped", swapped_values)
    src_re, src_im = cvc5_bind_entries(eq, "source_eq", source_values)
    for a, b in zip(sw_re + sw_im, src_re + src_im):
        eq.assertFormula(eq.mkTerm(Kind.EQUAL, a, b))
    eq_status = cvc5_status(eq.checkSat())

    neq = cvc5.Solver()
    neq.setLogic("QF_NIA")
    sw2_re, sw2_im = cvc5_bind_entries(neq, "swapped_neq", swapped_values)
    src2_re, src2_im = cvc5_bind_entries(neq, "source_neq", source_values)
    neq.assertFormula(cvc5_or(neq, [neq.mkTerm(Kind.NOT, neq.mkTerm(Kind.EQUAL, a, b)) for a, b in zip(sw2_re + sw2_im, src2_re + src2_im)]))
    neq_status = cvc5_status(neq.checkSat())
    return {
        "solver": "cvc5",
        "verdict": forced_status,
        "claim": "Pit and Source full generator entries are not equal under entry-binding SMT; forced equality is UNSAT.",
        "proof_kind": "entry_binding_smt",
        "symbolic_derivation_in_solver": False,
        "entry_binding_honesty_label": "ENTRY-BINDING SMT: generator formulas are constructed outside the solver; the solver binds scaled generator entries and checks equality/inequality.",
        "sigma_swapped_pit_source_convention_equality": eq_status,
        "sigma_swapped_pit_source_convention_inequality": neq_status,
        "binds_generator_entries": len(pit_values),
        "scale": SMT_SCALE,
        "asserted_precomputed_boolean": False,
        "pass": forced_status == "unsat" and eq_status == "sat" and neq_status == "unsat",
    }


def build_result() -> dict[str, Any]:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    channels = {
        "Funnel": channel_from_generator(generator_fn("Funnel")),
        "Cannon": channel_from_generator(generator_fn("Cannon")),
        "Vortex:pure_hamiltonian": channel_from_generator(generator_fn("Vortex", ne_variant="pure_hamiltonian")),
        "Vortex:weak_dissipator": channel_from_generator(generator_fn("Vortex", ne_variant="weak_dissipator")),
        "Spiral:pure_hamiltonian": channel_from_generator(generator_fn("Spiral", ne_variant="pure_hamiltonian")),
        "Spiral:weak_dissipator": channel_from_generator(generator_fn("Spiral", ne_variant="weak_dissipator")),
        "Pit": channel_from_generator(generator_fn("Pit")),
        "Source": channel_from_generator(generator_fn("Source")),
        "Hill": channel_from_generator(generator_fn("Hill")),
        "Citadel": channel_from_generator(generator_fn("Citadel")),
    }
    erased_channels = {
        "Cannon": channel_from_generator(generator_fn("Cannon", erased_weyl=True)),
        "Spiral:pure_hamiltonian": channel_from_generator(generator_fn("Spiral", ne_variant="pure_hamiltonian", erased_weyl=True)),
        "Spiral:weak_dissipator": channel_from_generator(generator_fn("Spiral", ne_variant="weak_dissipator", erased_weyl=True)),
        "Citadel:commuting_frame": channel_from_generator(generator_fn("Citadel", commuting_si_frame=True)),
        "Pit:sigma_only_swap": channel_from_generator(generator_fn("Pit", sigma_only_swap=True)),
        "Pit:sigma_swap_source_side": channel_from_generator(generator_fn("Pit", sigma_swap_source_side=True)),
    }

    certs = {}
    for name, channel in channels.items():
        certs[name] = {
            "cptp": channel_certificate(channel),
            "state_deltas": state_deltas(channel),
        }
    unitality = unitality_column(channels)
    for name, row in unitality["rows"].items():
        certs[name]["unitality"] = row
    source_lock = source_lock_freshness()
    axis0 = axis0_response()
    entropy = entropy_columns(channels)

    pit_gen = generator_fn("Pit")
    source_gen = generator_fn("Source")
    pit_swapped_source_gen = generator_fn("Pit", sigma_swap_source_side=True)
    z3_proof = z3_smt_suite(superoperator(pit_gen), superoperator(source_gen), superoperator(pit_swapped_source_gen))
    cvc5_proof = cvc5_smt_suite(superoperator(pit_gen), superoperator(source_gen), superoperator(pit_swapped_source_gen))

    pit_drift_z = real_float(jnp.trace(pit_gen(SENSITIVE_RHO) @ SZ))
    source_drift_z = real_float(jnp.trace(source_gen(SENSITIVE_RHO) @ SZ))
    pit_sigma_only_drift_z = real_float(jnp.trace(generator_fn("Pit", sigma_only_swap=True)(SENSITIVE_RHO) @ SZ))

    hill_sensitive_before = projector_coherence(SENSITIVE_RHO, [PZ_PLUS, PZ_MINUS])
    hill_sensitive_after = projector_coherence(apply_channel(channels["Hill"], SENSITIVE_RHO), [PZ_PLUS, PZ_MINUS])
    citadel_sensitive_before = projector_coherence(SENSITIVE_RHO, [PX_PLUS, PX_MINUS])
    citadel_sensitive_after = projector_coherence(apply_channel(channels["Citadel"], SENSITIVE_RHO), [PX_PLUS, PX_MINUS])

    fixed_point_checks = {
        "basis_label_policy": {
            "terrain_label_zero_projector_matrix": to_builtin(TERRAIN_KET0),
            "terrain_label_one_projector_matrix": to_builtin(TERRAIN_KET1),
            "note": "Labels follow the locked sigma convention: D[sigma_-] fixes the second matrix-basis projector.",
        },
        "Pit": {
            "source_jump": "sigma_-",
            "dissipator_target": "terrain |0><0|",
            "dissipator_target_residual": fro_norm(GAMMA_NI * dissipator(SIGMA_MINUS, TERRAIN_KET0)),
            "full_generator_target_residual": fro_norm(pit_gen(TERRAIN_KET0)),
            "full_generator_hamiltonian_tilt_recorded": fro_norm(pit_gen(TERRAIN_KET0)) > TOL,
            "sensitive_state_rz_drift": pit_drift_z,
            "attractor_side_pass": pit_drift_z < -1.0e-4,
        },
        "Source": {
            "source_jump": "sigma_+",
            "dissipator_target": "terrain |1><1|",
            "dissipator_target_residual": fro_norm(GAMMA_NI * dissipator(SIGMA_PLUS, TERRAIN_KET1)),
            "full_generator_target_residual": fro_norm(source_gen(TERRAIN_KET1)),
            "full_generator_hamiltonian_tilt_recorded": fro_norm(source_gen(TERRAIN_KET1)) > TOL,
            "sensitive_state_rz_drift": source_drift_z,
            "attractor_side_pass": source_drift_z > 1.0e-4,
        },
        "Hill": {
            "frame": "z-axis",
            "commutator_K_P_plus_norm": fro_norm((OMEGA_SI * SZ) @ PZ_PLUS - PZ_PLUS @ (OMEGA_SI * SZ)),
            "commutator_K_P_minus_norm": fro_norm((OMEGA_SI * SZ) @ PZ_MINUS - PZ_MINUS @ (OMEGA_SI * SZ)),
            "pure_projector_control_delta": trace_distance(apply_channel(channels["Hill"], PZ_PLUS), PZ_PLUS),
            "sensitive_coherence_before": hill_sensitive_before,
            "sensitive_coherence_after": hill_sensitive_after,
            "sensitive_state_control_pass": hill_sensitive_after < hill_sensitive_before - 1.0e-4,
        },
        "Citadel": {
            "frame": "x-axis",
            "commutator_K_P_plus_norm": fro_norm((OMEGA_SI * SX) @ PX_PLUS - PX_PLUS @ (OMEGA_SI * SX)),
            "commutator_K_P_minus_norm": fro_norm((OMEGA_SI * SX) @ PX_MINUS - PX_MINUS @ (OMEGA_SI * SX)),
            "pure_projector_control_delta": trace_distance(apply_channel(channels["Citadel"], PX_PLUS), PX_PLUS),
            "sensitive_coherence_before": citadel_sensitive_before,
            "sensitive_coherence_after": citadel_sensitive_after,
            "sensitive_state_control_pass": citadel_sensitive_after < citadel_sensitive_before - 1.0e-4,
        },
    }

    n0 = jnp.asarray([1.0, 1.0, 1.0], dtype=jnp.float64) / jnp.sqrt(3.0)
    rv0 = bloch(RHO_0)
    vort_pure = apply_channel(channels["Vortex:pure_hamiltonian"], RHO_0)
    spir_pure = apply_channel(channels["Spiral:pure_hamiltonian"], RHO_0)
    vort_weak = apply_channel(channels["Vortex:weak_dissipator"], RHO_0)
    spir_weak = apply_channel(channels["Spiral:weak_dissipator"], RHO_0)
    rotation_vortex_pure = real_float(jnp.dot(n0, jnp.cross(rv0, bloch(vort_pure))))
    rotation_spiral_pure = real_float(jnp.dot(n0, jnp.cross(rv0, bloch(spir_pure))))
    rotation_vortex_weak = real_float(jnp.dot(n0, jnp.cross(rv0, bloch(vort_weak))))
    rotation_spiral_weak = real_float(jnp.dot(n0, jnp.cross(rv0, bloch(spir_weak))))

    pair_separation = {
        "Funnel_vs_Cannon": {
            "source_table_claim": "opposite Weyl sign plus pinned coefficient-distinct dissipator family",
            "trace_distance_rho_0": trace_distance(apply_channel(channels["Funnel"], RHO_0), apply_channel(channels["Cannon"], RHO_0)),
            "trace_distance_rho_1": trace_distance(apply_channel(channels["Funnel"], RHO_1), apply_channel(channels["Cannon"], RHO_1)),
            "erased_weyl_trace_distance_rho_0": trace_distance(apply_channel(channels["Funnel"], RHO_0), apply_channel(erased_channels["Cannon"], RHO_0)),
        },
        "Vortex_vs_Spiral": {
            "pure_trace_distance_rho_0": trace_distance(vort_pure, spir_pure),
            "weak_trace_distance_rho_0": trace_distance(vort_weak, spir_weak),
            "vortex_rotation_direction_pure": rotation_vortex_pure,
            "spiral_rotation_direction_pure": rotation_spiral_pure,
            "vortex_rotation_direction_weak": rotation_vortex_weak,
            "spiral_rotation_direction_weak": rotation_spiral_weak,
            "erased_weyl_pure_trace_distance_rho_0": trace_distance(vort_pure, apply_channel(erased_channels["Spiral:pure_hamiltonian"], RHO_0)),
            "erased_weyl_weak_trace_distance_rho_0": trace_distance(vort_weak, apply_channel(erased_channels["Spiral:weak_dissipator"], RHO_0)),
        },
        "Pit_vs_Source": {
            "pit_sensitive_rz_drift": pit_drift_z,
            "source_sensitive_rz_drift": source_drift_z,
            "opposite_sink_source_directions": pit_drift_z < -1.0e-4 and source_drift_z > 1.0e-4,
            "finite_channel_trace_distance_rho_0": trace_distance(apply_channel(channels["Pit"], RHO_0), apply_channel(channels["Source"], RHO_0)),
        },
        "Hill_vs_Citadel": {
            "projector_overlap_matrix_z_vs_x": [
                [real_float(jnp.trace(PZ_PLUS @ PX_PLUS)), real_float(jnp.trace(PZ_PLUS @ PX_MINUS))],
                [real_float(jnp.trace(PZ_MINUS @ PX_PLUS)), real_float(jnp.trace(PZ_MINUS @ PX_MINUS))],
            ],
            "post_channel_trace_distance_rho_0": trace_distance(apply_channel(channels["Hill"], RHO_0), apply_channel(channels["Citadel"], RHO_0)),
            "commuting_frame_control_trace_distance_rho_0": trace_distance(apply_channel(channels["Hill"], RHO_0), apply_channel(erased_channels["Citadel:commuting_frame"], RHO_0)),
            "distinct_strata_pass": trace_distance(apply_channel(channels["Hill"], RHO_0), apply_channel(channels["Citadel"], RHO_0)) > 1.0e-4,
        },
    }

    placements = placement_table(channels)
    negative_controls = {
        "erased_weyl_sign_collapses_Funnel_Cannon": pair_separation["Funnel_vs_Cannon"]["erased_weyl_trace_distance_rho_0"] <= 1.0e-7,
        "erased_weyl_sign_collapses_Vortex_Spiral_pure": pair_separation["Vortex_vs_Spiral"]["erased_weyl_pure_trace_distance_rho_0"] <= 1.0e-7,
        "erased_weyl_sign_collapses_Vortex_Spiral_weak": pair_separation["Vortex_vs_Spiral"]["erased_weyl_weak_trace_distance_rho_0"] <= 1.0e-7,
        "commuting_frame_Si_control_collapses_Hill_Citadel": pair_separation["Hill_vs_Citadel"]["commuting_frame_control_trace_distance_rho_0"] <= 1.0e-7,
        "sigma_only_swap_gives_source_jump_direction": pit_sigma_only_drift_z > 1.0e-4,
        "sigma_only_swap_full_generator_still_differs_due_H_sign": trace_distance(apply_channel(erased_channels["Pit:sigma_only_swap"], RHO_0), apply_channel(channels["Source"], RHO_0)) > 1.0e-4,
        "sigma_swapped_pit_source_convention_equals_source": trace_distance(apply_channel(erased_channels["Pit:sigma_swap_source_side"], RHO_0), apply_channel(channels["Source"], RHO_0)) <= 1.0e-7,
    }

    cptp_pass = all(certs[name]["cptp"]["pass"] for name in certs)
    fixed_pass = (
        fixed_point_checks["Pit"]["attractor_side_pass"]
        and fixed_point_checks["Source"]["attractor_side_pass"]
        and fixed_point_checks["Hill"]["sensitive_state_control_pass"]
        and fixed_point_checks["Citadel"]["sensitive_state_control_pass"]
        and fixed_point_checks["Hill"]["commutator_K_P_plus_norm"] <= TOL
        and fixed_point_checks["Citadel"]["commutator_K_P_plus_norm"] <= TOL
    )
    pair_pass = (
        pair_separation["Funnel_vs_Cannon"]["trace_distance_rho_0"] > 1.0e-4
        and pair_separation["Vortex_vs_Spiral"]["pure_trace_distance_rho_0"] > 1.0e-4
        and pair_separation["Vortex_vs_Spiral"]["weak_trace_distance_rho_0"] > 1.0e-4
        and pair_separation["Vortex_vs_Spiral"]["vortex_rotation_direction_pure"] * pair_separation["Vortex_vs_Spiral"]["spiral_rotation_direction_pure"] < 0.0
        and pair_separation["Pit_vs_Source"]["opposite_sink_source_directions"]
        and pair_separation["Hill_vs_Citadel"]["distinct_strata_pass"]
    )
    placement_pass = (
        len(placements) == 16
        and sum(1 for row in placements if row["loop"] == "inner" and row["loop_coordinate_density_delta_max"] <= TOL) == 8
        and sum(1 for row in placements if row["loop"] == "outer" and row["loop_coordinate_density_delta_max"] > 1.0e-4) == 8
    )
    negative_pass = all(bool(value) for value in negative_controls.values())
    smt_pass = z3_proof["pass"] and cvc5_proof["pass"] and z3_proof["verdict"] == cvc5_proof["verdict"]
    state_pass = density_valid(RHO_0)["pass"] and density_valid(RHO_1)["pass"] and density_valid(SENSITIVE_RHO)["pass"]
    source_lock_pass = source_lock["all_fresh"]
    unitality_pass = unitality["pass"]
    axis0_pass = axis0["pass"]
    all_pass = bool(
        cptp_pass
        and fixed_pass
        and pair_pass
        and placement_pass
        and negative_pass
        and smt_pass
        and state_pass
        and source_lock_pass
        and unitality_pass
        and axis0_pass
    )

    choi_min = min(certs[name]["cptp"]["choi_min_eigenvalue"] for name in certs)
    tp_max = max(certs[name]["cptp"]["tp_residual"] for name in certs)
    shared_scalars = {
        "choi_min_eigenvalue_min": choi_min,
        "tp_residual_max": tp_max,
        "pair_funnel_cannon_trace_distance_rho_0": pair_separation["Funnel_vs_Cannon"]["trace_distance_rho_0"],
        "pair_funnel_cannon_erased_trace_distance_rho_0": pair_separation["Funnel_vs_Cannon"]["erased_weyl_trace_distance_rho_0"],
        "pair_vortex_spiral_pure_trace_distance_rho_0": pair_separation["Vortex_vs_Spiral"]["pure_trace_distance_rho_0"],
        "pair_vortex_spiral_weak_trace_distance_rho_0": pair_separation["Vortex_vs_Spiral"]["weak_trace_distance_rho_0"],
        "pair_vortex_spiral_erased_pure_trace_distance_rho_0": pair_separation["Vortex_vs_Spiral"]["erased_weyl_pure_trace_distance_rho_0"],
        "pair_pit_rz_drift": pit_drift_z,
        "pair_source_rz_drift": source_drift_z,
        "pair_hill_citadel_post_channel_trace_distance_rho_0": pair_separation["Hill_vs_Citadel"]["post_channel_trace_distance_rho_0"],
        "placement_count": float(len(placements)),
        "fiber_stationary_count": float(sum(1 for row in placements if row["loop"] == "inner" and row["loop_coordinate_density_delta_max"] <= TOL)),
        "base_visible_count": float(sum(1 for row in placements if row["loop"] == "outer" and row["loop_coordinate_density_delta_max"] > 1.0e-4)),
        "smt_pit_source_forced_equal_unsat": 1.0 if z3_proof["verdict"] == cvc5_proof["verdict"] == "unsat" else 0.0,
        "smt_sigma_swapped_valid": 1.0 if z3_proof["sigma_swapped_pit_source_convention_inequality"] == cvc5_proof["sigma_swapped_pit_source_convention_inequality"] == "unsat" else 0.0,
        "source_lock_fresh": 1.0 if source_lock_pass else 0.0,
        "unitality_max_non_ni_E_I_minus_I_fro_norm": unitality["max_non_ni_E_I_minus_I_fro_norm"],
        "unitality_min_ni_E_I_minus_I_fro_norm": unitality["min_ni_E_I_minus_I_fro_norm"],
        "axis0_pr_sign_Ne": 1.0 if axis0["doctrine_family_sign_table"]["pauli_participation_ratio"]["Ne"] == "+" else -1.0,
        "axis0_pr_sign_Ni": 1.0 if axis0["doctrine_family_sign_table"]["pauli_participation_ratio"]["Ni"] == "+" else -1.0,
        "axis0_pr_sign_Se": 1.0 if axis0["doctrine_family_sign_table"]["pauli_participation_ratio"]["Se"] == "+" else -1.0,
        "axis0_pr_sign_Si": 1.0 if axis0["doctrine_family_sign_table"]["pauli_participation_ratio"]["Si"] == "+" else -1.0,
    }

    return {
        "schema": "codex_ratchet.engine_leg_result.v1",
        "sim_id": SIM_ID,
        "object_id": OBJECT_ID,
        "engine": "jax",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result": READS_PEER_RESULT,
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH),
        "source_sha256": sha256_file(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "packages_used": ["jax", "jax.numpy", "jax.scipy.linalg", "z3", "cvc5", "json", "hashlib", "pathlib"],
        "aligned_packages_load_bearing": ["jax.scipy.linalg", "z3", "cvc5"],
        "claim_path_tools": ["jax.scipy.linalg", "z3", "cvc5"],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "source_line_refs": SOURCE_LINE_REFS,
        "source_lock_freshness": source_lock,
        "pin_spec": PIN_SPEC,
        "pauli_expansion_families": {
            "Se_Funnel_L": to_builtin(SE_FUNNEL_COEFFS),
            "Se_Cannon_R": to_builtin(SE_CANNON_COEFFS),
            "Ne_Vortex_L": to_builtin(NE_VORTEX_COEFFS),
            "Ne_Spiral_R": to_builtin(NE_SPIRAL_COEFFS),
            "family_note": "Coefficient rows are distinct but phase/sign gauge-equivalent within each L/R pair so Weyl erasure can be a decisive control.",
        },
        "pauli_expansion_family_pin_metadata": PAULI_EXPANSION_FAMILY_PIN_METADATA,
        "states": {
            "rho_0": to_builtin(RHO_0),
            "rho_1": to_builtin(RHO_1),
            "sensitive_rho": to_builtin(SENSITIVE_RHO),
            "rho_0_valid": density_valid(RHO_0),
            "rho_1_valid": density_valid(RHO_1),
            "sensitive_rho_valid": density_valid(SENSITIVE_RHO),
        },
        "terrain_certificates": certs,
        "fixed_point_and_strata_checks": fixed_point_checks,
        "unitality_column": unitality,
        "axis0_response": axis0,
        "entropy_columns": entropy,
        "pair_separation_table": pair_separation,
        "placements_16": placements,
        "negative_controls": negative_controls,
        "smt": {"z3": z3_proof, "cvc5": cvc5_proof, "agreement": z3_proof["verdict"] == cvc5_proof["verdict"]},
        "sigma_swap_control_detail": {
            "pit_sigma_only_swap_sensitive_rz_drift": pit_sigma_only_drift_z,
            "source_sensitive_rz_drift": source_drift_z,
            "interpretation": "sigma-only Pit swap matches the Source jump direction; full equality also requires the R-sheet Hamiltonian sign, which is checked separately.",
        },
        "crossover_proofs": {
            "z3": {"ran": True, "load_bearing": True, "verdict": z3_proof["verdict"], **z3_proof},
            "cvc5": {"ran": True, "load_bearing": True, "verdict": cvc5_proof["verdict"], **cvc5_proof},
        },
        "shared_scalars": shared_scalars,
        "controls": {
            "state_pass": state_pass,
            "cptp_pass": cptp_pass,
            "fixed_pass": fixed_pass,
            "pair_pass": pair_pass,
            "placement_pass": placement_pass,
            "negative_pass": negative_pass,
            "smt_pass": smt_pass,
            "source_lock_pass": source_lock_pass,
            "unitality_pass": unitality_pass,
            "axis0_response_computed": axis0_pass,
            "classification_ceiling_held": CLASSIFICATION == "scratch_diagnostic" and PROMOTION_ALLOWED is False and FORMAL_ADMISSION_ALLOWED is False,
        },
        "all_pass": all_pass,
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.write_text(json.dumps(to_builtin(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "result_path": str(RESULT_PATH),
                "all_pass": result["all_pass"],
                "pair_funnel_cannon": result["shared_scalars"]["pair_funnel_cannon_trace_distance_rho_0"],
                "placements": result["shared_scalars"]["placement_count"],
                "z3": result["smt"]["z3"]["verdict"],
                "cvc5": result["smt"]["cvc5"]["verdict"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
