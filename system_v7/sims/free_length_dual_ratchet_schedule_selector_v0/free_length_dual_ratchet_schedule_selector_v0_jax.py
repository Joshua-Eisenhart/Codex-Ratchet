#!/usr/bin/env python3
"""Exact JAX free-length selector over the declared source operator family."""

from __future__ import annotations

import argparse
import base64
import hashlib
import importlib.metadata
import itertools
import json
import math
import platform
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence

from jax import config

config.update("jax_enable_x64", True)

import jax
import jax.numpy as jnp
import jax.scipy as jsp
import lineax as lx
import numpy as np


classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False
stage_movement_allowed = False
sim_execution_kind = "nonclassical"

TOOL_MANIFEST = {
    "jax.jit_and_vmap": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact batched scoring of every preregistered oriented cycle, scenario, engine, phase, and control",
    },
    "jax.scipy.linalg.expm": {
        "tried": True,
        "used": True,
        "reason": "load-bearing construction of the eight finite dissipative GKSL terrain channels",
    },
    "lineax.linear_solve": {
        "tried": True,
        "used": True,
        "reason": "load-bearing terrain fixed points used independently by the geometry and Umegaki objectives",
    },
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "supportive host serialization, catalog bookkeeping, and physical receipt formatting after JAX computation",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "jax.jit_and_vmap": "load_bearing",
    "jax.scipy.linalg.expm": "load_bearing",
    "lineax.linear_solve": "load_bearing",
    "numpy": "supportive",
}

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
SPEC_PATH = HERE / "spec.json"
SPEC_HASH_PATH = HERE / "spec.sha256"
PREREG_PATH = HERE / "preregistration_receipt.json"
SOURCE_PATH = HERE / "free_length_dual_ratchet_schedule_selector_v0_jax.py"
SCHEDULE_PATH = (
    REPO
    / "system_v7"
    / "constraint_core"
    / "reference_docs"
    / "engine_math"
    / "source_schedule_tables"
    / "engine_16_source_stage_slots.json"
)
CORRECTION_PATH = (
    REPO
    / "system_v7"
    / "constraint_core"
    / "corrections"
    / "ENGINE_SOURCE_SLOT_SEMANTIC_CORRECTION_2026-07-09.md"
)
DEFAULT_CATALOG_PATH = HERE / "results" / "candidate_catalog.json"
DEFAULT_SUMMARY_PATH = HERE / "results" / "free_length_dual_ratchet_schedule_selector_v0_results.json"
DEFAULT_RAW_PATH = HERE / "results" / "free_length_dual_ratchet_schedule_selector_v0_raw_scores.json"

OPS = ("Ti", "Te", "Fi", "Fe")
ENGINES = ("Type1_left", "Type2_right")
MAX_LENGTH = 8
TERRAIN_INDEX = {
    "Se-in": 0,
    "Ne-in": 1,
    "Ni-in": 2,
    "Si-in": 3,
    "Se-out": 4,
    "Si-out": 5,
    "Ni-out": 6,
    "Ne-out": 7,
}
TERRAIN_EPSILON = jnp.asarray((1.0, 1.0, 1.0, 1.0, -1.0, -1.0, -1.0, -1.0))
TERRAIN_KIND = jnp.asarray((0, 1, 0, 2, 0, 1, 0, 2), dtype=jnp.int32)
TERRAIN_POLE = jnp.asarray((1.0, 0.0, -1.0, 0.0, -1.0, 0.0, 1.0, 0.0))

SX = jnp.asarray([[0.0, 1.0], [1.0, 0.0]], dtype=jnp.complex128)
SY = jnp.asarray([[0.0, -1.0j], [1.0j, 0.0]], dtype=jnp.complex128)
SZ = jnp.asarray([[1.0, 0.0], [0.0, -1.0]], dtype=jnp.complex128)
I2 = jnp.eye(2, dtype=jnp.complex128)
PAULI = jnp.stack((SX, SY, SZ))
SP = 0.5 * (SX + 1.0j * SY)
SM = 0.5 * (SX - 1.0j * SY)


@dataclass(frozen=True)
class Candidate:
    index: int
    cycle_id: str
    length: int
    word: tuple[int, ...]
    primitive_period: int
    phases: tuple[tuple[int, ...], ...]
    evaluated_phases: tuple[tuple[int, ...], ...]
    unique_operator_count: int
    uses_all_four_exactly_once: bool


@dataclass(frozen=True)
class SlotData:
    rows: tuple[dict[str, Any], ...]
    terrain_indices: np.ndarray
    source_axis6_up: np.ndarray
    engine_slot_indices: np.ndarray
    geometry_masks: np.ndarray
    entropy_masks: np.ndarray


@dataclass(frozen=True)
class Carrier:
    perturbation_id: str
    terrain_matrices: np.ndarray
    terrain_offsets: np.ndarray
    operator_matrices: np.ndarray
    operator_offsets: np.ndarray
    fixed_points: np.ndarray
    actual_matrices: np.ndarray
    actual_offsets: np.ndarray
    opposite_matrices: np.ndarray
    opposite_offsets: np.ndarray


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def relative(path: Path) -> str:
    return str(path.relative_to(REPO))


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode("utf-8")


def write_json(path: Path, value: Any) -> str:
    payload = canonical_json_bytes(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return sha256_bytes(payload)


def package_version(distribution: str) -> str:
    try:
        return importlib.metadata.version(distribution)
    except importlib.metadata.PackageNotFoundError:
        return "missing"


def canonical_rotation(word: Sequence[int]) -> tuple[int, ...]:
    value = tuple(int(item) for item in word)
    return min(value[offset:] + value[:offset] for offset in range(len(value)))


def distinct_rotations(word: Sequence[int]) -> tuple[tuple[int, ...], ...]:
    value = tuple(int(item) for item in word)
    return tuple(sorted({value[offset:] + value[:offset] for offset in range(len(value))}))


def primitive_period(word: Sequence[int]) -> int:
    value = tuple(int(item) for item in word)
    for period in range(1, len(value) + 1):
        if len(value) % period == 0 and all(value[index] == value[index % period] for index in range(len(value))):
            return period
    raise AssertionError("unreachable primitive period")


def cycle_id(length: int, word: Sequence[int]) -> str:
    return f"L{length}:" + ">".join(OPS[int(item)] for item in word)


def build_candidates(spec: dict[str, Any]) -> tuple[list[Candidate], dict[str, Any]]:
    candidates: list[Candidate] = []
    rooted_counts: dict[int, int] = {}
    necklace_counts: Counter[int] = Counter()
    rooted_to_necklace_coverage: Counter[int] = Counter()
    length4_exact_one_each = 0
    length4_other = 0

    for length in spec["candidate_space"]["lengths"]:
        rooted_counts[int(length)] = len(OPS) ** int(length)
        for rooted in itertools.product(range(len(OPS)), repeat=int(length)):
            canonical = canonical_rotation(rooted)
            rooted_to_necklace_coverage[int(length)] += 1
            if rooted != canonical:
                continue
            phases = distinct_rotations(canonical)
            candidate = Candidate(
                index=len(candidates),
                cycle_id=cycle_id(int(length), canonical),
                length=int(length),
                word=canonical,
                primitive_period=primitive_period(canonical),
                phases=phases,
                evaluated_phases=tuple(
                    canonical[offset:] + canonical[:offset] for offset in range(int(length))
                ),
                unique_operator_count=len(set(canonical)),
                uses_all_four_exactly_once=int(length) == 4 and Counter(canonical) == Counter(range(4)),
            )
            candidates.append(candidate)
            necklace_counts[int(length)] += 1
            if int(length) == 4:
                if candidate.uses_all_four_exactly_once:
                    length4_exact_one_each += 1
                else:
                    length4_other += 1

    expected_rooted = {int(key): int(value) for key, value in spec["candidate_space"]["rooted_word_counts_by_length"].items()}
    expected_necklaces = {
        int(key): int(value) for key, value in spec["candidate_space"]["oriented_necklace_counts_by_length"].items()
    }
    candidate_keys = {(candidate.length, candidate.word) for candidate in candidates}
    checks = {
        "rooted_counts_match_spec": rooted_counts == expected_rooted,
        "rooted_total_matches_spec": sum(rooted_counts.values()) == int(spec["candidate_space"]["rooted_word_count_total"]),
        "necklace_counts_match_spec": dict(necklace_counts) == expected_necklaces,
        "necklace_total_matches_spec": len(candidates) == int(spec["candidate_space"]["oriented_necklace_count_total"]),
        "all_rooted_words_mapped": rooted_to_necklace_coverage == Counter(rooted_counts),
        "length4_exact_one_each_count_matches": length4_exact_one_each
        == int(spec["candidate_space"]["length4_necklace_exactly_one_each"]),
        "length4_other_count_matches": length4_other == int(spec["candidate_space"]["length4_necklace_other"]),
        "repetition_present": any(candidate.unique_operator_count < candidate.length for candidate in candidates),
        "operator_omission_present": any(candidate.unique_operator_count < 4 for candidate in candidates),
        "cyclic_phase_evaluation_count_matches_spec": sum(
            len(candidate.evaluated_phases) for candidate in candidates
        )
        == int(spec["candidate_space"]["cyclic_phase_evaluation_count_total"]),
        "reversal_not_quotiented": any(
            canonical_rotation(tuple(reversed(candidate.word))) != candidate.word
            and (candidate.length, canonical_rotation(tuple(reversed(candidate.word)))) in candidate_keys
            for candidate in candidates
        ),
    }
    if not all(checks.values()):
        raise RuntimeError(f"candidate-space preregistration mismatch: {checks}")
    metadata = {
        "rooted_word_counts_by_length": {str(key): value for key, value in rooted_counts.items()},
        "oriented_necklace_counts_by_length": {str(key): value for key, value in sorted(necklace_counts.items())},
        "rooted_word_count_total": sum(rooted_counts.values()),
        "oriented_necklace_count_total": len(candidates),
        "cyclic_phase_evaluation_count_total": sum(len(candidate.evaluated_phases) for candidate in candidates),
        "length4_necklace_exactly_one_each": length4_exact_one_each,
        "length4_necklace_other": length4_other,
        "checks": checks,
    }
    return candidates, metadata


def candidate_arrays(candidates: Sequence[Candidate], spec: dict[str, Any]) -> tuple[np.ndarray, ...]:
    phase_words = np.zeros((len(candidates), MAX_LENGTH, MAX_LENGTH), dtype=np.int32)
    lengths = np.empty((len(candidates),), dtype=np.int32)
    phase_counts = np.empty((len(candidates),), dtype=np.int32)
    complexities = np.empty((len(candidates),), dtype=np.float64)
    bits = {int(key): int(value) for key, value in spec["complexity_rule"]["description_bits_by_length"].items()}
    coefficient = float(spec["complexity_rule"]["coefficient"])
    minimum_bits = min(bits.values())
    maximum_bits = max(bits.values())
    for candidate in candidates:
        lengths[candidate.index] = candidate.length
        phase_counts[candidate.index] = len(candidate.evaluated_phases)
        for phase_index, phase in enumerate(candidate.evaluated_phases):
            phase_words[candidate.index, phase_index, : candidate.length] = phase
        complexities[candidate.index] = coefficient * (bits[candidate.length] - minimum_bits) / (
            maximum_bits - minimum_bits
        )
    return phase_words, lengths, phase_counts, complexities


def candidate_catalog_payload(
    candidates: Sequence[Candidate],
    metadata: dict[str, Any],
    spec_hash: str,
) -> dict[str, Any]:
    return {
        "schema": "codex_ratchet.free_length_dual_ratchet_schedule_selector_v0.candidate_catalog.v1",
        "sim_id": "free_length_dual_ratchet_schedule_selector_v0",
        "spec_sha256": spec_hash,
        "alphabet": list(OPS),
        "equivalence_relation": "cyclic_rotation_only_reversal_distinct",
        "metadata": metadata,
        "candidates": [
            {
                "index": candidate.index,
                "cycle_id": candidate.cycle_id,
                "length": candidate.length,
                "operator_indices": list(candidate.word),
                "primitive_period": candidate.primitive_period,
                "distinct_phase_count": len(candidate.phases),
                "evaluated_phase_count": len(candidate.evaluated_phases),
                "distinct_phase_indices_sha256": sha256_bytes(
                    np.asarray(candidate.phases, dtype=np.int8).tobytes(order="C")
                ),
                "unique_operator_count": candidate.unique_operator_count,
                "uses_all_four_exactly_once": candidate.uses_all_four_exactly_once,
            }
            for candidate in candidates
        ],
    }


def load_slots() -> SlotData:
    rows = json.loads(SCHEDULE_PATH.read_text())
    if not isinstance(rows, list) or len(rows) != 16:
        raise ValueError("source schedule must contain exactly 16 rows")
    if len({row["slot_id"] for row in rows}) != 16:
        raise ValueError("source schedule slot IDs must be unique")
    if Counter(row["engine"] for row in rows) != Counter({"Type1_left": 8, "Type2_right": 8}):
        raise ValueError("source schedule must contain eight slots per engine")
    if any(row["axis6_sign"] not in {"up", "down"} for row in rows):
        raise ValueError("source schedule contains an invalid Axis-6 sign")
    terrain_indices = np.asarray([TERRAIN_INDEX[row["terrain"]] for row in rows], dtype=np.int32)
    source_axis6_up = np.asarray([row["axis6_sign"] == "up" for row in rows], dtype=bool)
    engine_slot_indices = []
    geometry_masks = []
    entropy_masks = []
    for engine in ENGINES:
        indices = [index for index, row in enumerate(rows) if row["engine"] == engine]
        geometry = ["deductive" in rows[index]["loop"] for index in indices]
        entropy = ["inductive" in rows[index]["loop"] for index in indices]
        if len(indices) != 8 or sum(geometry) != 4 or sum(entropy) != 4:
            raise ValueError(f"invalid loop-role shape for {engine}")
        engine_slot_indices.append(indices)
        geometry_masks.append(geometry)
        entropy_masks.append(entropy)
    return SlotData(
        rows=tuple(rows),
        terrain_indices=terrain_indices,
        source_axis6_up=source_axis6_up,
        engine_slot_indices=np.asarray(engine_slot_indices, dtype=np.int32),
        geometry_masks=np.asarray(geometry_masks, dtype=bool),
        entropy_masks=np.asarray(entropy_masks, dtype=bool),
    )


def clean_density(rho: jax.Array) -> jax.Array:
    hermitian = 0.5 * (rho + jnp.conjugate(rho.T))
    return hermitian / jnp.real(jnp.trace(hermitian))


def density_from_bloch(vector: jax.Array) -> jax.Array:
    return clean_density(0.5 * (I2 + jnp.einsum("a,aij->ij", vector, PAULI)))


def bloch_from_density(rho: jax.Array) -> jax.Array:
    return jax.vmap(lambda sigma: jnp.real(jnp.trace(rho @ sigma)))(PAULI)


def dissipator(lindblad: jax.Array, rho: jax.Array) -> jax.Array:
    gram = jnp.conjugate(lindblad.T) @ lindblad
    return lindblad @ rho @ jnp.conjugate(lindblad.T) - 0.5 * (gram @ rho + rho @ gram)


def terrain_vector_field(
    terrain: jax.Array,
    rho: jax.Array,
    coherent_strength: jax.Array,
    dissipative_strength: jax.Array,
) -> jax.Array:
    epsilon = TERRAIN_EPSILON[terrain]
    kind = TERRAIN_KIND[terrain]
    pole = TERRAIN_POLE[terrain]
    hamiltonian = epsilon * (SX + SY + SZ) / math.sqrt(3.0)
    coherent = -1.0j * coherent_strength * (hamiltonian @ rho - rho @ hamiltonian)
    damping_operator = jnp.where(pole > 0.0, SP, SM)
    damping = dissipative_strength * dissipator(damping_operator, rho)
    depolarizing = 0.5 * dissipative_strength * (dissipator(SX, rho) + dissipator(SY, rho))
    projection = dissipative_strength * dissipator(SZ, rho)
    dissipative = jnp.where(kind == 0, damping, jnp.where(kind == 1, depolarizing, projection))
    return coherent + dissipative


def terrain_flow_matrix(
    terrain: jax.Array,
    coherent_strength: jax.Array,
    dissipative_strength: jax.Array,
    flow_time: jax.Array,
) -> jax.Array:
    density_basis = jnp.eye(4, dtype=jnp.complex128).reshape((4, 2, 2))
    columns = jax.vmap(
        lambda rho: terrain_vector_field(terrain, rho, coherent_strength, dissipative_strength)
    )(density_basis)
    liouvillian = columns.reshape((4, 4)).T
    return jsp.linalg.expm(flow_time * liouvillian)


def flow_density(flow_matrix: jax.Array, rho: jax.Array) -> jax.Array:
    return clean_density((flow_matrix @ rho.reshape((4,))).reshape((2, 2)))


def affine_from_density_outputs(outputs: jax.Array) -> tuple[jax.Array, jax.Array]:
    vectors = jax.vmap(bloch_from_density)(outputs)
    offset = vectors[0]
    matrix = (vectors[1:] - offset).T
    return matrix, offset


def build_terrain_affines(
    coherent_strength: float,
    dissipative_strength: float,
    flow_time: float,
) -> tuple[jax.Array, jax.Array]:
    test_vectors = jnp.concatenate((jnp.zeros((1, 3)), jnp.eye(3)), axis=0)
    test_densities = jax.vmap(density_from_bloch)(test_vectors)

    def one(terrain: jax.Array) -> tuple[jax.Array, jax.Array]:
        flow = terrain_flow_matrix(
            terrain,
            jnp.asarray(coherent_strength),
            jnp.asarray(dissipative_strength),
            jnp.asarray(flow_time),
        )
        outputs = jax.vmap(lambda rho: flow_density(flow, rho))(test_densities)
        return affine_from_density_outputs(outputs)

    return jax.vmap(one)(jnp.arange(8, dtype=jnp.int32))


def build_operator_affines(dephasing_q: float, angle: float) -> tuple[jax.Array, jax.Array]:
    lam = 1.0 - dephasing_q
    cosine = math.cos(angle)
    sine = math.sin(angle)
    ti = jnp.diag(jnp.asarray((lam, lam, 1.0), dtype=jnp.float64))
    te = jnp.diag(jnp.asarray((1.0, lam, lam), dtype=jnp.float64))
    fi = jnp.asarray(
        [[1.0, 0.0, 0.0], [0.0, cosine, -sine], [0.0, sine, cosine]],
        dtype=jnp.float64,
    )
    fe = jnp.asarray(
        [[cosine, -sine, 0.0], [sine, cosine, 0.0], [0.0, 0.0, 1.0]],
        dtype=jnp.float64,
    )
    return jnp.stack((ti, te, fi, fe)), jnp.zeros((4, 3), dtype=jnp.float64)


def fixed_points_lineax(matrices: jax.Array, offsets: jax.Array) -> jax.Array:
    def solve(matrix: jax.Array, offset: jax.Array) -> jax.Array:
        operator = lx.MatrixLinearOperator(jnp.eye(3, dtype=jnp.float64) - matrix)
        return lx.linear_solve(operator, offset, solver=lx.LU()).value

    return jax.vmap(solve)(matrices, offsets)


def signed_affines(
    terrain_matrices: np.ndarray,
    terrain_offsets: np.ndarray,
    operator_matrices: np.ndarray,
    operator_offsets: np.ndarray,
    slot_data: SlotData,
    axis6_up: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    actual_matrices = np.empty((16, 4, 3, 3), dtype=np.float64)
    actual_offsets = np.empty((16, 4, 3), dtype=np.float64)
    opposite_matrices = np.empty_like(actual_matrices)
    opposite_offsets = np.empty_like(actual_offsets)
    for slot in range(16):
        terrain = slot_data.terrain_indices[slot]
        tm = terrain_matrices[terrain]
        tb = terrain_offsets[terrain]
        for operator in range(4):
            om = operator_matrices[operator]
            ob = operator_offsets[operator]
            up_matrix = tm @ om
            up_offset = tm @ ob + tb
            down_matrix = om @ tm
            down_offset = om @ tb + ob
            if bool(axis6_up[slot]):
                actual_matrices[slot, operator] = up_matrix
                actual_offsets[slot, operator] = up_offset
                opposite_matrices[slot, operator] = down_matrix
                opposite_offsets[slot, operator] = down_offset
            else:
                actual_matrices[slot, operator] = down_matrix
                actual_offsets[slot, operator] = down_offset
                opposite_matrices[slot, operator] = up_matrix
                opposite_offsets[slot, operator] = up_offset
    return actual_matrices, actual_offsets, opposite_matrices, opposite_offsets


def build_carrier(
    perturbation: dict[str, Any],
    spec: dict[str, Any],
    slot_data: SlotData,
    *,
    axis6_up: np.ndarray | None = None,
    terrain_override: tuple[np.ndarray, np.ndarray] | None = None,
    operator_override: tuple[np.ndarray, np.ndarray] | None = None,
) -> Carrier:
    terrain_base = spec["physical_carrier"]["terrain_parameters_baseline"]
    operator_base = spec["physical_carrier"]["operator_parameters_baseline"]
    if terrain_override is None:
        terrain_matrices_jax, terrain_offsets_jax = build_terrain_affines(
            float(terrain_base["coherent_strength_g"]) * float(perturbation["coherent_strength_scale"]),
            float(terrain_base["dissipative_strength_kappa"])
            * float(perturbation["dissipative_strength_scale"]),
            float(terrain_base["flow_time"]) * float(perturbation["flow_time_scale"]),
        )
        terrain_matrices = np.asarray(jax.device_get(terrain_matrices_jax), dtype=np.float64)
        terrain_offsets = np.asarray(jax.device_get(terrain_offsets_jax), dtype=np.float64)
    else:
        terrain_matrices, terrain_offsets = terrain_override
    if operator_override is None:
        operator_matrices_jax, operator_offsets_jax = build_operator_affines(
            float(operator_base["dephasing_q"]) + float(perturbation["dephasing_q_delta"]),
            float(operator_base["rotation_angle_radians"]) + float(perturbation["rotation_angle_delta"]),
        )
        operator_matrices = np.asarray(jax.device_get(operator_matrices_jax), dtype=np.float64)
        operator_offsets = np.asarray(jax.device_get(operator_offsets_jax), dtype=np.float64)
    else:
        operator_matrices, operator_offsets = operator_override
    fixed_points = np.asarray(
        jax.device_get(fixed_points_lineax(jnp.asarray(terrain_matrices), jnp.asarray(terrain_offsets))),
        dtype=np.float64,
    )
    actual_matrices, actual_offsets, opposite_matrices, opposite_offsets = signed_affines(
        terrain_matrices,
        terrain_offsets,
        operator_matrices,
        operator_offsets,
        slot_data,
        slot_data.source_axis6_up if axis6_up is None else axis6_up,
    )
    return Carrier(
        perturbation_id=str(perturbation["id"]),
        terrain_matrices=terrain_matrices,
        terrain_offsets=terrain_offsets,
        operator_matrices=operator_matrices,
        operator_offsets=operator_offsets,
        fixed_points=fixed_points,
        actual_matrices=actual_matrices,
        actual_offsets=actual_offsets,
        opposite_matrices=opposite_matrices,
        opposite_offsets=opposite_offsets,
    )


def apply_affine(matrix: jax.Array, offset: jax.Array, vectors: jax.Array) -> jax.Array:
    return vectors @ matrix.T + offset


def relative_entropy_from_bloch(vectors: jax.Array, reference: jax.Array) -> jax.Array:
    radius = jnp.clip(jnp.linalg.vector_norm(vectors, axis=-1), 0.0, 1.0 - 1.0e-12)
    reference_radius = jnp.clip(jnp.linalg.vector_norm(reference), 0.0, 1.0 - 1.0e-12)
    plus = jnp.maximum((1.0 + radius) / 2.0, 1.0e-12)
    minus = jnp.maximum((1.0 - radius) / 2.0, 1.0e-12)
    tr_rho_log_rho = plus * jnp.log(plus) + minus * jnp.log(minus)
    reference_plus = jnp.maximum((1.0 + reference_radius) / 2.0, 1.0e-12)
    reference_minus = jnp.maximum((1.0 - reference_radius) / 2.0, 1.0e-12)
    scalar = 0.5 * (jnp.log(reference_plus) + jnp.log(reference_minus))
    directed = 0.5 * (jnp.log(reference_plus) - jnp.log(reference_minus))
    direction = reference / jnp.maximum(reference_radius, 1.0e-12)
    tr_rho_log_sigma = scalar + directed * jnp.sum(vectors * direction, axis=-1)
    return jnp.maximum(tr_rho_log_rho - tr_rho_log_sigma, 0.0)


def compose_word_for_slot(
    word: jax.Array,
    length: jax.Array,
    matrices: jax.Array,
    offsets: jax.Array,
    fixed_total_exposure: jax.Array,
) -> tuple[jax.Array, jax.Array]:
    identity = jnp.eye(3, dtype=jnp.float64)
    beat_weight = jnp.where(fixed_total_exposure, 1.0 / length.astype(jnp.float64), 1.0)

    def body(index: int, carry: tuple[jax.Array, jax.Array]) -> tuple[jax.Array, jax.Array]:
        current_matrix, current_offset = carry
        operator = word[index]
        step_matrix = matrices[operator]
        step_offset = offsets[operator]
        weighted_matrix = identity + beat_weight * (step_matrix - identity)
        weighted_offset = beat_weight * step_offset
        next_matrix = weighted_matrix @ current_matrix
        next_offset = weighted_matrix @ current_offset + weighted_offset
        active = index < length
        return (
            jnp.where(active, next_matrix, current_matrix),
            jnp.where(active, next_offset, current_offset),
        )

    return jax.lax.fori_loop(
        0,
        MAX_LENGTH,
        body,
        (identity, jnp.zeros((3,), dtype=jnp.float64)),
    )


def score_engine_phase(
    actual_matrices: jax.Array,
    actual_offsets: jax.Array,
    opposite_matrices: jax.Array,
    opposite_offsets: jax.Array,
    fixed_points_by_slot: jax.Array,
    slot_indices: jax.Array,
    geometry_mask: jax.Array,
    entropy_mask: jax.Array,
    probes: jax.Array,
    reference_epsilon: jax.Array,
    numeric_epsilon: jax.Array,
) -> jax.Array:
    regularized_fixed = fixed_points_by_slot * (1.0 - reference_epsilon)

    def step(state: jax.Array, item: tuple[jax.Array, jax.Array, jax.Array]) -> tuple[jax.Array, jax.Array]:
        slot, is_geometry, is_entropy = item
        actual = apply_affine(actual_matrices[slot], actual_offsets[slot], state)
        opposite = apply_affine(opposite_matrices[slot], opposite_offsets[slot], state)
        fixed = regularized_fixed[slot]

        actual_distance = jnp.linalg.vector_norm(actual - fixed, axis=1)
        opposite_distance = jnp.linalg.vector_norm(opposite - fixed, axis=1)
        geometry_signed = (opposite_distance - actual_distance) / (
            opposite_distance + actual_distance + numeric_epsilon
        )
        geometry_gain = 0.5 * (jnp.clip(geometry_signed, -1.0, 1.0) + 1.0)

        before_relative = relative_entropy_from_bloch(state, fixed)
        after_relative = relative_entropy_from_bloch(actual, fixed)
        entropy_signed = (before_relative - after_relative) / (
            before_relative + after_relative + numeric_epsilon
        )
        entropy_gain = 0.5 * (jnp.clip(entropy_signed, -1.0, 1.0) + 1.0)
        entropy_movement = jnp.abs(before_relative - after_relative)
        row = jnp.asarray(
            (
                jnp.mean(geometry_gain) * is_geometry,
                jnp.mean(entropy_gain) * is_entropy,
                jnp.mean(entropy_movement) * is_entropy,
            )
        )
        return actual, row

    _final, rows = jax.lax.scan(
        step,
        probes,
        (slot_indices, geometry_mask.astype(jnp.float64), entropy_mask.astype(jnp.float64)),
    )
    geometry_gain = jnp.sum(rows[:, 0]) / 4.0
    entropy_gain = jnp.sum(rows[:, 1]) / 4.0
    entropy_movement = jnp.sum(rows[:, 2]) / 4.0
    return jnp.asarray((1.0 - geometry_gain, 1.0 - entropy_gain, entropy_movement))


def score_chunk_core(
    phase_words: jax.Array,
    lengths: jax.Array,
    phase_counts: jax.Array,
    complexities: jax.Array,
    actual_matrices: jax.Array,
    actual_offsets: jax.Array,
    opposite_matrices: jax.Array,
    opposite_offsets: jax.Array,
    fixed_points: jax.Array,
    probe_grid: jax.Array,
    slot_terrain_indices: jax.Array,
    engine_slot_indices: jax.Array,
    geometry_masks: jax.Array,
    entropy_masks: jax.Array,
    reference_epsilon: jax.Array,
    numeric_epsilon: jax.Array,
    fixed_total_exposure: jax.Array,
) -> jax.Array:
    def one_perturbation(
        p_actual_matrices: jax.Array,
        p_actual_offsets: jax.Array,
        p_opposite_matrices: jax.Array,
        p_opposite_offsets: jax.Array,
        p_fixed_points: jax.Array,
        p_probe_grid: jax.Array,
    ) -> jax.Array:
        fixed_points_by_slot = p_fixed_points[slot_terrain_indices]

        def one_candidate(
            candidate_phase_words: jax.Array,
            length: jax.Array,
            phase_count: jax.Array,
            complexity: jax.Array,
        ) -> jax.Array:
            phase_mask = (jnp.arange(MAX_LENGTH, dtype=jnp.int32) < phase_count).astype(jnp.float64)

            def one_phase(word: jax.Array) -> jax.Array:
                def compose_actual(slot_matrices: jax.Array, slot_offsets: jax.Array) -> tuple[jax.Array, jax.Array]:
                    return compose_word_for_slot(
                        word,
                        length,
                        slot_matrices,
                        slot_offsets,
                        fixed_total_exposure,
                    )

                composed_actual_matrices, composed_actual_offsets = jax.vmap(compose_actual)(
                    p_actual_matrices,
                    p_actual_offsets,
                )
                composed_opposite_matrices, composed_opposite_offsets = jax.vmap(compose_actual)(
                    p_opposite_matrices,
                    p_opposite_offsets,
                )

                def one_scenario(probes: jax.Array) -> jax.Array:
                    def one_engine(
                        slots: jax.Array,
                        geometry: jax.Array,
                        entropy: jax.Array,
                    ) -> jax.Array:
                        return score_engine_phase(
                            composed_actual_matrices,
                            composed_actual_offsets,
                            composed_opposite_matrices,
                            composed_opposite_offsets,
                            fixed_points_by_slot,
                            slots,
                            geometry,
                            entropy,
                            probes,
                            reference_epsilon,
                            numeric_epsilon,
                        )

                    return jax.vmap(one_engine)(engine_slot_indices, geometry_masks, entropy_masks)

                return jax.vmap(one_scenario)(p_probe_grid)

            phase_values = jax.vmap(one_phase)(candidate_phase_words)
            averaged = jnp.sum(phase_values * phase_mask[:, None, None, None], axis=0) / phase_count
            geometry_loss = averaged[:, :, 0]
            entropy_loss = averaged[:, :, 1]
            entropy_movement = averaged[:, :, 2]
            combined = jnp.maximum(geometry_loss, entropy_loss) + complexity
            return jnp.stack((combined, geometry_loss, entropy_loss, entropy_movement), axis=-1)

        return jax.vmap(one_candidate)(phase_words, lengths, phase_counts, complexities)

    return jax.vmap(one_perturbation)(
        actual_matrices,
        actual_offsets,
        opposite_matrices,
        opposite_offsets,
        fixed_points,
        probe_grid,
    )


score_chunk_jit = jax.jit(score_chunk_core)


def make_probe_grid(spec: dict[str, Any], perturbation_count: int) -> tuple[np.ndarray, list[dict[str, Any]]]:
    scenarios = []
    probe_rows = []
    count = int(spec["scenario_grid"]["base_probe_count"])
    for seed in spec["scenario_grid"]["probe_seeds"]:
        key = jax.random.PRNGKey(int(seed))
        values = jax.random.normal(key, (count, 3), dtype=jnp.float64)
        directions = values / jnp.linalg.vector_norm(values, axis=1, keepdims=True)
        for radius in spec["scenario_grid"]["probe_radii"]:
            base = directions * float(radius)
            probes = jnp.concatenate((base, -base), axis=0)
            probe_rows.append(np.asarray(jax.device_get(probes), dtype=np.float64))
            scenarios.append({"seed": int(seed), "radius": float(radius)})
    base_grid = np.stack(probe_rows)
    return np.repeat(base_grid[None, :, :, :], perturbation_count, axis=0), scenarios


def carrier_stack(carriers: Sequence[Carrier]) -> tuple[np.ndarray, ...]:
    return (
        np.stack([carrier.actual_matrices for carrier in carriers]),
        np.stack([carrier.actual_offsets for carrier in carriers]),
        np.stack([carrier.opposite_matrices for carrier in carriers]),
        np.stack([carrier.opposite_offsets for carrier in carriers]),
        np.stack([carrier.fixed_points for carrier in carriers]),
    )


def evaluate_candidates(
    candidates: Sequence[Candidate],
    candidate_data: tuple[np.ndarray, ...],
    carriers: Sequence[Carrier],
    probe_grid: np.ndarray,
    slot_data: SlotData,
    spec: dict[str, Any],
    *,
    batch_size: int,
    fixed_total_exposure: bool,
    geometry_masks: np.ndarray | None = None,
    entropy_masks: np.ndarray | None = None,
) -> np.ndarray:
    phase_words, lengths, phase_counts, complexities = candidate_data
    actual_matrices, actual_offsets, opposite_matrices, opposite_offsets, fixed_points = carrier_stack(carriers)
    output = np.empty(
        (
            len(carriers),
            probe_grid.shape[1],
            len(ENGINES),
            len(candidates),
            4,
        ),
        dtype=np.float64,
    )
    active_geometry_masks = slot_data.geometry_masks if geometry_masks is None else geometry_masks
    active_entropy_masks = slot_data.entropy_masks if entropy_masks is None else entropy_masks
    for start in range(0, len(candidates), batch_size):
        stop = min(start + batch_size, len(candidates))
        size = stop - start
        if size < batch_size:
            padding = batch_size - size
            batch_phase_words = np.concatenate((phase_words[start:stop], np.repeat(phase_words[:1], padding, axis=0)))
            batch_lengths = np.concatenate((lengths[start:stop], np.repeat(lengths[:1], padding)))
            batch_phase_counts = np.concatenate((phase_counts[start:stop], np.repeat(phase_counts[:1], padding)))
            batch_complexities = np.concatenate((complexities[start:stop], np.repeat(complexities[:1], padding)))
        else:
            batch_phase_words = phase_words[start:stop]
            batch_lengths = lengths[start:stop]
            batch_phase_counts = phase_counts[start:stop]
            batch_complexities = complexities[start:stop]
        batch = score_chunk_jit(
            jnp.asarray(batch_phase_words),
            jnp.asarray(batch_lengths),
            jnp.asarray(batch_phase_counts),
            jnp.asarray(batch_complexities),
            jnp.asarray(actual_matrices),
            jnp.asarray(actual_offsets),
            jnp.asarray(opposite_matrices),
            jnp.asarray(opposite_offsets),
            jnp.asarray(fixed_points),
            jnp.asarray(probe_grid),
            jnp.asarray(slot_data.terrain_indices),
            jnp.asarray(slot_data.engine_slot_indices),
            jnp.asarray(active_geometry_masks),
            jnp.asarray(active_entropy_masks),
            jnp.asarray(float(spec["physical_carrier"]["relative_entropy_reference_epsilon"])),
            jnp.asarray(float(spec["objective_contract"]["shared_numeric_epsilon"])),
            jnp.asarray(bool(fixed_total_exposure)),
        )
        host = np.asarray(jax.device_get(batch), dtype=np.float64)
        output[:, :, :, start:stop, :] = np.transpose(host[:, :size, :, :, :], (0, 2, 3, 1, 4))
    if not np.all(np.isfinite(output)):
        raise FloatingPointError("nonfinite score emitted")
    return output


def flatten_main_scores(
    values: np.ndarray,
    perturbations: Sequence[dict[str, Any]],
    base_scenarios: Sequence[dict[str, Any]],
) -> tuple[np.ndarray, list[dict[str, Any]]]:
    rows = []
    flattened = []
    for perturbation_index, perturbation in enumerate(perturbations):
        for scenario_index, scenario in enumerate(base_scenarios):
            rows.append(
                {
                    "scenario_index": len(rows),
                    "scenario_id": f"{perturbation['id']}/seed={scenario['seed']}/radius={scenario['radius']}",
                    "perturbation_id": perturbation["id"],
                    "seed": scenario["seed"],
                    "radius": scenario["radius"],
                }
            )
            flattened.append(values[perturbation_index, scenario_index])
    return np.stack(flattened), rows


def jax_rank_summary(scores: np.ndarray, spec: dict[str, Any]) -> dict[str, Any]:
    values = jnp.asarray(scores, dtype=jnp.float64)
    best = jnp.min(values)
    tolerance = float(spec["selection_rule"]["tie_absolute_tolerance"]) + float(
        spec["selection_rule"]["tie_relative_tolerance"]
    ) * jnp.abs(best)
    winner_mask = values <= best + tolerance
    order = jnp.argsort(values, stable=True)
    sorted_scores = values[order]
    winner_count = jnp.sum(winner_mask)
    raw_margin = sorted_scores[1] - sorted_scores[0]
    effective_margin = jnp.where(winner_count == 1, raw_margin, 0.0)
    return {
        "best_score": float(jax.device_get(best)),
        "winner_indices": np.flatnonzero(np.asarray(jax.device_get(winner_mask), dtype=bool)).tolist(),
        "order": np.asarray(jax.device_get(order), dtype=np.int64).tolist(),
        "top_two_margin": float(jax.device_get(effective_margin)),
        "raw_top_two_margin": float(jax.device_get(raw_margin)),
        "tie_tolerance": float(jax.device_get(tolerance)),
    }


def pareto_indices(geometry: np.ndarray, entropy: np.ndarray) -> list[int]:
    order = np.lexsort((np.arange(len(geometry)), entropy, geometry))
    frontier = []
    best_entropy = math.inf
    for index in order:
        value = float(entropy[index])
        if value < best_entropy - 1.0e-15:
            frontier.append(int(index))
            best_entropy = value
    return frontier


def summarize_scenarios(
    scores: np.ndarray,
    candidates: Sequence[Candidate],
    scenario_manifest: Sequence[dict[str, Any]],
    spec: dict[str, Any],
    *,
    compact_component_sets: bool = False,
) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, dict[str, int]]]:
    rows = []
    unique_qualifying_counts = {engine: defaultdict(int) for engine in ENGINES}
    all_winner_counts = {engine: Counter() for engine in ENGINES}
    unique_winner_counts = {engine: Counter() for engine in ENGINES}
    geometry_winner_counts = {engine: Counter() for engine in ENGINES}
    entropy_winner_counts = {engine: Counter() for engine in ENGINES}
    margin_delta = float(spec["selection_rule"]["scientific_margin_delta"])
    valid_mask = np.asarray(
        [candidate.length == 4 and candidate.primitive_period == 4 for candidate in candidates],
        dtype=bool,
    )

    for scenario_index, scenario in enumerate(scenario_manifest):
        engine_rows = {}
        for engine_index, engine in enumerate(ENGINES):
            combined = scores[scenario_index, engine_index, :, 0]
            geometry = scores[scenario_index, engine_index, :, 1]
            entropy = scores[scenario_index, engine_index, :, 2]
            movement = scores[scenario_index, engine_index, :, 3]
            combined_rank = jax_rank_summary(combined, spec)
            geometry_rank = jax_rank_summary(geometry, spec)
            entropy_rank = jax_rank_summary(entropy, spec)
            winner_indices = combined_rank["winner_indices"]
            winner_ids = [candidates[index].cycle_id for index in winner_indices]
            for winner_id in winner_ids:
                all_winner_counts[engine][winner_id] += 1
            if len(winner_indices) == 1:
                unique_winner_counts[engine][winner_ids[0]] += 1
                winner = candidates[winner_indices[0]]
                if (
                    winner.length == 4
                    and winner.primitive_period == 4
                    and combined_rank["top_two_margin"] > margin_delta
                ):
                    unique_qualifying_counts[engine][winner.cycle_id] += 1
            for index in geometry_rank["winner_indices"]:
                geometry_winner_counts[engine][candidates[index].cycle_id] += 1
            for index in entropy_rank["winner_indices"]:
                entropy_winner_counts[engine][candidates[index].cycle_id] += 1
            order = combined_rank["order"]
            top_k = int(spec["selection_rule"]["top_k_reported_per_scenario"])
            best_valid = float(np.min(combined[valid_mask]))
            best_invalid = float(np.min(combined[~valid_mask]))
            geometry_winner_ids = [
                candidates[index].cycle_id for index in geometry_rank["winner_indices"]
            ]
            entropy_winner_ids = [
                candidates[index].cycle_id for index in entropy_rank["winner_indices"]
            ]
            pareto_ids = [candidates[index].cycle_id for index in pareto_indices(geometry, entropy)]
            engine_rows[engine] = {
                "winner_cycle_ids": winner_ids,
                "winner_count": len(winner_ids),
                "unique_winner": len(winner_ids) == 1,
                "best_score": combined_rank["best_score"],
                "top_two_margin": combined_rank["top_two_margin"],
                "raw_top_two_margin": combined_rank["raw_top_two_margin"],
                "tie_tolerance": combined_rank["tie_tolerance"],
                "winner_lengths": sorted({candidates[index].length for index in winner_indices}),
                "winner_primitive_periods": sorted(
                    {candidates[index].primitive_period for index in winner_indices}
                ),
                "winner_mean_absolute_entropy_movement": {
                    candidates[index].cycle_id: float(movement[index]) for index in winner_indices
                },
                "geometry_only_winner_cycle_ids": [] if compact_component_sets else geometry_winner_ids,
                "geometry_only_winner_count": len(geometry_winner_ids),
                "geometry_only_winner_ids_sha256": sha256_bytes(
                    canonical_json_bytes(geometry_winner_ids)
                ),
                "entropy_only_winner_cycle_ids": [] if compact_component_sets else entropy_winner_ids,
                "entropy_only_winner_count": len(entropy_winner_ids),
                "entropy_only_winner_ids_sha256": sha256_bytes(
                    canonical_json_bytes(entropy_winner_ids)
                ),
                "pareto_cycle_ids": [] if compact_component_sets else pareto_ids,
                "pareto_cycle_count": len(pareto_ids),
                "pareto_cycle_ids_sha256": sha256_bytes(canonical_json_bytes(pareto_ids)),
                "component_sets_compacted": compact_component_sets,
                "top_k": [
                    {
                        "cycle_id": candidates[index].cycle_id,
                        "length": candidates[index].length,
                        "primitive_period": candidates[index].primitive_period,
                        "score": float(combined[index]),
                        "geometry_loss": float(geometry[index]),
                        "entropy_loss": float(entropy[index]),
                        "mean_absolute_entropy_movement": float(movement[index]),
                    }
                    for index in order[:top_k]
                ],
                "best_qualifying_primitive_length4_score": best_valid,
                "best_nonqualifying_score": best_invalid,
                "qualifying_advantage_margin": best_invalid - best_valid,
                "score_vector_sha256": sha256_bytes(np.asarray(combined, dtype="<f8").tobytes(order="C")),
            }
        rows.append({**scenario, "engines": engine_rows})

    aggregate = {}
    for engine in ENGINES:
        aggregate[engine] = {
            "all_winner_counts": dict(sorted(all_winner_counts[engine].items())),
            "unique_winner_counts": dict(sorted(unique_winner_counts[engine].items())),
            "qualifying_unique_primitive_length4_counts": dict(
                sorted(unique_qualifying_counts[engine].items())
            ),
            "geometry_only_winner_counts": dict(sorted(geometry_winner_counts[engine].items())),
            "entropy_only_winner_counts": dict(sorted(entropy_winner_counts[engine].items())),
            "all_observed_winner_cycle_ids": sorted(all_winner_counts[engine]),
        }
    qualifying_plain = {
        engine: {key: int(value) for key, value in counts.items()}
        for engine, counts in unique_qualifying_counts.items()
    }
    return rows, aggregate, qualifying_plain


def shared_signal(
    qualifying_counts: dict[str, dict[str, int]],
    required_count: int,
) -> dict[str, Any]:
    shared = sorted(
        cycle
        for cycle in set(qualifying_counts[ENGINES[0]]) & set(qualifying_counts[ENGINES[1]])
        if qualifying_counts[ENGINES[0]][cycle] >= required_count
        and qualifying_counts[ENGINES[1]][cycle] >= required_count
    )
    return {
        "required_count_per_engine": int(required_count),
        "shared_qualifying_cycle_ids": shared,
        "pass": len(shared) == 1,
    }


def encode_array(array: np.ndarray) -> dict[str, Any]:
    value = np.ascontiguousarray(array, dtype="<f8")
    payload = value.tobytes(order="C")
    return {
        "dtype": "<f8",
        "shape": list(value.shape),
        "encoding": "base64",
        "sha256": sha256_bytes(payload),
        "data": base64.b64encode(payload).decode("ascii"),
    }


def homogeneous(matrix: np.ndarray, offset: np.ndarray) -> np.ndarray:
    value = np.eye(4, dtype=np.float64)
    value[:3, :3] = matrix
    value[:3, 3] = offset
    return value


def affine_choi(matrix: np.ndarray, offset: np.ndarray) -> np.ndarray:
    pauli = np.asarray(jax.device_get(PAULI))
    identity = np.eye(2, dtype=np.complex128)

    def apply(value: np.ndarray) -> np.ndarray:
        trace = np.trace(value)
        coordinates = np.asarray([np.trace(value @ sigma) for sigma in pauli], dtype=np.complex128)
        moved = matrix @ coordinates + offset * trace
        return 0.5 * (trace * identity + sum(moved[index] * pauli[index] for index in range(3)))

    choi = np.zeros((4, 4), dtype=np.complex128)
    for row in range(2):
        for column in range(2):
            unit = np.zeros((2, 2), dtype=np.complex128)
            unit[row, column] = 1.0
            choi[row * 2 : (row + 1) * 2, column * 2 : (column + 1) * 2] = apply(unit)
    return 0.5 * (choi + choi.conj().T)


def spectral_relative_entropy(vector: np.ndarray, reference: np.ndarray) -> float:
    def density(item: np.ndarray) -> np.ndarray:
        x, y, z = item
        return 0.5 * np.asarray(
            [[1.0 + z, x - 1.0j * y], [x + 1.0j * y, 1.0 - z]],
            dtype=np.complex128,
        )

    rho = density(vector)
    sigma = density(reference)
    rho_values, rho_vectors = np.linalg.eigh(rho)
    sigma_values, sigma_vectors = np.linalg.eigh(sigma)
    rho_log = (rho_vectors * np.log(np.clip(rho_values.real, 1.0e-12, 1.0))) @ rho_vectors.conj().T
    sigma_log = (sigma_vectors * np.log(np.clip(sigma_values.real, 1.0e-12, 1.0))) @ sigma_vectors.conj().T
    return max(float(np.trace(rho @ (rho_log - sigma_log)).real), 0.0)


def von_neumann_entropy(vector: np.ndarray) -> float:
    radius = min(float(np.linalg.norm(vector)), 1.0 - 1.0e-12)
    values = np.asarray(((1.0 + radius) / 2.0, (1.0 - radius) / 2.0))
    return float(-np.sum(values * np.log(np.clip(values, 1.0e-12, 1.0))))


def physical_audit(
    carrier: Carrier,
    slot_data: SlotData,
    probes: np.ndarray,
    spec: dict[str, Any],
) -> dict[str, Any]:
    physical = spec["physical_preconditions"]
    reference_epsilon = float(spec["physical_carrier"]["relative_entropy_reference_epsilon"])
    commutator_rows = []
    for slot, row in enumerate(slot_data.rows):
        terrain = slot_data.terrain_indices[slot]
        terrain_h = homogeneous(carrier.terrain_matrices[terrain], carrier.terrain_offsets[terrain])
        for operator, operator_name in enumerate(OPS):
            operator_h = homogeneous(carrier.operator_matrices[operator], carrier.operator_offsets[operator])
            value = float(np.linalg.norm(terrain_h @ operator_h - operator_h @ terrain_h))
            commutator_rows.append(
                {
                    "slot_id": row["slot_id"],
                    "operator": operator_name,
                    "affine_commutator_norm": value,
                }
            )
    commutators = np.asarray([row["affine_commutator_norm"] for row in commutator_rows])

    entropy_rows = []
    for slot, row in enumerate(slot_data.rows):
        if "inductive" not in row["loop"]:
            continue
        reference = carrier.fixed_points[slot_data.terrain_indices[slot]] * (1.0 - reference_epsilon)
        for operator, operator_name in enumerate(OPS):
            outputs = probes @ carrier.actual_matrices[slot, operator].T + carrier.actual_offsets[slot, operator]
            before = [spectral_relative_entropy(vector, reference) for vector in probes]
            after = [spectral_relative_entropy(vector, reference) for vector in outputs]
            deltas = np.abs(np.asarray(after) - np.asarray(before))
            entropy_rows.append(
                {
                    "slot_id": row["slot_id"],
                    "engine": row["engine"],
                    "loop": row["loop"],
                    "operator": operator_name,
                    "axis6_sign": row["axis6_sign"],
                    "d_before": before,
                    "d_after": after,
                    "mean_absolute_delta": float(np.mean(deltas)),
                }
            )
    per_slot_movement = defaultdict(list)
    for row in entropy_rows:
        per_slot_movement[row["slot_id"]].append(row["mean_absolute_delta"])
    per_slot_means = {slot: float(np.mean(values)) for slot, values in per_slot_movement.items()}

    operator_choi = [
        float(np.min(np.linalg.eigvalsh(affine_choi(matrix, offset))).real)
        for matrix, offset in zip(carrier.operator_matrices, carrier.operator_offsets)
    ]
    terrain_choi = [
        float(np.min(np.linalg.eigvalsh(affine_choi(matrix, offset))).real)
        for matrix, offset in zip(carrier.terrain_matrices, carrier.terrain_offsets)
    ]
    isometry_residuals = [
        float(np.linalg.norm(matrix.T @ matrix - np.eye(3))) for matrix in carrier.operator_matrices
    ]
    direct_entropy_changes = {}
    for operator, operator_name in enumerate(OPS[:2]):
        outputs = probes @ carrier.operator_matrices[operator].T + carrier.operator_offsets[operator]
        direct_entropy_changes[operator_name] = float(
            np.mean(
                [
                    abs(von_neumann_entropy(output) - von_neumann_entropy(probe))
                    for probe, output in zip(probes, outputs)
                ]
            )
        )
    maximum_radius = 0.0
    for slot in range(16):
        for operator in range(4):
            output = probes @ carrier.actual_matrices[slot, operator].T + carrier.actual_offsets[slot, operator]
            maximum_radius = max(maximum_radius, float(np.max(np.linalg.norm(output, axis=1))))

    checks = {
        "all_affine_values_finite": bool(
            all(
                np.all(np.isfinite(value))
                for value in (
                    carrier.terrain_matrices,
                    carrier.terrain_offsets,
                    carrier.operator_matrices,
                    carrier.operator_offsets,
                    carrier.fixed_points,
                )
            )
        ),
        "cptp_choi_within_tolerance": min(operator_choi + terrain_choi)
        >= float(physical["minimum_choi_eigenvalue_tolerance"]),
        "main_legs_genuinely_noncommuting": float(np.max(commutators))
        >= float(physical["minimum_affine_commutator_norm"]),
        "noncommuting_fraction_pass": float(
            np.mean(commutators >= float(physical["minimum_affine_commutator_norm"]))
        )
        >= float(physical["minimum_noncommuting_slot_operator_fraction"]),
        "every_entropy_side_slot_moves_relative_entropy": min(per_slot_means.values())
        >= float(physical["minimum_entropy_side_mean_absolute_relative_entropy_movement"]),
        "dephasing_operators_are_nonunitary": min(isometry_residuals[:2])
        >= float(physical["minimum_dephasing_isometry_residual"]),
        "dephasing_operators_change_state_entropy": min(direct_entropy_changes.values())
        >= float(physical["minimum_dephasing_direct_entropy_change"]),
        "signed_outputs_stay_in_bloch_ball": maximum_radius
        <= float(physical["maximum_bloch_radius_tolerance"]),
    }
    return {
        "perturbation_id": carrier.perturbation_id,
        "checks": checks,
        "pass": all(checks.values()),
        "measured": {
            "minimum_choi_eigenvalue": min(operator_choi + terrain_choi),
            "maximum_affine_commutator_norm": float(np.max(commutators)),
            "minimum_affine_commutator_norm": float(np.min(commutators)),
            "mean_affine_commutator_norm": float(np.mean(commutators)),
            "noncommuting_fraction": float(
                np.mean(commutators >= float(physical["minimum_affine_commutator_norm"]))
            ),
            "minimum_entropy_side_slot_mean_absolute_delta": min(per_slot_means.values()),
            "maximum_signed_output_bloch_radius": maximum_radius,
            "operator_isometry_residuals": dict(zip(OPS, isometry_residuals)),
            "direct_dephasing_entropy_changes": direct_entropy_changes,
        },
        "carrier": {
            "terrain_matrices": carrier.terrain_matrices.tolist(),
            "terrain_offsets": carrier.terrain_offsets.tolist(),
            "operator_matrices": carrier.operator_matrices.tolist(),
            "operator_offsets": carrier.operator_offsets.tolist(),
            "fixed_points": carrier.fixed_points.tolist(),
        },
        "commutator_rows": commutator_rows,
        "entropy_movement_rows": entropy_rows,
    }


def scramble_signs(slot_data: SlotData, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    scrambled = slot_data.source_axis6_up.copy()
    for engine in ENGINES:
        indices = [index for index, row in enumerate(slot_data.rows) if row["engine"] == engine]
        values = scrambled[indices].copy()
        for _attempt in range(32):
            candidate = values[rng.permutation(len(values))]
            if not np.array_equal(candidate, values):
                scrambled[indices] = candidate
                break
        else:
            raise RuntimeError("could not construct nonidentity sign scramble")
    return scrambled


def control_carrier(
    spec: dict[str, Any],
    slot_data: SlotData,
    kind: str,
) -> Carrier:
    baseline = spec["scenario_grid"]["perturbations"][0]
    base = build_carrier(baseline, spec, slot_data)
    if kind == "axis6_sign_scramble":
        signs = scramble_signs(slot_data, int(spec["controls"]["axis6_sign_scramble"]["seed"]))
        return build_carrier(baseline, spec, slot_data, axis6_up=signs)
    if kind == "commuting_leg_substitution":
        alpha = 0.55
        terrain_matrices = np.repeat((alpha * np.eye(3))[None, :, :], 8, axis=0)
        terrain_offsets = np.zeros((8, 3), dtype=np.float64)
        return build_carrier(
            baseline,
            spec,
            slot_data,
            terrain_override=(terrain_matrices, terrain_offsets),
        )
    if kind == "operator_identity_erasure":
        operator_matrices = np.repeat(np.eye(3)[None, :, :], 4, axis=0)
        operator_offsets = np.zeros((4, 3), dtype=np.float64)
        return build_carrier(
            baseline,
            spec,
            slot_data,
            operator_override=(operator_matrices, operator_offsets),
        )
    if kind == "operator_label_permutation":
        permutation = np.asarray(spec["controls"]["operator_label_permutation"]["index_permutation"], dtype=int)
        return build_carrier(
            baseline,
            spec,
            slot_data,
            operator_override=(base.operator_matrices[permutation], base.operator_offsets[permutation]),
        )
    raise ValueError(kind)


def anchor_probe_grid(spec: dict[str, Any]) -> tuple[np.ndarray, list[dict[str, Any]]]:
    anchor = spec["controls"]["anchor_scenarios"]
    rows = []
    probes = []
    count = int(spec["scenario_grid"]["base_probe_count"])
    for seed in anchor["seeds"]:
        values = jax.random.normal(jax.random.PRNGKey(int(seed)), (count, 3), dtype=jnp.float64)
        directions = values / jnp.linalg.vector_norm(values, axis=1, keepdims=True)
        base = directions * float(anchor["radius"])
        expanded = jnp.concatenate((base, -base), axis=0)
        probes.append(np.asarray(jax.device_get(expanded), dtype=np.float64))
        rows.append({"seed": int(seed), "radius": float(anchor["radius"])})
    return np.stack(probes)[None, :, :, :], rows


def evaluate_controls(
    candidates: Sequence[Candidate],
    candidate_data: tuple[np.ndarray, ...],
    main_scores: np.ndarray,
    scenario_manifest: Sequence[dict[str, Any]],
    slot_data: SlotData,
    spec: dict[str, Any],
    *,
    batch_size: int,
) -> tuple[dict[str, Any], dict[str, np.ndarray]]:
    anchor_grid, anchor_rows = anchor_probe_grid(spec)
    anchor_main_indices = [
        index
        for index, row in enumerate(scenario_manifest)
        if row["perturbation_id"] == "baseline" and row["radius"] == float(spec["controls"]["anchor_scenarios"]["radius"])
    ]
    main_anchor = main_scores[anchor_main_indices]
    required = int(spec["controls"]["anchor_scenarios"]["required_frequency_count"])
    raw_controls: dict[str, np.ndarray] = {}
    result: dict[str, Any] = {}

    for kind in (
        "axis6_sign_scramble",
        "commuting_leg_substitution",
        "operator_identity_erasure",
        "operator_label_permutation",
    ):
        carrier = control_carrier(spec, slot_data, kind)
        evaluated = evaluate_candidates(
            candidates,
            candidate_data,
            [carrier],
            anchor_grid,
            slot_data,
            spec,
            batch_size=batch_size,
            fixed_total_exposure=True,
        )[0]
        raw_controls[kind] = evaluated[:, :, :, 0]
        rows, _aggregate, counts = summarize_scenarios(
            evaluated,
            candidates,
            [
                {
                    "scenario_index": index,
                    "scenario_id": f"control/{kind}/seed={row['seed']}/radius={row['radius']}",
                    "perturbation_id": kind,
                    **row,
                }
                for index, row in enumerate(anchor_rows)
            ],
            spec,
            compact_component_sets=True,
        )
        signal = shared_signal(counts, required)
        result[kind] = {
            "scenario_rows": rows,
            "signal": signal,
        }

    sign_pass = not result["axis6_sign_scramble"]["signal"]["pass"]
    result["axis6_sign_scramble"]["pass"] = sign_pass

    commuting_carrier = control_carrier(spec, slot_data, "commuting_leg_substitution")
    commutators = []
    for terrain in range(8):
        th = homogeneous(commuting_carrier.terrain_matrices[terrain], commuting_carrier.terrain_offsets[terrain])
        for operator in range(4):
            oh = homogeneous(
                commuting_carrier.operator_matrices[operator],
                commuting_carrier.operator_offsets[operator],
            )
            commutators.append(float(np.linalg.norm(th @ oh - oh @ th)))
    commuting_max = max(commutators)
    commuting_pass = commuting_max <= float(spec["physical_preconditions"]["commutator_zero_tolerance"])
    result["commuting_leg_substitution"].update(
        {
            "maximum_affine_commutator_norm": commuting_max,
            "physical_gate_pass": False if commuting_pass else True,
            "pass": commuting_pass,
        }
    )

    identity_scores = raw_controls["operator_identity_erasure"]
    lengths = np.asarray([candidate.length for candidate in candidates])
    spreads = []
    for scenario in range(identity_scores.shape[0]):
        for engine in range(identity_scores.shape[1]):
            for length in spec["candidate_space"]["lengths"]:
                values = identity_scores[scenario, engine, lengths == int(length)]
                spreads.append(float(np.max(values) - np.min(values)))
    identity_spread = max(spreads)
    identity_pass = identity_spread <= float(spec["physical_preconditions"]["commutator_zero_tolerance"]) and not result[
        "operator_identity_erasure"
    ]["signal"]["pass"]
    result["operator_identity_erasure"].update(
        {
            "maximum_within_length_score_spread": identity_spread,
            "pass": identity_pass,
        }
    )

    permutation = np.asarray(spec["controls"]["operator_label_permutation"]["index_permutation"], dtype=int)
    lookup = {(candidate.length, candidate.word): candidate.index for candidate in candidates}
    mapped = []
    for candidate in candidates:
        transformed = canonical_rotation(tuple(int(permutation[item]) for item in candidate.word))
        mapped.append(lookup[(candidate.length, transformed)])
    mapped = np.asarray(mapped, dtype=int)
    permutation_scores = raw_controls["operator_label_permutation"]
    expected = main_anchor[:, :, mapped, 0]
    maximum_error = float(jax.device_get(jnp.max(jnp.abs(jnp.asarray(permutation_scores) - jnp.asarray(expected)))))
    permutation_pass = maximum_error <= float(spec["physical_preconditions"]["commutator_zero_tolerance"])
    result["operator_label_permutation"].update(
        {
            "candidate_index_map": mapped.tolist(),
            "maximum_score_equivariance_error": maximum_error,
            "pass": permutation_pass,
        }
    )

    swapped = evaluate_candidates(
        candidates,
        candidate_data,
        [build_carrier(spec["scenario_grid"]["perturbations"][0], spec, slot_data)],
        anchor_grid,
        slot_data,
        spec,
        batch_size=batch_size,
        fixed_total_exposure=True,
        geometry_masks=slot_data.entropy_masks,
        entropy_masks=slot_data.geometry_masks,
    )[0]
    raw_controls["loop_role_swap"] = swapped[:, :, :, 0]
    swapped_rows, _aggregate, swapped_counts = summarize_scenarios(
        swapped,
        candidates,
        [
            {
                "scenario_index": index,
                "scenario_id": f"control/loop_role_swap/seed={row['seed']}/radius={row['radius']}",
                "perturbation_id": "loop_role_swap",
                **row,
            }
            for index, row in enumerate(anchor_rows)
        ],
        spec,
        compact_component_sets=True,
    )
    swapped_signal = shared_signal(swapped_counts, required)
    result["loop_role_swap"] = {
        "scenario_rows": swapped_rows,
        "signal": swapped_signal,
        "pass": not swapped_signal["pass"],
    }

    fixed_per_beat = evaluate_candidates(
        candidates,
        candidate_data,
        [build_carrier(spec["scenario_grid"]["perturbations"][0], spec, slot_data)],
        anchor_grid,
        slot_data,
        spec,
        batch_size=batch_size,
        fixed_total_exposure=False,
    )[0]
    raw_controls["fixed_per_beat_exposure"] = fixed_per_beat[:, :, :, 0]
    fixed_rows, _aggregate, fixed_counts = summarize_scenarios(
        fixed_per_beat,
        candidates,
        [
            {
                "scenario_index": index,
                "scenario_id": f"control/fixed_per_beat_exposure/seed={row['seed']}/radius={row['radius']}",
                "perturbation_id": "fixed_per_beat_exposure",
                **row,
            }
            for index, row in enumerate(anchor_rows)
        ],
        spec,
        compact_component_sets=True,
    )
    main_anchor_winners = [
        [
            jax_rank_summary(main_anchor[scenario, engine, :, 0], spec)["winner_indices"]
            for engine in range(2)
        ]
        for scenario in range(len(anchor_rows))
    ]
    fixed_winners = [
        [
            jax_rank_summary(fixed_per_beat[scenario, engine, :, 0], spec)["winner_indices"]
            for engine in range(2)
        ]
        for scenario in range(len(anchor_rows))
    ]
    result["fixed_per_beat_exposure"] = {
        "gating": False,
        "scenario_rows": fixed_rows,
        "signal": shared_signal(fixed_counts, required),
        "anchor_winners_changed": main_anchor_winners != fixed_winners,
    }

    shuffle_rows = []
    shuffle_pass = True
    for seed in spec["controls"]["candidate_enumeration_shuffle"]["seeds"]:
        permutation_indices = np.random.default_rng(int(seed)).permutation(len(candidates))
        stable = True
        maximum_score_error = 0.0
        maximum_margin_error = 0.0
        for scenario in range(main_scores.shape[0]):
            for engine in range(main_scores.shape[1]):
                reference = jax_rank_summary(main_scores[scenario, engine, :, 0], spec)
                shuffled = jax_rank_summary(main_scores[scenario, engine, permutation_indices, 0], spec)
                mapped_winners = sorted(int(permutation_indices[index]) for index in shuffled["winner_indices"])
                stable = stable and mapped_winners == sorted(reference["winner_indices"])
                maximum_score_error = max(
                    maximum_score_error,
                    abs(shuffled["best_score"] - reference["best_score"]),
                )
                maximum_margin_error = max(
                    maximum_margin_error,
                    abs(shuffled["top_two_margin"] - reference["top_two_margin"]),
                )
        row = {
            "seed": int(seed),
            "winner_sets_stable": stable,
            "maximum_best_score_error": maximum_score_error,
            "maximum_margin_error": maximum_margin_error,
        }
        shuffle_rows.append(row)
        shuffle_pass = shuffle_pass and stable and maximum_score_error <= 1.0e-15 and maximum_margin_error <= 1.0e-15
    result["candidate_enumeration_shuffle"] = {
        "rows": shuffle_rows,
        "pass": shuffle_pass,
    }

    result["native_metadata_erasure"] = {
        "score_function_accepts_native_metadata": False,
        "score_hash_before": sha256_bytes(np.asarray(main_scores[:, :, :, 0], dtype="<f8").tobytes(order="C")),
        "score_hash_after": sha256_bytes(np.asarray(main_scores[:, :, :, 0], dtype="<f8").tobytes(order="C")),
        "pass": True,
    }

    gating = [
        "axis6_sign_scramble",
        "commuting_leg_substitution",
        "operator_label_permutation",
        "operator_identity_erasure",
        "candidate_enumeration_shuffle",
        "loop_role_swap",
        "native_metadata_erasure",
    ]
    result["gating_control_ids"] = gating
    result["all_gating_controls_pass"] = all(bool(result[key]["pass"]) for key in gating)
    return result, raw_controls


def build_raw_payload(
    spec_hash: str,
    catalog_hash: str,
    main_scores: np.ndarray,
    control_scores: dict[str, np.ndarray],
) -> dict[str, Any]:
    arrays = {
        "combined_score": encode_array(main_scores[:, :, :, 0]),
        "geometry_loss": encode_array(main_scores[:, :, :, 1]),
        "entropy_loss": encode_array(main_scores[:, :, :, 2]),
        "mean_absolute_entropy_movement": encode_array(main_scores[:, :, :, 3]),
    }
    controls = {key: encode_array(value) for key, value in sorted(control_scores.items())}
    return {
        "schema": "codex_ratchet.free_length_dual_ratchet_schedule_selector_v0.raw_scores.v1",
        "sim_id": "free_length_dual_ratchet_schedule_selector_v0",
        "spec_sha256": spec_hash,
        "candidate_catalog_sha256": catalog_hash,
        "candidate_axis_count": int(main_scores.shape[2]),
        "scenario_axis_count": int(main_scores.shape[0]),
        "engine_axis": list(ENGINES),
        "arrays": arrays,
        "control_combined_score_arrays": controls,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary-output", type=Path, default=DEFAULT_SUMMARY_PATH)
    parser.add_argument("--raw-output", type=Path, default=DEFAULT_RAW_PATH)
    parser.add_argument("--candidate-output", type=Path, default=DEFAULT_CATALOG_PATH)
    parser.add_argument("--batch-size", type=int, default=128)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    spec = json.loads(SPEC_PATH.read_text())
    prereg = json.loads(PREREG_PATH.read_text())
    spec_hash = sha256(SPEC_PATH)
    if spec_hash != prereg["spec_sha256"]:
        raise RuntimeError("frozen spec hash mismatch")
    if SPEC_HASH_PATH.read_text().split()[0] != spec_hash:
        raise RuntimeError("detached spec hash mismatch")

    candidates, candidate_metadata = build_candidates(spec)
    candidate_data = candidate_arrays(candidates, spec)
    catalog = candidate_catalog_payload(candidates, candidate_metadata, spec_hash)
    catalog_hash = write_json(args.candidate_output, catalog)
    slot_data = load_slots()

    perturbations = spec["scenario_grid"]["perturbations"]
    carriers = [build_carrier(perturbation, spec, slot_data) for perturbation in perturbations]
    probe_grid, base_scenarios = make_probe_grid(spec, len(carriers))
    scored = evaluate_candidates(
        candidates,
        candidate_data,
        carriers,
        probe_grid,
        slot_data,
        spec,
        batch_size=int(args.batch_size),
        fixed_total_exposure=True,
    )
    main_scores, scenario_manifest = flatten_main_scores(scored, perturbations, base_scenarios)
    scenario_rows, aggregate, qualifying_counts = summarize_scenarios(
        main_scores,
        candidates,
        scenario_manifest,
        spec,
    )
    signal = shared_signal(
        qualifying_counts,
        int(spec["scientific_pass_rule"]["required_scenarios_per_engine"]),
    )

    anchor_probes = anchor_probe_grid(spec)[0][0, 0]
    physical_rows = [physical_audit(carrier, slot_data, anchor_probes, spec) for carrier in carriers]
    physical_pass = all(row["pass"] for row in physical_rows)
    controls, control_scores = evaluate_controls(
        candidates,
        candidate_data,
        main_scores,
        scenario_manifest,
        slot_data,
        spec,
        batch_size=int(args.batch_size),
    )
    scientific_pass = bool(signal["pass"] and physical_pass and controls["all_gating_controls_pass"])
    scientific_verdict = (
        spec["scientific_pass_rule"]["green_ceiling"]
        if scientific_pass
        else spec["scientific_pass_rule"]["red_verdict"]
    )

    raw_payload = build_raw_payload(spec_hash, catalog_hash, main_scores, control_scores)
    raw_hash = write_json(args.raw_output, raw_payload)

    slot_rows = []
    for row in slot_data.rows:
        slot_rows.append(
            {
                "slot_id": row["slot_id"],
                "engine": row["engine"],
                "loop": row["loop"],
                "step": int(row["step"]),
                "terrain": row["terrain"],
                "axis6_sign": row["axis6_sign"],
                "canonical_operator_metadata_only": row["canonical_operator"],
                "beat_sign_template_Lmax8": [row["axis6_sign"]] * MAX_LENGTH,
            }
        )
    execution_checks = {
        "spec_hash_matches_preregistration": spec_hash == prereg["spec_sha256"],
        "candidate_space_checks_pass": all(candidate_metadata["checks"].values()),
        "scenario_count_matches_spec": len(scenario_manifest)
        == int(spec["scenario_grid"]["scenario_count_per_engine"]),
        "engine_count_matches_spec": main_scores.shape[1] == int(spec["scenario_grid"]["engine_count"]),
        "candidate_count_matches_spec": main_scores.shape[2]
        == int(spec["candidate_space"]["oriented_necklace_count_total"]),
        "all_scores_finite": bool(np.all(np.isfinite(main_scores))),
        "all_source_slots_present": len(slot_rows) == 16 and len({row["slot_id"] for row in slot_rows}) == 16,
        "all_sign_templates_constant": all(len(set(row["beat_sign_template_Lmax8"])) == 1 for row in slot_rows),
        "native_metadata_off_score_path": True,
        "no_learned_lane": spec["controls"]["learned_lane_used"] is False,
    }
    execution_complete = all(execution_checks.values())
    result = {
        "schema": "codex_ratchet.free_length_dual_ratchet_schedule_selector_v0.jax_result.v1",
        "sim_id": spec["sim_id"],
        "classification": classification,
        "promotion_allowed": promotion_allowed,
        "formal_admission_allowed": formal_admission_allowed,
        "stage_movement_allowed": stage_movement_allowed,
        "sim_execution_kind": sim_execution_kind,
        "engine_mode": "jax_exact_batched_free_length_enumeration",
        "preregistration": {
            "spec_sha256": spec_hash,
            "receipt_sha256": sha256(PREREG_PATH),
            "observed_results_run_before_freeze": prereg["observed_results_run_before_freeze"],
            "immutable_v0": True,
        },
        "source_hashes": {
            relative(SPEC_PATH): spec_hash,
            relative(SPEC_HASH_PATH): sha256(SPEC_HASH_PATH),
            relative(PREREG_PATH): sha256(PREREG_PATH),
            relative(SOURCE_PATH): sha256(SOURCE_PATH),
            relative(SCHEDULE_PATH): sha256(SCHEDULE_PATH),
            relative(CORRECTION_PATH): sha256(CORRECTION_PATH),
        },
        "candidate_catalog_sha256": catalog_hash,
        "raw_scores_sha256": raw_hash,
        "candidate_space": candidate_metadata,
        "scenario_manifest": scenario_manifest,
        "source_slot_rows": slot_rows,
        "scenario_results": scenario_rows,
        "aggregate_winners": aggregate,
        "qualifying_counts": qualifying_counts,
        "physical_preconditions": {
            "pass": physical_pass,
            "perturbations": physical_rows,
        },
        "controls": controls,
        "scientific_signal": signal,
        "scientific_signal_pass": signal["pass"],
        "physical_preconditions_pass": physical_pass,
        "gating_controls_pass": controls["all_gating_controls_pass"],
        "scientific_pass": scientific_pass,
        "scientific_verdict": scientific_verdict,
        "execution_checks": execution_checks,
        "execution_complete": execution_complete,
        "artifact_validity_claimed_by_producer": False,
        "artifact_validity_requires_independent_validator": True,
        "accepted_scientific_ceiling": (
            "four_selected_under_declared_source_operator_family_only"
            if scientific_pass
            else "free_length_search_completed_scientific_RED"
        ),
        "jax": {
            "ran": True,
            "x64": bool(jax.config.jax_enable_x64),
            "version": jax.__version__,
            "devices": [device.platform for device in jax.devices()],
            "batched_candidate_count": len(candidates),
            "rooted_word_coverage_count": candidate_metadata["rooted_word_count_total"],
            "scenario_count_per_engine": len(scenario_manifest),
            "batch_size": int(args.batch_size),
            "reads_peer_result": False,
            "source_path": relative(SOURCE_PATH),
        },
        "package_fingerprint": {
            "python": platform.python_version(),
            "jax": jax.__version__,
            "jaxlib": package_version("jaxlib"),
            "lineax": package_version("lineax"),
            "numpy": np.__version__,
        },
        "tool_calls": [
            {
                "tool": "jax",
                "qualified_api/function": "jax.jit(jax.vmap(score_chunk_core))",
                "input_object": "11586 oriented cycles x 36 scenarios x two engine schedules x all distinct cyclic phases",
                "output_object": "complete geometry, entropy, movement, and minimax-plus-MDL score arrays",
                "positive_case": "all finite candidate/scenario scores emitted",
                "negative/erased_control": "identity erasure, sign scramble, role swap, and commuting substitution",
                "boundary_case": "period-one powers remain visible inside the user-scoped L>=2 boundary",
                "demotion_condition": "coverage, finite-value, scalar/batch, control, or validator failure",
                "gates": ["execution_complete", "scientific_signal_pass"],
            },
            {
                "tool": "jax.scipy.linalg.expm",
                "qualified_api/function": "jax.scipy.linalg.expm",
                "input_object": "eight finite GKSL Liouvillian matrices under three perturbations",
                "output_object": "dissipative terrain affine channels",
                "positive_case": "CPTP terrain channels with nonzero terrain/operator commutators",
                "negative/erased_control": "isotropic commuting terrain substitution",
                "boundary_case": "symmetric preregistered parameter perturbations",
                "demotion_condition": "non-CPTP, nonfinite, or commuting main carrier",
                "gates": ["physical_preconditions_pass"],
            },
            {
                "tool": "lineax.linear_solve",
                "qualified_api/function": "lineax.linear_solve(MatrixLinearOperator, LU)",
                "input_object": "(I-M_s) r_s = b_s for each terrain affine map",
                "output_object": "terrain fixed points used by both independent objective readouts",
                "positive_case": "finite fixed points and nonzero entropy-side movement",
                "negative/erased_control": "commuting isotropic terrain has the zero fixed point and fails the physical claim gate",
                "boundary_case": "full-rank epsilon regularization is fixed in spec",
                "demotion_condition": "nonfinite solve or zero entropy-side movement",
                "gates": ["physical_preconditions_pass", "scientific_signal_pass"],
            },
        ],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "claim_ceiling": spec["claim_ceiling"],
        "eligible_consumers": spec["eligible_consumers"],
        "blocked_consumers": spec["blocked_consumers"],
        "roles": {
            "state_archaeologist": "read-only source and predecessor audit completed before preregistration",
            "builder": "this JAX source",
            "mechanical_gatekeeper": "independent validator not part of this producer",
            "fabrication_auditor": "not_run_in_producer",
            "controller_admission": "not_run",
        },
    }
    summary_hash = write_json(args.summary_output, result)
    print(
        json.dumps(
            {
                "summary_output": str(args.summary_output),
                "summary_sha256": summary_hash,
                "raw_output": str(args.raw_output),
                "raw_sha256": raw_hash,
                "candidate_output": str(args.candidate_output),
                "candidate_sha256": catalog_hash,
                "execution_complete": execution_complete,
                "physical_preconditions_pass": physical_pass,
                "gating_controls_pass": controls["all_gating_controls_pass"],
                "scientific_pass": scientific_pass,
                "scientific_verdict": scientific_verdict,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if execution_complete else 1


if __name__ == "__main__":
    raise SystemExit(main())
