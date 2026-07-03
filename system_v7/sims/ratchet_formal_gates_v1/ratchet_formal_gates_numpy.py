#!/usr/bin/env python3
"""Formal gates for the ratchet definition on the real 3-qubit carrier.

Ceiling: scratch_diagnostic; promotion_allowed=false.

The numeric carrier is the C^8 3-qubit engine surface from
system_v7/constraint_core/engines/oracle_targets_3q.py.  The observable quotient
uses the full 63-element non-identity Pauli probe family.  The SMT gates use
z3 and cvc5 with erased controls.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import math
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import cvc5
import numpy as np
import z3
from cvc5 import Kind

classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False
TOOL_MANIFEST = {
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing full C^8 density carrier enumeration, Pauli expectation quotient, and Xi_ref representative-independence check",
    },
    "scipy.linalg.expm": {
        "tried": True,
        "used": True,
        "reason": "load-bearing import-through oracle_targets_3q.py engine convention for finite 3-qubit stage states",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing SMT polarity checks for R5 token identity and R6 progress/non-step axioms",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent SMT cross-check for the same R5/R6 obligations",
    },
    "json": {"tried": True, "used": True, "reason": "artifact serialization"},
}
TOOL_INTEGRATION_DEPTH = {
    "numpy": "load_bearing",
    "scipy.linalg.expm": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "json": "supportive",
}

SIM_ID = "ratchet_formal_gates_v1"
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
RESULTS = HERE / "results"
SPEC = HERE / "spec.json"
ORACLE_DIR = REPO / "system_v7" / "constraint_core" / "engines"
sys.path.insert(0, str(ORACLE_DIR))
import oracle_targets_3q as oracle  # noqa: E402


@dataclass(frozen=True)
class CarrierState:
    label: str
    family: str
    rho: np.ndarray
    pvec: tuple[float, ...]


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def canonical_rho(rho: np.ndarray) -> np.ndarray:
    rho = (rho + rho.conj().T) / 2
    tr = np.trace(rho).real
    if abs(tr) < 1e-15:
        raise ValueError("zero-trace density candidate")
    rho = rho / tr
    rho[np.abs(rho) < 1e-14] = 0
    return rho


def make_probe() -> np.ndarray:
    rho0_q0 = 0.5 * (oracle.I2 + oracle.PROBE_B[0] * oracle.sx + oracle.PROBE_B[1] * oracle.sy + oracle.PROBE_B[2] * oracle.sz)
    plus = 0.5 * (oracle.I2 + oracle.sx)
    return oracle.kron3(rho0_q0, plus, plus)


def pvec(rho: np.ndarray) -> tuple[float, ...]:
    return tuple(float(np.trace(rho @ oracle.PMATS[s]).real) for s in oracle.STRINGS)


def rounded_pvec_key(values: tuple[float, ...], ndigits: int = 12) -> tuple[float, ...]:
    return tuple(round(float(v), ndigits) for v in values)


def enumerate_carrier() -> list[CarrierState]:
    probe = make_probe()
    states: list[CarrierState] = []
    for t in range(8):
        generator = oracle.gen(t)
        fixed = canonical_rho(oracle.flow(generator, probe.copy(), t=8.0, steps=1600))
        states.append(CarrierState(f"terrain_{t}_fixed", "terrain_fixed", fixed, pvec(fixed)))
        for op_name in oracle.NATIVE[t]:
            op = oracle.op(op_name)
            terrain_first = canonical_rho(op(oracle.flow(generator, probe.copy())))
            operator_first = canonical_rho(oracle.flow(generator, op(probe.copy())))
            states.append(CarrierState(f"stage_{t}_{op_name}_terrain_first", "stage_order", terrain_first, pvec(terrain_first)))
            states.append(CarrierState(f"stage_{t}_{op_name}_operator_first", "stage_order", operator_first, pvec(operator_first)))
    labels = [s.label for s in states]
    if len(labels) != len(set(labels)):
        raise AssertionError("carrier labels are not unique")
    return states


def quotient_classes(states: list[CarrierState]) -> dict[str, Any]:
    buckets: dict[tuple[float, ...], list[CarrierState]] = defaultdict(list)
    for state in states:
        buckets[rounded_pvec_key(state.pvec)].append(state)
    sorted_keys = sorted(buckets)
    classes = []
    projection = {}
    for idx, key in enumerate(sorted_keys):
        labels = sorted(s.label for s in buckets[key])
        for label in labels:
            projection[label] = idx
        classes.append(
            {
                "class_id": idx,
                "size": len(labels),
                "labels": labels,
                "probe_key_sha256": sha256_text(json.dumps(list(key), sort_keys=True)),
            }
        )
    pair_checks = []
    for a, b in itertools.combinations(states, 2):
        same = projection[a.label] == projection[b.label]
        diff_norm = float(np.linalg.norm(np.asarray(a.pvec) - np.asarray(b.pvec)))
        pair_checks.append(
            {
                "a": a.label,
                "b": b.label,
                "same_class": same,
                "probe_l2": diff_norm,
                "difference_survives_observable_quotient": not same,
            }
        )
    return {
        "definition": "rho_a ~ rho_b iff every one of the 63 non-identity 3-qubit Pauli expectations is equal after deterministic rounding at 12 decimals",
        "non_circularity": "depends only on carrier states and finite probe family; no update maps, admissibility predicates, or Xi candidates are referenced",
        "probe_count": len(oracle.STRINGS),
        "carrier_count": len(states),
        "quotient_class_count": len(classes),
        "class_sizes": [c["size"] for c in classes],
        "classes": classes,
        "projection": projection,
        "pair_check_count": len(pair_checks),
        "surviving_difference_count": sum(1 for p in pair_checks if p["difference_survives_observable_quotient"]),
        "collapsed_pair_count": sum(1 for p in pair_checks if p["same_class"]),
        "max_collapsed_pair_probe_l2": max((p["probe_l2"] for p in pair_checks if p["same_class"]), default=0.0),
        "min_surviving_pair_probe_l2": min((p["probe_l2"] for p in pair_checks if not p["same_class"]), default=0.0),
        "gate_pass": len(classes) > 0 and len(oracle.STRINGS) == 63,
    }


def bits(index: int) -> tuple[int, int, int]:
    return ((index >> 2) & 1, (index >> 1) & 1, index & 1)


def index_from_bits(values: tuple[int, ...]) -> int:
    out = 0
    for value in values:
        out = (out << 1) | int(value)
    return out


def partial_trace(rho: np.ndarray, keep: tuple[int, ...]) -> np.ndarray:
    keep = tuple(keep)
    drop = tuple(i for i in range(3) if i not in keep)
    dim = 2 ** len(keep)
    out = np.zeros((dim, dim), dtype=np.complex128)
    for row in range(8):
        row_bits = bits(row)
        row_keep = tuple(row_bits[i] for i in keep)
        row_out = index_from_bits(row_keep)
        for col in range(8):
            col_bits = bits(col)
            if any(row_bits[i] != col_bits[i] for i in drop):
                continue
            col_keep = tuple(col_bits[i] for i in keep)
            col_out = index_from_bits(col_keep)
            out[row_out, col_out] += rho[row, col]
    return canonical_rho(out)


def entropy_bits(rho: np.ndarray) -> float:
    vals = np.linalg.eigvalsh((rho + rho.conj().T) / 2)
    vals = np.clip(np.real(vals), 0.0, 1.0)
    return float(-sum(v * math.log(v, 2) for v in vals if v > 1e-14))


def qubit_local_strength(pv: tuple[float, ...], qubit: int) -> float:
    total = 0.0
    for axis in "XYZ":
        label = ["I", "I", "I"]
        label[qubit] = axis
        idx = oracle.STRINGS.index("".join(label))
        total += abs(float(pv[idx]))
    return total


def xi_ref_descriptor(ref: CarrierState, target: CarrierState) -> tuple[int, float, tuple[float, ...]]:
    cut_qubit = max(range(3), key=lambda q: (qubit_local_strength(ref.pvec, q), -q))
    rho_b = partial_trace(target.rho, tuple(i for i in range(3) if i != cut_qubit))
    coherent_info = entropy_bits(rho_b) - entropy_bits(target.rho)
    local = []
    for axis in "XYZ":
        label = ["I", "I", "I"]
        label[cut_qubit] = axis
        idx = oracle.STRINGS.index("".join(label))
        local.append(round(float(target.pvec[idx]), 12))
    return cut_qubit, round(float(coherent_info), 12), tuple(local)


def xi_ref_lift_check(states: list[CarrierState], quotient: dict[str, Any]) -> dict[str, Any]:
    by_label = {s.label: s for s in states}
    classes = quotient["classes"]
    failures = []
    max_descriptor_spread = 0.0
    checked_pairs = 0
    lifted = {}
    for c_ref in classes:
        ref_states = [by_label[label] for label in c_ref["labels"]]
        for c_target in classes:
            target_states = [by_label[label] for label in c_target["labels"]]
            descriptors = []
            for ref in ref_states:
                for target in target_states:
                    descriptors.append(xi_ref_descriptor(ref, target))
            checked_pairs += 1
            first = descriptors[0]
            numeric_spread = max(
                abs(float(d[1]) - float(first[1])) + sum(abs(float(a) - float(b)) for a, b in zip(d[2], first[2])) + (0 if d[0] == first[0] else 1)
                for d in descriptors
            )
            max_descriptor_spread = max(max_descriptor_spread, numeric_spread)
            if any(d != first for d in descriptors[1:]):
                failures.append({"c_ref": c_ref["class_id"], "c_target": c_target["class_id"], "descriptors": [list(d[:2]) + [list(d[2])] for d in descriptors]})
            lifted[f"{c_ref['class_id']}->{c_target['class_id']}"] = {"cut_qubit": first[0], "coherent_info_bits": first[1], "local_probe_xyz": list(first[2])}
    status = "quotient_lift_constructed" if not failures else "demoted_to_raw_carrier_discriminator"
    return {
        "definition": "Xi_ref(c_ref,c) is the representative-independent value of the point-reference descriptor computed from any x_ref in c_ref and x in c",
        "raw_descriptor": "cut qubit selected by reference representative local Pauli strength; target value is coherent information S(B)-S(AB) plus local XYZ readout on that cut",
        "well_definedness_condition": "for every c_ref,c, all representative pairs produce identical descriptors at 12 decimals",
        "checked_class_pairs": checked_pairs,
        "multi_representative_class_count": sum(1 for c in classes if c["size"] > 1),
        "max_descriptor_spread": max_descriptor_spread,
        "failure_count": len(failures),
        "failures": failures[:20],
        "status": status,
        "gate_pass": not failures,
        "lifted_values": lifted,
    }


def z3_token_identity_gate(erased: bool, replay_case: bool) -> str:
    solver = z3.Solver()
    same_content, probe_indist, lineage_connected = z3.Bools("same_content probe_indist lineage_connected")
    logged_replay, fresh_tuple, same_entity = z3.Bools("logged_replay fresh_tuple same_entity")
    hell_old, admitted_new = z3.Bools("hell_old admitted_new")
    solver.add(same_entity == z3.And(same_content, probe_indist, lineage_connected, z3.Not(logged_replay)))
    if not erased:
        solver.add(z3.Implies(z3.And(hell_old, admitted_new), z3.And(logged_replay, fresh_tuple, z3.Not(same_entity))))
    solver.add(hell_old, admitted_new, same_content, probe_indist, lineage_connected)
    if replay_case:
        solver.add(logged_replay, fresh_tuple, z3.Not(same_entity))
    else:
        solver.add(z3.Not(logged_replay), z3.Not(fresh_tuple), same_entity)
    return str(solver.check())


def cvc5_bool_const(tm: cvc5.TermManager, name: str) -> cvc5.Term:
    return tm.mkConst(tm.getBooleanSort(), name)


def cvc5_token_identity_gate(erased: bool, replay_case: bool) -> str:
    tm = cvc5.TermManager()
    slv = cvc5.Solver(tm)
    slv.setLogic("QF_UF")
    same_content = cvc5_bool_const(tm, "same_content")
    probe_indist = cvc5_bool_const(tm, "probe_indist")
    lineage_connected = cvc5_bool_const(tm, "lineage_connected")
    logged_replay = cvc5_bool_const(tm, "logged_replay")
    fresh_tuple = cvc5_bool_const(tm, "fresh_tuple")
    same_entity = cvc5_bool_const(tm, "same_entity")
    hell_old = cvc5_bool_const(tm, "hell_old")
    admitted_new = cvc5_bool_const(tm, "admitted_new")
    same_entity_def = tm.mkTerm(Kind.AND, same_content, probe_indist, lineage_connected, tm.mkTerm(Kind.NOT, logged_replay))
    slv.assertFormula(tm.mkTerm(Kind.EQUAL, same_entity, same_entity_def))
    if not erased:
        antecedent = tm.mkTerm(Kind.AND, hell_old, admitted_new)
        consequent = tm.mkTerm(Kind.AND, logged_replay, fresh_tuple, tm.mkTerm(Kind.NOT, same_entity))
        slv.assertFormula(tm.mkTerm(Kind.IMPLIES, antecedent, consequent))
    for term in (hell_old, admitted_new, same_content, probe_indist, lineage_connected):
        slv.assertFormula(term)
    if replay_case:
        slv.assertFormula(logged_replay)
        slv.assertFormula(fresh_tuple)
        slv.assertFormula(tm.mkTerm(Kind.NOT, same_entity))
    else:
        slv.assertFormula(tm.mkTerm(Kind.NOT, logged_replay))
        slv.assertFormula(tm.mkTerm(Kind.NOT, fresh_tuple))
        slv.assertFormula(same_entity)
    return str(slv.checkSat())


def z3_lex_less(a: tuple[z3.ArithRef, z3.ArithRef, z3.ArithRef], b: tuple[z3.ArithRef, z3.ArithRef, z3.ArithRef]) -> z3.BoolRef:
    return z3.Or(a[0] < b[0], z3.And(a[0] == b[0], a[1] < b[1]), z3.And(a[0] == b[0], a[1] == b[1], a[2] < b[2]))


def z3_progress_gate(erased: bool) -> str:
    solver = z3.Solver()
    changed_x, changed_h, changed_q, non_step = z3.Bools("changed_x changed_h changed_q non_step")
    mu0 = z3.Ints("mu0_0 mu0_1 mu0_2")
    mu1 = z3.Ints("mu1_0 mu1_1 mu1_2")
    solver.add(*(v >= 0 for v in (*mu0, *mu1)))
    solver.add(non_step == z3.Not(z3.Or(changed_x, changed_h, changed_q)))
    effective = z3.Not(non_step)
    if not erased:
        solver.add(z3.Implies(effective, z3_lex_less(mu1, mu0)))
    solver.add(effective, z3.Not(z3_lex_less(mu1, mu0)))
    return str(solver.check())


def z3_nonstep_objectivity_gate() -> str:
    solver = z3.Solver()
    changed_x, changed_h, changed_q, non_step = z3.Bools("changed_x changed_h changed_q non_step")
    solver.add(non_step == z3.Not(z3.Or(changed_x, changed_h, changed_q)))
    solver.add(z3.Not(changed_x), z3.Not(changed_h), z3.Not(changed_q), z3.Not(non_step))
    return str(solver.check())


def cvc5_lex_less(tm: cvc5.TermManager, a: tuple[cvc5.Term, cvc5.Term, cvc5.Term], b: tuple[cvc5.Term, cvc5.Term, cvc5.Term]) -> cvc5.Term:
    return tm.mkTerm(
        Kind.OR,
        tm.mkTerm(Kind.LT, a[0], b[0]),
        tm.mkTerm(Kind.AND, tm.mkTerm(Kind.EQUAL, a[0], b[0]), tm.mkTerm(Kind.LT, a[1], b[1])),
        tm.mkTerm(Kind.AND, tm.mkTerm(Kind.EQUAL, a[0], b[0]), tm.mkTerm(Kind.EQUAL, a[1], b[1]), tm.mkTerm(Kind.LT, a[2], b[2])),
    )


def cvc5_progress_gate(erased: bool) -> str:
    tm = cvc5.TermManager()
    slv = cvc5.Solver(tm)
    slv.setLogic("QF_LIA")
    changed_x = cvc5_bool_const(tm, "changed_x")
    changed_h = cvc5_bool_const(tm, "changed_h")
    changed_q = cvc5_bool_const(tm, "changed_q")
    non_step = cvc5_bool_const(tm, "non_step")
    isort = tm.getIntegerSort()
    zero = tm.mkInteger(0)
    mu0 = tuple(tm.mkConst(isort, f"mu0_{i}") for i in range(3))
    mu1 = tuple(tm.mkConst(isort, f"mu1_{i}") for i in range(3))
    for term in (*mu0, *mu1):
        slv.assertFormula(tm.mkTerm(Kind.GEQ, term, zero))
    any_changed = tm.mkTerm(Kind.OR, changed_x, changed_h, changed_q)
    slv.assertFormula(tm.mkTerm(Kind.EQUAL, non_step, tm.mkTerm(Kind.NOT, any_changed)))
    effective = tm.mkTerm(Kind.NOT, non_step)
    less = cvc5_lex_less(tm, mu1, mu0)
    if not erased:
        slv.assertFormula(tm.mkTerm(Kind.IMPLIES, effective, less))
    slv.assertFormula(effective)
    slv.assertFormula(tm.mkTerm(Kind.NOT, less))
    return str(slv.checkSat())


def cvc5_nonstep_objectivity_gate() -> str:
    tm = cvc5.TermManager()
    slv = cvc5.Solver(tm)
    slv.setLogic("QF_UF")
    changed_x = cvc5_bool_const(tm, "changed_x")
    changed_h = cvc5_bool_const(tm, "changed_h")
    changed_q = cvc5_bool_const(tm, "changed_q")
    non_step = cvc5_bool_const(tm, "non_step")
    any_changed = tm.mkTerm(Kind.OR, changed_x, changed_h, changed_q)
    slv.assertFormula(tm.mkTerm(Kind.EQUAL, non_step, tm.mkTerm(Kind.NOT, any_changed)))
    for term in (changed_x, changed_h, changed_q, non_step):
        slv.assertFormula(tm.mkTerm(Kind.NOT, term))
    return str(slv.checkSat())


def smt_gates() -> dict[str, Any]:
    token = {
        "formal_criterion": "token=(content,lineage_id,branch_id,replay_receipt_id); same-entity iff identical content, probe-indistinguishable, lineage-connected, and no logged replay receipt",
        "polarity": "bad same-identity reentry must be UNSAT; explicit replay with fresh tuple must be SAT-as-new-branch",
        "without_fresh_identity_tuple": {
            "z3_with_axioms": z3_token_identity_gate(erased=False, replay_case=False),
            "z3_erased_axioms": z3_token_identity_gate(erased=True, replay_case=False),
            "cvc5_with_axioms": cvc5_token_identity_gate(erased=False, replay_case=False),
            "cvc5_erased_axioms": cvc5_token_identity_gate(erased=True, replay_case=False),
        },
        "with_logged_replay_receipt": {
            "z3_with_axioms": z3_token_identity_gate(erased=False, replay_case=True),
            "cvc5_with_axioms": cvc5_token_identity_gate(erased=False, replay_case=True),
        },
    }
    token["gate_pass"] = (
        token["without_fresh_identity_tuple"]["z3_with_axioms"] == "unsat"
        and token["without_fresh_identity_tuple"]["z3_erased_axioms"] == "sat"
        and token["without_fresh_identity_tuple"]["cvc5_with_axioms"] == "unsat"
        and token["without_fresh_identity_tuple"]["cvc5_erased_axioms"] == "sat"
        and token["with_logged_replay_receipt"]["z3_with_axioms"] == "sat"
        and token["with_logged_replay_receipt"]["cvc5_with_axioms"] == "sat"
    )
    progress = {
        "codomain": "N^3 with strict lexicographic order",
        "open_choice": True,
        "open_choice_reason": "The source spec requires mu but does not fix codomain/order; N^3 keeps survivor, status, and receipt budgets separate.",
        "non_step_predicate": "non_step iff changed_X=false and changed_H=false and changed_observable_quotient=false",
        "polarity": "effective step with non-decreasing mu is UNSAT under axiom; erased control is SAT",
        "strict_decrease": {
            "z3_with_axioms": z3_progress_gate(erased=False),
            "z3_erased_axioms": z3_progress_gate(erased=True),
            "cvc5_with_axioms": cvc5_progress_gate(erased=False),
            "cvc5_erased_axioms": cvc5_progress_gate(erased=True),
        },
        "non_step_objectivity": {
            "z3_definition_violation": z3_nonstep_objectivity_gate(),
            "cvc5_definition_violation": cvc5_nonstep_objectivity_gate(),
        },
    }
    progress["gate_pass"] = (
        progress["strict_decrease"]["z3_with_axioms"] == "unsat"
        and progress["strict_decrease"]["z3_erased_axioms"] == "sat"
        and progress["strict_decrease"]["cvc5_with_axioms"] == "unsat"
        and progress["strict_decrease"]["cvc5_erased_axioms"] == "sat"
        and progress["non_step_objectivity"]["z3_definition_violation"] == "unsat"
        and progress["non_step_objectivity"]["cvc5_definition_violation"] == "unsat"
    )
    progress["termination_argument"] = "Strict descent in N^3 lexicographic order is well-founded; the survivor stream terminates because the finite carrier gives a finite initial rank and every effective survivor step must strictly decrease it."
    return {"token_identity_R5": token, "progress_measure_R6": progress}


def carrier_json(states: list[CarrierState], projection: dict[str, int]) -> list[dict[str, Any]]:
    out = []
    for state in states:
        out.append(
            {
                "label": state.label,
                "family": state.family,
                "quotient_class": projection[state.label],
                "pvec": [float(v) for v in state.pvec],
                "trace": float(np.trace(state.rho).real),
                "min_eig": float(np.min(np.linalg.eigvalsh((state.rho + state.rho.conj().T) / 2))),
            }
        )
    return out


def main() -> None:
    RESULTS.mkdir(exist_ok=True)
    states = enumerate_carrier()
    quotient = quotient_classes(states)
    xi_ref = xi_ref_lift_check(states, quotient)
    smt = smt_gates()
    runtime_caveat = {
        "doctor_summary": "doctor was not green in this session: quimb and clifford import-cache checks failed; active installer scan was blocked by sandbox ps permission",
        "used_for_this_gate": ["numpy", "scipy via oracle_targets_3q.py", "z3", "cvc5"],
        "install_attempted": False,
    }
    result = {
        "schema": "codex_ratchet.ratchet_formal_gates_v1.numpy_result.v1",
        "generated_at": now_iso(),
        "sim_id": SIM_ID,
        "classification": classification,
        "claim_ceiling": "formal_gate_diagnostic_only",
        "promotion_allowed": promotion_allowed,
        "formal_admission_allowed": formal_admission_allowed,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "carrier_source": "system_v7/constraint_core/engines/oracle_targets_3q.py",
        "runtime_caveat": runtime_caveat,
        "carrier_summary": {
            "hilbert_space": "C^8",
            "state_count": len(states),
            "probe_count": len(oracle.STRINGS),
            "pauli_strings": oracle.STRINGS,
            "full_enumeration": True,
            "sampling": False,
            "families": {name: sum(1 for s in states if s.family == name) for name in sorted({s.family for s in states})},
        },
        "carrier_states": carrier_json(states, quotient["projection"]),
        "gates": {
            **smt,
            "observable_quotient_R4": quotient,
            "xi_ref_quotient_lift": xi_ref,
        },
    }
    result["all_pass"] = all(gate.get("gate_pass", False) for gate in result["gates"].values())
    out = RESULTS / f"{SIM_ID}_numpy_results.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"result_path": str(out), "all_pass": result["all_pass"], "gate_verdicts": {k: v.get("gate_pass") for k, v in result["gates"].items()}}, indent=2))


if __name__ == "__main__":
    main()
