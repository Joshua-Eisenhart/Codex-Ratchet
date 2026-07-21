# Bridge validation

This tests whether a proposed trace->partition bridge honestly lets the
**fixed** ratchet (`ratchet_contract/contract.py`, `gates.py`, `mss.py`) see
competing candidates. It does **not** ratchet the axioms, and it does not
admit any real carrier. It validates the **input interface** the ratchet
kernel is fed through — nothing about `IDENTITY_GATE`, `mss.py`'s
partition-coarseness judge, or the six gates changes here or is exercised
here beyond reusing their partition-coarseness kernel (`normalise_partition`,
`partition_coarser`, `partition_digest`, `collapsed_demand_edges` from
`gates.py`, and `ControlCase` from `contract.py`).

`promotion_allowed: false`. `formal_admission_allowed: false`. Passing this
campaign is the **precondition** to adapting real carriers into the bridge
contract — that adaptation is explicitly **not done here**.

## The corrected bridge contract

The owner's corrections (2026-07-20) override
`system_v8/bridge_designs/design_action_predictive_quotient.md` and
`design_smt_relational.md` wherever the two disagree:

- **Input** — a finite ORDERED PROBE WORD: a sequence of public actions.
  Not primitive time, not a causal state machine, just an ordered finite
  history. A `HistoryPoint` = `(root, prefix)` is the syntactic address of
  one such history.
- **Output** — a finite OUTCOME RECORD (`Outcome`, a multiplicity table
  over a finite token alphabet) plus an OPAQUE continuation state. No
  continuous or primitive probability anywhere on the shared surface:
  multiplicities are positive integers — counts, relative weights,
  instrument-branch weights — never floats.
- **Candidate interface** — `step_C(state, action, nest_context) ->
  (state', outcome)`. `state` is opaque: neither bridge in this package
  ever compares, hashes, or exposes an `OpaqueState` to a partition
  decision. Both bridges only ever compare `Outcome` records reached by
  replaying probe words from the syntactic `(root, prefix)` address.
- **Public vocabulary** — manifold-native operations, never POVM/
  membership/eigenprojector tokens: `prepare_restrict`, `ordered_compose`,
  `bracket_compose`, `perturb`, `delay_retain_history`,
  `couple_inner_outer`, `couple_neighbor_neighbor`, `renest`,
  `extend_under_constraint`, `read_outcome` (`MANIFOLD_ACTION_CATEGORIES`
  in `bridge_interface.py`).
- **Predictive quotient** — `h ~_C h'` iff, for every action word `u` with
  `|u| <= H`, replaying `u` from `h` and from `h'` produces identical
  `Outcome` traces. Deterministic equality over finite outcome records, no
  primitive probability anywhere in the comparison.
- **Bookkeeping vs illicit identity** (the rule every control is built to
  exercise) — code MAY use raw IDs/indices/hashes/equality for
  implementation bookkeeping (a memo dict keyed by `(root, prefix)`, a dict
  lookup keyed by a raw action token whose *value* is the declared
  meaning). That is not forbidden `a=a`. The violation is only when a
  handle **alters the semantic result** without an allowed probe/history
  exposing the difference. `C2` and the hidden-lookup-table self-test are
  the positive and negative demonstrations of exactly this line.

## The 3 dangers this campaign guards against

1. **Primitive time.** The input is an ordered *word*, not a causal state
   machine or a wall-clock. `bridge_interface.py`'s `FORBIDDEN_SURFACE_TOKENS`
   includes `time.time(`, `datetime.now(`, `perf_counter(`, and
   `causal_state_machine`; `run_bridge_validation.py` greps the campaign's
   own source for them every run.
2. **Primitive probability.** The output is a finite multiplicity table,
   never a continuous chance. `Outcome` rejects non-positive-integer
   multiplicities at construction time (`bridge_interface.py`); there is no
   quantizer anywhere in either bridge because there is nothing continuous
   left to quantize — the single biggest simplification the correction
   buys over the original design docs' `Q_epsilon` machinery.
3. **Deck neutrality is only conditional on a frozen deck.** No deck is
   neutral in the abstract; a claim of separation or of merge is only ever
   relative to the specific action alphabet used. `C7` (thin deck) and `C8`
   (carrier-biased deck) are the mechanical enforcement: a deck that is too
   thin to test a claim reports `HOLD`, never a false tie; a deck that only
   one candidate-shape can meaningfully answer is caught by ablation, never
   silently scored as a real discriminator.

## The two bridges — live rivals, neither primary

- **`bridge_action_predictive.py`** — the predictive-quotient bridge.
  Adapts `design_action_predictive_quotient.md` section 5's bounded
  backward color-refinement recursion. Memoized, bottom-up, provably the
  same relation as brute-force enumeration of every continuation word up
  to horizon `H` (`separating_witness` does the brute-force enumeration,
  used to cross-check the recursion and to produce a human-readable
  witness).
- **`bridge_smt_relational.py`** — the SMT-relational bridge. Adapts
  `design_smt_relational.md` sections 3-5. Ground facts (what `step_C`
  actually returns) can only come from replaying the candidate in Python —
  no solver can call an arbitrary Python object's `step_C`. What genuinely
  *is* delegated to z3 and cvc5 is the recursive combination of those
  ground facts into a same/different verdict at depth `H`: each `same_v`
  is a fresh solver Bool variable asserted via a hard iff-constraint
  referencing the *previously defined* variable one depth down — never a
  Python-precomputed literal substituted in — so `s.add(Not(same_H));
  s.check()` genuinely exercises the solver's own constraint propagation.
  `SAT` = distinct, `UNSAT` = same block. z3 and cvc5 are two
  **independently written** builders (not two renderers of one shared
  AST), cross-checked against each other and against a third, solver-free
  Python reference (`_reference_same`) on every pairwise decision — a
  disagreement among the three is a real, reported finding
  (`SmtDecision.agree`), never silently resolved by picking one.

`C9` requires the two bridges to agree on every exact toy case gathered
across `C1`-`C8`; `run_bridge_validation.py`'s `agreement_matrix` surfaces
the same data as its own top-level section.

## The 9 controls

Each control (`controls.py`) is a small candidate/deck isolating exactly
one bridge property, self-verifying like `toy_candidates.py` +
`run_contract_selfcheck.py`'s discrimination matrix. Current result
(`python3 run_bridge_validation.py`, fresh run — see "Reproducing" below):

| Control | Claim | Expected verdict | Observed | Fired as expected |
|---|---|---|---|---|
| C1 | two internally-different implementations (int-backed vs str-backed opaque state), identical behaviour | `MERGE` | `MERGE` | yes |
| C2 | raw-label relabeling that changes a semantic outcome vs. honest bookkeeping that doesn't | illicit `FAIL`, honest `PASS` | illicit `False`, honest `True` | yes |
| C3 | two histories distinguishable only by `ordered_compose` order | `SEPARATE` | `SEPARATE` | yes |
| C4 | a candidate that loses its record under `delay` | `FAIL persistence` | `FAIL_PERSISTENCE` | yes |
| C5 | a frozen candidate (`extend_under_constraint` always rejected) | `FAIL evolvability` | `FAIL_EVOLVABILITY` | yes |
| C6 | a candidate that works locally but cannot complete `renest` | `DEAD_END` / Purgatory | `DEAD_END` | yes |
| C7 | a deliberately thin action deck | `HOLD`, never a false tie | `HOLD_THIN_ACTION_DECK` | yes |
| C8 | a deliberately carrier-biased deck (`couple_neighbor_neighbor` only one candidate-shape can answer) | `DETECTED` or `HELD` | `DECK_BIAS_DETECTED` | yes |
| C9 | the two bridges agree on every exact toy case gathered from C1-C8 | `AGREE` | `AGREE` | yes |

All nine fired as expected on a fresh run. Where a control's `reasons` dict
carries a `bridge_agreement` note, that note is what `C9` aggregates — see
`results/bridge_validation.json`'s `agreement_matrix` for the full table.

**Methodological finding surfaced while building C2** (kept here because it
also shapes `bridge_self_tests.py`): checking whether two bridge-induced
*partitions* match is the wrong tool for relabeling-honesty. Partition
coarseness is invariant under any bijective relabeling of block content by
construction — that is the entire point of a quotient — so a candidate that
applies a *consistent* relabeling bug (for example, swapping every `pos`
outcome for `neg` under a renamed deck) can still induce a partition with
identical grouping structure, silently passing a partition-only check. `C2`
and the self-tests below therefore compare raw outcome content against the
fixed, un-relabeled outcome vocabulary — never partition digests — for the
property that actually matters. `bridge_self_tests.py`'s relabeling
self-test checks this claim directly rather than asserting it: on the
illicit candidate built for `C2`, the partition-only view is confirmed to
stay invariant (would-be-missed) while the direct-content view correctly
fails.

## The 3 bridge self-tests

`bridge_self_tests.py`, distinct from the 9 candidate-level controls —
these test the bridges' own invariance properties, not a candidate's
behaviour:

1. **Action-deck permutation + relabeling invariance.** Renaming action
   tokens must not change what a candidate reports for the semantically
   same history. Checked by direct outcome-content comparison (see the
   methodological finding above), on both the honest and illicit
   candidates from `C2`.
2. **Outcome-encoding change invariance.** Renaming the *outcome* token
   vocabulary (not the action vocabulary), consistently, must not change
   the induced *partition*. True by construction for any bridge that only
   ever compares `Outcome` values by structural equality rather than
   pattern-matching a specific token string — checked here, not just
   assumed, on both bridges.
3. **Hidden lookup-table control.** A candidate that hides a hand-authored
   answer table behind `step_C`, keyed by the literal raw action-token
   strings rather than any genuine order/continuation-sensitive rule, must
   be caught. The opaque-state interface does not make `step_C` neutral by
   itself — this candidate is caught the same way `C2`'s illicit candidate
   is caught (relabeling exposes that the table's keys never travelled
   with the renaming), and separately by falling through to a constant
   default on a word combination its hand-authored table never covered.

All three fired as expected on a fresh run.

## Known issue (diagnosed, worked around, not hidden)

The cvc5 Python binding (`cvc5.cvc5_python_base`) segfaults during normal
CPython interpreter shutdown once enough `Solver`/`TermManager` objects
have been created in-process (confirmed with `python3 -X faulthandler`: the
crash is inside "Garbage-collecting" with zero Python frames on the stack,
*after* `main()` had already returned its correct exit code and every
result was written and printed). The bug is in cvc5's native destructor/
finalizer ordering on interpreter teardown, not in anything this package
computes. `run_bridge_validation.py`'s `__main__` block flushes stdout/
stderr and then calls `os._exit()`, which skips CPython's normal
GC-driven shutdown path and avoids the crash without touching program
logic, the written receipt, or the exit code contract.

## Reproducing

```
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 run_bridge_validation.py
```

Exit code `0` iff all 9 controls fired as expected, all 3 self-tests fired
as expected, `C9` shows bridge agreement on every gathered case, the
forbidden-surface-token scan is clean, and every `MANIFOLD_ACTION_CATEGORIES`
entry is exercised by at least one control's deck. Exit code `1` otherwise,
with the JSON `findings` list naming exactly which check failed — reported,
never forced. Full receipt: `results/bridge_validation.json`.

## What this does not establish

This package never runs on a real carrier (spinor/QIT density matrix,
classical relation, octonion). It does not compute an `MSS` result, does
not move a frontier, and does not admit anything into
`system_v7/constraint_core/ratchet/ratchet_engine.py`. It establishes only
that, on synthetic toy candidates purpose-built to isolate each property,
the trace->partition bridge machinery (a) merges genuine behavioural ties,
(b) separates genuine behavioural differences including order-sensitivity,
(c) demotes to `HOLD` rather than lying about a thin or biased deck, (d)
catches raw-label/illicit-identity smuggling including through the opaque-
state interface, and (e) produces the same verdict via two independently
implemented decision procedures. That is the precondition this campaign
was scoped to establish before any real carrier is adapted into the
contract — the adaptation itself is future work.
