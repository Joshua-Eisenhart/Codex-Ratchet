#!/usr/bin/env python3
"""
run_contract_selfcheck.py -- instantiate the toys, run every gate on each,
run pairwise_mss/frontier on toy pairs, write
ratchet_contract/results/selfcheck.json = the discrimination matrix
(gate x toy -> verdict) + pairwise_mss results (base-only and
demand-thickened) + a mechanical, grep-based confirmation that no LLM or
network call exists anywhere in this contract.

2026-07-20 update, post fresh-context audit (results/AUDIT_VERDICT.md,
overall CLEAN, two low-severity findings):
  F1 -- ControlSet.negative / expected_distinguishable=False were declared
        and populated by the toys but had zero consumers (gates.py's
        probe_validity_gate only ever read .positive). Fixed in gates.py:
        probe_validity_gate now also checks negative controls and FAILs if
        D falsely separates one. This file adds the D=("noop",) "leaky D"
        demonstration that makes that branch actually fire in the receipt.
  F2 -- the roster toys only ever drove evolvability_gate's evolve()->None
        FAIL branch (toy_frozen); the D-collapse branch and the
        primitive-smuggle branch were verified only by the auditor's own
        constructed inputs, never inside this receipt. This file adds two
        more non-roster fixtures, one per branch, so both fire here too.

Exit codes (matches fuel_gate/fuel_adequacy_gate.py's discipline -- the
interface is the exit code, not printed prose):
    0 = every gate demonstrated >=2 distinct verdicts across the toy set
        (non-vacuous), the no-LLM/network scan is clean, the headline
        pairwise_mss demo is a genuine strict coarsening, AND both audit
        fixes are confirmed firing (not just present in code).
    1 = one of those checks failed -- printed JSON names which.
"""

from __future__ import annotations

import itertools
import json
import sys
from pathlib import Path

from contract import Carrier, CandidatePackage, ControlCase, ControlSet, NestInterface
from gates import (
    buildability_gate,
    probe_validity_gate,
    IDENTITY_GATE,
    persistence_gate,
    evolvability_gate,
    extension_gate,
    adequacy,
)
from mss import pairwise_mss, frontier
from toy_candidates import all_toys, X_BASE, D_BASE

RATCHET_CONTRACT_DIR = Path(__file__).resolve().parent
RESULTS_PATH = RATCHET_CONTRACT_DIR / "results" / "selfcheck.json"


# ---------------------------------------------------------------------------
# A single non-roster fixture used ONLY to prove buildability_gate can FAIL.
# The 4 roster toys (toy_candidates.py) are all well-formed candidates --
# each isolates a DIFFERENT gate's failure by design, not buildability's.
# A gate that never fails on anything is vacuous, so this fixture exists
# purely to exercise that branch honestly rather than leaving it unproven.
# ---------------------------------------------------------------------------
class _BrokenBuildabilityFixture(CandidatePackage):
    @property
    def name(self) -> str:
        return "_broken_buildability_fixture(non_roster_vacuity_check_only)"

    @property
    def carrier(self):
        return Carrier(description="deliberately broken -- apply() always raises", allowed_ops=("noop",))

    def states(self):
        return (0, 1)

    def probes(self):
        return ("probe",)

    def apply(self, op, state):
        raise RuntimeError("this candidate cannot run its own probes -- buildability_gate must FAIL it")

    def reidentify(self, record, current_state):
        return record == current_state

    def persist(self, state, *, perturbation=None, delay=0, partial_access=None, relabeled=False):
        return state

    def evolve(self, new_constraint):
        return None

    def nest_interface(self):
        return NestInterface()

    def declared_primitives(self):
        return ()

    def controls(self):
        return ControlSet()


# ---------------------------------------------------------------------------
# Two more non-roster fixtures, added for audit finding F2. The roster toys
# only exercise evolvability_gate's evolve()->None branch (toy_frozen). The
# other two FAIL branches inside evolvability_gate -- the extension
# collapsing a demanded distinction, and the extension smuggling in a new
# declared primitive -- were previously verified only by the auditor's own
# constructed inputs, never inside this receipt. Each fixture here isolates
# exactly one of those two branches, the same single-axis-isolation
# discipline the roster toys already follow.
# ---------------------------------------------------------------------------
class _EvolveCollapsesDistinctionFixture(CandidatePackage):
    """Identity-honest (reidentify matches the read_value probe partition,
    same as toy_quotient_respecting), but evolve() returns an extension
    whose reidentify has been degraded to treat every pair as the same
    entity -- collapsing the base demand set's one required distinction.
    Fires evolvability_gate's 'the evolved extension destroys a
    previously-live demanded distinction' branch."""

    def __init__(self, states=X_BASE, collapse: bool = False):
        self._states = tuple(states)
        self._collapse = collapse

    @property
    def name(self) -> str:
        return "_evolve_collapses_distinction_fixture(non_roster_F2_demo)"

    @property
    def carrier(self):
        return Carrier(description="value-honest identity; evolve() returns a degraded, "
                                     "over-merging extension", allowed_ops=("noop",))

    def states(self):
        return self._states

    def probes(self):
        return ("read_value",)

    def apply(self, op, state):
        raw_id, value = state
        if op == "read_value":
            return value
        if op == "noop":
            return state
        raise ValueError(f"unknown op {op!r}")

    def reidentify(self, record, current_state):
        if self._collapse:
            return True  # degraded: every pair reads as "the same" post-evolution
        return record[1] == current_state[1]

    def persist(self, state, *, perturbation=None, delay=0, partial_access=None, relabeled=False):
        return (state[0], state[1])

    def evolve(self, new_constraint):
        return _EvolveCollapsesDistinctionFixture(self._states, collapse=True)

    def nest_interface(self):
        return NestInterface()

    def declared_primitives(self):
        return ()

    def controls(self):
        pos = (ControlCase("red_vs_blue", (0, "red"), (1, "blue"), True),)
        return ControlSet(positive=pos, negative=())


class _EvolveSmugglesPrimitiveFixture(CandidatePackage):
    """Identity-honest, and its evolve() extension does NOT collapse any
    demanded distinction -- but the extension declares a NEW primitive
    ('time') absent from the original's declared_primitives(). Fires
    evolvability_gate's 'evolve() smuggled in a new declared primitive'
    branch, isolated from the D-collapse branch above."""

    def __init__(self, states=X_BASE, smuggled=()):
        self._states = tuple(states)
        self._smuggled = tuple(smuggled)

    @property
    def name(self) -> str:
        return "_evolve_smuggles_primitive_fixture(non_roster_F2_demo)"

    @property
    def carrier(self):
        return Carrier(description="value-honest identity; evolve() returns a clean "
                                     "extension that adds an undeclared-before primitive",
                        allowed_ops=("noop",))

    def states(self):
        return self._states

    def probes(self):
        return ("read_value",)

    def apply(self, op, state):
        raw_id, value = state
        if op == "read_value":
            return value
        if op == "noop":
            return state
        raise ValueError(f"unknown op {op!r}")

    def reidentify(self, record, current_state):
        return record[1] == current_state[1]

    def persist(self, state, *, perturbation=None, delay=0, partial_access=None, relabeled=False):
        return (state[0], state[1])

    def evolve(self, new_constraint):
        return _EvolveSmugglesPrimitiveFixture(self._states, smuggled=("time",))

    def nest_interface(self):
        return NestInterface()

    def declared_primitives(self):
        return self._smuggled

    def controls(self):
        pos = (ControlCase("red_vs_blue", (0, "red"), (1, "blue"), True),)
        return ControlSet(positive=pos, negative=())


def _build_matrix(toys):
    matrix = {}
    for c in toys:
        matrix[c.name] = {
            "buildability_gate": buildability_gate(c).to_json(),
            "probe_validity_gate__own_D": probe_validity_gate(c).to_json(),
            "probe_validity_gate__thin_D": probe_validity_gate(c, D=("constant_probe",)).to_json(),
            # "noop" echoes the FULL (raw_id, value) state -- for toys that
            # declare a same-value/different-raw_id negative control (an
            # aliasing pair that must NOT be told apart), this D falsely
            # separates it. F1's fix, exercised here (not a new fixture --
            # every toy already has "noop" in its apply() dispatch).
            "probe_validity_gate__leaky_D": probe_validity_gate(c, D=("noop",)).to_json(),
            "IDENTITY_GATE": IDENTITY_GATE(c).to_json(),
            "persistence_gate__base_D": persistence_gate(c, X_BASE, D_BASE).to_json(),
            "evolvability_gate__base_D": evolvability_gate(c, X_BASE, D_BASE).to_json(),
            "extension_gate__base_D": extension_gate(c, X_BASE, D_BASE).to_json(),
            "adequacy": adequacy(c, X_BASE, D_BASE).to_json(),
        }
    return matrix


def _build_vacuity_report(matrix, toy_names, broken_name, broken_buildability_verdict):
    vacuity = {}

    bb_verdicts = {n: matrix[n]["buildability_gate"]["verdict"] for n in toy_names}
    bb_verdicts[broken_name] = broken_buildability_verdict
    vacuity["buildability_gate"] = {
        "verdicts": bb_verdicts,
        "distinct_verdicts": sorted(set(bb_verdicts.values())),
        "pass": len(set(bb_verdicts.values())) >= 2,
        "note": ("the 4 roster toys are all well-formed and PASS; FAIL is demonstrated via a "
                 "separate non-roster broken fixture (apply() always raises), never by breaking a "
                 "toy that another gate depends on for a clean single-axis failure"),
    }

    pv_own = {n: matrix[n]["probe_validity_gate__own_D"]["verdict"] for n in toy_names}
    pv_thin = {n: matrix[n]["probe_validity_gate__thin_D"]["verdict"] for n in toy_names}
    pv_leaky = {n: matrix[n]["probe_validity_gate__leaky_D"]["verdict"] for n in toy_names}
    vacuity["probe_validity_gate"] = {
        "own_D_verdicts": pv_own,
        "thin_D_verdicts": pv_thin,
        "leaky_D_verdicts": pv_leaky,
        "distinct_verdicts": sorted(set(list(pv_own.values()) + list(pv_thin.values()) + list(pv_leaky.values()))),
        "pass": len(set(list(pv_own.values()) + list(pv_thin.values()) + list(pv_leaky.values()))) >= 2,
        "note": ("own_D (the toy's own adequate probes) demonstrates PASS; thin_D=('constant_probe',) "
                 "demonstrates HOLD -- 'probe family has not demonstrated discrimination power'; "
                 "leaky_D=('noop',) demonstrates FAIL for toys with a declared negative control -- "
                 "'noop' echoes the full (raw_id,value) state, so it separates a same-value/"
                 "different-raw_id alias pair the candidate declares must not be separated "
                 "(audit finding F1's fix)"),
    }

    for gate_key, matrix_key in (
        ("IDENTITY_GATE", "IDENTITY_GATE"),
        ("persistence_gate", "persistence_gate__base_D"),
        ("evolvability_gate", "evolvability_gate__base_D"),
        ("extension_gate", "extension_gate__base_D"),
        ("adequacy", "adequacy"),
    ):
        verdicts = {n: matrix[n][matrix_key]["verdict"] for n in toy_names}
        vacuity[gate_key] = {
            "verdicts": verdicts,
            "distinct_verdicts": sorted(set(verdicts.values())),
            "pass": len(set(verdicts.values())) >= 2,
        }

    return vacuity


def _confirm_no_llm_or_network_calls():
    """Mechanical (grep-based), not asserted in prose: scans the contract's
    own source files for tokens that would indicate a model/network call."""
    suspicious_tokens = [
        "openai", "anthropic", "requests.", "urllib", "http.client", "socket.",
        "subprocess", "os.system", "eval(", "exec(",
    ]
    scanned = ["contract.py", "gates.py", "mss.py", "toy_candidates.py"]
    hits = {}
    for fname in scanned:
        text = (RATCHET_CONTRACT_DIR / fname).read_text(encoding="utf-8")
        found = [tok for tok in suspicious_tokens if tok in text]
        if found:
            hits[fname] = found
    return {
        "scanned_files": scanned,
        "suspicious_tokens_checked": suspicious_tokens,
        "hits": hits,
        "clean": len(hits) == 0,
    }


def main() -> int:
    toys = list(all_toys())
    toy_names = [c.name for c in toys]
    by_name = {c.name: c for c in toys}

    matrix = _build_matrix(toys)

    broken = _BrokenBuildabilityFixture()
    broken_result = buildability_gate(broken).to_json()

    evolve_collapse_fixture = _EvolveCollapsesDistinctionFixture()
    evolve_collapse_identity = IDENTITY_GATE(evolve_collapse_fixture, X_BASE).to_json()
    evolve_collapse_result = evolvability_gate(evolve_collapse_fixture, X_BASE, D_BASE).to_json()

    evolve_smuggle_fixture = _EvolveSmugglesPrimitiveFixture()
    evolve_smuggle_identity = IDENTITY_GATE(evolve_smuggle_fixture, X_BASE).to_json()
    evolve_smuggle_result = evolvability_gate(evolve_smuggle_fixture, X_BASE, D_BASE).to_json()

    vacuity = _build_vacuity_report(matrix, toy_names, broken.name, broken_result["verdict"])

    # -- pairwise_mss across every toy pair, base-only and demand-thickened --
    pairwise_base = {}
    pairwise_thick = {}
    for A, B in itertools.combinations(toys, 2):
        key = f"{A.name}__vs__{B.name}"
        pairwise_base[key] = pairwise_mss(A, B, X_BASE, D_BASE).to_json()
        pairwise_thick[key] = pairwise_mss(
            A, B, X_BASE, D_BASE,
            thicken_persistence=True, thicken_evolvability=True, thicken_wholenest=True,
        ).to_json()

    # -- frontier: base-only (shows dominance + branch re-merge) and fully
    #    demand-thickened (shows purgatory pruning the frontier to the one
    #    candidate that survives everything) --
    frontier_base = frontier(toys, X_BASE, D_BASE)
    frontier_thick = frontier(
        toys, X_BASE, D_BASE,
        thicken_persistence=True, thicken_evolvability=True, thicken_wholenest=True,
    )

    headline_pair = pairwise_mss(by_name["toy_frozen"], by_name["toy_quotient_respecting"], X_BASE, D_BASE).to_json()

    no_llm = _confirm_no_llm_or_network_calls()

    # -- one place a reader can find every FAIL/HOLD branch demonstrated in
    #    THIS receipt, not scattered across side keys or left to an
    #    auditor's own constructed inputs (audit findings F1 + F2) --
    fail_branch_demonstrations = {
        "buildability_gate.FAIL": {
            "candidate": broken.name,
            "result": broken_result,
            "note": "non-roster fixture -- the 4 roster toys are all well-formed by design",
        },
        "probe_validity_gate.HOLD_thin_D": {
            "candidate": "toy_raw_label", "D": ["constant_probe"],
            "result": matrix["toy_raw_label"]["probe_validity_gate__thin_D"],
        },
        "probe_validity_gate.FAIL_negative_control_leak": {
            "candidate": "toy_quotient_respecting", "D": ["noop"],
            "result": matrix["toy_quotient_respecting"]["probe_validity_gate__leaky_D"],
            "note": "audit finding F1 fix -- previously dead scaffolding (zero consumers of "
                    "ControlSet.negative), now a real, firing FAIL branch in probe_validity_gate",
        },
        "IDENTITY_GATE.FAIL_unearned_identity": {
            "candidate": "toy_raw_label", "result": matrix["toy_raw_label"]["IDENTITY_GATE"],
        },
        "IDENTITY_GATE.FAIL_internal_reidentify_contradiction": {
            "candidate": "toy_intransitive_reidentify",
            "result": matrix["toy_intransitive_reidentify"]["IDENTITY_GATE"],
            "note": "old partition-equality-only check would PASS; widened direct in-block check FAILs",
        },
        "persistence_gate.FAIL_collapse_under_continuation": {
            "candidate": "toy_amnesiac", "result": matrix["toy_amnesiac"]["persistence_gate__base_D"],
        },
        "evolvability_gate.FAIL_no_admissible_extension": {
            "candidate": "toy_frozen", "result": matrix["toy_frozen"]["evolvability_gate__base_D"],
        },
        "evolvability_gate.FAIL_extension_collapses_distinction": {
            "candidate": evolve_collapse_fixture.name,
            "identity_gate_of_base_candidate": evolve_collapse_identity,
            "result": evolve_collapse_result,
            "note": "audit finding F2 fix -- distinct code path from the evolve()->None branch above; "
                    "the base fixture itself PASSES IDENTITY_GATE, isolating this to evolvability alone",
        },
        "evolvability_gate.FAIL_extension_smuggles_primitive": {
            "candidate": evolve_smuggle_fixture.name,
            "identity_gate_of_base_candidate": evolve_smuggle_identity,
            "result": evolve_smuggle_result,
            "note": "audit finding F2 fix -- distinct code path from both evolvability branches above",
        },
        "extension_gate.FAIL_stale_nest_digest": {
            "candidate": "toy_frozen", "result": matrix["toy_frozen"]["extension_gate__base_D"],
        },
    }

    all_gates_non_vacuous = all(v["pass"] for v in vacuity.values())
    headline_is_strict_coarsening = headline_pair["verdict"] in ("A_WEAKER", "B_WEAKER")

    f1_fires = matrix["toy_quotient_respecting"]["probe_validity_gate__leaky_D"]["verdict"] == "FAIL"
    f2_collapse_fires = (
        evolve_collapse_result["verdict"] == "FAIL"
        and "destroys a previously-live" in evolve_collapse_result["reasons"].get("reason", "")
    )
    f2_smuggle_fires = (
        evolve_smuggle_result["verdict"] == "FAIL"
        and "smuggled" in evolve_smuggle_result["reasons"].get("reason", "")
    )
    intransitive_identity_fires = (
        matrix["toy_intransitive_reidentify"]["IDENTITY_GATE"]["verdict"] == "FAIL"
        and bool(matrix["toy_intransitive_reidentify"]["IDENTITY_GATE"]["reasons"].get(
            "reidentify_internal_contradictions"
        ))
    )
    f2_fixtures_identity_honest = (
        evolve_collapse_identity["verdict"] == "PASS" and evolve_smuggle_identity["verdict"] == "PASS"
    )
    audit_fixes_confirmed = (
        f1_fires and f2_collapse_fires and f2_smuggle_fires and f2_fixtures_identity_honest
        and intransitive_identity_fires
    )

    ok = all_gates_non_vacuous and no_llm["clean"] and headline_is_strict_coarsening and audit_fixes_confirmed

    result = {
        "schema_version": "ratchet-contract-selfcheck/0.2",
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "ceiling": "infrastructure_selfcheck_on_toy_candidates; promotion_allowed=false",
        "X_BASE": list(X_BASE),
        "D_BASE": [list(pair) for pair in D_BASE],
        "discrimination_matrix": matrix,
        "buildability_gate_vacuity_fixture": {
            "fixture_name": broken.name,
            "result": broken_result,
        },
        "evolvability_gate_extra_fixtures": {
            "collapses_distinction": {
                "fixture_name": evolve_collapse_fixture.name,
                "identity_gate": evolve_collapse_identity,
                "evolvability_gate": evolve_collapse_result,
            },
            "smuggles_primitive": {
                "fixture_name": evolve_smuggle_fixture.name,
                "identity_gate": evolve_smuggle_identity,
                "evolvability_gate": evolve_smuggle_result,
            },
        },
        "fail_branch_demonstrations": fail_branch_demonstrations,
        "vacuity_report": vacuity,
        "pairwise_mss_base": pairwise_base,
        "pairwise_mss_thickened": pairwise_thick,
        "frontier_base": frontier_base,
        "frontier_thickened": frontier_thick,
        "headline_pairwise_mss_result": headline_pair,
        "no_llm_or_network_calls": no_llm,
        "audit_response": {
            "audit_verdict_file": "results/AUDIT_VERDICT.md",
            "F1_negative_control_check_wired": True,
            "F1_fires_in_this_receipt": f1_fires,
            "F2_evolvability_D_collapse_branch_fires_in_this_receipt": f2_collapse_fires,
            "F2_evolvability_primitive_smuggle_branch_fires_in_this_receipt": f2_smuggle_fires,
            "F2_new_fixtures_are_identity_honest": f2_fixtures_identity_honest,
            "F1_identity_internal_contradiction_fires": intransitive_identity_fires,
        },
        "confirmations": {
            "all_gates_non_vacuous": all_gates_non_vacuous,
            "no_llm_or_network_calls_clean": no_llm["clean"],
            "headline_pairwise_mss_is_strict_coarsening": headline_is_strict_coarsening,
            "audit_fixes_confirmed": audit_fixes_confirmed,
            "overall_ok": ok,
        },
    }

    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_PATH.write_text(json.dumps(result, indent=2, sort_keys=False) + "\n", encoding="utf-8")

    print(json.dumps(result["confirmations"], indent=2))
    print(f"\nfull receipt written to {RESULTS_PATH}")
    print(f"\nheadline pairwise_mss(toy_frozen, toy_quotient_respecting, X_BASE, D_BASE) = "
          f"{headline_pair['verdict']}: {headline_pair['reasons'].get('reason')}")
    print(f"\nF1 (negative-control leak) fires: {f1_fires}")
    print(f"F2 (evolvability D-collapse) fires: {f2_collapse_fires}")
    print(f"F2 (evolvability primitive-smuggle) fires: {f2_smuggle_fires}")
    print("new toy IDENTITY_GATE = "
          f"{matrix['toy_intransitive_reidentify']['IDENTITY_GATE']['verdict']}: "
          f"{matrix['toy_intransitive_reidentify']['IDENTITY_GATE']['reasons']}")
    print("collapsed-demand breakdown fields are emitted on continuation FAILs as "
          "already_collapsed_at_base_edges and newly_collapsed_by_continuation_edges")

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
