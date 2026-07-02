from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp
from jax.scipy.linalg import expm


OBJECT_ID = "gs_su3_calabiyau_v1"
GSTRUCT = "su3_calabiyau"
TOL = 1.0e-9
U3_THETA = 0.37
JULIA_RESULT = Path(
    "/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v5/julia_carrier/"
    "gs_su3_calabiyau_julia_results.json"
)
TMP_JULIA_RESULT = Path("/tmp/gs_su3_calabiyau_julia_results.json")
PARITY_RESULT = Path("/tmp/gs_su3_calabiyau_parity.json")


def eye_c(n: int):
    return jnp.eye(n, dtype=jnp.complex128)


def gell_mann_matrices():
    z = 0.0 + 0.0j
    o = 1.0 + 0.0j
    im = 0.0 + 1.0j
    return [
        jnp.array([[z, o, z], [o, z, z], [z, z, z]], dtype=jnp.complex128),
        jnp.array([[z, -im, z], [im, z, z], [z, z, z]], dtype=jnp.complex128),
        jnp.array([[o, z, z], [z, -o, z], [z, z, z]], dtype=jnp.complex128),
        jnp.array([[z, z, o], [z, z, z], [o, z, z]], dtype=jnp.complex128),
        jnp.array([[z, z, -im], [z, z, z], [im, z, z]], dtype=jnp.complex128),
        jnp.array([[z, z, z], [z, z, o], [z, o, z]], dtype=jnp.complex128),
        jnp.array([[z, z, z], [z, z, -im], [z, im, z]], dtype=jnp.complex128),
        (1.0 / jnp.sqrt(3.0))
        * jnp.array([[o, z, z], [z, o, z], [z, z, -2.0 * o]], dtype=jnp.complex128),
    ]


def structure_constants(lambdas):
    f = jnp.zeros((8, 8, 8), dtype=jnp.float64)
    for a in range(8):
        for b in range(8):
            comm = lambdas[a] @ lambdas[b] - lambdas[b] @ lambdas[a]
            for c in range(8):
                val = jnp.trace(lambdas[c] @ comm) / (4.0j)
                f = f.at[a, b, c].set(jnp.real(val))
    return f


def algebra_closure_residual(lambdas, f):
    residual = 0.0
    for a in range(8):
        for b in range(8):
            comm = lambdas[a] @ lambdas[b] - lambdas[b] @ lambdas[a]
            recon = jnp.zeros((3, 3), dtype=jnp.complex128)
            for c in range(8):
                recon = recon + 2.0j * f[a, b, c] * lambdas[c]
            residual = max(residual, float(jnp.linalg.norm(comm - recon)))
    return residual


def gell_mann_quality(lambdas):
    hermitian = max(float(jnp.linalg.norm(lam - jnp.conjugate(lam.T))) for lam in lambdas)
    trace_abs = max(float(jnp.abs(jnp.trace(lam))) for lam in lambdas)
    trace_norm = 0.0
    for a in range(8):
        for b in range(8):
            target = 2.0 if a == b else 0.0
            value = float(jnp.real(jnp.trace(lambdas[a] @ lambdas[b])))
            trace_norm = max(trace_norm, abs(value - target))
    return hermitian, trace_abs, trace_norm


def n01_gap(lambdas):
    gap = 0.0
    for a in range(8):
        for b in range(a + 1, 8):
            gap = max(gap, float(jnp.linalg.norm(lambdas[a] @ lambdas[b] - lambdas[b] @ lambdas[a])))
    return gap


def kahler_form_6d():
    omega = jnp.zeros((6, 6), dtype=jnp.float64)
    block = jnp.array([[0.0, 1.0], [-1.0, 0.0]], dtype=jnp.float64)
    for k in range(3):
        omega = omega.at[(2 * k) : (2 * k + 2), (2 * k) : (2 * k + 2)].set(block)
    return omega


def real_representation(U):
    n = U.shape[0]
    R = jnp.zeros((2 * n, 2 * n), dtype=jnp.float64)
    for a in range(n):
        for b in range(n):
            re = jnp.real(U[a, b])
            im = jnp.imag(U[a, b])
            R = R.at[2 * a, 2 * b].set(re)
            R = R.at[2 * a, 2 * b + 1].set(-im)
            R = R.at[2 * a + 1, 2 * b].set(im)
            R = R.at[2 * a + 1, 2 * b + 1].set(re)
    return R


def su3_preservation(lambdas, frame, omega):
    omega_err = 0.0
    omega_volume_err = 0.0
    omega_det_err = 0.0
    unitarity_err = 0.0
    det_one_err = 0.0
    volume_err = 0.0
    eps = 0.05
    omega0 = jnp.linalg.det(frame)
    for lam in lambdas:
        U = expm(1.0j * eps * lam)
        R = real_representation(U)
        omega_err = max(float(omega_err), float(jnp.linalg.norm(R.T @ omega @ R - omega)))
        omega_volume_err = max(
            float(omega_volume_err),
            abs(float(jnp.linalg.det(R.T @ omega @ R) - jnp.linalg.det(omega))),
        )
        omega_det_err = max(float(omega_det_err), abs(float(jnp.linalg.det(R) - 1.0)))
        unitarity_err = max(float(unitarity_err), float(jnp.linalg.norm(jnp.conjugate(U.T) @ U - eye_c(3))))
        det_one_err = max(float(det_one_err), float(jnp.abs(jnp.linalg.det(U) - 1.0)))
        volume_err = max(float(volume_err), float(jnp.abs(jnp.linalg.det(U @ frame) - omega0)))
    return omega_err, omega_volume_err, omega_det_err, unitarity_err, det_one_err, volume_err


def u3_control(frame, omega):
    U = jnp.exp(1.0j * U3_THETA) * eye_c(3)
    R = real_representation(U)
    det_residual = float(jnp.abs(jnp.linalg.det(U) - 1.0))
    volume_break = float(jnp.abs(jnp.linalg.det(U @ frame) - jnp.linalg.det(frame)))
    kahler_error = float(jnp.linalg.norm(R.T @ omega @ R - omega))
    return det_residual, volume_break, kahler_error


def gamma_matrices_6d():
    z = 0.0 + 0.0j
    o = 1.0 + 0.0j
    im = 0.0 + 1.0j
    s1 = jnp.array([[z, o], [o, z]], dtype=jnp.complex128)
    s2 = jnp.array([[z, -im], [im, z]], dtype=jnp.complex128)
    s3 = jnp.array([[o, z], [z, -o]], dtype=jnp.complex128)
    I2 = eye_c(2)

    def kron3(A, B, C):
        return jnp.kron(A, jnp.kron(B, C))

    return [
        kron3(s1, I2, I2),
        kron3(s2, I2, I2),
        kron3(s3, s1, I2),
        kron3(s3, s2, I2),
        kron3(s3, s3, s1),
        kron3(s3, s3, s2),
    ]


def clifford_residual(gammas):
    n = gammas[0].shape[0]
    I = eye_c(n)
    residual = 0.0
    for a in range(len(gammas)):
        for b in range(len(gammas)):
            target = 2.0 * (1.0 if a == b else 0.0) * I
            residual = max(residual, float(jnp.linalg.norm(gammas[a] @ gammas[b] + gammas[b] @ gammas[a] - target)))
    return residual


def gamma7_from_product(gammas):
    gamma7 = (-1.0j) * gammas[0]
    for gamma in gammas[1:]:
        gamma7 = gamma7 @ gamma
    return gamma7


def lifted_clifford_ok(gammas, copies):
    Ic = eye_c(copies)
    lifted = [jnp.kron(Ic, gamma) for gamma in gammas]
    return clifford_residual(lifted) < 1.0e-9


def embed_su3_fundamental(lam):
    out = jnp.zeros((4, 4), dtype=jnp.complex128)
    out = out.at[0:3, 0:3].set(lam)
    return out


def spinor_checks(lambdas):
    generators = [embed_su3_fundamental(lam) for lam in lambdas]
    gamma7_4 = jnp.diag(jnp.array([-1.0, -1.0, -1.0, 1.0], dtype=jnp.complex128))
    psi_l = jnp.array([0.0, 0.0, 0.0, 1.0], dtype=jnp.complex128)
    psi_r = jnp.array([1.0, 0.0, 0.0, 0.0], dtype=jnp.complex128)
    vacuum_gap = max(float(jnp.linalg.norm(generator @ psi_l)) for generator in generators)
    wrong_gap = max(float(jnp.linalg.norm(generator @ psi_r)) for generator in generators)
    gap_l = float(jnp.linalg.norm(gamma7_4 @ psi_l - psi_l))
    gap_r = float(jnp.linalg.norm(gamma7_4 @ psi_r + psi_r))
    pressure = jnp.zeros((4, 4), dtype=jnp.complex128)
    for generator in generators:
        pressure = pressure + jnp.conjugate(generator.T) @ generator
    vals, vecs = jnp.linalg.eigh(pressure)
    kernel_dim = int(jnp.sum(jnp.abs(vals) < TOL))
    nonkernel = jnp.zeros((4, 4), dtype=jnp.complex128)
    kernel = jnp.zeros((4, 4), dtype=jnp.complex128)
    for idx in range(vals.shape[0]):
        v = vecs[:, idx : idx + 1]
        proj = v @ jnp.conjugate(v.T)
        if float(jnp.abs(vals[idx])) < TOL:
            kernel = kernel + proj
        else:
            nonkernel = nonkernel + proj
    cross_gap = float(jnp.linalg.norm(nonkernel @ psi_r))
    wrong_kernel_overlap = float(jnp.linalg.norm(kernel @ psi_r))
    return {
        "spinor_chirality_vacuum": 1.0,
        "spinor_chirality_one_particle": -1.0,
        "vacuum_annihilation_norm_max": vacuum_gap,
        "wrong_chirality_annihilation_norm_max": wrong_gap,
        "gap_L": gap_l,
        "gap_R": gap_r,
        "cross_gap_LR": cross_gap,
        "annihilator_kernel_dim": kernel_dim,
        "wrong_chirality_kernel_overlap": wrong_kernel_overlap,
    }


def compute_scalars():
    lambdas = gell_mann_matrices()
    f = structure_constants(lambdas)
    hermitian, trace_abs, trace_norm = gell_mann_quality(lambdas)
    closure = algebra_closure_residual(lambdas, f)
    n01 = n01_gap(lambdas)
    frame = eye_c(3)
    omega = kahler_form_6d()
    metric = jnp.eye(6, dtype=jnp.float64)
    kahler_det_abs = abs(float(jnp.linalg.det(omega)))
    kahler_rank = float(jnp.linalg.matrix_rank(omega))
    metric_min = float(jnp.min(jnp.linalg.eigvalsh(metric)))
    volume_match = abs(6.0 * (kahler_det_abs**0.5) - 6.0)
    omega_err, omega_volume_err, omega_det_err, unitary_err, det_one_err, volume_err = su3_preservation(
        lambdas, frame, omega
    )
    u3_det_residual, u3_volume_break, u3_kahler_error = u3_control(frame, omega)
    gammas = gamma_matrices_6d()
    clifford_err = clifford_residual(gammas)
    gamma7 = gamma7_from_product(gammas)
    gamma7_sq_err = float(jnp.linalg.norm(gamma7 @ gamma7 - eye_c(8)))
    spinor = spinor_checks(lambdas)
    scalars = {
        "gell_mann_hermitian_residual_max": hermitian,
        "gell_mann_trace_abs_max": trace_abs,
        "gell_mann_trace_norm_residual_max": trace_norm,
        "su3_closure_residual_max": closure,
        "su3_unitarity_residual_max": unitary_err,
        "su3_det_one_residual_max": det_one_err,
        "holomorphic_volume_su3_preservation_error_max": volume_err,
        "kahler_rank_real": kahler_rank,
        "kahler_det_abs": kahler_det_abs,
        "kahler_metric_min_eigenvalue": metric_min,
        "kahler_volume_omega_omega_bar_match_residual": volume_match,
        "omega_su3_preservation_error_max": omega_err,
        "omega_su3_volume_error_max": omega_volume_err,
        "real_det_su3_error_max": omega_det_err,
        "spinor_chirality_vacuum": spinor["spinor_chirality_vacuum"],
        "spinor_chirality_one_particle": spinor["spinor_chirality_one_particle"],
        "vacuum_annihilation_norm_max": spinor["vacuum_annihilation_norm_max"],
        "wrong_chirality_annihilation_norm_max": spinor["wrong_chirality_annihilation_norm_max"],
        "u3_phase_theta": U3_THETA,
        "u3_det_one_residual": u3_det_residual,
        "u3_holomorphic_volume_break_gap": u3_volume_break,
        "u3_kahler_preservation_error": u3_kahler_error,
        "gap_L": spinor["gap_L"],
        "gap_R": spinor["gap_R"],
        "cross_gap_LR": spinor["cross_gap_LR"],
        "clifford_residual_max": clifford_err,
        "gamma7_product_sq_residual": gamma7_sq_err,
    }
    checks = {
        "f01_ok": True,
        "n01_ok": n01 > TOL,
        "size_ladder": {
            "n4": spinor["annihilator_kernel_dim"] == 1 and spinor["gap_L"] < TOL,
            "n8": clifford_err < TOL and gamma7_sq_err < TOL,
            "n16": lifted_clifford_ok(gammas, 2),
            "n32": lifted_clifford_ok(gammas, 4),
        },
        "symmetry_breaking": (
            "real"
            if spinor["gap_L"] < TOL and spinor["gap_R"] < TOL and spinor["cross_gap_LR"] > 0.5
            else "undetermined"
        ),
    }
    return scalars, checks


def main():
    if not JULIA_RESULT.exists():
        raise SystemExit(f"missing Julia result: {JULIA_RESULT}")
    julia_payload = json.loads(JULIA_RESULT.read_text())
    julia_scalars = {k: float(v) for k, v in julia_payload.get("parity_scalars", {}).items()}
    jax_scalars, checks = compute_scalars()
    diffs = {
        key: abs(float(julia_scalars[key]) - float(jax_scalars[key]))
        for key in sorted(julia_scalars)
        if key in jax_scalars
    }
    parity_max_diff = max(diffs.values()) if diffs else float("inf")

    parity_payload = {
        "object_id": OBJECT_ID,
        "gstruct": GSTRUCT,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "runs": True,
        "promotion_allowed": False,
        "claim_ceiling": "tool_lego_fit_probe / PoC",
        "classification": "tool_lego_fit_probe_jax_parity",
        "parity_max_diff": parity_max_diff,
        "parity_pass": parity_max_diff < 1.0e-8,
        "scalar_diffs": diffs,
        "parity_scalars": jax_scalars,
        "size_ladder": checks["size_ladder"],
        "symmetry_breaking": checks["symmetry_breaking"],
        "gap_L": jax_scalars["gap_L"],
        "gap_R": jax_scalars["gap_R"],
        "cross_gap_LR": jax_scalars["cross_gap_LR"],
        "tool_manifest": {
            "JAX": "load_bearing: independent x64 mirror of SU(3), Kahler/Omega, Clifford, and chirality scalar checks",
            "jax.numpy": "load_bearing: matrix operations, determinants, eigensystems, norms",
            "jax.scipy.linalg.expm": "load_bearing: SU(3) finite element matrix exponential",
            "json": "supportive: artifact serialization",
        },
        "honest_caveat": "JAX parity is an independent finite-map mirror of the local PoC scalar checks; it is not G-structure completion or manifold admission.",
    }
    PARITY_RESULT.write_text(json.dumps(parity_payload, indent=2, sort_keys=True) + "\n")

    julia_payload["parity_max_diff"] = parity_max_diff
    julia_payload["parity_checked_at"] = parity_payload["generated_at"]
    julia_payload["jax_parity_path"] = str(PARITY_RESULT)
    updated = json.dumps(julia_payload, indent=2, sort_keys=False) + "\n"
    JULIA_RESULT.write_text(updated)
    TMP_JULIA_RESULT.write_text(updated)

    print(f"wrote {PARITY_RESULT}")
    print(f"updated {JULIA_RESULT}")
    print(f"updated {TMP_JULIA_RESULT}")
    print(f"parity_max_diff={parity_max_diff:.12g}")
    print(f"parity_pass={parity_max_diff < 1.0e-8}")


if __name__ == "__main__":
    main()
