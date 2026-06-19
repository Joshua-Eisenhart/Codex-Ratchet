#!/usr/bin/env python3
# object_id: xi_shell_bridge_probe
# classification: scratch_diagnostic
# fence: formal_scout/scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

from __future__ import annotations

import datetime as _dt
import json
import math
import sys
from pathlib import Path
from typing import Any

import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp


OBJECT_ID = "xi_shell_bridge_probe"
BASE_DIR = Path("/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier")
RESULT_PATH = BASE_DIR / "xi_shell_bridge_probe_jax_results.json"
JULIA_REFERENCE_PATH = BASE_DIR / "xi_shell_bridge_probe_julia_results.json"
TOL = 1.0e-9
STRICT_STOP_TOL = 1.0e-6
ENTROPY_EPS = 1.0e-12
J_COUNT = 3
K_COUNT = 3
REMOTE_EDIT_PAIR = (3, 2)
REMOTE_EDIT_DELTA = 1.137
BLOCKED_CONSUMERS = [
    "Axis0-admission",
    "gravity",
    "physics",
    "bridge-admission",
    "FEP",
    "consciousness",
    "formal-admission",
]


def py_float(x: Any) -> float:
    return float(jax.device_get(x))


def pair_key(j: int, k: int) -> str:
    return f"{j},{k}"


def branch_pairs() -> list[tuple[int, int]]:
    return [(j, k) for j in range(1, J_COUNT + 1) for k in range(1, K_COUNT + 1)]


def spinor(theta: float, phi: float) -> jax.Array:
    return jnp.array([jnp.cos(theta / 2.0), jnp.exp(1j * phi) * jnp.sin(theta / 2.0)], dtype=jnp.complex128)


def spinor_perp(theta: float, phi: float) -> jax.Array:
    return jnp.array([-jnp.exp(-1j * phi) * jnp.sin(theta / 2.0), jnp.cos(theta / 2.0)], dtype=jnp.complex128)


def bloch_vector(theta: float, phi: float) -> jax.Array:
    return jnp.array([jnp.sin(theta) * jnp.cos(phi), jnp.sin(theta) * jnp.sin(phi), jnp.cos(theta)], dtype=jnp.float64)


def density(psi: jax.Array) -> jax.Array:
    v = psi / jnp.linalg.norm(psi)
    return jnp.outer(v, jnp.conj(v))


def branch_weights() -> list[float]:
    raw = []
    for j, k in branch_pairs():
        raw.append(1.0 + float((17 * j + 29 * k + 11 * j * k) % 13) / 7.0 + 0.05 * j + 0.03 * k)
    total = sum(raw)
    return [x / total for x in raw]


def scrambled_weights(weights: list[float]) -> list[float]:
    return list(reversed(weights))


def nested_hopf_frame(j: int, k: int, weight: float) -> dict[str, Any]:
    eta = math.pi * (float(j) + 0.17 * float(k)) / (2.0 * (float(J_COUNT) + 1.0))
    phi = 2.0 * math.pi * float((2 * j + k) % (J_COUNT * K_COUNT)) / float(J_COUNT * K_COUNT) + 0.07 * k
    chi = 2.0 * math.pi * float((j + 2 * k + 1) % 11) / 11.0 + 0.11 * j
    base = jnp.array(
        [
            jnp.sin(2.0 * eta) * jnp.cos(phi + chi),
            jnp.sin(2.0 * eta) * jnp.sin(phi + chi),
            jnp.cos(2.0 * eta),
        ],
        dtype=jnp.float64,
    )
    fiber = jnp.array([jnp.cos(phi - chi), jnp.sin(phi - chi), jnp.cos(2.0 * eta)], dtype=jnp.float64)
    fiber = fiber / jnp.linalg.norm(fiber)
    gamma = py_float(jnp.clip(jnp.dot(base, fiber), -1.0, 1.0))
    lam = py_float(0.5 + 0.24 * jnp.tanh(1.2 * gamma))
    theta_a = 2.0 * eta
    phi_a = phi + chi
    theta_b = py_float(jnp.arccos(jnp.clip(fiber[2], -1.0, 1.0)))
    phi_b = py_float(jnp.arctan2(fiber[1], fiber[0]))
    phase = py_float((phi - chi) + 0.5 * base[1])
    return {
        "geometry": "nested_hopf_tori",
        "j": j,
        "k": k,
        "weight": weight,
        "eta": eta,
        "phi": phi,
        "chi": chi,
        "theta_a": theta_a,
        "phi_a": phi_a,
        "theta_b": theta_b,
        "phi_b": phi_b,
        "gamma": gamma,
        "lambda": lam,
        "phase": phase,
        "hopf_base": [py_float(x) for x in base],
        "fiber_axis": [py_float(x) for x in fiber],
    }


def flat_product_frame(j: int, k: int, weight: float) -> dict[str, Any]:
    theta_a = math.pi * float(j) / float(J_COUNT + 1)
    phi_a = 2.0 * math.pi * float(k) / float(K_COUNT) + 0.13 * j
    theta_b = math.pi * float(k) / float(K_COUNT + 1)
    phi_b = 2.0 * math.pi * float(j) / float(J_COUNT) + 0.17 * k
    a_axis = bloch_vector(theta_a, phi_a)
    b_axis = bloch_vector(theta_b, phi_b)
    gamma = py_float(jnp.clip(jnp.dot(a_axis, b_axis), -1.0, 1.0))
    lam = py_float(0.5 + 0.24 * jnp.tanh(1.2 * gamma))
    phase = phi_a - phi_b
    return {
        "geometry": "flat_s2_product",
        "j": j,
        "k": k,
        "weight": weight,
        "theta_a": theta_a,
        "phi_a": phi_a,
        "theta_b": theta_b,
        "phi_b": phi_b,
        "gamma": gamma,
        "lambda": lam,
        "phase": phase,
        "a_axis": [py_float(x) for x in a_axis],
        "b_axis": [py_float(x) for x in b_axis],
        "flat_control_note": "two independent S2 spinor frames; no S3 eta/fiber coordinate",
    }


def frame_for(geometry: str, j: int, k: int, weight: float) -> dict[str, Any]:
    if geometry == "nested_hopf_tori":
        return nested_hopf_frame(j, k, weight)
    if geometry == "flat_s2_product":
        return flat_product_frame(j, k, weight)
    raise ValueError(f"unknown geometry: {geometry}")


def rho_from_frame(frame: dict[str, Any], remote_delta: float = 0.0) -> jax.Array:
    a = spinor(float(frame["theta_a"]), float(frame["phi_a"]))
    ap = spinor_perp(float(frame["theta_a"]), float(frame["phi_a"]))
    b = spinor(float(frame["theta_b"]), float(frame["phi_b"]) + remote_delta)
    bp = spinor_perp(float(frame["theta_b"]), float(frame["phi_b"]) + remote_delta)
    lam = float(frame["lambda"])
    phase = float(frame["phase"])
    psi = jnp.sqrt(lam) * jnp.kron(a, b) + jnp.exp(1j * phase) * jnp.sqrt(1.0 - lam) * jnp.kron(ap, bp)
    return density(psi)


def product_rho_from_frame(frame: dict[str, Any]) -> jax.Array:
    a = spinor(math.pi / 3.0, 0.21)
    b = spinor(float(frame["theta_b"]), float(frame["phi_b"]))
    return density(jnp.kron(a, b))


def partial_trace_a(rho: jax.Array) -> jax.Array:
    rows = []
    for a in range(2):
        row = []
        for ap in range(2):
            row.append(sum(rho[2 * a + b, 2 * ap + b] for b in range(2)))
        rows.append(row)
    return jnp.array(rows, dtype=jnp.complex128)


def partial_trace_b(rho: jax.Array) -> jax.Array:
    rows = []
    for b in range(2):
        row = []
        for bp in range(2):
            row.append(sum(rho[2 * a + b, 2 * a + bp] for a in range(2)))
        rows.append(row)
    return jnp.array(rows, dtype=jnp.complex128)


def von_neumann_entropy(rho: jax.Array) -> float:
    herm = (rho + jnp.conj(rho.T)) / 2.0
    vals = jnp.linalg.eigvalsh(herm)
    clipped = jnp.maximum(jnp.real(vals), 0.0)
    terms = jnp.where(clipped > ENTROPY_EPS, clipped * jnp.log2(clipped), 0.0)
    return py_float(-jnp.sum(terms))


def effective_rank(rho: jax.Array) -> int:
    vals = jnp.linalg.eigvalsh((rho + jnp.conj(rho.T)) / 2.0)
    return int(py_float(jnp.sum(jnp.real(vals) > TOL)))


def readout(rho: jax.Array) -> dict[str, Any]:
    rho_a = partial_trace_a(rho)
    rho_b = partial_trace_b(rho)
    s_a = von_neumann_entropy(rho_a)
    s_b = von_neumann_entropy(rho_b)
    s_ab = von_neumann_entropy(rho)
    return {
        "S_A": s_a,
        "S_B": s_b,
        "S_AB": s_ab,
        "S_A_given_B": s_ab - s_b,
        "I_c_A_to_B": s_b - s_ab,
        "I_A_B": s_a + s_b - s_ab,
        "purity": py_float(jnp.real(jnp.trace(rho @ rho))),
        "effective_rank": effective_rank(rho),
    }


def density_diagnostics(rho: jax.Array) -> dict[str, Any]:
    vals = jnp.linalg.eigvalsh((rho + jnp.conj(rho.T)) / 2.0)
    return {
        "trace_residual": py_float(jnp.abs(jnp.real(jnp.trace(rho)) - 1.0)),
        "hermitian_residual": py_float(jnp.linalg.norm(rho - jnp.conj(rho.T))),
        "min_eigenvalue": py_float(jnp.min(jnp.real(vals))),
        "purity": py_float(jnp.real(jnp.trace(rho @ rho))),
    }


def xi_for_geometry(
    geometry: str,
    weights: list[float],
    *,
    product_cut: bool = False,
    one_future_pair: tuple[int, int] | None = None,
    remote_edit_pair: tuple[int, int] | None = None,
    remote_delta: float = 0.0,
) -> dict[str, Any]:
    xi = jnp.zeros((4, 4), dtype=jnp.complex128)
    frames: list[dict[str, Any]] = []
    rhos: dict[str, jax.Array] = {}
    branch_diag: list[dict[str, Any]] = []
    for idx, (j, k) in enumerate(branch_pairs()):
        w = weights[idx] if one_future_pair is None else (1.0 if (j, k) == one_future_pair else 0.0)
        frame = frame_for(geometry, j, k, w)
        delta = remote_delta if remote_edit_pair is not None and (j, k) == remote_edit_pair else 0.0
        rho = product_rho_from_frame(frame) if product_cut else rho_from_frame(frame, remote_delta=delta)
        xi = xi + w * rho
        frames.append(frame)
        rhos[pair_key(j, k)] = rho
        diag = density_diagnostics(rho)
        branch_diag.append(
            {
                "j": j,
                "k": k,
                "weight": w,
                "gamma": frame["gamma"],
                "lambda": frame["lambda"],
                "trace_residual": diag["trace_residual"],
                "hermitian_residual": diag["hermitian_residual"],
                "min_eigenvalue": diag["min_eigenvalue"],
            }
        )
    return {
        "geometry": geometry,
        "xi": xi,
        "frames": frames,
        "branch_rhos": rhos,
        "branch_diagnostics": branch_diag,
        "xi_diagnostics": density_diagnostics(xi),
        "readout": readout(xi),
    }


def readout_delta(a: dict[str, Any], b: dict[str, Any]) -> dict[str, float]:
    diffs: dict[str, float] = {}
    max_diff = 0.0
    for key in ("I_c_A_to_B", "S_A_given_B", "I_A_B"):
        diff = abs(float(a[key]) - float(b[key]))
        diffs[key] = diff
        max_diff = max(max_diff, diff)
    diffs["max"] = max_diff
    return diffs


def weighted_signature(frames: list[dict[str, Any]]) -> list[float]:
    total = sum(float(f["weight"]) for f in frames)
    return [
        sum(float(f["weight"]) * float(f["gamma"]) for f in frames) / total,
        sum(float(f["weight"]) * float(f["lambda"]) for f in frames) / total,
        sum(float(f["weight"]) * math.cos(float(f["phase"])) for f in frames) / total,
        sum(float(f["weight"]) * math.sin(float(f["phase"])) for f in frames) / total,
    ]


def matrix_linf(a: jax.Array, b: jax.Array) -> float:
    return py_float(jnp.max(jnp.abs(a - b)))


def ftl_message_check(weights: list[float]) -> dict[str, Any]:
    base = xi_for_geometry("nested_hopf_tori", weights)
    edited = xi_for_geometry("nested_hopf_tori", weights, remote_edit_pair=REMOTE_EDIT_PAIR, remote_delta=REMOTE_EDIT_DELTA)
    key = pair_key(*REMOTE_EDIT_PAIR)
    branch_a_diff = matrix_linf(partial_trace_a(base["branch_rhos"][key]), partial_trace_a(edited["branch_rhos"][key]))
    global_a_diff = matrix_linf(partial_trace_a(base["xi"]), partial_trace_a(edited["xi"]))
    global_readout_delta = readout_delta(base["readout"], edited["readout"])
    leak = branch_a_diff > TOL or global_a_diff > TOL
    return {
        "remote_edit_pair": list(REMOTE_EDIT_PAIR),
        "remote_edit_delta": REMOTE_EDIT_DELTA,
        "branch_rho_A_linf_diff": branch_a_diff,
        "global_rho_A_linf_diff": global_a_diff,
        "global_readout_delta": global_readout_delta,
        "global_readout_changed": global_readout_delta["max"] > STRICT_STOP_TOL,
        "remote_marginal_invariant": not leak,
        "controllable_ftl_message_capacity": 1.0 if leak else 0.0,
        "verdict": "LEAK_FALSIFIES_MODEL" if leak else "ZERO_CONTROLLABLE_MESSAGE",
    }


def parity_against_peer(result: dict[str, Any], peer_path: Path) -> dict[str, Any]:
    if not peer_path.exists():
        return {
            "peer_result_path": str(peer_path),
            "status": "missing_julia_reference",
            "shared_scalar_rows": [],
            "max_diff_key": None,
            "parity_max_diff": None,
            "within_1e_9": False,
            "strict_divergence_gt_1e_6": [],
            "boolean_mismatches": [],
            "missing_keys": [],
            "stop_condition_fired": False,
        }
    peer = json.loads(peer_path.read_text(encoding="utf-8"))
    rows = []
    max_diff = 0.0
    max_diff_key = None
    strict = []
    missing = []
    for key, value in result["shared_scalars"].items():
        if key not in peer.get("shared_scalars", {}):
            missing.append(key)
            continue
        jv = float(value)
        pv = float(peer["shared_scalars"][key])
        diff = abs(jv - pv)
        if diff > max_diff:
            max_diff = diff
            max_diff_key = key
        row = {"key": key, "jax": jv, "julia": pv, "abs_diff": diff}
        rows.append(row)
        if diff > STRICT_STOP_TOL:
            strict.append(row)
    mismatches = []
    for key, value in result["shared_booleans"].items():
        if key not in peer.get("shared_booleans", {}):
            missing.append(key)
            continue
        if bool(value) != bool(peer["shared_booleans"][key]):
            mismatches.append({"key": key, "jax": bool(value), "julia": bool(peer["shared_booleans"][key])})
    return {
        "peer_result_path": str(peer_path),
        "status": "compared",
        "shared_scalar_rows": rows,
        "max_diff_key": max_diff_key,
        "parity_max_diff": max_diff,
        "within_1e_9": max_diff < TOL and not strict and not mismatches and not missing,
        "strict_divergence_gt_1e_6": strict,
        "boolean_mismatches": mismatches,
        "missing_keys": missing,
        "stop_condition_fired": bool(strict) or bool(mismatches) or bool(missing),
    }


def scalarize_readout(prefix: str, readout_dict: dict[str, Any]) -> dict[str, float]:
    return {
        f"{prefix}.I_c_A_to_B": float(readout_dict["I_c_A_to_B"]),
        f"{prefix}.S_A_given_B": float(readout_dict["S_A_given_B"]),
        f"{prefix}.I_A_B": float(readout_dict["I_A_B"]),
        f"{prefix}.S_AB": float(readout_dict["S_AB"]),
        f"{prefix}.purity": float(readout_dict["purity"]),
        f"{prefix}.effective_rank": float(readout_dict["effective_rank"]),
    }


def build_result() -> dict[str, Any]:
    weights = branch_weights()
    nested = xi_for_geometry("nested_hopf_tori", weights)
    flat = xi_for_geometry("flat_s2_product", weights)
    scrambled = xi_for_geometry("nested_hopf_tori", scrambled_weights(weights))
    one_future = xi_for_geometry("nested_hopf_tori", weights, one_future_pair=(2, 2))
    product_cut = xi_for_geometry("nested_hopf_tori", weights, product_cut=True)
    ftl = ftl_message_check(weights)

    geometry_delta = readout_delta(nested["readout"], flat["readout"])
    scrambled_delta = readout_delta(nested["readout"], scrambled["readout"])
    product_ic_abs = abs(float(product_cut["readout"]["I_c_A_to_B"]))
    one_future_degenerate = int(one_future["readout"]["effective_rank"]) == 1 and abs(float(one_future["readout"]["S_AB"])) < TOL
    nested_signature = weighted_signature(nested["frames"])
    flat_signature = weighted_signature(flat["frames"])
    geometry_signature_l2 = math.sqrt(sum((a - b) ** 2 for a, b in zip(nested_signature, flat_signature, strict=True)))
    flat_same_to_machine = geometry_delta["max"] < TOL
    geometry_verdict = "KILLED_BY_FLAT_CONTROL" if flat_same_to_machine else "SURVIVED_CANDIDATE_ONLY"
    xi_geometry_load_bearing = "FALSE" if flat_same_to_machine else "SURVIVED (candidate only)"

    controls = {
        "flat_geometry_is_distinct": geometry_signature_l2 > STRICT_STOP_TOL,
        "scrambled_Omega_changes_readout": scrambled_delta["max"] > STRICT_STOP_TOL,
        "one_future_degenerates": one_future_degenerate,
        "product_no_entanglement_cut_Ic_zero": product_ic_abs < TOL,
        "zero_controllable_message": ftl["controllable_ftl_message_capacity"] == 0.0,
    }
    verdicts = {
        "xi_geometry_load_bearing_candidate": not flat_same_to_machine,
        "flat_control_killed_geometry_load_bearing": flat_same_to_machine,
        "kill_control_valid": controls["flat_geometry_is_distinct"],
        "controls_pass": all(bool(v) for v in controls.values()),
        "promotion_allowed": False,
        "formal_admission_allowed": False,
    }

    shared_scalars: dict[str, float] = {}
    shared_scalars.update(scalarize_readout("nested", nested["readout"]))
    shared_scalars.update(scalarize_readout("flat", flat["readout"]))
    shared_scalars.update(scalarize_readout("scrambled", scrambled["readout"]))
    shared_scalars.update(scalarize_readout("one_future", one_future["readout"]))
    shared_scalars.update(scalarize_readout("product_cut", product_cut["readout"]))
    shared_scalars["nested_flat_delta.I_c_A_to_B"] = geometry_delta["I_c_A_to_B"]
    shared_scalars["nested_flat_delta.S_A_given_B"] = geometry_delta["S_A_given_B"]
    shared_scalars["nested_flat_delta.I_A_B"] = geometry_delta["I_A_B"]
    shared_scalars["nested_flat_delta.max"] = geometry_delta["max"]
    shared_scalars["scrambled_delta.max"] = scrambled_delta["max"]
    shared_scalars["product_cut.I_c_abs"] = product_ic_abs
    shared_scalars["geometry_signature_l2"] = geometry_signature_l2
    shared_scalars["ftl.branch_rho_A_linf_diff"] = ftl["branch_rho_A_linf_diff"]
    shared_scalars["ftl.global_rho_A_linf_diff"] = ftl["global_rho_A_linf_diff"]
    shared_scalars["ftl.global_readout_delta.max"] = ftl["global_readout_delta"]["max"]
    shared_scalars["ftl.controllable_message_capacity"] = ftl["controllable_ftl_message_capacity"]

    shared_booleans = {f"control.{key}": value for key, value in controls.items()}
    shared_booleans.update({f"verdict.{key}": value for key, value in verdicts.items()})

    result: dict[str, Any] = {
        "object_id": OBJECT_ID,
        "backend": "jax_full_sim",
        "generated_at": _dt.datetime.now(_dt.UTC).isoformat(),
        "source_path": str(Path(__file__).resolve()),
        "result_path": str(RESULT_PATH),
        "peer_result_path": str(JULIA_REFERENCE_PATH),
        "jax_enable_x64": bool(jax.config.read("jax_enable_x64")),
        "classification": "scratch_diagnostic",
        "fence": "formal_scout/scratch_diagnostic",
        "promotion_allowed": False,
        "PROMOTION_ALLOWED": False,
        "formal_admission_allowed": False,
        "FORMAL_ADMISSION_ALLOWED": False,
        "claim_ceiling": "Finite Xi_shell bridge object and kill controls only; no Axis0, gravity, physics, bridge-admission, FEP, consciousness, or formal admission claim.",
        "sim_execution_kind": "bridge",
        "sim_class": "xi_shell_bridge_flat_geometry_kill_control_probe",
        "tol": TOL,
        "strict_stop_tol": STRICT_STOP_TOL,
        "blocked_consumers": BLOCKED_CONSUMERS,
        "eligible_consumers": ["formal_scout_review_only"],
        "allowed_claims": [
            "finite Xi_fuzz cut object exists in this probe",
            "flat geometry kill control result for this finite construction",
            "zero-controllable-message diagnostic for the branch edit tested",
        ],
        "geometry_control": {
            "nested": "S3 nested Hopf torus frame z=cos(eta)e^{i phi}, w=sin(eta)e^{i chi}; base/fiber feed Weyl/gamma state construction",
            "flat": "plain product of two independent S2 spinor frames; same gamma-to-lambda and rho_AB construction, no S3 eta/fiber",
            "same_weights_for_nested_and_flat": True,
            "geometry_signature_l2": geometry_signature_l2,
        },
        "branch_weights": weights,
        "fuzz_field": {
            "index_set": [[j, k] for j, k in branch_pairs()],
            "weight_rule": "normalized positive finite compatibility weights over (j,k); identical for nested and flat kill control",
            "Xi_fuzz": "sum_jk p(j,k) rho_AB(j,k)",
            "axis0_readout_names_only": ["I_c_A_to_B", "S_A_given_B", "I_A_B"],
        },
        "xi_geometry_load_bearing": xi_geometry_load_bearing,
        "geometry_load_bearing_verdict": geometry_verdict,
        "nested_readout": nested["readout"],
        "flat_readout": flat["readout"],
        "nested_flat_delta": geometry_delta,
        "scrambled_Omega_control": {"readout": scrambled["readout"], "delta_from_nested": scrambled_delta},
        "one_future_control": {"selected_branch": [2, 2], "readout": one_future["readout"], "degenerate": one_future_degenerate},
        "product_no_entanglement_cut": {"readout": product_cut["readout"], "I_c_abs": product_ic_abs},
        "ftl_message_capacity_check": ftl,
        "controls": controls,
        "verdicts": verdicts,
        "nested_branch_diagnostics": nested["branch_diagnostics"],
        "flat_branch_diagnostics": flat["branch_diagnostics"],
        "xi_diagnostics": {
            "nested": nested["xi_diagnostics"],
            "flat": flat["xi_diagnostics"],
            "scrambled": scrambled["xi_diagnostics"],
            "one_future": one_future["xi_diagnostics"],
            "product_cut": product_cut["xi_diagnostics"],
        },
        "tool_manifest": {
            "JAX": "load-bearing finite branch map, x64 density matrices, controls, and result synthesis",
            "jax.numpy": "load-bearing partial traces, eigenspectra, entropies, norms, and parity scalars",
            "json": "supportive result serialization",
        },
        "TOOL_MANIFEST": {
            "JAX": "load-bearing finite branch map, x64 density matrices, controls, and result synthesis",
            "jax.numpy": "load-bearing partial traces, eigenspectra, entropies, norms, and parity scalars",
            "json": "supportive result serialization",
        },
        "tool_integration_depth": {"JAX": "load_bearing", "jax.numpy": "load_bearing", "json": "supportive"},
        "TOOL_INTEGRATION_DEPTH": {"JAX": "load_bearing", "jax.numpy": "load_bearing", "json": "supportive"},
        "divergence_log": [
            "flat_s2_product kill control compared against nested_hopf_tori with identical branch weights",
            "scrambled_Omega, one_future, product_no_entanglement_cut, and remote-branch FTL controls run",
        ],
        "shared_scalars": shared_scalars,
        "shared_booleans": shared_booleans,
        "plain_sentence": "This is only a finite Xi_shell bridge falsifier: it computes Xi_fuzz readouts on nested-Hopf versus flat S2-product geometry and keeps Axis0/gravity/physics consumers blocked.",
    }
    result["parity"] = parity_against_peer(result, JULIA_REFERENCE_PATH)
    result["stop_condition_fired"] = (not verdicts["controls_pass"]) or bool(result["parity"]["stop_condition_fired"])
    return result


def print_summary(result: dict[str, Any]) -> None:
    n = result["nested_readout"]
    f = result["flat_readout"]
    print("xi_shell_bridge_probe - JAX full sim")
    print(f"nested_hopf I_c={n['I_c_A_to_B']} S(A|B)={n['S_A_given_B']} I(A:B)={n['I_A_B']}")
    print(f"flat_s2_product I_c={f['I_c_A_to_B']} S(A|B)={f['S_A_given_B']} I(A:B)={f['I_A_B']}")
    print(
        f"xi_geometry_load_bearing={result['xi_geometry_load_bearing']} "
        f"verdict={result['geometry_load_bearing_verdict']} "
        f"nested_flat_delta_max={result['nested_flat_delta']['max']}"
    )
    print(
        f"scrambled_Omega_changes_readout={str(result['controls']['scrambled_Omega_changes_readout']).lower()} "
        f"delta_max={result['scrambled_Omega_control']['delta_from_nested']['max']}"
    )
    print(
        f"one_future_degenerates={str(result['one_future_control']['degenerate']).lower()} "
        f"S_AB={result['one_future_control']['readout']['S_AB']} "
        f"effective_rank={result['one_future_control']['readout']['effective_rank']}"
    )
    print(
        f"product_no_entanglement_cut_Ic_zero={str(result['controls']['product_no_entanglement_cut_Ic_zero']).lower()} "
        f"I_c={result['product_no_entanglement_cut']['readout']['I_c_A_to_B']}"
    )
    ftl = result["ftl_message_capacity_check"]
    print(
        f"controllable_ftl_message_capacity={ftl['controllable_ftl_message_capacity']} "
        f"branch_rho_A_linf_diff={ftl['branch_rho_A_linf_diff']} "
        f"global_readout_delta_max={ftl['global_readout_delta']['max']}"
    )
    parity = result["parity"]
    print(
        f"parity_status={parity['status']} parity_max_diff={parity['parity_max_diff']} "
        f"within_1e-9={str(parity['within_1e_9']).lower()}"
    )
    print(f"blocked_consumers={','.join(result['blocked_consumers'])}")
    print(f"wrote: {result['result_path']}")


def main() -> int:
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print_summary(result)
    if result["stop_condition_fired"]:
        print("STOP: xi_shell_bridge_probe control/parity condition failed.")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
