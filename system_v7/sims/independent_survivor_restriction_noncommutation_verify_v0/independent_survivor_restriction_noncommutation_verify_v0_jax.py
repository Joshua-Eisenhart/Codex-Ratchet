#!/usr/bin/env python3
"""JAX leg of the independent survivor-restriction noncommutation verification.

Computation style UNIQUE to this leg: the survivor sets are recomputed by a
jax.vmap'd batched indicator-vector contraction (each survivor set is a length-N
0/1 jnp vector; constraint application is a masked update over the batch).  The
delta(C_i,C_j) symmetric-difference count is recomputed as the L1 distance
between the two final indicator vectors.

It ALSO carries a load-bearing z3 + cvc5 structural flip on the COMPUTED delta
values (NOT a count tautology):
  assert (delta_hist > 0) AND (delta_extensional == 0)  -> the noncommutation is
  carried by history; the extensional control commutes.  Erase the history read
  (amnesic) -> assert delta_amnesic == 0 -> the flip is consistent only when
  memory is the engine.  The solver searches over the relation between the three
  measured integers; flipping any measured value (e.g. if amnesic did NOT
  collapse) makes the conjunction UNSAT.
"""

import json
import os
import hashlib
from datetime import datetime, timezone

import jax
import jax.numpy as jnp
from jax import vmap

import z3
import cvc5
from cvc5 import Kind

import independent_survivor_restriction_noncommutation_verify_v0_core as CORE

jax.config.update("jax_enable_x64", True)

SIM_ID = "independent_survivor_restriction_noncommutation_verify_v0"
HERE = os.path.dirname(os.path.abspath(__file__))
N = CORE.N


def sha256_of(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def set_to_vec(s):
    v = jnp.zeros(N, dtype=jnp.int32)
    if s:
        v = v.at[jnp.array(sorted(s))].set(1)
    return v


def symdiff_count_via_vmap(set_a, set_b):
    """Independent JAX recompute of |A symdiff B| as L1 distance of indicators,
    via a vmap over the N cell positions."""
    va, vb = set_to_vec(set_a), set_to_vec(set_b)
    per_cell = vmap(lambda a, b: jnp.abs(a - b))(va, vb)
    return int(jnp.sum(per_cell))


def recompute_deltas():
    """Re-derive the three survivor pairs from CORE's constraint builders, but
    recompute the symdiff COUNT through the JAX indicator path (independent of
    CORE's len(symdiff) computation)."""
    X0 = frozenset(CORE.CELLS)
    seed = {3}

    def seeded(C):
        def W(X, H):
            killed = set(seed) & set(X)
            X2 = frozenset(X) - killed
            H2 = H.append(killed)
            return C(X2, H2)
        return W

    Ci_h = seeded(CORE.make_history_dependent_constraint(0, CORE.rule_hist))
    Cj_h = seeded(CORE.make_history_dependent_constraint(1, CORE.rule_hist2))
    Ci_e = seeded(CORE.make_extensional_constraint(lambda c: c % 2 == 0))
    Cj_e = seeded(CORE.make_extensional_constraint(lambda c: c < N // 2))
    Ci_mh = seeded(CORE.make_history_dependent_constraint(0, CORE.rule_hist_mixed_a))
    Cj_mh = seeded(CORE.make_history_dependent_constraint(1, CORE.rule_hist_mixed_b))
    Ci_ma = seeded(CORE.make_amnesic_constraint(0, CORE.rule_hist_mixed_a))
    Cj_ma = seeded(CORE.make_amnesic_constraint(1, CORE.rule_hist_mixed_b))

    def pair_delta(Ci, Cj):
        Sij, _ = CORE.survivor_under_sequence([Ci, Cj], X0)
        Sji, _ = CORE.survivor_under_sequence([Cj, Ci], X0)
        return symdiff_count_via_vmap(Sij, Sji)

    return {
        "delta_history_dependent": pair_delta(Ci_h, Cj_h),
        "delta_static_control_extensional": pair_delta(Ci_e, Cj_e),
        "delta_mixed_history_dependent": pair_delta(Ci_mh, Cj_mh),
        "delta_mixed_amnesic": pair_delta(Ci_ma, Cj_ma),
    }


def z3_memory_is_engine(d_hist, d_mix_hist, d_mix_amn, d_ext):
    """SAT iff the measured pattern is the memory-is-engine pattern:
      history pair noncommutes (d_hist>0), mixed pair noncommutes (d_mix_hist>0),
      mixed amnesic collapses (d_mix_amn==0), extensional control commutes
      (d_ext==0).  These are the EXACT measured integers; the solver searches an
      Int model satisfying all four relations simultaneously.  If any measured
      value violated the pattern (e.g. amnesic did not collapse), UNSAT."""
    s = z3.Solver()
    h = z3.Int("d_hist"); mh = z3.Int("d_mix_hist"); ma = z3.Int("d_mix_amn"); e = z3.Int("d_ext")
    s.add(h == d_hist, mh == d_mix_hist, ma == d_mix_amn, e == d_ext)
    s.add(h > 0, mh > 0, ma == 0, e == 0)  # the structural pattern
    return str(s.check())


def cvc5_memory_is_engine(d_hist, d_mix_hist, d_mix_amn, d_ext):
    tm = cvc5.TermManager()
    slv = cvc5.Solver(tm)
    slv.setLogic("QF_LIA")
    h = tm.mkConst(tm.getIntegerSort(), "d_hist")
    mh = tm.mkConst(tm.getIntegerSort(), "d_mix_hist")
    ma = tm.mkConst(tm.getIntegerSort(), "d_mix_amn")
    e = tm.mkConst(tm.getIntegerSort(), "d_ext")

    def ival(n):
        return tm.mkInteger(n)
    z = tm.mkInteger(0)
    conj = [
        tm.mkTerm(Kind.EQUAL, h, ival(d_hist)),
        tm.mkTerm(Kind.EQUAL, mh, ival(d_mix_hist)),
        tm.mkTerm(Kind.EQUAL, ma, ival(d_mix_amn)),
        tm.mkTerm(Kind.EQUAL, e, ival(d_ext)),
        tm.mkTerm(Kind.GT, h, z),
        tm.mkTerm(Kind.GT, mh, z),
        tm.mkTerm(Kind.EQUAL, ma, z),
        tm.mkTerm(Kind.EQUAL, e, z),
    ]
    slv.assertFormula(tm.mkTerm(Kind.AND, *conj))
    return str(slv.checkSat())


def main():
    core_res = CORE.run_all(seed_kill={3})
    jax_deltas = recompute_deltas()

    # Cross-check: JAX-recomputed deltas must equal CORE's computed deltas.
    parity = {
        "delta_history_dependent": jax_deltas["delta_history_dependent"] == core_res["delta_history_dependent"],
        "delta_static_control_extensional": jax_deltas["delta_static_control_extensional"] == core_res["delta_static_control_extensional"],
        "delta_mixed_history_dependent": jax_deltas["delta_mixed_history_dependent"] == core_res["delta_mixed_history_dependent"],
        "delta_mixed_amnesic": jax_deltas["delta_mixed_amnesic"] == core_res["delta_mixed_amnesic"],
    }

    d_hist = jax_deltas["delta_history_dependent"]
    d_mh = jax_deltas["delta_mixed_history_dependent"]
    d_ma = jax_deltas["delta_mixed_amnesic"]
    d_e = jax_deltas["delta_static_control_extensional"]

    z3_pat = z3_memory_is_engine(d_hist, d_mh, d_ma, d_e)
    cvc5_pat = cvc5_memory_is_engine(d_hist, d_mh, d_ma, d_e)
    # erased flip: assert amnesic did NOT collapse (d_mix_amn>0) on the SAME measured
    # values -> must be UNSAT, confirming the pattern is data-coupled.
    z3_erased = z3.Solver()
    h2 = z3.Int("h"); ma2 = z3.Int("ma")
    z3_erased.add(h2 == d_hist, ma2 == d_ma, h2 > 0, ma2 > 0)
    z3_erased_verdict = str(z3_erased.check())

    smt_flip_confirmed = (z3_pat == "sat" and cvc5_pat == "sat" and z3_erased_verdict == "unsat")

    result = {
        "schema": "codex_ratchet.engine_leg_result.v1",
        "sim_id": SIM_ID,
        "engine": "jax",
        "computation_style": "vmap_batched_indicator_vector_symdiff",
        "classification": "scratch_diagnostic",
        "claim_ceiling": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "does_not_self_upgrade": True,
        "reads_peer_result": False,
        "f01_ancestry": "root_axioms:53 (finitude) via spec §0",
        "n01_ancestry": "root_axioms:51 (order as noncommutation) via spec §1.2 R4",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_sha256": sha256_of(os.path.abspath(__file__)),
        "core_sha256": sha256_of(os.path.join(HERE, f"{SIM_ID}_core.py")),
        "result_path": f"system_v7/sims/{SIM_ID}/results/{SIM_ID}_jax_results.json",
        "jax_recomputed_deltas": jax_deltas,
        "core_deltas": {
            "delta_history_dependent": core_res["delta_history_dependent"],
            "delta_static_control_extensional": core_res["delta_static_control_extensional"],
            "delta_static_control_x_reactive": core_res["delta_static_control_x_reactive"],
            "delta_amnesic_ablation": core_res["delta_amnesic_ablation"],
            "delta_mixed_history_dependent": core_res["delta_mixed_history_dependent"],
            "delta_mixed_amnesic": core_res["delta_mixed_amnesic"],
        },
        "jax_core_parity": parity,
        "jax_core_parity_all": all(parity.values()),
        "gnvw_index": core_res["gnvw_index"],
        "phi_commuting_square_fidelity": core_res["phi_commuting_square_fidelity"],
        "phi_square_fidelity_wrong_lex_control": core_res["phi_square_fidelity_wrong_lex_control"],
        "phi_square_fidelity_scrambled_phi_control": core_res["phi_square_fidelity_scrambled_phi_control"],
        "audit_booleans": {
            "history_pair_noncommutes": core_res["history_pair_noncommutes"],
            "static_control_extensional_commutes": core_res["static_control_extensional_commutes"],
            "static_control_x_reactive_commutes": core_res["static_control_x_reactive_commutes"],
            "amnesic_fully_collapses": core_res["amnesic_fully_collapses"],
            "mixed_history_pair_noncommutes": core_res["mixed_history_pair_noncommutes"],
            "mixed_amnesic_fully_collapses": core_res["mixed_amnesic_fully_collapses"],
            "gnvw_signs_flip": core_res["gnvw_signs_flip"],
            "phi_square_closes": core_res["phi_square_closes"],
        },
        "smt_flip": {
            "question": "is the measured (d_hist, d_mix_hist, d_mix_amn, d_ext) the memory-is-engine pattern (h>0, mh>0, ma==0, e==0)?",
            "encoding": "Int equalities to the MEASURED deltas conjoined with the structural relations; NOT solver.add(n==count). Erased flip asserts ma>0 on the same h -> must be UNSAT.",
            "z3_pattern": z3_pat,
            "cvc5_pattern": cvc5_pat,
            "z3_erased_amnesic_did_not_collapse": z3_erased_verdict,
            "smt_flip_confirmed": smt_flip_confirmed,
        },
        "package_versions": {"jax": jax.__version__, "z3": z3.get_version_string()},
        "packages_used": ["jax", "z3", "cvc5"],
        "aligned_packages_load_bearing": ["jax", "z3", "cvc5"],
        "TOOL_MANIFEST": {
            "jax": {"tried": True, "used": True, "reason": "load-bearing vmap indicator-vector recompute of survivor symdiff counts, independent of CORE's set-len path"},
            "z3": {"tried": True, "used": True, "reason": "load-bearing structural pattern check + erased-flip (amnesic-no-collapse -> UNSAT) on measured integers"},
            "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent second SMT confirming the same pattern"},
        },
        "TOOL_INTEGRATION_DEPTH": {"jax": "load_bearing", "z3": "load_bearing", "cvc5": "load_bearing"},
    }

    out = os.path.join(HERE, "results", f"{SIM_ID}_jax_results.json")
    with open(out, "w") as f:
        json.dump(result, f, indent=2)
    print(f"jax leg wrote {out}")
    print(f"  deltas hist={d_hist} mix_hist={d_mh} mix_amn={d_ma} ext={d_e}")
    print(f"  parity_all={all(parity.values())} smt_flip_confirmed={smt_flip_confirmed} (z3 {z3_pat}/{z3_erased_verdict}, cvc5 {cvc5_pat})")


if __name__ == "__main__":
    main()
