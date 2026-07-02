#!/usr/bin/env python3
"""Capstone of the runbook lift-adjudication wave (2026-06-15).

The gluing fleet (wf wlibwq2pd) left one frontier: contextuality kills only
NONCONTEXTUAL classical models on the FIXED cover; glm-5.1 noted a context-indexed
classical model on an enlarged quotient could still reproduce the statistics. If
so, NO carrier is forced 'beyond every quotient' -- the lift is installed.

This sim settles it for the strongest finite obstruction (Peres-Mermin):
  (1) NONCONTEXTUAL classical model: one value per observable, shared across all
      contexts -> z3 UNSAT (this IS contextuality).
  (2) CONTEXT-INDEXED classical model: a value per (observable, context); the same
      observable may take different values in different contexts -> z3 SAT.

Reading: contextuality is NOT 'a carrier forced beyond every quotient'. It is
exactly the failure of CONTEXT-INDEPENDENCE. A classical model on a context-indexed
(enlarged) quotient reproduces it. So the non-classical lift (rho) appears only once
you INSTALL context-independence as a constraint -- and that demand is not forced by
finite probe data. Under F01 the quotient floor + refinement/context-indexing suffices.

FENCED: this is demonstrated for the Peres-Mermin obstruction (the strongest finite
no-noncontextual-model witness). It STRONGLY SUGGESTS, but does NOT prove, the
universal claim 'no carrier is ever forced beyond every quotient.' That universal
needs more obstruction classes + a fleet pass. scratch_diagnostic, no promotion.
"""

import json
import os
import hashlib
from datetime import datetime, timezone

import z3

SIM_ID = "contextuality_as_installed_context_independence_smt_v0"
HERE = os.path.dirname(os.path.abspath(__file__))

CELLS = ["a", "b", "c", "d", "e", "f", "g", "h", "i"]
CONTEXTS = {"R1": ["a", "b", "c"], "R2": ["d", "e", "f"], "R3": ["g", "h", "i"],
            "C1": ["a", "d", "g"], "C2": ["b", "e", "h"], "C3": ["c", "f", "i"]}
PM = {"R1": 1, "R2": 1, "R3": 1, "C1": 1, "C2": 1, "C3": -1}


def sha256_of(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def noncontextual():
    s = z3.Solver()
    v = {c: z3.Int(c) for c in CELLS}
    for c in CELLS:
        s.add(z3.Or(v[c] == 1, v[c] == -1))
    for ctx, cells in CONTEXTS.items():
        s.add(v[cells[0]] * v[cells[1]] * v[cells[2]] == PM[ctx])
    return str(s.check())


def context_indexed():
    s = z3.Solver()
    w = {(c, ctx): z3.Int(f"{c}_{ctx}") for ctx in CONTEXTS for c in CONTEXTS[ctx]}
    for k in w:
        s.add(z3.Or(w[k] == 1, w[k] == -1))
    for ctx, cells in CONTEXTS.items():
        s.add(w[(cells[0], ctx)] * w[(cells[1], ctx)] * w[(cells[2], ctx)] == PM[ctx])
    return str(s.check())


def main():
    nonctx = noncontextual()
    ctxidx = context_indexed()
    deflation = (nonctx == "unsat" and ctxidx == "sat")
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    result = {
        "schema": "codex_ratchet.engine_leg_result.v1",
        "sim_id": SIM_ID,
        "engine": "smt",
        "computation_style": "noncontextual_vs_context_indexed_classical_model_z3",
        "classification": "broken",
        "graveyard_keep": True,
        "refuted_by": "REFUTED_20260615.md (deep audit wf w2qgptvqb): by-construction tautology + carrier smuggle",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "does_not_self_upgrade": True,
        "reads_peer_result": False,
        "generated_at": timestamp,
        "written_at": timestamp,
        "source_sha256": sha256_of(os.path.abspath(__file__)),
        "result_path": f"system_v7/sims/{SIM_ID}/results/{SIM_ID}_smt_results.json",
        "noncontextual_model_smt": nonctx,
        "context_indexed_model_smt": ctxidx,
        "positive_tests": {
            "noncontextual_model_unsat": nonctx == "unsat",
        },
        "negative_tests": {
            "context_indexed_model_sat_by_construction": ctxidx == "sat",
            "deflationary_thesis_retracted": deflation,
            "accepted_claims_empty": True,
        },
        "facts": {
            "noncontextual_model_smt": nonctx,
            "context_indexed_model_smt": ctxidx,
            "classification": "broken",
            "graveyard_keep": True,
        },
        "accepted_claims": [],
        "rejected_claims": [
            "context_indexed_classical_model_is_sat is a BY-CONSTRUCTION TAUTOLOGY (18 independent variables; SAT for all 64 sign combos; z3 adds nothing)",
            "calling the context-indexed model 'classical' is CIRCULAR (the context-label carries the non-classical structure)",
            "'contextuality = failure of context-independence, not beyond quotient' / the deflationary thesis -- RETRACTED",
        ],
        "honest_scope": {
            "earns": "NOTHING. This sim is REFUTED (classification=broken). The only non-trivial fact (noncontextual UNSAT) is a third copy of finite_contextuality_assignment_smt_lift_discriminator_v0.",
            "does_not_earn": "anything. See REFUTED_20260615.md. The question 'is any carrier forced beyond every quotient?' is UNRESOLVED.",
        },
        "thesis_candidate_fenced": "RETRACTED -- REFUTED_20260615.md. The context_indexed() SAT is a by-construction tautology (18 independent vars) and the carrier is smuggled via context-labels (a_R1 != a_C1 = the non-classical structure relabeled). This sim does NOT earn the deflationary thesis. The question 'is any carrier forced beyond every quotient?' is UNRESOLVED.",
        "REFUTED": "see REFUTED_20260615.md (deep audit wf w2qgptvqb): by-construction tautology + carrier smuggle. Do not cite. GRAVEYARD_KEEP.",
        "packages_used": ["z3"],
        "TOOL_MANIFEST": {"z3": {"tried": True, "used": True, "reason": "ran, but the context_indexed SAT is by-construction -- z3 not load-bearing here (REFUTED)"}},
        "TOOL_INTEGRATION_DEPTH": {"z3": "decorative_refuted"},
    }

    out = os.path.join(HERE, "results", f"{SIM_ID}_smt_results.json")
    with open(out, "w") as f:
        json.dump(result, f, indent=2)
    print(f"wrote {out}  [REFUTED / classification=broken]")
    print(f"  noncontextual model smt: {nonctx} (a 3rd copy of the assignment sim)")
    print(f"  context_indexed smt: {ctxidx} (BY-CONSTRUCTION TAUTOLOGY -- 18 independent vars, not a finding)")
    print(f"  REFUTED: deflationary thesis retracted (carrier smuggle); see REFUTED_20260615.md")


if __name__ == "__main__":
    main()
