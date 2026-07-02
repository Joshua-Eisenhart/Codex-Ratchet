import jax; jax.config.update("jax_enable_x64", True)
import json
from datetime import datetime, timezone
from pathlib import Path

import jax.numpy as jnp


CLAIM_CEILING = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
JULIA_RESULT_PATH = Path("/tmp/geometry_weyl_lr_gamma5_results.json")
OUT_PATH = Path("/tmp/geometry_weyl_lr_gamma5_jax_results.json")


def grid(n_grid):
    phis = jnp.linspace(0.0, 2.0 * jnp.pi, n_grid)
    chis = jnp.linspace(0.0, 2.0 * jnp.pi, n_grid)
    etas = jnp.linspace(0.0, 0.5 * jnp.pi, n_grid)
    phi, chi, eta = jnp.meshgrid(phis, chis, etas, indexing="ij")
    return phi.reshape(-1), chi.reshape(-1), eta.reshape(-1), phis, chis, etas


def psi_l(phi, chi, eta):
    return jnp.array(
        [
            jnp.exp(1j * (phi + chi)) * jnp.cos(eta),
            jnp.exp(1j * (phi - chi)) * jnp.sin(eta),
        ],
        dtype=jnp.complex128,
    )


def psi_r(phi, chi, eta):
    return jnp.conj(psi_l(phi, chi, eta))


gamma5 = jnp.diag(jnp.array([1.0, -1.0], dtype=jnp.float64)).astype(jnp.complex128)


def chirality(psi):
    return jnp.real(jnp.vdot(psi, gamma5 @ psi))


def density(psi):
    return jnp.outer(psi, jnp.conj(psi))


def ti(rho, q=0.3):
    p0 = jnp.array([[1.0, 0.0], [0.0, 0.0]], dtype=jnp.complex128)
    p1 = jnp.array([[0.0, 0.0], [0.0, 1.0]], dtype=jnp.complex128)
    return (1.0 - q) * rho + q * (p0 @ rho @ p0 + p1 @ rho @ p1)


def fe(rho, phi_w=jnp.pi / 4.0):
    u = jnp.diag(
        jnp.array(
            [jnp.exp(-1j * phi_w / 2.0), jnp.exp(1j * phi_w / 2.0)],
            dtype=jnp.complex128,
        )
    )
    return u @ rho @ jnp.conj(u.T)


def n01_gap():
    psi = psi_l(0.3, 0.7, 0.4)
    rho = density(psi)
    path_a = ti(fe(rho))
    path_b = fe(ti(rho))
    return float(jnp.linalg.norm(path_a - path_b))


def main():
    phi, chi, eta, phis, chis, etas = grid(8)
    chirality_l_vmap = jax.vmap(lambda a, b, c: chirality(psi_l(a, b, c)))
    chirality_r_vmap = jax.vmap(lambda a, b, c: chirality(psi_r(a, b, c)))

    chirality_l = chirality_l_vmap(phi, chi, eta)
    chirality_r = chirality_r_vmap(phi, chi, eta)
    analytic_l = jnp.cos(2.0 * eta)
    analytic_r_requested = -jnp.cos(2.0 * eta)

    chirality_l_max_err = float(jnp.max(jnp.abs(chirality_l - analytic_l)))
    chirality_r_max_err = float(jnp.max(jnp.abs(chirality_r - analytic_r_requested)))
    delta_jax = n01_gap()

    julia_result = json.loads(JULIA_RESULT_PATH.read_text())
    julia_l = jnp.array(julia_result["grid_8"]["chirality_L"], dtype=jnp.float64)
    julia_r = jnp.array(julia_result["grid_8"]["chirality_R"], dtype=jnp.float64)
    max_diff_l = jnp.max(jnp.abs(chirality_l - julia_l))
    max_diff_r = jnp.max(jnp.abs(chirality_r - julia_r))
    max_diff_julia_vs_jax = float(jnp.maximum(max_diff_l, max_diff_r))
    parity_pass = max_diff_julia_vs_jax < 1e-10

    result = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "jax_ran": True,
        "claim_ceiling": CLAIM_CEILING,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "chirality_L_max_err": chirality_l_max_err,
        "chirality_R_max_err": chirality_r_max_err,
        "n01_delta_jax": delta_jax,
        "parity_pass": parity_pass,
        "max_diff_julia_vs_jax": max_diff_julia_vs_jax,
        "all_requested_checks_pass": bool(
            chirality_l_max_err < 1e-12
            and chirality_r_max_err < 1e-12
            and delta_jax > 1e-6
            and parity_pass
        ),
        "grid_8": {
            "shape": [8, 8, 8],
            "phi": [float(x) for x in phis.tolist()],
            "chi": [float(x) for x in chis.tolist()],
            "eta": [float(x) for x in etas.tolist()],
            "chirality_L": [float(x) for x in chirality_l.tolist()],
            "chirality_R": [float(x) for x in chirality_r.tolist()],
            "analytic_L": [float(x) for x in analytic_l.tolist()],
            "analytic_R_requested": [float(x) for x in analytic_r_requested.tolist()],
        },
        "notes": {
            "R_sheet_raw_convention": "psi_R=conj(psi_L) with shared gamma5=diag(+1,-1) gives raw +cos(2*eta), not requested -cos(2*eta).",
            "N01_gap": "Ti z-dephase and Fe z-rotation commute under the stated channels, so the literal order gap is near zero.",
        },
    }
    OUT_PATH.write_text(json.dumps(result, indent=2) + "\n")
    print("JAX_DONE")


if __name__ == "__main__":
    main()
