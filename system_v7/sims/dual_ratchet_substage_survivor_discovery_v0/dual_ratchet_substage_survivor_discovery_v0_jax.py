#!/usr/bin/env python3
"""Target-free dual restriction and quotient discovery for engine substages."""

from __future__ import annotations

import hashlib
import importlib.metadata
import itertools
import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence

from jax import config

config.update("jax_enable_x64", True)

import jax
import jax.numpy as jnp
import numpy as np
from scipy.optimize import linear_sum_assignment


classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False
stage_movement_allowed = False
sim_execution_kind = "nonclassical"

TOOL_MANIFEST = {
    "jax": {
        "tried": True,
        "used": True,
        "reason": "load-bearing batched affine composition, geometry fingerprints, density spectra, and entropy fingerprints",
    },
    "scipy.optimize.linear_sum_assignment": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact terrain-ensemble automorphism matching",
    },
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "supportive candidate construction, finite Choi checks, clustering, and serialization",
    },
    "stage_interior_architecture_tournament": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact eight terrain flow maps from the current house carrier",
        "role_source": "upstream",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "jax": "load_bearing",
    "scipy.optimize.linear_sum_assignment": "load_bearing",
    "numpy": "supportive",
    "stage_interior_architecture_tournament": "load_bearing",
}

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
RESULT_PATH = HERE / "results" / "dual_ratchet_substage_survivor_discovery_v0_jax_results.json"
SPEC_PATH = HERE / "spec.json"
BASE_PATH = (
    REPO
    / "system_v7"
    / "constraint_core"
    / "sims_and_scripts"
    / "stage_interior_architecture_tournament_sim.py"
)
BASE_DIR = BASE_PATH.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
import stage_interior_architecture_tournament_sim as stage_base  # noqa: E402


PAULI = np.stack([stage_base.SX, stage_base.SY, stage_base.SZ])
I2 = stage_base.I2
FINGERPRINT_EPS = 1.0e-14
STRICT_ENTROPY = 1.0e-8


@dataclass(frozen=True)
class AffineMap:
    matrix: np.ndarray
    offset: np.ndarray


@dataclass(frozen=True)
class Candidate:
    candidate_id: str
    samples: tuple[AffineMap, ...]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [jsonable(item) for item in value]
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.floating, np.integer)):
        return value.item()
    if isinstance(value, np.bool_):
        return bool(value)
    if isinstance(value, Path):
        return str(value)
    return value


def compact_result(value: Any) -> Any:
    """Drop high-volume vectors while preserving the decisions they support."""
    if isinstance(value, dict):
        return {
            str(key): compact_result(item)
            for key, item in value.items()
            if key != "fingerprint"
        }
    if isinstance(value, (list, tuple)):
        return [compact_result(item) for item in value]
    return value


def normalize_axis(axis: Sequence[float]) -> np.ndarray:
    vector = np.asarray(axis, dtype=float)
    return vector / np.linalg.norm(vector)


def dephasing_map(axis: Sequence[float], strength: float) -> AffineMap:
    direction = normalize_axis(axis)
    matrix = (1.0 - strength) * np.eye(3) + strength * np.outer(direction, direction)
    return AffineMap(matrix=matrix, offset=np.zeros(3))


def rotation_map(axis: Sequence[float], angle: float) -> AffineMap:
    x, y, z = normalize_axis(axis)
    cross = np.array([[0.0, -z, y], [z, 0.0, -x], [-y, x, 0.0]])
    matrix = np.eye(3) + math.sin(angle) * cross + (1.0 - math.cos(angle)) * (cross @ cross)
    return AffineMap(matrix=matrix, offset=np.zeros(3))


def depolarizing_map(strength: float) -> AffineMap:
    return AffineMap(matrix=(1.0 - strength) * np.eye(3), offset=np.zeros(3))


def amplitude_damping_map(strength: float, pole: int) -> AffineMap:
    matrix = np.diag([math.sqrt(1.0 - strength), math.sqrt(1.0 - strength), 1.0 - strength])
    return AffineMap(matrix=matrix, offset=np.array([0.0, 0.0, float(pole) * strength]))


def identity_map() -> AffineMap:
    return AffineMap(matrix=np.eye(3), offset=np.zeros(3))


def transpose_map() -> AffineMap:
    return AffineMap(matrix=np.diag([1.0, -1.0, 1.0]), offset=np.zeros(3))


def build_candidates(
    spec: dict[str, Any],
    *,
    include_generic_axes: bool,
    erase_rotation_sides: bool = False,
) -> tuple[list[Candidate], dict[str, dict[str, Any]]]:
    axes = list(spec["main_axis_registry"])
    registry = ["pauli_x", "pauli_y", "pauli_z"]
    if include_generic_axes:
        axes.extend(spec["generic_axis_challenge"])
        registry.extend(["generic_h0", "generic_123"])

    candidates: list[Candidate] = []
    truth: dict[str, dict[str, Any]] = {}

    def add(samples: Iterable[AffineMap], **metadata: Any) -> None:
        candidate_id = f"candidate_{len(candidates):03d}"
        candidates.append(Candidate(candidate_id=candidate_id, samples=tuple(samples)))
        truth[candidate_id] = metadata

    strengths = spec["candidate_family_samples"]["axis_dephasing_strengths"]
    angles = spec["candidate_family_samples"]["axis_rotation_absolute_angles"]
    sides = [1] if erase_rotation_sides else spec["candidate_family_samples"]["axis_rotation_sides"]
    for axis, registry_name in zip(axes, registry):
        add(
            (dephasing_map(axis, strength) for strength in strengths),
            family="axis_dephasing_path",
            axis_registry=registry_name,
            main_registry=registry_name.startswith("pauli_"),
            expected_operator=("Te" if registry_name in {"pauli_x", "pauli_y"} else "Ti")
            if registry_name.startswith("pauli_")
            else None,
        )
        add(
            (rotation_map(axis, side * angle) for angle in angles for side in sides),
            family="axis_rotation_path",
            axis_registry=registry_name,
            main_registry=registry_name.startswith("pauli_"),
            expected_operator=("Fi" if registry_name in {"pauli_x", "pauli_y"} else "Fe")
            if registry_name.startswith("pauli_")
            else None,
        )

    add((identity_map(), identity_map(), identity_map()), family="identity_null", axis_registry=None, main_registry=False)
    add(
        (depolarizing_map(value) for value in spec["candidate_family_samples"]["isotropic_depolarizing_strengths"]),
        family="isotropic_depolarizing_control",
        axis_registry=None,
        main_registry=False,
    )
    add(
        (
            amplitude_damping_map(value, pole)
            for value in spec["candidate_family_samples"]["amplitude_damping_strengths"]
            for pole in spec["candidate_family_samples"]["amplitude_damping_poles"]
        ),
        family="amplitude_damping_control",
        axis_registry="pauli_z",
        main_registry=False,
    )
    add((transpose_map(),), family="transpose_non_cp_control", axis_registry=None, main_registry=False)
    return candidates, truth


def affine_from_terrain(terrain: int) -> AffineMap:
    zero = stage_base.bloch(stage_base.flow_terrain(terrain, stage_base.dm(np.zeros(3))))
    columns = []
    for index in range(3):
        basis = np.zeros(3)
        basis[index] = 1.0
        moved = stage_base.bloch(stage_base.flow_terrain(terrain, stage_base.dm(basis)))
        columns.append(moved - zero)
    return AffineMap(matrix=np.column_stack(columns), offset=zero)


def terrain_maps() -> list[AffineMap]:
    return [affine_from_terrain(terrain) for terrain in sorted(stage_base.TERR)]


def fixed_point(channel: AffineMap) -> np.ndarray:
    return np.linalg.lstsq(np.eye(3) - channel.matrix, channel.offset, rcond=None)[0]


def signed_permutation_matrices() -> list[np.ndarray]:
    matrices = []
    for permutation in itertools.permutations(range(3)):
        for signs in itertools.product((-1.0, 1.0), repeat=3):
            matrix = np.zeros((3, 3))
            for row, column in enumerate(permutation):
                matrix[row, column] = signs[row]
            matrices.append(matrix)
    return matrices


def discover_terrain_automorphisms(
    terrains: Sequence[AffineMap],
    tolerance: float,
) -> dict[str, Any]:
    rows = []
    for matrix in signed_permutation_matrices():
        costs = np.zeros((len(terrains), len(terrains)))
        for left, terrain in enumerate(terrains):
            transformed_matrix = matrix @ terrain.matrix @ matrix.T
            transformed_offset = matrix @ terrain.offset
            for right, target in enumerate(terrains):
                costs[left, right] = np.linalg.norm(transformed_matrix - target.matrix) + np.linalg.norm(
                    transformed_offset - target.offset
                )
        left_indices, right_indices = linear_sum_assignment(costs)
        maximum_error = float(np.max(costs[left_indices, right_indices]))
        if maximum_error <= tolerance:
            rows.append(
                {
                    "matrix": matrix,
                    "determinant": int(round(np.linalg.det(matrix))),
                    "terrain_permutation": right_indices,
                    "maximum_match_error": maximum_error,
                }
            )
    proper = [row for row in rows if row["determinant"] == 1]
    axis_orbits = []
    for axis_index in range(3):
        vector = np.eye(3)[axis_index]
        orbit = sorted({int(np.argmax(np.abs(row["matrix"] @ vector))) for row in proper})
        axis_orbits.append(orbit)
    return {
        "rows": rows,
        "count": len(rows),
        "proper_rotation_count": len(proper),
        "axis_orbits_zero_based": axis_orbits,
        "all_matches_within_tolerance": all(row["maximum_match_error"] <= tolerance for row in rows),
    }


def symmetry_closed_probes(
    seed: int,
    base_count: int,
    radius_min: float,
    radius_max: float,
    automorphisms: Sequence[dict[str, Any]],
) -> np.ndarray:
    rng = np.random.default_rng(seed)
    base = rng.normal(size=(base_count, 3))
    base /= np.linalg.norm(base, axis=1, keepdims=True)
    base *= rng.uniform(radius_min, radius_max, size=(base_count, 1))
    expanded = np.vstack([row["matrix"] @ vector for vector in base for row in automorphisms])
    return np.unique(np.round(expanded, 13), axis=0)


def apply_affine(channel: AffineMap, vectors: np.ndarray) -> np.ndarray:
    return vectors @ channel.matrix.T + channel.offset


def apply_to_matrix(channel: AffineMap, value: np.ndarray) -> np.ndarray:
    trace = np.trace(value)
    coordinates = np.array([np.trace(value @ sigma) for sigma in PAULI], dtype=complex)
    moved = channel.matrix @ coordinates + channel.offset * trace
    return 0.5 * (trace * I2 + sum(moved[index] * PAULI[index] for index in range(3)))


def choi_matrix(channel: AffineMap) -> np.ndarray:
    choi = np.zeros((4, 4), dtype=complex)
    for row in range(2):
        for column in range(2):
            matrix_unit = np.zeros((2, 2), dtype=complex)
            matrix_unit[row, column] = 1.0
            moved = apply_to_matrix(channel, matrix_unit)
            choi[row * 2 : (row + 1) * 2, column * 2 : (column + 1) * 2] = moved
    return 0.5 * (choi + choi.conj().T)


def physical_summary(candidate: Candidate, tolerance: float) -> dict[str, Any]:
    minimum_choi = min(float(np.min(np.linalg.eigvalsh(choi_matrix(sample))).real) for sample in candidate.samples)
    maximum_offset = max(float(np.linalg.norm(sample.offset)) for sample in candidate.samples)
    return {
        "minimum_choi_eigenvalue": minimum_choi,
        "all_samples_cp": minimum_choi >= -tolerance,
        "maximum_unital_offset_norm": maximum_offset,
        "all_samples_unital": maximum_offset <= tolerance,
    }


@jax.jit
def geometry_fingerprint_jax(
    sample_matrices: jax.Array,
    sample_offsets: jax.Array,
    terrain_matrices: jax.Array,
    terrain_offsets: jax.Array,
    probes: jax.Array,
) -> jax.Array:
    def one_sample(operator_matrix, operator_offset):
        def one_terrain(terrain_matrix, terrain_offset):
            operator_first = probes @ operator_matrix.T + operator_offset
            terrain_after = operator_first @ terrain_matrix.T + terrain_offset
            terrain_first = probes @ terrain_matrix.T + terrain_offset
            operator_after = terrain_first @ operator_matrix.T + operator_offset
            return jnp.linalg.norm(terrain_after - operator_after, axis=1)

        return jax.vmap(one_terrain)(terrain_matrices, terrain_offsets)

    values = jax.vmap(one_sample)(sample_matrices, sample_offsets)
    return jnp.sort(values.reshape(-1))


def density_from_bloch_jax(vector: jax.Array) -> jax.Array:
    x, y, z = vector
    return 0.5 * jnp.array(
        [[1.0 + z, x - 1.0j * y], [x + 1.0j * y, 1.0 - z]],
        dtype=jnp.complex128,
    )


def entropy_jax(vector: jax.Array) -> jax.Array:
    eigenvalues = jnp.linalg.eigvalsh(density_from_bloch_jax(vector))
    safe = jnp.clip(jnp.real(eigenvalues), 1.0e-14, 1.0)
    return -jnp.sum(safe * jnp.log(safe))


def relative_entropy_jax(left: jax.Array, right: jax.Array) -> jax.Array:
    rho = density_from_bloch_jax(left)
    sigma = density_from_bloch_jax(right)
    left_values, left_vectors = jnp.linalg.eigh(rho)
    right_values, right_vectors = jnp.linalg.eigh(sigma)
    left_log = (left_vectors * jnp.log(jnp.clip(jnp.real(left_values), 1.0e-12, 1.0))) @ jnp.conj(left_vectors.T)
    right_log = (right_vectors * jnp.log(jnp.clip(jnp.real(right_values), 1.0e-12, 1.0))) @ jnp.conj(right_vectors.T)
    return jnp.maximum(jnp.real(jnp.trace(rho @ (left_log - right_log))), 0.0)


@jax.jit
def entropy_fingerprint_jax(
    sample_matrices: jax.Array,
    sample_offsets: jax.Array,
    terrain_matrices: jax.Array,
    terrain_offsets: jax.Array,
    terrain_fixed_points: jax.Array,
    probes: jax.Array,
) -> tuple[jax.Array, jax.Array]:
    input_entropy = jax.vmap(entropy_jax)(probes)

    def one_sample(operator_matrix, operator_offset):
        operator_outputs = probes @ operator_matrix.T + operator_offset
        direct_entropy_delta = jax.vmap(entropy_jax)(operator_outputs) - input_entropy

        def one_terrain(terrain_matrix, terrain_offset, fixed):
            terrain_first = probes @ terrain_matrix.T + terrain_offset
            operator_first = operator_outputs
            terrain_after_operator = operator_first @ terrain_matrix.T + terrain_offset
            operator_after_terrain = terrain_first @ operator_matrix.T + operator_offset
            base_u = jax.vmap(lambda vector: relative_entropy_jax(vector, fixed))(terrain_first)
            first_u = jax.vmap(lambda vector: relative_entropy_jax(vector, fixed))(terrain_after_operator)
            second_u = jax.vmap(lambda vector: relative_entropy_jax(vector, fixed))(operator_after_terrain)
            return jnp.stack([first_u - base_u, jnp.abs(first_u - second_u)], axis=-1)

        u_values = jax.vmap(one_terrain)(terrain_matrices, terrain_offsets, terrain_fixed_points)
        return direct_entropy_delta, u_values

    direct, u_values = jax.vmap(one_sample)(sample_matrices, sample_offsets)
    return direct.reshape(-1), jnp.sort(u_values.reshape(-1))


def normalized(vector: np.ndarray) -> np.ndarray:
    norm = float(np.linalg.norm(vector))
    return np.zeros_like(vector) if norm <= FINGERPRINT_EPS else vector / norm


def candidate_arrays(candidate: Candidate) -> tuple[np.ndarray, np.ndarray]:
    return (
        np.stack([sample.matrix for sample in candidate.samples]),
        np.stack([sample.offset for sample in candidate.samples]),
    )


def fixed_direction_dimension(matrix: np.ndarray, tolerance: float) -> int:
    singular_values = np.linalg.svd(matrix - np.eye(3), compute_uv=False)
    return int(np.sum(singular_values <= tolerance))


def fixed_direction_line(matrix: np.ndarray) -> np.ndarray | None:
    _u, singular_values, vh = np.linalg.svd(matrix - np.eye(3))
    if int(np.sum(singular_values <= 1.0e-8)) != 1:
        return None
    return normalize_axis(vh[-1])


def canonical_line(vector: np.ndarray, digits: int = 10) -> tuple[float, float, float]:
    value = normalize_axis(vector)
    pivot = next((index for index, item in enumerate(value) if abs(item) > 1.0e-10), 0)
    if value[pivot] < 0.0:
        value = -value
    return tuple(round(float(item), digits) for item in value)


def geometry_orbit_key(
    fixed_line: np.ndarray,
    automorphisms: Sequence[dict[str, Any]],
) -> tuple[tuple[float, float, float], ...]:
    proper = [row for row in automorphisms if row["determinant"] == 1]
    return tuple(sorted({canonical_line(row["matrix"] @ fixed_line) for row in proper}))


def geometry_lane(
    candidate: Candidate,
    terrains: Sequence[AffineMap],
    probes: np.ndarray,
    spec: dict[str, Any],
) -> dict[str, Any]:
    matrices, offsets = candidate_arrays(candidate)
    physical = physical_summary(candidate, spec["density_tolerance"])
    identity_distances = [float(np.linalg.norm(matrix - np.eye(3)) + np.linalg.norm(offset)) for matrix, offset in zip(matrices, offsets)]
    fixed_dimensions = [fixed_direction_dimension(matrix, spec["identity_tolerance"]) for matrix in matrices]
    fixed_lines = [fixed_direction_line(matrix) for matrix in matrices]
    isometry_residuals = [float(np.linalg.norm(matrix.T @ matrix - np.eye(3))) for matrix in matrices]
    contractions = [float(np.min(np.linalg.svd(matrix, compute_uv=False))) for matrix in matrices]
    nonidentity = max(identity_distances) > spec["identity_tolerance"]
    one_fixed_direction = bool(fixed_dimensions) and all(value == 1 for value in fixed_dimensions)
    if max(isometry_residuals) <= 1.0e-8:
        family = "geometry_isometry_axis"
    elif one_fixed_direction and min(contractions) < 1.0 - 1.0e-8:
        family = "geometry_contraction_axis"
    else:
        family = "geometry_other"
    terrain_matrices = np.stack([terrain.matrix for terrain in terrains])
    terrain_offsets = np.stack([terrain.offset for terrain in terrains])
    fingerprint = np.asarray(
        geometry_fingerprint_jax(
            jnp.asarray(matrices),
            jnp.asarray(offsets),
            jnp.asarray(terrain_matrices),
            jnp.asarray(terrain_offsets),
            jnp.asarray(probes),
        )
    )
    admissible = bool(
        physical["all_samples_cp"]
        and physical["all_samples_unital"]
        and nonidentity
        and one_fixed_direction
        and family in {"geometry_isometry_axis", "geometry_contraction_axis"}
        and np.linalg.norm(fingerprint) > FINGERPRINT_EPS
    )
    reasons = []
    if not physical["all_samples_cp"]:
        reasons.append("non_cp")
    if not physical["all_samples_unital"]:
        reasons.append("nonunital")
    if not nonidentity:
        reasons.append("identity")
    if not one_fixed_direction:
        reasons.append("fixed_direction_dimension_not_one")
    if family == "geometry_other":
        reasons.append("no_axis_family")
    if np.linalg.norm(fingerprint) <= FINGERPRINT_EPS:
        reasons.append("terrain_commutator_fingerprint_zero")
    return {
        "candidate_id": candidate.candidate_id,
        "admissible": admissible,
        "rejection_reasons": reasons,
        "lane_family": family,
        "fixed_direction_dimensions": fixed_dimensions,
        "fixed_direction_line": next((line for line in fixed_lines if line is not None), None),
        "maximum_isometry_residual": max(isometry_residuals),
        "minimum_singular_value": min(contractions),
        "maximum_identity_distance": max(identity_distances),
        "fingerprint_norm": float(np.linalg.norm(fingerprint)),
        "fingerprint": normalized(fingerprint),
        "physical": physical,
    }


def entropy_lane(
    candidate: Candidate,
    terrains: Sequence[AffineMap],
    probes: np.ndarray,
    spec: dict[str, Any],
) -> dict[str, Any]:
    matrices, offsets = candidate_arrays(candidate)
    physical = physical_summary(candidate, spec["density_tolerance"])
    terrain_matrices = np.stack([terrain.matrix for terrain in terrains])
    terrain_offsets = np.stack([terrain.offset for terrain in terrains])
    terrain_fixed_points = np.stack([fixed_point(terrain) for terrain in terrains])
    direct_delta, fingerprint = entropy_fingerprint_jax(
        jnp.asarray(matrices),
        jnp.asarray(offsets),
        jnp.asarray(terrain_matrices),
        jnp.asarray(terrain_offsets),
        jnp.asarray(terrain_fixed_points),
        jnp.asarray(probes),
    )
    direct = np.asarray(direct_delta)
    fingerprint_array = np.asarray(fingerprint)
    entropy_preserved = float(np.max(np.abs(direct))) <= 1.0e-8
    mixing = float(np.min(direct)) >= -1.0e-8 and float(np.max(direct)) > STRICT_ENTROPY
    if mixing:
        family = "entropy_mixing"
    elif entropy_preserved:
        family = "entropy_isospectral"
    else:
        family = "entropy_mixed_direction"
    fingerprint_norm = float(np.linalg.norm(fingerprint_array))
    admissible = bool(
        physical["all_samples_cp"]
        and family in {"entropy_mixing", "entropy_isospectral"}
        and fingerprint_norm > 1.0e-8
    )
    reasons = []
    if not physical["all_samples_cp"]:
        reasons.append("non_cp")
    if family == "entropy_mixed_direction":
        reasons.append("von_neumann_entropy_not_one_direction_or_isospectral")
    if fingerprint_norm <= 1.0e-8:
        reasons.append("terrain_relative_entropy_response_zero")
    return {
        "candidate_id": candidate.candidate_id,
        "admissible": admissible,
        "rejection_reasons": reasons,
        "lane_family": family,
        "direct_entropy_delta_min": float(np.min(direct)),
        "direct_entropy_delta_max": float(np.max(direct)),
        "direct_entropy_delta_max_abs": float(np.max(np.abs(direct))),
        "fingerprint_norm": fingerprint_norm,
        "fingerprint": normalized(fingerprint_array),
        "physical": physical,
    }


def connected_components(rows: Sequence[dict[str, Any]], threshold: float) -> list[list[str]]:
    by_id = {row["candidate_id"]: row for row in rows}
    adjacency = {candidate_id: set() for candidate_id in by_id}
    ids = sorted(by_id)
    for left_index, left_id in enumerate(ids):
        left = by_id[left_id]
        for right_id in ids[left_index + 1 :]:
            right = by_id[right_id]
            if left["lane_family"] != right["lane_family"]:
                continue
            left_fp = left["fingerprint"]
            right_fp = right["fingerprint"]
            if np.linalg.norm(left_fp) <= FINGERPRINT_EPS or np.linalg.norm(right_fp) <= FINGERPRINT_EPS:
                similar = np.linalg.norm(left_fp) <= FINGERPRINT_EPS and np.linalg.norm(right_fp) <= FINGERPRINT_EPS
            else:
                similar = float(np.dot(left_fp, right_fp)) >= threshold
            if similar:
                adjacency[left_id].add(right_id)
                adjacency[right_id].add(left_id)
    components = []
    unseen = set(ids)
    while unseen:
        start = min(unseen)
        stack = [start]
        component = set()
        while stack:
            current = stack.pop()
            if current in component:
                continue
            component.add(current)
            stack.extend(sorted(adjacency[current] - component, reverse=True))
        unseen -= component
        components.append(sorted(component))
    return sorted(components, key=lambda row: tuple(row))


def geometry_components(
    rows: Sequence[dict[str, Any]],
    automorphisms: Sequence[dict[str, Any]],
) -> list[list[str]]:
    groups: dict[tuple[Any, ...], list[str]] = {}
    for row in rows:
        line = row["fixed_direction_line"]
        if line is None:
            key = (row["lane_family"], "no_fixed_line", row["candidate_id"])
        else:
            key = (row["lane_family"], geometry_orbit_key(np.asarray(line), automorphisms))
        groups.setdefault(key, []).append(row["candidate_id"])
    return sorted((sorted(members) for members in groups.values()), key=lambda row: tuple(row))


def partition_key(components: Sequence[Sequence[str]]) -> tuple[tuple[str, ...], ...]:
    return tuple(sorted(tuple(sorted(component)) for component in components))


def restrict_rows(rows: Sequence[dict[str, Any]], ids: set[str]) -> list[dict[str, Any]]:
    return [row for row in rows if row["candidate_id"] in ids]


def run_order(
    order: str,
    geometry_rows: Sequence[dict[str, Any]],
    entropy_rows: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    geometry_by_id = {row["candidate_id"]: row for row in geometry_rows}
    entropy_by_id = {row["candidate_id"]: row for row in entropy_rows}
    ids = sorted(geometry_by_id)
    survivors = set(ids)
    hell = []
    stages = ("geometry", "entropy") if order == "G_then_E" else ("entropy", "geometry")
    for stage in stages:
        lane = geometry_by_id if stage == "geometry" else entropy_by_id
        rejected = []
        for candidate_id in sorted(survivors):
            if not lane[candidate_id]["admissible"]:
                rejected.append(candidate_id)
                hell.append(
                    {
                        "candidate_id": candidate_id,
                        "rejected_by": stage,
                        "reasons": lane[candidate_id]["rejection_reasons"],
                    }
                )
        survivors -= set(rejected)
    return {
        "order": order,
        "semantics": "fixed_extensional_filter_only",
        "survivor_ids": sorted(survivors),
        "survivor_count": len(survivors),
        "hell": hell,
        "hell_count": len(hell),
    }


def summarize_partition(
    components: Sequence[Sequence[str]],
    truth: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        {
            "members": list(component),
            "truth_families_posthoc": sorted({truth[item]["family"] for item in component}),
            "truth_axes_posthoc": sorted({str(truth[item]["axis_registry"]) for item in component}),
            "expected_operators_posthoc": sorted(
                {truth[item]["expected_operator"] for item in component if truth[item].get("expected_operator")}
            ),
        }
        for component in components
    ]


def source_bridge(
    final_components: Sequence[Sequence[str]],
    truth: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    representatives = {}
    for operator, family, axis in (
        ("Ti", "axis_dephasing_path", "pauli_z"),
        ("Te", "axis_dephasing_path", "pauli_x"),
        ("Fi", "axis_rotation_path", "pauli_x"),
        ("Fe", "axis_rotation_path", "pauli_z"),
    ):
        matches = [
            candidate_id
            for candidate_id, metadata in truth.items()
            if metadata["family"] == family and metadata["axis_registry"] == axis
        ]
        if len(matches) != 1:
            raise RuntimeError(f"source bridge could not identify one {operator} representative")
        representatives[operator] = matches[0]
    class_for = {}
    for class_index, component in enumerate(final_components):
        for candidate_id in component:
            class_for[candidate_id] = class_index
    classes = {operator: class_for.get(candidate_id) for operator, candidate_id in representatives.items()}
    return {
        "source_representatives": representatives,
        "source_class_indices": classes,
        "all_four_source_operators_covered": all(value is not None for value in classes.values()),
        "all_four_source_operators_in_distinct_classes": len(set(classes.values())) == 4,
        "transverse_y_candidates_share_Te_Fi_classes": all(
            any(
                truth[candidate_id]["axis_registry"] == "pauli_y"
                and truth[candidate_id]["family"] == family
                and class_for.get(candidate_id) == classes[operator]
                for candidate_id in truth
            )
            for operator, family in (("Te", "axis_dephasing_path"), ("Fi", "axis_rotation_path"))
        ),
        "representative_choice_emitted_by_ratchet": False,
        "representative_choice_note": "x and y are one discovered transverse orbit; choosing x for Te/Fi remains the source gauge convention",
    }


def one_universe(
    spec: dict[str, Any],
    terrains: Sequence[AffineMap],
    automorphisms: dict[str, Any],
    *,
    include_generic_axes: bool,
    erase_rotation_sides: bool = False,
    terrain_override: Sequence[AffineMap] | None = None,
) -> dict[str, Any]:
    candidates, truth = build_candidates(
        spec,
        include_generic_axes=include_generic_axes,
        erase_rotation_sides=erase_rotation_sides,
    )
    active_terrains = list(terrain_override or terrains)
    active_automorphisms = discover_terrain_automorphisms(
        active_terrains,
        spec["automorphism_match_tolerance"],
    )
    seed_runs = []
    for seed in spec["probe_seeds"]:
        probes = symmetry_closed_probes(
            seed,
            spec["probe_base_count"],
            spec["probe_radius_min"],
            spec["probe_radius_max"],
            active_automorphisms["rows"],
        )
        geometry_rows = [geometry_lane(candidate, active_terrains, probes, spec) for candidate in candidates]
        entropy_rows = [entropy_lane(candidate, active_terrains, probes, spec) for candidate in candidates]
        geometry_ids = {row["candidate_id"] for row in geometry_rows if row["admissible"]}
        entropy_ids = {row["candidate_id"] for row in entropy_rows if row["admissible"]}
        intersection = geometry_ids & entropy_ids
        geometry_partition = geometry_components(
            restrict_rows(geometry_rows, intersection),
            active_automorphisms["rows"],
        )
        entropy_partition = connected_components(
            restrict_rows(entropy_rows, intersection),
            spec["fingerprint_cosine_threshold"],
        )
        threshold_rows = []
        for threshold in spec["fingerprint_threshold_sweep"]:
            g_partition = geometry_components(
                restrict_rows(geometry_rows, intersection),
                active_automorphisms["rows"],
            )
            e_partition = connected_components(restrict_rows(entropy_rows, intersection), threshold)
            threshold_rows.append(
                {
                    "threshold": threshold,
                    "geometry_class_count": len(g_partition),
                    "entropy_class_count": len(e_partition),
                    "partitions_agree": partition_key(g_partition) == partition_key(e_partition),
                }
            )
        orders = {
            order: run_order(order, geometry_rows, entropy_rows)
            for order in ("G_then_E", "E_then_G")
        }
        seed_runs.append(
            {
                "seed": seed,
                "probe_count": len(probes),
                "candidate_count": len(candidates),
                "geometry_rows": geometry_rows,
                "entropy_rows": entropy_rows,
                "geometry_survivor_ids": sorted(geometry_ids),
                "entropy_survivor_ids": sorted(entropy_ids),
                "intersection_survivor_ids": sorted(intersection),
                "intersection_survivor_count": len(intersection),
                "geometry_partition": geometry_partition,
                "entropy_partition": entropy_partition,
                "geometry_class_count": len(geometry_partition),
                "entropy_class_count": len(entropy_partition),
                "partitions_agree": partition_key(geometry_partition) == partition_key(entropy_partition),
                "threshold_sweep": threshold_rows,
                "orders": orders,
                "extensional_filter_survivors_agree": orders["G_then_E"]["survivor_ids"]
                == orders["E_then_G"]["survivor_ids"],
                "rejection_attribution_differs_by_filter_order": orders["G_then_E"]["hell"]
                != orders["E_then_G"]["hell"],
                "partition_summary": summarize_partition(geometry_partition, truth),
                "source_bridge": source_bridge(geometry_partition, truth) if not include_generic_axes else None,
            }
        )

    reference_partition = partition_key(seed_runs[0]["geometry_partition"])
    enumeration_checks = []
    reference_rows = seed_runs[0]["geometry_rows"]
    reference_ids = set(seed_runs[0]["intersection_survivor_ids"])
    for enumeration_seed in spec["candidate_enumeration_seeds"]:
        shuffled = list(restrict_rows(reference_rows, reference_ids))
        np.random.default_rng(enumeration_seed).shuffle(shuffled)
        partition = geometry_components(shuffled, active_automorphisms["rows"])
        enumeration_checks.append(
            {
                "seed": enumeration_seed,
                "partition_stable": partition_key(partition) == reference_partition,
            }
        )
    return {
        "include_generic_axes": include_generic_axes,
        "erase_rotation_sides": erase_rotation_sides,
        "terrain_automorphisms": active_automorphisms,
        "candidate_truth_posthoc": truth,
        "seed_runs": seed_runs,
        "all_seed_geometry_partitions_stable": all(
            partition_key(row["geometry_partition"]) == reference_partition for row in seed_runs
        ),
        "all_seed_entropy_partitions_match_geometry": all(row["partitions_agree"] for row in seed_runs),
        "all_seed_extensional_filter_intersections_agree": all(
            row["extensional_filter_survivors_agree"] for row in seed_runs
        ),
        "all_threshold_rows_stable": all(
            item["geometry_class_count"] == seed_runs[0]["geometry_class_count"]
            and item["entropy_class_count"] == seed_runs[0]["entropy_class_count"]
            and item["partitions_agree"]
            for row in seed_runs
            for item in row["threshold_sweep"]
        ),
        "enumeration_checks": enumeration_checks,
        "all_enumeration_partitions_stable": all(row["partition_stable"] for row in enumeration_checks),
        "reference_class_count": seed_runs[0]["geometry_class_count"],
        "reference_intersection_survivor_count": seed_runs[0]["intersection_survivor_count"],
        "reference_partition": seed_runs[0]["geometry_partition"],
    }


def main() -> int:
    spec = json.loads(SPEC_PATH.read_text())
    terrains = terrain_maps()
    automorphisms = discover_terrain_automorphisms(terrains, spec["automorphism_match_tolerance"])

    main_universe = one_universe(
        spec,
        terrains,
        automorphisms,
        include_generic_axes=False,
    )
    generic_challenge = one_universe(
        spec,
        terrains,
        automorphisms,
        include_generic_axes=True,
    )
    side_erasure = one_universe(
        spec,
        terrains,
        automorphisms,
        include_generic_axes=False,
        erase_rotation_sides=True,
    )
    isotropic_terrains = [depolarizing_map(0.45) for _ in terrains]
    terrain_erasure = one_universe(
        spec,
        terrains,
        automorphisms,
        include_generic_axes=False,
        terrain_override=isotropic_terrains,
    )

    main_seed = main_universe["seed_runs"][0]
    main_checks = {
        "target_count_not_supplied_to_selectors": spec["target_survivor_count_supplied_to_selectors"] is False,
        "terrain_automorphism_group_nontrivial": automorphisms["count"] >= 4,
        "proper_terrain_symmetry_has_transverse_xy_and_axial_z_orbits": automorphisms[
            "axis_orbits_zero_based"
        ]
        == [[0, 1], [0, 1], [2]],
        "geometry_and_entropy_intersection_has_four_classes_in_main_registry": main_universe[
            "reference_class_count"
        ]
        == 4,
        "independent_lane_partitions_agree_on_main_registry": main_universe[
            "all_seed_entropy_partitions_match_geometry"
        ],
        "fixed_extensional_filter_orders_share_survivor_intersection": main_universe[
            "all_seed_extensional_filter_intersections_agree"
        ],
        "probe_seed_partitions_stable": main_universe["all_seed_geometry_partitions_stable"],
        "candidate_enumeration_partitions_stable": main_universe["all_enumeration_partitions_stable"],
        "threshold_sweep_partitions_stable": main_universe["all_threshold_rows_stable"],
        "source_representatives_cover_four_distinct_classes": main_seed["source_bridge"][
            "all_four_source_operators_in_distinct_classes"
        ],
        "transverse_y_competitors_quotient_with_source_x_representatives": main_seed["source_bridge"][
            "transverse_y_candidates_share_Te_Fi_classes"
        ],
    }
    falsifier_checks = {
        "generic_axes_add_at_least_one_class": generic_challenge["reference_class_count"] > 4,
        "generic_axis_challenge_blocks_foundational_four": generic_challenge["reference_class_count"]
        != main_universe["reference_class_count"],
        "rotation_side_erasure_changes_entropy_convergence_or_class_count": (
            not side_erasure["all_seed_entropy_partitions_match_geometry"]
            or side_erasure["reference_class_count"] != 4
        ),
        "terrain_isotropy_erasure_changes_class_count_or_survivors": (
            terrain_erasure["reference_class_count"] != 4
            or terrain_erasure["reference_intersection_survivor_count"]
            != main_universe["reference_intersection_survivor_count"]
        ),
        "source_gauge_representative_not_emitted": main_seed["source_bridge"][
            "representative_choice_emitted_by_ratchet"
        ]
        is False,
    }
    conditional_four_observed = all(main_checks.values())
    foundational_four_earned = bool(
        conditional_four_observed and not falsifier_checks["generic_axis_challenge_blocks_foundational_four"]
    )
    all_pass = bool(all(main_checks.values()) and all(falsifier_checks.values()) and not foundational_four_earned)
    result = {
        "schema": "codex_ratchet.dual_ratchet_substage_survivor_discovery_v0.jax_result.v1",
        "sim_id": spec["sim_id"],
        "classification": classification,
        "promotion_allowed": promotion_allowed,
        "formal_admission_allowed": formal_admission_allowed,
        "stage_movement_allowed": stage_movement_allowed,
        "sim_execution_kind": sim_execution_kind,
        "engine_mode": spec["engine_mode"],
        "reads_peer_result": False,
        "source_hashes": {
            str(SPEC_PATH.relative_to(REPO)): sha256(SPEC_PATH),
            str(Path(__file__).resolve().relative_to(REPO)): sha256(Path(__file__).resolve()),
            str(BASE_PATH.relative_to(REPO)): sha256(BASE_PATH),
        },
        "scientific_question": spec["scientific_question"],
        "premise_boundary": {
            "eight_house_terrain_flows_are_input": True,
            "finite_candidate_family_registry_is_input": True,
            "finite_pauli_axis_registry_is_main_universe_input": True,
            "generic_axis_challenge_is_required": True,
            "candidate_names_hidden_from_selectors": True,
            "desired_survivor_count_supplied": False,
            "full_R1_R6_history_dependent_ratchet_tested": False,
        },
        "terrain_automorphisms": automorphisms,
        "main_pauli_registry": compact_result(main_universe),
        "generic_axis_challenge": compact_result(generic_challenge),
        "rotation_side_erasure_control": compact_result(side_erasure),
        "terrain_isotropy_erasure_control": compact_result(terrain_erasure),
        "main_checks": main_checks,
        "falsifier_checks": falsifier_checks,
        "conditional_four_class_quotient_observed": conditional_four_observed,
        "foundational_four_substage_emergence_earned": foundational_four_earned,
        "history_dependent_dual_ratchet_tested": False,
        "bidirectional_ratchet_earned": False,
        "per_stage_four_substages_earned": False,
        "filter_order_semantics": "The two orders apply fixed extensional predicates, so their common survivor intersection is plumbing, not a noncommuting ratchet result.",
        "scientific_verdict": "conditional_pauli_registry_four_class_operator_quotient_only"
        if conditional_four_observed and not foundational_four_earned
        else "main_candidate_failed_or_unconditional_result_requires_audit",
        "all_pass": all_pass,
        "accepted_status_label": "passes local rerun" if all_pass else "local candidate gate failed",
        "jax": {
            "ran": True,
            "version": jax.__version__,
            "x64": bool(jax.config.jax_enable_x64),
            "devices": [device.platform for device in jax.devices()],
            "source_path": str(Path(__file__).resolve()),
            "packages_used": ["jax", "jax.numpy", "numpy", "scipy.optimize.linear_sum_assignment"],
            "aligned_packages_load_bearing": ["jax", "scipy.optimize.linear_sum_assignment"],
            "reads_peer_result": False,
        },
        "package_fingerprint": {
            "python": sys.version,
            "jax": jax.__version__,
            "numpy": np.__version__,
            "scipy": importlib.metadata.version("scipy"),
        },
        "tool_calls": [
            {
                "tool": "jax",
                "function": "jax.vmap + jax.numpy.linalg.eigh",
                "input_object": "anonymous channel-family samples x exact terrain affine maps x symmetry-closed density probes",
                "output_object": "independent commutator and entropy/Umegaki fingerprints",
                "positive_case": "lane partitions agree on the main Pauli registry",
                "negative_control": "terrain-isotropy and rotation-side erasures change the quotient",
                "boundary_case": "generic axes remain visible and block foundational emergence",
                "demotion_condition": "lane, seed, order, threshold, or control failure",
                "gates": ["conditional_four_class_quotient_observed", "all_pass"],
            },
            {
                "tool": "scipy.optimize.linear_sum_assignment",
                "function": "linear_sum_assignment",
                "input_object": "signed-permutation conjugates of the eight exact terrain affine maps",
                "output_object": "terrain-set automorphism matches and axis orbits",
                "positive_case": "proper symmetry discovers x/y as one orbit and z as another",
                "negative_control": "isotropic terrain erasure changes the quotient",
                "boundary_case": "only transformations matching the full affine-map multiset at tolerance are admitted",
                "demotion_condition": "no nontrivial exact automorphism or match error above tolerance",
                "gates": ["terrain_automorphism_group_nontrivial", "all_pass"],
            },
        ],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "claim_ceiling": spec["claim_ceiling"],
        "eligible_consumers": ["bounded four-operator-class coverage hypothesis"],
        "blocked_consumers": [
            "unconditional four-substage emergence",
            "four history-dependent substages inside each of 16 stages",
            "source-gauge representative selection",
            "full R1-R6 ratchet admission",
            "canonical QIT engine admission",
            "Type-1/Type-2 scientific intelligence",
            "Axis0 alignment or entropy theorem",
            "perception, objects, MMMs, or ontology authority",
            "Leviathan mesh mutation",
        ],
    }
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(jsonable(result), indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "result_path": str(RESULT_PATH),
                "automorphisms": automorphisms["count"],
                "proper_axis_orbits": automorphisms["axis_orbits_zero_based"],
                "main_classes": main_universe["reference_class_count"],
                "generic_challenge_classes": generic_challenge["reference_class_count"],
                "conditional_four": conditional_four_observed,
                "foundational_four": foundational_four_earned,
                "all_pass": all_pass,
            },
            indent=2,
        )
    )
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
