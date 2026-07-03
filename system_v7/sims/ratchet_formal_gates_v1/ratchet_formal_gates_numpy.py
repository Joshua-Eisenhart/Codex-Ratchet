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


def probe_indices(labels: list[str]) -> list[int]:
    return [oracle.STRINGS.index(label) for label in labels]


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


def roster_formula(states: list[CarrierState]) -> dict[str, Any]:
    native_counts = {str(t): len(oracle.NATIVE[t]) for t in range(8)}
    expected = sum(1 + 2 * len(oracle.NATIVE[t]) for t in range(8))
    return {
        "formula": "8 terrains x (1 fixed + 2 native operators x 2 order states)",
        "computed_from_oracle_NATIVE": "sum_t(1 fixed + 2 order states * len(oracle.NATIVE[t]))",
        "native_operator_counts": native_counts,
        "expected_count": expected,
        "actual_count": len(states),
        "count_matches_formula": len(states) == expected,
    }


def quotient_classes_for_indices(
    states: list[CarrierState],
    indices: list[int],
    *,
    probe_epoch_id: str,
    definition: str,
    ndigits: int = 12,
) -> dict[str, Any]:
    buckets: dict[tuple[float, ...], list[CarrierState]] = defaultdict(list)
    for state in states:
        epoch_pvec = tuple(state.pvec[i] for i in indices)
        buckets[rounded_pvec_key(epoch_pvec, ndigits=ndigits)].append(state)
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
        avec = np.asarray([a.pvec[i] for i in indices])
        bvec = np.asarray([b.pvec[i] for i in indices])
        diff_norm = float(np.linalg.norm(avec - bvec))
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
        "probe_epoch_id": probe_epoch_id,
        "definition": definition,
        "rounding_digits": ndigits,
        "non_circularity": "depends only on carrier states and finite probe family; no update maps, admissibility predicates, or Xi candidates are referenced",
        "probe_count": len(indices),
        "probe_labels": [oracle.STRINGS[i] for i in indices],
        "carrier_count": len(states),
        "roster_formula": roster_formula(states),
        "quotient_class_count": len(classes),
        "class_sizes": [c["size"] for c in classes],
        "multi_representative_class_count": sum(1 for c in classes if c["size"] > 1),
        "classes": classes,
        "projection": projection,
        "pair_check_count": len(pair_checks),
        "surviving_difference_count": sum(1 for p in pair_checks if p["difference_survives_observable_quotient"]),
        "collapsed_pair_count": sum(1 for p in pair_checks if p["same_class"]),
        "max_collapsed_pair_probe_l2": max((p["probe_l2"] for p in pair_checks if p["same_class"]), default=0.0),
        "min_surviving_pair_probe_l2": min((p["probe_l2"] for p in pair_checks if not p["same_class"]), default=0.0),
        "gate_pass": len(classes) > 0,
    }


def coarse_probe_quotient_classes(states: list[CarrierState]) -> dict[str, Any]:
    return quotient_classes_for_indices(
        states,
        probe_indices(["ZII"]),
        probe_epoch_id="M_coarse_single_qubit_Z",
        definition="rho_a ~_M_coarse rho_b iff the first-qubit Z expectation ZII agrees after deterministic coarse rounding to the nearest integer",
        ndigits=0,
    )


def probe_epoching(full: dict[str, Any], coarse: dict[str, Any]) -> dict[str, Any]:
    coarse_to_full: dict[int, set[int]] = defaultdict(set)
    full_to_coarse: dict[int, int] = {}
    for label, full_class in full["projection"].items():
        coarse_class = coarse["projection"][label]
        coarse_to_full[coarse_class].add(full_class)
        full_to_coarse[full_class] = coarse_class
    merge_examples = [
        {
            "coarse_class": coarse_class,
            "merged_full_classes": sorted(full_classes),
            "labels": coarse["classes"][coarse_class]["labels"],
        }
        for coarse_class, full_classes in sorted(coarse_to_full.items())
        if len(full_classes) > 1
    ]
    return {
        "equivalence_scope": "within_epoch_only",
        "cross_epoch_identity_rule": "requires_reprojection",
        "two_epoch_example": {
            "full_pauli_epoch": {
                "epoch_id": full["probe_epoch_id"],
                "probe_count": full["probe_count"],
                "quotient_class_count": full["quotient_class_count"],
                "multi_representative_class_count": full["multi_representative_class_count"],
            },
            "coarse_z_epoch": {
                "epoch_id": coarse["probe_epoch_id"],
                "probe_count": coarse["probe_count"],
                "quotient_class_count": coarse["quotient_class_count"],
                "multi_representative_class_count": coarse["multi_representative_class_count"],
            },
            "merge_examples": merge_examples[:5],
            "full_class_to_coarse_reprojection_sample": dict(list(sorted(full_to_coarse.items()))[:10]),
            "classes_split_or_merge_across_epochs": bool(merge_examples) or full["quotient_class_count"] != coarse["quotient_class_count"],
            "lineage_survives_reprojection": set(full["projection"]) == set(coarse["projection"]),
        },
    }


def quotient_classes(states: list[CarrierState]) -> dict[str, Any]:
    full = quotient_classes_for_indices(
        states,
        list(range(len(oracle.STRINGS))),
        probe_epoch_id="M_full_pauli_63",
        definition="rho_a ~_M_full rho_b iff every one of the 63 non-identity 3-qubit Pauli expectations is equal after deterministic rounding at 12 decimals",
    )
    coarse = coarse_probe_quotient_classes(states)
    full["probe_epoching"] = probe_epoching(full, coarse)
    full["gate_pass"] = (
        full["gate_pass"]
        and full["probe_count"] == 63
        and full["roster_formula"]["count_matches_formula"]
        and full["roster_formula"]["expected_count"] == 40
        and full["probe_epoching"]["two_epoch_example"]["lineage_survives_reprojection"]
        and full["probe_epoching"]["two_epoch_example"]["coarse_z_epoch"]["multi_representative_class_count"] > 0
    )
    return full


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
    nontrivial = sum(1 for c in classes if c["size"] > 1) > 0
    status = "quotient_lift_constructed_nontrivial" if nontrivial and not failures else "demoted_to_raw_carrier_discriminator"
    return {
        "probe_epoch_id": quotient.get("probe_epoch_id", "unknown"),
        "definition": "Xi_ref(c_ref,c) is the representative-independent value of the point-reference descriptor computed from any x_ref in c_ref and x in c",
        "raw_descriptor": "cut qubit selected by reference representative local Pauli strength; target value is coherent information S(B)-S(AB) plus local XYZ readout on that cut",
        "well_definedness_condition": "for every c_ref,c, all representative pairs produce identical descriptors at 12 decimals",
        "checked_class_pairs": checked_pairs,
        "multi_representative_class_count": sum(1 for c in classes if c["size"] > 1),
        "max_descriptor_spread": max_descriptor_spread,
        "failure_count": len(failures),
        "failures": failures[:20],
        "status": status,
        "gate_pass": nontrivial and not failures,
        "lifted_values": lifted,
    }


TOKEN_DOMAIN_BOUNDS = {
    "content_id": (0, 2),
    "probe_signature": (0, 2),
    "lineage_id": (0, 1),
    "branch_id": (0, 1),
    "replay_receipt_id": (0, 1),
}


def z3_in_domain(value: z3.ArithRef, lo: int, hi: int) -> z3.BoolRef:
    return z3.And(value >= lo, value <= hi)


def z3_token_fields(prefix: str) -> dict[str, z3.ArithRef]:
    return {name: z3.Int(f"{prefix}_{name}") for name in TOKEN_DOMAIN_BOUNDS}


def z3_token_domain(fields: dict[str, z3.ArithRef]) -> list[z3.BoolRef]:
    return [z3_in_domain(fields[name], lo, hi) for name, (lo, hi) in TOKEN_DOMAIN_BOUNDS.items()]


def z3_same_entity(a: dict[str, z3.ArithRef], b: dict[str, z3.ArithRef]) -> z3.BoolRef:
    return z3.And(
        a["probe_signature"] == b["probe_signature"],
        a["lineage_id"] == b["lineage_id"],
        a["branch_id"] == b["branch_id"],
        a["replay_receipt_id"] == 0,
        b["replay_receipt_id"] == 0,
    )


def z3_fresh(a: dict[str, z3.ArithRef], b: dict[str, z3.ArithRef]) -> z3.BoolRef:
    return z3.Or(
        a["probe_signature"] != b["probe_signature"],
        a["lineage_id"] != b["lineage_id"],
        a["branch_id"] != b["branch_id"],
        a["replay_receipt_id"] != 0,
        b["replay_receipt_id"] != 0,
    )


def z3_replay(a: dict[str, z3.ArithRef], b: dict[str, z3.ArithRef]) -> z3.BoolRef:
    return z3.And(
        a["probe_signature"] == b["probe_signature"],
        a["lineage_id"] == b["lineage_id"],
        z3.Or(a["replay_receipt_id"] != 0, b["replay_receipt_id"] != 0),
    )


def z3_token_identity_gate(erased: bool, scenario: str) -> str:
    solver = z3.Solver()
    old = z3_token_fields(f"{scenario}_old")
    new = z3_token_fields(f"{scenario}_new")
    solver.add(*(z3_token_domain(old) + z3_token_domain(new)))
    same_entity = z3_same_entity(old, new) if not erased else z3.Bool(f"{scenario}_same_entity_erased")
    fresh = z3_fresh(old, new) if not erased else z3.Bool(f"{scenario}_fresh_erased")
    replay = z3_replay(old, new) if not erased else z3.Bool(f"{scenario}_replay_erased")
    if scenario == "content_perturbation_same_probe_signature":
        solver.add(old["content_id"] != new["content_id"])
        solver.add(old["probe_signature"] == new["probe_signature"])
        solver.add(old["lineage_id"] == new["lineage_id"], old["branch_id"] == new["branch_id"])
        solver.add(old["replay_receipt_id"] == 0, new["replay_receipt_id"] == 0)
        solver.add(z3.Not(same_entity))
    elif scenario == "different_probe_signature":
        solver.add(old["content_id"] == new["content_id"])
        solver.add(old["probe_signature"] != new["probe_signature"])
        solver.add(old["lineage_id"] == new["lineage_id"], old["branch_id"] == new["branch_id"])
        solver.add(old["replay_receipt_id"] == 0, new["replay_receipt_id"] == 0)
        solver.add(same_entity)
    elif scenario == "replay_receipt_opens_fresh_branch":
        solver.add(old["content_id"] == new["content_id"])
        solver.add(old["probe_signature"] == new["probe_signature"])
        solver.add(old["lineage_id"] == new["lineage_id"])
        solver.add(old["branch_id"] == new["branch_id"])
        solver.add(old["replay_receipt_id"] == 0, new["replay_receipt_id"] != 0)
        solver.add(z3.Not(fresh), z3.Not(replay), same_entity)
    else:
        raise ValueError(f"unknown token scenario {scenario}")
    return str(solver.check())


def cvc5_bool_const(tm: cvc5.TermManager, name: str) -> cvc5.Term:
    return tm.mkConst(tm.getBooleanSort(), name)


def cvc5_int_const(tm: cvc5.TermManager, name: str) -> cvc5.Term:
    return tm.mkConst(tm.getIntegerSort(), name)


def cvc5_int(tm: cvc5.TermManager, value: int) -> cvc5.Term:
    return tm.mkInteger(value)


def cvc5_token_fields(tm: cvc5.TermManager, prefix: str) -> dict[str, cvc5.Term]:
    return {name: cvc5_int_const(tm, f"{prefix}_{name}") for name in TOKEN_DOMAIN_BOUNDS}


def cvc5_token_domain(tm: cvc5.TermManager, fields: dict[str, cvc5.Term]) -> list[cvc5.Term]:
    return [
        tm.mkTerm(Kind.AND, tm.mkTerm(Kind.GEQ, fields[name], cvc5_int(tm, lo)), tm.mkTerm(Kind.LEQ, fields[name], cvc5_int(tm, hi)))
        for name, (lo, hi) in TOKEN_DOMAIN_BOUNDS.items()
    ]


def cvc5_eq(tm: cvc5.TermManager, a: cvc5.Term, b: cvc5.Term) -> cvc5.Term:
    return tm.mkTerm(Kind.EQUAL, a, b)


def cvc5_neq(tm: cvc5.TermManager, a: cvc5.Term, b: cvc5.Term) -> cvc5.Term:
    return tm.mkTerm(Kind.NOT, cvc5_eq(tm, a, b))


def cvc5_same_entity(tm: cvc5.TermManager, a: dict[str, cvc5.Term], b: dict[str, cvc5.Term]) -> cvc5.Term:
    return tm.mkTerm(
        Kind.AND,
        cvc5_eq(tm, a["probe_signature"], b["probe_signature"]),
        cvc5_eq(tm, a["lineage_id"], b["lineage_id"]),
        cvc5_eq(tm, a["branch_id"], b["branch_id"]),
        cvc5_eq(tm, a["replay_receipt_id"], cvc5_int(tm, 0)),
        cvc5_eq(tm, b["replay_receipt_id"], cvc5_int(tm, 0)),
    )


def cvc5_fresh(tm: cvc5.TermManager, a: dict[str, cvc5.Term], b: dict[str, cvc5.Term]) -> cvc5.Term:
    return tm.mkTerm(
        Kind.OR,
        cvc5_neq(tm, a["probe_signature"], b["probe_signature"]),
        cvc5_neq(tm, a["lineage_id"], b["lineage_id"]),
        cvc5_neq(tm, a["branch_id"], b["branch_id"]),
        cvc5_neq(tm, a["replay_receipt_id"], cvc5_int(tm, 0)),
        cvc5_neq(tm, b["replay_receipt_id"], cvc5_int(tm, 0)),
    )


def cvc5_replay(tm: cvc5.TermManager, a: dict[str, cvc5.Term], b: dict[str, cvc5.Term]) -> cvc5.Term:
    return tm.mkTerm(
        Kind.AND,
        cvc5_eq(tm, a["probe_signature"], b["probe_signature"]),
        cvc5_eq(tm, a["lineage_id"], b["lineage_id"]),
        tm.mkTerm(Kind.OR, cvc5_neq(tm, a["replay_receipt_id"], cvc5_int(tm, 0)), cvc5_neq(tm, b["replay_receipt_id"], cvc5_int(tm, 0))),
    )


def cvc5_token_identity_gate(erased: bool, scenario: str) -> str:
    tm = cvc5.TermManager()
    slv = cvc5.Solver(tm)
    slv.setLogic("QF_LIA")
    old = cvc5_token_fields(tm, f"{scenario}_old")
    new = cvc5_token_fields(tm, f"{scenario}_new")
    for formula in cvc5_token_domain(tm, old) + cvc5_token_domain(tm, new):
        slv.assertFormula(formula)
    same_entity = cvc5_same_entity(tm, old, new) if not erased else cvc5_bool_const(tm, f"{scenario}_same_entity_erased")
    fresh = cvc5_fresh(tm, old, new) if not erased else cvc5_bool_const(tm, f"{scenario}_fresh_erased")
    replay = cvc5_replay(tm, old, new) if not erased else cvc5_bool_const(tm, f"{scenario}_replay_erased")
    if scenario == "content_perturbation_same_probe_signature":
        slv.assertFormula(cvc5_neq(tm, old["content_id"], new["content_id"]))
        slv.assertFormula(cvc5_eq(tm, old["probe_signature"], new["probe_signature"]))
        slv.assertFormula(cvc5_eq(tm, old["lineage_id"], new["lineage_id"]))
        slv.assertFormula(cvc5_eq(tm, old["branch_id"], new["branch_id"]))
        slv.assertFormula(cvc5_eq(tm, old["replay_receipt_id"], cvc5_int(tm, 0)))
        slv.assertFormula(cvc5_eq(tm, new["replay_receipt_id"], cvc5_int(tm, 0)))
        slv.assertFormula(tm.mkTerm(Kind.NOT, same_entity))
    elif scenario == "different_probe_signature":
        slv.assertFormula(cvc5_eq(tm, old["content_id"], new["content_id"]))
        slv.assertFormula(cvc5_neq(tm, old["probe_signature"], new["probe_signature"]))
        slv.assertFormula(cvc5_eq(tm, old["lineage_id"], new["lineage_id"]))
        slv.assertFormula(cvc5_eq(tm, old["branch_id"], new["branch_id"]))
        slv.assertFormula(cvc5_eq(tm, old["replay_receipt_id"], cvc5_int(tm, 0)))
        slv.assertFormula(cvc5_eq(tm, new["replay_receipt_id"], cvc5_int(tm, 0)))
        slv.assertFormula(same_entity)
    elif scenario == "replay_receipt_opens_fresh_branch":
        slv.assertFormula(cvc5_eq(tm, old["content_id"], new["content_id"]))
        slv.assertFormula(cvc5_eq(tm, old["probe_signature"], new["probe_signature"]))
        slv.assertFormula(cvc5_eq(tm, old["lineage_id"], new["lineage_id"]))
        slv.assertFormula(cvc5_eq(tm, old["branch_id"], new["branch_id"]))
        slv.assertFormula(cvc5_eq(tm, old["replay_receipt_id"], cvc5_int(tm, 0)))
        slv.assertFormula(cvc5_neq(tm, new["replay_receipt_id"], cvc5_int(tm, 0)))
        slv.assertFormula(tm.mkTerm(Kind.NOT, fresh))
        slv.assertFormula(tm.mkTerm(Kind.NOT, replay))
        slv.assertFormula(same_entity)
    else:
        raise ValueError(f"unknown token scenario {scenario}")
    return str(slv.checkSat())


def z3_lex_less(a: tuple[z3.ArithRef, z3.ArithRef, z3.ArithRef], b: tuple[z3.ArithRef, z3.ArithRef, z3.ArithRef]) -> z3.BoolRef:
    return z3.Or(a[0] < b[0], z3.And(a[0] == b[0], a[1] < b[1]), z3.And(a[0] == b[0], a[1] == b[1], a[2] < b[2]))


def z3_registers(prefix: str) -> tuple[z3.ArithRef, z3.ArithRef, z3.ArithRef]:
    return z3.Ints(f"{prefix}_X {prefix}_H {prefix}_Q")


def z3_register_domain(reg: tuple[z3.ArithRef, z3.ArithRef, z3.ArithRef]) -> list[z3.BoolRef]:
    x, h, q = reg
    return [x >= 0, x <= 7, h >= 0, h <= 9, q >= 0, q <= 40]


def z3_progress_gate(erased: bool) -> str:
    solver = z3.Solver()
    pre = z3_registers("pre")
    post = z3_registers("post")
    mu0 = z3.Ints("mu0_0 mu0_1 mu0_2")
    mu1 = z3.Ints("mu1_0 mu1_1 mu1_2")
    solver.add(*(z3_register_domain(pre) + z3_register_domain(post)))
    solver.add(*(v >= 0 for v in (*mu0, *mu1)))
    changed_x = pre[0] != post[0]
    changed_h = pre[1] != post[1]
    changed_q = pre[2] != post[2]
    non_step = z3.Not(z3.Or(changed_x, changed_h, changed_q))
    effective = z3.Not(non_step)
    if not erased:
        solver.add(z3.Implies(effective, z3_lex_less(mu1, mu0)))
    solver.add(effective, z3.Not(z3_lex_less(mu1, mu0)))
    return str(solver.check())


def z3_nonstep_objectivity_gate() -> str:
    solver = z3.Solver()
    pre = z3_registers("objective_pre")
    post = z3_registers("objective_post")
    solver.add(*(z3_register_domain(pre) + z3_register_domain(post)))
    changed_x = pre[0] != post[0]
    changed_h = pre[1] != post[1]
    changed_q = pre[2] != post[2]
    non_step = z3.Not(z3.Or(changed_x, changed_h, changed_q))
    solver.add(pre[0] == post[0], pre[1] == post[1], pre[2] == post[2], z3.Not(non_step))
    return str(solver.check())


def z3_fuel_stutter_gate(erased: bool, k_bound: int) -> str:
    solver = z3.Solver()
    steps = k_bound + 1
    for idx in range(steps):
        pre = z3_registers(f"stutter_{idx}_pre")
        post = z3_registers(f"stutter_{idx}_post")
        solver.add(*(z3_register_domain(pre) + z3_register_domain(post)))
        non_step = z3.Not(z3.Or(pre[0] != post[0], pre[1] != post[1], pre[2] != post[2]))
        solver.add(non_step)
    consecutive_nonsteps = z3.Int("consecutive_nonsteps")
    solver.add(consecutive_nonsteps == steps)
    if not erased:
        solver.add(consecutive_nonsteps <= k_bound)
    solver.add(consecutive_nonsteps > k_bound)
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
    isort = tm.getIntegerSort()
    zero = tm.mkInteger(0)
    pre = tuple(tm.mkConst(isort, f"pre_{name}") for name in ("X", "H", "Q"))
    post = tuple(tm.mkConst(isort, f"post_{name}") for name in ("X", "H", "Q"))
    bounds = ((0, 7), (0, 9), (0, 40))
    for term_tuple in (pre, post):
        for term, (lo, hi) in zip(term_tuple, bounds):
            slv.assertFormula(tm.mkTerm(Kind.GEQ, term, tm.mkInteger(lo)))
            slv.assertFormula(tm.mkTerm(Kind.LEQ, term, tm.mkInteger(hi)))
    mu0 = tuple(tm.mkConst(isort, f"mu0_{i}") for i in range(3))
    mu1 = tuple(tm.mkConst(isort, f"mu1_{i}") for i in range(3))
    for term in (*mu0, *mu1):
        slv.assertFormula(tm.mkTerm(Kind.GEQ, term, zero))
    any_changed = tm.mkTerm(Kind.OR, cvc5_neq(tm, pre[0], post[0]), cvc5_neq(tm, pre[1], post[1]), cvc5_neq(tm, pre[2], post[2]))
    non_step = tm.mkTerm(Kind.NOT, any_changed)
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
    slv.setLogic("QF_LIA")
    isort = tm.getIntegerSort()
    pre = tuple(tm.mkConst(isort, f"objective_pre_{name}") for name in ("X", "H", "Q"))
    post = tuple(tm.mkConst(isort, f"objective_post_{name}") for name in ("X", "H", "Q"))
    bounds = ((0, 7), (0, 9), (0, 40))
    for term_tuple in (pre, post):
        for term, (lo, hi) in zip(term_tuple, bounds):
            slv.assertFormula(tm.mkTerm(Kind.GEQ, term, tm.mkInteger(lo)))
            slv.assertFormula(tm.mkTerm(Kind.LEQ, term, tm.mkInteger(hi)))
    any_changed = tm.mkTerm(Kind.OR, cvc5_neq(tm, pre[0], post[0]), cvc5_neq(tm, pre[1], post[1]), cvc5_neq(tm, pre[2], post[2]))
    non_step = tm.mkTerm(Kind.NOT, any_changed)
    for i in range(3):
        slv.assertFormula(cvc5_eq(tm, pre[i], post[i]))
    slv.assertFormula(tm.mkTerm(Kind.NOT, non_step))
    return str(slv.checkSat())


def cvc5_fuel_stutter_gate(erased: bool, k_bound: int) -> str:
    tm = cvc5.TermManager()
    slv = cvc5.Solver(tm)
    slv.setLogic("QF_LIA")
    isort = tm.getIntegerSort()
    bounds = ((0, 7), (0, 9), (0, 40))
    steps = k_bound + 1
    for idx in range(steps):
        pre = tuple(tm.mkConst(isort, f"stutter_{idx}_pre_{name}") for name in ("X", "H", "Q"))
        post = tuple(tm.mkConst(isort, f"stutter_{idx}_post_{name}") for name in ("X", "H", "Q"))
        for term_tuple in (pre, post):
            for term, (lo, hi) in zip(term_tuple, bounds):
                slv.assertFormula(tm.mkTerm(Kind.GEQ, term, tm.mkInteger(lo)))
                slv.assertFormula(tm.mkTerm(Kind.LEQ, term, tm.mkInteger(hi)))
        any_changed = tm.mkTerm(Kind.OR, cvc5_neq(tm, pre[0], post[0]), cvc5_neq(tm, pre[1], post[1]), cvc5_neq(tm, pre[2], post[2]))
        slv.assertFormula(tm.mkTerm(Kind.NOT, any_changed))
    consecutive = tm.mkConst(isort, "consecutive_nonsteps")
    slv.assertFormula(cvc5_eq(tm, consecutive, tm.mkInteger(steps)))
    if not erased:
        slv.assertFormula(tm.mkTerm(Kind.LEQ, consecutive, tm.mkInteger(k_bound)))
    slv.assertFormula(tm.mkTerm(Kind.GT, consecutive, tm.mkInteger(k_bound)))
    return str(slv.checkSat())


def smt_gates() -> dict[str, Any]:
    k_bound = 2
    token = {
        "formal_criterion": "token=(content_id,probe_signature,lineage_id,branch_id,replay_receipt_id); same_entity/fresh/replay are derived from tuple field equalities over finite domains",
        "identity_grounding": "probe_signature_not_content_id",
        "content_id_role": "provenance_metadata_only",
        "domain_quantification": {
            "finite_domains": TOKEN_DOMAIN_BOUNDS,
            "all_tuple_pairs_checked": True,
            "solver_shape": "existential counterexample search over bounded tuple fields; UNSAT means no tuple in the finite domain violates the derived law",
        },
        "derived_predicates": {
            "same_entity": "same probe_signature, same lineage_id, same branch_id, and both replay_receipt_id=0; content_id is ignored",
            "fresh": "different probe_signature or lineage_id or branch_id, or either replay_receipt_id nonzero",
            "replay": "same probe_signature and lineage_id with either replay_receipt_id nonzero",
        },
        "polarity": "derived-law violation scenarios must be UNSAT under field-derived predicates and SAT when predicate axioms are erased",
        "content_perturbation_same_probe_signature": {
            "meaning": "different content_id with identical probe_signature remains same entity; laundering by content perturbation is caught",
            "z3_violation": z3_token_identity_gate(erased=False, scenario="content_perturbation_same_probe_signature"),
            "z3_erased_predicates": z3_token_identity_gate(erased=True, scenario="content_perturbation_same_probe_signature"),
            "cvc5_violation": cvc5_token_identity_gate(erased=False, scenario="content_perturbation_same_probe_signature"),
            "cvc5_erased_predicates": cvc5_token_identity_gate(erased=True, scenario="content_perturbation_same_probe_signature"),
        },
        "different_probe_signature": {
            "meaning": "same content_id with different probe_signature is genuinely different",
            "z3_violation": z3_token_identity_gate(erased=False, scenario="different_probe_signature"),
            "z3_erased_predicates": z3_token_identity_gate(erased=True, scenario="different_probe_signature"),
            "cvc5_violation": cvc5_token_identity_gate(erased=False, scenario="different_probe_signature"),
            "cvc5_erased_predicates": cvc5_token_identity_gate(erased=True, scenario="different_probe_signature"),
        },
        "replay_receipt_opens_fresh_branch": {
            "meaning": "same probe_signature/lineage/branch plus logged replay receipt is replay and fresh, not same_entity",
            "z3_violation": z3_token_identity_gate(erased=False, scenario="replay_receipt_opens_fresh_branch"),
            "z3_erased_predicates": z3_token_identity_gate(erased=True, scenario="replay_receipt_opens_fresh_branch"),
            "cvc5_violation": cvc5_token_identity_gate(erased=False, scenario="replay_receipt_opens_fresh_branch"),
            "cvc5_erased_predicates": cvc5_token_identity_gate(erased=True, scenario="replay_receipt_opens_fresh_branch"),
        },
    }
    token["gate_pass"] = (
        token["content_perturbation_same_probe_signature"]["z3_violation"] == "unsat"
        and token["content_perturbation_same_probe_signature"]["z3_erased_predicates"] == "sat"
        and token["content_perturbation_same_probe_signature"]["cvc5_violation"] == "unsat"
        and token["content_perturbation_same_probe_signature"]["cvc5_erased_predicates"] == "sat"
        and token["different_probe_signature"]["z3_violation"] == "unsat"
        and token["different_probe_signature"]["z3_erased_predicates"] == "sat"
        and token["different_probe_signature"]["cvc5_violation"] == "unsat"
        and token["different_probe_signature"]["cvc5_erased_predicates"] == "sat"
        and token["replay_receipt_opens_fresh_branch"]["z3_violation"] == "unsat"
        and token["replay_receipt_opens_fresh_branch"]["z3_erased_predicates"] == "sat"
        and token["replay_receipt_opens_fresh_branch"]["cvc5_violation"] == "unsat"
        and token["replay_receipt_opens_fresh_branch"]["cvc5_erased_predicates"] == "sat"
    )
    progress = {
        "codomain": "N^3 with strict lexicographic order",
        "open_choice": True,
        "open_choice_reason": "The source spec requires mu but does not fix codomain/order; N^3 keeps survivor, status, and receipt budgets separate.",
        "registers": {"X": "finite set bitmask", "H": "finite counter/sequence id", "Q": "finite quotient class count"},
        "non_step_predicate": "derived: non_step iff X_pre=X_post and H_pre=H_post and Q_pre=Q_post",
        "polarity": "effective step with non-decreasing mu is UNSAT under axiom; erased control is SAT; >K consecutive non-steps is UNSAT under fuel and SAT when fuel is erased",
        "strict_decrease": {
            "z3_with_axioms": z3_progress_gate(erased=False),
            "z3_erased_axioms": z3_progress_gate(erased=True),
            "cvc5_with_axioms": cvc5_progress_gate(erased=False),
            "cvc5_erased_axioms": cvc5_progress_gate(erased=True),
        },
        "register_equality_objectivity": {
            "z3_definition_violation": z3_nonstep_objectivity_gate(),
            "cvc5_definition_violation": cvc5_nonstep_objectivity_gate(),
        },
        "anti_stall_fuel_bound": {
            "K": k_bound,
            "violation": "more than K consecutive derived non-steps is process failure, not a rest state",
            "z3_with_axioms": z3_fuel_stutter_gate(erased=False, k_bound=k_bound),
            "z3_erased_fuel_axiom": z3_fuel_stutter_gate(erased=True, k_bound=k_bound),
            "cvc5_with_axioms": cvc5_fuel_stutter_gate(erased=False, k_bound=k_bound),
            "cvc5_erased_fuel_axiom": cvc5_fuel_stutter_gate(erased=True, k_bound=k_bound),
        },
    }
    progress["gate_pass"] = (
        progress["strict_decrease"]["z3_with_axioms"] == "unsat"
        and progress["strict_decrease"]["z3_erased_axioms"] == "sat"
        and progress["strict_decrease"]["cvc5_with_axioms"] == "unsat"
        and progress["strict_decrease"]["cvc5_erased_axioms"] == "sat"
        and progress["register_equality_objectivity"]["z3_definition_violation"] == "unsat"
        and progress["register_equality_objectivity"]["cvc5_definition_violation"] == "unsat"
        and progress["anti_stall_fuel_bound"]["z3_with_axioms"] == "unsat"
        and progress["anti_stall_fuel_bound"]["z3_erased_fuel_axiom"] == "sat"
        and progress["anti_stall_fuel_bound"]["cvc5_with_axioms"] == "unsat"
        and progress["anti_stall_fuel_bound"]["cvc5_erased_fuel_axiom"] == "sat"
    )
    progress["termination_argument"] = "Strict descent in N^3 lexicographic order is well-founded for effective steps. Derived non-steps are allowed only up to the fuel bound; >K consecutive non-steps is process failure. At full Pauli resolution on density matrices no nontrivial hidden activity exists because 63 expectations determine rho, but coarse probe families reintroduce hidden-activity risk, so the fuel rule is load-bearing for coarse epochs."
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
    coarse_quotient = coarse_probe_quotient_classes(states)
    xi_ref_full = xi_ref_lift_check(states, quotient)
    xi_ref = xi_ref_lift_check(states, coarse_quotient)
    xi_ref_full["status"] = "constructed_untested_nontrivially_at_full_resolution"
    xi_ref_full["gate_pass"] = False
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
            "coarse_probe_quotient_R4_epoch": coarse_quotient,
            "xi_ref_full_resolution_caveat": xi_ref_full,
            "xi_ref_quotient_lift": xi_ref,
        },
    }
    result["all_pass"] = all(
        gate.get("gate_pass", False)
        for name, gate in result["gates"].items()
        if name != "xi_ref_full_resolution_caveat"
    )
    out = RESULTS / f"{SIM_ID}_numpy_results.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"result_path": str(out), "all_pass": result["all_pass"], "gate_verdicts": {k: v.get("gate_pass") for k, v in result["gates"].items()}}, indent=2))


if __name__ == "__main__":
    main()
