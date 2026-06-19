#!/usr/bin/env python3
# object_id: clifford_algebra_ladder
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false
# claim_ceiling: Finite Clifford/quaternion carrier diagnostic only. No basin,
# admission, engine, Axis0, bridge, gravity, or manifold-closure claim.

import jax

jax.config.update("jax_enable_x64", True)

import datetime as _dt
import json
import sys
from pathlib import Path
from typing import Any

import jax.numpy as jnp


OBJECT_ID = "clifford_algebra_ladder"
BASE_DIR = Path("/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier")
RESULT_PATH = BASE_DIR / "clifford_algebra_ladder_jax_results.json"
JULIA_REFERENCE_PATH = BASE_DIR / "clifford_algebra_ladder_julia_results.json"
TOL = 1.0e-9
STRICT_STOP_TOL = 1.0e-6


def py_float(x: Any) -> float:
    return float(jax.device_get(x))


def setprod(table: jax.Array, a: int, b: int, c: int, s: float) -> jax.Array:
    return table.at[c, a, b].set(s)


def add_identity(table: jax.Array, dim: int) -> jax.Array:
    for a in range(dim):
        table = setprod(table, 0, a, a, 1.0)
        table = setprod(table, a, 0, a, 1.0)
    return table


def complex_table() -> jax.Array:
    table = jnp.zeros((2, 2, 2), dtype=jnp.float64)
    table = add_identity(table, 2)
    return setprod(table, 1, 1, 0, -1.0)


def quaternion_table() -> jax.Array:
    table = jnp.zeros((4, 4, 4), dtype=jnp.float64)
    table = add_identity(table, 4)
    for a in range(1, 4):
        table = setprod(table, a, a, 0, -1.0)
    for i, j, k in [(1, 2, 3)]:
        for a, b, c, s in [
            (i, j, k, 1.0),
            (j, k, i, 1.0),
            (k, i, j, 1.0),
            (j, i, k, -1.0),
            (k, j, i, -1.0),
            (i, k, j, -1.0),
        ]:
            table = setprod(table, a, b, c, s)
    return table


def blade_product(mask_a: int, mask_b: int, signature: list[int]) -> tuple[float, int]:
    sign = 1.0
    for i in range(len(signature)):
        if (mask_a >> i) & 1:
            for j in range(i):
                if (mask_b >> j) & 1:
                    sign *= -1.0
            if (mask_b >> i) & 1:
                sign *= float(signature[i])
    return sign, mask_a ^ mask_b


def clifford_table(signature: list[int]) -> jax.Array:
    dim = 2 ** len(signature)
    table = jnp.zeros((dim, dim, dim), dtype=jnp.float64)
    for a in range(dim):
        for b in range(dim):
            sign, c = blade_product(a, b, signature)
            table = setprod(table, a, b, c, sign)
    return table


def basis(dim: int, idx: int, scale: float = 1.0) -> jax.Array:
    return scale * jnp.eye(dim, dtype=jnp.float64)[idx]


def mv_mul(table: jax.Array, x: jax.Array, y: jax.Array) -> jax.Array:
    return jnp.einsum("cab,a,b->c", table, x, y)


def table_residual(table: jax.Array, subbasis: list[jax.Array], target: jax.Array) -> float:
    max_resid = 0.0
    dim = table.shape[0]
    for a in range(len(subbasis)):
        for b in range(len(subbasis)):
            product = mv_mul(table, subbasis[a], subbasis[b])
            expected = jnp.zeros((dim,), dtype=jnp.float64)
            for c in range(len(subbasis)):
                expected = expected + target[c, a, b] * subbasis[c]
            max_resid = max(max_resid, py_float(jnp.linalg.norm(product - expected)))
    return max_resid


def even_dim(signature: list[int]) -> int:
    return sum(1 for mask in range(2 ** len(signature)) if mask.bit_count() % 2 == 0)


def gamma_matrices_cl30() -> list[jax.Array]:
    sx = jnp.asarray([[0.0, 1.0], [1.0, 0.0]], dtype=jnp.complex128)
    sy = jnp.asarray([[0.0, -1.0j], [1.0j, 0.0]], dtype=jnp.complex128)
    sz = jnp.asarray([[1.0, 0.0], [0.0, -1.0]], dtype=jnp.complex128)
    return [sx, sy, sz]


def gamma_relation_residual(gammas: list[jax.Array]) -> float:
    ident = jnp.eye(2, dtype=jnp.complex128)
    zero = jnp.zeros((2, 2), dtype=jnp.complex128)
    max_resid = 0.0
    for i in range(3):
        for j in range(3):
            target = 2.0 * ident if i == j else zero
            residual = jnp.linalg.norm(gammas[i] @ gammas[j] + gammas[j] @ gammas[i] - target, ord=2)
            max_resid = max(max_resid, py_float(residual))
    return max_resid


def parity_against_peer(result: dict[str, Any], peer_path: Path) -> dict[str, Any]:
    if not peer_path.exists():
        return {
            "peer_result_path": str(peer_path),
            "status": "missing_julia_reference",
            "shared_scalar_rows": [],
            "max_diff_key": None,
            "parity_max_diff": None,
            "within_1e_9": False,
            "strict_divergence_gt_1e_6": [{"missing": str(peer_path)}],
            "boolean_mismatches": [],
            "missing_keys": [],
            "stop_condition_fired": True,
        }
    peer = json.loads(peer_path.read_text(encoding="utf-8"))
    rows: list[dict[str, Any]] = []
    max_diff = 0.0
    max_diff_key = None
    strict: list[dict[str, Any]] = []
    missing: list[str] = []
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
    mismatches: list[dict[str, Any]] = []
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


def build_result() -> dict[str, Any]:
    table_cl01 = clifford_table([-1])
    table_cl02 = clifford_table([-1, -1])
    table_cl20 = clifford_table([1, 1])
    table_cl30 = clifford_table([1, 1, 1])

    cl01_basis = [basis(2, 0), basis(2, 1)]
    cl02_basis = [basis(4, 0), basis(4, 1), basis(4, 2), basis(4, 3)]
    cl20_basis = [basis(4, 0), basis(4, 1), basis(4, 2), basis(4, 3)]
    cl30_even_oriented = [basis(8, 0), basis(8, 0b011, -1.0), basis(8, 0b110, -1.0), basis(8, 0b101)]
    cl30_even_raw_named = [basis(8, 0), basis(8, 0b011), basis(8, 0b110), basis(8, 0b101, -1.0)]

    c_table = complex_table()
    h_table = quaternion_table()

    cl01_complex_resid = table_residual(table_cl01, cl01_basis, c_table)
    cl02_h_resid = table_residual(table_cl02, cl02_basis, h_table)
    cl20_wrong_h_resid = table_residual(table_cl20, cl20_basis, h_table)
    cl30_even_h_resid = table_residual(table_cl30, cl30_even_oriented, h_table)
    cl30_even_raw_h_resid = table_residual(table_cl30, cl30_even_raw_named, h_table)
    gamma_resid = gamma_relation_residual(gamma_matrices_cl30())

    dimension_rows = {
        "Cl(0,1)": {"n": 1, "dim": table_cl01.shape[0], "expected": 2},
        "Cl(0,2)": {"n": 2, "dim": table_cl02.shape[0], "expected": 4},
        "Cl(3,0)": {"n": 3, "dim": table_cl30.shape[0], "expected": 8, "even_dim": even_dim([1, 1, 1]), "expected_even_dim": 4},
    }
    dim_max_resid = max(abs(float(row["dim"] - row["expected"])) for row in dimension_rows.values())
    even_dim_resid = abs(float(dimension_rows["Cl(3,0)"]["even_dim"] - dimension_rows["Cl(3,0)"]["expected_even_dim"]))
    verdicts = {
        "cl01_is_C": cl01_complex_resid < TOL and table_cl01.shape[0] == 2,
        "cl02_is_H": cl02_h_resid < TOL and table_cl02.shape[0] == 4,
        "cl30_even_is_H": cl30_even_h_resid < TOL and even_dim([1, 1, 1]) == 4,
        "clifford_even_3_is_H": cl30_even_h_resid < TOL,
        "gamma_relations_hold": gamma_resid < TOL,
        "dimension_pattern_holds": dim_max_resid < TOL and even_dim_resid < TOL,
    }
    controls = {
        "wrong_signature_cl20_not_H": cl20_wrong_h_resid > 1.0,
        "raw_cl30_bivector_orientation_not_standard_H": cl30_even_raw_h_resid > 1.0,
        "oriented_cl30_bivectors_match_H": cl30_even_h_resid < TOL,
    }
    controls["control_miswired"] = not (
        controls["wrong_signature_cl20_not_H"]
        and controls["raw_cl30_bivector_orientation_not_standard_H"]
        and controls["oriented_cl30_bivectors_match_H"]
    )
    all_verdicts = all(bool(v) for v in verdicts.values())
    shared_scalars = {
        "cl01.dim": table_cl01.shape[0],
        "cl02.dim": table_cl02.shape[0],
        "cl30.dim": table_cl30.shape[0],
        "cl30.even_dim": even_dim([1, 1, 1]),
        "cl01_complex_table_residual": cl01_complex_resid,
        "cl02_quaternion_table_residual": cl02_h_resid,
        "cl30_even_quaternion_table_residual": cl30_even_h_resid,
        "cl30_even_raw_quaternion_table_residual": cl30_even_raw_h_resid,
        "wrong_signature_cl20_quaternion_table_residual": cl20_wrong_h_resid,
        "gamma_cl30_anticommutator_max_residual": gamma_resid,
        "dimension_max_residual": dim_max_resid,
        "even_dimension_residual": even_dim_resid,
    }
    shared_booleans: dict[str, bool] = {}
    for key, value in verdicts.items():
        shared_booleans[f"verdict.{key}"] = bool(value)
    for key, value in controls.items():
        shared_booleans[f"control.{key}"] = bool(value)

    result: dict[str, Any] = {
        "object_id": OBJECT_ID,
        "backend": "jax_full_sim",
        "generated_at": _dt.datetime.now(_dt.UTC).isoformat(),
        "source_path": str(Path(__file__).resolve()),
        "result_path": str(RESULT_PATH),
        "peer_result_path": str(JULIA_REFERENCE_PATH),
        "jax_enable_x64": bool(jax.config.read("jax_enable_x64")),
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "claim_ceiling": "Finite Clifford/quaternion carrier diagnostic only; no basin, admission, engine, Axis0, bridge, gravity, or manifold-closure claim.",
        "sim_execution_kind": "nonclassical",
        "sim_class": "carrier_probe",
        "tol": TOL,
        "strict_stop_tol": STRICT_STOP_TOL,
        "question": "Do the low real Clifford rungs compute C/H identities, and does Cl^0(3,0) compute the quaternion spinor-neighborhood carrier?",
        "basis_convention": {
            "Cl(p,q)": "p positive generators square +1, q negative generators square -1",
            "Cl(0,2)_H_basis": "1,e1,e2,e12 maps to 1,i,j,k",
            "Cl(3,0)_even_H_basis": "1,-e12,-e23,-e31 maps to 1,i,j,k; raw e12,e23,e31 has the opposite handed product and is recorded as a control",
        },
        "dimension_rows": dimension_rows,
        "gamma_representation": "Pauli matrices sigma_x, sigma_y, sigma_z over C^2; {gamma_i,gamma_j}=2 delta_ij I",
        "tool_manifest": {
            "JAX": "load_bearing explicit finite Clifford blade multiplication and table checks",
            "jax.numpy": "load_bearing x64 array algebra, norms, and gamma relation residuals",
            "JSON": "supportive result serialization",
        },
        "tool_integration_depth": {
            "JAX": "load_bearing",
            "jax.numpy": "load_bearing",
            "JSON": "supportive",
        },
        "verdicts": verdicts,
        "controls": controls,
        "numbers": shared_scalars,
        "shared_scalars": shared_scalars,
        "shared_booleans": shared_booleans,
        "plain_sentence": "The computed low Clifford rungs match C and H, and the oriented even bivectors of Cl(3,0) match the quaternion table; this is a scratch carrier diagnostic only.",
    }
    result["parity"] = parity_against_peer(result, JULIA_REFERENCE_PATH)
    result["stop_condition_fired"] = controls["control_miswired"] or not all_verdicts or bool(result["parity"]["stop_condition_fired"])
    return result


def print_summary(result: dict[str, Any]) -> None:
    s = result["shared_scalars"]
    print("clifford_algebra_ladder - JAX full sim")
    print(
        f"classification: {result['classification']} | promotion_allowed: {str(result['promotion_allowed']).lower()} | "
        f"formal_admission_allowed: {str(result['formal_admission_allowed']).lower()} | jax_enable_x64: {str(result['jax_enable_x64']).lower()}"
    )
    print(f"cl01_is_C={str(result['verdicts']['cl01_is_C']).lower()} residual={s['cl01_complex_table_residual']} dim={s['cl01.dim']}")
    print(f"cl02_is_H={str(result['verdicts']['cl02_is_H']).lower()} residual={s['cl02_quaternion_table_residual']} dim={s['cl02.dim']}")
    print(
        f"clifford_even_3_is_H={str(result['verdicts']['clifford_even_3_is_H']).lower()} "
        f"residual={s['cl30_even_quaternion_table_residual']} raw_orientation_residual={s['cl30_even_raw_quaternion_table_residual']}"
    )
    print(f"gamma_relations_hold={str(result['verdicts']['gamma_relations_hold']).lower()} gamma_residual={s['gamma_cl30_anticommutator_max_residual']}")
    print(
        f"wrong_signature_control_ok={str(result['controls']['wrong_signature_cl20_not_H']).lower()} "
        f"wrong_signature_residual={s['wrong_signature_cl20_quaternion_table_residual']}"
    )
    parity = result["parity"]
    print(f"parity_max_diff={parity['parity_max_diff']} within_1e-9={str(parity['within_1e_9']).lower()} max_diff_key={parity.get('max_diff_key')}")
    if parity["strict_divergence_gt_1e_6"] or parity["boolean_mismatches"] or parity["missing_keys"]:
        print("STOP: JAX and Julia disagree beyond the strict parity stop condition:")
        print(json.dumps({
            "strict_divergence_gt_1e_6": parity["strict_divergence_gt_1e_6"],
            "boolean_mismatches": parity["boolean_mismatches"],
            "missing_keys": parity["missing_keys"],
        }, indent=2, sort_keys=True))
    if result["controls"]["control_miswired"]:
        print("STOP: clifford_algebra_ladder control failed.")
    print(result["plain_sentence"])
    print(f"wrote: {result['result_path']}")
    if not result["stop_condition_fired"]:
        print("CODEX2_B1_DONE")


def main() -> int:
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print_summary(result)
    return 2 if result["stop_condition_fired"] else 0


if __name__ == "__main__":
    sys.exit(main())
