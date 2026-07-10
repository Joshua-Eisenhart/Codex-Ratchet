#!/usr/bin/env python3
"""Batched JAX robustness sweep for the learned stage-interior candidates."""

from __future__ import annotations

import hashlib
import importlib.metadata
import itertools
import json
import math
import platform
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Sequence

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

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
SOURCE_PATH = HERE / "dual_ratchet_stage_interior_learning_v0_jax_sweep.py"
RESULT_PATH = HERE / "results" / "dual_ratchet_stage_interior_learning_v0_jax_sweep_results.json"
SPEC_PATH = HERE / "spec.json"
PYTORCH_SOURCE_PATH = HERE / "dual_ratchet_stage_interior_learning_v0_pytorch.py"
PYTORCH_RESULT_PATH = HERE / "results" / "dual_ratchet_stage_interior_learning_v0_pytorch_results.json"
BASE_PATH = (
    REPO
    / "system_v7"
    / "constraint_core"
    / "sims_and_scripts"
    / "stage_interior_architecture_tournament_sim.py"
)

OPS = ("Ti", "Te", "Fi", "Fe")
ENGINES = ("Type1_left", "Type2_right")
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

G = 0.35
KAPPA = 1.0
FLOW_TIME = 1.0
OPERATOR_Q = 1.0 - math.exp(-1.0)
ROTATION_ANGLE = math.pi / 4.0
PERTURBATION_LINF_RADIUS = 0.04
TIE_ABSOLUTE_TOLERANCE = 1.0e-5
TIE_RELATIVE_TOLERANCE = 5.0e-4
SCORE_REPRODUCTION_TOLERANCE = 5.0e-10
FIXED_POINT_RESIDUAL_TOLERANCE = 1.0e-10

PERTURBATIONS: tuple[tuple[str, tuple[float, float, float]], ...] = (
    ("baseline", (0.0, 0.0, 0.0)),
    ("w1_plus", (1.0, 0.0, 0.0)),
    ("w1_minus", (-1.0, 0.0, 0.0)),
    ("w2_plus", (0.0, 1.0, 0.0)),
    ("w2_minus", (0.0, -1.0, 0.0)),
    ("w3_plus", (0.0, 0.0, 1.0)),
    ("w3_minus", (0.0, 0.0, -1.0)),
    ("all_plus", (1.0, 1.0, 1.0)),
    ("all_minus", (-1.0, -1.0, -1.0)),
    ("contrast_1_plus", (1.0, -1.0, 1.0)),
    ("contrast_1_minus", (-1.0, 1.0, -1.0)),
    ("contrast_2_plus", (1.0, 1.0, -1.0)),
    ("contrast_2_minus", (-1.0, -1.0, 1.0)),
    ("contrast_3_plus", (-1.0, 1.0, 1.0)),
    ("contrast_3_minus", (1.0, -1.0, -1.0)),
)

SX = jnp.asarray([[0.0, 1.0], [1.0, 0.0]], dtype=jnp.complex128)
SY = jnp.asarray([[0.0, -1.0j], [1.0j, 0.0]], dtype=jnp.complex128)
SZ = jnp.asarray([[1.0, 0.0], [0.0, -1.0]], dtype=jnp.complex128)
PAULI = jnp.stack((SX, SY, SZ))
I2 = jnp.eye(2, dtype=jnp.complex128)
SP = 0.5 * (SX + 1.0j * SY)
SM = 0.5 * (SX - 1.0j * SY)
P0 = 0.5 * (I2 + SZ)
P1 = 0.5 * (I2 - SZ)
QP = 0.5 * (I2 + SX)
QM = 0.5 * (I2 - SX)
UX = jsp.linalg.expm(-1.0j * ROTATION_ANGLE / 2.0 * SX)
UZ = jsp.linalg.expm(-1.0j * ROTATION_ANGLE / 2.0 * SZ)
PAIR_LEFT = jnp.asarray((0, 0, 0, 1, 1, 2), dtype=jnp.int32)
PAIR_RIGHT = jnp.asarray((1, 2, 3, 2, 3, 3), dtype=jnp.int32)

TOOL_MANIFEST = {
    "jax": {
        "tried": True,
        "used": True,
        "reason": "load-bearing x64 jit/vmap sweep over engine, cycle, probe, learned-seed, radius, and weight perturbation axes",
    },
    "jax.scipy.linalg.expm": {
        "tried": True,
        "used": True,
        "reason": "load-bearing reconstruction of the eight finite house GKSL terrain channels and two unitary operator channels",
    },
    "lineax.linear_solve": {
        "tried": True,
        "used": True,
        "reason": "load-bearing fixed-point references in the relative-entropy score",
    },
    "numpy.random.Generator": {
        "tried": True,
        "used": True,
        "reason": "control-only reproduction of the PyTorch receipt's original PCG64 probe set; excluded from the robustness sweep",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "jax": "load_bearing",
    "jax.scipy.linalg.expm": "load_bearing",
    "lineax.linear_solve": "load_bearing",
    "numpy.random.Generator": "control_only",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative(path: Path) -> str:
    return str(path.relative_to(REPO))


def package_version(distribution: str) -> str:
    try:
        return importlib.metadata.version(distribution)
    except importlib.metadata.PackageNotFoundError:
        return "missing"


def jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [jsonable(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, jax.Array):
        return jax.device_get(value).tolist()
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.floating, np.integer)):
        return value.item()
    if isinstance(value, np.bool_):
        return bool(value)
    return value


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


def terrain_vector_field(terrain: jax.Array, rho: jax.Array) -> jax.Array:
    epsilon = TERRAIN_EPSILON[terrain]
    kind = TERRAIN_KIND[terrain]
    pole = TERRAIN_POLE[terrain]
    hamiltonian = epsilon * (SX + SY + SZ) / math.sqrt(3.0)
    coherent = -1.0j * G * (hamiltonian @ rho - rho @ hamiltonian)
    damping_operator = jnp.where(pole > 0.0, SP, SM)
    damping = KAPPA * dissipator(damping_operator, rho)
    depolarizing = 0.5 * KAPPA * (dissipator(SX, rho) + dissipator(SY, rho))
    projection = KAPPA * dissipator(SZ, rho)
    dissipative = jnp.where(kind == 0, damping, jnp.where(kind == 1, depolarizing, projection))
    return coherent + dissipative


def terrain_flow_matrix(terrain: jax.Array) -> jax.Array:
    density_basis = jnp.eye(4, dtype=jnp.complex128).reshape((4, 2, 2))
    columns = jax.vmap(lambda rho: terrain_vector_field(terrain, rho))(density_basis)
    liouvillian = columns.reshape((4, 4)).T
    return jsp.linalg.expm(FLOW_TIME * liouvillian)


def flow_density(flow_matrix: jax.Array, rho: jax.Array) -> jax.Array:
    evolved = flow_matrix @ rho.reshape((4,))
    return clean_density(evolved.reshape((2, 2)))


def operator_density(operator: jax.Array, rho: jax.Array) -> jax.Array:
    ti = (1.0 - OPERATOR_Q) * rho + OPERATOR_Q * (P0 @ rho @ P0 + P1 @ rho @ P1)
    te = (1.0 - OPERATOR_Q) * rho + OPERATOR_Q * (QP @ rho @ QP + QM @ rho @ QM)
    fi = UX @ rho @ jnp.conjugate(UX.T)
    fe = UZ @ rho @ jnp.conjugate(UZ.T)
    return jax.lax.dynamic_index_in_dim(jnp.stack((ti, te, fi, fe)), operator, keepdims=False)


def affine_from_density_outputs(outputs: jax.Array) -> tuple[jax.Array, jax.Array]:
    vectors = jax.vmap(bloch_from_density)(outputs)
    offset = vectors[0]
    matrix = (vectors[1:] - offset).T
    return matrix, offset


def build_channel_affines() -> tuple[jax.Array, jax.Array, jax.Array, jax.Array]:
    test_vectors = jnp.concatenate((jnp.zeros((1, 3)), jnp.eye(3)), axis=0)
    test_densities = jax.vmap(density_from_bloch)(test_vectors)

    def terrain_affine(terrain: jax.Array) -> tuple[jax.Array, jax.Array]:
        flow = terrain_flow_matrix(terrain)
        outputs = jax.vmap(lambda rho: flow_density(flow, rho))(test_densities)
        return affine_from_density_outputs(outputs)

    def operator_affine(operator: jax.Array) -> tuple[jax.Array, jax.Array]:
        outputs = jax.vmap(lambda rho: operator_density(operator, rho))(test_densities)
        return affine_from_density_outputs(outputs)

    terrain_matrices, terrain_offsets = jax.vmap(terrain_affine)(jnp.arange(8, dtype=jnp.int32))
    operator_matrices, operator_offsets = jax.vmap(operator_affine)(jnp.arange(4, dtype=jnp.int32))
    return terrain_matrices, terrain_offsets, operator_matrices, operator_offsets


def fixed_points_lineax(matrices: jax.Array, offsets: jax.Array) -> jax.Array:
    def solve(matrix: jax.Array, offset: jax.Array) -> jax.Array:
        operator = lx.MatrixLinearOperator(jnp.eye(3) - matrix)
        return lx.linear_solve(operator, offset, solver=lx.LU()).value

    return jax.vmap(solve)(matrices, offsets)


def apply_affine(matrix: jax.Array, offset: jax.Array, vectors: jax.Array) -> jax.Array:
    return vectors @ matrix.T + offset


def phase_cycle(cycle: jax.Array, native_operator: jax.Array) -> jax.Array:
    anchor = jnp.argmax(cycle == native_operator)
    return cycle[(jnp.arange(4, dtype=jnp.int32) + anchor) % 4]


def run_stage(
    slot: jax.Array,
    cycle: jax.Array,
    weights: jax.Array,
    probes: jax.Array,
    slot_terrain: jax.Array,
    slot_axis6_up: jax.Array,
    slot_native: jax.Array,
    terrain_matrices: jax.Array,
    terrain_offsets: jax.Array,
    operator_matrices: jax.Array,
    operator_offsets: jax.Array,
    *,
    flip_axis6: jax.Array,
    drop_position: jax.Array,
) -> tuple[jax.Array, jax.Array]:
    terrain = slot_terrain[slot]
    is_up = jnp.logical_xor(slot_axis6_up[slot], flip_axis6)
    phased = phase_cycle(cycle, slot_native[slot])

    def step(value: jax.Array, item: tuple[jax.Array, jax.Array, jax.Array]) -> tuple[jax.Array, jax.Array]:
        position, operator, weight = item
        operator_first = apply_affine(
            terrain_matrices[terrain],
            terrain_offsets[terrain],
            apply_affine(operator_matrices[operator], operator_offsets[operator], value),
        )
        terrain_first = apply_affine(
            operator_matrices[operator],
            operator_offsets[operator],
            apply_affine(terrain_matrices[terrain], terrain_offsets[terrain], value),
        )
        moved = jnp.where(is_up, operator_first, terrain_first)
        updated = (1.0 - weight) * value + weight * moved
        next_value = jnp.where(position == drop_position, value, updated)
        return next_value, next_value

    final, trajectory = jax.lax.scan(
        step,
        probes,
        (jnp.arange(4, dtype=jnp.int32), phased, weights),
    )
    return final, jnp.swapaxes(trajectory, 0, 1)


def entropy_from_bloch(vectors: jax.Array) -> jax.Array:
    radius = jnp.clip(jnp.linalg.vector_norm(vectors, axis=-1), 0.0, 1.0 - 1.0e-10)
    plus = jnp.maximum((1.0 + radius) / 2.0, 1.0e-12)
    minus = jnp.maximum((1.0 - radius) / 2.0, 1.0e-12)
    return -(plus * jnp.log(plus) + minus * jnp.log(minus))


def relative_entropy_from_bloch(vectors: jax.Array, reference: jax.Array) -> jax.Array:
    radius = jnp.clip(jnp.linalg.vector_norm(vectors, axis=-1), 0.0, 1.0 - 1.0e-10)
    ref_radius = jnp.clip(jnp.linalg.vector_norm(reference), 0.0, 1.0 - 1.0e-10)
    plus = jnp.maximum((1.0 + radius) / 2.0, 1.0e-12)
    minus = jnp.maximum((1.0 - radius) / 2.0, 1.0e-12)
    tr_rho_log_rho = plus * jnp.log(plus) + minus * jnp.log(minus)
    ref_plus = jnp.maximum((1.0 + ref_radius) / 2.0, 1.0e-12)
    ref_minus = jnp.maximum((1.0 - ref_radius) / 2.0, 1.0e-12)
    a = 0.5 * (jnp.log(ref_plus) + jnp.log(ref_minus))
    b = 0.5 * (jnp.log(ref_plus) - jnp.log(ref_minus))
    direction = reference / jnp.maximum(ref_radius, 1.0e-12)
    tr_rho_log_sigma = a + b * jnp.sum(vectors * direction, axis=-1)
    return jnp.maximum(tr_rho_log_rho - tr_rho_log_sigma, 0.0)


def pair_separation_loss(signatures: jax.Array, scale: float) -> jax.Array:
    differences = signatures[PAIR_LEFT] - signatures[PAIR_RIGHT]
    squared_distances = jnp.sum(differences**2, axis=1)
    return jnp.mean(jnp.exp(-squared_distances / scale))


def score_cycle(
    engine: jax.Array,
    cycle: jax.Array,
    weights: jax.Array,
    probes: jax.Array,
    geometry_slots: jax.Array,
    entropy_slots: jax.Array,
    slot_terrain: jax.Array,
    slot_axis6_up: jax.Array,
    slot_native: jax.Array,
    terrain_matrices: jax.Array,
    terrain_offsets: jax.Array,
    operator_matrices: jax.Array,
    operator_offsets: jax.Array,
    terrain_fixed_points: jax.Array,
    geometry_pair_scale: float,
    entropy_pair_scale: float,
    axis6_scale: float,
    drop_scale: float,
) -> jax.Array:
    active_geometry = geometry_slots[engine]
    active_entropy = entropy_slots[engine]

    def geometry_row(slot: jax.Array) -> tuple[jax.Array, jax.Array, jax.Array]:
        final, _ = run_stage(
            slot,
            cycle,
            weights,
            probes,
            slot_terrain,
            slot_axis6_up,
            slot_native,
            terrain_matrices,
            terrain_offsets,
            operator_matrices,
            operator_offsets,
            flip_axis6=jnp.asarray(False),
            drop_position=jnp.asarray(-1),
        )
        flipped, _ = run_stage(
            slot,
            cycle,
            weights,
            probes,
            slot_terrain,
            slot_axis6_up,
            slot_native,
            terrain_matrices,
            terrain_offsets,
            operator_matrices,
            operator_offsets,
            flip_axis6=jnp.asarray(True),
            drop_position=jnp.asarray(-1),
        )
        dropped = jax.vmap(
            lambda position: run_stage(
                slot,
                cycle,
                weights,
                probes,
                slot_terrain,
                slot_axis6_up,
                slot_native,
                terrain_matrices,
                terrain_offsets,
                operator_matrices,
                operator_offsets,
                flip_axis6=jnp.asarray(False),
                drop_position=position,
            )[0]
        )(jnp.arange(4, dtype=jnp.int32))
        drop_effects = jnp.mean((dropped - final[None, :, :]) ** 2, axis=(1, 2))
        return final.reshape((-1,)), jnp.mean((final - flipped) ** 2), drop_effects

    signatures, flip_effects, drop_effects = jax.vmap(geometry_row)(active_geometry)
    geometry_separation = pair_separation_loss(signatures, geometry_pair_scale)
    axis6_penalty = jnp.exp(-jnp.mean(flip_effects) / axis6_scale)
    drop_penalty = jnp.mean(jnp.exp(-drop_effects / drop_scale))
    geometry_score = geometry_separation + 0.5 * axis6_penalty + 0.5 * drop_penalty

    def entropy_row(slot: jax.Array) -> tuple[jax.Array, jax.Array]:
        _, trajectory = run_stage(
            slot,
            cycle,
            weights,
            probes,
            slot_terrain,
            slot_axis6_up,
            slot_native,
            terrain_matrices,
            terrain_offsets,
            operator_matrices,
            operator_offsets,
            flip_axis6=jnp.asarray(False),
            drop_position=jnp.asarray(-1),
        )
        entropy = entropy_from_bloch(trajectory)
        relative_entropy = relative_entropy_from_bloch(
            trajectory,
            terrain_fixed_points[slot_terrain[slot]],
        )
        profile = jnp.concatenate((entropy.reshape((-1,)), relative_entropy.reshape((-1,))))
        variation = jnp.mean(jnp.abs(relative_entropy[:, 1:] - relative_entropy[:, :-1]))
        return profile, variation

    entropy_profiles, variations = jax.vmap(entropy_row)(active_entropy)
    entropy_separation = pair_separation_loss(entropy_profiles, entropy_pair_scale)
    variation_penalty = jnp.exp(-jnp.mean(variations) / entropy_pair_scale)
    entropy_score = entropy_separation + 0.5 * variation_penalty
    return jnp.asarray((geometry_score + entropy_score, geometry_score, entropy_score))


def score_scenario(
    engine: jax.Array,
    weights_by_cycle: jax.Array,
    probes: jax.Array,
    cycles: jax.Array,
    geometry_slots: jax.Array,
    entropy_slots: jax.Array,
    slot_terrain: jax.Array,
    slot_axis6_up: jax.Array,
    slot_native: jax.Array,
    terrain_matrices: jax.Array,
    terrain_offsets: jax.Array,
    operator_matrices: jax.Array,
    operator_offsets: jax.Array,
    terrain_fixed_points: jax.Array,
    score_scales: jax.Array,
) -> jax.Array:
    return jax.vmap(
        lambda cycle, weights: score_cycle(
            engine,
            cycle,
            weights,
            probes,
            geometry_slots,
            entropy_slots,
            slot_terrain,
            slot_axis6_up,
            slot_native,
            terrain_matrices,
            terrain_offsets,
            operator_matrices,
            operator_offsets,
            terrain_fixed_points,
            score_scales[0],
            score_scales[1],
            score_scales[2],
            score_scales[3],
        )
    )(cycles, weights_by_cycle)


def candidate_cycles() -> list[tuple[str, ...]]:
    return [("Ti",) + tail for tail in itertools.permutations(("Te", "Fi", "Fe"))]


def cycle_label(cycle: Sequence[str]) -> str:
    return ">".join(cycle)


def make_probe_set(seed: int, count: int, radius: float) -> jax.Array:
    values = jax.random.normal(jax.random.PRNGKey(seed), (count, 3), dtype=jnp.float64)
    directions = values / jnp.linalg.vector_norm(values, axis=1, keepdims=True)
    return directions * radius


def make_receipt_control_probes(spec: dict[str, Any]) -> jax.Array:
    rng = np.random.default_rng(int(spec["probe_seed"]))
    values = rng.normal(size=(int(spec["probe_count"]), 3))
    values /= np.linalg.norm(values, axis=1, keepdims=True)
    return jnp.asarray(values * float(spec["probe_radius"]), dtype=jnp.float64)


def scalar_stats(values: jax.Array) -> dict[str, float]:
    quantiles = jax.device_get(jnp.quantile(values, jnp.asarray((0.0, 0.05, 0.5, 0.95, 1.0))))
    return {
        "minimum": float(quantiles[0]),
        "p05": float(quantiles[1]),
        "median": float(quantiles[2]),
        "p95": float(quantiles[3]),
        "maximum": float(quantiles[4]),
        "mean": float(jax.device_get(jnp.mean(values))),
    }


def ranking_summary(
    scores: jax.Array,
    cycles: Sequence[Sequence[str]],
    reference_index: int,
) -> dict[str, Any]:
    ordered = jnp.sort(scores, axis=1)
    best = ordered[:, 0]
    second = ordered[:, 1]
    margins = second - best
    relative_margins = margins / jnp.maximum(jnp.abs(best), 1.0e-12)
    tie_floors = jnp.maximum(TIE_ABSOLUTE_TOLERANCE, TIE_RELATIVE_TOLERANCE * jnp.abs(best))
    ties = margins <= tie_floors
    winners = jnp.argmin(scores, axis=1)
    winner_counts = jnp.bincount(winners, length=len(cycles))
    reference_scores = scores[:, reference_index]
    competitors = jnp.min(
        jnp.where(jnp.arange(len(cycles)) == reference_index, jnp.inf, scores),
        axis=1,
    )
    reference_margins = competitors - reference_scores
    reference_ranks = 1 + jnp.sum(scores < reference_scores[:, None], axis=1)
    counts = [int(item) for item in jax.device_get(winner_counts)]
    scenario_count = int(scores.shape[0])
    modal_index = int(jax.device_get(jnp.argmax(winner_counts)))
    tie_count = int(jax.device_get(jnp.sum(ties)))
    return {
        "scenario_count": scenario_count,
        "score_direction": "lower_is_better",
        "reference_cycle": list(cycles[reference_index]),
        "modal_cycle": list(cycles[modal_index]),
        "modal_cycle_fraction": counts[modal_index] / scenario_count,
        "reference_cycle_winner_fraction": counts[reference_index] / scenario_count,
        "winner_counts": {cycle_label(cycle): counts[index] for index, cycle in enumerate(cycles)},
        "unique_winner_count": sum(count > 0 for count in counts),
        "tie_count": tie_count,
        "tie_fraction": tie_count / scenario_count,
        "tie_rule": {
            "absolute_tolerance": TIE_ABSOLUTE_TOLERANCE,
            "relative_tolerance": TIE_RELATIVE_TOLERANCE,
            "formula": "top_two_margin <= max(abs_tol, rel_tol * abs(best_score))",
        },
        "top_two_absolute_margin": scalar_stats(margins),
        "top_two_relative_margin": scalar_stats(relative_margins),
        "reference_vs_best_competitor_margin": scalar_stats(reference_margins),
        "reference_rank": {
            "mean": float(jax.device_get(jnp.mean(reference_ranks))),
            "maximum": int(jax.device_get(jnp.max(reference_ranks))),
        },
        "reference_cycle_wins_every_scenario": counts[reference_index] == scenario_count,
        "no_ties_under_declared_rule": tie_count == 0,
    }


def main() -> int:
    spec = json.loads(SPEC_PATH.read_text())
    pytorch_result = json.loads(PYTORCH_RESULT_PATH.read_text())
    schedule_path = REPO / spec["source_schedule"]
    dependency_path = REPO / spec["operator_basis_dependency"]
    schedule = json.loads(schedule_path.read_text())
    cycles = candidate_cycles()
    cycle_to_index = {cycle: index for index, cycle in enumerate(cycles)}
    seeds = [int(seed) for seed in spec["seeds"]]
    seed_to_index = {seed: index for index, seed in enumerate(seeds)}

    expected_run_keys = {
        (engine, cycle, seed)
        for engine in ENGINES
        for cycle in cycles
        for seed in seeds
    }
    observed_run_keys = {
        (row["engine"], tuple(row["cycle"]), int(row["seed"]))
        for row in pytorch_result["runs"]
    }
    run_lookup = {
        (row["engine"], tuple(row["cycle"]), int(row["seed"])): row
        for row in pytorch_result["runs"]
    }
    base_weights = jnp.asarray(
        [
            [
                [
                    run_lookup[(engine, cycle, seed)]["learned_weights_native_first"]
                    for cycle in cycles
                ]
                for seed in seeds
            ]
            for engine in ENGINES
        ],
        dtype=jnp.float64,
    )
    receipt_losses = jnp.asarray(
        [
            [
                [run_lookup[(engine, cycle, seed)]["final_total_loss"] for cycle in cycles]
                for seed in seeds
            ]
            for engine in ENGINES
        ],
        dtype=jnp.float64,
    )

    slot_terrain = jnp.asarray([TERRAIN_INDEX[row["terrain"]] for row in schedule], dtype=jnp.int32)
    slot_axis6_up = jnp.asarray([row["axis6_sign"] == "up" for row in schedule])
    slot_native = jnp.asarray([OPS.index(row["canonical_operator"]) for row in schedule], dtype=jnp.int32)
    geometry_slot_rows: list[list[int]] = []
    entropy_slot_rows: list[list[int]] = []
    axis6_counts: dict[str, dict[str, int]] = {}
    for engine in ENGINES:
        engine_rows = [index for index, row in enumerate(schedule) if row["engine"] == engine]
        geometry_slot_rows.append(
            sorted(
                [index for index in engine_rows if "deductive" in schedule[index]["loop"]],
                key=lambda index: int(schedule[index]["step"]),
            )
        )
        entropy_slot_rows.append(
            sorted(
                [index for index in engine_rows if "inductive" in schedule[index]["loop"]],
                key=lambda index: int(schedule[index]["step"]),
            )
        )
        axis6_counts[engine] = dict(Counter(schedule[index]["axis6_sign"] for index in engine_rows))
    geometry_slots = jnp.asarray(geometry_slot_rows, dtype=jnp.int32)
    entropy_slots = jnp.asarray(entropy_slot_rows, dtype=jnp.int32)
    cycle_indices = jnp.asarray([[OPS.index(operator) for operator in cycle] for cycle in cycles], dtype=jnp.int32)
    score_scales = jnp.asarray(
        (
            float(spec["geometry_pair_scale"]),
            float(spec["entropy_pair_scale"]),
            float(spec["axis6_scale"]),
            float(spec["drop_scale"]),
        )
    )

    terrain_matrices, terrain_offsets, operator_matrices, operator_offsets = build_channel_affines()
    terrain_fixed_points = fixed_points_lineax(terrain_matrices, terrain_offsets)
    fixed_point_residuals = jax.vmap(
        lambda matrix, offset, fixed: jnp.linalg.vector_norm((jnp.eye(3) - matrix) @ fixed - offset)
    )(terrain_matrices, terrain_offsets, terrain_fixed_points)

    @jax.jit
    def batched_score(
        scenario_engines: jax.Array,
        scenario_weights: jax.Array,
        scenario_probes: jax.Array,
        active_operator_matrices: jax.Array,
        active_operator_offsets: jax.Array,
    ) -> jax.Array:
        return jax.vmap(
            lambda engine, weights, probes: score_scenario(
                engine,
                weights,
                probes,
                cycle_indices,
                geometry_slots,
                entropy_slots,
                slot_terrain,
                slot_axis6_up,
                slot_native,
                terrain_matrices,
                terrain_offsets,
                active_operator_matrices,
                active_operator_offsets,
                terrain_fixed_points,
                score_scales,
            )
        )(scenario_engines, scenario_weights, scenario_probes)

    receipt_probes = make_receipt_control_probes(spec)
    parity_engines = jnp.asarray([engine for engine in range(2) for _seed in seeds], dtype=jnp.int32)
    parity_weights = jnp.stack([base_weights[engine, seed] for engine in range(2) for seed in range(len(seeds))])
    parity_probes = jnp.stack([receipt_probes for _ in range(len(parity_engines))])
    parity_scores = batched_score(
        parity_engines,
        parity_weights,
        parity_probes,
        operator_matrices,
        operator_offsets,
    )
    parity_total = parity_scores[:, :, 0].reshape((2, len(seeds), len(cycles)))
    score_reproduction_error = jnp.abs(parity_total - receipt_losses)
    score_reproduction_relative_error = score_reproduction_error / jnp.maximum(jnp.abs(receipt_losses), 1.0e-12)
    nominal_aggregate_scores = jnp.mean(parity_total, axis=1)
    nominal_winners = jnp.argmin(nominal_aggregate_scores, axis=1)
    reference_cycles = [tuple(pytorch_result["selected_cycles"][engine]) for engine in ENGINES]
    reference_indices = [cycle_to_index[cycle] for cycle in reference_cycles]

    perturbation_directions = jnp.asarray([row[1] for row in PERTURBATIONS], dtype=jnp.float64)
    perturbation_deltas = PERTURBATION_LINF_RADIUS * perturbation_directions
    perturbed_nonnative = jnp.clip(
        base_weights[..., 1:][..., None, :] + perturbation_deltas,
        1.0e-8,
        1.0,
    )
    native_weights = jnp.ones(perturbed_nonnative.shape[:-1] + (1,), dtype=jnp.float64)
    perturbed_weights = jnp.concatenate((native_weights, perturbed_nonnative), axis=-1)

    probe_seeds = sorted(set(seeds + [max(seeds) + 1]))
    probe_radii = sorted(set((0.35, float(spec["probe_radius"]), 0.80)))
    probe_grid: list[jax.Array] = []
    probe_metadata: list[tuple[int, float]] = []
    for probe_seed in probe_seeds:
        for radius in probe_radii:
            probe_grid.append(make_probe_set(probe_seed, int(spec["probe_count"]), radius))
            probe_metadata.append((probe_seed, radius))
    probe_grid_array = jnp.stack(probe_grid)

    scenario_engines: list[int] = []
    scenario_training_seed_indices: list[int] = []
    scenario_probe_indices: list[int] = []
    scenario_perturbation_indices: list[int] = []
    scenario_weights: list[jax.Array] = []
    scenario_probes: list[jax.Array] = []
    for engine in range(len(ENGINES)):
        for training_seed in range(len(seeds)):
            for probe_index in range(len(probe_metadata)):
                for perturbation in range(len(PERTURBATIONS)):
                    scenario_engines.append(engine)
                    scenario_training_seed_indices.append(training_seed)
                    scenario_probe_indices.append(probe_index)
                    scenario_perturbation_indices.append(perturbation)
                    scenario_weights.append(perturbed_weights[engine, training_seed, :, perturbation, :])
                    scenario_probes.append(probe_grid_array[probe_index])
    scenario_engines_array = jnp.asarray(scenario_engines, dtype=jnp.int32)
    scenario_weights_array = jnp.stack(scenario_weights)
    scenario_probes_array = jnp.stack(scenario_probes)
    sweep_scores = batched_score(
        scenario_engines_array,
        scenario_weights_array,
        scenario_probes_array,
        operator_matrices,
        operator_offsets,
    )
    sweep_total = sweep_scores[:, :, 0]
    sweep_shape = (
        len(ENGINES),
        len(seeds),
        len(probe_metadata),
        len(PERTURBATIONS),
        len(cycles),
    )
    sweep_total_tensor = sweep_total.reshape(sweep_shape)

    # The score itself contains an Axis-6 flip penalty. This direct output control
    # instead flips the source sign array while preserving engine/method indices.
    flipped_slot_axis6_up = jnp.logical_not(slot_axis6_up)

    @jax.jit
    def batched_score_with_flipped_source_axis6(
        scenario_engines_input: jax.Array,
        scenario_weights_input: jax.Array,
        scenario_probes_input: jax.Array,
    ) -> jax.Array:
        return jax.vmap(
            lambda engine, weights, probes: jax.vmap(
                lambda cycle, cycle_weights: score_cycle(
                    engine,
                    cycle,
                    cycle_weights,
                    probes,
                    geometry_slots,
                    entropy_slots,
                    slot_terrain,
                    flipped_slot_axis6_up,
                    slot_native,
                    terrain_matrices,
                    terrain_offsets,
                    operator_matrices,
                    operator_offsets,
                    terrain_fixed_points,
                    score_scales[0],
                    score_scales[1],
                    score_scales[2],
                    score_scales[3],
                )
            )(cycle_indices, weights)
        )(scenario_engines_input, scenario_weights_input, scenario_probes_input)

    parity_axis6_flipped = batched_score_with_flipped_source_axis6(
        parity_engines,
        parity_weights,
        parity_probes,
    )
    axis6_score_effect = jnp.abs(parity_scores[:, :, 0] - parity_axis6_flipped[:, :, 0])

    uniform_weights = jnp.tile(jnp.asarray((1.0, 0.35, 0.35, 0.35)), (len(cycles), 1))[None, :, :]
    control_engine = jnp.asarray((0,), dtype=jnp.int32)
    control_probe = probe_grid_array[0][None, :, :]
    identity_operators = jnp.tile(jnp.eye(3)[None, :, :], (len(OPS), 1, 1))
    zero_operator_offsets = jnp.zeros((len(OPS), 3), dtype=jnp.float64)
    erased_cycle_scores = batched_score(
        control_engine,
        uniform_weights,
        control_probe,
        identity_operators,
        zero_operator_offsets,
    )[0, :, 0]
    actual_uniform_cycle_scores = batched_score(
        control_engine,
        uniform_weights,
        control_probe,
        operator_matrices,
        operator_offsets,
    )[0, :, 0]
    erased_cycle_spread = jnp.max(erased_cycle_scores) - jnp.min(erased_cycle_scores)
    actual_uniform_cycle_spread = jnp.max(actual_uniform_cycle_scores) - jnp.min(actual_uniform_cycle_scores)
    scalar_first = score_scenario(
        scenario_engines_array[0],
        scenario_weights_array[0],
        scenario_probes_array[0],
        cycle_indices,
        geometry_slots,
        entropy_slots,
        slot_terrain,
        slot_axis6_up,
        slot_native,
        terrain_matrices,
        terrain_offsets,
        operator_matrices,
        operator_offsets,
        terrain_fixed_points,
        score_scales,
    )
    batched_scalar_error = jnp.max(jnp.abs(scalar_first - sweep_scores[0]))

    receipt_hash_rows = []
    for source_name, expected_hash in sorted(pytorch_result["source_hashes"].items()):
        source = REPO / source_name
        actual_hash = sha256(source) if source.exists() else None
        receipt_hash_rows.append(
            {
                "path": source_name,
                "expected_sha256": expected_hash,
                "actual_sha256": actual_hash,
                "match": actual_hash == expected_hash,
            }
        )

    axis6_method_separation = (
        spec["engine_method_policy"]["Type1_left"]
        == ["deductive_geometry", "inductive_entropy"]
        and spec["engine_method_policy"]["Type2_right"]
        == ["inductive_entropy", "deductive_geometry"]
        and axis6_counts == {
            "Type1_left": {"up": 4, "down": 4},
            "Type2_right": {"up": 4, "down": 4},
        }
    )
    actual_perturbation = jnp.abs(perturbed_weights - base_weights[..., None, :])
    perturbation_score_effect = jnp.max(
        jnp.abs(sweep_total_tensor[:, :, :, 1:, :] - sweep_total_tensor[:, :, :, :1, :])
    )
    receipt_global_claims_false = (
        pytorch_result["classification"] == "scratch_diagnostic"
        and pytorch_result["promotion_allowed"] is False
        and pytorch_result["formal_admission_allowed"] is False
        and pytorch_result["stage_movement_allowed"] is False
        and pytorch_result["universal_four_operator_basis_earned"] is False
        and pytorch_result["axis0_alignment_earned"] is False
    )
    expected_runtime = Path("/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3")
    controls = {
        "sim_stack_python_used": Path(sys.executable).resolve() == expected_runtime.resolve(),
        "jax_x64_enabled": bool(jax.config.read("jax_enable_x64")),
        "pytorch_receipt_is_scratch_with_global_claims_false": receipt_global_claims_false,
        "pytorch_receipt_source_hashes_match": all(row["match"] for row in receipt_hash_rows),
        "receipt_run_matrix_is_exactly_two_engines_by_six_cycles_by_three_seeds": (
            len(pytorch_result["runs"]) == 36
            and len(run_lookup) == 36
            and observed_run_keys == expected_run_keys
        ),
        "all_six_oriented_cycles_and_both_engines_swept": (
            len(cycles) == 6
            and len(ENGINES) == 2
            and sweep_total.shape[0]
            == len(ENGINES) * len(seeds) * len(probe_metadata) * len(PERTURBATIONS)
        ),
        "receipt_scores_reproduced_within_tolerance": bool(
            jax.device_get(jnp.max(score_reproduction_error) <= SCORE_REPRODUCTION_TOLERANCE)
        ),
        "receipt_aggregate_selected_cycles_reproduced": [
            int(item) for item in jax.device_get(nominal_winners)
        ]
        == reference_indices,
        "zero_perturbation_recovers_receipt_weights": bool(
            jax.device_get(jnp.max(actual_perturbation[..., 0, :]) == 0.0)
        ),
        "nonnative_weight_perturbations_respect_declared_linf_bound": bool(
            jax.device_get(jnp.max(actual_perturbation[..., 1:]) <= PERTURBATION_LINF_RADIUS + 1.0e-15)
        ),
        "native_weight_remains_exactly_one": bool(jax.device_get(jnp.all(perturbed_weights[..., 0] == 1.0))),
        "bounded_weight_perturbations_change_scores": bool(
            jax.device_get(perturbation_score_effect > 1.0e-10)
        ),
        "lineax_fixed_point_residuals_below_tolerance": bool(
            jax.device_get(jnp.max(fixed_point_residuals) <= FIXED_POINT_RESIDUAL_TOLERANCE)
        ),
        "type_chirality_and_axis6_are_encoded_as_separate_inputs": axis6_method_separation,
        "source_axis6_flip_changes_scores_without_swapping_engine_chirality": bool(
            jax.device_get(jnp.max(axis6_score_effect) > 1.0e-10)
        ),
        "operator_erasure_with_uniform_weights_collapses_cycle_ranking": bool(
            jax.device_get(erased_cycle_spread <= 1.0e-12)
        ),
        "actual_channels_with_uniform_weights_are_cycle_order_sensitive": bool(
            jax.device_get(actual_uniform_cycle_spread > 1.0e-8)
        ),
        "batched_and_scalar_scores_match": bool(jax.device_get(batched_scalar_error <= 1.0e-12)),
    }
    controls_all_pass = all(controls.values())

    rankings: dict[str, Any] = {}
    engine_stability: dict[str, bool] = {}
    for engine_index, engine in enumerate(ENGINES):
        engine_indices = [index for index, value in enumerate(scenario_engines) if value == engine_index]
        all_summary = ranking_summary(
            jnp.take(sweep_total, jnp.asarray(engine_indices), axis=0),
            cycles,
            reference_indices[engine_index],
        )
        baseline_indices = [
            index
            for index in engine_indices
            if scenario_perturbation_indices[index] == 0
        ]
        by_radius = {}
        for radius in probe_radii:
            radius_indices = [
                index
                for index in engine_indices
                if probe_metadata[scenario_probe_indices[index]][1] == radius
            ]
            by_radius[str(radius)] = ranking_summary(
                jnp.take(sweep_total, jnp.asarray(radius_indices), axis=0),
                cycles,
                reference_indices[engine_index],
            )
        baseline_summary = ranking_summary(
            jnp.take(sweep_total, jnp.asarray(baseline_indices), axis=0),
            cycles,
            reference_indices[engine_index],
        )
        nominal_order = jnp.argsort(nominal_aggregate_scores[engine_index])
        nominal_sorted = jnp.sort(nominal_aggregate_scores[engine_index])
        rankings[engine] = {
            "pytorch_receipt_selected_cycle": list(reference_cycles[engine_index]),
            "jax_reproduced_nominal_aggregate": {
                "cycle_scores": {
                    cycle_label(cycle): float(nominal_aggregate_scores[engine_index, cycle_index])
                    for cycle_index, cycle in enumerate(cycles)
                },
                "ranking": [list(cycles[int(index)]) for index in jax.device_get(nominal_order)],
                "top_two_margin": float(jax.device_get(nominal_sorted[1] - nominal_sorted[0])),
            },
            "all_scenarios": all_summary,
            "zero_perturbation_scenarios": baseline_summary,
            "by_probe_radius": by_radius,
        }
        engine_stability[engine] = bool(
            all_summary["reference_cycle_wins_every_scenario"]
            and all_summary["no_ties_under_declared_rule"]
        )

    ranking_stability_pass = controls_all_pass and all(engine_stability.values())
    if not controls_all_pass:
        verdict = "invalid_or_inconclusive_jax_scoring_controls_failed"
    elif ranking_stability_pass:
        verdict = "finite_cycle_ranking_stable_under_declared_jax_sweep_only"
    else:
        verdict = "cycle_ranking_unstable_or_tied_under_declared_jax_sweep"

    source_paths = (
        SOURCE_PATH,
        SPEC_PATH,
        PYTORCH_SOURCE_PATH,
        PYTORCH_RESULT_PATH,
        schedule_path,
        dependency_path,
        BASE_PATH,
    )
    result = {
        "schema": "codex_ratchet.dual_ratchet_stage_interior_learning_v0.jax_sweep_result.v1",
        "sim_id": spec["sim_id"],
        "classification": classification,
        "promotion_allowed": promotion_allowed,
        "formal_admission_allowed": formal_admission_allowed,
        "stage_movement_allowed": stage_movement_allowed,
        "sim_execution_kind": sim_execution_kind,
        "source_hashes": {relative(path): sha256(path) for path in source_paths},
        "pytorch_receipt_source_hash_audit": receipt_hash_rows,
        "package_fingerprint": {
            "python": platform.python_version(),
            "python_executable": sys.executable,
            "jax": package_version("jax"),
            "jaxlib": package_version("jaxlib"),
            "lineax": package_version("lineax"),
            "numpy": package_version("numpy"),
            "jax_enable_x64": bool(jax.config.read("jax_enable_x64")),
            "jax_default_backend": jax.default_backend(),
            "jax_devices": [str(device) for device in jax.devices()],
        },
        "jax": {
            "ran": True,
            "source_path": relative(SOURCE_PATH),
            "source_sha256": sha256(SOURCE_PATH),
            "packages_used": ["jax", "jax.numpy", "jax.scipy.linalg.expm", "lineax", "numpy"],
            "aligned_packages_load_bearing": ["jax", "jax.scipy.linalg.expm", "lineax"],
            "reads_peer_result": True,
            "peer_result_read_scope": "learned nonnative weights plus expected final scores for a reproduction control",
            "independent_scoring_implementation": True,
            "peer_read_ceiling": "robustness_consumer_only_not_independent_learning_or_cross_engine_confirmation",
            "batch_axes": [
                "engine",
                "learned_weight_seed",
                "probe_seed",
                "probe_radius",
                "weight_perturbation",
                "oriented_cycle",
            ],
            "batched_scenario_count": int(sweep_total.shape[0]),
            "batched_cycle_score_count": int(sweep_total.size),
        },
        "sweep_config": {
            "engines": list(ENGINES),
            "oriented_cycles": [list(cycle) for cycle in cycles],
            "learned_weight_seeds": seeds,
            "probe_generator": "jax.random.normal normalized to fixed radius",
            "probe_seeds": probe_seeds,
            "probe_radii": probe_radii,
            "probe_count_per_scenario": int(spec["probe_count"]),
            "perturbation_linf_radius": PERTURBATION_LINF_RADIUS,
            "perturbations": [
                {"name": name, "direction": list(direction)}
                for name, direction in PERTURBATIONS
            ],
            "scenario_count": int(sweep_total.shape[0]),
            "raw_scenario_arrays_emitted": False,
        },
        "chirality_axis6_separation": {
            "engine_chirality": spec["engine_method_policy"],
            "chirality_role_in_this_sweep": "engine-specific slot partition and learned-weight provenance; no JAX retraining claim",
            "axis6_role": "independent per-source-slot operator-first versus terrain-first channel composition",
            "axis6_derived_from_engine_chirality": False,
            "source_axis6_counts_by_engine": axis6_counts,
            "axis6_flip_preserves_engine_and_method_indices": True,
        },
        "controls": {
            "all_pass": controls_all_pass,
            "checks": controls,
            "measurements": {
                "maximum_receipt_score_absolute_error": float(jax.device_get(jnp.max(score_reproduction_error))),
                "maximum_receipt_score_relative_error": float(
                    jax.device_get(jnp.max(score_reproduction_relative_error))
                ),
                "maximum_actual_weight_perturbation": float(jax.device_get(jnp.max(actual_perturbation))),
                "maximum_weight_perturbation_score_effect": float(jax.device_get(perturbation_score_effect)),
                "maximum_lineax_fixed_point_residual": float(jax.device_get(jnp.max(fixed_point_residuals))),
                "maximum_source_axis6_flip_score_effect": float(jax.device_get(jnp.max(axis6_score_effect))),
                "operator_erasure_uniform_weight_cycle_score_spread": float(jax.device_get(erased_cycle_spread)),
                "actual_channel_uniform_weight_cycle_score_spread": float(
                    jax.device_get(actual_uniform_cycle_spread)
                ),
                "batched_scalar_max_absolute_error": float(jax.device_get(batched_scalar_error)),
            },
        },
        "ranking_stability": {
            "pass": ranking_stability_pass,
            "required_rule": "both receipt-selected engine-local cycles win every scenario with no declared ties",
            "engine_pass": engine_stability,
            "rankings": rankings,
        },
        "verdict_pass": ranking_stability_pass,
        "verdict": verdict,
        "universal_four_operator_basis_earned": False,
        "global_per_stage_four_substages_earned": False,
        "axis0_alignment_earned": False,
        "canonical_type1_type2_engines_earned": False,
        "canonical_four_beat_order_earned": False,
        "perception_claim_earned": False,
        "object_claim_earned": False,
        "blocked_consumers": [
            "universal four-operator basis",
            "canonical per-stage four-substage order",
            "Axis0 beginning/end alignment",
            "canonical Type-1/Type-2 engine admission",
            "perception or object claims",
        ],
        "claim_ceiling": (
            "A green result could show only that the PyTorch-learned finite cycle ranking survives the declared "
            "JAX probe/weight sweep. It cannot earn universal four, Axis0, canonical engines or order, perception, "
            "objects, promotion, formal admission, or stage movement."
        ),
        "tool_calls": [
            {
                "tool": "jax",
                "qualified_api/function": "jax.jit(jax.vmap(score_scenario))",
                "input_object": "1080 compact scenarios over two engines, six cycles, learned seeds, probe seeds/radii, and bounded weight perturbations",
                "output_object": "6480 geometry-plus-entropy cycle scores summarized as rankings and margins",
                "positive_case": "actual finite terrain/operator channels with receipt-learned weights",
                "negative/erased_control": "identity operator erasure plus uniform nonnative weights collapses all cycle scores",
                "boundary_case": "zero perturbation reproduces the receipt weights and original PCG64 probes reproduce receipt scores",
                "demotion_condition": "score reproduction, scalar/batch agreement, erasure, or coverage control failure",
                "gates": ["controls.all_pass", "ranking_stability.pass", "verdict_pass"],
            },
            {
                "tool": "jax.scipy.linalg.expm",
                "qualified_api/function": "jax.scipy.linalg.expm",
                "input_object": "eight 4x4 complex GKSL Liouvillians and x/z unitary generators",
                "output_object": "finite x64 terrain and operator Bloch-affine channels",
                "positive_case": "source-aligned house channel reconstruction",
                "negative/erased_control": "operator maps replaced by identity in cycle-erasure control",
                "boundary_case": "affine channel extracted from zero and Cartesian Bloch basis states",
                "demotion_condition": "receipt scoring cannot be reproduced within tolerance",
                "gates": ["controls.all_pass", "ranking_stability.pass"],
            },
            {
                "tool": "lineax",
                "qualified_api/function": "lineax.linear_solve(MatrixLinearOperator, solver=lineax.LU)",
                "input_object": "eight finite (I - terrain_matrix) fixed-point systems",
                "output_object": "terrain reference Bloch vectors for relative entropy",
                "positive_case": "all eight fixed-point residuals below tolerance",
                "negative/erased_control": "control fails closed if any residual exceeds tolerance",
                "boundary_case": "affine nonunital damping terrains",
                "demotion_condition": "maximum fixed-point residual exceeds 1e-10",
                "gates": ["controls.all_pass", "ranking_stability.pass", "verdict_pass"],
            },
        ],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "roles_run": {
            "builder": "current bounded JAX worker",
            "mechanical_gatekeeper": "self-check controls in this artifact only",
            "fresh_context_fabrication_auditor": "not_run",
            "controller_admission": "not_run",
        },
    }
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(jsonable(result), indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "result_path": str(RESULT_PATH),
                "controls_all_pass": controls_all_pass,
                "ranking_stability_pass": ranking_stability_pass,
                "verdict": verdict,
                "engine_pass": engine_stability,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if controls_all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
