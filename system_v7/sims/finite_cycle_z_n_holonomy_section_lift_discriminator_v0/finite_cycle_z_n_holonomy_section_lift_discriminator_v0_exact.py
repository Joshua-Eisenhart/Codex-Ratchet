#!/usr/bin/env python3
"""Executable answer to the Ratchet Runbook full-run ledger's caveat #3:
"when does increasing probe resolution FORCE a genuine lift rather than just a
finer finite quotient?" -- i.e., is the rejection of lifts a by-construction
artifact of finite probes, or a real, flip-able discriminator?

Setup (all finite, no continuum). Base = cycle Z_m (nodes 0..m-1, edges i->i+1
and the wraparound m-1->0). A connection g assigns a phase increment g_e in Z_N
to each edge. The lift is the discrete Z_N bundle; a configuration over node i is
a phase p in Z_N reached by walking from a basepoint.

Two probe regimes:
  * endpoint-only probe -> the bare quotient = the nodes (phase erased)
  * endpoint + phase probe (resolution N) -> the full lift

The discriminator (standard obstruction theory, finite + decidable):
  A GLOBAL SECTION exists  <=>  the phase is a function of the node (a label that
  refines the base partition)  <=>  the lift is NOT forced (refinement suffices).
  A global section exists  <=>  the total HOLONOMY H = sum(g) mod N == 0
  (equivalently the H^1(Z_m; Z_N) class is trivial).
  H != 0  =>  no global section  =>  the bare/refined quotient CANNOT carry the
  phase consistently  =>  a finite Z_N FIBER LIFT is FORCED.

So: the lift is forced by HOLONOMY (a finite cohomology class), NOT by resolution.
Increasing N only refines granularity; it never changes the forced/not verdict.
The continuum is never needed. This both (a) confirms the runbook run (continuous
Hopf/U(1) lift is not forced) and (b) refines it (a finite Z_N lift IS forced
when holonomy is nonzero) -- and it FLIPS on the trivial-connection control, so it
is not a by-construction artifact.

Cross-check: section-existence is computed TWO independent ways --
  A) the closed-form  sum(g) % N == 0
  B) an explicit search for phi: nodes->Z_N with phi[i+1]-phi[i] == g_i on every
     edge INCLUDING the wraparound (a genuine constraint solve)
They must agree on every case.
"""

import json
import os
import hashlib
from math import gcd
from datetime import datetime, timezone

SIM_ID = "finite_cycle_z_n_holonomy_section_lift_discriminator_v0"
HERE = os.path.dirname(os.path.abspath(__file__))


def sha256_of(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def holonomy(g, N):
    return sum(g) % N


def section_exists_formula(g, N):
    return holonomy(g, N) == 0


def section_exists_search(g, N):
    """Explicit independent solve: does phi: nodes->Z_N exist with
    phi[(i+1)%m] - phi[i] == g[i] (mod N) for every edge i (incl wraparound)?
    Fix phi[0]=0, propagate forward, then check the wraparound edge closes."""
    m = len(g)
    phi = [0] * m
    for i in range(m - 1):
        phi[i + 1] = (phi[i] + g[i]) % N
    # wraparound edge (m-1 -> 0): need phi[0] - phi[m-1] == g[m-1]
    closes = ((phi[0] - phi[m - 1]) % N) == (g[m - 1] % N)
    return closes


def sheets_over_basepoint(g, N):
    """number of distinct phases the basepoint is reachable with = |<H>| in Z_N."""
    H = holonomy(g, N)
    return N // gcd(N, H) if H != 0 else 1


def analyze(g, N):
    H = holonomy(g, N)
    sa = section_exists_formula(g, N)
    sb = section_exists_search(g, N)
    s = sheets_over_basepoint(g, N)
    no_global_section = not sa  # finite obstruction sanity check (NOT a lift discriminator -- fleet 6/6 circular)
    return {
        "g": list(g), "N": N, "holonomy": H,
        "section_exists_formula": sa, "section_exists_search": sb,
        "methods_agree": sa == sb,
        "sheets_over_basepoint": s,
        "bare_quotient_erases_a_distinction": s > 1,
        "no_global_section": no_global_section,
    }


def main():
    m = 4  # base cycle length
    cases = []

    # NEGATIVE CONTROL family: trivial holonomy (sum == 0) at several resolutions
    for N in (2, 3, 4, 6, 12):
        g = [1, 0, 0, (N - 1) % N]  # sum = N == 0 mod N  -> H=0
        cases.append(("control_trivial_holonomy", analyze(g, N)))

    # POSITIVE family: nontrivial holonomy, put H on one edge, sweep H and N
    positives = []
    for N in (2, 3, 4, 6, 12):
        for H in range(1, N):
            g = [H, 0, 0, 0]  # holonomy = H != 0
            res = analyze(g, N)
            positives.append(res)
            cases.append(("positive_nontrivial_holonomy", res))

    # ---- the load-bearing claims ----
    methods_all_agree = all(c[1]["methods_agree"] for c in cases)
    # the FLIP: forced iff holonomy != 0, across ALL cases
    flip_clean = all(c[1]["no_global_section"] == (c[1]["holonomy"] != 0) for c in cases)
    # control: trivial holonomy => lift NOT forced (every resolution)
    control_rejects = all(not c[1]["no_global_section"] for c in cases if c[0] == "control_trivial_holonomy")
    # resolution-independence: for fixed nonzero holonomy structure, forced verdict
    # does not depend on N (it is always forced); and refinement-only never forces.
    positives_all_forced = all(p["no_global_section"] for p in positives)
    # the answer to caveat #3: forced verdict is a function of holonomy, NOT of N
    resolution_does_not_force = control_rejects and positives_all_forced

    result = {
        "schema": "codex_ratchet.engine_leg_result.v1",
        "sim_id": SIM_ID,
        "engine": "exact",
        "computation_style": "finite_cyclic_connection_section_obstruction_two_methods",
        "classification": "scratch_diagnostic",
        "evidence_eligible": False,
        "evidence_ineligible_reason": "CIRCULAR (fleet wlgj6haef 6/6): definitional restatement of the standard obstruction theorem; cannot back an evidence_grade row. Finite obstruction sanity check only.",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "does_not_self_upgrade": True,
        "reads_peer_result": False,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_sha256": sha256_of(os.path.abspath(__file__)),
        "result_path": f"system_v7/sims/{SIM_ID}/results/{SIM_ID}_exact_results.json",
        "base_cycle_length": m,
        "claims": {
            "two_methods_agree_section_existence": methods_all_agree,
            "no_global_section_iff_holonomy_nonzero": flip_clean,  # standard theorem sanity check, NOT a lift discriminator
            "trivial_holonomy_control_rejects_lift": control_rejects,
            "resolution_does_not_force_lift_holonomy_does": resolution_does_not_force,
            "interpretation": (
                "RETRACTED as a finding (fleet wlgj6haef 6/6 CIRCULAR; deep audit w2qgptvqb): this is a "
                "DEFINITIONAL restatement of the standard obstruction theorem (a Z_N bundle over a cycle has a "
                "global section iff total holonomy vanishes mod N). lift_forced := not section_exists, so "
                "'forced iff holonomy != 0' adds no empirical check. The two-methods-agree test is NOT independent "
                "(both prove the same theorem). It does NOT answer caveat #3 (stays finite; never engages the "
                "continuum) and does NOT show a fiber is forced over a larger quotient. Cite FLEET_VERDICT_20260615.md."
            ),
        },
        "cases": [{"family": fam, **res} for fam, res in cases],
        "honest_scope": {
            "earns": "ONLY a sanity check that the standard finite fact holds (a Z_N bundle over a cycle has a global section iff total holonomy vanishes mod N), via two agreeing methods. The control/positive FLIP is a HELD DIVERGENCE (fleet 2 genuine / 4 rigged-by-definition), NOT a settled bias-check. finite_refinement_vs_larger_quotient_unresolved=true: it does NOT show a fiber lift is forced rather than a larger finite quotient.",
            "does_not_earn": "claim 'lift_forced iff holonomy!=0' is CIRCULAR (lift_forced := not section_exists; fleet wlgj6haef 4/4) -- a restatement of the standard obstruction theorem, not an independent finding. It does NOT answer caveat #3: it stays finite and never engages the continuum. The real answer to caveat #3 is F01 (continuous lifts are never forced -- declared, not a hidden bias); that lives in the runbook, not here. scratch_diagnostic.",
            "fleet_verdict": "CIRCULAR / does-not-close-caveat-3 (FLEET_VERDICT_20260615.md). Cite that, not these self-claims.",
        },
        "TOOL_MANIFEST": {"python-stdlib": {"tried": True, "used": True, "reason": "exact integer/gcd obstruction computation, two independent methods"}},
        "TOOL_INTEGRATION_DEPTH": {"python-stdlib": "supportive"},
    }

    out = os.path.join(HERE, "results", f"{SIM_ID}_exact_results.json")
    with open(out, "w") as f:
        json.dump(result, f, indent=2)
    c = result["claims"]
    print(f"exact leg wrote {out}")
    print(f"  two_methods_agree            = {c['two_methods_agree_section_existence']}")
    print(f"  no_global_section IFF holonomy!=0 = {c['no_global_section_iff_holonomy_nonzero']}  (standard theorem sanity check, NOT a lift flip)")
    print(f"  trivial-holonomy control rejects lift = {c['trivial_holonomy_control_rejects_lift']}")
    print(f"  resolution does NOT force; holonomy does = {c['resolution_does_not_force_lift_holonomy_does']}")
    print(f"  ({len([x for x in cases if x[0]=='positive_nontrivial_holonomy'])} positive cases, "
          f"{len([x for x in cases if x[0]=='control_trivial_holonomy'])} control cases)")


if __name__ == "__main__":
    main()
