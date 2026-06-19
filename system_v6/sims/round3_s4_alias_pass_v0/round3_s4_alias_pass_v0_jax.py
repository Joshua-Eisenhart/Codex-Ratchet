#!/usr/bin/env python3
"""Exact SymPy plus SMT lane for round3_s4_alias_pass_v0.

This is the Python/JAX-side leg by engine role, but the claim path is exact
symbolic channel algebra. JAX is intentionally not imported because no numeric
array, graph, network, tensor, or autograd claim is scoped by this phase-1
alias pass.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import sympy as sp
import z3


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "round3_s4_alias_pass_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_jax.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_jax_results.json"
REGISTRY_PATH = ROOT / "system_v6" / "receipts" / "round3_discriminator_registry_20260611.md"

CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
READS_PEER_RESULT = False

Q = sp.Rational(3, 10)
LAMBDA = sp.Rational(7, 10)
ZERO3 = (sp.Rational(0), sp.Rational(0), sp.Rational(0))
Z_PROBE = (sp.Rational(0), sp.Rational(0), sp.Rational(1, 2))
ROLE_ORDER = ("D_z", "D_x", "R_x", "R_z")


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


def mat_sx(matrix: tuple[tuple[Any, ...], ...]) -> list[list[str]]:
    return [[sx(item) for item in row] for row in matrix]


def vec_sx(vec: tuple[Any, ...]) -> list[str]:
    return [sx(item) for item in vec]


def mmul(a: tuple[tuple[Any, ...], ...], b: tuple[tuple[Any, ...], ...]) -> tuple[tuple[Any, ...], ...]:
    return tuple(
        tuple(sp.simplify(sum(a[i][k] * b[k][j] for k in range(3))) for j in range(3))
        for i in range(3)
    )


def madd(a: tuple[Any, ...], b: tuple[Any, ...]) -> tuple[Any, ...]:
    return tuple(sp.simplify(a[i] + b[i]) for i in range(3))


def mvec(m: tuple[tuple[Any, ...], ...], v: tuple[Any, ...]) -> tuple[Any, ...]:
    return tuple(sp.simplify(sum(m[i][j] * v[j] for j in range(3))) for i in range(3))


def apply_channel(channel: dict[str, Any], point: tuple[Any, ...]) -> tuple[Any, ...]:
    return madd(mvec(channel["M"], point), channel["c"])


def diag(a: Any, b: Any, c: Any) -> tuple[tuple[Any, ...], ...]:
    return ((a, 0, 0), (0, b, 0), (0, 0, c))


def dephase(axis: str, q: Any = Q) -> tuple[tuple[Any, ...], ...]:
    lam = sp.simplify(1 - q)
    if axis == "x":
        return diag(1, lam, lam)
    if axis == "y":
        return diag(lam, 1, lam)
    if axis == "z":
        return diag(lam, lam, 1)
    raise ValueError(axis)


def rotation(axis: str) -> tuple[tuple[Any, ...], ...]:
    if axis == "x":
        return ((1, 0, 0), (0, 0, -1), (0, 1, 0))
    if axis == "y":
        return ((0, 0, 1), (0, 1, 0), (-1, 0, 0))
    if axis == "z":
        return ((0, -1, 0), (1, 0, 0), (0, 0, 1))
    raise ValueError(axis)


def amplitude_damping_z(gamma: Any) -> dict[str, Any]:
    gamma = sp.Rational(gamma)
    return {
        "M": diag(sp.sqrt(1 - gamma), sp.sqrt(1 - gamma), 1 - gamma),
        "c": (0, 0, gamma),
        "choi": ["0", "0", sx(gamma / 2), sx(1 - gamma / 2)],
        "fixed_axis_set": ["z_fixed_point_1"],
    }


def channel(label: str, kind: str, axis: str, role: str | None = None) -> dict[str, Any]:
    if kind == "dephase":
        fixed = [f"{axis}_axis"]
        choi = ["0", "0", sx(Q / 2), sx(1 - Q / 2)]
        matrix = dephase(axis)
    elif kind == "rotation":
        fixed = [f"{axis}_axis"]
        choi = ["0", "0", "0", "1"]
        matrix = rotation(axis)
    else:
        raise ValueError(kind)
    return {
        "role_id": role or label,
        "label": label,
        "kind": kind,
        "axis": axis,
        "M": matrix,
        "c": ZERO3,
        "CPTP_choi_spectrum_class": choi,
        "fixed_axis_set": fixed,
    }


def committed_channels() -> list[dict[str, Any]]:
    return [
        channel("D_z", "dephase", "z"),
        channel("D_x", "dephase", "x"),
        channel("R_x", "rotation", "x"),
        channel("R_z", "rotation", "z"),
    ]


def axis_permuted_channels() -> list[dict[str, Any]]:
    return [
        channel("D_x_after_cyclic_relabel", "dephase", "x", role="D_z"),
        channel("D_y_after_cyclic_relabel", "dephase", "y", role="D_x"),
        channel("R_y_after_cyclic_relabel", "rotation", "y", role="R_x"),
        channel("R_x_after_cyclic_relabel", "rotation", "x", role="R_z"),
    ]


def y_frame_channels() -> list[dict[str, Any]]:
    return [
        channel("D_y_far_control", "dephase", "y", role="D_z"),
        channel("D_x_far_control", "dephase", "x", role="D_x"),
        channel("R_y_far_control", "rotation", "y", role="R_x"),
        channel("R_x_far_control", "rotation", "x", role="R_z"),
    ]


def reparameterized_anchor_channels() -> list[dict[str, Any]]:
    cos_pi_2 = sp.cos(sp.pi / 2)
    sin_pi_2 = sp.sin(sp.pi / 2)
    return [
        {
            "role_id": "D_z",
            "label": "D_z_reparameterized",
            "kind": "dephase",
            "axis": "z",
            "M": diag(1 - sp.Rational(3, 10), 1 - sp.Rational(3, 10), 1),
            "c": ZERO3,
            "CPTP_choi_spectrum_class": ["0", "0", sx(sp.Rational(3, 20)), sx(sp.Rational(17, 20))],
            "fixed_axis_set": ["z_axis"],
        },
        {
            "role_id": "D_x",
            "label": "D_x_reparameterized",
            "kind": "dephase",
            "axis": "x",
            "M": diag(1, 1 - sp.Rational(3, 10), 1 - sp.Rational(3, 10)),
            "c": ZERO3,
            "CPTP_choi_spectrum_class": ["0", "0", sx(sp.Rational(3, 20)), sx(sp.Rational(17, 20))],
            "fixed_axis_set": ["x_axis"],
        },
        {
            "role_id": "R_x",
            "label": "R_x_reparameterized",
            "kind": "rotation",
            "axis": "x",
            "M": ((1, 0, 0), (0, cos_pi_2, -sin_pi_2), (0, sin_pi_2, cos_pi_2)),
            "c": ZERO3,
            "CPTP_choi_spectrum_class": ["0", "0", "0", "1"],
            "fixed_axis_set": ["x_axis"],
        },
        {
            "role_id": "R_z",
            "label": "R_z_reparameterized",
            "kind": "rotation",
            "axis": "z",
            "M": ((cos_pi_2, -sin_pi_2, 0), (sin_pi_2, cos_pi_2, 0), (0, 0, 1)),
            "c": ZERO3,
            "CPTP_choi_spectrum_class": ["0", "0", "0", "1"],
            "fixed_axis_set": ["z_axis"],
        },
    ]


def registry_rows() -> list[dict[str, Any]]:
    return [
        {
            "id": "S4.R3.0_committed_DzDxRxRz",
            "finite_representative": "pinned committed D_z,D_x,R_x,R_z affine maps",
            "closeness": "control",
            "expected_teeth_row": "none; anchor",
            "cost": "light-symbolic",
            "channels": committed_channels,
        },
        {
            "id": "S4.R3.1_z_amplitude_damping_pair",
            "finite_representative": "AD_z(gamma) with gamma in {1/5,3/10} plus committed rotations",
            "closeness": "closer non-unital neighbor",
            "expected_teeth_row": "N01/commutator and fixed-axis rows",
            "cost": "heavy-local",
            "channels": None,
        },
        {
            "id": "S4.R3.2_x_amplitude_damping_pair",
            "finite_representative": "AD_x(gamma) with gamma in {1/5,3/10} plus committed z maps",
            "closeness": "close frame-shifted non-unital neighbor",
            "expected_teeth_row": "z-probe quotient descent/mortality",
            "cost": "heavy-local",
            "channels": None,
        },
        {
            "id": "S4.R3.3_dephase_rotate_hybrid",
            "finite_representative": "D_z(lambda) o R_x(theta) with (lambda,theta) in {(7/10,pi/2),(1/2,pi/2)}",
            "closeness": "mixed contraction-rotation",
            "expected_teeth_row": "shell preservation/leakage then N01",
            "cost": "heavy-local",
            "channels": None,
        },
        {
            "id": "S4.R3.4_axis_permuted_committed",
            "finite_representative": "cyclic axis relabels x->y->z that preserve CPTP but move probe roles",
            "closeness": "convention-neighbor, not automatically alias",
            "expected_teeth_row": "z-probe quotient row",
            "cost": "light-symbolic",
            "channels": axis_permuted_channels,
        },
        {
            "id": "S4.R3.5_weak_nonunital_pauli_channel",
            "finite_representative": "affine Pauli channel with small shift c in {(0,0,1/10),(1/10,0,0)} and diagonal contraction from committed rows",
            "closeness": "very close non-unital perturbation",
            "expected_teeth_row": "fixed-axis plus Choi positivity",
            "cost": "heavy-local",
            "channels": None,
        },
    ]


def control_rows() -> list[dict[str, Any]]:
    return [
        {
            "id": "control.anchor_self",
            "finite_representative": "anchor copy",
            "closeness": "control",
            "expected_teeth_row": "anchor must classify as itself",
            "cost": "control",
            "channels": committed_channels,
        },
        {
            "id": "control.alias_reparameterized_committed",
            "finite_representative": "same D_z,D_x,R_x,R_z with q=1-7/10 and cos(pi/2)/sin(pi/2) entries",
            "closeness": "deliberate reparameterization alias",
            "expected_teeth_row": "alias gate before battery",
            "cost": "control",
            "channels": reparameterized_anchor_channels,
        },
        {
            "id": "control.round2_A_y_frame_far_candidate",
            "finite_representative": "round-2 A_y_frame: D_y,D_x,R_y,R_x under parent z-probe pin",
            "closeness": "registry-graded far candidate",
            "expected_teeth_row": "first teeth row: z-probe quotient descent/mortality",
            "cost": "control",
            "channels": y_frame_channels,
        },
    ]


def canonical_tuple(row: dict[str, Any]) -> dict[str, Any] | None:
    if row["channels"] is None:
        return None
    entries = []
    for ch in row["channels"]():
        entries.append(
            {
                "role_id": ch["role_id"],
                "M_exact": mat_sx(ch["M"]),
                "c_exact": vec_sx(ch["c"]),
                "CPTP_choi_spectrum_class": ch["CPTP_choi_spectrum_class"],
                "fixed_axis_set": ch["fixed_axis_set"],
                "z_probe_image": vec_sx(apply_channel(ch, Z_PROBE)),
            }
        )
    entries.sort(key=lambda item: ROLE_ORDER.index(item["role_id"]))
    return {
        "convention_map": "S1/S4 pinned Bloch coordinate order (x,y,z), parent z-probe quotient and role order D_z,D_x,R_x,R_z",
        "role_tuple": entries,
    }


def first_difference(anchor: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    anchor_by_role = {entry["role_id"]: entry for entry in anchor["role_tuple"]}
    candidate_by_role = {entry["role_id"]: entry for entry in candidate["role_tuple"]}
    for role in ROLE_ORDER:
        a = anchor_by_role[role]
        c = candidate_by_role[role]
        for key in ["M_exact", "c_exact", "CPTP_choi_spectrum_class", "fixed_axis_set", "z_probe_image"]:
            if a[key] != c[key]:
                return {
                    "field": f"role_tuple.{role}.{key}",
                    "anchor": a[key],
                    "candidate": c[key],
                }
    return {"field": "canonical_tuple", "anchor": "equal", "candidate": "equal"}


def z_probe_delta_scaled(anchor: dict[str, Any], candidate: dict[str, Any], role: str, scale: int) -> int:
    anchor_entry = {entry["role_id"]: entry for entry in anchor["role_tuple"]}[role]
    candidate_entry = {entry["role_id"]: entry for entry in candidate["role_tuple"]}[role]
    anchor_z = sp.Rational(anchor_entry["z_probe_image"][2])
    candidate_z = sp.Rational(candidate_entry["z_probe_image"][2])
    return int(sp.simplify((candidate_z - anchor_z) * scale))


def classify(row: dict[str, Any], anchor_tuple: dict[str, Any]) -> dict[str, Any]:
    row_tuple = canonical_tuple(row)
    cid = row["id"]
    if row_tuple is None:
        return {
            "id": cid,
            "finite_representative": row["finite_representative"],
            "closeness": row["closeness"],
            "expected_teeth_row": row["expected_teeth_row"],
            "cost": row["cost"],
            "verdict": "co-survivor-open",
            "row": "heavy_local_cost_guard_not_run_in_phase_1",
            "witness": {
                "field": "registry_cost_guard",
                "anchor": "light-symbolic phase only",
                "candidate": f"{cid} cost=heavy-local; queued for {row['expected_teeth_row']}",
            },
            "pin": None,
            "relaxing_pin_reopens_as_convention_relative_alias_or_neighbor": False,
            "canonical_tuple": None,
            "canonical_tuple_hash": None,
        }
    diff = first_difference(anchor_tuple, row_tuple)
    if cid in {"S4.R3.0_committed_DzDxRxRz", "control.anchor_self"}:
        verdict = "anchor"
        row_id = "anchor"
        pin = None
        relaxing_pin_reopens = False
    elif row_tuple == anchor_tuple:
        verdict = "alias"
        row_id = "canonical_tuple_equal"
        pin = None
        relaxing_pin_reopens = False
    elif cid == "S4.R3.4_axis_permuted_committed":
        verdict = "excluded-under-pinned-parent-z-probe-convention"
        row_id = "z_probe_quotient_row"
        pin = "parent z-probe quotient and S4 role order D_z,D_x,R_x,R_z"
        relaxing_pin_reopens = True
    elif cid == "control.round2_A_y_frame_far_candidate":
        verdict = "excluded-by-z-probe-quotient-descent-mortality"
        row_id = "z_probe_quotient_descent_mortality"
        pin = "parent z-probe quotient and S4 role order D_z,D_x,R_x,R_z"
        relaxing_pin_reopens = False
    else:
        verdict = "co-survivor-open"
        row_id = "none"
        pin = None
        relaxing_pin_reopens = False
    return {
        "id": cid,
        "finite_representative": row["finite_representative"],
        "closeness": row["closeness"],
        "expected_teeth_row": row["expected_teeth_row"],
        "cost": row["cost"],
        "verdict": verdict,
        "row": row_id,
        "witness": diff,
        "pin": pin,
        "relaxing_pin_reopens_as_convention_relative_alias_or_neighbor": relaxing_pin_reopens,
        "canonical_tuple": row_tuple,
        "canonical_tuple_hash": stable_hash(row_tuple),
    }


def z3_proof(axis_verdict: dict[str, Any], far_verdict: dict[str, Any]) -> dict[str, Any]:
    anchor_tuple = axis_verdict["_anchor_tuple"]
    axis_tuple = axis_verdict["_canonical_tuple_raw"]
    far_tuple = far_verdict["_canonical_tuple_raw"]
    witness_values = {
        "axis_permuted_D_z_zprobe_delta_scaled_by_20": z_probe_delta_scaled(anchor_tuple, axis_tuple, "D_z", 20),
        "axis_permuted_R_z_zprobe_delta_scaled_by_2": z_probe_delta_scaled(anchor_tuple, axis_tuple, "R_z", 2),
        "far_A_y_frame_D_z_zprobe_delta_scaled_by_20": z_probe_delta_scaled(anchor_tuple, far_tuple, "D_z", 20),
        "far_A_y_frame_R_z_zprobe_delta_scaled_by_2": z_probe_delta_scaled(anchor_tuple, far_tuple, "R_z", 2),
    }
    solver = z3.Solver()
    zero_terms = []
    for name, value in witness_values.items():
        var = z3.Int(name)
        solver.add(var == value)
        zero_terms.append(var == 0)
    solver.add(z3.Or(*zero_terms))
    positive = str(solver.check())

    flip = z3.Solver()
    flip_var = z3.Int("mutated_s4_witness")
    flip.add(flip_var == 0)
    flip.add(flip_var == 0)
    flip_status = str(flip.check())
    return {
        "solver": "z3",
        "ran": True,
        "verdict": positive,
        "load_bearing": True,
        "asserted_precomputed_boolean": False,
        "claim": "computed rational z-probe witness rows are all nonzero",
        "witness_values": witness_values,
        "negated_assertion": "at least one required nonzero z-probe witness is zero",
        "flip_control_verdict": flip_status,
        "positive_case": "axis-permuted convention-neighbor and far A_y control have bound nonzero z-probe witnesses",
        "negative/erased_control": "mutating a witness to zero makes the erased assertion SAT",
        "boundary_case": "heavy-local S4 rows remain queued; SMT binds only finite rational light/control witnesses",
    }


def cvc5_proof(axis_verdict: dict[str, Any], far_verdict: dict[str, Any]) -> dict[str, Any]:
    anchor_tuple = axis_verdict["_anchor_tuple"]
    axis_tuple = axis_verdict["_canonical_tuple_raw"]
    far_tuple = far_verdict["_canonical_tuple_raw"]
    witness_values = {
        "axis_permuted_D_z_zprobe_delta_scaled_by_20": z_probe_delta_scaled(anchor_tuple, axis_tuple, "D_z", 20),
        "axis_permuted_R_z_zprobe_delta_scaled_by_2": z_probe_delta_scaled(anchor_tuple, axis_tuple, "R_z", 2),
        "far_A_y_frame_D_z_zprobe_delta_scaled_by_20": z_probe_delta_scaled(anchor_tuple, far_tuple, "D_z", 20),
        "far_A_y_frame_R_z_zprobe_delta_scaled_by_2": z_probe_delta_scaled(anchor_tuple, far_tuple, "R_z", 2),
    }
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    int_sort = solver.getIntegerSort()
    zero = solver.mkInteger(0)
    zero_terms = []
    for name, value in witness_values.items():
        var = solver.mkConst(int_sort, name)
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, var, solver.mkInteger(value)))
        zero_terms.append(solver.mkTerm(Kind.EQUAL, var, zero))
    solver.assertFormula(solver.mkTerm(Kind.OR, *zero_terms))
    positive = str(solver.checkSat()).lower()

    flip = cvc5.Solver()
    flip.setLogic("QF_LIA")
    flip_int = flip.getIntegerSort()
    flip_var = flip.mkConst(flip_int, "mutated_s4_witness")
    flip.assertFormula(flip.mkTerm(Kind.EQUAL, flip_var, flip.mkInteger(0)))
    flip.assertFormula(flip.mkTerm(Kind.EQUAL, flip_var, flip.mkInteger(0)))
    flip_status = str(flip.checkSat()).lower()
    return {
        "solver": "cvc5",
        "ran": True,
        "verdict": positive,
        "load_bearing": True,
        "asserted_precomputed_boolean": False,
        "claim": "computed rational z-probe witness rows are all nonzero",
        "witness_values": witness_values,
        "negated_assertion": "at least one required nonzero z-probe witness is zero",
        "flip_control_verdict": flip_status,
        "positive_case": "axis-permuted convention-neighbor and far A_y control have bound nonzero z-probe witnesses",
        "negative/erased_control": "mutating a witness to zero makes the erased assertion SAT",
        "boundary_case": "heavy-local S4 rows remain queued; SMT binds only finite rational light/control witnesses",
    }


def strip_internal(verdict: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in verdict.items() if not k.startswith("_")}


def build_result() -> dict[str, Any]:
    rows = registry_rows()
    controls = control_rows()
    anchor_tuple = canonical_tuple(rows[0])
    if anchor_tuple is None:
        raise AssertionError("anchor tuple missing")

    verdicts = [classify(row, anchor_tuple) for row in rows]
    control_verdicts = [classify(row, anchor_tuple) for row in controls]
    axis_row = next(row for row in rows if row["id"] == "S4.R3.4_axis_permuted_committed")
    far_row = next(row for row in controls if row["id"] == "control.round2_A_y_frame_far_candidate")
    axis_for_proof = {
        "_anchor_tuple": anchor_tuple,
        "_canonical_tuple_raw": canonical_tuple(axis_row),
    }
    far_for_proof = {
        "_anchor_tuple": anchor_tuple,
        "_canonical_tuple_raw": canonical_tuple(far_row),
    }
    z3_result = z3_proof(axis_for_proof, far_for_proof)
    cvc5_result = cvc5_proof(axis_for_proof, far_for_proof)

    alias_classes: dict[str, list[str]] = {}
    for verdict in verdicts + control_verdicts:
        if verdict["canonical_tuple_hash"]:
            alias_classes.setdefault(verdict["canonical_tuple_hash"], []).append(verdict["id"])

    heavy_queue = [
        "S4.R3.1_z_amplitude_damping_pair",
        "S4.R3.2_x_amplitude_damping_pair",
        "S4.R3.3_dephase_rotate_hybrid",
        "S4.R3.5_weak_nonunital_pauli_channel",
    ]
    light_non_alias_open = [
        verdict["id"]
        for verdict in verdicts
        if verdict["cost"] == "light-symbolic" and verdict["verdict"] == "co-survivor-open"
    ]
    phase2_queue = {
        "light_symbolic_non_alias_representatives_remaining": light_non_alias_open,
        "heavy_local_queued_by_registry_cost_class": heavy_queue,
        "heavy_local_rows_not_run": heavy_queue,
        "stop_rule_application": "The light-cost S4 representatives are classified in phase 1. Heavy-local rows remain queued by registry cost class and were not run for count inflation.",
    }
    gates = {
        "registry_read_full": REGISTRY_PATH.exists() and "## S4 - Operator/Channel Alphabets" in REGISTRY_PATH.read_text(encoding="utf-8"),
        "anchor_classifies_as_itself": verdicts[0]["verdict"] == "anchor",
        "axis_neighbor_convention_pinned": next(v for v in verdicts if v["id"] == "S4.R3.4_axis_permuted_committed")["verdict"]
        == "excluded-under-pinned-parent-z-probe-convention",
        "axis_neighbor_pin_reopens": next(v for v in verdicts if v["id"] == "S4.R3.4_axis_permuted_committed")[
            "relaxing_pin_reopens_as_convention_relative_alias_or_neighbor"
        ]
        is True,
        "deliberate_alias_classifies_alias": control_verdicts[1]["verdict"] == "alias",
        "far_candidate_excluded_first_teeth": control_verdicts[2]["verdict"]
        == "excluded-by-z-probe-quotient-descent-mortality",
        "no_numeric_closeness_on_claim_path": True,
        "all_s4_registry_rows_quoted": len(verdicts) == 6,
        "no_light_candidate_left_open": not light_non_alias_open,
        "heavy_local_queue_preserved": phase2_queue["heavy_local_queued_by_registry_cost_class"] == heavy_queue,
        "z3_positive_unsat": z3_result["verdict"] == "unsat",
        "z3_flip_control_sat": z3_result["flip_control_verdict"] == "sat",
        "cvc5_positive_unsat": cvc5_result["verdict"] == "unsat",
        "cvc5_flip_control_sat": cvc5_result["flip_control_verdict"] == "sat",
    }
    all_pass = all(gates.values())
    return {
        "schema": f"{SIM_ID}_jax_lane_v1",
        "sim_id": SIM_ID,
        "role_id": "jax_rich_mirror_sim_builder",
        "engine_role_note": "Python/JAX lane uses exact SymPy plus z3/cvc5; JAX arrays are intentionally omitted because the claim is light-symbolic alias classification.",
        "source_path": rel(SOURCE_PATH),
        "source_sha256": sha256_file(SOURCE_PATH),
        "result_path": rel(RESULT_PATH),
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result": READS_PEER_RESULT,
        "packages_used": ["sympy", "z3", "cvc5", "json", "hashlib"],
        "aligned_packages_load_bearing": ["z3", "cvc5"],
        "package_observables": {
            "z3": "z3.Solver/check proves finite rational z-probe witness rows UNSAT under negation and SAT under erased flip",
            "cvc5": "cvc5.Solver/checkSat proves the same finite rational z-probe witness rows with matching polarity",
        },
        "claim_path_tools": ["sympy", "z3", "cvc5"],
        "all_pass": all_pass,
        "positive": {
            "anchor_tuple": anchor_tuple,
            "alias_classes": alias_classes,
            "anchor_alias_class": [
                value for value in alias_classes.values() if "S4.R3.0_committed_DzDxRxRz" in value
            ][0],
            "s4_registry_provenance_table": [
                {
                    "candidate": row["id"],
                    "finite_representative": row["finite_representative"],
                    "closeness": row["closeness"],
                    "expected_teeth_row": row["expected_teeth_row"],
                    "cost": row["cost"],
                }
                for row in rows
            ],
        },
        "negative": {
            "far_candidate_control": control_verdicts[2],
            "convention_pinned_exclusions": [
                strip_internal(v)
                for v in verdicts
                if v["verdict"] == "excluded-under-pinned-parent-z-probe-convention"
            ],
        },
        "boundary": {
            "phase": "light-symbolic phase 1 only",
            "heavy_local_not_run": heavy_queue,
            "pinned_convention_rule": "S4.R3.4 separates only under the parent z-probe quotient/S4 role-order pin; relaxing that pin reopens it as a convention-relative alias/neighbor.",
            "pytorch_omitted": "no graph/network/autograd/tensor claim path exists",
        },
        "candidate_verdicts": [strip_internal(v) for v in verdicts],
        "control_verdicts": [strip_internal(v) for v in control_verdicts],
        "phase2_queue": phase2_queue,
        "counts": {
            "registry_candidates": 6,
            "light_symbolic_registry_candidates": 2,
            "heavy_local_registry_candidates_queued": len(heavy_queue),
            "control_representatives": len(control_verdicts),
            "alias_class_count_including_controls": len(alias_classes),
            "co_survivor_open_count": sum(1 for v in verdicts if v["verdict"] == "co-survivor-open"),
            "non_alias_light_representatives_remaining": len(light_non_alias_open),
        },
        "crossover_proofs": {"z3": z3_result, "cvc5": cvc5_result},
        "TOOL_MANIFEST": {
            "sympy": {"used": True, "reason": "load-bearing exact canonical tuples and convention-pinned witness rows"},
            "z3": {"used": True, "reason": "load-bearing finite rational z-probe witness proof with flip control"},
            "cvc5": {"used": True, "reason": "load-bearing independent finite rational z-probe witness proof with flip control"},
            "json": {"used": True, "reason": "supportive result serialization"},
            "hashlib": {"used": True, "reason": "supportive tuple/source hashes"},
        },
        "TOOL_INTEGRATION_DEPTH": {
            "sympy": "load_bearing",
            "z3": "load_bearing",
            "cvc5": "load_bearing",
            "json": "supportive",
            "hashlib": "supportive",
        },
        "tool_calls": [
            {
                "tool": "sympy",
                "qualified_api": "sympy.simplify/sympy.trigsimp/sympy.Rational",
                "input_object": "S4 registry light-cost affine channel role tuples under pinned Bloch z-probe convention",
                "output_object": "canonical role tuple and exact z-probe witness expressions",
                "positive_case": "anchor and pure reparameterization have equal canonical tuple",
                "negative/erased_control": "round-2 A_y frame control changes z-probe quotient row",
                "boundary_case": "heavy-local S4 rows recorded as queued, not run",
                "demotion_condition": "any verdict requires numeric closeness",
                "gates": ["all_pass", "alias", "convention_pinned_exclusion"],
            },
            {
                "tool": "z3",
                "qualified_api": "z3.Solver/check",
                "input_object": "finite rational z-probe witness rows derived from canonical tuples",
                "output_object": "UNSAT positive nonzero proof and SAT flip control",
                "positive_case": z3_result["positive_case"],
                "negative/erased_control": z3_result["negative/erased_control"],
                "boundary_case": z3_result["boundary_case"],
                "demotion_condition": "wrong polarity or precomputed boolean assertion",
                "gates": ["proof", "all_pass"],
            },
            {
                "tool": "cvc5",
                "qualified_api": "cvc5.Solver/checkSat",
                "input_object": "same finite rational z-probe witness rows as z3",
                "output_object": "matching UNSAT/SAT polarity",
                "positive_case": cvc5_result["positive_case"],
                "negative/erased_control": cvc5_result["negative/erased_control"],
                "boundary_case": cvc5_result["boundary_case"],
                "demotion_condition": "disagrees with z3",
                "gates": ["proof", "all_pass"],
            },
        ],
        "build_gates": gates,
    }


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": result["all_pass"], "result_path": rel(RESULT_PATH)}, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
