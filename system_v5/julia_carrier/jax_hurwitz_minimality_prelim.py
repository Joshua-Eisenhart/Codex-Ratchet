#!/usr/bin/env python3
import jax

jax.config.update("jax_enable_x64", True)

import datetime as _dt
import json
import sys
from pathlib import Path
from typing import Any

import jax.numpy as jnp


OBJECT_ID = "hurwitz_minimality_prelim"
BASE_DIR = Path("/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier")
RESULT_PATH = BASE_DIR / "hurwitz_minimality_prelim_jax_results.json"
JULIA_REFERENCE_PATH = BASE_DIR / "hurwitz_minimality_prelim_julia_results.json"
TOL = 1.0e-9
STRICT_STOP_TOL = 1.0e-6
NORM_PROBE_COUNT = 64
FANO = [
    (1, 2, 3),
    (1, 4, 5),
    (1, 7, 6),
    (2, 4, 6),
    (2, 5, 7),
    (3, 4, 7),
    (3, 6, 5),
]


def py_float(x: Any) -> float:
    return float(jax.device_get(x))


def py_bool(x: Any) -> bool:
    return bool(jax.device_get(x))


def setprod(table: jax.Array, a: int, b: int, c: int, s: float) -> jax.Array:
    return table.at[c, a, b].set(s)


def add_identity(table: jax.Array, dim: int) -> jax.Array:
    for a in range(dim):
        table = setprod(table, 0, a, a, 1.0)
        table = setprod(table, a, 0, a, 1.0)
    return table


def real_table() -> jax.Array:
    table = jnp.zeros((1, 1, 1), dtype=jnp.float64)
    return setprod(table, 0, 0, 0, 1.0)


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
        rows = [
            (i, j, k, 1.0),
            (j, k, i, 1.0),
            (k, i, j, 1.0),
            (j, i, k, -1.0),
            (k, j, i, -1.0),
            (i, k, j, -1.0),
        ]
        for a, b, c, s in rows:
            table = setprod(table, a, b, c, s)
    return table


def octonion_table() -> jax.Array:
    table = jnp.zeros((8, 8, 8), dtype=jnp.float64)
    table = add_identity(table, 8)
    for a in range(1, 8):
        table = setprod(table, a, a, 0, -1.0)
    for i, j, k in FANO:
        rows = [
            (i, j, k, 1.0),
            (j, k, i, 1.0),
            (k, i, j, 1.0),
            (j, i, k, -1.0),
            (k, j, i, -1.0),
            (i, k, j, -1.0),
        ]
        for a, b, c, s in rows:
            table = setprod(table, a, b, c, s)
    return table


def basis(dim: int, idx: int) -> jax.Array:
    return jnp.eye(dim, dtype=jnp.float64)[idx]


def multiply(table: jax.Array, x: jax.Array, y: jax.Array) -> jax.Array:
    return jnp.einsum("cab,a,b->c", table, x, y)


def commutator_max(table: jax.Array) -> float:
    dim = table.shape[0]
    max_seen = 0.0
    for a in range(dim):
        for b in range(dim):
            ea = basis(dim, a)
            eb = basis(dim, b)
            value = py_float(jnp.linalg.norm(multiply(table, ea, eb) - multiply(table, eb, ea)))
            max_seen = max(max_seen, value)
    return max_seen


def associator_max(table: jax.Array) -> float:
    dim = table.shape[0]
    max_seen = 0.0
    for a in range(dim):
        for b in range(dim):
            for c in range(dim):
                ea = basis(dim, a)
                eb = basis(dim, b)
                ec = basis(dim, c)
                left = multiply(table, multiply(table, ea, eb), ec)
                right = multiply(table, ea, multiply(table, eb, ec))
                value = py_float(jnp.linalg.norm(left - right))
                max_seen = max(max_seen, value)
    return max_seen


def probe_vector(dim: int, sample_idx: int, side: int) -> jax.Array:
    vals: list[float] = []
    for j in range(1, dim + 1):
        raw = (
            (sample_idx + 17) * (j + 3) * (side + 5) * 37
            + (j + 1) ** 2 * 19
            + sample_idx * 11
            + side * 13
        ) % 101
        vals.append((float(raw) - 50.0) / 37.0)
    return jnp.asarray(vals, dtype=jnp.float64)


def norm_mult_residual(table: jax.Array) -> float:
    dim = table.shape[0]
    max_seen = 0.0
    for sample_idx in range(1, NORM_PROBE_COUNT + 1):
        x = probe_vector(dim, sample_idx, 1)
        y = probe_vector(dim, sample_idx, 2)
        residual = py_float(jnp.abs(jnp.linalg.norm(multiply(table, x, y)) - jnp.linalg.norm(x) * jnp.linalg.norm(y)))
        max_seen = max(max_seen, residual)
    return max_seen


def has_zero_divisors_sampled(table: jax.Array) -> tuple[bool, float, dict[str, Any] | None]:
    dim = table.shape[0]
    min_product_norm = float("inf")
    for a in range(dim):
        for b in range(dim):
            product_norm = py_float(jnp.linalg.norm(multiply(table, basis(dim, a), basis(dim, b))))
            min_product_norm = min(min_product_norm, product_norm)
            if product_norm < TOL:
                return True, min_product_norm, {
                    "kind": "basis_pair",
                    "a": a,
                    "b": b,
                    "product_norm": product_norm,
                }
    for sample_idx in range(1, NORM_PROBE_COUNT + 1):
        x = probe_vector(dim, sample_idx, 1)
        y = probe_vector(dim, sample_idx, 2)
        if py_float(jnp.linalg.norm(x)) > TOL and py_float(jnp.linalg.norm(y)) > TOL:
            product_norm = py_float(jnp.linalg.norm(multiply(table, x, y)))
            min_product_norm = min(min_product_norm, product_norm)
            if product_norm < TOL:
                return True, min_product_norm, {
                    "kind": "probe_pair",
                    "sample_idx": sample_idx,
                    "product_norm": product_norm,
                }
    return False, min_product_norm, None


def analyze_algebra(name: str, label: str, table: jax.Array) -> dict[str, Any]:
    dim = table.shape[0]
    comm = commutator_max(table)
    assoc = associator_max(table)
    norm_resid = norm_mult_residual(table)
    has_zero, min_product_norm, zero_witness = has_zero_divisors_sampled(table)
    n01 = comm > TOL
    assoc_pass = assoc < TOL
    normed_division = norm_resid < TOL and not has_zero
    return {
        "name": name,
        "label": label,
        "dim": dim,
        "commutator_max": comm,
        "associator_max": assoc,
        "norm_mult_residual": norm_resid,
        "has_zero_divisors": has_zero,
        "zero_divisor_check": {
            "kind": "basis_pairs_plus_deterministic_pseudorandom_nonzero_probe_pairs",
            "probe_count": NORM_PROBE_COUNT,
            "min_product_norm_seen": min_product_norm,
            "witness": zero_witness,
        },
        "n01_pass": n01,
        "assoc_pass": assoc_pass,
        "normed_division": normed_division,
    }


def quaternion_to_su2(q: jax.Array) -> jax.Array:
    a, b, c, d = q
    return jnp.asarray(
        [
            [a + b * 1j, c + d * 1j],
            [-c + d * 1j, a - b * 1j],
        ],
        dtype=jnp.complex128,
    )


def unit_quaternion_probes() -> list[jax.Array]:
    probes = [
        jnp.asarray([1.0, 0.0, 0.0, 0.0], dtype=jnp.float64),
        jnp.asarray([0.0, 1.0, 0.0, 0.0], dtype=jnp.float64),
        jnp.asarray([0.0, 0.0, 1.0, 0.0], dtype=jnp.float64),
        jnp.asarray([0.0, 0.0, 0.0, 1.0], dtype=jnp.float64),
    ]
    for sample_idx in range(1, NORM_PROBE_COUNT + 1):
        v = probe_vector(4, sample_idx, 3)
        probes.append(v / jnp.linalg.norm(v))
    return probes


def spinor_is_h_verdict() -> dict[str, Any]:
    identity2 = jnp.eye(2, dtype=jnp.complex128)
    max_unitarity = 0.0
    max_det = 0.0
    probes = unit_quaternion_probes()
    for q in probes:
        u = quaternion_to_su2(q)
        max_unitarity = max(max_unitarity, py_float(jnp.max(jnp.abs(u @ jnp.conj(u.T) - identity2))))
        max_det = max(max_det, py_float(jnp.abs(jnp.linalg.det(u) - (1.0 + 0.0j))))
    return {
        "value": max_unitarity < TOL and max_det < TOL,
        "numbers": {
            "unit_quaternion_probe_count": len(probes),
            "max_unitarity_residual": max_unitarity,
            "max_det_residual": max_det,
            "tol": TOL,
        },
        "map": "q=(a,b,c,d) -> [[a+bi, c+di], [-c+di, a-bi]]",
        "identification_fence": "Computed SU(2)=Sp(1) carrier check only; Pauli/Cl0(3) noted as standard spinor-side identification, not promoted here.",
    }


def compute_verdicts(algebras: dict[str, Any]) -> dict[str, Any]:
    candidates = [
        (alg["dim"], key)
        for key, alg in algebras.items()
        if alg["n01_pass"] and alg["assoc_pass"] and alg["normed_division"]
    ]
    candidates.sort(key=lambda row: row[0])
    selected = None if not candidates else candidates[0][1]
    selected_dim = None if selected is None else algebras[selected]["dim"]
    return {
        "minimal_N01_assoc_div": {
            "value": selected == "H",
            "selected": selected,
            "selected_dim": selected_dim,
            "candidate_order": [{"algebra": key, "dim": dim} for dim, key in candidates],
            "numbers": {
                key: {
                    "dim": algebras[key]["dim"],
                    "n01_pass": algebras[key]["n01_pass"],
                    "assoc_pass": algebras[key]["assoc_pass"],
                    "normed_division": algebras[key]["normed_division"],
                }
                for key in ["R", "C", "H", "O"]
            },
        },
        "spinor_is_H": spinor_is_h_verdict(),
    }


def shared_scalar_diffs(jax_result: dict[str, Any], julia_reference: dict[str, Any]) -> dict[str, Any]:
    keys = jax_result["shared_scalar_keys"]
    rows: list[dict[str, Any]] = []
    max_diff = 0.0
    divergences_1e6: list[dict[str, Any]] = []
    boolean_mismatches: list[dict[str, Any]] = []
    for algebra_name, algebra in jax_result["algebras"].items():
        julia_algebra = julia_reference["algebras"][algebra_name]
        for key in keys:
            jv = float(algebra[key])
            rv = float(julia_algebra[key])
            diff = abs(jv - rv)
            max_diff = max(max_diff, diff)
            row = {
                "algebra": algebra_name,
                "key": key,
                "jax": jv,
                "julia": rv,
                "abs_diff": diff,
            }
            rows.append(row)
            if diff > STRICT_STOP_TOL:
                divergences_1e6.append(row)
        for key in ["has_zero_divisors", "n01_pass", "assoc_pass", "normed_division"]:
            if bool(algebra[key]) != bool(julia_algebra[key]):
                boolean_mismatches.append({
                    "algebra": algebra_name,
                    "key": key,
                    "jax": bool(algebra[key]),
                    "julia": bool(julia_algebra[key]),
                })
    return {
        "shared_scalar_rows": rows,
        "parity_max_diff": max_diff,
        "within_1e_9": max_diff < TOL,
        "strict_divergence_gt_1e_6": divergences_1e6,
        "boolean_mismatches": boolean_mismatches,
        "stop_condition_fired": bool(divergences_1e6) or bool(boolean_mismatches),
    }


def build_result() -> dict[str, Any]:
    algebras = {
        "R": analyze_algebra("R", "real_numbers", real_table()),
        "C": analyze_algebra("C", "complex_numbers", complex_table()),
        "H": analyze_algebra("H", "quaternions", quaternion_table()),
        "O": analyze_algebra("O", "octonions", octonion_table()),
    }
    verdicts = compute_verdicts(algebras)
    controls = {
        "R_commutative_control_ok": not algebras["R"]["n01_pass"],
        "C_commutative_control_ok": not algebras["C"]["n01_pass"],
        "O_nonassociative_control_ok": not algebras["O"]["assoc_pass"],
    }
    controls["control_miswired"] = not (
        controls["R_commutative_control_ok"]
        and controls["C_commutative_control_ok"]
        and controls["O_nonassociative_control_ok"]
    )
    sentence = (
        "At scratch_diagnostic ceiling, N01 plus associativity plus minimal normed-division filtering selects H, "
        "and the unit-quaternion SU(2)=Sp(1) check supports H as the spinor carrier, with the stated fences."
        if verdicts["minimal_N01_assoc_div"]["value"] and verdicts["spinor_is_H"]["value"]
        else "At scratch_diagnostic ceiling, the corrected Hurwitz minimality diagnostic did not select H cleanly; inspect controls and parity before using it."
    )
    shared_scalar_keys = ["dim", "commutator_max", "associator_max", "norm_mult_residual"]
    shared_scalars: dict[str, float] = {}
    shared_booleans: dict[str, bool] = {}
    for algebra_key in ["R", "C", "H", "O"]:
        for scalar_key in shared_scalar_keys:
            shared_scalars[f"{algebra_key}.{scalar_key}"] = float(algebras[algebra_key][scalar_key])
        for bool_key in ["has_zero_divisors", "n01_pass", "assoc_pass", "normed_division"]:
            shared_booleans[f"{algebra_key}.{bool_key}"] = bool(algebras[algebra_key][bool_key])
    shared_booleans["verdict.minimal_N01_assoc_div"] = bool(verdicts["minimal_N01_assoc_div"]["value"])
    shared_booleans["verdict.spinor_is_H"] = bool(verdicts["spinor_is_H"]["value"])
    for key, value in controls.items():
        shared_booleans[f"control.{key}"] = bool(value)
    result: dict[str, Any] = {
        "object_id": OBJECT_ID,
        "backend": "jax_mirror",
        "generated_at": _dt.datetime.now(_dt.UTC).isoformat(),
        "source_path": str(Path(__file__).resolve()),
        "result_path": str(RESULT_PATH),
        "julia_reference_path": str(JULIA_REFERENCE_PATH),
        "jax_enable_x64": bool(jax.config.read("jax_enable_x64")),
        "question": "Among Hurwitz normed division algebras R,C,H,O, does N01 noncommutation plus associativity plus minimality select H, and is H the spinor carrier?",
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "claim_ceiling": "PRELIM Hurwitz finite-table diagnostic only; no forcing proof, basin, admission, engine, bridge, Axis0, or manifold closure claim",
        "expected_controls": {
            "R": "commutative control; must fail n01_pass",
            "C": "commutative control; must fail n01_pass",
            "O": "nonassociative control; must fail assoc_pass",
            "H": "expected minimal noncommutative associative normed division algebra",
        },
        "fences": [
            "Presumes the normed-division-algebra frame is the right place to look; this is a presumption, not forced.",
            "Does not forbid noncommutative operator algebras over R or C; commutativity here is the scalar algebra, not operators on it.",
            "H selection is a ratchet/minimality diagnostic result, not a proof that the engine must be spinorial.",
        ],
        "root_constraints": {
            "F01": "finite explicit real multiplication tables / structure constants for R,C,H,O",
            "N01": "basis-pair commutator norm of the scalar algebra multiplication table",
        },
        "tol": TOL,
        "strict_stop_tol": STRICT_STOP_TOL,
        "norm_probe_count": NORM_PROBE_COUNT,
        "probe_source": "deterministic pseudorandom real vectors for reproducible Julia/JAX parity",
        "shared_scalar_keys": shared_scalar_keys,
        "shared_scalars": shared_scalars,
        "shared_booleans": shared_booleans,
        "algebras": algebras,
        "verdicts": verdicts,
        "control_status": controls,
        "plain_sentence": sentence,
    }
    if JULIA_REFERENCE_PATH.exists():
        julia_reference = json.loads(JULIA_REFERENCE_PATH.read_text(encoding="utf-8"))
        parity = shared_scalar_diffs(result, julia_reference)
    else:
        parity = {
            "shared_scalar_rows": [],
            "parity_max_diff": None,
            "within_1e_9": False,
            "strict_divergence_gt_1e_6": [{
                "missing": str(JULIA_REFERENCE_PATH),
                "reason": "Julia reference JSON must exist before JAX parity can run.",
            }],
            "boolean_mismatches": [],
            "stop_condition_fired": True,
        }
    result["parity"] = parity
    result["stop_condition_fired"] = controls["control_miswired"] or bool(parity["stop_condition_fired"])
    return result


def print_summary(result: dict[str, Any]) -> None:
    print("Hurwitz minimality prelim - JAX mirror")
    print(
        f"classification: {result['classification']} | "
        f"promotion_allowed: {str(result['promotion_allowed']).lower()} | "
        f"jax_enable_x64: {str(result['jax_enable_x64']).lower()}"
    )
    for key in ["R", "C", "H", "O"]:
        a = result["algebras"][key]
        print(
            f"{key}: dim={a['dim']} "
            f"commutator_max={a['commutator_max']} "
            f"associator_max={a['associator_max']} "
            f"norm_mult_residual={a['norm_mult_residual']} "
            f"has_zero_divisors={str(a['has_zero_divisors']).lower()} "
            f"n01_pass={str(a['n01_pass']).lower()} "
            f"assoc_pass={str(a['assoc_pass']).lower()} "
            f"normed_division={str(a['normed_division']).lower()}"
        )
    minimal = result["verdicts"]["minimal_N01_assoc_div"]
    spinor = result["verdicts"]["spinor_is_H"]
    print(
        f"minimal_N01_assoc_div={str(minimal['value']).lower()} "
        f"selected={minimal['selected']} dim={minimal['selected_dim']}"
    )
    print(f"spinor_is_H={str(spinor['value']).lower()} numbers={json.dumps(spinor['numbers'], sort_keys=True)}")
    parity = result["parity"]
    print(f"parity_max_diff={parity['parity_max_diff']} within_1e-9={str(parity['within_1e_9']).lower()}")
    if parity["strict_divergence_gt_1e_6"] or parity["boolean_mismatches"]:
        print("STOP: JAX and Julia disagree beyond the strict parity stop condition:")
        print(json.dumps({
            "strict_divergence_gt_1e_6": parity["strict_divergence_gt_1e_6"],
            "boolean_mismatches": parity["boolean_mismatches"],
        }, indent=2, sort_keys=True))
    if result["control_status"]["control_miswired"]:
        print("STOP: Hurwitz control failed; multiplication table is miswired.")
    print(result["plain_sentence"])
    print(f"wrote: {result['result_path']}")
    if not result["stop_condition_fired"]:
        print("CODEX2_HURWITZ_DONE")


def main() -> int:
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print_summary(result)
    return 2 if result["stop_condition_fired"] else 0


if __name__ == "__main__":
    sys.exit(main())
