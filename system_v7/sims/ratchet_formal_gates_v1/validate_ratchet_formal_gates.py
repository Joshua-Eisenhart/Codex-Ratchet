#!/usr/bin/env python3
"""Validate ratchet_formal_gates_v1 and write human-readable receipts."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SIM_ID = "ratchet_formal_gates_v1"
HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
TOL = 1e-9

classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False
TOOL_MANIFEST = {
    "json": {"tried": True, "used": True, "reason": "load-bearing result read and validator result serialization"},
    "markdown": {"tried": True, "used": True, "reason": "supportive FORMAL_SPEC.md and RESULTS.md emission"},
}
TOOL_INTEGRATION_DEPTH = {"json": "load_bearing", "markdown": "supportive"}


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load(name: str) -> dict[str, Any]:
    return json.loads((RESULTS / name).read_text(encoding="utf-8"))


def by_label(result: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {row["label"]: row for row in result["carrier_states"]}


def compare_numeric(py: dict[str, Any], jl: dict[str, Any]) -> dict[str, Any]:
    failures = []
    py_states = by_label(py)
    jl_states = by_label(jl)
    if set(py_states) != set(jl_states):
        failures.append({"field": "carrier_labels", "python_only": sorted(set(py_states) - set(jl_states)), "julia_only": sorted(set(jl_states) - set(py_states))})
    max_pvec_diff = 0.0
    max_trace_diff = 0.0
    for label in sorted(set(py_states) & set(jl_states)):
        pyp = py_states[label]["pvec"]
        jlp = jl_states[label]["pvec"]
        if len(pyp) != len(jlp):
            failures.append({"label": label, "field": "pvec_length", "python": len(pyp), "julia": len(jlp)})
            continue
        diffs = [abs(float(a) - float(b)) for a, b in zip(pyp, jlp)]
        max_pvec_diff = max(max_pvec_diff, max(diffs, default=0.0))
        if max(diffs, default=0.0) > TOL:
            failures.append({"label": label, "field": "pvec", "max_diff": max(diffs)})
        trace_diff = abs(float(py_states[label]["trace"]) - float(jl_states[label]["trace"]))
        max_trace_diff = max(max_trace_diff, trace_diff)
        if trace_diff > TOL:
            failures.append({"label": label, "field": "trace", "diff": trace_diff})
    labels = sorted(set(py_states) & set(jl_states))
    for i, left in enumerate(labels):
        for right in labels[i + 1 :]:
            py_same = int(py_states[left]["quotient_class"]) == int(py_states[right]["quotient_class"])
            jl_same = int(jl_states[left]["quotient_class"]) == int(jl_states[right]["quotient_class"])
            if py_same != jl_same:
                failures.append({"field": "quotient_equivalence_relation", "left": left, "right": right, "python_same": py_same, "julia_same": jl_same})
                break
        if failures and failures[-1].get("field") == "quotient_equivalence_relation":
            break
    pyq = py["gates"]["observable_quotient_R4"]
    jlq = jl["gates"]["observable_quotient_R4"]
    for key in ("carrier_count", "probe_count", "quotient_class_count", "class_sizes", "pair_check_count", "surviving_difference_count", "collapsed_pair_count"):
        if pyq[key] != jlq[key]:
            failures.append({"field": f"observable_quotient_R4.{key}", "python": pyq[key], "julia": jlq[key]})
    pyx = py["gates"]["xi_ref_quotient_lift"]
    jlx = jl["gates"]["xi_ref_quotient_lift"]
    for key in ("checked_class_pairs", "multi_representative_class_count", "failure_count", "status"):
        if pyx[key] != jlx[key]:
            failures.append({"field": f"xi_ref_quotient_lift.{key}", "python": pyx[key], "julia": jlx[key]})
    xi_spread_diff = abs(float(pyx["max_descriptor_spread"]) - float(jlx["max_descriptor_spread"]))
    if xi_spread_diff > TOL:
        failures.append({"field": "xi_ref_quotient_lift.max_descriptor_spread", "diff": xi_spread_diff})
    return {
        "parity_abs_tol": TOL,
        "parity_pass": not failures,
        "failure_count": len(failures),
        "failures": failures[:50],
        "max_pvec_abs_diff": max_pvec_diff,
        "max_trace_abs_diff": max_trace_diff,
        "xi_ref_max_descriptor_spread_diff": xi_spread_diff,
    }


def gate_verdicts(py: dict[str, Any], jl: dict[str, Any], parity: dict[str, Any]) -> dict[str, Any]:
    gates = py["gates"]
    out = {
        "token_identity_R5": {
            "pass": bool(gates["token_identity_R5"]["gate_pass"]),
            "basis": "z3+cvc5 both polarities: bad same-identity reentry UNSAT; erased bad reentry SAT; logged replay SAT-as-new-branch",
        },
        "progress_measure_R6": {
            "pass": bool(gates["progress_measure_R6"]["gate_pass"]),
            "basis": "z3+cvc5 effective-step strict lexicographic decrease plus objective non-step predicate",
        },
        "observable_quotient_R4": {
            "pass": bool(gates["observable_quotient_R4"]["gate_pass"] and jl["gates"]["observable_quotient_R4"]["gate_pass"] and parity["parity_pass"]),
            "basis": "full C^8 carrier enumeration with all 63 non-identity Pauli probes; numpy/Julia parity at 1e-9",
        },
        "xi_ref_quotient_lift": {
            "pass": bool(gates["xi_ref_quotient_lift"]["gate_pass"] and jl["gates"]["xi_ref_quotient_lift"]["gate_pass"] and parity["parity_pass"]),
            "basis": "representative-independence checked over every quotient-class pair in numpy and Julia",
            "status": gates["xi_ref_quotient_lift"]["status"],
        },
    }
    return out


def write_results_md(py: dict[str, Any], jl: dict[str, Any], parity: dict[str, Any], verdicts: dict[str, Any]) -> None:
    q = py["gates"]["observable_quotient_R4"]
    xi = py["gates"]["xi_ref_quotient_lift"]
    lines = [
        "# ratchet_formal_gates_v1 RESULTS",
        "",
        "classification: `scratch_diagnostic`",
        "claim_ceiling: `formal_gate_diagnostic_only`",
        "promotion_allowed: `false`",
        "formal_admission_allowed: `false`",
        "",
        "## Carrier",
        "",
        "- Hilbert carrier: `C^8`.",
        f"- Executable finite carrier states: `{q['carrier_count']}`.",
        f"- Probe family: `{q['probe_count']}` non-identity 3-qubit Pauli strings.",
        "- Enumeration: full deterministic carrier/probe enumeration; no sampling.",
        "",
        "## Gate Verdicts",
        "",
        "| gate | verdict | basis |",
        "|---|---|---|",
    ]
    for gate, row in verdicts.items():
        lines.append(f"| `{gate}` | `{'PASS' if row['pass'] else 'FAIL'}` | {row['basis']} |")
    lines.extend(
        [
            "",
            "## Numeric Parity",
            "",
            f"- numpy/Julia parity at 1e-9: `{parity['parity_pass']}`.",
            f"- max Pauli-vector abs diff: `{parity['max_pvec_abs_diff']}`.",
            f"- max trace abs diff: `{parity['max_trace_abs_diff']}`.",
            f"- Xi_ref descriptor spread diff: `{parity['xi_ref_max_descriptor_spread_diff']}`.",
            f"- parity failures: `{parity['failures']}`.",
            "",
            "## Quotient And Xi_ref",
            "",
            f"- quotient classes: `{q['quotient_class_count']}`.",
            f"- class sizes: `{q['class_sizes']}`.",
            f"- collapsed pairs: `{q['collapsed_pair_count']}`.",
            f"- surviving differences: `{q['surviving_difference_count']}`.",
            f"- Xi_ref status: `{xi['status']}`.",
            f"- Xi_ref checked class pairs: `{xi['checked_class_pairs']}`.",
            f"- Xi_ref multi-representative classes: `{xi['multi_representative_class_count']}`.",
            f"- Xi_ref failures: `{xi['failure_count']}`.",
            "",
            "## Runtime Caveat",
            "",
            py.get("runtime_caveat", {}).get("doctor_summary", "not recorded"),
            "",
            "Generated: " + now_iso(),
            "",
        ]
    )
    (RESULTS / "RESULTS.md").write_text("\n".join(lines), encoding="utf-8")


def write_formal_spec(py: dict[str, Any], parity: dict[str, Any], verdicts: dict[str, Any]) -> None:
    token = py["gates"]["token_identity_R5"]
    progress = py["gates"]["progress_measure_R6"]
    quotient = py["gates"]["observable_quotient_R4"]
    xi = py["gates"]["xi_ref_quotient_lift"]
    lines = [
        "# FORMAL_SPEC: ratchet_formal_gates_v1",
        "",
        "Status: `scratch_diagnostic`; `promotion_allowed=false`; `formal_admission_allowed=false`.",
        "",
        "This file is generated from the executable gate artifacts in `results/`. It closes the referee-specified formalization gaps as a Gate-1 diagnostic layer only; it does not advance the Axis-0 bridge, `Phi_0`, or the unified emergence pipeline.",
        "",
        "## Source Anchors",
        "",
        "- `system_v7/sims/DUAL_RATCHET_FORMALIZATION_XI_EXTRACTION_20260703.md`: R1-R6 extraction, theorem obligations, Xi candidate status, and open gaps.",
        "- `/Users/joshuaeisenhart/wiki/concepts/axes-full-layout-relations-anti-conflation-2026-07-03.md` section 7: referee obligations for R5, R6, observable quotient, and Xi_ref quotient-lift.",
        "- `system_v7/constraint_core/reference_docs_from_josh/physics_program/ratchet_definition_and_emergence_spec_DRAFT_20260614.md`: canonical ratchet definition draft and scratch-only ceiling.",
        "- `system_v7/constraint_core/engines/oracle_targets_3q.py`: real C^8 carrier and full 63-Pauli probe convention used by the executable numeric gates.",
        "",
        "## 1. Token Identity (R5)",
        "",
        "Formal definition: a token identity tuple is `(content, lineage_id, branch_id, replay_receipt_id)`. Two token occurrences are the same entity iff content is identical, probe observations are indistinguishable, lineage is connected, and there is no logged replay receipt separating the occurrences. A replay receipt opens a fresh branch identity even when content and probes match.",
        "",
        "Executable SMT gate:",
        f"- bad re-entry without fresh identity tuple: z3 `{token['without_fresh_identity_tuple']['z3_with_axioms']}`, cvc5 `{token['without_fresh_identity_tuple']['cvc5_with_axioms']}`.",
        f"- erased-control bad re-entry: z3 `{token['without_fresh_identity_tuple']['z3_erased_axioms']}`, cvc5 `{token['without_fresh_identity_tuple']['cvc5_erased_axioms']}`.",
        f"- logged replay as new branch: z3 `{token['with_logged_replay_receipt']['z3_with_axioms']}`, cvc5 `{token['with_logged_replay_receipt']['cvc5_with_axioms']}`.",
        f"- Gate verdict: `{'PASS' if verdicts['token_identity_R5']['pass'] else 'FAIL'}`.",
        "",
        "## 2. Progress Measure mu (R6)",
        "",
        "Formal definition: `mu : State -> N^3` with strict lexicographic order. The source spec demands a progress measure but does not fix codomain/order; this is the one explicit OPEN-CHOICE. Alternatives retained in `spec.json` are a single finite-state rank in `N`, an `N^2` survivor/receipt rank, or an ordinal notation below `omega^k`.",
        "",
        "Objective non-step predicate: a step is a non-step iff it changes none of `X_k`, `H_k`, or the observable quotient projection. This predicate is observer-independent because it is computed from equality of three finite registers, not from a narrative judgment.",
        "",
        "Executable SMT gate:",
        f"- effective step with non-decreasing mu: z3 `{progress['strict_decrease']['z3_with_axioms']}`, cvc5 `{progress['strict_decrease']['cvc5_with_axioms']}`.",
        f"- erased-control effective step: z3 `{progress['strict_decrease']['z3_erased_axioms']}`, cvc5 `{progress['strict_decrease']['cvc5_erased_axioms']}`.",
        f"- objective non-step definition violation: z3 `{progress['non_step_objectivity']['z3_definition_violation']}`, cvc5 `{progress['non_step_objectivity']['cvc5_definition_violation']}`.",
        f"- Termination argument: {progress['termination_argument']}",
        f"- Gate verdict: `{'PASS' if verdicts['progress_measure_R6']['pass'] else 'FAIL'}`.",
        "",
        "## 3. Observable Quotient (R4)",
        "",
        "Formal definition: the carrier is the finite executable set of real 3-qubit engine states generated from `oracle_targets_3q.py`. The probe family `M` is all 63 non-identity 3-qubit Pauli strings. `rho_a ~ rho_b` iff every probe expectation in `M` agrees. The projection map sends each carrier state to its equivalence-class id. A difference survives the observable quotient iff the two states project to distinct classes.",
        "",
        "Non-circularity: the quotient is defined before R4 consumes it and depends only on carrier states plus probes; it does not depend on update maps, admissibility predicates, or Xi candidates.",
        "",
        "Executable numeric gate:",
        f"- carrier states: `{quotient['carrier_count']}`.",
        f"- probes: `{quotient['probe_count']}`.",
        f"- quotient classes: `{quotient['quotient_class_count']}`.",
        f"- class sizes: `{quotient['class_sizes']}`.",
        f"- numpy/Julia parity at 1e-9: `{parity['parity_pass']}` with max pvec diff `{parity['max_pvec_abs_diff']}`.",
        f"- Gate verdict: `{'PASS' if verdicts['observable_quotient_R4']['pass'] else 'FAIL'}`.",
        "",
        "## 4. Xi_ref Quotient-Lift",
        "",
        "Formal definition: `x_ref` is selected as a quotient class `c_ref`, not as a raw representative. `Xi_ref(c_ref, c)` is well-defined only if the raw point-reference descriptor `Xi_ref(x_ref, x)` is independent of the representative choices `x_ref in c_ref` and `x in c`.",
        "",
        "Executable descriptor: the reference representative selects a cut qubit by maximal local Pauli strength; the target descriptor records coherent information `S(B)-S(AB)` for that cut plus local XYZ expectations. This is a discriminator/lift test, not a final Axis-0 bridge doctrine.",
        "",
        "Executable lift gate:",
        f"- status: `{xi['status']}`.",
        f"- checked quotient-class pairs: `{xi['checked_class_pairs']}`.",
        f"- multi-representative classes: `{xi['multi_representative_class_count']}`.",
        f"- max descriptor spread: `{xi['max_descriptor_spread']}`.",
        f"- failure count: `{xi['failure_count']}`.",
        f"- Gate verdict: `{'PASS' if verdicts['xi_ref_quotient_lift']['pass'] else 'FAIL'}`.",
        "",
        "## Overall Gate Result",
        "",
        f"- all gates pass: `{all(row['pass'] for row in verdicts.values())}`.",
        "- accepted ceiling: `passes local rerun` if the Python, Julia, validator, and lint commands in the closeout all exit 0; never above `scratch_diagnostic` / `formal_gate_diagnostic_only` without later admission gates.",
        "- blocked consumers: Axis-0 bridge closure, `Phi_0` evaluation, unified emergence admission, and further pipeline advancement.",
        "",
        "Generated: " + now_iso(),
        "",
    ]
    (HERE / "FORMAL_SPEC.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    py = load(f"{SIM_ID}_numpy_results.json")
    jl = load(f"{SIM_ID}_julia_results.json")
    parity = compare_numeric(py, jl)
    verdicts = gate_verdicts(py, jl, parity)
    validator = {
        "schema": "codex_ratchet.ratchet_formal_gates_v1.validator.v1",
        "generated_at": now_iso(),
        "sim_id": SIM_ID,
        "classification": classification,
        "claim_ceiling": "formal_gate_diagnostic_only",
        "promotion_allowed": promotion_allowed,
        "formal_admission_allowed": formal_admission_allowed,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "parity": parity,
        "gate_verdicts": verdicts,
        "all_pass": all(row["pass"] for row in verdicts.values()),
    }
    (RESULTS / f"{SIM_ID}_validator_results.json").write_text(json.dumps(validator, indent=2, sort_keys=True), encoding="utf-8")
    write_results_md(py, jl, parity, verdicts)
    write_formal_spec(py, parity, verdicts)
    print(json.dumps({"validator_path": str(RESULTS / f"{SIM_ID}_validator_results.json"), "formal_spec": str(HERE / "FORMAL_SPEC.md"), "all_pass": validator["all_pass"], "gate_verdicts": {k: v["pass"] for k, v in verdicts.items()}}, indent=2))


if __name__ == "__main__":
    main()
