#!/usr/bin/env python3
"""Finite force/transition-channel taxonomy scout.

This is a scratch diagnostic that starts from the completed face-readout
taxonomy carrier and asks a narrower next question: can "force" labels be
represented as distinct finite transition channels on one spinor-network
substrate, rather than as names pasted onto one scalar?

Claim ceiling: finite channel taxonomy only. No force, particle, gravity,
Axis0, physics, M(C), PEPS3D, or bridge admission.
"""

from __future__ import annotations

import datetime as _dt
import importlib.util
import json
from pathlib import Path
from typing import Any, Callable

import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
FACE_SOURCE = ROOT / "system_v5/ops/formal_scouts/sim_spinor_network_face_readout_taxonomy.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/spinor_network_force_transition_channel_taxonomy_results.json"
JULIA_RESULT_PATH = ROOT / "system_v5/julia_carrier/spinor_network_force_transition_channel_taxonomy_julia_results.json"

OBJECT_ID = "spinor_network_force_transition_channel_taxonomy"
CLASSIFICATION = "scratch_diagnostic"
TOL = 1.0e-10
RANK_TOL = 1.0e-8


def load_face_module() -> Any:
    spec = importlib.util.spec_from_file_location("face_taxonomy", FACE_SOURCE)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load face taxonomy source: {FACE_SOURCE}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ft = load_face_module()

FORCE_KEYS: tuple[str, ...] = (
    "electromagnetic_phase_coupling",
    "strong_binding_confinement",
    "weak_decay_topology_change",
    "gravity_sync_flattening",
)
DELTA_KEYS: tuple[str, ...] = (
    "expansion_dark_energy_time",
    "preserved_info_dark_matter",
    "bounded_knot_matter_mass",
    "composite_knot_baryons_hadrons",
    "transition_forces",
    "synchronization_gradient_gravity",
)
CHANNEL_ORDER: tuple[str, ...] = ("identity_control", *FORCE_KEYS)


def py_float(value: Any) -> float:
    return float(jax.device_get(value))


def bell_edge_density() -> jax.Array:
    vec = jnp.zeros((4,), dtype=jnp.complex128)
    vec = vec.at[0].set(1.0 / jnp.sqrt(2.0))
    vec = vec.at[3].set(1.0 / jnp.sqrt(2.0))
    return jnp.outer(vec, jnp.conj(vec))


def replace_leading_subsystem(rho: jax.Array, replacement: jax.Array, n_replace: int) -> jax.Array:
    """Trace-and-prepare the leading nodes; CPTP for fixed replacement state."""
    rest = ft.reduced_density(rho, tuple(range(n_replace, ft.N)))
    return jnp.kron(replacement, rest)


def identity_channel(rho: jax.Array) -> jax.Array:
    return rho


def electromagnetic_phase_channel(rho: jax.Array) -> jax.Array:
    unitary = ft.controlled_phase((0, 1), jnp.pi / 5.0)
    return unitary @ rho @ jnp.conj(unitary.T)


def strong_binding_channel(rho: jax.Array) -> jax.Array:
    return replace_leading_subsystem(rho, bell_edge_density(), 2)


def weak_decay_channel(rho: jax.Array) -> jax.Array:
    return replace_leading_subsystem(rho, ft.I2 / 2.0, 1)


def gravity_sync_channel(rho: jax.Array) -> jax.Array:
    flat = ft.density(ft.graph_state(jnp.pi))
    return 0.65 * rho + 0.35 * flat


CHANNELS: dict[str, Callable[[jax.Array], jax.Array]] = {
    "identity_control": identity_channel,
    "electromagnetic_phase_coupling": electromagnetic_phase_channel,
    "strong_binding_confinement": strong_binding_channel,
    "weak_decay_topology_change": weak_decay_channel,
    "gravity_sync_flattening": gravity_sync_channel,
}


def selected_input_states() -> dict[str, jax.Array]:
    single = ft.density(ft.single_knot_state())
    return {
        "identity_control": single,
        "electromagnetic_phase_coupling": ft.density(ft.graph_state(jnp.pi / 2.0)),
        "strong_binding_confinement": single,
        "weak_decay_topology_change": single,
        "gravity_sync_flattening": single,
    }


def density_readouts(rho: jax.Array) -> tuple[dict[str, float], dict[str, Any]]:
    diagonal_probs = jnp.real(jnp.diag(rho))
    expansion = ft.entropy_probs(diagonal_probs) / jnp.log(jnp.array(float(ft.DIM), dtype=jnp.float64))
    edge_mis = [ft.edge_mutual_information(rho, left, right) / (2.0 * ft.LN2) for left, right in ft.EDGES]
    matter, matter_detail = ft.knot_scores(rho)
    composite, composite_detail = ft.composite_score(rho)
    gravity, gravity_detail = ft.gravity_score(rho)
    transition, transition_detail = ft.transition_readout(rho)
    readouts = {
        "expansion_dark_energy_time": py_float(expansion),
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
        "min_eigenvalue": py_float(jnp.min(jnp.linalg.eigvalsh((rho + jnp.conj(rho.T)) / 2.0))),
    }
    return readouts, details


def channel_record(name: str, input_rho: jax.Array) -> dict[str, Any]:
    output_rho = CHANNELS[name](input_rho)
    before, before_details = density_readouts(input_rho)
    after, after_details = density_readouts(output_rho)
    delta = {key: after[key] - before[key] for key in DELTA_KEYS}
    trace = py_float(jnp.real(jnp.trace(output_rho)))
    min_eig = py_float(jnp.min(jnp.linalg.eigvalsh((output_rho + jnp.conj(output_rho.T)) / 2.0)))
    return {
        "input_readouts": before,
        "output_readouts": after,
        "delta": delta,
        "trace_distance": py_float(ft.trace_distance(input_rho, output_rho)),
        "output_trace": trace,
        "output_min_eigenvalue": min_eig,
        "input_details": before_details,
        "output_details": after_details,
        "density_valid": abs(trace - 1.0) <= TOL and min_eig >= -1.0e-9,
    }


def response_matrix(records: dict[str, Any]) -> jax.Array:
    return jnp.array([[records[name]["delta"][key] for key in DELTA_KEYS] for name in FORCE_KEYS], dtype=jnp.float64)


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
    inputs = selected_input_states()
    records = {name: channel_record(name, inputs[name]) for name in CHANNEL_ORDER}
    matrix = response_matrix(records)
    singular_values = jnp.linalg.svd(matrix, compute_uv=False)
    channel_response_rank = int(jnp.sum(singular_values > RANK_TOL))

    identity_zero = all(abs(records["identity_control"]["delta"][key]) <= TOL for key in DELTA_KEYS)
    em = records["electromagnetic_phase_coupling"]
    strong = records["strong_binding_confinement"]
    weak = records["weak_decay_topology_change"]
    sync = records["gravity_sync_flattening"]
    em_phase_selective = (
        em["trace_distance"] > 0.05
        and abs(em["delta"]["expansion_dark_energy_time"]) <= TOL
        and abs(em["delta"]["bounded_knot_matter_mass"]) <= TOL
        and abs(em["delta"]["synchronization_gradient_gravity"]) <= TOL
        and abs(em["delta"]["preserved_info_dark_matter"]) > 1.0e-3
    )
    strong_binding_selective = (
        strong["delta"]["composite_knot_baryons_hadrons"] > 0.9
        and strong["delta"]["preserved_info_dark_matter"] > 0.05
        and strong["delta"]["bounded_knot_matter_mass"] < -0.25
    )
    weak_decay_selective = (
        weak["delta"]["bounded_knot_matter_mass"] < -0.9
        and weak["delta"]["synchronization_gradient_gravity"] < -0.9
        and abs(weak["delta"]["composite_knot_baryons_hadrons"]) <= TOL
    )
    sync_flatten_selective = (
        sync["delta"]["synchronization_gradient_gravity"] < -0.9
        and sync["delta"]["expansion_dark_energy_time"] > 0.05
        and sync["delta"]["preserved_info_dark_matter"] < -0.05
    )
    density_valid = all(records[name]["density_valid"] for name in CHANNEL_ORDER)
    distinct_channels = channel_response_rank >= 3

    positive = {
        "same_finite_carrier_distinct_transition_channels": {
            "pass": distinct_channels,
            "channel_response_rank": channel_response_rank,
            "singular_values": [py_float(v) for v in singular_values],
            "matrix_channel_order": list(FORCE_KEYS),
            "matrix_delta_order": list(DELTA_KEYS),
            "response_matrix": [[py_float(v) for v in row] for row in jax.device_get(matrix)],
        },
        "identity_channel_zero_delta_control": {"pass": identity_zero, "delta": records["identity_control"]["delta"]},
        "electromagnetic_phase_channel_selective": {"pass": em_phase_selective, "record": em},
        "strong_binding_channel_selective": {"pass": strong_binding_selective, "record": strong},
        "weak_decay_channel_selective": {"pass": weak_decay_selective, "record": weak},
        "gravity_sync_flattening_channel_selective": {"pass": sync_flatten_selective, "record": sync},
        "finite_density_validity_controls": {
            "pass": density_valid,
            "per_channel": {name: {"trace": records[name]["output_trace"], "min_eigenvalue": records[name]["output_min_eigenvalue"]} for name in CHANNEL_ORDER},
        },
    }
    graveyard_companions = {
        "anti_force_admission_fence": {"pass": True, "promotion_allowed": False, "formal_admission_allowed": False},
        "anti_single_force_scalar_control": {"pass": distinct_channels, "minimum_rank_required": 3, "rank": channel_response_rank},
        "identity_channel_must_not_move_faces": {"pass": identity_zero},
    }
    boundary = {
        "finite_spinor_network_boundary": {
            "pass": True,
            "n_spinor_nodes": ft.N,
            "hilbert_dimension": ft.DIM,
            "primitive": "finite spinor-network density derived from psi over (C^2)^5",
        },
        "jax_x64_no_numpy_compute": {"pass": bool(jax.config.read("jax_enable_x64")), "jax_enable_x64": bool(jax.config.read("jax_enable_x64")), "numpy_compute_used": False},
    }

    shared_scalars: dict[str, float] = {
        "channel_response_rank": float(channel_response_rank),
        "identity_zero": 1.0 if identity_zero else 0.0,
        "em_phase_selective": 1.0 if em_phase_selective else 0.0,
        "strong_binding_selective": 1.0 if strong_binding_selective else 0.0,
        "weak_decay_selective": 1.0 if weak_decay_selective else 0.0,
        "sync_flatten_selective": 1.0 if sync_flatten_selective else 0.0,
        "density_valid": 1.0 if density_valid else 0.0,
    }
    for idx, value in enumerate(singular_values):
        shared_scalars[f"channel_singular_value_{idx}"] = py_float(value)
    for channel_name in CHANNEL_ORDER:
        shared_scalars[f"{channel_name}.trace_distance"] = float(records[channel_name]["trace_distance"])
        for key in DELTA_KEYS:
            shared_scalars[f"{channel_name}.delta.{key}"] = float(records[channel_name]["delta"][key])

    local_all_pass = all(row["pass"] for row in positive.values()) and all(row["pass"] for row in graveyard_companions.values()) and all(row["pass"] for row in boundary.values())
    result: dict[str, Any] = {
        "schema": "FINITE_SPINOR_NETWORK_FORCE_TRANSITION_CHANNEL_TAXONOMY_v1",
        "object_id": OBJECT_ID,
        "name": OBJECT_ID,
        "backend": "jax",
        "created_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(Path(__file__)),
        "result_path": str(RESULT_PATH),
        "peer_result_path": str(JULIA_RESULT_PATH),
        "classification": CLASSIFICATION,
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "claim_ceiling": "finite force/transition-channel taxonomy only; no force, particle, gravity, Axis0, physics, M(C), PEPS3D, or bridge admission",
        "depends_on": {
            "face_taxonomy_source": str(FACE_SOURCE),
            "face_taxonomy_result": str(ROOT / "system_v5/ops/formal_scouts/results/spinor_network_face_readout_taxonomy_results.json"),
        },
        "carrier": {
            "primitive": "finite spinor-network state psi; channels operate on spinor-derived density readouts",
            "nodes": ft.N,
            "edges": [list(edge) for edge in ft.EDGES],
            "hilbert_dimension": ft.DIM,
        },
        "channel_interpretation_fence": {
            "electromagnetic_phase_coupling": "phase/coupling channel label only",
            "strong_binding_confinement": "binding/confinement channel label only",
            "weak_decay_topology_change": "decay/topology-change channel label only",
            "gravity_sync_flattening": "synchronization/flattening channel label only",
        },
        "records": records,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "shared_scalars": shared_scalars,
        "blocked_consumers": ["force admission", "particle admission", "gravity admission", "Standard Model claim", "Axis0", "physics", "M(C)", "PEPS3D", "bridge", "final manifold closure"],
        "eligible_consumers": ["scratch diagnostic audits", "transition taxonomy follow-up scouts", "dual-backend parity checks"],
        "TOOL_MANIFEST": {
            "JAX jax.numpy x64": {"tried": True, "used": True, "reason": "load-bearing finite channel action, density/readout deltas, rank controls, and parity scalars"},
            "Python importlib/json/pathlib": {"tried": True, "used": True, "reason": "supportive import of completed face taxonomy functions and receipt writing"},
        },
        "TOOL_INTEGRATION_DEPTH": {"JAX jax.numpy x64": "load_bearing", "Python importlib/json/pathlib": "supportive"},
    }
    result["tool_manifest"] = result["TOOL_MANIFEST"]
    result["tool_integration_depth"] = result["TOOL_INTEGRATION_DEPTH"]
    result["parity"] = parity_block(result)
    result["all_pass"] = bool(local_all_pass and result["parity"]["peer_available"] and result["parity"]["within_1e_10"])
    result["summary"] = {
        "all_pass": result["all_pass"],
        "local_all_pass": bool(local_all_pass),
        "channel_response_rank": channel_response_rank,
        "identity_zero": identity_zero,
        "em_phase_selective": em_phase_selective,
        "strong_binding_selective": strong_binding_selective,
        "weak_decay_selective": weak_decay_selective,
        "sync_flatten_selective": sync_flatten_selective,
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
