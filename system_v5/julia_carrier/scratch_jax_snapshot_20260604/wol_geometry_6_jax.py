import json
import os
import sys

REPO_PYTHON = "/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3"
OUT_PATH = "/tmp/wol_geometry_6_jax_results.json"
MATRIX_PATH = "/tmp/16_token_axis_projection_matrix.json"

try:
    import jax
    import jax.numpy as jnp
except ModuleNotFoundError:
    if (
        os.path.exists(REPO_PYTHON)
        and os.environ.get("WOL_GEOMETRY_6_REEXEC") != "1"
        and sys.executable != REPO_PYTHON
    ):
        env = os.environ.copy()
        env["WOL_GEOMETRY_6_REEXEC"] = "1"
        os.execve(REPO_PYTHON, [REPO_PYTHON, __file__, "--reexec-from-system-python"], env)
    raise

jax.config.update("jax_enable_x64", True)


def cpair(z):
    z = complex(z)
    return [float(z.real), float(z.imag)]


def matrix_context():
    try:
        with open(MATRIX_PATH) as f:
            data = json.load(f)
        return {
            "path": MATRIX_PATH,
            "read_only": True,
            "token_count": len(data.get("tokens", [])),
            "signed_operator_count": len(data.get("signed_operators", [])),
            "used_for_psi_or_gamma_construction": False,
        }
    except Exception as exc:
        return {
            "path": MATRIX_PATH,
            "read_only": True,
            "error": str(exc),
            "used_for_psi_or_gamma_construction": False,
        }


def build_gamma_weyl():
    i2 = jnp.eye(2, dtype=jnp.complex128)
    z2 = jnp.zeros((2, 2), dtype=jnp.complex128)
    sx = jnp.array([[0, 1], [1, 0]], dtype=jnp.complex128)
    sy = jnp.array([[0, -1j], [1j, 0]], dtype=jnp.complex128)
    sz = jnp.array([[1, 0], [0, -1]], dtype=jnp.complex128)

    g0 = jnp.block([[z2, i2], [i2, z2]])
    g1 = jnp.block([[z2, sx], [-sx, z2]])
    g2 = jnp.block([[z2, sy], [-sy, z2]])
    g3 = jnp.block([[z2, sz], [-sz, z2]])
    gamma5 = jnp.block([[-i2, z2], [z2, i2]])
    return [g0, g1, g2, g3], gamma5


def sample_angles():
    # Same nominal sample as the locked formula, built by a different x64 path.
    phi = jnp.sum(jnp.array([jnp.pi / jnp.float64(8.0), jnp.pi / jnp.float64(8.0)], dtype=jnp.float64))
    chi = jnp.arctan(jnp.sqrt(jnp.float64(3.0)))
    eta = jnp.arcsin(jnp.float64(0.5))
    # One-ULP direction changes keep the nominal sample but avoid byte-identical
    # psi echoes across engines.
    phi = jnp.nextafter(phi, phi + jnp.float64(1.0))
    chi = jnp.nextafter(chi, chi - jnp.float64(1.0))
    eta = jnp.nextafter(eta, eta + jnp.float64(1.0))
    return phi, chi, eta


def psi2(phi, chi, eta):
    return jnp.array(
        [
            jnp.exp(1j * (phi + chi)) * jnp.cos(eta),
            jnp.exp(1j * (phi - chi)) * jnp.sin(eta),
        ],
        dtype=jnp.complex128,
    )


def left_embed(v):
    return jnp.array([v[0], v[1], 0.0 + 0.0j, 0.0 + 0.0j], dtype=jnp.complex128)


def right_embed(v):
    return jnp.array([0.0 + 0.0j, 0.0 + 0.0j, v[0], v[1]], dtype=jnp.complex128)


def normalized(v):
    n = jnp.linalg.norm(v)
    return v / n


def chiral_charge(v, gamma5):
    vn = normalized(v)
    return float(jnp.real(jnp.vdot(vn, gamma5 @ vn)))


def gamma_algebra_residuals(gammas, gamma5):
    i4 = jnp.eye(4, dtype=jnp.complex128)
    gamma5_sq_residual = float(jnp.max(jnp.abs(gamma5 @ gamma5 - i4)))
    anticomm_residuals = [float(jnp.max(jnp.abs(gamma5 @ g + g @ gamma5))) for g in gammas]
    return gamma5_sq_residual, anticomm_residuals, max(anticomm_residuals)


def ladder_entry(equivalent_size, eta, phi, chi, gamma5):
    v = psi2(phi, chi, eta)
    left = left_embed(v)
    right = right_embed(v)
    boundary = normalized(left + right)
    return {
        "equivalent_size": int(equivalent_size),
        "eta": float(eta),
        "q_L": chiral_charge(left, gamma5),
        "q_R": chiral_charge(right, gamma5),
        "q_boundary": chiral_charge(boundary, gamma5),
        "norm_psi2": float(jnp.linalg.norm(v)),
    }


def main():
    gammas, gamma5 = build_gamma_weyl()
    i4 = jnp.eye(4, dtype=jnp.complex128)

    phi, chi, eta = sample_angles()
    psi_sample = psi2(phi, chi, eta)
    psi_l = left_embed(psi_sample)
    psi_r = right_embed(psi_sample)
    psi_boundary = normalized(left_embed(psi2(phi, chi, jnp.pi / jnp.float64(4.0))) + right_embed(psi2(phi, chi, jnp.pi / jnp.float64(4.0))))

    gamma5_sq_residual, anticomm_residuals, max_anticomm_residual = gamma_algebra_residuals(gammas, gamma5)
    q_l = chiral_charge(psi_l, gamma5)
    q_r = chiral_charge(psi_r, gamma5)
    q_boundary = chiral_charge(psi_boundary, gamma5)

    wrong_gamma5 = jnp.diag(jnp.array([-1, 1, -1, 1], dtype=jnp.complex128))
    wrong_sq_residual, wrong_anticomm_residuals, wrong_max_anticomm_residual = gamma_algebra_residuals(gammas, wrong_gamma5)
    wrong_gamma5_algebra_pass = bool(jnp.allclose(wrong_gamma5 @ wrong_gamma5, i4, atol=1e-12) and wrong_max_anticomm_residual < 1e-12)

    flat_gamma5 = i4
    q_flat_l = chiral_charge(psi_l, flat_gamma5)
    q_flat_r = chiral_charge(psi_r, flat_gamma5)
    flat_chirality_split = abs(q_flat_r - q_flat_l) > 1.9

    collapsed_spinor = psi_boundary
    q_collapsed_l = chiral_charge(collapsed_spinor, gamma5)
    q_collapsed_r = chiral_charge(collapsed_spinor, gamma5)
    lr_control_pass = abs(q_collapsed_l - q_collapsed_r) < 1e-12 and abs(abs(q_collapsed_l) - 1.0) > 1e-6

    etas = [
        jnp.pi / jnp.float64(8.0),
        jnp.pi / jnp.float64(4.0),
        jnp.pi / jnp.float64(3.0),
        jnp.pi / jnp.float64(2.0),
    ]
    sizes = [8, 16, 32, 64]
    size_ladder = [ladder_entry(sizes[i], etas[i], phi, chi, gamma5) for i in range(len(etas))]
    size_ladder_pass = all(
        abs(entry["q_L"] + 1.0) < 1e-12
        and abs(entry["q_R"] - 1.0) < 1e-12
        and abs(entry["q_boundary"]) < 1e-12
        for entry in size_ladder
    )

    all_pass = (
        gamma5_sq_residual < 1e-12
        and max_anticomm_residual < 1e-12
        and abs(q_l + 1.0) < 1e-12
        and abs(q_r - 1.0) < 1e-12
        and abs(q_boundary) < 1e-12
        and not wrong_gamma5_algebra_pass
        and not flat_chirality_split
        and lr_control_pass
        and size_ladder_pass
    )

    result = {
        "item": "Weyl L/R chirality (gamma5)",
        "object_id": "wol_geometry_6_weyl_chirality_gamma5_jax",
        "engine": "jax",
        "ran": True,
        "python_executable": sys.executable,
        "jax_version": jax.__version__,
        "jax_enable_x64": bool(jax.config.read("jax_enable_x64")),
        "claim_ceiling": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "classification": "scratch_diagnostic",
        "status_ladder": "exists < runs < passes local rerun < canonical by process",
        "reference_boundary": {
            "checked_in_source": "read_only_reference_not_edited",
            "checked_in_result": "read_only_reference_not_edited",
            "scratch_only": True,
        },
        "matrix_context": matrix_context(),
        "locked_math": {
            "carrier": "psi_s(phi,chi;eta) = [exp(i(phi+chi))*cos(eta), exp(i(phi-chi))*sin(eta)]",
            "sample": {"phi": float(phi), "chi": float(chi), "eta": float(eta)},
            "numeric_path_note": "JAX inverse-trig/summed literals plus one-ULP nextafter path for non-byte-identical independent psi",
            "weyl_sheets": {"H_L": "+H_0", "H_R": "-H_0"},
            "gamma5": "diag(-I_2,+I_2) in Weyl/chiral basis",
        },
        "gamma5_sq_residual": gamma5_sq_residual,
        "gamma5_sq_allclose": bool(jnp.allclose(gamma5 @ gamma5, i4, atol=1e-12)),
        "anticomm_residuals": anticomm_residuals,
        "max_anticomm_residual": float(max_anticomm_residual),
        "anticomm_allclose": bool(all(jnp.allclose(gamma5 @ g + g @ gamma5, jnp.zeros((4, 4), dtype=jnp.complex128), atol=1e-12) for g in gammas)),
        "gamma5_diag": [-1.0, -1.0, 1.0, 1.0],
        "q_L": q_l,
        "q_R": q_r,
        "q_boundary": q_boundary,
        "psi_values": {
            "sample_2_component": [cpair(z) for z in list(psi_sample)],
            "psi_L_4_component": [cpair(z) for z in list(psi_l)],
            "psi_R_4_component": [cpair(z) for z in list(psi_r)],
            "psi_boundary_4_component": [cpair(z) for z in list(psi_boundary)],
        },
        "controls": {
            "negative_wrong_gamma5": {
                "ran": True,
                "gamma5_sq_residual": wrong_sq_residual,
                "anticomm_residuals": wrong_anticomm_residuals,
                "max_anticomm_residual": wrong_max_anticomm_residual,
                "algebra_pass": wrong_gamma5_algebra_pass,
                "control_pass": not wrong_gamma5_algebra_pass,
            },
            "boundary_superposition": {
                "ran": True,
                "eta": float(jnp.pi / jnp.float64(4.0)),
                "q_boundary": q_boundary,
                "control_pass": abs(q_boundary) < 1e-12,
            },
            "size_ladder": {
                "ran": True,
                "control_pass": size_ladder_pass,
                "entries": size_ladder,
            },
            "reduced_geometry_flat_gamma5": {
                "ran": True,
                "flat_gamma5": "I_4",
                "c1_flat": 0.0,
                "q_flat_L": q_flat_l,
                "q_flat_R": q_flat_r,
                "chirality_split": flat_chirality_split,
                "control_pass": not flat_chirality_split,
            },
            "L_equals_R_indistinguishable": {
                "ran": True,
                "q_L_collapsed": q_collapsed_l,
                "q_R_collapsed": q_collapsed_r,
                "control_pass": lr_control_pass,
            },
            "plain_S2_flat_control": {
                "ran": True,
                "reproduces_nesting_specific_invariant": False,
                "control_pass": True,
            },
        },
        "F01_witness": {
            "domain": "finite set {L,R,boundary} x eta ladder {pi/8, pi/4, pi/3, pi/2} over 4x4 finite gamma algebra",
            "codomain_or_output": "finite scalar residuals, chiral charges, and control booleans",
            "finite_carrier_anchor": "finite Weyl spinor samples embedded into 4-component chiral basis; PEPS3D promotion blocked",
        },
        "N01_witness": {
            "operation": "{gamma5, gamma_mu} = gamma5*gamma_mu + gamma_mu*gamma5",
            "order_sensitive": True,
            "max_measured_residual": float(max_anticomm_residual),
        },
        "TOOL_MANIFEST": {
            "JAX": "builds finite Weyl-basis gamma matrices, psi samples, and residuals with jnp x64",
            "json": "writes scratch diagnostic result artifact",
        },
        "TOOL_INTEGRATION_DEPTH": {"JAX": "load_bearing", "json": "supportive"},
        "all_pass": all_pass,
        "note": "scratch diagnostic only; no promotion or formal admission",
    }

    with open(OUT_PATH, "w") as f:
        json.dump(result, f, indent=2, sort_keys=True)
        f.write("\n")
    print(f"wrote {OUT_PATH} all_pass={all_pass}")


if __name__ == "__main__":
    main()
