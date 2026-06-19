# Independent verification — survivor-set-restriction noncommutation crux

**Auditor:** fresh-context subagent. No git run. Files only under this sim dir.
**Date:** 2026-06-14. **Ceiling:** scratch_diagnostic, promotion_allowed=false.

## What was on disk (the "earning sim")

The crux describes `finite_ordered_survivor_ratchet_emergence_v0` /
`..._definition_witness_v0` from
`system_v6/foundations/ratchet_definition_and_emergence_spec_DRAFT_20260614.md` §5.
**That sim is NOT built anywhere in the repo.** What exists:
- the §5 SPEC (a DRAFT, today-dated, ceiling `scratch_diagnostic`, no admission);
- `system_v7/sims/axis0_terrain_engine_leap_v0` — an explicit **BAD-TWIN negative
  fixture** (`build_card.md`) that deliberately carries the crux vocabulary
  (gnvw/survivor/amnesic/update_lex/update_geo) with `axis0_earned:true` as an
  intentionally unbacked claim, designed to FAIL gates;
- `finite_ring_checkerboard_qca_ordered_descending_chain_gnvw_v0` — an EMPTY stub
  (only an empty `results/` dir);
- adjacent quotient/carrier sims, none of which compute the survivor-set-restriction
  symdiff `delta(C_i,C_j)=|Surv(C_iC_j) symdiff Surv(C_jC_i)|`. The carrier sim
  computes map-noncommutation `U1∘U2≠U2∘U1` on elements, not survivor-set restriction.

There was therefore **no builder output to trust or distrust**. Per the task I
re-derived the crux quantities from scratch in a new sim dir and ran all legs.

## What I built and ran (3 independent engines, all exit 0)

| Engine | Code path | exit |
|---|---|---|
| JAX | vmap indicator-vector XOR symdiff + z3/cvc5 on measured ints | 0 |
| PyTorch | boolean-tensor XOR symdiff + permutation-matrix winding GNVW | 0 |
| Julia | from-scratch native Set symdiff + modular winding (different language) | 0 |

Three-engine agreement: **clean, zero mismatches** (`check_agreement.py` exit 0).
`reads_peer_result=false` on all three; Julia is an independent reimplementation.

## The re-derived numbers (all three engines agree)

| Quantity | value | reading |
|---|---|---|
| `delta_history_dependent` | **2** | survivor-set-restriction noncommutation is REAL (nonzero) |
| `delta_static_control_extensional` | **0** | pure set-intersection commutes (the ratchet_s1-style commuting-filter case) |
| `delta_static_control_x_reactive` | **3** | FINDING: a history-INDEPENDENT CA-style local rule still does NOT commute |
| `delta_mixed_history_dependent` | **2** | clean R3 isolator: noncommutes with H-read |
| `delta_mixed_amnesic` | **0** | removing ONLY the H-read collapses it to 0 — memory is the engine |
| GNVW left/right/identity | **-1 / +1 / 0** | signs flip for L/R, 0 for identity |
| Phi square fidelity | **1.0** | BUT by construction (see below) |
| Phi wrong-lex control | 0.78 | the square test can break — discriminating |
| Phi scrambled-Phi control | 0.28 | the square test can break — discriminating |
| SMT memory-is-engine flip | z3 SAT / cvc5 SAT / erased UNSAT | confirmed on measured ints |

## Findings the spec glosses (held open, not collapsed)

1. **"Static predicates commute" is true ONLY for extensional predicates.** The
   spec §2.2 HOLE-3 prose says static/extensional predicates commute because
   `A∩B=B∩A`. My extensional control (per-cell absolute property) gives delta=0,
   confirming that. BUT a history-INDEPENDENT *CA-style local rule* that reads the
   CURRENT survivor-set neighbourhood gives delta=3 — it does NOT commute. So
   there are TWO distinct "static control" readings with OPPOSITE answers. The
   order-sensitivity has (at least) two sources: (i) the history-ledger read R3,
   and (ii) the running-survivor-set read. Both must be ablated to attribute
   noncommutation to memory.

2. **The amnesic ablation needs the MIXED-rule isolator to be clean.** The naive
   amnesic ablation of `rule_hist` makes that rule VACUOUS (it only ever fires on
   a history read), so delta→0 is partly "rule switched off", not "two live rules
   now commute". The mixed-rule isolator (`rule_hist_mixed_*`, which keeps an
   X-reactive kill under amnesia) gives delta_mixed_history=2, delta_mixed_amnesic=0:
   a NON-trivial rule still collapses to commuting when ONLY the H-read is removed.
   That is the clean proof that the H-read (R3 memory) is the engine.

3. **The Phi commuting square closes by construction.** `update_lex` literally
   reuses the geometric constraint and Phi is the identity-on-index bijection, so
   `Phi∘Update_lex = Update_geo∘Phi` is a tautology (the same object projected two
   ways agrees with itself). The negative controls prove the test is not vacuous,
   but the positive 1.0 does NOT earn an independent lexical↔geometric map. This is
   exactly spec fork (A) "analogy-until-Phi-built" and the §5.5 near-tautology gap.

4. **GNVW is genuine but unbridged.** L/R/identity = -1/+1/0 is a real translation
   index computed from the permutation winding, but it is an independent fact about
   ring shifts, NOT coupled to the survivor noncommutation. It does not close the
   map↔constraint gap either.

## Verdict: definition_witness_only

- The survivor-set-restriction noncommutation is **genuinely nonzero** for the
  history-dependent pair and **genuinely zero** for the extensional control.
- The amnesic ablation **genuinely collapses** the noncommutation (memory is the
  engine, R3 confirmed) under the clean mixed-rule isolator.
- The GNVW signs **genuinely flip**.
- BUT the lexical↔geometric bridge (the Phi commuting square) **closes by
  construction**, not by an earned lower-level derivation. The ratchet is realized
  and its defining properties are witnessed with real controls, but EMERGENCE — the
  ratchet provably FALLING OUT of local QCA rules + topology rather than being
  re-instantiated from the definition — is NOT demonstrated. The map↔constraint gap
  is described and isolated, not closed.

This matches the spec's own honest ceiling (§6: "Unified emergence: NOT YET EARNED",
fork A live). The crux machinery is real and the controls discriminate; the object
witnesses the DEFINITION. It does not smuggle (every scalar is recomputed across
three independent engines with firing controls) and it does not fail.
