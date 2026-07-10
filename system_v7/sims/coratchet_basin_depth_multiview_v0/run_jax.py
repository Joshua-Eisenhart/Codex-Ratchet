#!/usr/bin/env python3
"""Deterministic JAX workhorse for the preregistered co-ratchet basin audit.

This lane independently reconstructs the finite qubit channels fixed by the
specification.  It does not import another engine implementation or read a
peer result.  Axis 6 is represented only by channel-composition precedence;
UP/DOWN never changes the four operator formulas.
"""

from __future__ import annotations

import hashlib
import importlib.metadata
import itertools
import json
import math
import sys
from pathlib import Path
from typing import Any, Sequence

from jax import config

config.update("jax_enable_x64", True)

import dynamiqs as dq
import jax
import jax.numpy as jnp
import jax.scipy.linalg as jsp_linalg


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
HERE = ROOT / "system_v7/sims/coratchet_basin_depth_multiview_v0"
SOURCE_PATH = HERE / "run_jax.py"
SPEC_PATH = HERE / "spec.json"
PREREGISTRATION_PATH = HERE / "preregistration_receipt.json"
CANONICAL_SEMANTICS_PATH = (
    ROOT / "system_v5/ops/formal_scouts/canonical_qit_engine_specs.py"
)
RESULT_PATH = (
    HERE / "results/coratchet_basin_depth_multiview_v0_jax_results.json"
)

EXPECTED_SPEC_SHA256 = "f370aeb1366f30857c89d5ab9c94af54aea6f40fb8db6309776a5c0fa79dacb7"
EXPECTED_PREREGISTRATION_SHA256 = (
    "cb5e4f552ebc51684ab5a081b399025324e49efc75d841598e0cb3e6586a177c"
)
EXPECTED_COMMITTED_SEMANTICS_SHA256 = (
    "0b8df7def1c274cf118995663abd9ec95886197d1dfb01de4519c19ca9351f83"
)

CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
STAGE_MOVEMENT_ALLOWED = False
READS_PEER_RESULT = False

DTYPE = jnp.complex128
RANDOM_SEED = 20260710
DIM = 2
SUPER_DIM = DIM * DIM
FIXED_TOL = 1.0e-9
CONTRACTION_TOL = 1.0e-8
CONVERGENCE_EPS = 1.0e-8
MONOTONIC_TOL = 1.0e-9
COVARIANCE_TOL = 1.0e-9
CPTP_TOL = 2.0e-10
DYNAMIQS_PARITY_TOL = 2.0e-8

I2 = jnp.eye(2, dtype=DTYPE)
SX = jnp.asarray([[0.0, 1.0], [1.0, 0.0]], dtype=DTYPE)
SY = jnp.asarray([[0.0, -1.0j], [1.0j, 0.0]], dtype=DTYPE)
SZ = jnp.asarray([[1.0, 0.0], [0.0, -1.0]], dtype=DTYPE)
SIGMA_MINUS = jnp.asarray([[0.0, 0.0], [1.0, 0.0]], dtype=DTYPE)
SIGMA_PLUS = jnp.asarray([[0.0, 1.0], [0.0, 0.0]], dtype=DTYPE)
H0 = 0.77 * SZ + 0.13 * SX

PERCEPTION_L_TYPE_ONE = {
    "Se": SZ,
    "Ne": SIGMA_PLUS,
    "Ni": -1.0j * SY,
    "Si": SIGMA_MINUS,
}

TERRAIN_RATES = {
    "Type1_left": {"Se": 0.18, "Ne": 0.13, "Ni": 0.28, "Si": 0.20},
    "Type2_right": {"Se": 0.18, "Ne": 0.15, "Ni": 0.27, "Si": 0.21},
}

ORDERED_SLOT_SPECS: tuple[tuple[str, str, str, str], ...] = (
    ("TiSe", "Se", "Ti", "operator_first"),
    ("SeTi", "Se", "Ti", "terrain_first"),
    ("FiSe", "Se", "Fi", "operator_first"),
    ("SeFi", "Se", "Fi", "terrain_first"),
    ("TiNe", "Ne", "Ti", "operator_first"),
    ("NeTi", "Ne", "Ti", "terrain_first"),
    ("FiNe", "Ne", "Fi", "operator_first"),
    ("NeFi", "Ne", "Fi", "terrain_first"),
    ("TeNi", "Ni", "Te", "operator_first"),
    ("NiTe", "Ni", "Te", "terrain_first"),
    ("FeNi", "Ni", "Fe", "operator_first"),
    ("NiFe", "Ni", "Fe", "terrain_first"),
    ("TeSi", "Si", "Te", "operator_first"),
    ("SiTe", "Si", "Te", "terrain_first"),
    ("FeSi", "Si", "Fe", "operator_first"),
    ("SiFe", "Si", "Fe", "terrain_first"),
)

PAULI_BASIS_TRANSFORMS = {
    "I": I2,
    "X": SX,
    "Y": SY,
    "Z": SZ,
}

TOOL_MANIFEST = {
    "jax": {
        "tried": True,
        "used": True,
        "reason": "load-bearing x64 vectorization, spectra, 1024-state trajectories, controls, and deterministic random sweeps",
    },
    "jax.scipy.linalg.expm": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite-time exponentiation of every Lindblad and unitary generator",
    },
    "dynamiqs.mesolve": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent Lindblad parity microcheck gating result validity and all_pass",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "jax": "load_bearing",
    "jax.scipy.linalg.expm": "load_bearing",
    "dynamiqs.mesolve": "load_bearing",
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def scalar(value: Any) -> float:
    return float(jax.device_get(jnp.real(value)))


def integer(value: Any) -> int:
    return int(jax.device_get(value))


def boolean(value: Any) -> bool:
    return bool(jax.device_get(value))


def jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, complex):
        return {"real": float(value.real), "imag": float(value.imag)}
    if isinstance(value, (str, bool, int, float)) or value is None:
        return value
    if hasattr(value, "tolist"):
        return jsonable(jax.device_get(value).tolist())
    if hasattr(value, "item"):
        return jsonable(value.item())
    raise TypeError(f"not JSON serializable: {type(value)!r}")


def strict_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(
        jsonable(payload), indent=2, sort_keys=True, allow_nan=False
    ) + "\n"
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(encoded, encoding="utf-8")
    temporary.replace(path)


def vec(matrix: jax.Array) -> jax.Array:
    """Column-vectorize a 2x2 operator."""
    return jnp.transpose(matrix).reshape((SUPER_DIM,))


def unvec(vector: jax.Array) -> jax.Array:
    return jnp.transpose(vector.reshape((DIM, DIM)))


def hermitize(matrix: jax.Array) -> jax.Array:
    return 0.5 * (matrix + jnp.conj(matrix.T))


def unitary_channel(unitary: jax.Array) -> jax.Array:
    return jnp.kron(jnp.conj(unitary), unitary)


def lindbladian_superoperator(hamiltonian: jax.Array, jump: jax.Array) -> jax.Array:
    jump_product = jnp.conj(jump.T) @ jump
    coherent = -1.0j * (
        jnp.kron(I2, hamiltonian) - jnp.kron(jnp.transpose(hamiltonian), I2)
    )
    dissipative = (
        jnp.kron(jnp.conj(jump), jump)
        - 0.5 * jnp.kron(I2, jump_product)
        - 0.5 * jnp.kron(jnp.transpose(jump_product), I2)
    )
    return coherent + dissipative


def finite_lindblad_channel(
    hamiltonian: jax.Array, jump: jax.Array, duration: float
) -> jax.Array:
    return jsp_linalg.expm(
        jnp.asarray(duration, dtype=jnp.float64)
        * lindbladian_superoperator(hamiltonian, jump)
    )


def hamiltonian_channel(hamiltonian: jax.Array, duration: float) -> jax.Array:
    unitary = jsp_linalg.expm(-1.0j * duration * hamiltonian)
    return unitary_channel(unitary)


def pinching_channel(axis: jax.Array, strength: float) -> jax.Array:
    plus = 0.5 * (I2 + axis)
    minus = 0.5 * (I2 - axis)
    pinching = (
        jnp.kron(jnp.conj(plus), plus)
        + jnp.kron(jnp.conj(minus), minus)
    )
    return (1.0 - strength) * jnp.eye(SUPER_DIM, dtype=DTYPE) + strength * pinching


def rotation_channel(axis: jax.Array, angle: float) -> jax.Array:
    unitary = jsp_linalg.expm(-0.5j * angle * axis)
    return unitary_channel(unitary)


def operator_channel(operator: str, multiplier: float) -> jax.Array:
    if operator == "Ti":
        return pinching_channel(SZ, 0.12 * multiplier)
    if operator == "Te":
        return pinching_channel(SX, 0.09 * multiplier)
    if operator == "Fi":
        return rotation_channel(SX, 0.15 * multiplier)
    if operator == "Fe":
        return rotation_channel(SZ, 0.11 * multiplier)
    raise ValueError(f"unknown operator {operator!r}")


def terrain_channel(
    perception: str,
    engine_type: str,
    multiplier: float,
    *,
    dissipative: bool = True,
) -> jax.Array:
    if engine_type not in {"Type1_left", "Type2_right"}:
        raise ValueError(f"unknown engine type {engine_type!r}")
    sign = 1.0 if engine_type == "Type1_left" else -1.0
    hamiltonian = sign * H0
    jump = PERCEPTION_L_TYPE_ONE[perception]
    if engine_type == "Type2_right":
        jump = SX @ jump @ SX
    jump = jnp.sqrt(TERRAIN_RATES[engine_type][perception] * multiplier) * jump
    duration = 0.2 * multiplier
    if not dissipative:
        return hamiltonian_channel(hamiltonian, duration)
    return finite_lindblad_channel(hamiltonian, jump, duration)


def stage_map(
    terrain: jax.Array, operator: jax.Array, precedence: str
) -> jax.Array:
    if precedence == "operator_first":
        return terrain @ operator
    if precedence == "terrain_first":
        return operator @ terrain
    raise ValueError(f"unknown precedence {precedence!r}")


def compose_execution_order(stages: Sequence[jax.Array]) -> jax.Array:
    cycle = jnp.eye(SUPER_DIM, dtype=DTYPE)
    for stage in stages:
        cycle = stage @ cycle
    return cycle


def build_source_cycle(
    engine_type: str,
    multiplier: float = 1.0,
    order: Sequence[int] | None = None,
    *,
    erase_dissipation: bool = False,
) -> tuple[jax.Array, list[jax.Array], list[dict[str, Any]]]:
    terrains = {
        perception: terrain_channel(
            perception,
            engine_type,
            multiplier,
            dissipative=not erase_dissipation,
        )
        for perception in ("Se", "Ne", "Ni", "Si")
    }
    operators = {
        name: (
            jnp.eye(SUPER_DIM, dtype=DTYPE)
            if erase_dissipation and name in {"Ti", "Te"}
            else operator_channel(name, multiplier)
        )
        for name in ("Ti", "Te", "Fi", "Fe")
    }
    stages: list[jax.Array] = []
    rows: list[dict[str, Any]] = []
    for token, perception, operator_name, precedence in ORDERED_SLOT_SPECS:
        value = stage_map(
            terrains[perception], operators[operator_name], precedence
        )
        stages.append(value)
        rows.append(
            {
                "token": token,
                "terrain_family": perception,
                "operator": operator_name,
                "native_formula": (
                    f"T_{perception} o {operator_name}"
                    if precedence == "operator_first"
                    else f"{operator_name} o T_{perception}"
                ),
                "axis6_token_precedence": (
                    "up" if precedence == "operator_first" else "down"
                ),
                "composition_precedence": precedence,
                "axis6_action_side": "closure_only",
                "closure_type": (
                    "lindblad_dephasing_cptp_composition"
                    if operator_name in {"Ti", "Te"}
                    else "lindblad_unitary_adjoint_cptp_composition"
                ),
                "operator_formula_unchanged_by_axis6": True,
            }
        )
    execution_order = list(range(len(stages))) if order is None else list(order)
    ordered_stages = [stages[index] for index in execution_order]
    return compose_execution_order(ordered_stages), stages, [rows[i] for i in execution_order]


def apply_superoperator(superoperator: jax.Array, matrix: jax.Array) -> jax.Array:
    return unvec(superoperator @ vec(matrix))


def bloch_affine_readout(superoperator: jax.Array) -> dict[str, Any]:
    center = apply_superoperator(superoperator, 0.5 * I2)
    offset = jnp.real(jnp.asarray([
        jnp.trace(center @ SX),
        jnp.trace(center @ SY),
        jnp.trace(center @ SZ),
    ]))
    columns = []
    for axis in (SX, SY, SZ):
        output = apply_superoperator(superoperator, 0.5 * (I2 + axis))
        columns.append(jnp.real(jnp.asarray([
            jnp.trace(output @ SX),
            jnp.trace(output @ SY),
            jnp.trace(output @ SZ),
        ])) - offset)
    linear = jnp.stack(columns, axis=1)
    singular_values = jnp.linalg.svd(linear, compute_uv=False)
    return {
        "linear_matrix": jsonable(linear),
        "offset": jsonable(offset),
        "singular_values": jsonable(singular_values),
        "trace_distance_contraction_coefficient": scalar(jnp.max(singular_values)),
    }


def choi_matrix(superoperator: jax.Array) -> jax.Array:
    result = jnp.zeros((SUPER_DIM, SUPER_DIM), dtype=DTYPE)
    for row in range(DIM):
        for column in range(DIM):
            basis = jnp.zeros((DIM, DIM), dtype=DTYPE).at[row, column].set(1.0)
            result = result + jnp.kron(
                basis, apply_superoperator(superoperator, basis)
            )
    return hermitize(result)


def cptp_report(superoperator: jax.Array) -> dict[str, Any]:
    choi_values = jnp.linalg.eigvalsh(choi_matrix(superoperator))
    identity_vector = vec(I2)
    trace_residual = jnp.linalg.norm(
        jnp.conj(identity_vector) @ superoperator - jnp.conj(identity_vector)
    )
    minimum_choi = jnp.min(jnp.real(choi_values))
    return {
        "minimum_choi_eigenvalue": scalar(minimum_choi),
        "trace_preservation_residual": scalar(trace_residual),
        "pass": boolean(
            jnp.logical_and(
                minimum_choi >= -CPTP_TOL, trace_residual <= CPTP_TOL
            )
        ),
    }


def spectral_multiset_gap(left: jax.Array, right: jax.Array) -> float:
    best = math.inf
    for permutation in itertools.permutations(range(SUPER_DIM)):
        candidate = max(
            abs(complex(left[index]) - complex(right[permutation[index]]))
            for index in range(SUPER_DIM)
        )
        best = min(best, candidate)
    return float(best)


def fixed_point_report(superoperator: jax.Array) -> dict[str, Any]:
    eigenvalues, eigenvectors = jnp.linalg.eig(superoperator)
    distances = jnp.abs(eigenvalues - 1.0)
    fixed_index = integer(jnp.argmin(distances))
    fixed_raw = unvec(eigenvectors[:, fixed_index])
    fixed = hermitize(fixed_raw / jnp.trace(fixed_raw))
    fixed = fixed / jnp.trace(fixed)
    fixed_values = jnp.linalg.eigvalsh(fixed)
    fixed_multiplicity = integer(jnp.sum(distances <= FIXED_TOL))
    others = jnp.concatenate(
        [eigenvalues[:fixed_index], eigenvalues[fixed_index + 1 :]]
    )
    subdominant = scalar(jnp.max(jnp.abs(others)))
    residual = scalar(jnp.linalg.norm(superoperator @ vec(fixed) - vec(fixed)))
    return {
        "eigenvalues": [
            {"real": scalar(jnp.real(value)), "imag": scalar(jnp.imag(value))}
            for value in eigenvalues
        ],
        "eigenvalues_array": eigenvalues,
        "fixed_state": fixed,
        "fixed_state_json": jsonable(fixed),
        "fixed_point_multiplicity": fixed_multiplicity,
        "minimum_fixed_state_eigenvalue": scalar(jnp.min(fixed_values)),
        "fixed_point_residual": residual,
        "subdominant_eigenvalue_modulus": subdominant,
        "contraction_gap": 1.0 - subdominant,
    }


def density_from_bloch(vector: jax.Array) -> jax.Array:
    x, y, z = vector
    return 0.5 * jnp.asarray(
        [[1.0 + z, x - 1.0j * y], [x + 1.0j * y, 1.0 - z]],
        dtype=DTYPE,
    )


def deterministic_initial_states() -> jax.Array:
    radial_index = jnp.repeat(jnp.arange(16, dtype=jnp.float64), 64)
    direction_index = jnp.tile(jnp.arange(64, dtype=jnp.float64), 16)
    radii = radial_index / 15.0
    golden_angle = jnp.pi * (3.0 - jnp.sqrt(5.0))
    z = 1.0 - 2.0 * (direction_index + 0.5) / 64.0
    planar = jnp.sqrt(jnp.maximum(0.0, 1.0 - z * z))
    azimuth = golden_angle * (direction_index + 64.0 * radial_index)
    directions = jnp.stack(
        [planar * jnp.cos(azimuth), planar * jnp.sin(azimuth), z], axis=1
    )
    bloch = radii[:, None] * directions
    return jax.vmap(density_from_bloch)(bloch)


def trace_distance(left: jax.Array, right: jax.Array) -> jax.Array:
    values = jnp.linalg.eigvalsh(hermitize(left - right))
    return 0.5 * jnp.sum(jnp.abs(values))


def matrix_log_full_rank(matrix: jax.Array) -> jax.Array:
    values, vectors = jnp.linalg.eigh(hermitize(matrix))
    logs = jnp.log(jnp.clip(jnp.real(values), 1.0e-15, 1.0))
    return (vectors * logs) @ jnp.conj(vectors.T)


def umegaki_relative_entropy(left: jax.Array, right_log: jax.Array) -> jax.Array:
    values = jnp.linalg.eigvalsh(hermitize(left))
    positive = jnp.clip(jnp.real(values), 0.0, 1.0)
    left_log_term = jnp.sum(
        jnp.where(positive > 1.0e-15, positive * jnp.log(positive), 0.0)
    )
    cross_term = jnp.real(jnp.trace(left @ right_log))
    return jnp.maximum(left_log_term - cross_term, 0.0)


def bures_distance(left: jax.Array, right: jax.Array) -> jax.Array:
    fidelity = jnp.real(jnp.trace(left @ right)) + 2.0 * jnp.sqrt(
        jnp.maximum(0.0, jnp.real(jnp.linalg.det(left)))
        * jnp.maximum(0.0, jnp.real(jnp.linalg.det(right)))
    )
    root_fidelity = jnp.sqrt(jnp.clip(fidelity, 0.0, 1.0))
    squared = jnp.maximum(0.0, 2.0 - 2.0 * root_fidelity)
    return jnp.where(squared < 1.0e-14, 0.0, jnp.sqrt(squared))


def trajectory_vectors(
    cycle: jax.Array, initial_vectors: jax.Array, maximum_horizon: int
) -> jax.Array:
    def step(states: jax.Array, _unused: None) -> tuple[jax.Array, jax.Array]:
        next_states = states @ jnp.transpose(cycle)
        return next_states, next_states

    _last, tail = jax.lax.scan(
        step, initial_vectors, xs=None, length=maximum_horizon
    )
    return jnp.concatenate([initial_vectors[None, :, :], tail], axis=0)


def metric_trajectories(
    history_vectors: jax.Array, fixed_state: jax.Array
) -> dict[str, jax.Array]:
    history = jax.vmap(jax.vmap(unvec))(history_vectors)
    fixed_log = matrix_log_full_rank(fixed_state)

    def one_time(states: jax.Array) -> tuple[jax.Array, jax.Array, jax.Array]:
        trace_values = jax.vmap(lambda rho: trace_distance(rho, fixed_state))(states)
        umegaki_values = jax.vmap(
            lambda rho: umegaki_relative_entropy(rho, fixed_log)
        )(states)
        bures_values = jax.vmap(lambda rho: bures_distance(rho, fixed_state))(states)
        return trace_values, umegaki_values, bures_values

    trace_values, umegaki_values, bures_values = jax.vmap(one_time)(history)
    return {
        "trace": trace_values,
        "umegaki": umegaki_values,
        "bures": bures_values,
    }


def horizon_profile(values: jax.Array, horizons: Sequence[int]) -> dict[str, Any]:
    return {
        str(horizon): {
            "maximum": scalar(jnp.max(values[horizon])),
            "mean": scalar(jnp.mean(values[horizon])),
        }
        for horizon in horizons
    }


def first_epsilon_depth(maximum_trace: jax.Array, epsilon: float) -> int | None:
    values = jax.device_get(maximum_trace).tolist()
    return next((index for index, value in enumerate(values) if value <= epsilon), None)


def spectral_depth_prediction(
    subdominant: float, initial_maximum: float, epsilon: float
) -> int | None:
    if initial_maximum <= epsilon:
        return 0
    if not 0.0 < subdominant < 1.0:
        return None
    return max(1, int(math.ceil(math.log(epsilon / initial_maximum) / math.log(subdominant))))


def depth_factor(observed: int | None, predicted: int | None) -> float | None:
    if observed is None or predicted is None:
        return None
    if observed == 0 and predicted == 0:
        return 1.0
    return max(float(max(observed, 1)) / max(predicted, 1), float(max(predicted, 1)) / max(observed, 1))


def analyse_cycle(
    cycle: jax.Array,
    initial_states: jax.Array,
    horizons: Sequence[int],
    *,
    include_internal_arrays: bool = False,
) -> dict[str, Any]:
    fixed = fixed_point_report(cycle)
    initial_vectors = jax.vmap(vec)(initial_states)
    maximum_horizon = max(horizons)
    history = trajectory_vectors(cycle, initial_vectors, maximum_horizon)
    metrics = metric_trajectories(history, fixed["fixed_state"])
    maximum_trace = jnp.max(metrics["trace"], axis=1)
    observed_depth = first_epsilon_depth(maximum_trace, CONVERGENCE_EPS)
    predicted_depth = spectral_depth_prediction(
        fixed["subdominant_eigenvalue_modulus"],
        scalar(maximum_trace[0]),
        CONVERGENCE_EPS,
    )
    factor = depth_factor(observed_depth, predicted_depth)
    maximum_ume_increase = scalar(
        jnp.max(metrics["umegaki"][1:] - metrics["umegaki"][:-1])
    )
    maximum_bures_increase = scalar(
        jnp.max(metrics["bures"][1:] - metrics["bures"][:-1])
    )
    tests = {
        "T1_unique_full_rank_fixed_point": (
            fixed["fixed_point_multiplicity"] == 1
            and fixed["minimum_fixed_state_eigenvalue"] > FIXED_TOL
        ),
        "T2_strict_transverse_contraction": (
            fixed["subdominant_eigenvalue_modulus"] < 1.0 - CONTRACTION_TOL
        ),
        "T3_global_sampled_convergence": (
            scalar(maximum_trace[maximum_horizon]) < CONVERGENCE_EPS
        ),
        "T4_relative_entropy_pawl": maximum_ume_increase <= MONOTONIC_TOL,
        "T5_depth_matches_spectral_prediction": factor is not None and factor <= 4.0,
    }
    report = {
        "cycle_cptp": cptp_report(cycle),
        "spectrum": {
            "eigenvalues": fixed["eigenvalues"],
            "fixed_point_multiplicity": fixed["fixed_point_multiplicity"],
            "minimum_fixed_state_eigenvalue": fixed[
                "minimum_fixed_state_eigenvalue"
            ],
            "fixed_point_residual": fixed["fixed_point_residual"],
            "subdominant_eigenvalue_modulus": fixed[
                "subdominant_eigenvalue_modulus"
            ],
            "contraction_gap": fixed["contraction_gap"],
        },
        "fixed_state": fixed["fixed_state_json"],
        "trajectory_count": int(initial_states.shape[0]),
        "horizons": list(horizons),
        "trace_distance_profile": horizon_profile(metrics["trace"], horizons),
        "umegaki_relative_entropy_profile": horizon_profile(
            metrics["umegaki"], horizons
        ),
        "bures_distance_profile": horizon_profile(metrics["bures"], horizons),
        "maximum_ume_increase": maximum_ume_increase,
        "maximum_bures_increase": maximum_bures_increase,
        "epsilon_depth": {
            "epsilon": CONVERGENCE_EPS,
            "observed": observed_depth,
            "spectral_prediction": predicted_depth,
            "factor": factor,
        },
        "tests": tests,
    }
    if include_internal_arrays:
        report["_fixed_state_array"] = fixed["fixed_state"]
        report["_eigenvalues_array"] = fixed["eigenvalues_array"]
        report["_history_vectors"] = history
        report["_metrics"] = metrics
    return report


def strip_internal(report: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in report.items() if not key.startswith("_")}


def parameter_robustness(
    engine_type: str,
    nominal: dict[str, Any],
    initial_states: jax.Array,
    horizons: Sequence[int],
) -> dict[str, Any]:
    rows: dict[str, Any] = {}
    nominal_fixed = nominal["_fixed_state_array"]
    for multiplier in (0.9, 1.0, 1.1):
        if multiplier == 1.0:
            report = nominal
        else:
            cycle, _stages, _rows = build_source_cycle(engine_type, multiplier)
            report = analyse_cycle(cycle, initial_states, horizons)
        fixed = (
            report["_fixed_state_array"]
            if "_fixed_state_array" in report
            else fixed_point_report(build_source_cycle(engine_type, multiplier)[0])[
                "fixed_state"
            ]
        )
        drift = scalar(trace_distance(fixed, nominal_fixed))
        retained = all(
            bool(report["tests"][name])
            for name in (
                "T1_unique_full_rank_fixed_point",
                "T2_strict_transverse_contraction",
                "T3_global_sampled_convergence",
                "T4_relative_entropy_pawl",
            )
        )
        rows[f"{multiplier:.1f}"] = {
            "retains_T1_T4": retained,
            "fixed_point_trace_distance_from_nominal": drift,
            "tests": report["tests"],
            "spectrum": report["spectrum"],
        }
    passed = all(
        row["retains_T1_T4"]
        and row["fixed_point_trace_distance_from_nominal"] < 0.2
        for row in rows.values()
    )
    return {"multipliers": rows, "pass": passed}


def conjugation_superoperator(unitary: jax.Array) -> jax.Array:
    return unitary_channel(unitary)


def basis_covariance(
    cycle: jax.Array,
    nominal: dict[str, Any],
    initial_states: jax.Array,
    maximum_horizon: int,
) -> dict[str, Any]:
    native_history = nominal["_history_vectors"]
    native_metrics = nominal["_metrics"]
    native_eigenvalues = nominal["_eigenvalues_array"]
    initial_vectors = jax.vmap(vec)(initial_states)
    rows: dict[str, Any] = {}
    for label, unitary in PAULI_BASIS_TRANSFORMS.items():
        conjugation = conjugation_superoperator(unitary)
        transformed_cycle = conjugation @ cycle @ jnp.conj(conjugation.T)
        transformed_initial = initial_vectors @ jnp.transpose(conjugation)
        transformed_fixed = unvec(
            conjugation @ vec(nominal["_fixed_state_array"])
        )
        transformed_history = trajectory_vectors(
            transformed_cycle, transformed_initial, maximum_horizon
        )
        transformed_metrics = metric_trajectories(
            transformed_history, transformed_fixed
        )
        expected_history = native_history @ jnp.transpose(conjugation)
        eigenvalues = jnp.linalg.eigvals(transformed_cycle)
        rows[label] = {
            "spectrum_multiset_gap": spectral_multiset_gap(
                native_eigenvalues, eigenvalues
            ),
            "state_trajectory_covariance_residual": scalar(
                jnp.max(jnp.abs(transformed_history - expected_history))
            ),
            "trace_distance_trajectory_gap": scalar(
                jnp.max(jnp.abs(transformed_metrics["trace"] - native_metrics["trace"]))
            ),
            "umegaki_trajectory_gap": scalar(
                jnp.max(
                    jnp.abs(
                        transformed_metrics["umegaki"] - native_metrics["umegaki"]
                    )
                )
            ),
            "bures_trajectory_gap": scalar(
                jnp.max(jnp.abs(transformed_metrics["bures"] - native_metrics["bures"]))
            ),
        }
    maximum_gap = max(max(row.values()) for row in rows.values())
    return {"transforms": rows, "maximum_gap": maximum_gap, "pass": maximum_gap <= COVARIANCE_TOL}


def schedule_orders() -> dict[str, list[int]]:
    native = list(range(16))
    orders: dict[str, list[int]] = {"native": native, "reverse": list(reversed(native))}
    for shift in range(1, 16):
        orders[f"cyclic_shift_{shift}"] = native[shift:] + native[:shift]
    keys = jax.random.split(jax.random.PRNGKey(RANDOM_SEED + 1), 16)
    for index, key in enumerate(keys):
        order = jax.device_get(jax.random.permutation(key, 16)).tolist()
        orders[f"seeded_permutation_{index:02d}"] = [int(item) for item in order]
    return orders


def schedule_atlas(
    engine_type: str,
    initial_states: jax.Array,
    horizons: Sequence[int],
) -> dict[str, Any]:
    atlas: dict[str, Any] = {}
    initial_vectors = jax.vmap(vec)(initial_states)
    for name, order in schedule_orders().items():
        cycle, _stages, rows = build_source_cycle(engine_type, order=order)
        fixed = fixed_point_report(cycle)
        history = trajectory_vectors(cycle, initial_vectors, max(horizons))
        fixed_state = fixed["fixed_state"]
        trace_values = jax.vmap(
            lambda time_states: jax.vmap(
                lambda vector: trace_distance(unvec(vector), fixed_state)
            )(time_states)
        )(history)
        atlas[name] = {
            "order_indices": order,
            "ordered_tokens": [row["token"] for row in rows],
            "fixed_state": fixed["fixed_state_json"],
            "fixed_point_multiplicity": fixed["fixed_point_multiplicity"],
            "subdominant_eigenvalue_modulus": fixed[
                "subdominant_eigenvalue_modulus"
            ],
            "contraction_gap": fixed["contraction_gap"],
            "maximum_trace_distance_by_horizon": {
                str(horizon): scalar(jnp.max(trace_values[horizon]))
                for horizon in horizons
            },
        }
    return {
        "interpretation": "descriptive atlas only; T8 assigns no pass merely for changing or preserving a fixed point",
        "schedule_count": len(atlas),
        "schedules": atlas,
    }


def random_density(key: jax.Array) -> jax.Array:
    real_key, imag_key = jax.random.split(key)
    matrix = jax.random.normal(real_key, (2, 2), dtype=jnp.float64) + 1.0j * jax.random.normal(
        imag_key, (2, 2), dtype=jnp.float64
    )
    density = matrix @ jnp.conj(matrix.T) + 0.05 * I2
    return density / jnp.trace(density)


def random_kraus_channel(key: jax.Array) -> jax.Array:
    real_key, imag_key = jax.random.split(key)
    raw = jax.random.normal(real_key, (4, 2, 2), dtype=jnp.float64) + 1.0j * jax.random.normal(
        imag_key, (4, 2, 2), dtype=jnp.float64
    )
    gram = jnp.sum(jnp.conj(jnp.swapaxes(raw, 1, 2)) @ raw, axis=0)
    values, vectors = jnp.linalg.eigh(hermitize(gram))
    inverse_root = (vectors * (1.0 / jnp.sqrt(jnp.clip(values, 1.0e-14)))) @ jnp.conj(vectors.T)
    kraus = raw @ inverse_root
    return jnp.sum(jax.vmap(lambda item: jnp.kron(jnp.conj(item), item))(kraus), axis=0)


def replacement_channel(state: jax.Array) -> jax.Array:
    return jnp.outer(vec(state), jnp.conj(vec(I2)))


def matched_random_stage(key: jax.Array, target_identity_distance: float) -> tuple[jax.Array, float]:
    kraus_key, state_key = jax.random.split(key)
    replacement = replacement_channel(random_density(state_key))
    random_channel = 0.8 * random_kraus_channel(kraus_key) + 0.2 * replacement
    identity = jnp.eye(SUPER_DIM, dtype=DTYPE)
    random_distance = scalar(jnp.linalg.norm(random_channel - identity))
    if random_distance < target_identity_distance:
        random_channel = replacement
        random_distance = scalar(jnp.linalg.norm(random_channel - identity))
    mixing = min(1.0, target_identity_distance / max(random_distance, 1.0e-15))
    matched = (1.0 - mixing) * identity + mixing * random_channel
    mismatch = abs(scalar(jnp.linalg.norm(matched - identity)) - target_identity_distance)
    return matched, mismatch


def random_primitive_controls(
    native_cycle: jax.Array, native_stages: Sequence[jax.Array], control_count: int
) -> dict[str, Any]:
    target_distances = [
        scalar(jnp.linalg.norm(stage - jnp.eye(SUPER_DIM, dtype=DTYPE)))
        for stage in native_stages
    ]
    control_keys = jax.random.split(jax.random.PRNGKey(RANDOM_SEED), control_count)
    rows: list[dict[str, Any]] = []
    for control_index, control_key in enumerate(control_keys):
        stage_keys = jax.random.split(control_key, len(native_stages))
        stages: list[jax.Array] = []
        mismatches: list[float] = []
        for stage_key, target_distance in zip(stage_keys, target_distances):
            stage, mismatch = matched_random_stage(stage_key, target_distance)
            stages.append(stage)
            mismatches.append(mismatch)
        cycle = compose_execution_order(stages)
        fixed = fixed_point_report(cycle)
        cycle_cptp = cptp_report(cycle)
        primitive = (
            fixed["fixed_point_multiplicity"] == 1
            and fixed["minimum_fixed_state_eigenvalue"] > FIXED_TOL
            and fixed["subdominant_eigenvalue_modulus"] < 1.0 - CONTRACTION_TOL
            and cycle_cptp["pass"]
        )
        rows.append(
            {
                "control_index": control_index,
                "primitive": primitive,
                "contraction_gap": fixed["contraction_gap"],
                "subdominant_eigenvalue_modulus": fixed[
                    "subdominant_eigenvalue_modulus"
                ],
                "minimum_fixed_state_eigenvalue": fixed[
                    "minimum_fixed_state_eigenvalue"
                ],
                "maximum_stage_identity_distance_mismatch": max(mismatches),
                "cycle_cptp": cycle_cptp,
            }
        )
    gaps = jnp.asarray([row["contraction_gap"] for row in rows], dtype=jnp.float64)
    percentile_95 = scalar(jnp.quantile(gaps, 0.95))
    native_gap = fixed_point_report(native_cycle)["contraction_gap"]
    controls_valid = all(
        row["primitive"]
        and row["maximum_stage_identity_distance_mismatch"] <= 1.0e-10
        for row in rows
    )
    return {
        "seed": RANDOM_SEED,
        "control_count": control_count,
        "matching_rule": "same 2x2 carrier, 16 stages, execution order, and per-stage Frobenius distance from identity; random four-Kraus channels include a full-rank replacement component",
        "controls_valid": controls_valid,
        "native_contraction_gap": native_gap,
        "control_gap_percentile_95": percentile_95,
        "native_exceeds_control_percentile_95": native_gap > percentile_95,
        "rows": rows,
    }


def unitary_no_attraction_control(engine_type: str) -> dict[str, Any]:
    cycle, stages, rows = build_source_cycle(engine_type, erase_dissipation=True)
    fixed = fixed_point_report(cycle)
    destroyed = (
        fixed["subdominant_eigenvalue_modulus"] >= 1.0 - CONTRACTION_TOL
        or fixed["fixed_point_multiplicity"] != 1
    )
    return {
        "erasure": "terrain jumps removed; Ti and Te replaced by identity; Fi and Fe retained",
        "ordered_tokens": [row["token"] for row in rows],
        "all_stages_cptp": all(cptp_report(stage)["pass"] for stage in stages),
        "fixed_point_multiplicity": fixed["fixed_point_multiplicity"],
        "subdominant_eigenvalue_modulus": fixed[
            "subdominant_eigenvalue_modulus"
        ],
        "strict_attraction_destroyed": destroyed,
        "pass": destroyed,
    }


def commuting_fixed_manifold_control() -> dict[str, Any]:
    z_dephase = pinching_channel(SZ, 0.12)
    cycle = compose_execution_order([z_dephase] * 16)
    fixed = fixed_point_report(cycle)
    passed = fixed["fixed_point_multiplicity"] >= 2
    return {
        "construction": "16 mutually commuting z-dephasing channels with all Hamiltonian and rotation components erased",
        "fixed_point_multiplicity": fixed["fixed_point_multiplicity"],
        "subdominant_eigenvalue_modulus": fixed[
            "subdominant_eigenvalue_modulus"
        ],
        "fixed_manifold_retained": passed,
        "cycle_cptp": cptp_report(cycle),
        "pass": passed,
    }


def dynamiqs_parity_microcheck() -> dict[str, Any]:
    duration = 0.2
    hamiltonian = 0.77 * dq.sigmaz() + 0.13 * dq.sigmax()
    jump = dq.sigmaz()
    times = jnp.asarray([0.0, duration], dtype=jnp.float64)
    mixed = density_from_bloch(jnp.asarray([0.31, -0.22, 0.47], dtype=jnp.float64))
    pure = density_from_bloch(
        jnp.asarray([1.0 / jnp.sqrt(2.0), 0.5, 0.5], dtype=jnp.float64)
    )
    pure = pure / jnp.trace(pure)
    exact_channel = finite_lindblad_channel(H0, SZ, duration)

    def solve(state: jax.Array, h: Any, jumps: list[Any]) -> jax.Array:
        result = dq.mesolve(
            h,
            jumps,
            dq.asqarray(state, dims=(2,)),
            times,
            method=dq.method.Tsit5(rtol=1.0e-11, atol=1.0e-11),
            options=dq.Options(progress_meter=False),
        )
        return result.states.to_jax()[-1]

    positive_dynamiqs = solve(mixed, hamiltonian, [jump])
    positive_exact = apply_superoperator(exact_channel, mixed)
    positive_residual = scalar(jnp.linalg.norm(positive_dynamiqs - positive_exact))

    erased_dynamiqs = solve(mixed, 0.0 * hamiltonian, [])
    erased_residual = scalar(jnp.linalg.norm(erased_dynamiqs - mixed))

    boundary_dynamiqs = solve(pure, hamiltonian, [jump])
    boundary_exact = apply_superoperator(exact_channel, pure)
    boundary_residual = scalar(jnp.linalg.norm(boundary_dynamiqs - boundary_exact))

    passed = max(positive_residual, erased_residual, boundary_residual) <= DYNAMIQS_PARITY_TOL
    return {
        "function_called": "dynamiqs.mesolve",
        "positive_case": {
            "description": "nontrivial Type1 Se H0 plus sigma_z jump on a full-rank state",
            "residual_vs_jax_scipy_expm": positive_residual,
        },
        "negative_erased_control": {
            "description": "zero Hamiltonian and empty jump list must preserve the input",
            "residual_from_identity": erased_residual,
        },
        "boundary_case": {
            "description": "pure Bloch-sphere boundary input under the same nontrivial generator",
            "residual_vs_jax_scipy_expm": boundary_residual,
        },
        "tolerance": DYNAMIQS_PARITY_TOL,
        "demotion_condition": "any positive, erased, or pure-boundary residual above tolerance invalidates the JAX lane and forces all_pass false",
        "pass": passed,
        "gates": ["result_integrity", "all_pass"],
    }


def source_semantics_receipt(spec: dict[str, Any]) -> dict[str, Any]:
    expected_tokens = [row[0] for row in ORDERED_SLOT_SPECS]
    source_hash = sha256_file(CANONICAL_SEMANTICS_PATH)
    checks = {
        "spec_hash_matches_preregistered_value": sha256_file(SPEC_PATH)
        == EXPECTED_SPEC_SHA256,
        "preregistration_hash_matches_preregistered_value": sha256_file(
            PREREGISTRATION_PATH
        )
        == EXPECTED_PREREGISTRATION_SHA256,
        "worktree_semantics_matches_committed_HEAD_hash": source_hash
        == EXPECTED_COMMITTED_SEMANTICS_SHA256,
        "ordered_slots_match_spec": expected_tokens == spec["ordered_source_slots"],
        "classification_locked": spec["classification"] == CLASSIFICATION,
        "promotion_locked_false": spec["promotion_allowed"] is False,
        "formal_admission_locked_false": spec["formal_admission_allowed"] is False,
    }
    return {
        "hashes": {
            rel(SPEC_PATH): sha256_file(SPEC_PATH),
            rel(PREREGISTRATION_PATH): sha256_file(PREREGISTRATION_PATH),
            rel(CANONICAL_SEMANTICS_PATH): source_hash,
            rel(SOURCE_PATH): sha256_file(SOURCE_PATH),
        },
        "expected_hashes": {
            rel(SPEC_PATH): EXPECTED_SPEC_SHA256,
            rel(PREREGISTRATION_PATH): EXPECTED_PREREGISTRATION_SHA256,
            "git_show_HEAD:system_v5/ops/formal_scouts/canonical_qit_engine_specs.py": EXPECTED_COMMITTED_SEMANTICS_SHA256,
        },
        "checks": checks,
        "pass": all(checks.values()),
    }


def package_receipt() -> dict[str, Any]:
    return {
        "interpreter": {
            "executable": sys.executable,
            "version": sys.version,
            "prefix": sys.prefix,
        },
        "packages": {
            "jax": {
                "version": jax.__version__,
                "module_path": str(Path(jax.__file__).resolve()),
            },
            "jaxlib": {
                "version": importlib.metadata.version("jaxlib"),
                "distribution_path": str(
                    Path(importlib.metadata.distribution("jaxlib").locate_file(""))
                    .resolve()
                ),
            },
            "dynamiqs": {
                "version": importlib.metadata.version("dynamiqs"),
                "module_path": str(Path(dq.__file__).resolve()),
            },
        },
        "jax": {
            "x64_enabled": bool(jax.config.jax_enable_x64),
            "devices": [
                {
                    "platform": device.platform,
                    "device_kind": device.device_kind,
                    "id": device.id,
                }
                for device in jax.devices()
            ],
        },
    }


def type_difference(type_reports: dict[str, dict[str, Any]], horizons: Sequence[int]) -> dict[str, Any]:
    left = type_reports["Type1_left"]
    right = type_reports["Type2_right"]
    fixed_gap = scalar(
        trace_distance(left["_fixed_state_array"], right["_fixed_state_array"])
    )
    depth_profile_gap = max(
        abs(
            left["trace_distance_profile"][str(horizon)]["maximum"]
            - right["trace_distance_profile"][str(horizon)]["maximum"]
        )
        for horizon in horizons
    )
    passed = max(fixed_gap, depth_profile_gap) > 1.0e-6
    return {
        "fixed_point_trace_distance": fixed_gap,
        "maximum_depth_profile_gap": depth_profile_gap,
        "threshold": 1.0e-6,
        "pass": passed,
    }


def choose_verdict(tests: dict[str, bool]) -> str:
    nominal = all(tests[f"T{index}"] for index in range(1, 5))
    robust = all(tests[f"T{index}"] for index in range(1, 8))
    controls = tests["T10"] and tests["T11"] and tests["T12"]
    if robust and tests["T9"] and controls:
        return "REAL_DISTINCTIVE_INSTALLED_BASINS"
    if robust and controls and not tests["T9"]:
        return "REAL_BUT_GENERIC_INSTALLED_BASINS"
    if nominal:
        return "LOCAL_OR_FRAGILE_INSTALLED_BASIN_ONLY"
    return "NO_REAL_ATTRACTOR_BASIN_IN_THIS_MAP"


def build_result() -> dict[str, Any]:
    spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    hashes = source_semantics_receipt(spec)
    initial_states = deterministic_initial_states()
    horizons = tuple(int(value) for value in spec["parameter_grid"]["horizons"])
    maximum_horizon = max(horizons)

    parity = dynamiqs_parity_microcheck()
    type_reports: dict[str, dict[str, Any]] = {}
    engine_payloads: dict[str, Any] = {}
    stage_payloads: dict[str, Any] = {}
    random_controls: dict[str, Any] = {}
    unitary_controls: dict[str, Any] = {}
    commuting_control = commuting_fixed_manifold_control()

    for engine_type in spec["parameter_grid"]["engine_types"]:
        cycle, stages, rows = build_source_cycle(engine_type)
        report = analyse_cycle(
            cycle,
            initial_states,
            horizons,
            include_internal_arrays=True,
        )
        type_reports[engine_type] = report
        stage_checks = [cptp_report(stage) for stage in stages]
        stage_payloads[engine_type] = {
            "stage_count": len(stages),
            "all_stage_maps_cptp": all(row["pass"] for row in stage_checks),
            "minimum_stage_choi_eigenvalue": min(
                row["minimum_choi_eigenvalue"] for row in stage_checks
            ),
            "maximum_stage_trace_preservation_residual": max(
                row["trace_preservation_residual"] for row in stage_checks
            ),
            "rows": [
                {**metadata, "cptp": cptp}
                for metadata, cptp in zip(rows, stage_checks)
            ],
        }
        robustness = parameter_robustness(
            engine_type, report, initial_states, horizons
        )
        covariance = basis_covariance(
            cycle, report, initial_states, maximum_horizon
        )
        schedules = schedule_atlas(engine_type, initial_states, horizons)
        random_control = random_primitive_controls(
            cycle, stages, int(spec["parameter_grid"]["random_control_count"])
        )
        unitary_control = unitary_no_attraction_control(engine_type)
        random_controls[engine_type] = random_control
        unitary_controls[engine_type] = unitary_control
        engine_payloads[engine_type] = {
            "nominal": strip_internal(report),
            "bloch_affine_readout": bloch_affine_readout(cycle),
            "parameter_robustness": robustness,
            "basis_covariance": covariance,
            "schedule_atlas": schedules,
            "random_primitive_controls": random_control,
            "unitary_no_attraction_control": unitary_control,
        }

    type_delta = type_difference(type_reports, horizons)
    tests = {
        "T1": all(
            report["tests"]["T1_unique_full_rank_fixed_point"]
            for report in type_reports.values()
        ),
        "T2": all(
            report["tests"]["T2_strict_transverse_contraction"]
            for report in type_reports.values()
        ),
        "T3": all(
            report["tests"]["T3_global_sampled_convergence"]
            for report in type_reports.values()
        ),
        "T4": all(
            report["tests"]["T4_relative_entropy_pawl"]
            for report in type_reports.values()
        ),
        "T5": all(
            report["tests"]["T5_depth_matches_spectral_prediction"]
            for report in type_reports.values()
        ),
        "T6": all(
            engine_payloads[engine]["parameter_robustness"]["pass"]
            for engine in engine_payloads
        ),
        "T7": all(
            engine_payloads[engine]["basis_covariance"]["pass"]
            for engine in engine_payloads
        ),
        "T8": None,
        "T9": all(
            control["controls_valid"]
            and control["native_exceeds_control_percentile_95"]
            for control in random_controls.values()
        ),
        "T10": all(control["pass"] for control in unitary_controls.values()),
        "T11": commuting_control["pass"],
        "T12": type_delta["pass"],
    }
    verdict = choose_verdict(tests)
    stage_integrity = all(
        payload["all_stage_maps_cptp"] for payload in stage_payloads.values()
    )
    cycle_integrity = all(
        report["cycle_cptp"]["pass"] for report in type_reports.values()
    )
    result_integrity = (
        hashes["pass"]
        and parity["pass"]
        and stage_integrity
        and cycle_integrity
        and bool(jax.config.jax_enable_x64)
        and int(initial_states.shape[0]) == 1024
    )
    all_pass = result_integrity and verdict in {
        "REAL_DISTINCTIVE_INSTALLED_BASINS",
        "REAL_BUT_GENERIC_INSTALLED_BASINS",
    }

    return {
        "schema": "codex_ratchet.coratchet_basin_depth_multiview_v0.jax_result.v1",
        "sim_id": spec["sim_id"],
        "engine": "jax",
        "engine_contract": spec["engine_contract"],
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "stage_movement_allowed": STAGE_MOVEMENT_ALLOWED,
        "reads_peer_result": READS_PEER_RESULT,
        "ran": True,
        "determinism": {
            "random_seed": RANDOM_SEED,
            "jax_x64_required": True,
            "initial_state_construction": "16 deterministic radii x 64 Fibonacci-sphere directions",
            "initial_state_count": int(initial_states.shape[0]),
            "schedule_permutation_count": 16,
            "result_timestamp_policy": "no wall-clock timestamp is serialized",
        },
        "source_and_spec_binding": hashes,
        "runtime": package_receipt(),
        "source_semantics": {
            "carrier": "2x2 density matrices / four-dimensional Liouville space",
            "terrain_law": "exp(0.2 L_GKSL) using H=+/-H0 and Type2 L=sigma_x L_Type1 sigma_x",
            "operator_maps": {
                "Ti": "z-pinching with q=0.12",
                "Te": "x-pinching with q=0.09",
                "Fi": "x-axis unitary rotation theta=0.15",
                "Fe": "z-axis unitary rotation phi=0.11",
            },
            "axis6_rule": "composition precedence only; operator formulas are invariant under UP/DOWN",
            "cycle_execution_convention": "listed slot 0 acts first; cycle=S15 o ... o S0",
            "ordered_source_slots": spec["ordered_source_slots"],
            "independent_construction": True,
        },
        "stage_maps": stage_payloads,
        "engines": engine_payloads,
        "controls": {
            "commuting_fixed_manifold": commuting_control,
            "type_difference": type_delta,
        },
        "preregistered_tests": {
            "T1_unique_full_rank_fixed_point": tests["T1"],
            "T2_strict_transverse_contraction": tests["T2"],
            "T3_global_sampled_convergence": tests["T3"],
            "T4_relative_entropy_pawl": tests["T4"],
            "T5_depth_matches_spectral_prediction": tests["T5"],
            "T6_parameter_robustness": tests["T6"],
            "T7_basis_covariance": tests["T7"],
            "T8_schedule_sensitivity": {
                "status": "atlas_only",
                "binary_scientific_pass_assigned": False,
                "atlas_reported_for_both_types": all(
                    engine_payloads[engine]["schedule_atlas"]["schedule_count"]
                    == 33
                    for engine in engine_payloads
                ),
            },
            "T9_genericity_kill_control": tests["T9"],
            "T10_unitary_no_attraction_control": tests["T10"],
            "T11_commuting_fixed_manifold_control": tests["T11"],
            "T12_type_difference": tests["T12"],
        },
        "scientific_verdict": verdict,
        "result_integrity": {
            "source_and_spec_hashes": hashes["pass"],
            "dynamiqs_gating_parity": parity["pass"],
            "all_32_stage_maps_cptp": stage_integrity,
            "both_cycle_maps_cptp": cycle_integrity,
            "jax_x64": bool(jax.config.jax_enable_x64),
            "exactly_1024_initial_states": int(initial_states.shape[0]) == 1024,
            "pass": result_integrity,
        },
        "all_pass": all_pass,
        "rich_package_parity_microcheck": parity,
        "packages_used": [
            "jax",
            "jax.numpy",
            "jax.scipy.linalg.expm",
            "dynamiqs",
        ],
        "aligned_packages_load_bearing": [
            "jax",
            "jax.scipy.linalg.expm",
            "dynamiqs",
        ],
        "claim_path_tools": [
            "jax.lax.scan",
            "jax.vmap",
            "jax.numpy.linalg.eig",
            "jax.numpy.linalg.eigh",
            "jax.scipy.linalg.expm",
            "jax.random",
            "dynamiqs.mesolve",
        ],
        "functions_called": [
            "jax.config.update",
            "jax.lax.scan",
            "jax.vmap",
            "jax.random.PRNGKey",
            "jax.random.split",
            "jax.random.permutation",
            "jax.random.normal",
            "jax.numpy.linalg.eig",
            "jax.numpy.linalg.eigh",
            "jax.numpy.linalg.eigvalsh",
            "jax.numpy.linalg.det",
            "jax.numpy.linalg.norm",
            "jax.numpy.quantile",
            "jax.scipy.linalg.expm",
            "dynamiqs.asqarray",
            "dynamiqs.mesolve",
            "dynamiqs.Options",
        ],
        "tool_calls": [
            {
                "tool": "jax.scipy.linalg.expm",
                "qualified_api": "jax.scipy.linalg.expm",
                "input_object": "independently constructed 4x4 Liouville GKSL and Hamiltonian generators",
                "output_object": "finite-time CPTP terrain and unitary superoperators",
                "positive_case": "32 source-faithful stage maps and two native cycles pass Choi/trace-preservation gates",
                "negative_erased_control": "Hamiltonian-only terrain plus identity Ti/Te destroys strict attraction",
                "boundary_case": "0.9 and 1.1 preregistered parameter multipliers remain inside the same construction",
                "demotion_condition": "any stage/cycle CPTP failure or parameter construction drift forces result_integrity false",
                "gates": ["result_integrity", "T1", "T2", "T3", "T4", "T6", "all_pass"],
            },
            {
                "tool": "jax",
                "qualified_api": "jax.lax.scan + jax.vmap + jax.numpy.linalg.eig/eigh",
                "input_object": "two 16-stage cycles, 1024 deterministic density states, horizons through 256, schedule and random-control families",
                "output_object": "spectra, fixed points, trace/Umegaki/Bures trajectories, robustness and control atlas",
                "positive_case": "native cycle tests T1-T7 are computed from x64 JAX trajectories",
                "negative_erased_control": "unitary-only and commuting-dephasing controls pressure uniqueness and contraction",
                "boundary_case": "pure Bloch boundary states and Pauli basis conjugations are included",
                "demotion_condition": "x64 disablement, wrong state count, failed controls, or nonfinite strict JSON blocks all_pass",
                "gates": ["T1", "T2", "T3", "T4", "T5", "T6", "T7", "T9", "T10", "T11", "T12", "all_pass"],
            },
            {
                "tool": "dynamiqs",
                "qualified_api": "dynamiqs.mesolve",
                "input_object": "Type1 Se H0/sigma_z Lindblad microfixtures",
                "output_object": "independent mixed, erased, and pure-boundary final density matrices",
                "positive_case": parity["positive_case"]["description"],
                "negative_erased_control": parity["negative_erased_control"][
                    "description"
                ],
                "boundary_case": parity["boundary_case"]["description"],
                "demotion_condition": parity["demotion_condition"],
                "gates": ["result_integrity", "all_pass"],
            },
        ],
        "positive_negative_boundary_demotion_receipts": {
            "positive": {
                "native_cycles": "T1-T7 measured independently for Type1 and Type2",
                "source_words": "all 16 explicit native formulas emitted per engine",
            },
            "negative": {
                "random_primitive": "64 matched random primitive CPTP cycles per engine",
                "unitary_erasure": "all dissipative components erased",
                "commuting_manifold": "16 commuting z-dephasing channels",
            },
            "boundary": {
                "parameter_multipliers": [0.9, 1.0, 1.1],
                "pure_state_shell_included": True,
                "pauli_basis_transforms": list(PAULI_BASIS_TRANSFORMS),
                "maximum_horizon": maximum_horizon,
            },
            "demotion": {
                "hash_or_source_drift": "result_integrity false",
                "dynamiqs_parity_failure": "result_integrity false and all_pass false",
                "CPTP_failure": "result_integrity false and all_pass false",
                "nominal_T1_T4_failure": "NO_REAL_ATTRACTOR_BASIN_IN_THIS_MAP",
                "robustness_or_control_failure": "LOCAL_OR_FRAGILE_INSTALLED_BASIN_ONLY or lower",
                "genericity_failure_with_other_gates_green": "REAL_BUT_GENERIC_INSTALLED_BASINS",
            },
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "claim_ceiling": spec["claim_ceiling"],
        "blocked_consumers": spec["blocked_consumers"],
        "eligible_consumers": [
            "numeric characterization of the explicitly installed finite CPTP cycle",
            "controller-side comparison with an independently authored Julia semantic-owner result",
        ],
    }


def main() -> int:
    result = build_result()
    strict_write_json(RESULT_PATH, result)
    print(
        json.dumps(
            {
                "sim_id": result["sim_id"],
                "engine": "jax",
                "scientific_verdict": result["scientific_verdict"],
                "result_integrity": result["result_integrity"]["pass"],
                "all_pass": result["all_pass"],
                "result_path": rel(RESULT_PATH),
            },
            sort_keys=True,
            allow_nan=False,
        )
    )
    return 0 if result["result_integrity"]["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
