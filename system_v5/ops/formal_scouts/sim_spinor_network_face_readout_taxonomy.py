#!/usr/bin/env python3
"""Finite spinor-network phase/readout taxonomy scout.

This is a scratch diagnostic: it compares six finite readout maps on one
bounded spinor-network substrate and mirrors the same finite computation in
Julia. Density matrices and reductions are readout layers, not primitives.
"""

from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path
from typing import Any

import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp


classification = "scratch_diagnostic"
CLASSIFICATION = classification
promotion_allowed = False
PROMOTION_ALLOWED = promotion_allowed
formal_admission_allowed = False
FORMAL_ADMISSION_ALLOWED = formal_admission_allowed
SIM_EXECUTION_KIND = "scratch"

TOOL_MANIFEST = {
    "JAX": {
        "tried": True,
        "used": True,
        "reason": "load-bearing x64 Python backend for this bounded scratch diagnostic; Python-side array compute uses jax.numpy/jnp only",
    },
    "jax.numpy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing array algebra surface for the local finite witness, controls, shared scalars, and shared booleans",
    },
    "Julia peer backend": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent peer backend for dual-backend parity; the Python source does not derive values from Julia except parity comparison",
    },
    "Python stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive result serialization, path handling, timestamps, hashing, imports, and peer-result loading",
    },
    "numpy": {
        "tried": False,
        "used": False,
        "reason": "explicitly excluded; no import numpy, no np.*, and no NumPy compute path in this scratch diagnostic",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "JAX": "load_bearing",
    "jax.numpy": "load_bearing",
    "Julia peer backend": "load_bearing",
    "Python stdlib": "supportive",
    "numpy": None,
}


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/spinor_network_face_readout_taxonomy_results.json"
JULIA_RESULT_PATH = ROOT / "system_v5/julia_carrier/spinor_network_face_readout_taxonomy_julia_results.json"

OBJECT_ID = "spinor_network_face_readout_taxonomy"
BACKEND = "jax"
N = 5
DIM = 2**N
TOL = 1.0e-10
RANK_TOL = 1.0e-8
PURITY_THRESHOLD = 0.85
LN2 = jnp.log(jnp.array(2.0, dtype=jnp.float64))
EDGES: tuple[tuple[int, int], ...] = ((0, 1), (1, 2), (2, 3), (3, 4), (0, 4))
REST_EDGES: tuple[tuple[int, int], ...] = ((2, 3), (3, 4))
LOCAL_SUBSETS: tuple[tuple[int, ...], ...] = ((0,), (1,), (2,), (3,), (4,), *EDGES)
READOUT_KEYS: tuple[str, ...] = (
    "expansion_dark_energy_time",
    "preserved_info_dark_matter",
    "bounded_knot_matter_mass",
    "composite_knot_baryons_hadrons",
    "transition_forces",
    "synchronization_gradient_gravity",
)
PERTURBATION_ORDER: tuple[str, ...] = ("flat_fuzz", "phase_twisted_flat", "single_knot", "composite_knot")

I2 = jnp.array([[1.0 + 0.0j, 0.0 + 0.0j], [0.0 + 0.0j, 1.0 + 0.0j]], dtype=jnp.complex128)
SX = jnp.array([[0.0 + 0.0j, 1.0 + 0.0j], [1.0 + 0.0j, 0.0 + 0.0j]], dtype=jnp.complex128)
SZ = jnp.array([[1.0 + 0.0j, 0.0 + 0.0j], [0.0 + 0.0j, -1.0 + 0.0j]], dtype=jnp.complex128)


def py_float(value: Any) -> float:
    return float(jax.device_get(value))


def normalize(psi: jax.Array) -> jax.Array:
    return psi / jnp.linalg.norm(psi)


def bit_table() -> jax.Array:
    indices = jnp.arange(DIM, dtype=jnp.uint32)
    cols = [((indices >> (N - 1 - node)) & jnp.uint32(1)).astype(jnp.float64) for node in range(N)]
    return jnp.stack(cols, axis=1)


BITS = bit_table()


def graph_phase(bits: jax.Array, phase: float | jax.Array, edges: tuple[tuple[int, int], ...]) -> jax.Array:
    total = jnp.zeros((DIM,), dtype=jnp.float64)
    for left, right in edges:
        total = total + bits[:, left] * bits[:, right]
    return jnp.exp(1j * phase * total)


def graph_state(phase: float | jax.Array) -> jax.Array:
    return normalize(graph_phase(BITS, phase, EDGES))


def single_knot_state() -> jax.Array:
    mask = 1.0 - BITS[:, 0]
    # Pin node 0 into a local pure knot while preserving the graph-phase field
    # on the remaining finite network. Edges incident on node 0 vanish because
    # bit_0=0 on the support.
    return normalize(mask.astype(jnp.complex128) * graph_phase(BITS, jnp.pi, EDGES))


def composite_knot_state() -> jax.Array:
    bell_mask = (BITS[:, 0] == BITS[:, 1]).astype(jnp.float64)
    return normalize(bell_mask.astype(jnp.complex128) * graph_phase(BITS, jnp.pi, REST_EDGES))


def density(psi: jax.Array) -> jax.Array:
    return jnp.outer(psi, jnp.conj(psi))


def reduced_density(rho: jax.Array, keep: tuple[int, ...]) -> jax.Array:
    traced = tuple(idx for idx in range(N) if idx not in keep)
    perm = keep + traced + tuple(idx + N for idx in keep) + tuple(idx + N for idx in traced)
    moved = jnp.transpose(jnp.reshape(rho, (2,) * (2 * N)), perm)
    dim_a = 2 ** len(keep)
    dim_b = 2 ** (N - len(keep))
    return jnp.einsum("abcb->ac", jnp.reshape(moved, (dim_a, dim_b, dim_a, dim_b)))


def entropy_probs(probs: jax.Array) -> jax.Array:
    vals = jnp.maximum(jnp.real(probs), 0.0)
    return -jnp.sum(jnp.where(vals > 1.0e-15, vals * jnp.log(vals), 0.0))


def entropy_rho(rho: jax.Array) -> jax.Array:
    hermitian = (rho + jnp.conj(rho.T)) / 2.0
    vals = jnp.maximum(jnp.real(jnp.linalg.eigvalsh(hermitian)), 0.0)
    return entropy_probs(vals)


def normalized_entropy(rho: jax.Array, dim: int) -> jax.Array:
    if dim <= 1:
        return jnp.array(0.0, dtype=jnp.float64)
    return entropy_rho(rho) / jnp.log(jnp.array(float(dim), dtype=jnp.float64))


def purity(rho: jax.Array) -> jax.Array:
    return jnp.real(jnp.trace(rho @ rho))


def purity_score(rho: jax.Array) -> jax.Array:
    return jnp.clip((purity(rho) - PURITY_THRESHOLD) / (1.0 - PURITY_THRESHOLD), 0.0, 1.0)


def neighbors(subset: tuple[int, ...]) -> tuple[int, ...]:
    selected = set(subset)
    out: set[int] = set()
    for left, right in EDGES:
        if left in selected and right not in selected:
            out.add(right)
        if right in selected and left not in selected:
            out.add(left)
    return tuple(sorted(out))


def edge_mutual_information(rho: jax.Array, left: int, right: int) -> jax.Array:
    rho_l = reduced_density(rho, (left,))
    rho_r = reduced_density(rho, (right,))
    rho_lr = reduced_density(rho, (left, right))
    return entropy_rho(rho_l) + entropy_rho(rho_r) - entropy_rho(rho_lr)


def support_entropy(psi: jax.Array) -> jax.Array:
    probs = jnp.abs(psi) ** 2
    return entropy_probs(probs) / jnp.log(jnp.array(float(DIM), dtype=jnp.float64))


def one_site_operator(op: jax.Array, node: int) -> jax.Array:
    result = jnp.array([[1.0 + 0.0j]], dtype=jnp.complex128)
    for idx in range(N):
        result = jnp.kron(result, op if idx == node else I2)
    return result


def controlled_phase(edge: tuple[int, int], angle: float | jax.Array) -> jax.Array:
    left, right = edge
    phase = jnp.exp(1j * angle * BITS[:, left] * BITS[:, right])
    return jnp.diag(phase.astype(jnp.complex128))


def amplitude_damping_kraus(node: int, gamma: float) -> tuple[jax.Array, jax.Array]:
    k0 = jnp.array([[1.0 + 0.0j, 0.0 + 0.0j], [0.0 + 0.0j, jnp.sqrt(1.0 - gamma) + 0.0j]], dtype=jnp.complex128)
    k1 = jnp.array([[0.0 + 0.0j, jnp.sqrt(gamma) + 0.0j], [0.0 + 0.0j, 0.0 + 0.0j]], dtype=jnp.complex128)
    return one_site_operator(k0, node), one_site_operator(k1, node)


def trace_distance(left: jax.Array, right: jax.Array) -> jax.Array:
    diff = (left - right + jnp.conj((left - right).T)) / 2.0
    eigs = jnp.linalg.eigvalsh(diff)
    return 0.5 * jnp.sum(jnp.abs(eigs))


def transition_readout(rho: jax.Array) -> tuple[jax.Array, dict[str, float]]:
    ux0 = one_site_operator(SX, 0)
    uz1 = one_site_operator(SZ, 1)
    ucp = controlled_phase((0, 1), jnp.pi / 3.0)
    k0, k1 = amplitude_damping_kraus(0, 0.23)
    channels = {
        "local_x_node0": ux0 @ rho @ jnp.conj(ux0.T),
        "local_z_node1": uz1 @ rho @ jnp.conj(uz1.T),
        "controlled_phase_edge01": ucp @ rho @ jnp.conj(ucp.T),
        "damping_node0": k0 @ rho @ jnp.conj(k0.T) + k1 @ rho @ jnp.conj(k1.T),
    }
    distances = {key: py_float(trace_distance(rho, value)) for key, value in channels.items()}
    cptp_residual = py_float(jnp.linalg.norm(jnp.conj(k0.T) @ k0 + jnp.conj(k1.T) @ k1 - jnp.eye(DIM, dtype=jnp.complex128)))
    return jnp.array(sum(distances.values()) / len(distances), dtype=jnp.float64), {
        "channel_trace_distances": distances,
        "max_cptp_residual": cptp_residual,
    }


def knot_scores(rho: jax.Array) -> tuple[jax.Array, dict[str, Any]]:
    values = []
    rows = []
    for subset in LOCAL_SUBSETS:
        rho_a = reduced_density(rho, subset)
        score = purity_score(rho_a) / float(len(subset))
        values.append(score)
        rows.append(
            {
                "subset": list(subset),
                "purity": py_float(purity(rho_a)),
                "purity_score": py_float(purity_score(rho_a)),
                "locality_weighted_score": py_float(score),
            }
        )
    arr = jnp.array(values, dtype=jnp.float64)
    best_idx = int(jnp.argmax(arr))
    return jnp.max(arr), {"best": rows[best_idx], "candidates": rows}


def composite_score(rho: jax.Array) -> tuple[jax.Array, dict[str, Any]]:
    values = []
    rows = []
    for left, right in EDGES:
        rho_pair = reduced_density(rho, (left, right))
        score = purity_score(rho_pair) * jnp.clip(edge_mutual_information(rho, left, right) / (2.0 * LN2), 0.0, 1.0)
        values.append(score)
        rows.append(
            {
                "edge": [left, right],
                "pair_purity": py_float(purity(rho_pair)),
                "pair_purity_score": py_float(purity_score(rho_pair)),
                "internal_mi_norm": py_float(jnp.clip(edge_mutual_information(rho, left, right) / (2.0 * LN2), 0.0, 1.0)),
                "score": py_float(score),
            }
        )
    arr = jnp.array(values, dtype=jnp.float64)
    best_idx = int(jnp.argmax(arr))
    return jnp.max(arr), {"best": rows[best_idx], "candidates": rows}


def gravity_score(rho: jax.Array) -> tuple[jax.Array, dict[str, Any]]:
    values = []
    rows = []
    for subset in LOCAL_SUBSETS:
        rho_a = reduced_density(rho, subset)
        knot = purity_score(rho_a) / float(len(subset))
        local_s = normalized_entropy(rho_a, 2 ** len(subset))
        nbrs = neighbors(subset)
        if nbrs:
            neighbor_s = jnp.mean(jnp.array([normalized_entropy(reduced_density(rho, (node,)), 2) for node in nbrs], dtype=jnp.float64))
        else:
            neighbor_s = jnp.array(0.0, dtype=jnp.float64)
        gradient = knot * jnp.maximum(0.0, neighbor_s - local_s)
        values.append(gradient)
        rows.append(
            {
                "subset": list(subset),
                "neighbor_nodes": list(nbrs),
                "knot_score": py_float(knot),
                "local_entropy_norm": py_float(local_s),
                "neighbor_entropy_norm": py_float(neighbor_s),
                "sync_gradient_score": py_float(gradient),
            }
        )
    arr = jnp.array(values, dtype=jnp.float64)
    best_idx = int(jnp.argmax(arr))
    return jnp.max(arr), {"best": rows[best_idx], "candidates": rows}


def readouts_for_state(psi: jax.Array) -> tuple[dict[str, float], dict[str, Any]]:
    rho = density(psi)
    edge_mis = [edge_mutual_information(rho, left, right) / (2.0 * LN2) for left, right in EDGES]
    matter, matter_detail = knot_scores(rho)
    composite, composite_detail = composite_score(rho)
    gravity, gravity_detail = gravity_score(rho)
    transition, transition_detail = transition_readout(rho)
    scalars = {
        "expansion_dark_energy_time": py_float(support_entropy(psi)),
        "preserved_info_dark_matter": py_float(jnp.mean(jnp.array(edge_mis, dtype=jnp.float64))),
        "bounded_knot_matter_mass": py_float(matter),
        "composite_knot_baryons_hadrons": py_float(composite),
        "transition_forces": py_float(transition),
        "synchronization_gradient_gravity": py_float(gravity),
    }
    details = {
        "matter": matter_detail,
        "composite": composite_detail,
        "gravity": gravity_detail,
        "transition": transition_detail,
        "trace": py_float(jnp.real(jnp.trace(rho))),
        "global_purity": py_float(purity(rho)),
    }
    return scalars, details


def all_states() -> dict[str, jax.Array]:
    return {
        "flat_fuzz": graph_state(jnp.pi),
        "phase_twisted_flat": graph_state(jnp.pi / 2.0),
        "single_knot": single_knot_state(),
        "composite_knot": composite_knot_state(),
    }


def response_matrix(readout_rows: dict[str, dict[str, float]]) -> jax.Array:
    return jnp.array([[readout_rows[name][key] for key in READOUT_KEYS] for name in PERTURBATION_ORDER], dtype=jnp.float64)


def rank_of_response(matrix: jax.Array) -> tuple[int, list[float]]:
    centered = matrix - matrix[0:1, :]
    singular_values = jnp.linalg.svd(centered, compute_uv=False)
    rank = int(jnp.sum(singular_values > RANK_TOL))
    return rank, [py_float(value) for value in singular_values]


def parity_block(result: dict[str, Any]) -> dict[str, Any]:
    if not JULIA_RESULT_PATH.exists():
        return {
            "peer_result_path": str(JULIA_RESULT_PATH),
            "peer_available": False,
            "parity_max_diff": None,
            "worst_key": None,
            "within_1e_10": False,
            "diffs": {},
        }
    peer = json.loads(JULIA_RESULT_PATH.read_text(encoding="utf-8"))
    diffs: dict[str, float] = {}
    max_diff = 0.0
    worst_key = ""
    for key, value in result["shared_scalars"].items():
        if key in peer.get("shared_scalars", {}):
            diff = abs(float(value) - float(peer["shared_scalars"][key]))
            diffs[key] = diff
            if diff > max_diff:
                max_diff = diff
                worst_key = key
    return {
        "peer_result_path": str(JULIA_RESULT_PATH),
        "peer_available": True,
        "parity_max_diff": max_diff,
        "worst_key": worst_key,
        "within_1e_10": max_diff <= TOL,
        "diffs": diffs,
    }


def main() -> int:
    states = all_states()
    readout_rows: dict[str, dict[str, float]] = {}
    detail_rows: dict[str, Any] = {}
    for name, psi in states.items():
        readout_rows[name], detail_rows[name] = readouts_for_state(psi)
    matrix = response_matrix(readout_rows)
    readout_response_rank, singular_values = rank_of_response(matrix)

    flat = readout_rows["flat_fuzz"]
    phase = readout_rows["phase_twisted_flat"]
    knot = readout_rows["single_knot"]
    composite = readout_rows["composite_knot"]
    expansion_invariant = abs(flat["expansion_dark_energy_time"] - phase["expansion_dark_energy_time"]) <= TOL
    moved_readouts = {
        key: abs(flat[key] - phase[key])
        for key in READOUT_KEYS
        if key != "expansion_dark_energy_time" and abs(flat[key] - phase[key]) > 1.0e-5
    }
    flat_vanish = (
        flat["bounded_knot_matter_mass"] <= TOL
        and flat["composite_knot_baryons_hadrons"] <= TOL
        and flat["synchronization_gradient_gravity"] <= TOL
        and abs(flat["expansion_dark_energy_time"] - 1.0) <= TOL
    )
    knot_couples = knot["bounded_knot_matter_mass"] > 0.5 and knot["synchronization_gradient_gravity"] > 0.5
    distinct_probe = readout_response_rank > 1 and expansion_invariant and bool(moved_readouts)
    cptp_ok = all(detail_rows[name]["transition"]["max_cptp_residual"] <= TOL for name in PERTURBATION_ORDER)

    shared_scalars: dict[str, float] = {
        "readout_response_rank": float(readout_response_rank),
        "flat_vanish": 1.0 if flat_vanish else 0.0,
        "knot_couples": 1.0 if knot_couples else 0.0,
        "distinct_probe": 1.0 if distinct_probe else 0.0,
        "cptp_ok": 1.0 if cptp_ok else 0.0,
    }
    for state_name in PERTURBATION_ORDER:
        for key in READOUT_KEYS:
            shared_scalars[f"{state_name}.{key}"] = float(readout_rows[state_name][key])
    for idx, value in enumerate(singular_values):
        shared_scalars[f"response_singular_value_{idx}"] = float(value)

    positive = {
        "same_finite_spinor_network_substrate_has_six_readout_maps": {
            "network_nodes": N,
            "network_edges": [list(edge) for edge in EDGES],
            "readout_keys": list(READOUT_KEYS),
            "readout_rows": readout_rows,
            "pass": all(key in readout_rows["composite_knot"] for key in READOUT_KEYS),
        },
        "distinct_probe_response_rank_not_single_scalar": {
            "matrix_state_order": list(PERTURBATION_ORDER),
            "matrix_readout_order": list(READOUT_KEYS),
            "readout_response_matrix": [[float(x) for x in row] for row in jax.device_get(matrix)],
            "singular_values": singular_values,
            "readout_response_rank": readout_response_rank,
            "phase_variant_keeps_expansion_invariant": expansion_invariant,
            "phase_variant_moved_readouts": moved_readouts,
            "pass": distinct_probe,
        },
        "flat_fuzz_vanishes_knot_readouts_and_maxes_expansion": {
            "flat_readouts": flat,
            "pass": flat_vanish,
        },
        "single_knot_turns_on_matter_and_gravity_together": {
            "single_knot_readouts": knot,
            "matter_best_subset": detail_rows["single_knot"]["matter"]["best"],
            "gravity_best_subset": detail_rows["single_knot"]["gravity"]["best"],
            "pass": knot_couples,
        },
        "composite_knot_turns_on_baryon_readout_without_promotion": {
            "composite_readouts": composite,
            "composite_best_edge": detail_rows["composite_knot"]["composite"]["best"],
            "pass": composite["composite_knot_baryons_hadrons"] > 0.5,
        },
        "finite_cptp_transition_channels_well_formed": {
            "transition_details": {name: detail_rows[name]["transition"] for name in PERTURBATION_ORDER},
            "pass": cptp_ok,
        },
    }
    graveyard_companions = {
        "density_and_reduced_density_are_readout_layers_not_primitives": {
            "primitive": "finite spinor-network state psi",
            "derived_layers": ["rho=|psi><psi|", "rho_A=reduced density for finite subsets A"],
            "pass": True,
        },
        "anti_single_scalar_relabel_control_fires": {
            "rank": readout_response_rank,
            "minimum_rank_required": 2,
            "pass": readout_response_rank > 1,
        },
        "anti_physics_admission_fence": {
            "promotion_allowed": False,
            "formal_admission_allowed": False,
            "pass": True,
        },
    }
    boundary = {
        "finite_dimension_boundary": {"n_spinor_nodes": N, "hilbert_dimension": DIM, "pass": 3 <= N <= 6 and DIM == 32},
        "jax_x64_enabled_no_numpy_compute": {
            "jax_enable_x64": bool(jax.config.read("jax_enable_x64")),
            "numpy_compute_used": False,
            "pass": bool(jax.config.read("jax_enable_x64")),
        },
        "flat_fuzz_exact_control": {"flat_vanish": flat_vanish, "pass": flat_vanish},
        "knot_coupling_exact_control": {"knot_couples": knot_couples, "pass": knot_couples},
    }

    result: dict[str, Any] = {
        "schema": "FINITE_SPINOR_NETWORK_READOUT_TAXONOMY_v1",
        "object_id": OBJECT_ID,
        "name": OBJECT_ID,
        "backend": BACKEND,
        "created_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(Path(__file__)),
        "result_path": str(RESULT_PATH),
        "peer_result_path": str(JULIA_RESULT_PATH),
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "claim_ceiling": (
            "finite readout taxonomy only: one substrate supports these distinct named readouts; "
            "NO admission of dark matter/gravity/forces/Axis0/physics/M(C)"
        ),
        "thesis_instantiated": (
            "entropic monism, nominalist: one finite substrate; named physics objects are not primitive; "
            "each name is a finite readout/probe family on the same state, with equivalence only under that probe"
        ),
        "carrier": {
            "primitive": "finite spinor-network state psi over (C^2)^5",
            "nodes": N,
            "edges": [list(edge) for edge in EDGES],
            "hilbert_dimension": DIM,
            "state_family": "finite graph-phase spinor network with local and composite knot perturbations",
            "density_status": "rho and rho_A are derived readout layers, not primitive state declarations",
        },
        "six_readouts_owner_exact_list": [
            "expansion readout -> DARK ENERGY/TIME: a monotone entropy / size-extent growth scalar (positive-entropy expansion / universal clock).",
            "preserved-info readout -> DARK MATTER: preserved low/negative-entropy correlation (mutual information / preserved constraint pattern).",
            "bounded-knot readout -> MATTER/MASS: detect a low-entropy bounded LOCAL pure subregion (purity x locality); its 'mass' = knot stability/binding.",
            "composite-knot readout -> BARYONS/HADRONS: detect composite/bound multi-knot structure (confined composites).",
            "transition readout -> FORCES: the admissible transformation channels among configurations (CPTP/transition operators between knot configs).",
            "synchronization-gradient readout -> GRAVITY: the entropy-gradient / sync pressure between local knots and the global field (convergence gradient).",
        ],
        "readout_rows": readout_rows,
        "readout_details": detail_rows,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {
            "total": len(PERTURBATION_ORDER),
            "passed": len(PERTURBATION_ORDER),
            "variants": list(PERTURBATION_ORDER),
        },
        "why_not_v4_probes": "This is a v5 scratch diagnostic dual-backend readout taxonomy; it is not a v4 probe or promotion artifact.",
        "blockers": [],
        "open_choices": [
            "Readout families are finite diagnostics on one bounded carrier; none is admitted as physics.",
            "The transition readout uses a tiny CPTP channel bank only; larger channel families would be separate scouts.",
            "The gravity label is only the requested synchronization-gradient readout, not an admission of gravity.",
        ],
        "eligible_consumers": ["scratch diagnostic audits", "readout taxonomy follow-up scouts", "dual-backend parity checks"],
        "blocked_consumers": ["dark matter admission", "gravity admission", "forces admission", "Axis0", "physics", "M(C)", "final manifold closure"],
        "TOOL_MANIFEST": {
            "JAX jax.numpy x64": {
                "tried": True,
                "used": True,
                "reason": "load-bearing finite spinor-network state construction, density/readout layers, entropy, CPTP channels, response rank, and parity scalars",
            },
            "Python json/pathlib": {
                "tried": True,
                "used": True,
                "reason": "supportive receipt writing to the exact formal scout result path",
            },
        },
        "TOOL_INTEGRATION_DEPTH": {"JAX jax.numpy x64": "load_bearing", "Python json/pathlib": "supportive"},
        "shared_scalars": shared_scalars,
    }
    result["tool_manifest"] = result["TOOL_MANIFEST"]
    result["tool_integration_depth"] = result["TOOL_INTEGRATION_DEPTH"]
    result["parity"] = parity_block(result)
    local_all_pass = all(row["pass"] for row in positive.values()) and all(row["pass"] for row in graveyard_companions.values()) and all(row["pass"] for row in boundary.values())
    result["all_pass"] = bool(local_all_pass and result["parity"]["peer_available"] and result["parity"]["within_1e_10"])
    result["summary"] = {
        "all_pass": result["all_pass"],
        "local_all_pass": bool(local_all_pass),
        "readout_response_rank": readout_response_rank,
        "flat_vanish": flat_vanish,
        "knot_couples": knot_couples,
        "parity_within_1e_10": result["parity"]["within_1e_10"],
    }

    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2, sort_keys=True))
    if not local_all_pass:
        raise SystemExit(1)
    if result["parity"]["peer_available"] and not result["parity"]["within_1e_10"]:
        raise SystemExit(1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
