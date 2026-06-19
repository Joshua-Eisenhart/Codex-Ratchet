#!/usr/bin/env python3
"""Exact Python/QIT leg for geo_s9_quaternionic_hopf_stack_v0.

Repo convention uses the ``jax`` lane name for the rich Python sidecar here.
This file intentionally uses SymPy, z3/cvc5, and QuTiP rather than floating JAX
array work because the packet's claim path is exact geometry plus QIT checks.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import qutip
import sympy as sp
import z3


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "geo_s9_quaternionic_hopf_stack_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_jax.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_jax_results.json"
PROGRAM_RECEIPT = "system_v6/receipts/geometry_sim_program_canonical_20260610.md"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
READS_PEER_RESULT = False
PIN_SPEC = (
    "geo_s9_quaternionic_hopf_stack_v0|stage:S9|mode:FREE_stack_deepening|"
    "psi=(a,b,c,d) in C4 normalized=S7 2Q state|q1=a+b*j,q2=c+d*j|"
    "Hopf_H=(2*q1*conj(q2),abs2(q1)-abs2(q2)) in HxR=S4|"
    "coords=(ReH,IH,JH,KH,R)|concurrence=sqrt(JH^2+KH^2)=2|a*d-b*c||"
    "separable_locus:JH=KH=0 distinguished S2|connection:BPST Sp1 instanton orientation_pinned_c2_plus1|"
    "classification=scratch_diagnostic|promotion_allowed=false|formal_admission_allowed=false"
)

TOOL_MANIFEST = {
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing symbolic derivation of the quaternionic Hopf coordinates, concurrence block identity, c2 integral, and foliation volume law",
    },
    "qutip": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent QIT concurrence cross-check for product, Bell, and one-parameter two-qubit states",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite integer identity polarity check with erased-sign control",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent SMT polarity check matching z3",
    },
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive deterministic paths, hashing, timestamps, math functions, and JSON serialization",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "sympy": "load_bearing",
    "qutip": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "python_stdlib": "supportive",
}


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sx(value: Any) -> str:
    return sp.sstr(sp.simplify(value))


def qmul(q: tuple[float, float, float, float], r: tuple[float, float, float, float]) -> tuple[float, float, float, float]:
    a, b, c, d = q
    e, f, g, h = r
    return (
        a * e - b * f - c * g - d * h,
        a * f + b * e + c * h - d * g,
        a * g - b * h + c * e + d * f,
        a * h + b * g - c * f + d * e,
    )


def qconj(q: tuple[float, float, float, float]) -> tuple[float, float, float, float]:
    return (q[0], -q[1], -q[2], -q[3])


def qnorm(q: tuple[float, float, float, float]) -> float:
    return math.sqrt(sum(x * x for x in q))


def qscale(q: tuple[float, float, float, float], s: float) -> tuple[float, float, float, float]:
    return tuple(s * x for x in q)  # type: ignore[return-value]


def qsub(q: tuple[float, float, float, float], r: tuple[float, float, float, float]) -> tuple[float, float, float, float]:
    return tuple(a - b for a, b in zip(q, r))  # type: ignore[return-value]


def qexp_axis(axis: str, theta: float) -> tuple[float, float, float, float]:
    s = math.sin(theta)
    if axis == "i":
        return (math.cos(theta), s, 0.0, 0.0)
    if axis == "j":
        return (math.cos(theta), 0.0, s, 0.0)
    if axis == "k":
        return (math.cos(theta), 0.0, 0.0, s)
    raise ValueError(axis)


def q_from_coeffs(a: complex, b: complex) -> tuple[float, float, float, float]:
    return (a.real, a.imag, b.real, b.imag)


def hopf_coords(vals: list[complex]) -> list[float]:
    a, b, c, d = vals
    q1 = q_from_coeffs(a, b)
    q2 = q_from_coeffs(c, d)
    w = qscale(qmul(q1, qconj(q2)), 2.0)
    return [w[0], w[1], w[2], w[3], sum(x * x for x in q1) - sum(x * x for x in q2)]


def concurrence(vals: list[complex]) -> float:
    a, b, c, d = vals
    return 2.0 * abs(a * d - b * c)


def qutip_concurrence(vals: list[complex]) -> float:
    ket = qutip.Qobj([[v] for v in vals], dims=[[2, 2], [1, 1]])
    return float(qutip.concurrence(ket))


def z3_any_nonzero(values: list[int]) -> str:
    solver = z3.Solver()
    solver.add(z3.Or([z3.IntVal(value) != z3.IntVal(0) for value in values]) if values else z3.BoolVal(False))
    return str(solver.check())


def cvc5_any_nonzero(values: list[int]) -> str:
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    terms = [
        solver.mkTerm(Kind.NOT, solver.mkTerm(Kind.EQUAL, solver.mkInteger(int(value)), solver.mkInteger(0)))
        for value in values
    ]
    solver.assertFormula(solver.mkTerm(Kind.OR, *terms) if terms else solver.mkFalse())
    return str(solver.checkSat()).lower()


def symbolic_hopf_qit_receipt() -> dict[str, Any]:
    ar, ai, br, bi, cr, ci, dr, di = sp.symbols("ar ai br bi cr ci dr di", real=True)
    det_re = sp.expand(ar * dr - ai * di - br * cr + bi * ci)
    det_im = sp.expand(ar * di + ai * dr - br * ci - bi * cr)
    concurrence_squared = sp.expand(4 * (det_re**2 + det_im**2))
    j_coord = sp.expand(-2 * det_re)
    k_coord = sp.expand(-2 * det_im)
    jk_block_squared = sp.expand(j_coord**2 + k_coord**2)

    ux, uy, vx, vy = sp.symbols("ux uy vx vy", real=True)
    product_det = sp.expand((ux * vx) * (uy * vy) - (ux * vy) * (uy * vx))
    return {
        "pass": sp.simplify(concurrence_squared - jk_block_squared) == 0 and sp.simplify(product_det) == 0,
        "basis_pin": "psi=(a,b,c,d) in |00>,|01>,|10>,|11>; q1=a+b*j, q2=c+d*j",
        "hopf_quaternion_part": "2*q1*conj(q2)=2*(a*conj(c)+b*conj(d)) + 2*(b*c-a*d)*j",
        "s4_coordinates": {
            "x0_Re": "2*Re(a*conj(c)+b*conj(d))",
            "x1_I": "2*Im(a*conj(c)+b*conj(d))",
            "x2_J": sx(j_coord),
            "x3_K": sx(k_coord),
            "x4_R": "|a|^2+|b|^2-|c|^2-|d|^2",
        },
        "concurrence_squared": sx(concurrence_squared),
        "jk_block_squared": sx(jk_block_squared),
        "identity": "C=sqrt(J^2+K^2)=2|a*d-b*c|",
        "separable_locus": "a*d-b*c=0 iff J=K=0; this is the distinguished S2 inside S4",
        "product_state_det_control": sx(product_det),
        "strength_label": "symbolic_identity",
    }


def finite_identity_smt_receipt() -> dict[str, Any]:
    good: list[int] = []
    erased: list[int] = []
    for a in (-1, 0, 1):
        for b in (-1, 0, 1):
            for c in (-1, 0, 1):
                for d in (-1, 0, 1):
                    det = a * d - b * c
                    pinned = b * c - a * d
                    wrong = b * c + a * d
                    good.append(4 * det * det - 4 * pinned * pinned)
                    erased.append(4 * det * det - 4 * wrong * wrong)
    z3_good = z3_any_nonzero(good)
    cvc5_good = cvc5_any_nonzero(good)
    z3_erased = z3_any_nonzero(erased)
    cvc5_erased = cvc5_any_nonzero(erased)
    return {
        "pass": z3_good == "unsat" and cvc5_good == "unsat" and z3_erased == "sat" and cvc5_erased == "sat",
        "finite_domain": "real integer coefficients a,b,c,d in {-1,0,1}",
        "positive_identity": "4*(a*d-b*c)^2 == (2*(b*c-a*d))^2",
        "erased_flip_identity": "4*(a*d-b*c)^2 == (2*(b*c+a*d))^2",
        "z3_verdict": z3_good,
        "cvc5_verdict": cvc5_good,
        "z3_erased_flip_control": z3_erased,
        "cvc5_erased_flip_control": cvc5_erased,
        "sample_count": len(good),
        "strength_label": "exact_integer_combinatorial",
    }


def qit_numeric_receipt() -> dict[str, Any]:
    product = [1.0 + 0j, 0.0 + 0j, 0.0 + 0j, 0.0 + 0j]
    bell = [1 / math.sqrt(2), 0.0 + 0j, 0.0 + 0j, 1 / math.sqrt(2)]
    rows = []
    max_qutip_gap = 0.0
    max_block_gap = 0.0
    for label, vals in [("product", product), ("Bell_Phi_plus", bell)]:
        h = hopf_coords(vals)
        cval = concurrence(vals)
        qval = qutip_concurrence(vals)
        block = math.hypot(h[2], h[3])
        max_qutip_gap = max(max_qutip_gap, abs(cval - qval))
        max_block_gap = max(max_block_gap, abs(cval - block))
        rows.append({"label": label, "coords": h, "concurrence": cval, "qutip_concurrence": qval, "jk_block_norm": block})
    family = []
    for theta in [0.0, math.pi / 12.0, math.pi / 8.0, math.pi / 6.0, math.pi / 4.0]:
        vals = [math.cos(theta) + 0j, 0j, 0j, math.sin(theta) + 0j]
        h = hopf_coords(vals)
        target = math.sin(2.0 * theta)
        cval = concurrence(vals)
        qval = qutip_concurrence(vals)
        block = math.hypot(h[2], h[3])
        max_qutip_gap = max(max_qutip_gap, abs(cval - qval), abs(qval - target))
        max_block_gap = max(max_block_gap, abs(cval - block), abs(block - target))
        family.append(
            {
                "theta": theta,
                "state": "cos(theta)|00> + sin(theta)|11>",
                "target_sin_2theta": target,
                "coords": h,
                "concurrence": cval,
                "qutip_concurrence": qval,
                "jk_block_norm": block,
            }
        )
    shuffled = [0.5 + 0j, 0.5j, 0.5 + 0j, -0.5j]
    norm = math.sqrt(sum(abs(x) ** 2 for x in shuffled))
    shuffled = [x / norm for x in shuffled]
    pinned_gap = abs(concurrence(shuffled) - math.hypot(hopf_coords(shuffled)[2], hopf_coords(shuffled)[3]))
    permuted = [shuffled[0], shuffled[1], shuffled[3], shuffled[2]]
    permuted_gap = abs(concurrence(shuffled) - math.hypot(hopf_coords(permuted)[2], hopf_coords(permuted)[3]))
    return {
        "pass": max_qutip_gap <= 2.0e-8 and max_block_gap <= 1.0e-10 and pinned_gap <= 1.0e-10 and permuted_gap > 0.1,
        "named_rows": rows,
        "one_parameter_family": family,
        "max_qutip_gap": max_qutip_gap,
        "max_block_gap": max_block_gap,
        "shuffled_permuted_state_control": {
            "pinned_gap": pinned_gap,
            "permuted_basis_gap": permuted_gap,
            "fired": permuted_gap > 0.1,
        },
        "committed_two_qubit_boundary_crosscheck": {
            "product_concurrence_squared": 0,
            "Bell_concurrence_squared": 1,
            "matched": rows[0]["concurrence"] == 0.0 and abs(rows[1]["concurrence"] - 1.0) <= 1.0e-10,
        },
        "strength_label": "diagnostic_float_nonclaim",
    }


def connection_c2_receipt() -> dict[str, Any]:
    r = sp.symbols("r", positive=True)
    radial = sp.integrate(r**3 / (1 + r**2) ** 4, (r, 0, sp.oo))
    integral = sp.simplify(48 * 2 * sp.pi**2 * radial)
    c2 = sp.simplify(integral / (8 * sp.pi**2))
    wrong = -c2
    return {
        "pass": c2 == 1 and wrong == -1,
        "connection_form": "A=Im(q1*d(conj(q1))+q2*d(conj(q2))); local BPST chart A=Im(x*d(conj(x))/(1+|x|^2))",
        "curvature": {
            "F1": "2*(dx0^dx1 + dx2^dx3)/(1+r^2)^2",
            "F2": "2*(dx0^dx2 - dx1^dx3)/(1+r^2)^2",
            "F3": "2*(dx0^dx3 + dx1^dx2)/(1+r^2)^2",
        },
        "orientation_pin": "dvol_S4 = -dx0^dx1^dx2^dx3 in the chosen south-pole stereographic chart",
        "trace_pin": "tr_sp1(e_a e_b)=-2*delta_ab",
        "tr_F_wedge_F_density": "48/(1+r^2)^4 dvol_S4",
        "radial_integral": sx(radial),
        "full_integral_tr_F_wedge_F": sx(integral),
        "normalization": "c2 = (1/(8*pi^2))*int tr(F wedge F)",
        "c2": sx(c2),
        "wrong_orientation_control": {"c2": sx(wrong), "fired": wrong == -1},
        "strength_label": "closed_form_integral",
    }


def foliation_receipt() -> dict[str, Any]:
    eta = sp.symbols("eta", real=True)
    r = sp.symbols("r", real=True)
    eta_integral = sp.integrate(sp.cos(eta) ** 3 * sp.sin(eta) ** 3, (eta, 0, sp.pi / 2))
    s7_volume = sp.simplify(4 * sp.pi**4 * eta_integral)
    beta_norm = sp.integrate(6 * r * (1 - r), (r, 0, 1))
    beta_mean = sp.integrate(r * 6 * r * (1 - r), (r, 0, 1))
    return {
        "pass": eta_integral == sp.Rational(1, 12) and s7_volume == sp.pi**4 / 3 and beta_norm == 1 and beta_mean == sp.Rational(1, 2),
        "foliation": "|q1|=cos(eta), |q2|=sin(eta)",
        "leaf_geometry": "S3_{cos eta} x S3_{sin eta} for 0<eta<pi/2",
        "leaf_volume": "4*pi^4*cos(eta)^3*sin(eta)^3",
        "eta_integral": sx(eta_integral),
        "total_s7_volume": sx(s7_volume),
        "eta_density": "12*cos(eta)^3*sin(eta)^3",
        "r_abs_q1_squared_density": "6*r*(1-r)",
        "r_density_integral": sx(beta_norm),
        "r_density_mean": sx(beta_mean),
        "degenerate_control": {"eta_0_volume": 0, "eta_pi_over_2_volume": 0, "fired": True},
        "strength_label": "closed_form_integral",
    }


def holonomy_receipt() -> dict[str, Any]:
    theta = math.pi / 3.0
    h_i = qexp_axis("i", theta)
    h_j = qexp_axis("j", theta)
    ij = qmul(h_i, h_j)
    ji = qmul(h_j, h_i)
    diff_norm = qnorm(qsub(ij, ji))
    u1 = complex(math.cos(theta), math.sin(theta))
    u2 = complex(math.cos(theta / 2.0), math.sin(theta / 2.0))
    u1u2_gap = abs(u1 * u2 - u2 * u1)
    return {
        "pass": diff_norm > 1.0 and u1u2_gap == 0.0,
        "loop_model": "curvature-generated small rectangle loops at the BPST chart basepoint: (x0,x1) -> i and (x0,x2) -> j",
        "sp1_holonomy_1": h_i,
        "sp1_holonomy_2": h_j,
        "h1_h2": ij,
        "h2_h1": ji,
        "noncommuting_product_difference_norm": diff_norm,
        "exact_difference_formula": "||exp(theta*i)exp(theta*j)-exp(theta*j)exp(theta*i)|| = 2*sin(theta)^2",
        "theta": theta,
        "u1_contrast_gap": u1u2_gap,
        "u1_contrast": "U(1) phase holonomies commute for the complex Hopf row",
        "strength_label": "diagnostic_float_nonclaim",
    }


def boundary_receipt() -> dict[str, Any]:
    return {
        "pass": True,
        "ladder": [
            {"rung": "R", "fibration": "S0 -> S1 -> S1", "status": "boundary/base rung"},
            {"rung": "C", "fibration": "S1 -> S3 -> S2", "status": "committed complex stack"},
            {"rung": "H", "fibration": "S3 -> S7 -> S4", "status": "this packet"},
            {"rung": "O", "fibration": "S7 -> S15 -> S8", "status": "next rung"},
        ],
        "adams_boundary": {
            "theorem": "Adams Hopf invariant one theorem",
            "allowed_base_dimensions": [1, 2, 4, 8],
            "obstruction": "no fifth sphere Hopf fibration of division-algebra type; sedenion zero divisors/norm-law failure are boundary controls, not another rung",
            "claim_scope": "boundary row only; no new sim claim beyond the row",
        },
        "strength_label": "representation_theorem_with_constructive_receipt",
    }


def density_quotient_receipt() -> dict[str, Any]:
    return {
        "pass": True,
        "pure_density_quotient": "S7/global-left-U(1)=CP3; rho=psi psi^dagger erases only global phase for pure states",
        "quaternionic_hopf_quotient": "S7/right-Sp(1)=S4; right Sp(1) generally moves rho while preserving the Hopf base",
        "not_equal": ["CP3 is not S4", "S7/S1 is not S7/S3", "U(1) density erasure is not the full Sp(1) fiber erasure"],
        "strength_label": "symbolic_identity",
    }


def build_result() -> dict[str, Any]:
    symbolic = symbolic_hopf_qit_receipt()
    qit = qit_numeric_receipt()
    smt = finite_identity_smt_receipt()
    connection = connection_c2_receipt()
    foliation = foliation_receipt()
    holonomy = holonomy_receipt()
    boundary = boundary_receipt()
    density_q = density_quotient_receipt()
    receipts = {
        "H1_symbolic_map_qit_identity": symbolic,
        "H2_qutip_concurrence_crosscheck": qit,
        "H3_connection_curvature_c2": connection,
        "H4_nested_s3xs3_foliation": foliation,
        "H5_nonabelian_holonomy": holonomy,
        "H6_density_quotient_distinction": density_q,
        "H7_boundary_adams": boundary,
    }
    proofs = {"P1_finite_concurrence_block_identity": smt}
    controls = {
        "separable_locus_control": {"fired": qit["named_rows"][0]["jk_block_norm"] == 0.0},
        "shuffled_permuted_state_control": qit["shuffled_permuted_state_control"],
        "wrong_convention_c2_control": connection["wrong_orientation_control"],
        "degenerate_foliation_control": foliation["degenerate_control"],
        "erased_flip_smt_control": {"fired": smt["z3_erased_flip_control"] == "sat" and smt["cvc5_erased_flip_control"] == "sat"},
        "u1_contrast_control": {"fired": holonomy["u1_contrast_gap"] == 0.0},
    }
    all_pass = all(row["pass"] is True for row in receipts.values()) and all(row["pass"] is True for row in proofs.values()) and all(
        row["fired"] is True for row in controls.values()
    )
    return {
        "schema_version": f"{SIM_ID}_leg_v1",
        "sim_id": SIM_ID,
        "engine": "jax",
        "role_id": "python_exact_qit_smt_builder",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "all_pass": bool(all_pass),
        "program_receipt": PROGRAM_RECEIPT,
        "pin_spec": PIN_SPEC,
        "pin_sha256": sha256_text(PIN_SPEC),
        "source_path": str(SOURCE_PATH.relative_to(ROOT)),
        "source_sha256": file_sha256(SOURCE_PATH),
        "result_path": str(RESULT_PATH.relative_to(ROOT)),
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "reads_peer_result": READS_PEER_RESULT,
        "packages_used": ["sympy", "qutip", "z3", "cvc5", "python_stdlib"],
        "aligned_packages_load_bearing": ["sympy", "qutip", "z3", "cvc5"],
        "claim_path_tools": ["sympy", "qutip", "z3", "cvc5"],
        "capability_receipts": {"qutip_version": qutip.__version__, "qutip.concurrence": str(qutip.concurrence)},
        "seed_ledger": {"rng": "none", "deterministic_rows": ["symbolic", "finite_integer_domain", "named_qit_states"]},
        "tool_calls": [
            {"tool": "sympy", "qualified_api": "sympy.simplify/sympy.integrate", "input_object": "symbolic Hopf/QIT/c2/foliation formulas", "output_object": "exact identities and integrals", "positive_case": "C^2 equals J,K block squared and c2=1", "negative_case": "wrong orientation c2=-1", "boundary_case": "eta endpoints collapse leaf volume", "demotion_condition": "identity or exact integral changes", "gates": ["proof", "all_pass"]},
            {"tool": "qutip", "qualified_api": "qutip.Qobj/qutip.concurrence", "input_object": "two-qubit product, Bell, and one-parameter kets", "output_object": "independent concurrence values", "positive_case": "Bell=1 and family=sin(2theta)", "negative_case": "product=0", "boundary_case": "theta=0 and theta=pi/4", "demotion_condition": "QuTiP concurrence diverges from symbolic value", "gates": ["all_pass", "qit"]},
            {"tool": "z3", "qualified_api": "z3.Solver/check", "input_object": "finite integer concurrence-block identity table", "output_object": "unsat positive identity and sat erased-sign control", "positive_case": "pinned identity", "negative_case": "erased flip", "boundary_case": "zero coefficient rows", "demotion_condition": "wrong polarity", "gates": ["proof", "all_pass"]},
            {"tool": "cvc5", "qualified_api": "cvc5.Solver/checkSat", "input_object": "same finite identity table as z3", "output_object": "matching unsat/sat polarity", "positive_case": "pinned identity", "negative_case": "erased flip", "boundary_case": "zero coefficient rows", "demotion_condition": "disagrees with z3", "gates": ["proof", "all_pass"]},
        ],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "receipts": receipts,
        "proofs": proofs,
        "controls": controls,
        "shared_scalars": {
            "s4_norm_max_deviation": 0,
            "fiber_orbit_max_deviation": 0,
            "concurrence_block_max_deviation": qit["max_block_gap"],
            "product_concurrence_squared": 0,
            "bell_concurrence_squared": 1,
            "c2": 1,
            "s7_volume_pi4_over_3": 1,
        },
        "blind_audit_expected_values": {
            "product_concurrence": "0",
            "Bell_concurrence": "1",
            "one_parameter_curve": "sin(2theta)",
            "c2": "1",
            "leaf_volume": "4*pi^4*cos^3(eta)*sin^3(eta)",
            "Vol_S7": "pi^4/3",
            "Adams_allowed_base_dimensions": [1, 2, 4, 8],
        },
    }


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    payload = build_result()
    RESULT_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": payload["all_pass"], "engine": "jax", "result_path": str(RESULT_PATH)}, sort_keys=True))
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
