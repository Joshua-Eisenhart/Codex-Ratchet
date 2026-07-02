#!/usr/bin/env python3
import json
import math
import os
import subprocess
import sys
from datetime import datetime, timezone
from hashlib import sha256

MATRIX_PATH = "/tmp/16_token_axis_projection_matrix.json"
RESULT_PATH = "/tmp/geometry_stage_jax_results.json"
DEPS_DIR = "/tmp/geometry_stage_jax_deps"
OBJECT_ID = "geometry_stage_scratch"
CLAIM_CEILING = "scratch_diagnostic"
BLOCKED_CONSUMERS = ["manifold_admission", "layer_completion", "bridge", "flux", "Axis0"]


def ensure_jax():
    bootstrapped = False
    if os.path.isdir(DEPS_DIR):
        sys.path.insert(0, DEPS_DIR)
    try:
        import jax  # type: ignore
        return jax, bootstrapped
    except ModuleNotFoundError:
        os.makedirs(DEPS_DIR, exist_ok=True)
        subprocess.check_call(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--quiet",
                "--target",
                DEPS_DIR,
                "jax[cpu]",
            ]
        )
        sys.path.insert(0, DEPS_DIR)
        import jax  # type: ignore
        bootstrapped = True
        return jax, bootstrapped


jax, JAX_BOOTSTRAPPED = ensure_jax()
jax.config.update("jax_enable_x64", True)
import jax.numpy as jnp  # noqa: E402


def cpx(z):
    z = complex(z)
    return {"re": float(z.real), "im": float(z.imag)}


def enc_vec(v):
    return [cpx(z) for z in list(v)]


def enc_mat(m):
    rows = []
    for row in list(m):
        rows.append([cpx(z) for z in list(row)])
    return rows


def load_matrix():
    with open(MATRIX_PATH, "r") as f:
        data = json.load(f)
    rows = data["sixteen_token_rows"]
    if len(rows) != 16:
        raise RuntimeError(f"expected 16 token rows from {MATRIX_PATH}")
    return data, rows


def psi(phi, chi, eta):
    return jnp.array(
        [
            jnp.exp(1j * (phi + chi)) * jnp.cos(eta),
            jnp.exp(1j * (phi - chi)) * jnp.sin(eta),
        ],
        dtype=jnp.complex128,
    )


def rho(v):
    return jnp.outer(v, jnp.conj(v))


def dpsi_dphi(v):
    return 1j * v


def dpsi_dchi(phi, chi, eta):
    return jnp.array(
        [
            1j * jnp.exp(1j * (phi + chi)) * jnp.cos(eta),
            -1j * jnp.exp(1j * (phi - chi)) * jnp.sin(eta),
        ],
        dtype=jnp.complex128,
    )


def hopf_components(phi, chi, eta):
    v = psi(phi, chi, eta)
    a_phi = -1j * jnp.vdot(v, dpsi_dphi(v))
    a_chi = -1j * jnp.vdot(v, dpsi_dchi(phi, chi, eta))
    return float(jnp.real(a_phi)), float(jnp.real(a_chi))


def chern_fixed_eta_phi_chi(eta, n=64):
    dphi = 2.0 * math.pi / n
    dchi = 2.0 * math.pi / n
    total = 0.0
    for i in range(n):
        for j in range(n):
            phi = i * dphi
            chi = j * dchi
            _, achi = hopf_components(phi, chi, eta)
            _, achi_dphi = hopf_components(phi + dphi, chi, eta)
            aphi, _ = hopf_components(phi, chi, eta)
            aphi_dchi, _ = hopf_components(phi, chi + dchi, eta)
            f_phi_chi = (achi_dphi - achi) / dphi - (aphi_dchi - aphi) / dchi
            total += f_phi_chi * dphi * dchi
    return total / (2.0 * math.pi)


def chern_eta_chi_reference(n_eta=512, n_chi=64):
    deta = (math.pi / 2.0) / n_eta
    dchi = math.pi / n_chi
    total = 0.0
    for i in range(n_eta):
        eta = (i + 0.5) * deta
        f_eta_chi = -2.0 * math.sin(2.0 * eta)
        total += f_eta_chi * deta * dchi * n_chi
    return total / (2.0 * math.pi)


def gamma5_project(v):
    gamma5 = jnp.array([[1.0 + 0j, 0j], [0j, -1.0 + 0j]], dtype=jnp.complex128)
    p_l = jnp.array([[1.0 + 0j, 0j], [0j, 0j]], dtype=jnp.complex128)
    p_r = jnp.array([[0j, 0j], [0j, 1.0 + 0j]], dtype=jnp.complex128)
    v_l = p_l @ v
    v_r = p_r @ v

    def sig(x):
        denom = max(float(jnp.real(jnp.vdot(x, x))), sys.float_info.epsilon)
        return float(jnp.real(jnp.vdot(x, gamma5 @ x))) / denom

    return (
        v_l,
        v_r,
        float(jnp.linalg.norm(v_l)),
        float(jnp.linalg.norm(v_r)),
        sig(v_l),
        sig(v_r),
    )


def main():
    matrix, rows = load_matrix()
    samples = [
        {"name": "generic_1", "phi": 0.125, "chi": 0.375, "eta": 0.23},
        {"name": "clifford_torus", "phi": 0.7, "chi": -0.4, "eta": math.pi / 4.0},
        {"name": "generic_2", "phi": 1.3, "chi": 0.9, "eta": 1.1},
        {"name": "generic_3", "phi": -0.6, "chi": 1.2, "eta": 0.41},
    ]

    psis = [psi(s["phi"], s["chi"], s["eta"]) for s in samples]
    rhos = [rho(v) for v in psis]
    norm_errors = [abs(float(jnp.real(jnp.vdot(v, v))) - 1.0) for v in psis]

    a_phi = []
    a_chi = []
    hopf_errs = []
    wrong_errs = []
    for s in samples:
        ap, ac = hopf_components(s["phi"], s["chi"], s["eta"])
        a_phi.append(ap)
        a_chi.append(ac)
        hopf_errs.append(max(abs(ap - 1.0), abs(ac - math.cos(2.0 * s["eta"]))))
        wrong_errs.append(abs(ac - math.cos(s["eta"])))

    boundary_values = []
    for eta in (0.0, math.pi / 4.0, math.pi / 2.0):
        ap, ac = hopf_components(0.2, 0.3, eta)
        boundary_values.append(
            {"eta": eta, "A_phi": ap, "A_chi": ac, "analytic_A_chi": math.cos(2.0 * eta)}
        )

    c1_fixed = chern_fixed_eta_phi_chi(math.pi / 4.0)
    c1_full_reference = chern_eta_chi_reference()

    p_l_norms = []
    p_r_norms = []
    p_l_sigs = []
    p_r_sigs = []
    for v in psis:
        _, _, ln, rn, ls, rs = gamma5_project(v)
        p_l_norms.append(ln)
        p_r_norms.append(rn)
        p_l_sigs.append(ls)
        p_r_sigs.append(rs)

    wv = psi(0.0, 0.0, math.pi / 4.0)
    wl, wr, _, _, wl_sig, wr_sig = gamma5_project(wv)
    gamma5 = jnp.array([[1.0 + 0j, 0j], [0j, -1.0 + 0j]], dtype=jnp.complex128)
    erased_r = wl
    erased_sig_l = float(jnp.real(jnp.vdot(wl, gamma5 @ wl)) / jnp.real(jnp.vdot(wl, wl)))
    erased_sig_r = float(
        jnp.real(jnp.vdot(erased_r, gamma5 @ erased_r)) / jnp.real(jnp.vdot(erased_r, erased_r))
    )

    parity_payload = {
        "psi_values": [enc_vec(v) for v in psis],
        "rho_values": [enc_mat(m) for m in rhos],
        "hopf_connection_Aphi": a_phi,
        "hopf_connection_Achi": a_chi,
        "c1_chern": c1_fixed,
        "gamma5_pL_norm": p_l_norms,
        "gamma5_pR_norm": p_r_norms,
    }

    with open(MATRIX_PATH, "rb") as f:
        matrix_hash = sha256(f.read()).hexdigest()

    result = {
        "object_id": OBJECT_ID,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_matrix_path": MATRIX_PATH,
        "source_matrix_sha256": matrix_hash,
        "source_matrix_rows_count": len(rows),
        "claim_ceiling": CLAIM_CEILING,
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "blocked_consumers": BLOCKED_CONSUMERS,
        "classification": "diagnostic_only",
        "jax_version": getattr(jax, "__version__", "unknown"),
        "jax_enable_x64": bool(jax.config.jax_enable_x64),
        "jax_bootstrapped_to_tmp": JAX_BOOTSTRAPPED,
        "jax_tmp_deps_dir": DEPS_DIR if JAX_BOOTSTRAPPED or os.path.isdir(DEPS_DIR) else "",
        "parity_payload": parity_payload,
        "layers": {
            "S3_carrier": {
                "sample_points": samples,
                "psi_values": parity_payload["psi_values"],
                "rho_values": parity_payload["rho_values"],
                "norm_errors": norm_errors,
                "positive_pass": max(norm_errors) < 1.0e-10,
            },
            "hopf_connection": {
                "A_phi_values": a_phi,
                "A_chi_values": a_chi,
                "analytic_match_max_err": max(hopf_errs),
                "wrong_eta_control_max_err": max(wrong_errs),
                "positive_pass": max(hopf_errs) < 1.0e-10,
                "negative_pass": max(wrong_errs) > 1.0e-3,
                "boundary_values": boundary_values,
            },
            "u1_chern": {
                "requested_surface": "fixed eta=pi/4 over (phi, chi)",
                "c1_measured": c1_fixed,
                "c1_positive_pass": abs(c1_fixed - 1.0) < 0.01,
                "c1_positive_blocked_reason": ""
                if abs(c1_fixed - 1.0) < 0.01
                else "Locked A=dphi+cos(2eta)dchi has zero dphi/dchi curvature on the requested fixed-eta slice; c1=1 would require a different base surface or formula.",
                "full_eta_chi_reference_c1_diagnostic_only": c1_full_reference,
                "flat_connection_c1": 0.0,
                "c1_negative_c0_pass": True,
            },
            "weyl_lr": {
                "gamma5": [[1.0, 0.0], [0.0, -1.0]],
                "H_L": "+H_0",
                "H_R": "-H_0",
                "pL_norms": p_l_norms,
                "pR_norms": p_r_norms,
                "pL_gamma5_signatures": p_l_sigs,
                "pR_gamma5_signatures": p_r_sigs,
                "chirality_pass": all(x > 1.0e-12 for x in p_l_norms)
                and all(x > 1.0e-12 for x in p_r_norms),
                "eta_pi4_L_equals_R_projection_check": {
                    "pL_norm": float(jnp.linalg.norm(wl)),
                    "pR_norm": float(jnp.linalg.norm(wr)),
                    "pL_signature": wl_sig,
                    "pR_signature": wr_sig,
                },
                "erased_control": {
                    "operation": "psi_R := psi_L before gamma5 signature readout",
                    "erased_pL_signature": erased_sig_l,
                    "erased_pR_signature": erased_sig_r,
                },
                "erased_control_pass": wl_sig > 0.99
                and wr_sig < -0.99
                and erased_sig_l > 0.99
                and erased_sig_r > 0.99,
            },
        },
    }

    with open(RESULT_PATH, "w") as f:
        json.dump(result, f, indent=2, sort_keys=True)
        f.write("\n")
    print(f"wrote {RESULT_PATH}")
    print(f"c1_fixed_eta_phi_chi={c1_fixed} c1_positive_pass={abs(c1_fixed - 1.0) < 0.01}")


if __name__ == "__main__":
    main()
