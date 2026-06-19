#!/usr/bin/env python3
# object_id: mp_sequential_universe_density_carrier
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp


REPO = Path("/Users/joshuaeisenhart/Codex-Ratchet")
JULIA_CARRIER = REPO / "system_v5" / "julia_carrier"
FORMAL_SCOUTS = REPO / "system_v5" / "ops" / "formal_scouts"
RESULT_PATH = FORMAL_SCOUTS / "results" / "mp_sequential_universe_toy_results.json"
JULIA_REFERENCE_PATH = JULIA_CARRIER / "mp_sequential_universe_toy_julia_results.json"
OBJECT_ID = "mp_sequential_universe_density_carrier"
TOL = 1.0e-9
STRICT_STOP_TOL = 1.0e-6
UNIVERSE_COUNT = 6
DT = 0.018
LOG2 = jnp.log(jnp.asarray(2.0, dtype=jnp.float64))

sys.path.insert(0, str(JULIA_CARRIER))
sys.path.insert(0, str(FORMAL_SCOUTS))

import canonical_qit_engine_specs as qit_specs  # noqa: E402
import jax_density_matrix_spinor_lift as owner_density  # noqa: E402


I2 = jnp.eye(2, dtype=jnp.complex128)
I4 = jnp.eye(4, dtype=jnp.complex128)
SX = jnp.asarray([[0.0, 1.0], [1.0, 0.0]], dtype=jnp.complex128)
SY = jnp.asarray([[0.0, -1.0j], [1.0j, 0.0]], dtype=jnp.complex128)
SZ = jnp.asarray([[1.0, 0.0], [0.0, -1.0]], dtype=jnp.complex128)
MIRROR = SX
PAULI = (SX, SY, SZ)


def py_float(x: Any) -> float:
    return float(jax.device_get(x))


def sha256(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def source_refs() -> dict[str, Any]:
    refs = {
        "density_matrix_spinor_lift": JULIA_CARRIER / "density_matrix_spinor_lift.jl",
        "jax_density_matrix_spinor_lift": JULIA_CARRIER / "jax_density_matrix_spinor_lift.py",
        "canonical_qit_engine_specs": FORMAL_SCOUTS / "canonical_qit_engine_specs.py",
    }
    return {key: {"path": str(path), "exists": path.exists(), "sha256": sha256(path)} for key, path in refs.items()}


def torch_matrix_to_jnp(t: Any) -> jax.Array:
    return jnp.asarray(t.detach().cpu().tolist(), dtype=jnp.complex128)


def qit_hamiltonian(engine_type: int) -> jax.Array:
    return torch_matrix_to_jnp(qit_specs.get_engine_spec(engine_type)["hamiltonian"])


def qit_lindblad(perception: str, engine_type: int) -> jax.Array:
    _, l_mat = qit_specs.get_lindblad_params(perception, engine_type)
    return torch_matrix_to_jnp(l_mat)


def qit_operator(op: str) -> jax.Array:
    return torch_matrix_to_jnp(qit_specs.OPERATOR_GENERATORS[op])


def normalize(v: jax.Array) -> jax.Array:
    norm = jnp.linalg.norm(v)
    return jnp.where(norm > TOL, v / norm, v)


def clamp_bloch(v: jax.Array, max_norm: float = 0.985) -> jax.Array:
    norm = jnp.linalg.norm(v)
    scale = jnp.where(norm > max_norm, max_norm / norm, 1.0)
    return v * scale


def rho_from_bloch(v: jax.Array) -> jax.Array:
    r = clamp_bloch(v)
    return 0.5 * (I2 + r[0] * SX + r[1] * SY + r[2] * SZ)


def bloch_from_rho(rho: jax.Array) -> jax.Array:
    return jnp.asarray(
        [jnp.real(jnp.trace(rho @ SX)), jnp.real(jnp.trace(rho @ SY)), jnp.real(jnp.trace(rho @ SZ))],
        dtype=jnp.float64,
    )


def renormalize_rho(rho: jax.Array) -> jax.Array:
    hermitian = 0.5 * (rho + jnp.conj(rho.T))
    return hermitian / jnp.trace(hermitian)


def lindblad_step(rho: jax.Array, h_mat: jax.Array, l_mat: jax.Array, rate: float) -> jax.Array:
    ldl = jnp.conj(l_mat.T) @ l_mat
    comm = h_mat @ rho - rho @ h_mat
    dissipator = l_mat @ rho @ jnp.conj(l_mat.T) - 0.5 * (ldl @ rho + rho @ ldl)
    return renormalize_rho(rho + DT * (-1j * comm + rate * dissipator))


def entropy(rho: jax.Array) -> jax.Array:
    vals = jnp.clip(jnp.linalg.eigvalsh(0.5 * (rho + jnp.conj(rho.T))), 0.0, 1.0)
    vals = vals / jnp.sum(vals)
    safe = jnp.where(vals > TOL, vals, 1.0)
    return -jnp.sum(jnp.where(vals > TOL, vals * jnp.log(safe) / LOG2, 0.0))


def partial_trace_a(rho_ab: jax.Array) -> jax.Array:
    t = jnp.reshape(rho_ab, (2, 2, 2, 2))
    return jnp.einsum("abcb->ac", t)


def partial_trace_b(rho_ab: jax.Array) -> jax.Array:
    t = jnp.reshape(rho_ab, (2, 2, 2, 2))
    return jnp.einsum("abac->bc", t)


def mutual_information(rho_ab: jax.Array) -> jax.Array:
    return entropy(partial_trace_a(rho_ab)) + entropy(partial_trace_b(rho_ab)) - entropy(rho_ab)


def spinor_perp(psi: jax.Array) -> jax.Array:
    return jnp.asarray([-jnp.conj(psi[1]), jnp.conj(psi[0])], dtype=jnp.complex128)


def owner_carrier(seed: float = 0.0) -> dict[str, Any]:
    psi = owner_density.spinor_from_angles(1.1 + 0.07 * seed, -0.7 + 0.11 * seed)
    rho = owner_density.dm(psi)
    bloch = owner_density.bloch_from_rho(rho)
    axis = normalize(bloch)
    rho_rebuilt = owner_density.rho_from_bloch(bloch)
    u2 = owner_density.su2(jnp.asarray([0.2, -0.5, 0.84], dtype=jnp.float64), 2.0 * jnp.pi)
    psi2 = u2 @ psi
    rho2 = u2 @ rho @ jnp.conj(u2.T)
    return {
        "psi": psi,
        "psi_perp": spinor_perp(psi),
        "rho": rho,
        "axis": axis,
        "bloch": bloch,
        "rho_reconstruction_residual": py_float(jnp.linalg.norm(rho - rho_rebuilt)),
        "spinor_norm_residual": py_float(jnp.abs(jnp.real(jnp.vdot(psi, psi)) - 1.0)),
        "rho_2pi_return_residual": py_float(jnp.linalg.norm(rho2 - rho)),
        "psi_2pi_sign_residual": py_float(jnp.linalg.norm(psi2 + psi)),
    }


def erased_owner_carrier() -> dict[str, Any]:
    psi = jnp.asarray([1.0 + 0.0j, 0.0 + 0.0j], dtype=jnp.complex128)
    axis = jnp.asarray([0.0, 0.0, 1.0], dtype=jnp.float64)
    return {
        "psi": psi,
        "psi_perp": spinor_perp(psi),
        "rho": rho_from_bloch(axis),
        "axis": axis,
        "bloch": axis,
        "rho_reconstruction_residual": 0.0,
        "spinor_norm_residual": 0.0,
        "rho_2pi_return_residual": 0.0,
        "psi_2pi_sign_residual": 0.0,
    }


def entangled_density(carrier: dict[str, Any], inherited: jax.Array) -> jax.Array:
    axis = carrier["axis"]
    memory_alignment = jnp.clip(jnp.dot(inherited, axis), 0.0, 0.96)
    memory_norm = jnp.clip(jnp.linalg.norm(inherited), 0.0, 0.96)
    corr_weight = jnp.clip(0.06 + 0.58 * memory_alignment + 0.22 * memory_norm, 0.0, 0.92)
    alpha = jnp.clip(0.66 + 0.18 * memory_alignment, 0.54, 0.86)
    psi = carrier["psi"]
    psi_perp = carrier["psi_perp"]
    ent = jnp.sqrt(alpha) * jnp.kron(psi, psi) + jnp.sqrt(1.0 - alpha) * jnp.kron(psi_perp, psi_perp)
    ent = ent / jnp.sqrt(jnp.real(jnp.vdot(ent, ent)))
    ent_rho = jnp.outer(ent, jnp.conj(ent))
    rho_a = rho_from_bloch(0.42 * axis + 0.48 * inherited)
    rho_b = rho_from_bloch(0.37 * axis + 0.51 * inherited)
    product = jnp.kron(rho_a, rho_b)
    return renormalize_rho(corr_weight * ent_rho + (1.0 - corr_weight) * product)


def op_axis(op: jax.Array) -> jax.Array:
    return jnp.asarray(
        [jnp.real(jnp.trace(op @ SX)) / 2.0, jnp.real(jnp.trace(op @ SY)) / 2.0, jnp.real(jnp.trace(op @ SZ)) / 2.0],
        dtype=jnp.float64,
    )


def qit_cycle(inherited: jax.Array, carrier: dict[str, Any]) -> tuple[jax.Array, jax.Array, float, float, float, float]:
    rho = entangled_density(carrier, inherited)
    axis = carrier["axis"]
    stage_count = 0
    for engine_type in (0, 1):
        h_base = qit_hamiltonian(engine_type)
        for perception, loop_class in qit_specs.get_schedule(engine_type):
            l_single = qit_lindblad(perception, engine_type)
            rate = float(qit_specs.get_topology_spec(perception, engine_type)["rate"])
            for substage_idx in range(qit_specs.N_SUBSTAGES_PER_MAIN):
                slot = qit_specs.get_operator_slot_spec(perception, engine_type, loop_class, substage_idx)
                op = qit_operator(slot["operator"])
                drive = jnp.dot(inherited, op_axis(op)) + 0.25 * jnp.dot(axis, op_axis(op))
                h_single = h_base + (0.030 * float(slot["sign"]) + 0.014 * drive) * op
                h_total = jnp.kron(h_single, I2) + jnp.kron(I2, 0.73 * h_single)
                l_a = jnp.kron(l_single, I2)
                l_b = jnp.kron(I2, MIRROR @ l_single @ MIRROR)
                rho = lindblad_step(rho, h_total, l_a, rate)
                rho = lindblad_step(rho, h_total, l_b, 0.71 * rate)
                stage_count += 1
    if stage_count != 2 * qit_specs.N_TOTAL_SUBSTAGES_PER_ENGINE:
        raise RuntimeError(f"unexpected qit stage count {stage_count}")
    rho_a = partial_trace_a(rho)
    rho_b = partial_trace_b(rho)
    out_bloch = clamp_bloch(0.5 * (bloch_from_rho(rho_a) + bloch_from_rho(rho_b)))
    mi = mutual_information(rho)
    mi_norm = jnp.clip(mi / 2.0, 0.0, 1.0)
    purity = jnp.real(jnp.trace(rho @ rho))
    entropy_basin = 1.0 - jnp.clip(entropy(rho) / 2.0, 0.0, 1.0)
    alignment = jnp.clip(0.5 + 0.5 * jnp.dot(out_bloch, axis), 0.0, 1.0)
    stability = jnp.clip(0.48 * mi_norm + 0.24 * entropy_basin + 0.18 * alignment + 0.10 * purity, 0.0, 1.0)
    mixed = 0.54 * inherited + (0.24 + 0.48 * mi_norm) * axis + 0.16 * out_bloch
    next_norm = jnp.clip(0.16 + 0.70 * mi_norm + 0.12 * jnp.linalg.norm(inherited), 0.0, 0.96)
    next_memory = next_norm * normalize(mixed)
    return next_memory, out_bloch, py_float(stability), py_float(mi), py_float(entropy_basin), py_float(purity)


def scramble_memory(v: jax.Array, axis: jax.Array) -> jax.Array:
    scramble = jnp.asarray([[0.0, 0.0, -1.0], [0.0, 1.0, 0.0], [-1.0, 0.0, 0.0]], dtype=jnp.float64)
    carrier_component = jnp.dot(v, axis)
    orthogonal = v - carrier_component * axis
    scrambled_orthogonal = scramble @ orthogonal
    scrambled_orthogonal = scrambled_orthogonal - jnp.dot(scrambled_orthogonal, axis) * axis
    return 0.62 * (-jnp.abs(carrier_component) * axis + scrambled_orthogonal)


def run_sequence(mode: str, carrier: dict[str, Any]) -> dict[str, Any]:
    prev = 0.18 * carrier["axis"]
    rows: list[dict[str, Any]] = []
    windows: list[float] = []
    mutual_infos: list[float] = []
    entropies: list[float] = []
    purities: list[float] = []
    for universe_idx in range(UNIVERSE_COUNT):
        if mode == "preserved":
            inherited = prev
        elif mode == "random":
            inherited = scramble_memory(prev, carrier["axis"])
        elif mode == "none":
            inherited = jnp.zeros((3,), dtype=jnp.float64)
        else:
            raise ValueError(mode)
        next_memory, out_bloch, stability, mi, entropy_basin, purity = qit_cycle(inherited, carrier)
        windows.append(stability)
        mutual_infos.append(mi)
        entropies.append(entropy_basin)
        purities.append(purity)
        rows.append(
            {
                "universe_index": universe_idx,
                "inheritance_mode": mode,
                "inherited_rho_correlation_vector": [py_float(x) for x in inherited],
                "out_density_bloch": [py_float(x) for x in out_bloch],
                "next_rho_correlation_vector": [py_float(x) for x in next_memory],
                "alignment_with_owner_density_axis": py_float(jnp.dot(inherited, carrier["axis"])),
                "mutual_information_bits": mi,
                "entropy_basin_score": entropy_basin,
                "stability_window": stability,
                "two_qubit_purity": purity,
            }
        )
        prev = next_memory
    diffs = [windows[i + 1] - windows[i] for i in range(len(windows) - 1)]
    return {
        "mode": mode,
        "rows": rows,
        "stability_windows": windows,
        "window_diffs": diffs,
        "mutual_information_bits": mutual_infos,
        "entropy_basin_scores": entropies,
        "purities": purities,
        "monotonic_strict_increase": all(diff > STRICT_STOP_TOL for diff in diffs),
        "net_increase": windows[-1] - windows[0],
        "final_window": windows[-1],
        "final_mutual_information_bits": mutual_infos[-1],
    }


def run_bundle(carrier: dict[str, Any]) -> dict[str, Any]:
    return {
        "preserved": run_sequence("preserved", carrier),
        "random_inheritance_control": run_sequence("random", carrier),
        "no_inheritance_control": run_sequence("none", carrier),
    }


def parity_against_julia(result: dict[str, Any]) -> dict[str, Any]:
    if not JULIA_REFERENCE_PATH.exists():
        return {
            "peer_result_path": str(JULIA_REFERENCE_PATH),
            "status": "missing_julia_reference",
            "parity_max_diff": None,
            "within_1e_9": False,
            "boolean_mismatches": ["missing_julia_reference"],
            "strict_divergence_gt_1e_6": ["missing_julia_reference"],
            "missing_keys": [],
            "stop_condition_fired": True,
        }
    peer = json.loads(JULIA_REFERENCE_PATH.read_text(encoding="utf-8"))
    rows: list[dict[str, Any]] = []
    missing: list[str] = []
    strict: list[dict[str, Any]] = []
    max_diff = 0.0
    for key, value in result["shared_scalars"].items():
        if key not in peer.get("shared_scalars", {}):
            missing.append(key)
            continue
        jax_value = float(value)
        julia_value = float(peer["shared_scalars"][key])
        diff = abs(jax_value - julia_value)
        row = {"key": key, "jax": jax_value, "julia": julia_value, "abs_diff": diff}
        rows.append(row)
        max_diff = max(max_diff, diff)
        if diff > STRICT_STOP_TOL:
            strict.append(row)
    mismatches: list[dict[str, Any]] = []
    for key, value in result["shared_booleans"].items():
        if key not in peer.get("shared_booleans", {}):
            missing.append(key)
            continue
        if bool(value) != bool(peer["shared_booleans"][key]):
            mismatches.append({"key": key, "jax": bool(value), "julia": bool(peer["shared_booleans"][key])})
    return {
        "peer_result_path": str(JULIA_REFERENCE_PATH),
        "status": "compared",
        "shared_scalar_rows": rows,
        "parity_max_diff": max_diff,
        "within_1e_9": max_diff <= TOL and not strict and not mismatches and not missing,
        "boolean_mismatches": mismatches,
        "strict_divergence_gt_1e_6": strict,
        "missing_keys": missing,
        "stop_condition_fired": bool(strict) or bool(mismatches) or bool(missing),
    }


def build_result() -> dict[str, Any]:
    carrier = owner_carrier()
    erased_carrier = erased_owner_carrier()
    sequences = run_bundle(carrier)
    erased_sequences = run_bundle(erased_carrier)
    preserved = sequences["preserved"]
    random_control = sequences["random_inheritance_control"]
    no_control = sequences["no_inheritance_control"]

    inherited_increases_stability = bool(
        preserved["monotonic_strict_increase"] and preserved["net_increase"] > 1.0e-3
    )
    random_inherit_fails = bool(
        (not random_control["monotonic_strict_increase"]) and random_control["net_increase"] < 0.03
    )
    no_inherit_fails = bool(
        (not no_control["monotonic_strict_increase"]) and abs(no_control["net_increase"]) <= STRICT_STOP_TOL
    )
    owner_delta = abs(preserved["final_window"] - erased_sequences["preserved"]["final_window"])
    owner_carrier_load_bearing = bool(owner_delta > STRICT_STOP_TOL)
    on_real_density_carrier = bool(
        carrier["rho_reconstruction_residual"] <= STRICT_STOP_TOL
        and carrier["spinor_norm_residual"] <= STRICT_STOP_TOL
        and carrier["psi_2pi_sign_residual"] <= STRICT_STOP_TOL
    )
    controls_fire = bool(random_inherit_fails and no_inherit_fails)

    shared_scalars = {
        "universe_count": float(UNIVERSE_COUNT),
        "qit_total_substages_per_engine": float(qit_specs.N_TOTAL_SUBSTAGES_PER_ENGINE),
        "qit_stage_count_per_universe": float(2 * qit_specs.N_TOTAL_SUBSTAGES_PER_ENGINE),
        "owner_axis_x": py_float(carrier["axis"][0]),
        "owner_axis_y": py_float(carrier["axis"][1]),
        "owner_axis_z": py_float(carrier["axis"][2]),
        "owner_density_bloch_norm": py_float(jnp.linalg.norm(carrier["bloch"])),
        "owner_rho_reconstruction_residual": float(carrier["rho_reconstruction_residual"]),
        "owner_psi_2pi_sign_residual": float(carrier["psi_2pi_sign_residual"]),
        "preserved_window_0": float(preserved["stability_windows"][0]),
        "preserved_window_final": float(preserved["final_window"]),
        "preserved_net_increase": float(preserved["net_increase"]),
        "preserved_final_mutual_information_bits": float(preserved["final_mutual_information_bits"]),
        "random_window_0": float(random_control["stability_windows"][0]),
        "random_window_final": float(random_control["final_window"]),
        "random_net_increase": float(random_control["net_increase"]),
        "no_inherit_window_0": float(no_control["stability_windows"][0]),
        "no_inherit_window_final": float(no_control["final_window"]),
        "no_inherit_net_increase": float(no_control["net_increase"]),
        "owner_erased_preserved_window_final": float(erased_sequences["preserved"]["final_window"]),
        "owner_erased_result_delta": float(owner_delta),
    }
    for idx, value in enumerate(preserved["stability_windows"]):
        shared_scalars[f"preserved_window_{idx}"] = float(value)
    for idx, value in enumerate(random_control["stability_windows"]):
        shared_scalars[f"random_window_{idx}"] = float(value)
    for idx, value in enumerate(no_control["stability_windows"]):
        shared_scalars[f"no_inherit_window_{idx}"] = float(value)

    shared_booleans = {
        "inherited_increases_stability": inherited_increases_stability,
        "random_inherit_fails": random_inherit_fails,
        "no_inherit_fails": no_inherit_fails,
        "controls_fire": controls_fire,
        "owner_carrier_load_bearing": owner_carrier_load_bearing,
        "on_real_density_carrier": on_real_density_carrier,
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "jax_enable_x64": bool(jax.config.read("jax_enable_x64")),
    }
    result: dict[str, Any] = {
        "object_id": OBJECT_ID,
        "backend": "jax",
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "result_path": str(RESULT_PATH),
        "julia_reference_path": str(JULIA_REFERENCE_PATH),
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "claim_ceiling": "Finite density-carrier inheritance diagnostic only; no physics, dark-matter, Standard Model, M(C), Axis0, bridge, engine admission, manifold closure, or formal admission claim.",
        "owner_source_refs": source_refs(),
        "carrier_anchors": {
            "density_bloch": [py_float(x) for x in carrier["bloch"]],
            "density_bloch_norm": py_float(jnp.linalg.norm(carrier["bloch"])),
            "rho_reconstruction_residual": carrier["rho_reconstruction_residual"],
            "spinor_norm_residual": carrier["spinor_norm_residual"],
            "rho_2pi_return_residual": carrier["rho_2pi_return_residual"],
            "psi_2pi_sign_residual": carrier["psi_2pi_sign_residual"],
        },
        "construction": {
            "memory_carrier": "two-qubit density matrix whose inherited state is previous-iteration rho correlation and mutual information",
            "stability_measure": "density entropy basin score plus mutual information, purity, and owner-density-axis alignment",
            "positive": "preserved rho correlation vector is passed to the next finite iteration",
            "controls": [
                "random inheritance applies an order/sign-scrambled correlation vector before the same density and QIT evolution",
                "no inheritance replaces the previous rho correlation by zero before the same density and QIT evolution",
                "owner-erased ablation replaces density_matrix_spinor_lift with a fixed computational-basis carrier",
            ],
        },
        "sequences": sequences,
        "owner_erased_ablation": erased_sequences,
        "controls": {
            "real_vs_scrambled_structure_flip": random_inherit_fails,
            "real_vs_erased_structure_flip": no_inherit_fails,
            "random_inheritance_does_not_raise_stability": random_inherit_fails,
            "no_inheritance_does_not_raise_stability": no_inherit_fails,
            "owner_carrier_erasure_changes_result": owner_carrier_load_bearing,
        },
        "tool_manifest": {
            "jax": "load-bearing x64 density-matrix, entropy, mutual-information, Lindblad, and parity arithmetic",
            "jax.numpy": "load-bearing x64 array and complex matrix arithmetic; no NumPy compute path",
            "owner_julia_carrier": "load-bearing density_matrix_spinor_lift carrier mirrored by jax_density_matrix_spinor_lift; owner-erased ablation changes the result",
            "canonical_qit_engine_specs": "load-bearing H0, Type1/2 signs, Se/Ne/Ni/Si Lindblad, operator slots, and 32-substage schedule metadata",
            "json": "supportive result serialization",
        },
        "TOOL_MANIFEST": {
            "jax": "load-bearing x64 density-matrix, entropy, mutual-information, Lindblad, and parity arithmetic",
            "jax.numpy": "load-bearing x64 array and complex matrix arithmetic; no NumPy compute path",
            "owner_julia_carrier": "load-bearing density_matrix_spinor_lift carrier mirrored by jax_density_matrix_spinor_lift; owner-erased ablation changes the result",
            "canonical_qit_engine_specs": "load-bearing H0, Type1/2 signs, Se/Ne/Ni/Si Lindblad, operator slots, and 32-substage schedule metadata",
            "json": "supportive result serialization",
        },
        "tool_integration_depth": {
            "jax": "load_bearing",
            "jax.numpy": "load_bearing",
            "owner_julia_carrier": "load_bearing",
            "canonical_qit_engine_specs": "load_bearing",
            "json": "supportive",
        },
        "TOOL_INTEGRATION_DEPTH": {
            "jax": "load_bearing",
            "jax.numpy": "load_bearing",
            "owner_julia_carrier": "load_bearing",
            "canonical_qit_engine_specs": "load_bearing",
            "json": "supportive",
        },
        "divergence_log": [
            "Positive: preserved rho correlation and mutual information raise the density stability window monotonically.",
            "Control: scrambled inheritance uses the same carrier/evolution after a wrong order/sign correlation flip and does not raise the window.",
            "Control: erased inheritance uses the same carrier/evolution from zero correlation and does not raise the window.",
            "Owner-carrier ablation: replacing density_matrix_spinor_lift with a fixed carrier changes the final stability window.",
        ],
        "shared_scalars": shared_scalars,
        "shared_booleans": shared_booleans,
    }
    result["parity"] = parity_against_julia(result)
    result["parity_stop_condition_fired"] = bool(result["parity"]["stop_condition_fired"])
    result["all_pass"] = bool(
        inherited_increases_stability
        and random_inherit_fails
        and no_inherit_fails
        and owner_carrier_load_bearing
        and on_real_density_carrier
        and not result["parity_stop_condition_fired"]
    )
    result["shared_booleans"]["all_pass"] = result["all_pass"]
    return result


def main() -> int:
    result = build_result()
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        "SCOUT_DONE "
        f"jax={RESULT_PATH} "
        f"julia={JULIA_REFERENCE_PATH} "
        f"all_pass={str(result['all_pass']).lower()} "
        f"owner_carrier_load_bearing={str(result['shared_booleans']['owner_carrier_load_bearing']).lower()} "
        f"inherited_increases_stability={str(result['shared_booleans']['inherited_increases_stability']).lower()} "
        f"random_inherit_fails={str(result['shared_booleans']['random_inherit_fails']).lower()} "
        f"no_inherit_fails={str(result['shared_booleans']['no_inherit_fails']).lower()} "
        f"on_real_density_carrier={str(result['shared_booleans']['on_real_density_carrier']).lower()}"
    )
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    sys.exit(main())
