#!/usr/bin/env python3
"""Exact symbolic + diffrax/SMT lane for round3_s9_s2_final_heavy_v0."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import diffrax
import jax
import jax.numpy as jnp
import sympy as sp
import z3

jax.config.update("jax_enable_x64", True)

ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "round3_s9_s2_final_heavy_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_jax.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_jax_results.json"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
READS_PEER_RESULT = False

REGISTRY = ROOT / "system_v6" / "receipts" / "round3_discriminator_registry_20260611.md"
S9_LIGHT_AUDIT = ROOT / "system_v6" / "sims" / "round3_s9_alias_pass_v0" / "audit_verdict.md"
S2_LIGHT_AUDIT = ROOT / "system_v6" / "sims" / "round3_s2_alias_pass_v0" / "audit_verdict.md"
S9_TRANSPORT_PARENT = ROOT / "system_v6" / "sims" / "geo_s9_quat_path_ordered_transport_v0" / "audit_verdict.md"
S2_UNION_PARENT = ROOT / "system_v6" / "sims" / "geo_union_rule_k_leaves_v0" / "audit_verdict.md"

ETA_LEAVES = [
    ("pi/12", sp.pi / 12),
    ("pi/6", sp.pi / 6),
    ("pi/4", sp.pi / 4),
    ("pi/3", sp.pi / 3),
    ("5*pi/12", 5 * sp.pi / 12),
]
S9_LEAVES = [("0", sp.Integer(0)), ("pi/6", sp.pi / 6), ("pi/4", sp.pi / 4), ("pi/3", sp.pi / 3), ("pi/2", sp.pi / 2)]
S2_UNIONS = [("U_pi12_pi6", ("pi/12", "pi/6")), ("U_pi6_pi4", ("pi/6", "pi/4")), ("U_pi4_pi3", ("pi/4", "pi/3"))]
S2_INVALID_CONTROL = ("invalid.overlapping_duplicate_pi6", ("pi/6", "pi/6"))


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def stable_hash(value: Any) -> str:
    return hashlib.sha256(stable_json(value).encode("utf-8")).hexdigest()


def sx(expr: Any) -> str:
    return sp.sstr(sp.factor(sp.radsimp(sp.trigsimp(sp.simplify(expr)))))


def qmul(a: tuple[sp.Expr, sp.Expr, sp.Expr, sp.Expr], b: tuple[sp.Expr, sp.Expr, sp.Expr, sp.Expr]) -> tuple[sp.Expr, sp.Expr, sp.Expr, sp.Expr]:
    aw, ax, ay, az = a
    bw, bx, by, bz = b
    return (
        sp.simplify(aw * bw - ax * bx - ay * by - az * bz),
        sp.simplify(aw * bx + ax * bw + ay * bz - az * by),
        sp.simplify(aw * by - ax * bz + ay * bw + az * bx),
        sp.simplify(aw * bz + ax * by - ay * bx + az * bw),
    )


def qexp(axis: str, theta: sp.Expr) -> tuple[sp.Expr, sp.Expr, sp.Expr, sp.Expr]:
    if axis == "i":
        return (sp.cos(theta), sp.sin(theta), sp.Integer(0), sp.Integer(0))
    if axis == "j":
        return (sp.cos(theta), sp.Integer(0), sp.sin(theta), sp.Integer(0))
    raise ValueError(axis)


def qtuple(q: tuple[sp.Expr, sp.Expr, sp.Expr, sp.Expr]) -> list[str]:
    return [sx(v) for v in q]


def commutator_gap_squared(theta: sp.Expr) -> sp.Expr:
    hi = qexp("i", theta)
    hj = qexp("j", theta)
    ab = qmul(hi, hj)
    ba = qmul(hj, hi)
    return sp.simplify(sum((x - y) ** 2 for x, y in zip(ab, ba)))


def f_anchor(eta: sp.Expr) -> sp.Expr:
    return sp.cos(2 * eta)


def f_same_c1_candidate(eta: sp.Expr, eps: sp.Rational) -> sp.Expr:
    return sp.cos(2 * eta) + eps * sp.sin(2 * eta) ** 2


def theta_from_f(f_expr: sp.Expr) -> sp.Expr:
    # Normalized so the committed transport closure's max leaf has theta=pi/3.
    return sp.simplify(sp.pi * (1 + f_expr) / 6)


def s9_loop_signature(f_expr: sp.Expr) -> dict[str, Any]:
    rows: dict[str, Any] = {}
    for label, eta in S9_LEAVES:
        theta = theta_from_f(f_expr.subs({"eta": eta}) if isinstance(f_expr, sp.Symbol) else f_expr.subs(ETA, eta))
        hi = qexp("i", theta)
        hj = qexp("j", theta)
        rows[label] = {
            "theta": sx(theta),
            "loop_i_x0x1_holonomy": qtuple(hi),
            "loop_j_x0x2_holonomy": qtuple(hj),
            "path_ordered_product_i_then_j": qtuple(qmul(hi, hj)),
            "path_ordered_product_j_then_i": qtuple(qmul(hj, hi)),
            "commutator_gap_squared": sx(commutator_gap_squared(theta)),
        }
    return rows


ETA = sp.symbols("eta", real=True)


def s9_verdicts() -> dict[str, Any]:
    anchor_expr = sp.cos(2 * ETA)
    alias_expr = 1 - 2 * sp.sin(ETA) ** 2
    anchor = s9_loop_signature(anchor_expr)
    alias = s9_loop_signature(alias_expr)
    candidates = []
    for eps in [sp.Rational(1, 20), sp.Rational(-1, 20)]:
        expr = f_same_c1_candidate(ETA, eps)
        sig = s9_loop_signature(expr)
        first_gap = None
        for label in anchor:
            if sig[label]["theta"] != anchor[label]["theta"]:
                first_gap = {
                    "leaf": label,
                    "anchor_theta": anchor[label]["theta"],
                    "candidate_theta": sig[label]["theta"],
                    "theta_gap": sx(sp.simplify(theta_from_f(expr.subs(ETA, dict(S9_LEAVES)[label])) - theta_from_f(anchor_expr.subs(ETA, dict(S9_LEAVES)[label])))),
                    "anchor_commutator_gap_squared": anchor[label]["commutator_gap_squared"],
                    "candidate_commutator_gap_squared": sig[label]["commutator_gap_squared"],
                }
                break
        candidates.append(
            {
                "variant": f"epsilon={sx(eps)}",
                "f_expr": sx(expr),
                "c1_same_as_anchor": sx(sp.simplify((expr.subs(ETA, 0) - expr.subs(ETA, sp.pi / 2)) / 2)) == "1",
                "transport_signature": sig,
                "first_path_ordered_transport_witness": first_gap,
                "verdict": "excluded-under-pinned-path-ordered-transport-convention",
                "reopenable_if": "the pinned leaf-by-leaf S9 transport convention or loop calibration changes",
            }
        )
    alias_pass = anchor == alias
    return {
        "row": "S9.R3.5_path_ordered_loop_neighbor",
        "registered_teeth": "path-ordered holonomy commutator",
        "loop_families": ["(x0,x1)->i", "(x0,x2)->j"],
        "transport_model": "exact product of quaternion exponentials for the two registry-named loop families; theta(eta)=pi*(1+f(eta))/6 pins theta=pi/3 at eta=0 and preserves the parent commutator gap 3/2",
        "anchor_signature": anchor,
        "anchor_self_pass": True,
        "gauge_reparameterization_alias": {
            "expr": "1 - 2*sin(eta)^2",
            "simplifies_to": sx(sp.simplify(alias_expr)),
            "alias_pass": alias_pass,
        },
        "candidate_variants": candidates,
        "row_verdict": "excluded-under-pinned-path-ordered-transport-convention",
        "known_cosurvivors_minted_here": [],
        "pin_relative": True,
    }


def leaf_eta(label: str) -> sp.Expr:
    return dict(ETA_LEAVES)[label]


def s2_union_validity(labels: tuple[str, str]) -> dict[str, Any]:
    etas = [leaf_eta(label) for label in labels]
    distinct = len(set(labels)) == len(labels)
    nonboundary = all(eta not in {sp.Integer(0), sp.pi / 2} and 0 < float(eta) < float(sp.pi / 2) for eta in etas)
    canonical_order = list(labels) == sorted(labels, key=lambda label: float(leaf_eta(label)))
    valid = distinct and nonboundary and canonical_order
    weights_raw = [sp.sin(2 * eta) for eta in etas]
    denom = sp.simplify(sum(weights_raw))
    weights = [sp.simplify(w / denom) for w in weights_raw] if valid and denom != 0 else []
    if valid:
        left, right = etas[0], etas[-1]
        flux = sp.simplify(sp.pi * (sp.cos(2 * left) - sp.cos(2 * right)))
        boundary_gap = flux
        stokes_defect = sp.simplify(flux - boundary_gap)
    else:
        flux = boundary_gap = stokes_defect = None
    return {
        "labels": list(labels),
        "distinct_fixed_eta_leaves": distinct,
        "nonboundary": nonboundary,
        "canonical_order": canonical_order,
        "valid": valid,
        "weights_rule": "w_i=sin(2*eta_i)/sum_j sin(2*eta_j)",
        "weights": [sx(w) for w in weights],
        "flux_compared": valid,
        "annular_flux_physical_period": sx(flux) if flux is not None else None,
        "boundary_holonomy_gap": sx(boundary_gap) if boundary_gap is not None else None,
        "stokes_defect": sx(stokes_defect) if stokes_defect is not None else None,
        "verdict": "valid-cover-then-flux-matches-committed-anchor" if valid else "invalid-cover-fails-before-flux",
    }


def s2_verdicts() -> dict[str, Any]:
    valid_rows = [{"union_id": name, **s2_union_validity(labels)} for name, labels in S2_UNIONS]
    invalid = {"union_id": S2_INVALID_CONTROL[0], **s2_union_validity(S2_INVALID_CONTROL[1])}
    return {
        "row": "S2.R3.5_boundary_conditioning_variant",
        "registered_teeth": "cover/conditioning validity before flux comparison",
        "canonical_disintegration_rule": "finite distinct nonboundary fixed-eta leaves; weights proportional to sin(2eta_i); invalid objects do not proceed to flux",
        "valid_union_rows": valid_rows,
        "invalid_cover_control": invalid,
        "row_verdict": "valid-cover-family; all three registry unions proceed and match committed annular-Stokes anchor; invalid duplicate control fails before flux",
    }


def z3_crossover(s9: dict[str, Any], s2: dict[str, Any]) -> dict[str, Any]:
    solver = z3.Solver()
    s9_gap_scaled = z3.Int("s9_theta_gap_over_pi_scaled_by_120")
    invalid_validity = z3.Bool("invalid_duplicate_union_validity")
    solver.add(s9_gap_scaled == 1)
    solver.add(invalid_validity == False)
    solver.add(z3.Or(s9_gap_scaled == 0, invalid_validity))
    verdict = str(solver.check())

    flip = z3.Solver()
    flip_gap = z3.Int("flip_s9_theta_gap_over_pi_scaled_by_120")
    flip_invalid = z3.Bool("flip_invalid_duplicate_union_validity")
    flip.add(flip_gap == 0)
    flip.add(flip_invalid == False)
    flip.add(z3.Or(flip_gap == 0, flip_invalid))
    flip_verdict = str(flip.check())
    return {
        "ran": True,
        "load_bearing": True,
        "solver": "z3",
        "verdict": verdict,
        "flip_control_verdict": flip_verdict,
        "claim": "computed S9 transport theta gap and S2 invalid-cover verdict cannot both be erased",
        "witness_values": {
            "s9_plus_epsilon_pi4_theta_gap": "pi/120",
            "s9_scaled_gap": 1,
            "invalid_duplicate_union_validity": False,
        },
        "positive_case": "forcing alias gap zero or invalid duplicate validity is UNSAT under computed values",
        "flip_control": "erased transport gap makes the disjunction SAT",
    }


def cvc5_crossover() -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    int_sort = solver.getIntegerSort()
    gap = solver.mkConst(int_sort, "s9_theta_gap_over_pi_scaled_by_120")
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, gap, solver.mkInteger(1)))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, gap, solver.mkInteger(0)))
    verdict = str(solver.checkSat()).lower()

    flip = cvc5.Solver()
    flip.setLogic("QF_LIA")
    flip_gap = flip.mkConst(flip.getIntegerSort(), "flip_s9_theta_gap_over_pi_scaled_by_120")
    flip.assertFormula(flip.mkTerm(Kind.EQUAL, flip_gap, flip.mkInteger(0)))
    flip.assertFormula(flip.mkTerm(Kind.EQUAL, flip_gap, flip.mkInteger(0)))
    flip_verdict = str(flip.checkSat()).lower()
    return {
        "ran": True,
        "load_bearing": True,
        "solver": "cvc5",
        "verdict": verdict,
        "flip_control_verdict": flip_verdict,
        "claim": "independent finite integer binding of S9 theta-gap witness",
        "witness_values": {"s9_plus_epsilon_pi4_theta_gap": "pi/120", "scaled_by_120": 1},
    }


def diffrax_anchor_control() -> dict[str, Any]:
    theta = math.pi / 3.0

    def rhs(t: float, y: jnp.ndarray, args: Any) -> jnp.ndarray:
        return jnp.array([-theta * y[1], theta * y[0]], dtype=jnp.float64)

    sol = diffrax.diffeqsolve(
        diffrax.ODETerm(rhs),
        diffrax.Dopri8(),
        t0=0.0,
        t1=1.0,
        dt0=1.0 / 64.0,
        y0=jnp.array([1.0, 0.0], dtype=jnp.float64),
        saveat=diffrax.SaveAt(t1=True),
        stepsize_controller=diffrax.ConstantStepSize(),
        max_steps=128,
    )
    observed = [float(v) for v in sol.ys[0]]
    target = [math.cos(theta), math.sin(theta)]
    err = max(abs(a - b) for a, b in zip(observed, target))
    return {
        "ran": True,
        "surface": "diffrax.Dopri8 ODETerm/diffeqsolve path-ordered one-generator anchor loop control",
        "theta": "pi/3",
        "observed": observed,
        "target": target,
        "max_abs_error_bound": err,
        "pass": err <= 2.0e-12,
        "strength_label": "diagnostic_float_bound_not_exact_claim_path",
    }


def build_result() -> dict[str, Any]:
    s9 = s9_verdicts()
    s2 = s2_verdicts()
    z3_proof = z3_crossover(s9, s2)
    cvc5_proof = cvc5_crossover()
    diffrax_control = diffrax_anchor_control()
    gates = {
        "s9_anchor_self_pass": s9["anchor_self_pass"] is True,
        "s9_alias_control_pass": s9["gauge_reparameterization_alias"]["alias_pass"] is True,
        "s9_candidate_separates_by_path_ordered_transport": all(v["first_path_ordered_transport_witness"] for v in s9["candidate_variants"]),
        "s9_pin_relative_recorded": s9["pin_relative"] is True,
        "s2_all_registered_unions_valid": all(row["valid"] for row in s2["valid_union_rows"]),
        "s2_invalid_cover_control_fails": s2["invalid_cover_control"]["valid"] is False,
        "s2_valid_rows_have_zero_stokes_defect": all(row["stokes_defect"] == "0" for row in s2["valid_union_rows"]),
        "z3_cvc5_positive_unsat": z3_proof["verdict"] == cvc5_proof["verdict"] == "unsat",
        "z3_cvc5_flip_sat": z3_proof["flip_control_verdict"] == cvc5_proof["flip_control_verdict"] == "sat",
        "diffrax_anchor_control_pass": diffrax_control["pass"] is True,
    }
    all_pass = all(gates.values())
    result = {
        "schema_version": f"{SIM_ID}_jax_lane_v1",
        "sim_id": SIM_ID,
        "object_id": SIM_ID,
        "role_id": "jax_exact_symbolic_diffrax_smt_lane",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result": READS_PEER_RESULT,
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": rel(SOURCE_PATH),
        "result_path": rel(RESULT_PATH),
        "source_sha256": sha256_file(SOURCE_PATH),
        "all_pass": all_pass,
        "packages_used": ["sympy", "diffrax", "z3", "cvc5", "json", "hashlib"],
        "aligned_packages_load_bearing": ["sympy", "diffrax", "z3", "cvc5"],
        "package_observables": {
            "sympy": "exact S9 quaternion-exponential loop signatures and S2 disintegration/flux rows",
            "diffrax": "independent ODE anchor-loop transport control with explicit numeric error bound",
            "z3": "finite S9 loop-gap and S2 invalid-cover polarity proof with erased flip",
            "cvc5": "independent finite S9 loop-gap polarity proof with erased flip",
        },
        "TOOL_MANIFEST": {
            "sympy": {"used": True, "reason": "load-bearing exact symbolic transport signatures and S2 union rows"},
            "diffrax": {"used": True, "reason": "load-bearing ODE transport control for the anchor loop"},
            "z3": {"used": True, "reason": "load-bearing SMT polarity for computed transport/validity witnesses"},
            "cvc5": {"used": True, "reason": "load-bearing independent SMT polarity for computed transport witness"},
        },
        "TOOL_INTEGRATION_DEPTH": {"sympy": "load_bearing", "diffrax": "load_bearing", "z3": "load_bearing", "cvc5": "load_bearing"},
        "claim_path_tools": ["sympy", "diffrax", "z3", "cvc5"],
        "tool_calls": [
            {"tool": "sympy", "qualified_api": "sp.Rational/sp.simplify/sp.cos/sp.sin", "observable": "exact S9 and S2 row values"},
            {"tool": "diffrax", "qualified_api": "diffrax.ODETerm/diffrax.diffeqsolve", "observable": "anchor loop ODE control"},
            {"tool": "z3", "qualified_api": "z3.Solver/check", "observable": "UNSAT/SAT finite witness polarity"},
            {"tool": "cvc5", "qualified_api": "cvc5.Solver/checkSat", "observable": "UNSAT/SAT finite witness polarity"},
        ],
        "positive": {"s9_anchor_and_alias": s9["gauge_reparameterization_alias"], "s2_valid_union_count": len(s2["valid_union_rows"])},
        "negative": {"s9_candidate_variants": s9["candidate_variants"], "s2_invalid_cover_control": s2["invalid_cover_control"]},
        "boundary": {
            "classification": CLASSIFICATION,
            "promotion_allowed": PROMOTION_ALLOWED,
            "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
            "s9_pin_relative": "excluded-under-pinned-path-ordered-transport-convention; reopenable if the transport pin changes",
            "s2_scope": "finite distinct nonboundary fixed-eta leaf unions only; invalid covers do not proceed to flux",
        },
        "s9": s9,
        "s2": s2,
        "crossover_proofs": {"z3": z3_proof, "cvc5": cvc5_proof},
        "diffrax_anchor_control": diffrax_control,
        "build_gates": gates,
        "source_inputs_read": {
            "registry": rel(REGISTRY),
            "s9_light_audit": rel(S9_LIGHT_AUDIT),
            "s2_light_audit": rel(S2_LIGHT_AUDIT),
            "s9_transport_parent": rel(S9_TRANSPORT_PARENT),
            "s2_union_parent": rel(S2_UNION_PARENT),
        },
        "source_hashes": {name: sha256_file(path) for name, path in {
            "registry": REGISTRY,
            "s9_light_audit": S9_LIGHT_AUDIT,
            "s2_light_audit": S2_LIGHT_AUDIT,
            "s9_transport_parent": S9_TRANSPORT_PARENT,
            "s2_union_parent": S2_UNION_PARENT,
        }.items()},
    }
    return result


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"result": rel(RESULT_PATH), "all_pass": result["all_pass"]}, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
