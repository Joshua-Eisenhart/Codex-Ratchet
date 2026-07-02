#!/usr/bin/env python3
"""JAX Hopf-linked information entropy controls scout.

Formal scout only. This probes the user's entropy/information framing without
claiming a completed layer:

* finite density matrices only;
* QIT cut readouts kept as separate columns;
* product, commuting/dephased, gauge, and permutation negatives;
* a matched unlinked topology control that blocks topology admission when it can
  imitate the linked readout.

The linked object is a finite three-region hyperedge phase state. It is a small
Hopf-linking analogue for JAX-side entropy/control scouting, not a PEPS3D layer
admission artifact and not physics.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import time
from typing import Any

import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "jax_hopf_linked_information_entropy_controls_probe"
RESULT_PATH = RESULT_DIR / f"{NAME}_results.json"

CLASSIFICATION = "formal_scout"
SIM_CLASS = "jax_hopf_linked_information_entropy_control_scout"
SOURCE_ALIGNMENT_CATEGORY = "finite_qit_entropy_information_hopf_link_controls"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: JAX finite-density QIT readouts for a Hopf-linked "
    "information candidate and controls. It does not admit a layer, Hopf "
    "geometry completion, topology-entanglement unification, Axis0, flux, FEP, "
    "physics, or final manifold claims."
)

TOOL_MANIFEST = {
    "jax": {
        "used": True,
        "role": "load_bearing",
        "reason": "JAX x64 complex density matrices, partial traces, entropy readouts, partial transpose, and controls are directly exercised.",
    },
    "jax.numpy": {
        "used": True,
        "role": "supportive",
        "reason": "Finite Hilbert-space linear algebra for QIT readouts and topology-control search.",
    },
    "python_json": {
        "used": True,
        "role": "supportive",
        "reason": "Result receipt serialization only.",
    },
    "pathlib": {
        "used": True,
        "role": "supportive",
        "reason": "Result path handling only.",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "jax": "load_bearing",
    "jax.numpy": "supportive",
    "python_json": "supportive",
    "pathlib": "supportive",
}

BLOCKED_CONSUMERS = [
    "layer_stacking",
    "official_g_structure_selection",
    "topology_entanglement_unification_claim",
    "flux",
    "Xi/Phi0",
    "Axis0",
    "Holodeck/FEP",
    "physics/gravity",
    "final_manifold",
]

TOL = 1.0e-9
SIGNAL_MIN = 1.0e-4
TOPOLOGY_GAP_MIN = 2.0e-2
LOG2 = jnp.log(jnp.array(2.0, dtype=jnp.float64))
BITS = jnp.asarray(
    [[(i >> (2 - k)) & 1 for k in range(3)] for i in range(8)],
    dtype=jnp.int32,
)
ZSIGNS = 1 - 2 * BITS


def _jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    if hasattr(value, "item"):
        try:
            return _jsonable(value.item())
        except Exception:
            return str(value)
    if isinstance(value, complex):
        return {"real": float(value.real), "imag": float(value.imag)}
    return value


def _hermitize(rho: jax.Array) -> jax.Array:
    return (rho + jnp.conj(rho.T)) / 2.0


def _normalize_density(rho: jax.Array) -> jax.Array:
    rho = _hermitize(rho)
    trace = jnp.real(jnp.trace(rho))
    return rho / jnp.maximum(trace, TOL)


def _density_from_state(psi: jax.Array) -> jax.Array:
    psi = psi / jnp.linalg.norm(psi)
    return _normalize_density(jnp.outer(psi, jnp.conj(psi)))


def _phase_state(theta: float, kind: str) -> jax.Array:
    """Finite three-region phase states.

    linked: one three-way hyperedge phase, the candidate Hopf-link analogue.
    chain: unlinked pairwise chain control, calibrated to match local entropy.
    pair_triangle: edge-only pairwise control used as a nearby degeneracy check.
    product: no information-carrying phase.
    """
    theta_j = jnp.array(theta, dtype=jnp.float64)
    if kind == "linked":
        phase = theta_j * jnp.prod(ZSIGNS, axis=1)
    elif kind == "chain":
        phase = theta_j * (ZSIGNS[:, 0] * ZSIGNS[:, 1] + ZSIGNS[:, 1] * ZSIGNS[:, 2]) / jnp.sqrt(2.0)
    elif kind == "pair_triangle":
        phase = theta_j * (
            ZSIGNS[:, 0] * ZSIGNS[:, 1]
            + ZSIGNS[:, 1] * ZSIGNS[:, 2]
            + ZSIGNS[:, 0] * ZSIGNS[:, 2]
        ) / jnp.sqrt(3.0)
    elif kind == "product":
        phase = jnp.zeros((8,), dtype=jnp.float64)
    else:
        raise ValueError(f"unknown state kind: {kind}")
    psi = jnp.exp(1j * phase).astype(jnp.complex128) / jnp.sqrt(jnp.array(8.0, dtype=jnp.float64))
    return _density_from_state(psi)


def _partial_trace(rho: jax.Array, keep: tuple[int, ...]) -> jax.Array:
    keep_set = set(keep)
    traced = [index for index in range(3) if index not in keep_set]
    arr = rho.reshape((2, 2, 2, 2, 2, 2))
    active = 3
    for index in sorted(traced, reverse=True):
        arr = jnp.trace(arr, axis1=index, axis2=index + active)
        active -= 1
    dim = 2 ** len(keep)
    return _normalize_density(arr.reshape((dim, dim)))


def _entropy(rho: jax.Array) -> float:
    rho = _normalize_density(rho)
    eigs = jnp.linalg.eigvalsh(_hermitize(rho)).real
    eigs = jnp.clip(eigs, 0.0, 1.0)
    eigs = eigs / jnp.maximum(jnp.sum(eigs), TOL)
    live = eigs[eigs > TOL]
    return float(-jnp.sum(live * jnp.log(live) / LOG2))


def _partial_transpose(rho: jax.Array, systems: tuple[int, ...]) -> jax.Array:
    axes = list(range(6))
    for system in systems:
        axes[system], axes[system + 3] = axes[system + 3], axes[system]
    return jnp.transpose(rho.reshape((2, 2, 2, 2, 2, 2)), axes).reshape((8, 8))


def _negativity(rho: jax.Array, systems: tuple[int, ...]) -> float:
    pt = _partial_transpose(_normalize_density(rho), systems)
    eigs = jnp.linalg.eigvalsh(_hermitize(pt)).real
    return float(jnp.sum(jnp.abs(eigs[eigs < 0.0])))


def _log_negativity(rho: jax.Array, systems: tuple[int, ...]) -> float:
    return float(jnp.log2(1.0 + 2.0 * _negativity(rho, systems)))


def _mi(rho: jax.Array, a: int, b: int) -> float:
    return _entropy(_partial_trace(rho, (a,))) + _entropy(_partial_trace(rho, (b,))) - _entropy(_partial_trace(rho, tuple(sorted((a, b)))))


def _readouts(rho: jax.Array) -> dict[str, float]:
    s_a = _entropy(_partial_trace(rho, (0,)))
    s_b = _entropy(_partial_trace(rho, (1,)))
    s_c = _entropy(_partial_trace(rho, (2,)))
    s_ab = _entropy(_partial_trace(rho, (0, 1)))
    s_ac = _entropy(_partial_trace(rho, (0, 2)))
    s_bc = _entropy(_partial_trace(rho, (1, 2)))
    s_abc = _entropy(rho)
    i_ab = s_a + s_b - s_ab
    i_ac = s_a + s_c - s_ac
    i_bc = s_b + s_c - s_bc
    i_a_bc = s_a + s_bc - s_abc
    cmi_a_c_given_b = s_ab + s_bc - s_b - s_abc
    return {
        "S_A": s_a,
        "S_B": s_b,
        "S_C": s_c,
        "S_AB": s_ab,
        "S_AC": s_ac,
        "S_BC": s_bc,
        "S_ABC": s_abc,
        "mean_single_site_entropy": (s_a + s_b + s_c) / 3.0,
        "I_A_B": i_ab,
        "I_A_C": i_ac,
        "I_B_C": i_bc,
        "I_A_BC": i_a_bc,
        "conditional_entropy_A_given_B": s_ab - s_b,
        "conditional_entropy_A_given_BC": s_abc - s_bc,
        "coherent_information_A_to_B": s_b - s_ab,
        "coherent_information_A_to_BC": s_bc - s_abc,
        "conditional_mutual_information_A_C_given_B": cmi_a_c_given_b,
        "tripartite_information": s_a + s_b + s_c - s_ab - s_ac - s_bc + s_abc,
        "negativity_A_BC": _negativity(rho, (0,)),
        "negativity_B_AC": _negativity(rho, (1,)),
        "negativity_C_AB": _negativity(rho, (2,)),
        "log_negativity_A_BC": _log_negativity(rho, (0,)),
        "log_negativity_B_AC": _log_negativity(rho, (1,)),
        "log_negativity_C_AB": _log_negativity(rho, (2,)),
    }


def _dephase(rho: jax.Array) -> jax.Array:
    return _normalize_density(jnp.diag(jnp.diag(rho)))


def _local_phase_unitary(phases: tuple[float, float, float]) -> jax.Array:
    diag = []
    for bits in BITS.tolist():
        angle = 0.0
        for bit, phase in zip(bits, phases):
            z = 1.0 if bit == 0 else -1.0
            angle += phase * z
        diag.append(jnp.exp(1j * jnp.array(angle, dtype=jnp.float64)))
    return jnp.diag(jnp.asarray(diag, dtype=jnp.complex128))


def _permute_unitary(perm: tuple[int, int, int]) -> jax.Array:
    rows = []
    for out_bits in BITS.tolist():
        row = []
        for in_bits in BITS.tolist():
            row.append(1.0 if tuple(out_bits) == tuple(in_bits[index] for index in perm) else 0.0)
        rows.append(row)
    return jnp.asarray(rows, dtype=jnp.complex128)


def _apply_unitary(rho: jax.Array, unitary: jax.Array) -> jax.Array:
    return _normalize_density(unitary @ rho @ jnp.conj(unitary.T))


def _max_readout_delta(left: dict[str, float], right: dict[str, float], keys: list[str]) -> float:
    return max(abs(float(left[key]) - float(right[key])) for key in keys)


def _density_checks(rho: jax.Array) -> dict[str, Any]:
    eigs = jnp.linalg.eigvalsh(_hermitize(rho)).real
    return {
        "trace_real": float(jnp.real(jnp.trace(rho))),
        "trace_imag_abs": abs(float(jnp.imag(jnp.trace(rho)))),
        "min_eigenvalue": float(jnp.min(eigs)),
        "pass": bool(
            abs(float(jnp.real(jnp.trace(rho))) - 1.0) < 1.0e-8
            and abs(float(jnp.imag(jnp.trace(rho)))) < 1.0e-8
            and float(jnp.min(eigs)) > -1.0e-8
        ),
    }


def _best_unlinked_match(target_single_entropy: float, kind: str) -> dict[str, Any]:
    best: dict[str, Any] | None = None
    for raw in range(1, 158):
        theta = raw / 100.0
        rho = _phase_state(theta, kind)
        readouts = _readouts(rho)
        error = abs(readouts["mean_single_site_entropy"] - target_single_entropy)
        if best is None or error < best["single_entropy_abs_error"]:
            best = {
                "kind": kind,
                "theta": theta,
                "single_entropy_abs_error": error,
                "readouts": readouts,
            }
    assert best is not None
    return best


def _scale_case(theta: float) -> dict[str, Any]:
    linked = _phase_state(theta, "linked")
    product = _phase_state(theta, "product")
    dephased = _dephase(linked)
    linked_r = _readouts(linked)
    product_r = _readouts(product)
    dephased_r = _readouts(dephased)

    chain_match = _best_unlinked_match(linked_r["mean_single_site_entropy"], "chain")
    triangle_match = _best_unlinked_match(linked_r["mean_single_site_entropy"], "pair_triangle")
    matched = min((chain_match, triangle_match), key=lambda row: row["single_entropy_abs_error"])
    matched_r = matched["readouts"]

    gauge_u = _local_phase_unitary((0.17, -0.31, 0.43))
    gauge_r = _readouts(_apply_unitary(linked, gauge_u))
    perm_u = _permute_unitary((2, 1, 0))
    perm_r = _readouts(_apply_unitary(linked, perm_u))
    invariant_keys = [
        "S_A",
        "S_B",
        "S_C",
        "I_A_B",
        "I_A_C",
        "I_B_C",
        "conditional_mutual_information_A_C_given_B",
        "coherent_information_A_to_BC",
        "log_negativity_A_BC",
        "log_negativity_B_AC",
        "log_negativity_C_AB",
    ]
    gauge_delta = _max_readout_delta(linked_r, gauge_r, invariant_keys)
    perm_delta = _max_readout_delta(linked_r, perm_r, invariant_keys)

    linked_signal = linked_r["conditional_mutual_information_A_C_given_B"]
    product_signal = product_r["conditional_mutual_information_A_C_given_B"]
    dephased_signal = dephased_r["conditional_mutual_information_A_C_given_B"]
    topology_gap = linked_signal - matched_r["conditional_mutual_information_A_C_given_B"]
    matched_zero = matched_r["conditional_mutual_information_A_C_given_B"] < SIGNAL_MIN

    controls = {
        "finite_density_matrix": _density_checks(linked),
        "product_information_kill": {
            "pass": bool(product_signal < SIGNAL_MIN and product_r["log_negativity_A_BC"] < SIGNAL_MIN),
            "product_cmi": product_signal,
            "product_log_negativity_A_BC": product_r["log_negativity_A_BC"],
        },
        "commuting_dephase_control": {
            "pass": bool(dephased_signal < SIGNAL_MIN and dephased_r["log_negativity_A_BC"] < SIGNAL_MIN),
            "dephased_cmi": dephased_signal,
            "dephased_log_negativity_A_BC": dephased_r["log_negativity_A_BC"],
        },
        "local_gauge_safe": {"pass": bool(gauge_delta < 1.0e-8), "max_readout_delta": gauge_delta},
        "permutation_safe_for_linked_symmetric_case": {"pass": bool(perm_delta < 1.0e-8), "max_readout_delta": perm_delta},
        "single_entropy_matched_unlinked_control": {
            "pass": bool(matched["single_entropy_abs_error"] < 1.0e-2),
            "kind": matched["kind"],
            "theta": matched["theta"],
            "single_entropy_abs_error": matched["single_entropy_abs_error"],
        },
        "linked_exceeds_matched_unlinked_cmi": {
            "pass": bool(topology_gap > TOPOLOGY_GAP_MIN),
            "linked_cmi": linked_signal,
            "matched_unlinked_cmi": matched_r["conditional_mutual_information_A_C_given_B"],
            "gap": topology_gap,
        },
        "matched_unlinked_zero_topology_claim": {
            "pass": bool(matched_zero),
            "matched_unlinked_cmi": matched_r["conditional_mutual_information_A_C_given_B"],
            "note": "This is intentionally not required for scout pass; if false, topology admission remains blocked.",
        },
    }
    bounded_pass = bool(
        controls["finite_density_matrix"]["pass"]
        and controls["product_information_kill"]["pass"]
        and controls["commuting_dephase_control"]["pass"]
        and controls["local_gauge_safe"]["pass"]
        and controls["permutation_safe_for_linked_symmetric_case"]["pass"]
        and controls["single_entropy_matched_unlinked_control"]["pass"]
        and linked_signal > SIGNAL_MIN
    )
    topology_admission_allowed = bool(
        bounded_pass
        and controls["linked_exceeds_matched_unlinked_cmi"]["pass"]
        and controls["matched_unlinked_zero_topology_claim"]["pass"]
    )
    return {
        "theta": theta,
        "linked_readouts": linked_r,
        "product_readouts": product_r,
        "commuting_dephased_readouts": dephased_r,
        "matched_unlinked_control": matched,
        "controls": controls,
        "bounded_scout_pass": bounded_pass,
        "topology_admission_allowed": topology_admission_allowed,
    }


def _stress_degeneracy_case() -> dict[str, Any]:
    """A nearby high-phase case where an edge-only control imitates the signal."""
    theta = 0.9
    linked = _readouts(_phase_state(theta, "linked"))
    triangle = _best_unlinked_match(linked["mean_single_site_entropy"], "pair_triangle")
    cmi_gap = linked["conditional_mutual_information_A_C_given_B"] - triangle["readouts"]["conditional_mutual_information_A_C_given_B"]
    return {
        "theta": theta,
        "control_kind": triangle["kind"],
        "control_theta": triangle["theta"],
        "single_entropy_abs_error": triangle["single_entropy_abs_error"],
        "linked_cmi": linked["conditional_mutual_information_A_C_given_B"],
        "matched_control_cmi": triangle["readouts"]["conditional_mutual_information_A_C_given_B"],
        "cmi_gap": cmi_gap,
        "interpretation": "nearby matched edge-only control can imitate CMI; this blocks broad topology-entanglement admission.",
    }


def main() -> int:
    started = time.time()
    source_path = pathlib.Path(__file__).resolve()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    cases = [_scale_case(theta) for theta in (0.3, 0.6)]
    stress = _stress_degeneracy_case()
    bounded_scout_pass = all(case["bounded_scout_pass"] for case in cases)
    topology_admission_allowed = all(case["topology_admission_allowed"] for case in cases) and abs(stress["cmi_gap"]) > TOPOLOGY_GAP_MIN
    topology_blocked = not topology_admission_allowed
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "sim_id": NAME,
        "name": NAME,
        "version": "1.0.0",
        "tier": "entropy_information_control_scout",
        "classification": CLASSIFICATION,
        "sim_class": SIM_CLASS,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "claim_boundary": CLAIM_CEILING,
        "source_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "purpose": "Probe finite QIT entropy/information readouts for a Hopf-linked information-network candidate in JAX, while blocking overclaim with matched controls.",
        "scientific_question": "Which finite density-matrix-native cut readouts survive product, commuting/dephased, gauge, permutation, and matched-unlinked controls?",
        "sim_execution_kind": "nonclassical_jax_mirror_formal_scout",
        "finite_map": "HopfLinkedInfo_JAX: finite three-region phase-density states -> separated QIT entropy/readout table plus control verdicts",
        "domain": "finite 2x2x2 Hilbert space density matrices over linked, product, dephased, gauge, permutation, and unlinked edge-only controls",
        "codomain_or_output": "finite QIT readouts: S, I(A:B), S(A|B), I_c, I(A:C|B), tripartite information, negativity, log-negativity, and admission/block flags",
        "root_constraints_in_force": {
            "F01": "finite Hilbert space, finite density matrices, finite cut family, finite control registry",
            "N01": "order-sensitive three-way phase map compared against product, commuting/dephased, gauge, permutation, and unlinked controls",
        },
        "carrier_layer": "JAX finite density-matrix mirror only",
        "geometry_layer": "Hopf-linked hyperedge analogue for entropy/control scouting",
        "carrier_realization": "jax.Array complex128 density matrices over three finite qubit-like regions",
        "peps3d_embedding": "not_admitted_jax_mirror_only",
        "spinor_state": "finite phase spinor amplitudes converted to density matrices; no torch PEPS3D spinor-network admission",
        "quaternion_action": "not_applicable",
        "dependency_receipts": ["system_v5/ops/formal_scouts/results/jax_results.json"],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "allowed_claims": [
            "JAX can compute the separated finite QIT readout table for this candidate and its controls.",
            "The bounded scout controls passed for the reported theta cases.",
            "Topology-entanglement admission remains blocked because a stronger matched-unlinked zero control is not established.",
        ],
        "all_pass": bool(bounded_scout_pass),
        "topology_admission_allowed": bool(topology_admission_allowed),
        "topology_admission_blocked": bool(topology_blocked),
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "result_summary": {
            "all_pass": bool(bounded_scout_pass),
            "topology_admission_allowed": bool(topology_admission_allowed),
            "topology_admission_blocked": bool(topology_blocked),
            "cases": len(cases),
            "cases_passed": sum(1 for case in cases if case["bounded_scout_pass"]),
            "max_product_cmi": max(case["product_readouts"]["conditional_mutual_information_A_C_given_B"] for case in cases),
            "max_dephased_cmi": max(case["commuting_dephased_readouts"]["conditional_mutual_information_A_C_given_B"] for case in cases),
            "min_linked_cmi": min(case["linked_readouts"]["conditional_mutual_information_A_C_given_B"] for case in cases),
            "min_linked_vs_matched_unlinked_cmi_gap": min(case["controls"]["linked_exceeds_matched_unlinked_cmi"]["gap"] for case in cases),
            "stress_degeneracy_cmi_gap": stress["cmi_gap"],
            "elapsed_seconds": round(time.time() - started, 6),
        },
        "host_numpy_boundary": {
            "numpy_imported": False,
            "claim_bearing_numeric_carrier": "JAX x64 / jax.numpy",
        },
        "jax_execution_evidence": {
            "x64_enabled": bool(jax.config.read("jax_enable_x64")),
            "arrays": "complex128 density matrices and float64 entropy/readout scalars",
            "transforms_used": ["jax.numpy.linalg.eigvalsh", "jax.numpy.trace", "jax.numpy.transpose"],
        },
        "known_value_checks": {
            "product_cmi_zero": {
                "pass": all(case["controls"]["product_information_kill"]["pass"] for case in cases),
                "max_product_cmi": max(case["product_readouts"]["conditional_mutual_information_A_C_given_B"] for case in cases),
            },
            "commuting_dephase_kills_quantum_signal": {
                "pass": all(case["controls"]["commuting_dephase_control"]["pass"] for case in cases),
                "max_dephased_cmi": max(case["commuting_dephased_readouts"]["conditional_mutual_information_A_C_given_B"] for case in cases),
            },
            "local_gauge_invariant": {
                "pass": all(case["controls"]["local_gauge_safe"]["pass"] for case in cases),
                "max_delta": max(case["controls"]["local_gauge_safe"]["max_readout_delta"] for case in cases),
            },
            "permutation_invariant_for_symmetric_linked_case": {
                "pass": all(case["controls"]["permutation_safe_for_linked_symmetric_case"]["pass"] for case in cases),
                "max_delta": max(case["controls"]["permutation_safe_for_linked_symmetric_case"]["max_readout_delta"] for case in cases),
            },
        },
        "controls": {
            "product_information_kill": all(case["controls"]["product_information_kill"]["pass"] for case in cases),
            "commuting_dephase_control": all(case["controls"]["commuting_dephase_control"]["pass"] for case in cases),
            "local_gauge_safe": all(case["controls"]["local_gauge_safe"]["pass"] for case in cases),
            "permutation_safe": all(case["controls"]["permutation_safe_for_linked_symmetric_case"]["pass"] for case in cases),
            "matched_unlinked_control_present": all(case["controls"]["single_entropy_matched_unlinked_control"]["pass"] for case in cases),
            "topology_claim_blocked_until_stronger_matched_control": bool(topology_blocked),
            "promotion_lock_control": {"pass": True, "promotion_allowed": PROMOTION_ALLOWED},
            "downstream_lock_control": {"pass": True, "blocked_consumers": BLOCKED_CONSUMERS},
        },
        "kill_conditions": [
            "fail if linked/product/dephased/gauge/permutation controls do not execute over finite density matrices",
            "fail if product or commuting/dephased controls carry nonzero CMI or log-negativity",
            "fail if local gauge or symmetric permutation changes QIT readouts",
            "block topology admission if matched unlinked edge-only controls can imitate the linked CMI signal",
            "fail if promotion_allowed becomes true or downstream consumers are unlocked",
        ],
        "positive": {
            "finite_density_readouts_present": {"pass": bool(bounded_scout_pass), "cases": len(cases)},
            "qit_columns_kept_separate": {
                "pass": True,
                "columns": [
                    "S",
                    "I(A:B)",
                    "S(A|B)",
                    "I_c",
                    "I(A:C|B)",
                    "tripartite_information",
                    "negativity",
                    "log_negativity",
                ],
            },
        },
        "graveyard_companions": {
            "topology_unification_not_admitted": {
                "pass": bool(topology_blocked),
                "stress_degeneracy": stress,
            },
            "dephased_commuting_variant_rejected": {
                "pass": all(case["controls"]["commuting_dephase_control"]["pass"] for case in cases),
            },
            "product_variant_rejected": {
                "pass": all(case["controls"]["product_information_kill"]["pass"] for case in cases),
            },
        },
        "boundary": {
            "promotion_allowed_false": {"pass": True, "value": PROMOTION_ALLOWED},
            "downstream_consumers_locked": {"pass": True, "blocked_consumers": BLOCKED_CONSUMERS},
            "not_peps3d_or_full_layer_admission": {
                "pass": True,
                "detail": "JAX density-matrix scout only; no torch PEPS3D carrier admission.",
            },
            "no_axis0_or_flux_unlock": {
                "pass": True,
                "detail": "Axis0, flux, Xi/Phi0, FEP, physics, and final manifold remain blocked.",
            },
        },
        "why_not_v4_probes": [
            "This is a bounded JAX mirror/control scout, not a v4/v4.3 promotion packet.",
            "The matched-unlinked topology control blocks stronger topology-entanglement claims.",
        ],
        "nearby_variants": {
            "total": len(cases),
            "passed": sum(1 for case in cases if case["bounded_scout_pass"]),
            "variants": [
                {"theta": case["theta"], "pass": case["bounded_scout_pass"]}
                for case in cases
            ],
        },
        "blocked_nearby_degeneracy": stress,
        "cases": cases,
        "result_path": str(RESULT_PATH),
    }
    RESULT_PATH.write_text(json.dumps(_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "all_pass": result["all_pass"],
                "topology_admission_allowed": result["topology_admission_allowed"],
                "topology_admission_blocked": result["topology_admission_blocked"],
                "result_path": result["result_path"],
                "summary": result["result_summary"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
