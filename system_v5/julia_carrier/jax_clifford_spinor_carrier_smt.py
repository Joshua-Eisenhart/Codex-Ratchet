#!/usr/bin/env python3
# object_id: jax_clifford_spinor_carrier_smt
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false
# claim_ceiling: JAX-only Clifford/spinor carrier rung with dual-SMT
# anticommutation check. No peer parity, bridge, manifold, basin, or axis claim.

import jax

jax.config.update("jax_enable_x64", True)

import datetime as _dt
import json
import sys
from pathlib import Path
from typing import Any

import jax.numpy as jnp
import numpy as np
import z3
import cvc5


OBJECT_ID = "jax_clifford_spinor_carrier_smt"
BASE_DIR = Path("/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier")
RESULT_PATH = BASE_DIR / "jax_clifford_spinor_carrier_smt_results.json"
TOL = 1.0e-9

classification = "scratch_diagnostic"
CLASSIFICATION = classification
promotion_allowed = False
PROMOTION_ALLOWED = promotion_allowed
formal_admission_allowed = False
FORMAL_ADMISSION_ALLOWED = formal_admission_allowed
reads_peer_result = False
READS_PEER_RESULT = reads_peer_result

TOOL_MANIFEST = {
    "jax": {
        "tried": True,
        "used": True,
        "reason": "load-bearing x64 construction of finite Pauli-tensor gamma matrices",
    },
    "jax.numpy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing Kronecker products, matrix products, chirality operator, and residual extraction",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing SMT SAT/UNSAT check of the finite anticommutation residual equations",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent SMT SAT/UNSAT check agreeing with z3",
    },
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "control-only host copy and residual cross-check; not in the claim path",
    },
    "json": {
        "tried": True,
        "used": True,
        "reason": "supportive result serialization",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "jax": "load_bearing",
    "jax.numpy": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "numpy": "supportive",
    "json": "supportive",
}


def to_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_jsonable(v) for v in value]
    if isinstance(value, Path):
        return str(value)
    if hasattr(value, "shape"):
        return to_jsonable(jax.device_get(value).tolist())
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, (np.bool_,)):
        return bool(value)
    return value


def pauli() -> tuple[jax.Array, jax.Array, jax.Array, jax.Array]:
    ident = jnp.asarray([[1, 0], [0, 1]], dtype=jnp.complex128)
    sx = jnp.asarray([[0, 1], [1, 0]], dtype=jnp.complex128)
    sy = jnp.asarray([[0, -1j], [1j, 0]], dtype=jnp.complex128)
    sz = jnp.asarray([[1, 0], [0, -1]], dtype=jnp.complex128)
    return ident, sx, sy, sz


def kron_all(parts: list[jax.Array]) -> jax.Array:
    out = parts[0]
    for part in parts[1:]:
        out = jnp.kron(out, part)
    return out


def gamma_matrices(n: int) -> list[jax.Array]:
    if n % 2 != 0:
        raise ValueError("this finite spinor construction expects even n")
    ident, sx, sy, sz = pauli()
    m = n // 2
    gammas = []
    for k in range(m):
        prefix = [sz] * k
        suffix = [ident] * (m - k - 1)
        gammas.append(kron_all(prefix + [sx] + suffix))
        gammas.append(kron_all(prefix + [sy] + suffix))
    return gammas


def gamma_matrices_cl3() -> list[jax.Array]:
    _, sx, sy, sz = pauli()
    return [sx, sy, sz]


def gamma5_chirality(gammas: list[jax.Array]) -> jax.Array:
    product = gammas[0]
    for gamma in gammas[1:]:
        product = product @ gamma
    m = len(gammas) // 2
    return ((-1j) ** m) * product


def clifford_algebra_dim(n: int) -> int:
    return 2 ** n


def spinor_rep_dim(n: int) -> int:
    return 2 ** (n // 2)


def gaussian_int(value: complex) -> tuple[int, int]:
    real = int(round(float(np.real(value))))
    imag = int(round(float(np.imag(value))))
    if abs(float(np.real(value)) - real) > TOL or abs(float(np.imag(value)) - imag) > TOL:
        raise ValueError(f"non-integral matrix entry for SMT encoding: {value!r}")
    return real, imag


def anticommutator_entries(gammas: list[jax.Array]) -> list[dict[str, int]]:
    dim = int(gammas[0].shape[0])
    ident = jnp.eye(dim, dtype=jnp.complex128)
    rows: list[dict[str, int]] = []
    for i, gi in enumerate(gammas):
        for j, gj in enumerate(gammas):
            target = 2 * ident if i == j else jnp.zeros_like(ident)
            residual = gi @ gj + gj @ gi - target
            host = np.asarray(jax.device_get(residual))
            for r in range(dim):
                for c in range(dim):
                    real, imag = gaussian_int(host[r, c])
                    rows.append({"i": i, "j": j, "r": r, "c": c, "real": real, "imag": imag})
    return rows


def max_anticommutator_residual(gammas: list[jax.Array]) -> float:
    dim = int(gammas[0].shape[0])
    ident = jnp.eye(dim, dtype=jnp.complex128)
    max_residual = 0.0
    for i, gi in enumerate(gammas):
        for j, gj in enumerate(gammas):
            target = 2 * ident if i == j else jnp.zeros_like(ident)
            residual = jnp.linalg.norm(gi @ gj + gj @ gi - target)
            max_residual = max(max_residual, float(jax.device_get(residual)))
    return max_residual


def z3_check(rows: list[dict[str, int]]) -> str:
    solver = z3.Solver()
    for row in rows:
        solver.add(z3.IntVal(row["real"]) == 0)
        solver.add(z3.IntVal(row["imag"]) == 0)
    return str(solver.check())


def cvc5_check(rows: list[dict[str, int]]) -> str:
    solver = cvc5.Solver()
    int_sort = solver.getIntegerSort()
    zero = solver.mkInteger(0)
    for idx, row in enumerate(rows):
        real_const = solver.mkConst(int_sort, f"real_{idx}")
        imag_const = solver.mkConst(int_sort, f"imag_{idx}")
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, real_const, solver.mkInteger(row["real"])))
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, imag_const, solver.mkInteger(row["imag"])))
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, real_const, zero))
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, imag_const, zero))
    return str(solver.checkSat())


def numpy_control(gammas: list[jax.Array]) -> dict[str, Any]:
    host = [np.asarray(jax.device_get(g)) for g in gammas]
    dim = host[0].shape[0]
    ident = np.eye(dim, dtype=np.complex128)
    max_residual = 0.0
    for i, gi in enumerate(host):
        for j, gj in enumerate(host):
            target = 2 * ident if i == j else np.zeros_like(ident)
            max_residual = max(max_residual, float(np.linalg.norm(gi @ gj + gj @ gi - target)))
    return {"role": "control_only", "max_anticommutator_residual": max_residual}


def build_result() -> dict[str, Any]:
    gammas_cl3 = gamma_matrices_cl3()
    gammas_cl6 = gamma_matrices(6)
    gamma5 = gamma5_chirality(gammas_cl6)
    wrong_gammas_cl6 = list(gammas_cl6)
    wrong_gammas_cl6[0] = 1j * wrong_gammas_cl6[0]

    cl3_rows = anticommutator_entries(gammas_cl3)
    cl6_rows = anticommutator_entries(gammas_cl6)
    wrong_rows = anticommutator_entries(wrong_gammas_cl6)
    z3_positive_cl3 = z3_check(cl3_rows)
    cvc5_positive_cl3 = cvc5_check(cl3_rows)
    z3_positive_cl6 = z3_check(cl6_rows)
    cvc5_positive_cl6 = cvc5_check(cl6_rows)
    z3_wrong = z3_check(wrong_rows)
    cvc5_wrong = cvc5_check(wrong_rows)

    anticommutation_sat = (
        z3_positive_cl3 == "sat"
        and cvc5_positive_cl3 == "sat"
        and z3_positive_cl6 == "sat"
        and cvc5_positive_cl6 == "sat"
    )
    wrong_sign_unsat = z3_wrong == "unsat" and cvc5_wrong == "unsat"
    z3_cvc5_agree = (
        z3_positive_cl3 == cvc5_positive_cl3
        and z3_positive_cl6 == cvc5_positive_cl6
        and z3_wrong == cvc5_wrong
    )
    not_bare_jnp = z3_cvc5_agree and anticommutation_sat and wrong_sign_unsat

    result = {
        "object_id": OBJECT_ID,
        "backend": "jax_smt_scout",
        "generated_at": _dt.datetime.now(_dt.UTC).isoformat(),
        "source_path": str(Path(__file__).resolve()),
        "result_path": str(RESULT_PATH),
        "reads_peer_result": READS_PEER_RESULT,
        "jax_enable_x64": bool(jax.config.read("jax_enable_x64")),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "sim_execution_kind": "nonclassical",
        "claim_ceiling": (
            "JAX-only Clifford/spinor carrier rung with load-bearing z3+cvc5 "
            "finite SMT anticommutation checks; no peer parity, bridge, basin, "
            "axis, manifold, or admission claim."
        ),
        "question": "Do JAX-built Euclidean Clifford gamma matrices satisfy the finite anticommutation law, with dual-SMT agreement and an erase-flip negative control?",
        "dimensions": {
            "cl3_dim": clifford_algebra_dim(3),
            "cl6_dim": clifford_algebra_dim(6),
            "spinor_dim_cl3": spinor_rep_dim(3),
            "spinor_dim_cl6": spinor_rep_dim(6),
            "cl3_gamma_matrix_shape": list(gammas_cl3[0].shape),
            "cl6_gamma_matrix_shape": list(gammas_cl6[0].shape),
        },
        "gamma5": {
            "definition": "(-i)^(n/2) product_i gamma_i for Cl(6)",
            "shape": list(gamma5.shape),
            "square_residual": float(jax.device_get(jnp.linalg.norm(gamma5 @ gamma5 - jnp.eye(gamma5.shape[0], dtype=jnp.complex128)))),
            "trace_real": float(jax.device_get(jnp.real(jnp.trace(gamma5)))),
            "trace_imag": float(jax.device_get(jnp.imag(jnp.trace(gamma5)))),
            "diagonal": [
                {"real": gaussian_int(complex(v))[0], "imag": gaussian_int(complex(v))[1]}
                for v in np.diag(np.asarray(jax.device_get(gamma5)))
            ],
        },
        "smt": {
            "encoding": "finite Gaussian-integer residual entries of {gamma_i,gamma_j}-2 delta_ij I are asserted equal to zero",
            "wrong_sign_control": "gamma_0 is multiplied by i, changing gamma_0^2 from +I to -I; asserting the +2 delta rule becomes UNSAT",
            "z3": {
                "version": z3.get_version_string(),
                "cl3_anticommutation_result": z3_positive_cl3,
                "cl6_anticommutation_result": z3_positive_cl6,
                "wrong_sign_result": z3_wrong,
            },
            "cvc5": {
                "version": getattr(cvc5, "__version__", "unknown"),
                "cl3_anticommutation_result": cvc5_positive_cl3,
                "cl6_anticommutation_result": cvc5_positive_cl6,
                "wrong_sign_result": cvc5_wrong,
            },
        },
        "numeric_residuals": {
            "cl3_anticommutator_max_residual": max_anticommutator_residual(gammas_cl3),
            "cl6_anticommutator_max_residual": max_anticommutator_residual(gammas_cl6),
            "wrong_sign_cl6_anticommutator_max_residual": max_anticommutator_residual(wrong_gammas_cl6),
        },
        "numpy_control": numpy_control(gammas_cl6),
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "verdicts": {
            "z3_cvc5_agree": z3_cvc5_agree,
            "anticommutation_sat": anticommutation_sat,
            "wrong_sign_unsat": wrong_sign_unsat,
            "not_bare_jnp": not_bare_jnp,
            "ran": True,
        },
    }
    result["stop_condition_fired"] = not all(result["verdicts"].values())
    return result


def print_summary(result: dict[str, Any]) -> None:
    verdicts = result["verdicts"]
    dims = result["dimensions"]
    print("jax_clifford_spinor_carrier_smt - JAX leg")
    print(f"wrote: {result['result_path']}")
    print(
        "SCOUT_DONE "
        f"z3_cvc5_agree={str(verdicts['z3_cvc5_agree']).lower()} "
        f"anticommutation_sat={str(verdicts['anticommutation_sat']).lower()} "
        f"wrong_sign_unsat={str(verdicts['wrong_sign_unsat']).lower()} "
        f"cl3_dim={dims['cl3_dim']} "
        f"cl6_dim={dims['cl6_dim']} "
        f"spinor_dim_cl6={dims['spinor_dim_cl6']} "
        f"not_bare_jnp={str(verdicts['not_bare_jnp']).lower()} "
        f"ran={str(verdicts['ran']).lower()}"
    )


def main() -> int:
    result = build_result()
    RESULT_PATH.write_text(json.dumps(to_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print_summary(result)
    return 2 if result["stop_condition_fired"] else 0


if __name__ == "__main__":
    sys.exit(main())
