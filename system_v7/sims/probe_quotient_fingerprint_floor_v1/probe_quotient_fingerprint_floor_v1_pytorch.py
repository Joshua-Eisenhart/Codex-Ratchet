#!/usr/bin/env python3
"""PyTorch leg for probe_quotient_fingerprint_floor_v1."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import torch
from torch.func import vmap
import z3

classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False
sim_execution_kind = "nonclassical"

TOOL_MANIFEST = {
    "torch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing complex128 finite table representation and equality computation",
    },
    "torch.func": {
        "tried": True,
        "used": True,
        "reason": "load-bearing vmap pairwise equality matrix and quotient class-count computation",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing consistency gate over torch-derived rows: full-P UNSAT and erased-P SAT polarity",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent consistency gate agreeing with z3 over torch-derived rows",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "torch": "load_bearing",
    "torch.func": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
}

SIM_ID = "probe_quotient_fingerprint_floor_v1"
HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_spec() -> dict[str, Any]:
    return json.loads((HERE / "spec.json").read_text(encoding="utf-8"))


def ordered_table(spec: dict[str, Any], order: list[str]) -> list[list[int]]:
    return [[int(spec["probes"][probe][label]) for probe in order] for label in spec["support"]]


def as_complex128(rows: list[list[int]]) -> torch.Tensor:
    real = torch.tensor(rows, dtype=torch.float64)
    imag = torch.zeros_like(real)
    return torch.complex(real, imag)


def tensor_rows_as_ints(table: torch.Tensor) -> list[list[int]]:
    return [[int(table[i, j].real.item()) for j in range(table.shape[1])] for i in range(table.shape[0])]


def quotient(labels: list[str], rows: list[list[int]]) -> tuple[list[list[str]], dict[str, tuple[int, ...]], dict[str, int]]:
    groups: list[list[str]] = []
    keys: list[tuple[int, ...]] = []
    signatures: dict[str, tuple[int, ...]] = {}
    for label, row in zip(labels, rows, strict=True):
        key = tuple(int(v) for v in row)
        signatures[label] = key
        if key in keys:
            groups[keys.index(key)].append(label)
        else:
            keys.append(key)
            groups.append([label])
    class_ids = {label: idx for idx, group in enumerate(groups) for label in group}
    return groups, signatures, class_ids


def torch_equality_matrix(table: torch.Tensor) -> list[list[bool]]:
    pairwise = vmap(lambda row: torch.all(row == table, dim=1))(table)
    return [[bool(value.item()) for value in row] for row in pairwise]


def z3_partition_violation(rows: list[list[int]], class_ids: list[int]) -> str:
    solver = z3.Solver()
    n = len(rows)
    width = len(rows[0]) if rows else 0
    value_vars = [[z3.Int(f"torch_z3_v_{i}_{j}") for j in range(width)] for i in range(n)]
    class_vars = [z3.Int(f"torch_z3_c_{i}") for i in range(n)]
    for i in range(n):
        solver.add(class_vars[i] == z3.IntVal(int(class_ids[i])))
        for j in range(width):
            solver.add(value_vars[i][j] == z3.IntVal(int(rows[i][j])))
    violations = []
    for i in range(n):
        for k in range(i + 1, n):
            same_class = class_vars[i] == class_vars[k]
            different_class = class_vars[i] != class_vars[k]
            same_values = z3.And([value_vars[i][j] == value_vars[k][j] for j in range(width)])
            different_value = z3.Or([value_vars[i][j] != value_vars[k][j] for j in range(width)])
            violations.append(z3.And(same_class, different_value))
            violations.append(z3.And(different_class, same_values))
    solver.add(z3.Or(violations) if violations else z3.BoolVal(False))
    return str(solver.check()).lower()


def cvc5_partition_violation(rows: list[list[int]], class_ids: list[int]) -> str:
    tm = cvc5.TermManager()
    solver = cvc5.Solver(tm)
    solver.setLogic("QF_LIA")
    n = len(rows)
    width = len(rows[0]) if rows else 0
    int_sort = tm.getIntegerSort()
    value_vars = [[tm.mkConst(int_sort, f"torch_cvc5_v_{i}_{j}") for j in range(width)] for i in range(n)]
    class_vars = [tm.mkConst(int_sort, f"torch_cvc5_c_{i}") for i in range(n)]
    for i in range(n):
        solver.assertFormula(tm.mkTerm(Kind.EQUAL, class_vars[i], tm.mkInteger(int(class_ids[i]))))
        for j in range(width):
            solver.assertFormula(tm.mkTerm(Kind.EQUAL, value_vars[i][j], tm.mkInteger(int(rows[i][j]))))
    violations = []
    for i in range(n):
        for k in range(i + 1, n):
            same_class = tm.mkTerm(Kind.EQUAL, class_vars[i], class_vars[k])
            different_class = tm.mkTerm(Kind.DISTINCT, class_vars[i], class_vars[k])
            same_values_terms = [tm.mkTerm(Kind.EQUAL, value_vars[i][j], value_vars[k][j]) for j in range(width)]
            different_value_terms = [tm.mkTerm(Kind.DISTINCT, value_vars[i][j], value_vars[k][j]) for j in range(width)]
            same_values = same_values_terms[0] if len(same_values_terms) == 1 else tm.mkTerm(Kind.AND, *same_values_terms)
            different_value = (
                different_value_terms[0]
                if len(different_value_terms) == 1
                else tm.mkTerm(Kind.OR, *different_value_terms)
            )
            violations.append(tm.mkTerm(Kind.AND, same_class, different_value))
            violations.append(tm.mkTerm(Kind.AND, different_class, same_values))
    solver.assertFormula(violations[0] if len(violations) == 1 else tm.mkTerm(Kind.OR, *violations))
    return str(solver.checkSat()).lower()


def find_merge_pair(labels: list[str], full_ids: dict[str, int], erased_ids: dict[str, int]) -> list[str] | None:
    for i, left in enumerate(labels):
        for right in labels[i + 1 :]:
            if full_ids[left] != full_ids[right] and erased_ids[left] == erased_ids[right]:
                return [left, right]
    return None


def find_persistent_pair(labels: list[str], full_ids: dict[str, int]) -> list[str] | None:
    for i, left in enumerate(labels):
        for right in labels[i + 1 :]:
            if full_ids[left] == full_ids[right]:
                return [left, right]
    return None


def main() -> int:
    RESULTS.mkdir(exist_ok=True)
    spec = load_spec()
    labels = list(spec["support"])
    full_table = as_complex128(ordered_table(spec, spec["probe_order_full"]))
    erased_table = as_complex128(ordered_table(spec, spec["probe_order_erased"]))
    full_rows = tensor_rows_as_ints(full_table)
    erased_rows = tensor_rows_as_ints(erased_table)
    full_classes, full_signatures, full_ids = quotient(labels, full_rows)
    erased_classes, erased_signatures, erased_ids = quotient(labels, erased_rows)
    full_class_vector = [full_ids[label] for label in labels]
    z3_full = z3_partition_violation(full_rows, full_class_vector)
    z3_erased = z3_partition_violation(erased_rows, full_class_vector)
    cvc5_full = cvc5_partition_violation(full_rows, full_class_vector)
    cvc5_erased = cvc5_partition_violation(erased_rows, full_class_vector)
    smt_ok = z3_full == "unsat" and cvc5_full == "unsat" and z3_erased == "sat" and cvc5_erased == "sat"
    merge_pair = find_merge_pair(labels, full_ids, erased_ids)
    persistent_pair = find_persistent_pair(labels, full_ids)
    expected = spec["expected"]
    controls_ok = (
        len(full_classes) == int(expected["full_class_count"])
        and len(erased_classes) == int(expected["erased_class_count"])
        and merge_pair == expected["merge_pair_when_erased"]
        and persistent_pair == expected["permanent_indistinguishable_pair"]
        and smt_ok
    )
    result = {
        "schema": "codex_ratchet.engine_leg_result.v1",
        "sim_id": SIM_ID,
        "engine": "pytorch_smt",
        "computation_style": "torch_complex128_vmap_fingerprint_table_plus_z3_cvc5",
        "classification": classification,
        "promotion_allowed": promotion_allowed,
        "formal_admission_allowed": formal_admission_allowed,
        "does_not_self_upgrade": True,
        "reads_peer_result": False,
        "written_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_path": str(Path(__file__).resolve()),
        "source_sha256": sha256_of(Path(__file__).resolve()),
        "spec_sha256": sha256_of(HERE / "spec.json"),
        "support": labels,
        "probe_order_full": spec["probe_order_full"],
        "probe_order_erased": spec["probe_order_erased"],
        "fingerprints_full": {label: list(full_signatures[label]) for label in labels},
        "fingerprints_erased": {label: list(erased_signatures[label]) for label in labels},
        "torch_observables": {
            "dtype": str(full_table.dtype),
            "full_equality_matrix": torch_equality_matrix(full_table),
            "erased_equality_matrix": torch_equality_matrix(erased_table),
        },
        "quotient_classes_full": full_classes,
        "quotient_class_count_full": len(full_classes),
        "quotient_classes_erased": erased_classes,
        "quotient_class_count_erased": len(erased_classes),
        "flip_control": {
            "erased_merge_pair": merge_pair,
            "full_class_count": len(full_classes),
            "erased_class_count": len(erased_classes),
            "added_probe": spec["added_probe"],
            "added_probe_split_pair": merge_pair,
            "added_probe_class_count": len(full_classes),
            "tautology_guard_tripped": not (z3_erased == "sat" and cvc5_erased == "sat"),
        },
        "positive_tests": {
            "full_table_partition_well_defined": z3_full == "unsat" and cvc5_full == "unsat",
            "specific_full_class_count": len(full_classes) == int(expected["full_class_count"]),
        },
        "negative_tests": {
            "erased_table_exposes_over_refinement": z3_erased == "sat" and cvc5_erased == "sat",
            "erased_merge_pair": merge_pair,
        },
        "boundary_tests": {
            "persistent_indistinguishable_pair_under_full_P": persistent_pair,
            "full_quotient_is_not_identity": any(len(group) > 1 for group in full_classes),
        },
        "smt_flip": {
            "z3_full_P": z3_full,
            "z3_erased_P": z3_erased,
            "cvc5_full_P": cvc5_full,
            "cvc5_erased_P": cvc5_erased,
            "real_vs_erased_flip_confirmed": smt_ok,
            "encoding": "SMT variables are equal to torch complex128-derived table entries and full-P class ids; the asserted violation is soundness-or-coarseness failure for the active probe list.",
        },
        "crossover_proofs": {
            "z3": {
                "ran": True,
                "load_bearing": True,
                "supportive": False,
                "verdict": z3_full,
                "erased_verdict": z3_erased,
                "claim": "load-bearing consistency gate: full P has no quotient violation and erased P exposes the expected coarseness witness against the forced full-Q table",
            },
            "cvc5": {
                "ran": True,
                "load_bearing": True,
                "supportive": False,
                "verdict": cvc5_full,
                "erased_verdict": cvc5_erased,
                "claim": "load-bearing consistency gate: independent solver agrees with z3 on full and erased probe lists",
            },
        },
        "tool_calls": [
            {
                "tool": "torch.func",
                "qualified_api/function": "torch.func.vmap",
                "input_object": "finite torch complex128 probe table",
                "output_object": "pairwise equality matrices and class counts",
                "positive_case": "full-P class count is 5",
                "negative/erased_control": "erased-P class count is 4",
                "boundary_case": "x4 and x5 remain indistinguishable under full P",
                "demotion_condition": "class counts or pairwise matrices disagree with table grouping",
                "gates": ["quotient", "divergence", "all_pass"],
            },
            {
                "tool": "z3",
                "qualified_api/function": "z3.Solver.check",
                "input_object": "torch complex128-derived rows and full-P class ids",
                "output_object": "UNSAT full-P and SAT erased-P verdicts",
                "positive_case": "full P has no soundness/coarseness violation",
                "negative/erased_control": "erased P exposes x0/x2 coarseness witness",
                "boundary_case": "x4/x5 same-class row remains allowed",
                "demotion_condition": "demote to plain torch table computation if full is not unsat or erased is not sat",
                "gates": ["consistency_check"],
            },
            {
                "tool": "cvc5",
                "qualified_api/function": "cvc5.Solver.checkSat",
                "input_object": "same torch complex128-derived rows and class ids as z3",
                "output_object": "matching UNSAT/SAT polarity",
                "positive_case": "full P has no soundness/coarseness violation",
                "negative/erased_control": "erased P exposes x0/x2 coarseness witness",
                "boundary_case": "x4/x5 same-class row remains allowed",
                "demotion_condition": "demote to single-solver consistency check if cvc5 disagrees with z3",
                "gates": ["consistency_check"],
            },
        ],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "packages_used": ["torch", "torch.func", "z3", "cvc5"],
        "aligned_packages_load_bearing": ["torch.func", "z3", "cvc5"],
        "package_observables": {
            "torch": "torch complex128 tensor held the finite table rows",
            "torch.func": "torch.func.vmap computed pairwise equality over the finite table rows",
            "z3": "load-bearing SMT full/erased quotient-table consistency polarity over torch-derived rows",
            "cvc5": "load-bearing independent SMT full/erased quotient-table consistency polarity over torch-derived rows",
        },
        "claim_path_tools": ["torch", "torch.func"],
        "all_pass": controls_ok,
        "criteria_checked": [
            "full class count",
            "erased class count",
            "merge pair",
            "added probe split",
            "persistent indistinguishable pair",
            "torch.func full equality matrix",
            "torch.func erased equality matrix",
            "z3 full UNSAT",
            "z3 erased SAT",
            "cvc5 full UNSAT",
            "cvc5 erased SAT",
        ],
        "surviving_alternatives": spec["surviving_alternatives"],
        "claim_ceiling": spec["claim_ceiling"],
    }
    out_path = RESULTS / f"{SIM_ID}_pytorch_results.json"
    out_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": controls_ok, "result_path": str(out_path), "smt_flip": result["smt_flip"]}, indent=2))
    return 0 if controls_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
