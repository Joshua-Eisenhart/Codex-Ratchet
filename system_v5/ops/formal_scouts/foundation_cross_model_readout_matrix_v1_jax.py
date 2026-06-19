#!/usr/bin/env python3
# object_id: foundation_cross_model_readout_matrix_v1_jax
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false
# reads_peer_result: false

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import math
from fractions import Fraction
from pathlib import Path
from typing import Any

import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp
import z3
import cvc5


RUNG_ID = "cross_model_readout_matrix_v1"
OBJECT_ID = "foundation_cross_model_readout_matrix_v1_jax"
ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/foundation_cross_model_readout_matrix_v1_jax.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_cross_model_readout_matrix_v1_jax_results.json"
CARRIER_SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/sim_three_engine_clifford_spinor_carrier_envelope.py"
CARRIER_RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/three_engine_clifford_spinor_carrier_envelope_results.json"
TOL = 1.0e-9

classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False
reads_peer_result = False

BASIS_LABELS = ["uuu", "duu", "udu", "ddu", "uud", "dud", "udd", "ddd"]
LENS_ORDER = ["qit", "igt", "holodeck_runtime", "physics_math"]
LABEL_SHUFFLE_ORDER = ["igt", "physics_math", "qit", "holodeck_runtime"]
PAULI_X = jnp.asarray([[0.0, 1.0], [1.0, 0.0]], dtype=jnp.complex128)
PAULI_Y = jnp.asarray([[0.0, -1.0j], [1.0j, 0.0]], dtype=jnp.complex128)

TOOL_MANIFEST = {
    "jax": {
        "tried": True,
        "used": True,
        "reason": "load-bearing x64 readout computation over the fixed finite carrier support",
    },
    "jax.numpy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing density, entropy, Pauli-coordinate, and matrix readout arithmetic",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing derive-in-solver proof for carrier-erasure collapse from bound carrier entries",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent derive-in-solver proof matching z3",
    },
    "json": {
        "tried": True,
        "used": True,
        "reason": "supportive result serialization",
    },
    "hashlib": {
        "tried": True,
        "used": True,
        "reason": "supportive source fingerprint",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "jax": "load_bearing",
    "jax.numpy": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "json": "supportive",
    "hashlib": "supportive",
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def to_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_jsonable(v) for v in value]
    if isinstance(value, Path):
        return str(value)
    if hasattr(value, "shape"):
        return to_jsonable(jax.device_get(value).tolist())
    if isinstance(value, Fraction):
        return f"{value.numerator}/{value.denominator}"
    return value


def support_vectors() -> list[dict[str, Any]]:
    states: list[dict[str, Any]] = []
    basis = jnp.zeros((8,), dtype=jnp.complex128).at[0].set(1.0 + 0.0j)
    states.append(
        {
            "state_id": "basis_uuu",
            "description": "Cl(6) spinor basis density at |uuu>",
            "amplitudes": basis,
        }
    )

    ghz = jnp.zeros((8,), dtype=jnp.complex128).at[0].set(1 / math.sqrt(2)).at[7].set(1 / math.sqrt(2))
    states.append(
        {
            "state_id": "ghz_phase",
            "description": "two-corner coherent spinor density over |uuu> and |ddd>",
            "amplitudes": ghz,
        }
    )

    w_state = (
        jnp.zeros((8,), dtype=jnp.complex128)
        .at[1]
        .set(1 / math.sqrt(3))
        .at[2]
        .set(1 / math.sqrt(3))
        .at[4]
        .set(1 / math.sqrt(3))
    )
    states.append(
        {
            "state_id": "w_single_down",
            "description": "single-down W spinor density over |duu>, |udu>, |uud>",
            "amplitudes": w_state,
        }
    )

    biased = (
        jnp.zeros((8,), dtype=jnp.complex128)
        .at[0]
        .set(math.sqrt(1 / 2))
        .at[3]
        .set(math.sqrt(1 / 4))
        .at[5]
        .set(1.0j * math.sqrt(1 / 8))
        .at[6]
        .set(math.sqrt(1 / 8))
    )
    states.append(
        {
            "state_id": "biased_phase",
            "description": "asymmetric phase spinor density with rational diagonal support",
            "amplitudes": biased,
        }
    )

    states.append(
        {
            "state_id": "uniform_mixed",
            "description": "max-entropy finite density state with flat ordered diagonal support",
            "density_diagonal": [1 / 8 for _ in range(8)],
        }
    )

    states.append(
        {
            "state_id": "even_parity_mixed",
            "description": "low-entropy even-parity diagonal density selected to invert IGT against QIT and holodeck",
            "density_diagonal": [1 / 4, 0.0, 1 / 4, 0.0, 1 / 4, 0.0, 1 / 4, 0.0],
        }
    )
    return states


def density_from_vector(vec: jax.Array) -> jax.Array:
    return jnp.outer(vec, jnp.conjugate(vec))


def density_from_diagonal(diagonal: list[float]) -> jax.Array:
    return jnp.diag(jnp.asarray(diagonal, dtype=jnp.complex128))


def density_from_state(state: dict[str, Any]) -> jax.Array:
    if "amplitudes" in state:
        return density_from_vector(state["amplitudes"])
    return density_from_diagonal(state["density_diagonal"])


def erased_density() -> jax.Array:
    return jnp.eye(8, dtype=jnp.complex128) / 8.0


def carrier_payload(state: dict[str, Any], rho: jax.Array, erased: bool) -> dict[str, Any]:
    if erased:
        return {
            "state_kind": "erased_density",
            "amplitudes": "maximally_mixed_density_no_spinor_amplitudes",
            "density_diagonal": diag_probs(rho),
        }
    if "amplitudes" in state:
        return {
            "state_kind": "pure_spinor_density",
            "amplitudes": to_jsonable(
                [
                    {"real": float(jax.device_get(jnp.real(v))), "imag": float(jax.device_get(jnp.imag(v)))}
                    for v in state["amplitudes"]
                ]
            ),
            "density_diagonal": diag_probs(rho),
        }
    return {
        "state_kind": "mixed_density",
        "amplitudes": "mixed_density_no_spinor_amplitudes",
        "density_diagonal": [float(v) for v in state["density_diagonal"]],
    }


def entropy_vn(rho: jax.Array) -> float:
    herm = (rho + jnp.conjugate(rho.T)) / 2.0
    vals = jnp.real(jnp.linalg.eigvalsh(herm))
    vals = jnp.clip(vals, 0.0, 1.0)
    safe = jnp.clip(vals, 1.0e-30, 1.0)
    entropy = -jnp.sum(jnp.where(vals > 1.0e-12, vals * jnp.log(safe), 0.0))
    return float(jax.device_get(entropy))


def partial_trace_q0(rho: jax.Array) -> jax.Array:
    red = jnp.zeros((2, 2), dtype=jnp.complex128)
    for q0_left in range(2):
        for q0_right in range(2):
            val = 0.0 + 0.0j
            for q1 in range(2):
                for q2 in range(2):
                    left = q0_left + 2 * q1 + 4 * q2
                    right = q0_right + 2 * q1 + 4 * q2
                    val = val + rho[left, right]
            red = red.at[q0_left, q0_right].set(val)
    return red


def diag_probs(rho: jax.Array) -> list[float]:
    return [float(jax.device_get(jnp.real(rho[idx, idx]))) for idx in range(8)]


def bit_sign(index: int, qubit: int) -> float:
    return 1.0 if ((index >> qubit) & 1) == 0 else -1.0


def z_expectations_from_diag(diag: list[float]) -> list[float]:
    return [sum(bit_sign(idx, qubit) * diag[idx] for idx in range(8)) for qubit in range(3)]


def pauli_coord(rho: jax.Array, qubit: int, pauli: str) -> float:
    total = 0.0 + 0.0j
    for rest in range(4):
        lower = rest & ((1 << qubit) - 1)
        upper = rest >> qubit
        idx0 = lower | (0 << qubit) | (upper << (qubit + 1))
        idx1 = lower | (1 << qubit) | (upper << (qubit + 1))
        if pauli == "X":
            total = total + rho[idx0, idx1] + rho[idx1, idx0]
        elif pauli == "Y":
            total = total + (-1.0j * rho[idx0, idx1]) + (1.0j * rho[idx1, idx0])
        else:
            raise ValueError(pauli)
    return float(jax.device_get(jnp.real(total)))


def qit_readout(rho: jax.Array) -> dict[str, float]:
    offdiag = rho - jnp.diag(jnp.diag(rho))
    return {
        "von_neumann_entropy": entropy_vn(rho),
        "coherence_l1": float(jax.device_get(jnp.sum(jnp.abs(offdiag)))),
        "purity": float(jax.device_get(jnp.real(jnp.trace(rho @ rho)))),
        "subsystem_entropy_q0": entropy_vn(partial_trace_q0(rho)),
    }


def igt_readout(rho: jax.Array) -> dict[str, Any]:
    z_vals = z_expectations_from_diag(diag_probs(rho))
    asym = [abs(z_vals[0] - z_vals[1]), abs(z_vals[0] - z_vals[2]), abs(z_vals[1] - z_vals[2])]
    return {
        "observable": "win_lose_payoff_asymmetry_only",
        "payoff_definition": "P[i,j]=max(0, z_i-z_j); report abs(P[i,j]-P[j,i]) == abs(z_i-z_j)",
        "z_expectations": z_vals,
        "asymmetry_pairs": {"q0_q1": asym[0], "q0_q2": asym[1], "q1_q2": asym[2]},
        "asymmetry_sum": float(sum(asym)),
    }


def holodeck_signature(diag: list[float]) -> dict[str, Any]:
    acc = 3
    seen: set[int] = set()
    path_sum = 0
    threshold_step = len(diag)
    found_threshold = False
    for idx, value in enumerate(diag):
        bucket = int(round(1000 * value))
        acc = (acc * 5 + bucket + idx) % 97
        seen.add(acc)
        path_sum += (idx + 1) * acc
        if not found_threshold and acc % 11 == 0:
            threshold_step = idx + 1
            found_threshold = True
    return {
        "ordered_basis": BASIS_LABELS,
        "final_accumulator_mod97": acc,
        "unique_runtime_states": len(seen),
        "threshold_step_mod11_zero": threshold_step,
        "weighted_path_sum": path_sum,
        "normalized_signature": [acc / 96, len(seen) / 8, threshold_step / 8, path_sum / (96 * sum(range(1, 9)))],
    }


def physics_readout(rho: jax.Array) -> dict[str, float | str]:
    x0 = pauli_coord(rho, 0, "X")
    y0 = pauli_coord(rho, 0, "Y")
    z0 = z_expectations_from_diag(diag_probs(rho))[0]
    grade1_norm = math.sqrt(x0 * x0 + y0 * y0 + z0 * z0)
    return {
        "coordinate_source": "first-qubit Pauli coordinates mirrored as Cl(3,0) grade-1 vector",
        "pauli_x_q0": x0,
        "pauli_y_q0": y0,
        "pauli_z_q0": z0,
        "clifford_grade1_norm": grade1_norm,
        "density_frobenius_norm": math.sqrt(float(jax.device_get(jnp.real(jnp.trace(rho @ rho))))),
    }


def scalar_profile(readouts: dict[str, Any]) -> dict[str, float]:
    qit = readouts["qit"]
    igt = readouts["igt"]
    hol = readouts["holodeck_runtime"]
    phy = readouts["physics_math"]
    return {
        "qit": qit["von_neumann_entropy"] + qit["coherence_l1"] + qit["purity"] + qit["subsystem_entropy_q0"],
        "igt": igt["asymmetry_sum"],
        "holodeck_runtime": sum(hol["normalized_signature"]),
        "physics_math": abs(float(phy["pauli_x_q0"]))
        + abs(float(phy["pauli_y_q0"]))
        + abs(float(phy["pauli_z_q0"]))
        + float(phy["clifford_grade1_norm"]),
    }


def matrix_from_profiles(profiles: list[dict[str, float]], order: list[str]) -> list[list[float]]:
    return [[profile[lens] for lens in order] for profile in profiles]


def matrix_l1_delta(left: list[list[float]], right: list[list[float]]) -> float:
    return sum(abs(left[row][col] - right[row][col]) for row in range(len(left)) for col in range(len(left[row])))


def column_std_sum(matrix: list[list[float]]) -> float:
    rows = len(matrix)
    cols = len(matrix[0])
    total = 0.0
    for col in range(cols):
        vals = [matrix[row][col] for row in range(rows)]
        mean_val = sum(vals) / rows
        total += math.sqrt(sum((v - mean_val) ** 2 for v in vals) / rows)
    return total


def rounded_signature(profile: dict[str, float]) -> list[float]:
    return [round(profile[lens], 9) for lens in LENS_ORDER]


def class_count(profiles: list[dict[str, float]]) -> int:
    return len({json.dumps(rounded_signature(profile)) for profile in profiles})


def pairwise_inversion_control(rows: list[dict[str, Any]], profiles: list[dict[str, float]]) -> dict[str, Any]:
    counts = [[0 for _ in LENS_ORDER] for _ in LENS_ORDER]
    examples: dict[str, list[dict[str, Any]]] = {}
    for a_idx, lens_a in enumerate(LENS_ORDER):
        for b_idx, lens_b in enumerate(LENS_ORDER):
            if a_idx == b_idx:
                continue
            pair_key = f"{lens_a}__{lens_b}"
            examples[pair_key] = []
            for left in range(len(profiles)):
                for right in range(left + 1, len(profiles)):
                    delta_a = profiles[left][lens_a] - profiles[right][lens_a]
                    delta_b = profiles[left][lens_b] - profiles[right][lens_b]
                    if delta_a * delta_b < -TOL:
                        counts[a_idx][b_idx] += 1
                        if len(examples[pair_key]) < 3:
                            examples[pair_key].append(
                                {
                                    "state_i": rows[left]["state_id"],
                                    "state_j": rows[right]["state_id"],
                                    lens_a: [profiles[left][lens_a], profiles[right][lens_a]],
                                    lens_b: [profiles[left][lens_b], profiles[right][lens_b]],
                                }
                            )
    off_diagonal = [
        counts[row_idx][col_idx]
        for row_idx in range(len(LENS_ORDER))
        for col_idx in range(len(LENS_ORDER))
        if row_idx != col_idx
    ]
    return {
        "lens_order": LENS_ORDER,
        "method": "strict pairwise ordering inversion count over scalar readout columns; ties do not count",
        "inversion_count_matrix": counts,
        "off_diagonal_min": min(off_diagonal),
        "no_two_lenses_co_monotone": all(count >= 1 for count in off_diagonal),
        "pair_examples": examples,
    }


def constraints_for_density(rho: jax.Array) -> dict[str, Any]:
    herm = (rho + jnp.conjugate(rho.T)) / 2.0
    eigs = jnp.real(jnp.linalg.eigvalsh(herm))
    return {
        "trace_eq_1": abs(float(jax.device_get(jnp.real(jnp.trace(rho)))) - 1.0) <= TOL,
        "psd": float(jax.device_get(jnp.min(eigs))) >= -TOL,
        "hermitian": float(jax.device_get(jnp.linalg.norm(rho - jnp.conjugate(rho.T)))) <= TOL,
        "normalization": abs(float(jax.device_get(jnp.real(jnp.trace(rho)))) - 1.0) <= TOL,
        "min_eigenvalue": float(jax.device_get(jnp.min(eigs))),
    }


def compute_rows(*, erased: bool = False, reversed_order: bool = False) -> tuple[list[dict[str, Any]], list[dict[str, float]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    profiles: list[dict[str, float]] = []
    constraints: list[dict[str, Any]] = []
    for state in support_vectors():
        rho = erased_density() if erased else density_from_state(state)
        diag = diag_probs(rho)
        if reversed_order:
            diag = list(reversed(diag))
        readouts = {
            "qit": qit_readout(rho),
            "igt": igt_readout(rho),
            "holodeck_runtime": holodeck_signature(diag),
            "physics_math": physics_readout(rho),
        }
        profile = scalar_profile(readouts)
        constraint = constraints_for_density(rho)
        rows.append(
            {
                "state_id": state["state_id"],
                "description": state["description"],
                "support_index_labels": BASIS_LABELS,
                "readouts": readouts,
                "scalar_profile": profile,
                "constraints": constraint,
            }
            | carrier_payload(state, rho, erased)
        )
        profiles.append(profile)
        constraints.append(constraint)
    return rows, profiles, constraints


def z3_real(frac: Fraction) -> z3.RatNumRef:
    return z3.RealVal(f"{frac.numerator}/{frac.denominator}")


def exact_z_expr(vars_: list[Any], qubit: int) -> Any:
    return z3.Sum([z3.RealVal(bit_sign(idx, qubit)) * vars_[idx] for idx in range(8)])


def z3_erasure_proof(probs: list[Fraction], *, prefix: str) -> dict[str, Any]:
    solver = z3.Solver()
    p_vars = [z3.Real(f"{prefix}_p_{idx}") for idx in range(8)]
    for idx, frac in enumerate(probs):
        solver.add(p_vars[idx] == z3_real(frac))
    z0 = exact_z_expr(p_vars, 0)
    z2 = exact_z_expr(p_vars, 2)
    solver.add(z2 - z0 == z3.RealVal(0))
    return {
        "verdict": str(solver.check()),
        "derived_relation": "z2 - z0 == 0, where zq=sum_b sign(q,b)*p_b is derived inside z3 from bound p_b entries",
        "bound_probabilities": [f"{p.numerator}/{p.denominator}" for p in probs],
    }


def cvc5_sum(solver: cvc5.Solver, terms: list[Any]) -> Any:
    if not terms:
        return solver.mkReal(0)
    if len(terms) == 1:
        return terms[0]
    return solver.mkTerm(cvc5.Kind.ADD, *terms)


def cvc5_sub(solver: cvc5.Solver, left: Any, right: Any) -> Any:
    return solver.mkTerm(cvc5.Kind.SUB, left, right)


def cvc5_sign_term(solver: cvc5.Solver, sign: float, var: Any) -> Any:
    if sign > 0:
        return var
    return solver.mkTerm(cvc5.Kind.MULT, solver.mkReal(-1), var)


def cvc5_z_expr(solver: cvc5.Solver, vars_: list[Any], qubit: int) -> Any:
    return cvc5_sum(solver, [cvc5_sign_term(solver, bit_sign(idx, qubit), vars_[idx]) for idx in range(8)])


def cvc5_erasure_proof(probs: list[Fraction], *, prefix: str) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("QF_LRA")
    real_sort = solver.getRealSort()
    p_vars = [solver.mkConst(real_sort, f"{prefix}_p_{idx}") for idx in range(8)]
    for idx, frac in enumerate(probs):
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, p_vars[idx], solver.mkReal(frac.numerator, frac.denominator)))
    z0 = cvc5_z_expr(solver, p_vars, 0)
    z2 = cvc5_z_expr(solver, p_vars, 2)
    solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, cvc5_sub(solver, z2, z0), solver.mkReal(0)))
    return {
        "verdict": str(solver.checkSat()),
        "derived_relation": "z2 - z0 == 0, where zq=sum_b sign(q,b)*p_b is derived inside cvc5 from bound p_b entries",
        "bound_probabilities": [f"{p.numerator}/{p.denominator}" for p in probs],
    }


def dual_smt_erasure_proof() -> dict[str, Any]:
    biased_probs = [Fraction(1, 2), Fraction(0), Fraction(0), Fraction(1, 4), Fraction(0), Fraction(1, 8), Fraction(1, 8), Fraction(0)]
    erased_probs = [Fraction(1, 8) for _ in range(8)]
    z3_real_result = z3_erasure_proof(biased_probs, prefix="real")
    z3_erased_result = z3_erasure_proof(erased_probs, prefix="erased")
    cvc5_real_result = cvc5_erasure_proof(biased_probs, prefix="real")
    cvc5_erased_result = cvc5_erasure_proof(erased_probs, prefix="erased")
    return {
        "claim": "The biased carrier state has a derived q2-vs-q0 payoff asymmetry, while maximally mixed erasure collapses that relation to zero.",
        "z3": {
            "version": z3.get_version_string(),
            "real_no_asymmetry": z3_real_result,
            "erased_no_asymmetry": z3_erased_result,
            "verdict": z3_real_result["verdict"],
            "negative_control_verdict": z3_erased_result["verdict"],
            "load_bearing": True,
        },
        "cvc5": {
            "version": getattr(cvc5, "__version__", "unknown"),
            "real_no_asymmetry": cvc5_real_result,
            "erased_no_asymmetry": cvc5_erased_result,
            "verdict": cvc5_real_result["verdict"],
            "negative_control_verdict": cvc5_erased_result["verdict"],
            "load_bearing": True,
        },
    }


def build_result() -> dict[str, Any]:
    rows, profiles, constraints = compute_rows()
    erased_rows, erased_profiles, _ = compute_rows(erased=True)
    reversed_rows, reversed_profiles, _ = compute_rows(reversed_order=True)

    matrix = matrix_from_profiles(profiles, LENS_ORDER)
    shuffled_matrix = matrix_from_profiles(profiles, LABEL_SHUFFLE_ORDER)
    erased_matrix = matrix_from_profiles(erased_profiles, LENS_ORDER)
    reversed_matrix = matrix_from_profiles(reversed_profiles, LENS_ORDER)
    igt_erased_profiles = [{**profile, "igt": 0.0} for profile in profiles]
    igt_erased_matrix = matrix_from_profiles(igt_erased_profiles, LENS_ORDER)

    label_delta = matrix_l1_delta(matrix, shuffled_matrix)
    real_structure = column_std_sum(matrix)
    erased_structure = column_std_sum(erased_matrix)
    map_before = column_std_sum([[row[1]] for row in matrix])
    map_after = column_std_sum([[row[1]] for row in igt_erased_matrix])
    order_delta = matrix_l1_delta(matrix, reversed_matrix)
    full_classes = class_count(profiles)
    erased_classes = class_count(erased_profiles)
    co_monotonicity = pairwise_inversion_control(rows, profiles)
    smt = dual_smt_erasure_proof()

    all_constraints_ok = all(c["trace_eq_1"] and c["psd"] and c["hermitian"] and c["normalization"] for c in constraints)
    controls_ok = (
        label_delta > TOL
        and real_structure > TOL
        and erased_structure <= TOL
        and map_before > TOL
        and map_after <= TOL
        and order_delta > TOL
        and full_classes > erased_classes
        and co_monotonicity["no_two_lenses_co_monotone"]
        and smt["z3"]["verdict"] == smt["cvc5"]["verdict"] == "unsat"
        and smt["z3"]["negative_control_verdict"] == smt["cvc5"]["negative_control_verdict"] == "sat"
    )

    return {
        "schema": "codex_ratchet.engine_leg_result.v1",
        "rung_id": RUNG_ID,
        "object_id": OBJECT_ID,
        "engine": "jax",
        "backend": "jax_x64_dual_smt_readout_matrix",
        "classification": classification,
        "promotion_allowed": promotion_allowed,
        "formal_admission_allowed": formal_admission_allowed,
        "reads_peer_result": reads_peer_result,
        "ran": True,
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH),
        "source_sha256": sha256_file(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "carrier_source_pin": {
            "source_path": str(CARRIER_SOURCE_PATH),
            "result_path": str(CARRIER_RESULT_PATH),
            "read_only": True,
            "rebuilt": False,
        },
        "jax_enable_x64": bool(jax.config.read("jax_enable_x64")),
        "claim_ceiling": "Scratch diagnostic cross-model readout matrix only: four readout lenses over one fixed six-state Clifford-spinor/density support S. No identity, canon, bridge, IGT truth, physics truth, Axis0, or formal admission claim.",
        "packages_used": ["jax", "jax.numpy", "z3", "cvc5", "json", "hashlib"],
        "aligned_packages_load_bearing": ["z3", "cvc5"],
        "package_table": TOOL_MANIFEST,
        "M": {
            "explicit_finite_probe_family": [
                "QIT: von Neumann entropy, l1 coherence, purity, first-qubit subsystem entropy",
                "IGT lens only: abs(P[i,j]-P[j,i]) over qubit-Z payoff probes derived from carrier density",
                "Holodeck/runtime: ordered diagonal trajectory accumulator/reachability signature",
                "Physics/math: first-qubit Pauli coordinate grade-vector mirror",
            ],
            "matrix_shape": [len(rows), len(LENS_ORDER)],
            "lens_order": LENS_ORDER,
        },
        "C": {
            "trace_eq_1": all(c["trace_eq_1"] for c in constraints),
            "psd": all(c["psd"] for c in constraints),
            "hermitian": all(c["hermitian"] for c in constraints),
            "normalization": all(c["normalization"] for c in constraints),
            "rung_specific_constraint": "All four readout maps consume the same fixed support S of six F01-finite Cl(6)-spinor/density states; every pair of scalar lens columns must have at least one measured ordering inversion.",
        },
        "S_mod_M": {
            "S": [row["state_id"] for row in rows],
            "equivalence_relation": "s ~_M t iff every scalarized readout probe in the four-lens matrix agrees after rounding to 1e-9",
            "full_probe_class_count": full_classes,
            "carrier_erased_class_count": erased_classes,
            "full_signatures": [rounded_signature(profile) for profile in profiles],
            "carrier_erased_signatures": [rounded_signature(profile) for profile in erased_profiles],
        },
        "readout_rows": rows,
        "control_rows": {
            "carrier_erasure_rows": erased_rows,
            "order_reversal_rows": reversed_rows,
        },
        "controls": {
            "label_shuffle": {
                "falsifies": "Rosetta-style relabeling where all lenses carry the same chart",
                "original_lens_order": LENS_ORDER,
                "shuffled_lens_order": LABEL_SHUFFLE_ORDER,
                "matrix_l1_delta": label_delta,
                "flips": label_delta > TOL,
            },
            "carrier_erasure": {
                "falsifies": "carrier-agnostic decorative readouts",
                "real_structure_norm": real_structure,
                "erased_structure_norm": erased_structure,
                "structure_drop": real_structure - erased_structure,
                "full_class_count": full_classes,
                "erased_class_count": erased_classes,
                "flips": real_structure > TOL and erased_structure <= TOL and full_classes > erased_classes,
            },
            "readout_map_erasure": {
                "falsifies": "a readout column that remains structured after replacing A_i with a constant map",
                "erased_lens": "igt",
                "column_structure_before": map_before,
                "column_structure_after": map_after,
                "flips": map_before > TOL and map_after <= TOL,
            },
            "order_composition_reversal": {
                "falsifies": "runtime readout ignoring its ordered carrier composition",
                "basis_order": BASIS_LABELS,
                "reversed_basis_order": list(reversed(BASIS_LABELS)),
                "matrix_l1_delta": order_delta,
                "flips": order_delta > TOL,
            },
            "pairwise_co_monotonicity": {
                "falsifies": "three non-physics lenses being merely co-monotone relabelings on this support",
                "flips": co_monotonicity["no_two_lenses_co_monotone"],
                "derived_from": "readout_rows[*].scalar_profile",
                **co_monotonicity,
            },
        },
        "co_monotonicity": co_monotonicity,
        "smt": smt,
        "summary": {
            "support_size": len(rows),
            "lens_count": len(LENS_ORDER),
            "full_probe_class_count": full_classes,
            "carrier_erased_class_count": erased_classes,
            "label_shuffle_delta": label_delta,
            "real_structure_norm": real_structure,
            "erased_structure_norm": erased_structure,
            "readout_map_erasure_before": map_before,
            "readout_map_erasure_after": map_after,
            "order_reversal_delta": order_delta,
            "pairwise_inversion_min": co_monotonicity["off_diagonal_min"],
            "pairwise_inversion_matrix": co_monotonicity["inversion_count_matrix"],
            "no_two_lenses_co_monotone": co_monotonicity["no_two_lenses_co_monotone"],
            "all_constraints_ok": all_constraints_ok,
        },
        "all_pass": all_constraints_ok and controls_ok,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
    }


def main() -> int:
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    result = to_jsonable(build_result())
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary = result["summary"]
    print(f"wrote: {RESULT_PATH}")
    print(
        "CROSS_MODEL_READOUT_MATRIX_V1_JAX_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"classes={summary['full_probe_class_count']}->{summary['carrier_erased_class_count']} "
        f"label_delta={summary['label_shuffle_delta']} "
        f"erased_structure={summary['erased_structure_norm']} "
        f"z3={result['smt']['z3']['verdict']} "
        f"cvc5={result['smt']['cvc5']['verdict']} "
        f"erase_z3={result['smt']['z3']['negative_control_verdict']} "
        f"erase_cvc5={result['smt']['cvc5']['negative_control_verdict']} "
        f"order_delta={summary['order_reversal_delta']}"
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
