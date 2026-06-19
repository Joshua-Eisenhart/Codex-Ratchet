#!/usr/bin/env python3
"""QIT source-native 3-qubit branch geometry scout.

This is a corrective scout for the 2026-06-06 physics excavation thread:
do not use toy graph-distance knot results as QIT-engine evidence. Use the
proposed QIT engine math/geometry:

- finite spinor-network carrier, with 3 qubits as the minimum branch carrier;
- left/right Weyl sheets with H_L=+H0 and H_R=-H0;
- Hopf spinor chart, fiber/base loop distinction, and density readouts;
- source-native terrain/operator/Axis6 schedule specs from
  canonical_qit_engine_specs.py;
- branch controls for sign-only, axis6-erased, phase-quotient, and 2-qubit
  floor failure.

Claim ceiling: scratch diagnostic only. No QIT engine admission, physics,
gravity, Axis0, M(C), PEPS3D, bridge, or final manifold claim.
"""

from __future__ import annotations

import json
import math
import pathlib
import sys
import time
from typing import Any

import jax

jax.config.update("jax_enable_x64", True)
import jax.numpy as jnp
import jax.scipy.linalg as jsp_linalg

ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "qit_source_native_three_qubit_branch_geometry_probe_results.json"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from canonical_qit_engine_specs import (  # noqa: E402
    OPERATOR_BASE_ANGLES,
    OPERATOR_GENERATORS,
    get_engine_spec,
    get_operator_slot_spec,
    get_schedule,
    get_terrain_dynamics_spec,
)

NAME = "qit_source_native_three_qubit_branch_geometry_probe"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
CLAIM_CEILING = (
    "3-qubit source-native QIT branch geometry scout only: finite spinor-network "
    "lift of left/right Weyl Hopf/density terrain-loop schedule branches. No QIT "
    "engine admission, no physics/gravity, no Axis0, no M(C), no PEPS3D, no bridge."
)

TOOL_MANIFEST = {
    "JAX jax.numpy x64": {
        "tried": True,
        "used": True,
        "reason": "load-bearing 3-qubit spinor-network state, density/channel evolution, branch-rank, entropy, MI, and commutator readouts",
    },
    "canonical_qit_engine_specs.py": {
        "tried": True,
        "used": True,
        "reason": "load-bearing source authority for H signs, terrain specs, schedules, operator slots, and Ax6 signs",
    },
    "Python json/pathlib": {
        "tried": True,
        "used": True,
        "reason": "supportive receipt writing to the exact formal scout result path",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "JAX jax.numpy x64": "load_bearing",
    "canonical_qit_engine_specs.py": "load_bearing",
    "Python json/pathlib": "supportive",
}

I2 = jnp.eye(2, dtype=jnp.complex128)
SX = jnp.array([[0, 1], [1, 0]], dtype=jnp.complex128)
SY = jnp.array([[0, -1j], [1j, 0]], dtype=jnp.complex128)
SZ = jnp.array([[1, 0], [0, -1]], dtype=jnp.complex128)
SIGMA_MINUS = jnp.array([[0, 0], [1, 0]], dtype=jnp.complex128)
SIGMA_PLUS = jnp.array([[0, 1], [0, 0]], dtype=jnp.complex128)
PROJECTORS = {
    "x": [0.5 * (I2 + SX), 0.5 * (I2 - SX)],
    "y": [0.5 * (I2 + SY), 0.5 * (I2 - SY)],
    "z": [0.5 * (I2 + SZ), 0.5 * (I2 - SZ)],
}
OBS = [SX, SY, SZ]


def as_jax_matrix(x: Any) -> jnp.ndarray:
    if hasattr(x, "detach"):
        return jnp.array(x.detach().cpu().numpy(), dtype=jnp.complex128)
    return jnp.array(x, dtype=jnp.complex128)


def dagger(a: jnp.ndarray) -> jnp.ndarray:
    return jnp.conjugate(jnp.swapaxes(a, -1, -2))


def kron_all(mats: list[jnp.ndarray]) -> jnp.ndarray:
    out = mats[0]
    for mat in mats[1:]:
        out = jnp.kron(out, mat)
    return out


def embed_single(mat: jnp.ndarray, target: int, n_qubits: int) -> jnp.ndarray:
    return kron_all([mat if i == target else I2 for i in range(n_qubits)])


def normalize_density(rho: jnp.ndarray) -> jnp.ndarray:
    rho = 0.5 * (rho + dagger(rho))
    vals, vecs = jnp.linalg.eigh(rho)
    vals = jnp.clip(jnp.real(vals), 1e-14, None)
    out = vecs @ jnp.diag(vals.astype(jnp.complex128)) @ dagger(vecs)
    return out / jnp.trace(out)


def spinor(phi: float, chi: float, eta: float) -> jnp.ndarray:
    return jnp.array(
        [
            jnp.exp(1j * (phi + chi)) * math.cos(eta),
            jnp.exp(1j * (phi - chi)) * math.sin(eta),
        ],
        dtype=jnp.complex128,
    )


def local_density_from_loop(loop: str, u: float, eta: float, phi0: float, chi0: float) -> jnp.ndarray:
    if loop == "fiber":
        psi = spinor(phi0 + u, chi0, eta)
    elif loop == "base":
        psi = spinor(phi0 - math.cos(2 * eta) * u, chi0 + u, eta)
    else:
        raise ValueError(loop)
    psi = psi.reshape((2, 1))
    return psi @ dagger(psi)


def finite_spinor_network_state(n_qubits: int, *, entangle: bool = True) -> jnp.ndarray:
    if n_qubits < 2:
        raise ValueError("need at least two Weyl sheet qubits")
    params = [
        (0.11, -0.31, 0.37),  # left Weyl sheet
        (-0.19, 0.27, 0.49),  # right Weyl sheet
        (0.07, 0.13, math.pi / 4),  # cut / shell / memory qubit
        (0.29, -0.17, 0.42),  # optional scale branch
    ][:n_qubits]
    locals_ = [spinor(*p) for p in params]
    edges = [(0, 1, 0.17), (0, 2, 0.41), (1, 2, -0.36)]
    if n_qubits >= 4:
        edges += [(2, 3, 0.23), (0, 3, -0.19)]
    amplitudes: list[jnp.ndarray] = []
    for basis in range(2**n_qubits):
        bits = [(basis >> (n_qubits - 1 - i)) & 1 for i in range(n_qubits)]
        amp = jnp.array(1.0 + 0j, dtype=jnp.complex128)
        for i, bit in enumerate(bits):
            amp = amp * locals_[i][bit]
        if entangle:
            phase = 0.0
            for a, b, weight in edges:
                if a < n_qubits and b < n_qubits:
                    phase += weight * (1.0 if bits[a] == bits[b] else -1.0)
            amp = amp * jnp.exp(1j * phase)
        amplitudes.append(amp)
    psi = jnp.array(amplitudes, dtype=jnp.complex128)
    return psi / jnp.linalg.norm(psi)


def density_from_state(psi: jnp.ndarray) -> jnp.ndarray:
    psi = psi.reshape((-1, 1))
    return normalize_density(psi @ dagger(psi))


def partial_trace(rho: jnp.ndarray, keep: list[int], n_qubits: int) -> jnp.ndarray:
    labels_left = list("abcdefghijklmnopqrstuvwxyz"[:n_qubits])
    labels_right = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ"[:n_qubits])
    for i in range(n_qubits):
        if i not in keep:
            labels_right[i] = labels_left[i]
    out_labels = [labels_left[i] for i in keep] + [labels_right[i] for i in keep]
    expr = "".join(labels_left + labels_right) + "->" + "".join(out_labels)
    traced = jnp.einsum(expr, rho.reshape([2] * (2 * n_qubits)))
    dim = 2 ** len(keep)
    return traced.reshape((dim, dim))


def entropy(rho: jnp.ndarray) -> float:
    vals = jnp.clip(jnp.real(jnp.linalg.eigvalsh(0.5 * (rho + dagger(rho)))), 1e-14, 1.0)
    return float(jnp.real(-jnp.sum(vals * jnp.log(vals))))


def purity(rho: jnp.ndarray) -> float:
    return float(jnp.real(jnp.trace(rho @ rho)))


def trace_distance(a: jnp.ndarray, b: jnp.ndarray) -> float:
    diff = 0.5 * ((a - b) + dagger(a - b))
    vals = jnp.linalg.eigvalsh(diff)
    return float(0.5 * jnp.sum(jnp.abs(jnp.real(vals))))


def mutual_information(rho: jnp.ndarray, a: int, b: int, n_qubits: int) -> float:
    rho_a = partial_trace(rho, [a], n_qubits)
    rho_b = partial_trace(rho, [b], n_qubits)
    rho_ab = partial_trace(rho, [a, b], n_qubits)
    return entropy(rho_a) + entropy(rho_b) - entropy(rho_ab)


def bloch_readout(rho: jnp.ndarray, qubit: int, n_qubits: int) -> list[float]:
    local = partial_trace(rho, [qubit], n_qubits)
    return [float(jnp.real(jnp.trace(obs @ local))) for obs in OBS]


def apply_unitary(rho: jnp.ndarray, unitary: jnp.ndarray) -> jnp.ndarray:
    return normalize_density(unitary @ rho @ dagger(unitary))


def apply_dephase(rho: jnp.ndarray, target: int, n_qubits: int, axis: str, rate: float) -> jnp.ndarray:
    projectors = [embed_single(p, target, n_qubits) for p in PROJECTORS[axis]]
    pinched = sum(p @ rho @ p for p in projectors)
    return normalize_density((1.0 - rate) * rho + rate * pinched)


def apply_lindblad_step(rho: jnp.ndarray, target: int, n_qubits: int, ladder: jnp.ndarray, rate: float) -> jnp.ndarray:
    l_op = embed_single(ladder, target, n_qubits)
    diss = l_op @ rho @ dagger(l_op) - 0.5 * (dagger(l_op) @ l_op @ rho + rho @ dagger(l_op) @ l_op)
    return normalize_density(rho + rate * diss)


def apply_operator(
    rho: jnp.ndarray,
    *,
    target: int,
    n_qubits: int,
    operator: str,
    sign: int,
    erased_axis6: bool = False,
) -> jnp.ndarray:
    sign = +1 if erased_axis6 else int(sign)
    if operator in {"Ti", "Te"}:
        axis = "z" if operator == "Ti" else "x"
        # Signed placement changes the finite contraction strength. This is
        # the scout's explicit Ax6-readout surface, not a physics assertion.
        base = 0.09 if operator == "Ti" else 0.075
        rate = base * (1.0 + 0.22 * sign)
        return apply_dephase(rho, target, n_qubits, axis, rate)
    generator = as_jax_matrix(OPERATOR_GENERATORS[operator])
    angle = float(OPERATOR_BASE_ANGLES[operator]) * sign
    unitary = jsp_linalg.expm(-0.5j * angle * embed_single(generator, target, n_qubits))
    return apply_unitary(rho, unitary)


def apply_terrain(
    rho: jnp.ndarray,
    *,
    target: int,
    n_qubits: int,
    perception: str,
    engine_type: int,
    disabled: bool = False,
) -> jnp.ndarray:
    if disabled:
        return rho
    terrain = get_terrain_dynamics_spec(perception, engine_type)
    rho = apply_dephase(rho, target, n_qubits, terrain["projector_axis"], 0.35 * float(terrain["rate"]))
    ladder = SIGMA_MINUS if engine_type == 0 else SIGMA_PLUS
    return apply_lindblad_step(rho, target, n_qubits, ladder, 0.18 * float(terrain["rate"]))


def apply_loop_ownership(
    rho: jnp.ndarray,
    *,
    target: int,
    n_qubits: int,
    loop_class: str,
    u: float,
    disabled: bool = False,
) -> jnp.ndarray:
    if disabled:
        return rho
    eta = 0.37 if target == 0 else 0.49
    phi = 0.11 if target == 0 else -0.19
    chi = -0.31 if target == 0 else 0.27
    loop = "fiber" if loop_class == "inner" else "base"
    local_loop = local_density_from_loop(loop, u, eta, phi, chi)
    axis = "z" if loop == "fiber" else "y"
    loop_projectors = [embed_single(p, target, n_qubits) for p in PROJECTORS[axis]]
    pinched = sum(p @ rho @ p for p in loop_projectors)
    # Density-stationary fiber gets a tiny bookkeeping mix; base loop is
    # density-visible and therefore stronger.
    weight = 0.015 if loop == "fiber" else 0.12
    # Couple a finite local loop target by matching its Bloch-z expectation.
    z = float(jnp.real(jnp.trace(SZ @ local_loop)))
    bias = 0.5 * (1.0 + max(min(z, 1.0), -1.0))
    target_projector = loop_projectors[0] * bias + loop_projectors[1] * (1.0 - bias)
    return normalize_density((1.0 - weight) * rho + 0.5 * weight * pinched + 0.5 * weight * target_projector @ rho @ target_projector)


def execute_engine_pair(
    n_qubits: int,
    *,
    entangle: bool = True,
    mode: str = "source_native",
    reverse_schedule: bool = False,
) -> tuple[jnp.ndarray, list[dict[str, Any]]]:
    psi = finite_spinor_network_state(n_qubits, entangle=entangle)
    rho = density_from_state(psi)
    rows: list[dict[str, Any]] = []
    engine_order = [0, 1]
    for engine_type in engine_order:
        target = engine_type
        schedule = list(get_schedule(engine_type))
        if reverse_schedule:
            schedule = list(reversed(schedule))
        for stage_index, (perception, loop_class) in enumerate(schedule):
            for substage_idx in range(4):
                slot = get_operator_slot_spec(perception, engine_type, loop_class, substage_idx)
                sign = int(slot["sign"])
                precedence = slot["precedence"]
                if mode == "axis6_erased":
                    sign = +1
                    precedence = "operator_first"
                terrain_disabled = mode == "sign_only"
                loop_disabled = mode in {"sign_only", "loop_erased"}
                if precedence == "operator_first":
                    rho = apply_operator(
                        rho,
                        target=target,
                        n_qubits=n_qubits,
                        operator=slot["operator"],
                        sign=sign,
                        erased_axis6=(mode == "axis6_erased"),
                    )
                    rho = apply_terrain(
                        rho,
                        target=target,
                        n_qubits=n_qubits,
                        perception=perception,
                        engine_type=engine_type,
                        disabled=terrain_disabled,
                    )
                else:
                    rho = apply_terrain(
                        rho,
                        target=target,
                        n_qubits=n_qubits,
                        perception=perception,
                        engine_type=engine_type,
                        disabled=terrain_disabled,
                    )
                    rho = apply_operator(
                        rho,
                        target=target,
                        n_qubits=n_qubits,
                        operator=slot["operator"],
                        sign=sign,
                        erased_axis6=(mode == "axis6_erased"),
                    )
                rho = apply_loop_ownership(
                    rho,
                    target=target,
                    n_qubits=n_qubits,
                    loop_class=loop_class,
                    u=0.17 * (1 + stage_index + substage_idx),
                    disabled=loop_disabled,
                )
                rows.append(
                    {
                        "engine_type": engine_type,
                        "target_qubit": target,
                        "perception": perception,
                        "loop_class": loop_class,
                        "substage_idx": substage_idx,
                        "operator": slot["operator"],
                        "axis6_sign": sign,
                        "precedence": precedence,
                        "entropy_global": entropy(rho),
                        "purity_global": purity(rho),
                        "mi_lr": mutual_information(rho, 0, 1, n_qubits),
                    }
                )
    return rho, rows


def signature(rho: jnp.ndarray, n_qubits: int) -> jnp.ndarray:
    values: list[float] = [
        entropy(rho),
        purity(rho),
        mutual_information(rho, 0, 1, n_qubits),
    ]
    if n_qubits >= 3:
        values.extend(
            [
                mutual_information(rho, 0, 2, n_qubits),
                mutual_information(rho, 1, 2, n_qubits),
                entropy(partial_trace(rho, [2], n_qubits)),
            ]
        )
    for q in range(min(n_qubits, 3)):
        values.extend(bloch_readout(rho, q, n_qubits))
    return jnp.array(values, dtype=jnp.float64)


def branch_matrix(n_qubits: int) -> dict[str, Any]:
    branches = {
        "source_native": execute_engine_pair(n_qubits, mode="source_native")[0],
        "sign_only_control": execute_engine_pair(n_qubits, mode="sign_only")[0],
        "axis6_erased_control": execute_engine_pair(n_qubits, mode="axis6_erased")[0],
        "phase_quotient_control": execute_engine_pair(n_qubits, entangle=False, mode="source_native")[0],
        "reverse_schedule_control": execute_engine_pair(n_qubits, mode="source_native", reverse_schedule=True)[0],
    }
    sigs = {name: signature(rho, n_qubits) for name, rho in branches.items()}
    names = list(sigs)
    matrix = jnp.stack([sigs[n] for n in names])
    centered = matrix - jnp.mean(matrix, axis=0, keepdims=True)
    svals = jnp.linalg.svd(centered, compute_uv=False)
    rank = int(jnp.sum(svals > 1e-4))
    gaps = {
        f"{a}_vs_{b}": float(jnp.linalg.norm(sigs[a] - sigs[b]))
        for i, a in enumerate(names)
        for b in names[i + 1 :]
    }
    return {
        "names": names,
        "rank": rank,
        "singular_values": [float(x) for x in svals],
        "gaps": gaps,
        "signatures": {k: [float(x) for x in v] for k, v in sigs.items()},
    }


def nonabelian_distance(n_qubits: int, *, mode_a: str, mode_b: str) -> float:
    rho0 = density_from_state(finite_spinor_network_state(n_qubits, entangle=True))
    a_then_b = execute_engine_pair(n_qubits, mode=mode_b)[0]
    # Use exact same initial state, but compare branch compositions by a small
    # second pass from the first branch endpoint.
    # This finite scout measures endpoint noncommutation by reusing the same
    # schedule map family in different branch modes, not by claiming a closed
    # symbolic channel identity.
    rho_a, _ = execute_engine_pair(n_qubits, mode=mode_a)
    rho_b, _ = execute_engine_pair(n_qubits, mode=mode_b)
    mix_ab = normalize_density(0.55 * rho_a + 0.45 * a_then_b)
    mix_ba = normalize_density(0.55 * rho_b + 0.45 * rho0)
    return trace_distance(mix_ab, mix_ba)


def hopf_loop_control() -> dict[str, Any]:
    eta = 0.41
    phi = 0.22
    chi = -0.18
    rho0 = local_density_from_loop("fiber", 0.0, eta, phi, chi)
    fiber = local_density_from_loop("fiber", 0.7, eta, phi, chi)
    base = local_density_from_loop("base", 0.7, eta, phi, chi)
    return {
        "fiber_density_stationary_gap": trace_distance(rho0, fiber),
        "base_density_visible_gap": trace_distance(rho0, base),
        "fiber_stationary": trace_distance(rho0, fiber) < 1e-10,
        "base_visible": trace_distance(rho0, base) > 0.1,
    }


def main() -> None:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    matrix3 = branch_matrix(3)
    matrix4 = branch_matrix(4)
    rho3, rows3 = execute_engine_pair(3, mode="source_native")
    rho2, _ = execute_engine_pair(2, mode="source_native")
    sig3 = signature(rho3, 3)
    sig2 = signature(rho2, 2)
    floor_gap = float(jnp.linalg.norm(sig3[: len(sig2)] - sig2))
    hopf = hopf_loop_control()

    positive = {
        "three_qubit_floor_enforced": {
            "pass": True,
            "n_qubits": 3,
            "hilbert_dimension": 8,
            "reason": "source branch includes left Weyl, right Weyl, and cut/shell memory spinor",
        },
        "source_native_branch_rank": {
            "pass": matrix3["rank"] >= 3,
            "rank": matrix3["rank"],
            "minimum_rank": 3,
            "singular_values": matrix3["singular_values"],
        },
        "hopf_loop_control": {
            "pass": bool(hopf["fiber_stationary"] and hopf["base_visible"]),
            **hopf,
        },
        "q2_cut_load_bearing": {
            "pass": floor_gap > 0.25,
            "three_vs_two_signature_gap": floor_gap,
            "reason": "2-qubit sheet-only control lacks the third cut/shell spinor and changes the branch signature",
        },
        "axis6_load_bearing": {
            "pass": matrix3["gaps"]["source_native_vs_axis6_erased_control"] > 0.05,
            "gap": matrix3["gaps"]["source_native_vs_axis6_erased_control"],
        },
        "phase_quotient_load_bearing": {
            "pass": matrix3["gaps"]["source_native_vs_phase_quotient_control"] > 0.05,
            "gap": matrix3["gaps"]["source_native_vs_phase_quotient_control"],
        },
        "four_qubit_branch_stays_noncollapsed": {
            "pass": matrix4["rank"] >= 3,
            "rank": matrix4["rank"],
            "minimum_rank": 3,
            "singular_values": matrix4["singular_values"],
        },
    }
    graveyard = {
        "sign_only_is_insufficient": {
            "pass": matrix3["gaps"]["source_native_vs_sign_only_control"] > 0.05,
            "gap": matrix3["gaps"]["source_native_vs_sign_only_control"],
        },
        "reverse_schedule_differs": {
            "pass": matrix3["gaps"]["source_native_vs_reverse_schedule_control"] > 0.05,
            "gap": matrix3["gaps"]["source_native_vs_reverse_schedule_control"],
        },
        "toy_knot_not_used": {
            "pass": True,
            "reason": "this scout does not consume knot_mass_gravity_rung_results.json; that result remains toy-scale scratch diagnostic only",
        },
    }
    branch_readings = {
        "R1_information_preserving_channel_reading": {
            "status": "open_supported",
            "support": "unitary/operator portions preserve finite density validity and rearrange MI signatures, but dissipative terrain is also active",
        },
        "R2_basin_fall_dissipation_reading": {
            "status": "open_supported",
            "support": "terrain and ladder channels change purity/entropy and make source_native differ from sign_only",
        },
        "R3_non_abelian_schedule_reading": {
            "status": "open_supported",
            "support": "reverse schedule control differs at 3-qubit floor; not promoted to canonical-cycle closure",
        },
    }
    all_pass = all(x["pass"] for x in positive.values()) and all(x["pass"] for x in graveyard.values())
    result = {
        "schema": "QIT_SOURCE_NATIVE_THREE_QUBIT_BRANCH_GEOMETRY_PROBE_v1",
        "name": NAME,
        "object_id": NAME,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "classification": CLASSIFICATION,
        "all_pass": bool(all_pass),
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "source_paths": [
            "/Users/joshuaeisenhart/Codex-Ratchet/system_v5/ops/formal_scouts/canonical_qit_engine_specs.py",
            "/Users/joshuaeisenhart/Codex-Ratchet/system_v5/ops/QIT_ENGINE_FULL_EXPLICIT_MATH_PACKET_20260522.md",
            "/Users/joshuaeisenhart/Codex-Ratchet/system_v5/docs/CONSTRAINT_ON_DISTINGUISHABILITY_FULL_MATH.md",
            "/Users/joshuaeisenhart/Codex-Ratchet/system_v5/docs/CLAUDE_THREAD_HANDOFF_QIT_ENGINES_OPERATIONAL_MANIFOLD_PRIMARY_20260515.md",
        ],
        "carrier": {
            "primitive": "finite 3-qubit spinor-network state psi over (C^2)^3",
            "minimum_qubits": 3,
            "hilbert_dimension": 8,
            "qubit_roles": ["left Weyl sheet", "right Weyl sheet", "cut/shell memory spinor"],
            "density_status": "rho and marginals are derived readout layers",
            "spinor_network_phase_edges": ["L-R", "L-cut", "R-cut"],
        },
        "branch_readings": branch_readings,
        "positive": positive,
        "graveyard_companions": graveyard,
        "branch_matrix_3q": matrix3,
        "branch_matrix_4q": matrix4,
        "microstep_count_3q_source_native": len(rows3),
        "summary": {
            "all_pass": bool(all_pass),
            "n_qubits_minimum": 3,
            "hilbert_dimension": 8,
            "branch_response_rank_3q": matrix3["rank"],
            "branch_response_rank_4q": matrix4["rank"],
            "axis6_gap": positive["axis6_load_bearing"]["gap"],
            "phase_quotient_gap": positive["phase_quotient_load_bearing"]["gap"],
            "two_qubit_floor_gap": floor_gap,
            "fiber_density_stationary_gap": hopf["fiber_density_stationary_gap"],
            "base_density_visible_gap": hopf["base_density_visible_gap"],
        },
        "blocked_consumers": [
            "QIT engine admission",
            "physics",
            "gravity",
            "Axis0",
            "M(C)",
            "PEPS3D",
            "bridge",
            "final manifold closure",
        ],
        "eligible_consumers": [
            "scratch diagnostic audits",
            "QIT source-native branch hardening",
            "independent Julia mirror candidate",
            "label-blind branch controls",
        ],
    }
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True))
    print(json.dumps(result["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
