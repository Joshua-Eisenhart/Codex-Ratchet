#!/usr/bin/env python3
# object_id: weyl_sheet_pair_probe
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

import jax; jax.config.update("jax_enable_x64", True)

import datetime as _dt
import json
import re
from pathlib import Path
from typing import Any

import jax.numpy as jnp


OBJECT_ID = "weyl_sheet_pair_probe"
BASE_DIR = Path("/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier")
RESULT_PATH = BASE_DIR / "weyl_sheet_pair_probe_jax_results.json"
JULIA_REFERENCE_PATH = BASE_DIR / "weyl_sheet_pair_probe_julia_results.json"
TOL = 1.0e-9
STRICT_STOP_TOL = 1.0e-6

I2 = jnp.array([[1.0 + 0.0j, 0.0 + 0.0j], [0.0 + 0.0j, 1.0 + 0.0j]], dtype=jnp.complex128)
SX = jnp.array([[0.0 + 0.0j, 1.0 + 0.0j], [1.0 + 0.0j, 0.0 + 0.0j]], dtype=jnp.complex128)
SY = jnp.array([[0.0 + 0.0j, -1.0j], [1.0j, 0.0 + 0.0j]], dtype=jnp.complex128)
SZ = jnp.array([[1.0 + 0.0j, 0.0 + 0.0j], [0.0 + 0.0j, -1.0 + 0.0j]], dtype=jnp.complex128)
N_REF = jnp.array([0.0, 0.0, 1.0], dtype=jnp.float64)


def py_float(x: Any) -> float:
    return float(jax.device_get(x))


def py_bool(x: Any) -> bool:
    return bool(jax.device_get(x))


def vec_payload(v: jax.Array) -> list[float]:
    return [py_float(v[i]) for i in range(int(v.shape[0]))]


def jax_x64_enabled() -> bool:
    try:
        return bool(jax.config.jax_enable_x64)
    except AttributeError:
        return bool(jax.config.read("jax_enable_x64"))


def source_numpy_markers() -> dict[str, bool]:
    text = Path(__file__).read_text(encoding="utf-8")
    return {
        "import_numpy_present": ("import " + "numpy") in text or ("from " + "numpy") in text,
        "np_dot_present": re.search(r"(?<![A-Za-z0-9_])np\.", text) is not None,
        "numpy_method_bridge_present": ("." + "numpy()") in text,
    }


def dm(psi: jax.Array) -> jax.Array:
    return jnp.outer(psi, jnp.conj(psi))


def rho_from_bloch(r: jax.Array) -> jax.Array:
    return 0.5 * (I2 + r[0] * SX + r[1] * SY + r[2] * SZ)


def bloch_from_rho(rho: jax.Array) -> jax.Array:
    return jnp.array(
        [
            jnp.real(jnp.trace(rho @ SX)),
            jnp.real(jnp.trace(rho @ SY)),
            jnp.real(jnp.trace(rho @ SZ)),
        ],
        dtype=jnp.float64,
    )


def spinor_from_angles(theta: float, phi: float, fiber_phase: float) -> jax.Array:
    return jnp.exp(1j * fiber_phase) * jnp.array(
        [jnp.cos(theta / 2.0), jnp.exp(1j * phi) * jnp.sin(theta / 2.0)],
        dtype=jnp.complex128,
    )


def spinor_from_bloch(r: jax.Array, fiber_phase: float) -> jax.Array:
    rn = r / jnp.linalg.norm(r)
    x = rn[0]
    y = rn[1]
    z = rn[2]
    if py_float(1.0 + z) > 1.0e-12:
        denom = jnp.sqrt(2.0 * (1.0 + z))
        section = jnp.array(
            [jnp.sqrt((1.0 + z) / 2.0), (x + 1j * y) / denom],
            dtype=jnp.complex128,
        )
    else:
        denom = jnp.sqrt(2.0 * (1.0 - z))
        section = jnp.array(
            [(x - 1j * y) / denom, jnp.sqrt((1.0 - z) / 2.0)],
            dtype=jnp.complex128,
        )
    return jnp.exp(1j * fiber_phase) * section / jnp.linalg.norm(section)


def canonical_section(r: jax.Array) -> jax.Array:
    return spinor_from_bloch(r, 0.0)


def fiber_phase(psi: jax.Array, r: jax.Array) -> jax.Array:
    anchor = canonical_section(r)
    z = jnp.vdot(anchor, psi)
    return jnp.arctan2(jnp.imag(z), jnp.real(z))


def wrap_phase(x: jax.Array) -> jax.Array:
    return jnp.arctan2(jnp.sin(x), jnp.cos(x))


def sigma_from_ref(n: jax.Array) -> jax.Array:
    return n[0] * SX + n[1] * SY + n[2] * SZ


def bool_scalar(value: bool) -> float:
    return 1.0 if value else 0.0


def pair_metrics(label: str, psi_l: jax.Array, psi_r: jax.Array) -> dict[str, Any]:
    rho_l = dm(psi_l)
    rho_r = dm(psi_r)
    r_l = bloch_from_rho(rho_l)
    r_r = bloch_from_rho(rho_r)
    m_sigma = sigma_from_ref(N_REF)

    signed_volume = jnp.dot(jnp.cross(r_l, r_r), N_REF)
    trace_chi = 2.0 * jnp.imag(jnp.trace(rho_l @ rho_r @ m_sigma))
    transverse_l = r_l - jnp.dot(r_l, N_REF) * N_REF
    transverse_r = r_r - jnp.dot(r_r, N_REF) * N_REF
    alpha_l = fiber_phase(psi_l, r_l)
    alpha_r = fiber_phase(psi_r, r_r)

    norm_residual = jnp.maximum(
        jnp.abs(jnp.real(jnp.vdot(psi_l, psi_l)) - 1.0),
        jnp.abs(jnp.real(jnp.vdot(psi_r, psi_r)) - 1.0),
    )
    trace_residual = jnp.maximum(
        jnp.abs(jnp.real(jnp.trace(rho_l)) - 1.0),
        jnp.abs(jnp.real(jnp.trace(rho_r)) - 1.0),
    )
    hermitian_residual = jnp.maximum(
        jnp.linalg.norm(rho_l - jnp.conj(rho_l.T)),
        jnp.linalg.norm(rho_r - jnp.conj(rho_r.T)),
    )
    idempotency_residual = jnp.maximum(
        jnp.linalg.norm(rho_l @ rho_l - rho_l),
        jnp.linalg.norm(rho_r @ rho_r - rho_r),
    )
    hopf_s2_residual = jnp.maximum(
        jnp.abs(jnp.linalg.norm(r_l) - 1.0),
        jnp.abs(jnp.linalg.norm(r_r) - 1.0),
    )
    rho_rebuild_residual = jnp.maximum(
        jnp.linalg.norm(rho_l - rho_from_bloch(r_l)),
        jnp.linalg.norm(rho_r - rho_from_bloch(r_r)),
    )

    return {
        "label": label,
        "chi": py_float(signed_volume),
        "chi_trace_form": py_float(trace_chi),
        "chi_trace_residual": py_float(jnp.abs(signed_volume - trace_chi)),
        "r_L": vec_payload(r_l),
        "r_R": vec_payload(r_r),
        "rho_L_trace_residual": py_float(jnp.abs(jnp.real(jnp.trace(rho_l)) - 1.0)),
        "rho_R_trace_residual": py_float(jnp.abs(jnp.real(jnp.trace(rho_r)) - 1.0)),
        "spinor_norm_residual": py_float(norm_residual),
        "trace_rho_residual": py_float(trace_residual),
        "hermitian_residual": py_float(hermitian_residual),
        "idempotency_residual": py_float(idempotency_residual),
        "hopf_s2_residual": py_float(hopf_s2_residual),
        "rho_reconstruction_residual": py_float(rho_rebuild_residual),
        "relative_fiber_phase": py_float(wrap_phase(alpha_l - alpha_r)),
        "fiber_phase_L": py_float(alpha_l),
        "fiber_phase_R": py_float(alpha_r),
        "transverse_scale": py_float(jnp.linalg.norm(transverse_l) * jnp.linalg.norm(transverse_r)),
        "overlap_abs": py_float(jnp.abs(jnp.vdot(psi_l, psi_r))),
    }


def parity_block(result: dict[str, Any]) -> dict[str, Any]:
    if not JULIA_REFERENCE_PATH.exists():
        return {
            "peer_result_path": str(JULIA_REFERENCE_PATH),
            "peer_available": False,
            "parity_max_diff": None,
            "worst_key": None,
            "within_1e_9": False,
            "strict_divergence_gt_1e_6": True,
            "missing_from_peer": sorted(result["shared_scalars"].keys()),
            "missing_from_self": [],
            "stop_condition_fired": True,
        }

    peer = json.loads(JULIA_REFERENCE_PATH.read_text(encoding="utf-8"))
    self_scalars = result["shared_scalars"]
    peer_scalars = peer["shared_scalars"]
    missing_from_peer = sorted(set(self_scalars) - set(peer_scalars))
    missing_from_self = sorted(set(peer_scalars) - set(self_scalars))
    diffs: dict[str, float] = {}
    max_diff = 0.0
    worst_key = ""

    for key, value in self_scalars.items():
        if key in peer_scalars:
            diff = abs(float(value) - float(peer_scalars[key]))
            diffs[key] = diff
            if diff > max_diff:
                max_diff = diff
                worst_key = key

    within = not missing_from_peer and not missing_from_self and max_diff < TOL
    strict_divergence = max_diff > STRICT_STOP_TOL
    return {
        "peer_result_path": str(JULIA_REFERENCE_PATH),
        "peer_available": True,
        "parity_max_diff": max_diff,
        "worst_key": worst_key,
        "within_1e_9": within,
        "strict_divergence_gt_1e_6": strict_divergence,
        "missing_from_peer": missing_from_peer,
        "missing_from_self": missing_from_self,
        "diffs": diffs,
        "stop_condition_fired": not within,
    }


def build_result() -> dict[str, Any]:
    psi_l = spinor_from_angles(1.07, -0.41, 0.73)
    psi_r = spinor_from_angles(0.82, 1.26, -0.18)
    generic = pair_metrics("generic_independent_LR", psi_l, psi_r)
    swap = pair_metrics("swap_RL", psi_r, psi_l)
    no_chirality = pair_metrics("no_chirality_same_hopf_base_pure_phase", psi_l, jnp.exp(1j * 0.61) * psi_l)

    parity_base = bloch_from_rho(dm(spinor_from_angles(1.11, 0.37, 0.21)))
    reflected = parity_base - 2.0 * jnp.dot(parity_base, N_REF) * N_REF
    parity_sym = pair_metrics(
        "parity_symmetric_reflection_across_ref_plane",
        spinor_from_bloch(parity_base, 0.22),
        spinor_from_bloch(reflected, -0.49),
    )
    no_chirality_antipodal = pair_metrics(
        "no_chirality_antipodal_hopf_base",
        spinor_from_bloch(parity_base, 0.14),
        spinor_from_bloch(-1.0 * parity_base, -0.32),
    )

    generic_chi = jnp.array(generic["chi"], dtype=jnp.float64)
    swap_chi = jnp.array(swap["chi"], dtype=jnp.float64)
    no_chirality_chi = jnp.array(no_chirality["chi"], dtype=jnp.float64)
    parity_symmetric_chi = jnp.array(parity_sym["chi"], dtype=jnp.float64)
    antipodal_chi = jnp.array(no_chirality_antipodal["chi"], dtype=jnp.float64)
    generic_overlap_abs = jnp.array(generic["overlap_abs"], dtype=jnp.float64)

    sign_flip_residual_j = jnp.abs(generic_chi + swap_chi)
    no_chirality_abs_j = jnp.abs(no_chirality_chi)
    parity_symmetric_abs_j = jnp.abs(parity_symmetric_chi)
    antipodal_abs_j = jnp.abs(antipodal_chi)
    sign_flip_residual = py_float(sign_flip_residual_j)
    no_chirality_abs = py_float(no_chirality_abs_j)
    parity_symmetric_abs = py_float(parity_symmetric_abs_j)
    antipodal_abs = py_float(antipodal_abs_j)

    controls = {
        "swap_sign_flip": py_bool((sign_flip_residual_j <= TOL) & ((generic_chi * swap_chi) < 0.0)),
        "no_chirality_zero": py_bool(no_chirality_abs_j <= TOL),
        "parity_symmetric_zero": py_bool(parity_symmetric_abs_j <= TOL),
        "no_chirality_antipodal_zero": py_bool(antipodal_abs_j <= TOL),
    }
    verdicts = {
        "generic_independent_LR": py_bool(generic_overlap_abs < 1.0 - 1.0e-6),
        "generic_chi_nonzero": py_bool(jnp.abs(generic_chi) > TOL),
        "chirality_load_bearing": (
            py_bool(jnp.abs(generic_chi) > TOL)
            and controls["swap_sign_flip"]
            and controls["no_chirality_zero"]
            and controls["parity_symmetric_zero"]
        ),
        "controls_all_pass": all(controls.values()),
    }
    max_pair_residual = py_float(
        jnp.max(
            jnp.array(
                [
                    generic["chi_trace_residual"],
                    generic["spinor_norm_residual"],
                    generic["trace_rho_residual"],
                    generic["hermitian_residual"],
                    generic["idempotency_residual"],
                    generic["hopf_s2_residual"],
                    generic["rho_reconstruction_residual"],
                    swap["chi_trace_residual"],
                    no_chirality["chi_trace_residual"],
                    parity_sym["chi_trace_residual"],
                ],
                dtype=jnp.float64,
            )
        )
    )

    shared_scalars = {
        "generic_chi": float(generic["chi"]),
        "generic_chi_trace_form": float(generic["chi_trace_form"]),
        "generic_chi_trace_residual": float(generic["chi_trace_residual"]),
        "generic_transverse_scale": float(generic["transverse_scale"]),
        "generic_relative_fiber_phase": float(generic["relative_fiber_phase"]),
        "generic_overlap_abs": float(generic["overlap_abs"]),
        "swap_chi": float(swap["chi"]),
        "swap_sign_flip_residual": float(sign_flip_residual),
        "no_chirality_chi": float(no_chirality["chi"]),
        "no_chirality_abs": float(no_chirality_abs),
        "parity_symmetric_chi": float(parity_sym["chi"]),
        "parity_symmetric_abs": float(parity_symmetric_abs),
        "no_chirality_antipodal_chi": float(no_chirality_antipodal["chi"]),
        "no_chirality_antipodal_abs": float(antipodal_abs),
        "max_pair_residual": float(max_pair_residual),
        "control_swap_sign_flip": bool_scalar(controls["swap_sign_flip"]),
        "control_no_chirality_zero": bool_scalar(controls["no_chirality_zero"]),
        "control_parity_symmetric_zero": bool_scalar(controls["parity_symmetric_zero"]),
        "verdict_generic_chi_nonzero": bool_scalar(verdicts["generic_chi_nonzero"]),
        "verdict_chirality_load_bearing": bool_scalar(verdicts["chirality_load_bearing"]),
        "numpy_compute_used_flag": 0.0,
    }

    tool_manifest = {
        "JAX jax.numpy x64": {
            "tried": True,
            "used": True,
            "role": "mirror_stress_jnp_x64",
            "reason": "load-bearing for density matrices, Pauli traces, Bloch vectors, cross/dot witness, and residual norms using jax.numpy x64",
        },
        "Julia LinearAlgebra": {
            "tried": True,
            "used": False,
            "role": "peer_reference_expected",
            "reason": "supportive peer parity lane read from its result JSON when present; no Julia compute is used inside JAX",
        },
    }
    tool_depth = {
        "JAX jax.numpy x64": "load_bearing",
        "Julia LinearAlgebra": "supportive",
    }
    source_markers = source_numpy_markers()
    result: dict[str, Any] = {
        "object_id": OBJECT_ID,
        "backend": "jax",
        "backend_roles": {
            "julia": "reference_exact_linearalgebra",
            "jax": "mirror_stress_jnp_x64",
        },
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "PROMOTION_ALLOWED": False,
        "FORMAL_ADMISSION_ALLOWED": False,
        "sim_execution_kind": "nonclassical",
        "sim_class": "carrier_probe",
        "carrier_layer": "left_right_weyl_pair_over_two_independent_hopf_maps",
        "geometry_layer": "C2_spinor_to_Bloch_Hopf_base_per_sheet",
        "claim_ceiling": "Carrier-only L/R Weyl sheet chirality diagnostic; no engine admission, Axis0, gravity, win/lose, bridge, or formal admission claim.",
        "allowed_claims": [
            "finite chiral carrier readout for independent L/R Hopf-base sheets",
            "control-bounded load-bearing status of the parity-odd pair witness",
        ],
        "eligible_consumers": ["formal_scout_review_only"],
        "blocked_consumers": [
            "engine_admission",
            "Axis0",
            "gravity",
            "win_lose_dynamics",
            "formal_admission",
            "bridge_or_downstream_claim",
        ],
        "out_of_scope": [
            "engine admission",
            "Axis0",
            "gravity",
            "win/lose dynamics",
            "formal admission",
            "bridge or downstream physical claim",
        ],
        "demotion_condition": "Demote to miswired scratch diagnostic if swap sign does not flip, same-sheet phase control is nonzero, parity-symmetric reflection is nonzero, NumPy compute appears, or peer shared scalar parity fails.",
        "promotion_condition": "None in this run; promotion_allowed is false and formal_admission_allowed is false.",
        "blocked_until": "A separate admitted process defines IGT win/lose and downstream engine/Axis gates; this probe intentionally does not.",
        "created_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(Path(__file__)),
        "result_path": str(RESULT_PATH),
        "peer_result_path": str(JULIA_REFERENCE_PATH),
        "julia_reference_path": str(JULIA_REFERENCE_PATH),
        "tol": TOL,
        "strict_stop_tol": STRICT_STOP_TOL,
        "reference_axis": {
            "name": "pauli_z_sheet_normal",
            "vector": vec_payload(N_REF),
            "role": "fixed label-neutral carrier-frame axis for the parity-odd witness",
        },
        "witness": {
            "formula": "chi = n_ref dot (r_L cross r_R)",
            "trace_equivalent": "chi = 2 Im Tr(rho_L rho_R (n_ref dot sigma))",
            "swap_rule": "chi(R,L) = -chi(L,R)",
            "fiber_phase_role": "diagnostic_only_not_load_bearing",
        },
        "tools": ["JAX jax.numpy x64", "Julia LinearAlgebra"],
        "tool_manifest": tool_manifest,
        "TOOL_MANIFEST": tool_manifest,
        "tool_integration_depth": tool_depth,
        "TOOL_INTEGRATION_DEPTH": tool_depth,
        "numpy_compute_used": False,
        "source_numpy_markers": source_markers,
        "jax_x64_enabled": jax_x64_enabled(),
        "pairs": {
            "generic": generic,
            "swap": swap,
            "no_chirality": no_chirality,
            "parity_symmetric": parity_sym,
            "no_chirality_antipodal": no_chirality_antipodal,
        },
        "controls": controls,
        "verdicts": verdicts,
        "shared_scalars": shared_scalars,
        "divergence_log": [
            "Generic independent L/R sheets produce nonzero chi under the fixed carrier-frame reference axis.",
            "L/R swap is required to flip chi sign, not merely change magnitude.",
            "Same Hopf base with pure fiber phase and parity-symmetric reflected base are required to collapse chi to zero.",
            "This divergence is carrier-only and does not define IGT win/lose, engine admission, Axis0, gravity, bridge, or formal admission.",
        ],
        "honest_caveat": "scratch_diagnostic is used intentionally; generic receipt validators that only admit canonical/classical/tool-fit/supporting/audit classes may reject this as noncanonical.",
        "plain_sentence": "L/R chirality is load-bearing for this finite chiral carrier witness: the independent sheet pair has a nonzero parity-odd readout, while same-sheet and parity-symmetric controls collapse to generic spinor geometry.",
    }
    result["parity"] = parity_block(result)
    result["all_pass"] = (
        bool(result["jax_x64_enabled"])
        and not bool(result["numpy_compute_used"])
        and not any(source_markers.values())
        and bool(verdicts["generic_independent_LR"])
        and bool(verdicts["chirality_load_bearing"])
        and bool(verdicts["controls_all_pass"])
        and bool(result["parity"]["within_1e_9"])
    )
    result["stop_condition_fired"] = not bool(result["all_pass"])
    return result


def main() -> None:
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    s = result["shared_scalars"]
    print(f"weyl_sheet_pair_probe jax wrote {RESULT_PATH}")
    print(
        "generic_chi={generic} swap_chi={swap} no_chirality_chi={no} parity_symmetric_chi={parity}".format(
            generic=s["generic_chi"],
            swap=s["swap_chi"],
            no=s["no_chirality_chi"],
            parity=s["parity_symmetric_chi"],
        )
    )
    print(
        "chirality_load_bearing={load} parity_max_diff={diff} numpy_compute_used={numpy_used} jax_x64_enabled={x64}".format(
            load=result["verdicts"]["chirality_load_bearing"],
            diff=result["parity"]["parity_max_diff"],
            numpy_used=result["numpy_compute_used"],
            x64=result["jax_x64_enabled"],
        )
    )
    if result["stop_condition_fired"]:
        print("STOP_CONDITION_FIRED weyl_sheet_pair_probe jax")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
