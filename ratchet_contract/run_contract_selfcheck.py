#!/usr/bin/env python3
"""
run_contract_selfcheck.py -- instantiate the toys, run every gate on each,
run pairwise_mss/frontier on toy pairs, write
ratchet_contract/results/selfcheck.json = the discrimination matrix
(gate x toy -> verdict) + pairwise_mss results (base-only and
demand-thickened) + a mechanical, grep-based confirmation that no LLM or
network call exists anywhere in this contract.

Exit codes (matches fuel_gate/fuel_adequacy_gate.py's discipline -- the
interface is the exit code, not printed prose):
    0 = every gate demonstrated >=2 distinct verdicts across the toy set
        (non-vacuous), the no-LLM/network scan is clean, and the headline
        pairwise_mss demo is a genuine strict coarsening.
    1 = one of those checks failed -- printed JSON names which.
"""

from __future__ import annotations

import itertools
import json
import sys
from pathlib import Path

from contract import Carrier, CandidatePackage, ControlSet, NestInterface
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


def _build_matrix(toys):
    matrix = {}
    for c in toys:
        matrix[c.name] = {
            "buildability_gate": buildability_gate(c).to_json(),
            "probe_validity_gate__own_D": probe_validity_gate(c).to_json(),
            "probe_validity_gate__thin_D": probe_validity_gate(c, D=("constant_probe",)).to_json(),
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
    vacuity["probe_validity_gate"] = {
        "own_D_verdicts": pv_own,
        "thin_D_verdicts": pv_thin,
        "distinct_verdicts": sorted(set(list(pv_own.values()) + list(pv_thin.values()))),
        "pass": len(set(list(pv_own.values()) + list(pv_thin.values()))) >= 2,
        "note": "own_D (the toy's own adequate probes) demonstrates PASS; thin_D=('constant_probe',) "
                "demonstrates HOLD -- 'probe family has not demonstrated discrimination power'",
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

    all_gates_non_vacuous = all(v["pass"] for v in vacuity.values())
    headline_is_strict_coarsening = headline_pair["verdict"] in ("A_WEAKER", "B_WEAKER")
    ok = all_gates_non_vacuous and no_llm["clean"] and headline_is_strict_coarsening

    result = {
        "schema_version": "ratchet-contract-selfcheck/0.1",
        "ceiling": "infrastructure_selfcheck_on_toy_candidates; promotion_allowed=false",
        "X_BASE": list(X_BASE),
        "D_BASE": [list(pair) for pair in D_BASE],
        "discrimination_matrix": matrix,
        "buildability_gate_vacuity_fixture": {
            "fixture_name": broken.name,
            "result": broken_result,
        },
        "vacuity_report": vacuity,
        "pairwise_mss_base": pairwise_base,
        "pairwise_mss_thickened": pairwise_thick,
        "frontier_base": frontier_base,
        "frontier_thickened": frontier_thick,
        "headline_pairwise_mss_result": headline_pair,
        "no_llm_or_network_calls": no_llm,
        "confirmations": {
            "all_gates_non_vacuous": all_gates_non_vacuous,
            "no_llm_or_network_calls_clean": no_llm["clean"],
            "headline_pairwise_mss_is_strict_coarsening": headline_is_strict_coarsening,
            "overall_ok": ok,
        },
    }

    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_PATH.write_text(json.dumps(result, indent=2, sort_keys=False) + "\n", encoding="utf-8")

    print(json.dumps(result["confirmations"], indent=2))
    print(f"\nfull receipt written to {RESULTS_PATH}")
    print(f"\nheadline pairwise_mss(toy_frozen, toy_quotient_respecting, X_BASE, D_BASE) = "
          f"{headline_pair['verdict']}: {headline_pair['reasons'].get('reason')}")

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
