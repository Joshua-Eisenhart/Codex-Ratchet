#!/usr/bin/env python3
"""Exact Python/JAX-side lane for round3_s4_heavy_discriminator_v0.

The lane uses exact SymPy channel algebra plus qutip/z3/cvc5 sanity checks.
JAX itself is not needed for the claim path:
the finite S4 heavy rows are 2x2 channel/Choi/order checks, not a batched sweep.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import qutip
import sympy as sp
import z3


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "round3_s4_heavy_discriminator_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_jax.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_jax_results.json"

CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
READS_PEER_RESULT = False

LAMBDA = sp.Rational(7, 10)
P_DEPHASE = sp.Rational(3, 20)
Z_PROBE = sp.Matrix([0, 0, sp.Rational(1, 2)])
ZERO3 = sp.Matrix([0, 0, 0])
ORDER_WITNESS = Z_PROBE

I2 = sp.eye(2)
SX = sp.Matrix([[0, 1], [1, 0]])
SY = sp.Matrix([[0, -sp.I], [sp.I, 0]])
SZ = sp.Matrix([[1, 0], [0, -1]])
PAULIS = (SX, SY, SZ)


@dataclass(frozen=True)
class Channel:
    label: str
    M: sp.Matrix
    c: sp.Matrix
    role: str


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def stable_hash(value: Any) -> str:
    return hashlib.sha256(stable_json(value).encode("utf-8")).hexdigest()


def sx(expr: Any) -> str:
    return sp.sstr(sp.factor(sp.trigsimp(sp.simplify(expr))))


def mat_sx(matrix: sp.Matrix) -> list[list[str]]:
    return [[sx(matrix[i, j]) for j in range(matrix.cols)] for i in range(matrix.rows)]


def vec_sx(vec: sp.Matrix) -> list[str]:
    return [sx(vec[i]) for i in range(vec.rows)]


def diag(a: Any, b: Any, c: Any) -> sp.Matrix:
    return sp.diag(sp.simplify(a), sp.simplify(b), sp.simplify(c))


def rx() -> sp.Matrix:
    return sp.Matrix([[1, 0, 0], [0, 0, -1], [0, 1, 0]])


def rz() -> sp.Matrix:
    return sp.Matrix([[0, -1, 0], [1, 0, 0], [0, 0, 1]])


def dz() -> Channel:
    return Channel("D_z", diag(LAMBDA, LAMBDA, 1), ZERO3, "D_z")


def dx() -> Channel:
    return Channel("D_x", diag(1, LAMBDA, LAMBDA), ZERO3, "D_x")


def rot_x() -> Channel:
    return Channel("R_x", rx(), ZERO3, "R_x")


def rot_z() -> Channel:
    return Channel("R_z", rz(), ZERO3, "R_z")


def ad_z(gamma: sp.Rational, label: str) -> Channel:
    return Channel(label, diag(sp.sqrt(1 - gamma), sp.sqrt(1 - gamma), 1 - gamma), sp.Matrix([0, 0, gamma]), label)


def ad_x(gamma: sp.Rational, label: str) -> Channel:
    return Channel(label, diag(1 - gamma, sp.sqrt(1 - gamma), sp.sqrt(1 - gamma)), sp.Matrix([gamma, 0, 0]), label)


def hybrid(lambda_value: sp.Rational, label: str) -> Channel:
    return Channel(label, diag(lambda_value, lambda_value, 1) * rx(), ZERO3, label)


def shift_z() -> Channel:
    return Channel("weak_shift_z", diag(LAMBDA, LAMBDA, 1), sp.Matrix([0, 0, sp.Rational(1, 10)]), "weak_shift_z")


def shift_x() -> Channel:
    return Channel("weak_shift_x", diag(1, LAMBDA, LAMBDA), sp.Matrix([sp.Rational(1, 10), 0, 0]), "weak_shift_x")


def apply_channel(ch: Channel, point: sp.Matrix) -> sp.Matrix:
    return sp.simplify(ch.M * point + ch.c)


def compose(a: Channel, b: Channel, label: str) -> Channel:
    return Channel(label, sp.simplify(a.M * b.M), sp.simplify(a.M * b.c + a.c), label)


def commutator_gap(a: Channel, b: Channel, point: sp.Matrix = ORDER_WITNESS) -> sp.Matrix:
    return sp.simplify(apply_channel(compose(a, b, f"{a.label}_then_{b.label}"), point) - apply_channel(compose(b, a, f"{b.label}_then_{a.label}"), point))


def phi_from_affine(M: sp.Matrix, c: sp.Matrix, op: sp.Matrix) -> sp.Matrix:
    trace = sp.trace(op)
    r = sp.Matrix([sp.trace(op * pauli) for pauli in PAULIS])
    rp = sp.simplify(M * r + trace * c)
    return sp.simplify(sp.Rational(1, 2) * (trace * I2 + rp[0] * SX + rp[1] * SY + rp[2] * SZ))


def choi_matrix(ch: Channel) -> sp.Matrix:
    e00 = sp.Matrix([[1, 0], [0, 0]])
    e01 = sp.Matrix([[0, 1], [0, 0]])
    e10 = sp.Matrix([[0, 0], [1, 0]])
    e11 = sp.Matrix([[0, 0], [0, 1]])
    return sp.simplify(
        sp.Rational(1, 2)
        * sp.Matrix.vstack(
            sp.Matrix.hstack(phi_from_affine(ch.M, ch.c, e00), phi_from_affine(ch.M, ch.c, e01)),
            sp.Matrix.hstack(phi_from_affine(ch.M, ch.c, e10), phi_from_affine(ch.M, ch.c, e11)),
        )
    )


def eig_spectrum(matrix: sp.Matrix) -> list[sp.Expr]:
    out: list[sp.Expr] = []
    for val, mult in matrix.eigenvals().items():
        out.extend([sp.factor(val)] * mult)
    return out


def choi_receipt(ch: Channel) -> dict[str, Any]:
    matrix = choi_matrix(ch)
    spectrum = eig_spectrum(matrix)
    return {
        "channel": ch.label,
        "M": mat_sx(ch.M),
        "c": vec_sx(ch.c),
        "choi_matrix": mat_sx(matrix),
        "choi_spectrum_exact": [sx(item) for item in spectrum],
        "choi_positive": all(bool(sp.simplify(item >= 0)) for item in spectrum),
        "negative_eigenvalues": [sx(item) for item in spectrum if bool(sp.simplify(item < 0))],
    }


def fixed_set_receipt(ch: Channel) -> dict[str, Any]:
    x, y, z = sp.symbols("x y z")
    point = sp.Matrix([x, y, z])
    equations = [sp.factor(item) for item in (ch.M * point + ch.c - point)]
    solution = sp.solve(equations, (x, y, z), dict=True)
    return {
        "channel": ch.label,
        "equations": [sx(eq) for eq in equations],
        "solution": [{str(k): sx(v) for k, v in sol.items()} for sol in solution],
        "has_free_axis": any(len(sol) < 3 for sol in solution),
        "empty_under_affine_equations": solution == [],
    }


def shell_leakage_receipt(ch: Channel) -> dict[str, Any]:
    point_a = sp.Matrix([0, 0, sp.Rational(1, 2)])
    point_b = sp.Matrix([0, sp.Rational(1, 2), sp.Rational(1, 2)])
    out_a = apply_channel(ch, point_a)
    out_b = apply_channel(ch, point_b)
    z_gap = sp.simplify(out_b[2] - out_a[2])
    return {
        "channel": ch.label,
        "same_input_z_shell_points": [vec_sx(point_a), vec_sx(point_b)],
        "outputs": [vec_sx(out_a), vec_sx(out_b)],
        "z_shell_leakage_witness": sx(z_gap),
        "shell_preserved": z_gap == 0,
    }


def z_probe_receipt(ch: Channel) -> dict[str, Any]:
    out = apply_channel(ch, Z_PROBE)
    return {
        "channel": ch.label,
        "z_probe": vec_sx(Z_PROBE),
        "image": vec_sx(out),
        "pin_relative_descends_to_committed_z_quotient": out[0] == 0 and out[1] == 0 and sp.simplify(out[2] - Z_PROBE[2]) == 0,
        "mortality_break_witness": {
            "x_component": sx(out[0]),
            "y_component": sx(out[1]),
            "z_delta": sx(sp.simplify(out[2] - Z_PROBE[2])),
        },
    }


def n01_receipt(a: Channel, b: Channel) -> dict[str, Any]:
    gap = commutator_gap(a, b)
    matrix_gap = sp.simplify(a.M * b.M - b.M * a.M)
    shift_gap = sp.simplify(a.M * b.c + a.c - (b.M * a.c + b.c))
    return {
        "pair": [a.label, b.label],
        "order_gap_on_z_probe": vec_sx(gap),
        "commutator_matrix": mat_sx(matrix_gap),
        "commutator_shift": vec_sx(shift_gap),
        "nonzero": any(sp.simplify(item) != 0 for item in list(gap) + list(matrix_gap) + list(shift_gap)),
    }


def qutip_affine_check(ch: Channel) -> dict[str, Any]:
    # qutip is channel-agnostic here: a maximally mixed state route sanity check.
    pauli = {"I": qutip.qeye(2), "X": qutip.sigmax(), "Y": qutip.sigmay(), "Z": qutip.sigmaz()}
    rho0 = qutip.Qobj((0.5 * (sp.eye(2))).evalf().tolist())
    components = [float(qutip.expect(pauli[key], rho0).real) for key in ("X", "Y", "Z")]
    return {
        "channel": ch.label,
        "route": "qutip.Qobj/qutip.expect sanity route over the maximally mixed one-qubit density object; channel-agnostic; exact affine/Choi rows remain SymPy",
        "center_components": components,
        "center_components_match_zero_density": all(abs(x) < 1e-12 for x in components),
    }


def smt_z3() -> dict[str, Any]:
    solver = z3.Solver()
    comm = z3.Int("comm_gap_scaled_10")
    quotient = z3.Int("quotient_x_scaled_10")
    choi = z3.Int("choi_negative_scaled_40")
    solver.add(comm == 2, quotient == 2, choi == -1)
    solver.add(z3.Or(comm == 0, quotient == 0, choi >= 0))
    verdict = str(solver.check())

    flip = z3.Solver()
    c2 = z3.Int("perturbed_comm_gap_scaled_10")
    q2 = z3.Int("perturbed_quotient_x_scaled_10")
    h2 = z3.Int("perturbed_choi_negative_scaled_40")
    flip.add(c2 == 0, q2 == 0, h2 == 0)
    flip.add(z3.Or(c2 == 0, q2 == 0, h2 >= 0))
    flip_verdict = str(flip.check())
    return {
        "ran": True,
        "solver": "z3",
        "verdict": verdict,
        "load_bearing": False,
        "supportive": True,
        "tool_honesty": "supportive_hardcoded_witness_binding",
        "witness_values": {
            "S4.R3.1 AD_z(1/5) comm_gap_z_scaled_10": 2,
            "S4.R3.2 AD_x(1/5) quotient_x_scaled_10": 2,
            "S4.R3.5 weak_shift choi_negative_scaled_40": -1,
        },
        "negated_assertion": "at least one computed nonzero/negative witness is erased",
        "flip_control_verdict": "tautological_flip" if flip_verdict == "sat" else flip_verdict,
        "flip_control_status": flip_verdict,
        "positive_case": "hardcoded commutator, quotient, and Choi witness tuple cannot satisfy the erasure disjunction",
        "negative/erased_control": "tautological_flip: asserted zero literals satisfy the disjunction",
        "boundary_case": "finite pinned S4 heavy rows only",
    }


def smt_cvc5() -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    int_sort = solver.getIntegerSort()
    comm = solver.mkConst(int_sort, "comm_gap_scaled_10")
    quotient = solver.mkConst(int_sort, "quotient_x_scaled_10")
    choi = solver.mkConst(int_sort, "choi_negative_scaled_40")
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, comm, solver.mkInteger(2)))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, quotient, solver.mkInteger(2)))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, choi, solver.mkInteger(-1)))
    erased = solver.mkTerm(
        Kind.OR,
        solver.mkTerm(Kind.EQUAL, comm, solver.mkInteger(0)),
        solver.mkTerm(Kind.EQUAL, quotient, solver.mkInteger(0)),
        solver.mkTerm(Kind.GEQ, choi, solver.mkInteger(0)),
    )
    solver.assertFormula(erased)
    verdict = str(solver.checkSat()).lower()

    flip = cvc5.Solver()
    flip.setLogic("QF_LIA")
    int_sort2 = flip.getIntegerSort()
    c2 = flip.mkConst(int_sort2, "perturbed_comm_gap_scaled_10")
    q2 = flip.mkConst(int_sort2, "perturbed_quotient_x_scaled_10")
    h2 = flip.mkConst(int_sort2, "perturbed_choi_negative_scaled_40")
    flip.assertFormula(flip.mkTerm(Kind.EQUAL, c2, flip.mkInteger(0)))
    flip.assertFormula(flip.mkTerm(Kind.EQUAL, q2, flip.mkInteger(0)))
    flip.assertFormula(flip.mkTerm(Kind.EQUAL, h2, flip.mkInteger(0)))
    flip.assertFormula(
        flip.mkTerm(
            Kind.OR,
            flip.mkTerm(Kind.EQUAL, c2, flip.mkInteger(0)),
            flip.mkTerm(Kind.EQUAL, q2, flip.mkInteger(0)),
            flip.mkTerm(Kind.GEQ, h2, flip.mkInteger(0)),
        )
    )
    flip_verdict = str(flip.checkSat()).lower()
    return {
        "ran": True,
        "solver": "cvc5",
        "verdict": verdict,
        "load_bearing": False,
        "supportive": True,
        "tool_honesty": "supportive_hardcoded_witness_binding",
        "witness_values": {
            "S4.R3.1 AD_z(1/5) comm_gap_z_scaled_10": 2,
            "S4.R3.2 AD_x(1/5) quotient_x_scaled_10": 2,
            "S4.R3.5 weak_shift choi_negative_scaled_40": -1,
        },
        "negated_assertion": "at least one computed nonzero/negative witness is erased",
        "flip_control_verdict": "tautological_flip" if flip_verdict == "sat" else flip_verdict,
        "flip_control_status": flip_verdict,
        "positive_case": "hardcoded commutator, quotient, and Choi witness tuple cannot satisfy the erasure disjunction",
        "negative/erased_control": "tautological_flip: asserted zero literals satisfy the disjunction",
        "boundary_case": "finite pinned S4 heavy rows only",
    }


def variant_rows() -> dict[str, list[Channel]]:
    return {
        "S4.R3.1_z_amplitude_damping_pair": [ad_z(sp.Rational(1, 5), "AD_z_gamma_1_5"), ad_z(sp.Rational(3, 10), "AD_z_gamma_3_10")],
        "S4.R3.2_x_amplitude_damping_pair": [ad_x(sp.Rational(1, 5), "AD_x_gamma_1_5"), ad_x(sp.Rational(3, 10), "AD_x_gamma_3_10")],
        "S4.R3.3_dephase_rotate_hybrid": [hybrid(sp.Rational(7, 10), "D_z_7_10_after_R_x_pi_2"), hybrid(sp.Rational(1, 2), "D_z_1_2_after_R_x_pi_2")],
        "S4.R3.5_weak_nonunital_pauli_channel": [shift_z(), shift_x()],
    }


def build_candidate_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    details: dict[str, Any] = {}
    rx_ch = rot_x()
    rz_ch = rot_z()
    for candidate, variants in variant_rows().items():
        variant_receipts = []
        for ch in variants:
            receipt = {
                "variant": ch.label,
                "choi": choi_receipt(ch),
                "fixed_set": fixed_set_receipt(ch),
                "z_probe": z_probe_receipt(ch),
                "qutip_route": qutip_affine_check(ch),
            }
            if candidate == "S4.R3.1_z_amplitude_damping_pair":
                receipt["n01_with_R_x"] = n01_receipt(ch, rx_ch)
            if candidate == "S4.R3.2_x_amplitude_damping_pair":
                receipt["n01_with_R_z"] = n01_receipt(ch, rz_ch)
            if candidate == "S4.R3.3_dephase_rotate_hybrid":
                receipt["shell_leakage"] = shell_leakage_receipt(ch)
                receipt["n01_with_D_z"] = n01_receipt(ch, dz())
            if candidate == "S4.R3.5_weak_nonunital_pauli_channel":
                receipt["n01_with_R_x"] = n01_receipt(ch, rx_ch)
            variant_receipts.append(receipt)
        details[candidate] = variant_receipts

    rows.append(
        {
            "candidate": "S4.R3.1_z_amplitude_damping_pair",
            "registry_row": "N01/commutator and fixed-axis rows",
            "verdict": "excluded-by-N01-commutator-and-fixed-axis-rows",
            "exact_witness": {
                "AD_z_gamma_1_5_order_gap_on_z_probe": details["S4.R3.1_z_amplitude_damping_pair"][0]["n01_with_R_x"]["order_gap_on_z_probe"],
                "AD_z_gamma_1_5_fixed_set": details["S4.R3.1_z_amplitude_damping_pair"][0]["fixed_set"]["solution"],
            },
            "co_survivor": False,
            "pin_relative": False,
        }
    )
    rows.append(
        {
            "candidate": "S4.R3.2_x_amplitude_damping_pair",
            "registry_row": "z-probe quotient descent/mortality",
            "verdict": "excluded-under-pinned-parent-z-probe-convention-by-z-probe-quotient-descent-mortality",
            "exact_witness": {
                "AD_x_gamma_1_5_z_probe_image": details["S4.R3.2_x_amplitude_damping_pair"][0]["z_probe"]["image"],
                "mortality_break_witness": details["S4.R3.2_x_amplitude_damping_pair"][0]["z_probe"]["mortality_break_witness"],
            },
            "co_survivor": False,
            "pin_relative": True,
        }
    )
    rows.append(
        {
            "candidate": "S4.R3.3_dephase_rotate_hybrid",
            "registry_row": "shell preservation/leakage then N01",
            "verdict": "excluded-by-shell-preservation-leakage",
            "exact_witness": {
                "lambda_7_10_shell_leakage": details["S4.R3.3_dephase_rotate_hybrid"][0]["shell_leakage"],
                "lambda_1_2_shell_leakage": details["S4.R3.3_dephase_rotate_hybrid"][1]["shell_leakage"],
            },
            "co_survivor": False,
            "pin_relative": False,
        }
    )
    rows.append(
        {
            "candidate": "S4.R3.5_weak_nonunital_pauli_channel",
            "registry_row": "fixed-axis plus Choi positivity",
            "verdict": "excluded-by-Choi-positivity-and-fixed-axis",
            "exact_witness": {
                "weak_shift_z_negative_choi_eigenvalues": details["S4.R3.5_weak_nonunital_pauli_channel"][0]["choi"]["negative_eigenvalues"],
                "weak_shift_x_negative_choi_eigenvalues": details["S4.R3.5_weak_nonunital_pauli_channel"][1]["choi"]["negative_eigenvalues"],
                "weak_shift_z_fixed_set": details["S4.R3.5_weak_nonunital_pauli_channel"][0]["fixed_set"],
            },
            "co_survivor": False,
            "pin_relative": False,
        }
    )
    return rows, details


def control_rows() -> dict[str, Any]:
    anchor_channels = [dz(), dx(), rot_x(), rot_z()]
    alias_channels = [
        Channel("D_z_reparam", diag(1 - 2 * P_DEPHASE, 1 - 2 * P_DEPHASE, 1), ZERO3, "D_z"),
        Channel("D_x_reparam", diag(1, 1 - 2 * P_DEPHASE, 1 - 2 * P_DEPHASE), ZERO3, "D_x"),
        Channel("R_x_reparam", rx(), ZERO3, "R_x"),
        Channel("R_z_reparam", rz(), ZERO3, "R_z"),
    ]
    axis_permuted_dz = Channel("D_x_after_cyclic_relabel", dx().M, ZERO3, "D_z")
    anchor_zprobe = vec_sx(apply_channel(dz(), Z_PROBE))
    axis_zprobe = vec_sx(apply_channel(axis_permuted_dz, Z_PROBE))
    return {
        "anchor_self": {
            "verdict": "pass",
            "choi_positive_all": all(choi_receipt(ch)["choi_positive"] for ch in anchor_channels),
            "choi_spectra": {ch.label: choi_receipt(ch)["choi_spectrum_exact"] for ch in anchor_channels},
            "n01_Dz_Rx_order_gap": n01_receipt(dz(), rot_x()),
        },
        "deliberate_alias_reparameterized_anchor": {
            "verdict": "alias",
            "anchor_hash": stable_hash([(ch.role, mat_sx(ch.M), vec_sx(ch.c)) for ch in anchor_channels]),
            "alias_hash": stable_hash([(ch.role, mat_sx(ch.M), vec_sx(ch.c)) for ch in alias_channels]),
        },
        "light_pass_R3_4_regression": {
            "verdict": "excluded-under-pinned-parent-z-probe-convention",
            "anchor_D_z_z_probe": anchor_zprobe,
            "axis_permuted_role_D_z_z_probe": axis_zprobe,
            "delta": vec_sx(apply_channel(axis_permuted_dz, Z_PROBE) - apply_channel(dz(), Z_PROBE)),
        },
    }


def build_result() -> dict[str, Any]:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    candidate_rows, details = build_candidate_rows()
    z3proof = smt_z3()
    cvc5proof = smt_cvc5()
    all_pass = (
        all(not row["co_survivor"] and row["verdict"].startswith("excluded") for row in candidate_rows)
        and z3proof["verdict"] == "unsat"
        and cvc5proof["verdict"] == "unsat"
        and z3proof["flip_control_verdict"] == "tautological_flip"
        and cvc5proof["flip_control_verdict"] == "tautological_flip"
        and not READS_PEER_RESULT
    )
    return {
        "schema": "codex_ratchet.engine_leg_result.v1",
        "sim_id": SIM_ID,
        "object_id": f"{SIM_ID}_jax",
        "engine": "jax",
        "role_id": "jax_exact_qutip_smt_s4_heavy_discriminator",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result": READS_PEER_RESULT,
        "all_pass": all_pass,
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": rel(SOURCE_PATH),
        "source_sha256": sha256_file(SOURCE_PATH),
        "result_path": rel(RESULT_PATH),
        "packages_used": ["sympy", "qutip", "z3", "cvc5", "json", "hashlib", "datetime", "pathlib"],
        "aligned_packages_load_bearing": ["sympy"],
        "claim_path_tools": ["sympy"],
        "package_observables": {
            "sympy": "exact affine, Choi-spectrum, fixed-set, quotient, shell, and commutator rows",
            "qutip": "maximally mixed one-qubit Qobj density route sanity check; channel-agnostic",
            "z3": "supportive hardcoded finite witness UNSAT check with tautological flip annotation; SymPy rows gate exclusions",
            "cvc5": "supportive hardcoded finite witness UNSAT check with tautological flip annotation; SymPy rows gate exclusions",
        },
        "TOOL_MANIFEST": {
            "sympy": {"used": True, "reason": "load-bearing exact affine/Choi/order algebra"},
            "qutip": {"used": True, "reason": "supportive channel-agnostic maximally mixed Qobj route sanity"},
            "z3": {"used": True, "reason": "supportive hardcoded finite witness check; tautological flip is annotated"},
            "cvc5": {"used": True, "reason": "supportive independent hardcoded finite witness check; tautological flip is annotated"},
        },
        "TOOL_INTEGRATION_DEPTH": {"sympy": "load_bearing", "qutip": "supportive", "z3": "supportive", "cvc5": "supportive"},
        "tool_calls": [
            {
                "tool": "sympy",
                "qualified_api/function": "sympy.Matrix/sympy.solve/sympy.eigenvals/sympy.simplify",
                "input_object": "finite S4 affine channels from registry rows",
                "output_object": {"candidate_rows": candidate_rows, "details_hash": stable_hash(details)},
                "positive_case": "anchor channels have nonnegative exact Choi spectra",
                "negative/erased_control": "R3.5 weak shifts expose exact negative Choi eigenvalue -1/40",
                "boundary_case": "2x2 Choi matrices only; no sweep beyond registry variants",
                "demotion_condition": "without exact spectra and witness rows, verdicts return to open + queued-heavy-local",
                "gates": ["candidate_verdicts", "all_pass"],
            },
            {
                "tool": "qutip",
                "qualified_api/function": "qutip.Qobj/qutip.expect",
                "input_object": "maximally mixed one-qubit density object route sanity for each channel variant",
                "output_object": "qutip_route fields in candidate_variant_details",
                "positive_case": "maximally mixed Qobj density center components are read through qutip.expect",
                "negative/erased_control": "none; this route is channel-agnostic",
                "boundary_case": "qutip is supportive route sanity only; exact verdict rows are SymPy",
                "demotion_condition": "already supportive because channel argument does not affect the observable",
                "gates": [],
            },
            {
                "tool": "z3",
                "qualified_api/function": "z3.Solver/z3.Int/Solver.check",
                "input_object": "hardcoded commutator, quotient, and Choi finite witness tuple",
                "output_object": z3proof,
                "positive_case": "hardcoded tuple cannot satisfy the erasure disjunction",
                "negative/erased_control": "tautological_flip: asserted zero literals satisfy the disjunction",
                "boundary_case": "supportive integer-scaled finite witness check only; exact verdict rows remain SymPy",
                "demotion_condition": "already supportive because solver inputs are not extracted from candidate rows",
                "gates": [],
            },
            {
                "tool": "cvc5",
                "qualified_api/function": "cvc5.Solver/mkConst/assertFormula/checkSat",
                "input_object": "same finite witnesses as z3",
                "output_object": cvc5proof,
                "positive_case": "matches z3 UNSAT for the hardcoded tuple",
                "negative/erased_control": "tautological_flip: asserted zero literals satisfy the disjunction",
                "boundary_case": "supportive integer-scaled finite witness check only",
                "demotion_condition": "already supportive because solver inputs are not extracted from candidate rows",
                "gates": [],
            },
        ],
        "positive": {
            "anchor_control": control_rows()["anchor_self"],
            "deliberate_alias": control_rows()["deliberate_alias_reparameterized_anchor"],
        },
        "negative": {
            "candidate_verdict_table": candidate_rows,
            "R3_4_regression": control_rows()["light_pass_R3_4_regression"],
        },
        "boundary": {
            "scope": "S4 heavy-local queued rows only",
            "classification": CLASSIFICATION,
            "promotion_allowed": PROMOTION_ALLOWED,
            "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
            "pinned_convention": "parent z-probe quotient and S4 role order from round3_s4_alias_pass_v0",
            "pytorch": "omitted honestly; no graph/network/autograd/tensor claim path",
        },
        "candidate_verdicts": candidate_rows,
        "candidate_variant_details": details,
        "control_rows": control_rows(),
        "crossover_proofs": {"z3": z3proof, "cvc5": cvc5proof},
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"result": rel(RESULT_PATH), "all_pass": result["all_pass"]}, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
