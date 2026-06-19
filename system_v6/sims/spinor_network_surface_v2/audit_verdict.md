# Independent audit verdict - spinor_network_surface_v2

Bottom line: VERDICT = MECHANICALLY GENUINE SCRATCH PACKET, BUT NO V2 RISE.

`spinor_network_surface_v2` is a real cross-backend working-tree packet: the three
engine lanes regenerate in a temp copy, the envelope rebuilds, the generic
three-engine validator passes, the packet validator passes, pytest reports
8/8 green before this audit file is written, the in-packet Haar count null
recomputes, the rebuilt wrong-row control fires through the real predicate, the
Kraus/Choi ledger is persisted and spot-verifies, and the A33 kinematic ceiling
is correctly 33.

The corrected floor does NOT rise above v1. The claimed load-bearing identity
statistic is not admitted as decisive family-identity evidence because the
"family-tied" target cells are the cells hit by four pinned Haar-random positive
states themselves. The positive predicate treats identity as matched when no
independent required-pair set is supplied, then the null scores those observed
slot-cell pairs. That can be a tail event under the packet's Monte Carlo, but it
is not a predeclared, family-predicted, falsifiable identity comparison for the
surface doctrine. The v1 floor therefore STANDS at the corrected narrower scope;
v2 adds useful repairs, but its rise claim FALLS.

Public repo label: `exists` in the working tree, with fresh validator/test/temp
rerun evidence. Not `canonical by process`; classification remains
`scratch_diagnostic`, `promotion_allowed=false`,
`formal_admission_allowed=false`. The v2 directory is untracked in this checkout.

## Fresh Checks

- Real repo generic validator:
  `PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed --require-tool-intent system_v6/sims/spinor_network_surface_v2/results/spinor_network_surface_v2_envelope_results.json`
  returned `ok=true`.
- Real repo packet validator, no-write post-audit in-process mode:
  `ok=true`, `error_count=0`.
- Real repo pytest before writing this verdict:
  `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=system_v6/sims/spinor_network_surface_v2 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest -q -p no:cacheprovider system_v6/sims/spinor_network_surface_v2/tests`
  returned `8 passed`.
- Temp-copy full regeneration under `/tmp/spinor-v2-audit.fUJRuB`:
  JAX, PyTorch, Julia, envelope, packet validator, generic validator, and pytest
  all completed after copying the validator helper into the temp tree. Regenerated
  engine values matched the packet: recovered=16, load-bearing recovered=11,
  controls=4, spurious=6, A33 ceiling=33, Kraus/Choi witnesses=10,
  Haar scaled expected count=7607.
- Independent null check:
  packet procedure recomputed `E[K_null]=7.60693359375`,
  `std=1.6109036343083065`; an independent NumPy RNG Monte Carlo with 4096
  trials gave `E[K_null]=7.5947265625`, `std=1.6622272812726102`.
- Wrong-row recompute:
  positive verdict `RECOVERY_PASS_NONTRIVIAL`, wrong-row verdict `RECOVERY_FAIL`,
  same `A33_committed_predeclared` classifier id, identity pairs mismatch,
  wrong-row nonorigin count 17.
- Kraus/Choi spot check:
  `target_id=chiral_quaternion_L`, recomputed completeness residual 0.0,
  Choi min eigenvalue `-1.2010633988133176e-16`, Choi trace 1.0,
  partial-trace residual 0.0.

## Per-Correction Adjudication

1. Haar count null: PASS.
   It is a pinned-seed Monte Carlo, not an exact Page-style lemma evaluation.
   The procedure honors the relevant hypotheses for the count reference:
   four independent full 4-qubit complex Haar states per trial, four sites per
   state, same A33 Voronoi classifier, 2048 trials, seed recorded. The reported
   7.607 is real and independently consistent.

2. Identity-based statistic: FAIL AS LOAD-BEARING DOCTRINE EVIDENCE.
   The packet's observed statistic is:
   `observed_family_tied_pair_count=16`, meaning 16 `slot_i:A33_cell` pairs
   hit by the four load-bearing Haar-pinned positive states. Under the packet
   null, pair-count mean is 10.2368, pair-count std is 1.9436, and
   `P(pair_count >= 16)` in the 2048-trial MC is 0.00244. The packet's
   surprisal score is also high: observed 40.3801 vs null mean 18.9342,
   z=4.2942, with no null trial at or above it in 2048 samples.

   Those numbers are statistically interesting only if the four seeds and their
   target cell identities were predeclared independently. In the code they are
   not. The positive path uses the observed family-cell map itself; when
   `identity_required_pairs` is absent, `identity_pairs_match_expected` is set
   true. The wrong-row and off-axis controls then compare against those observed
   positive pairs. That is post hoc identity scoring, not a falsifiable
   family-predicted cell set.

3. Bias-free families: PARTIAL.
   The four load-bearing families are `haar_pinned_seed_6608`,
   `haar_pinned_seed_6609`, `haar_pinned_seed_6610`, and
   `haar_pinned_seed_6611`. They are generated from complex-normal
   pseudo-Haar states with recorded seed hashes, and each reports four
   non-origin cells. This reduces chart-axis bias in the narrow sense that the
   load-bearing positive rows have no preferred chart axis.

   But these rows are samples from the same reference class as the Haar null,
   not structured Hopf/Weyl surface-family predictions. The v1 chiral,
   entangled, and pinned-random families are retained as anchors but explicitly
   not load-bearing. So the bias repair is a statistical-control repair, not an
   earned structured-family surface rise.

4. Rebuilt wrong-row control: PASS WITH DEPENDENCY CAVEAT.
   The control now uses the same A33 machinery with permuted row labels and
   fails through the real recovery predicate by identity-pair mismatch, not by
   a classifier-id string mismatch. This fixes the v1 wrong-row defect. Caveat:
   because the positive identity pair set is post hoc, the control is only as
   strong as that target-set boundary.

5. Kraus/Choi ledger: PASS.
   The ledger persists 10 computed branch witnesses with completeness,
   Choi positivity, trace, and partial-trace residual fields. One witness was
   independently recomputed and matches. Ceiling: these witnesses certify the
   finite piecewise prepare-and-mix channel branches used by the packet, not a
   global Hopfield/QNN theorem.

6. A33 geometric ceiling: PASS AS KINEMATIC CEILING.
   The packet computes all 33 A33 cells as reachable in principle by checking
   positivity and trace of `rho=(I+r.sigma)/2`; the four-site carrier can purify
   any single-qubit rank <= 2 quotient. This is the correct broad single-site
   quotient ceiling. It changes the v1 reading to 6/33 kinematically reachable
   cells, not 6 of a hidden smaller ceiling. V2 reports 16/33 recovered overall
   and 11/33 load-bearing Haar cells, but this is still not a dynamics-matched
   or family-appropriate ceiling.

7. Spurious extension: FAIL.
   The packet re-finds v1's 6/6 equal pair-mixture spurious rows over the four
   v1 anchor patterns. It does not search the Hopfield note's requested
   three-pattern mixtures, and it does not run random initial seeds beyond the
   stored/corrupt/pairmix anchor set. This is the clearest missing v2 research
   requirement.

8. V1 anchors and standard process: PASS WITH CEILINGS.
   The unchanged v1 recovered cell set reproduces exactly:
   `A33_x00_y00_zp10`, `A33_x00_yp5_z00`, `A33_xp10_y00_z00`,
   `A33_xp5_y00_z00`, `A33_xp5_y00_zm5`, `A33_xp5_y00_zp5`.
   SMT flips are non-tautological at finite-count level: z3, cvc5, and Julia Z3
   bind computed counts and flip under the mutated identity-surprisal condition.
   Tool use is honest enough for scratch diagnostics. It is not proof of the
   identity premise.

## Corrected Floor

STANDS vs v1, DOES NOT RISE.

What stands:
- v1's corrected narrow first floor remains citable: family-tied chart-cell
  recovery with count below Haar, real falsifiers, 6 pair-mixture spurious
  attractors, finite transition-graph evidence, and typed non-product rows.
- v2 preserves the v1 anchors and repairs several mechanical weaknesses.

What does not rise:
- v2 does not provide an admitted significant identity statistic for the surface
  doctrine because the identity targets are not independent of the observed
  Haar-pinned positives.
- v2 does not complete the spurious-extension requirement from the Hopfield note.

## Named Caveats

- `UNTRACKED_PACKET`: the v2 packet is present but untracked in this checkout.
- `POST_HOC_IDENTITY_STATISTIC`: positive family-cell identities are observed,
  then scored; no independent required-pair hypothesis is supplied.
- `HAAR_AS_POSITIVE_FAMILY`: the load-bearing rows are Haar-pinned random states,
  not structured Hopf/Weyl family predictions.
- `SEEDS_NOT_PRECOMMITTED_IN_CARD`: seeds and hashes are recorded in results, but
  the build card did not predeclare the specific seed set or predicted cells.
- `NO_THREE_PATTERN_SPURIOUS_SEARCH`: v2 re-finds pair mixtures only.
- `KINEMATIC_CEILING_ONLY`: A33=33 is the full single-site quotient ceiling, not
  a dynamics-specific reachable-set ceiling.
- `FINITE_COUNT_SMT_ONLY`: solver flips bind finite packet counts, not global
  basin or surface semantics.
- `ALGORITHM_MIRROR_BACKENDS`: Julia/JAX/PyTorch independently implement the same
  algorithm; this is cross-runtime recomputation, not independent mathematics.
- `POST_AUDIT_PYTEST_BOUNDARY`: the pytest suite contains a builder-phase
  assertion that `audit_verdict.md` is absent, so the 8-passed result is the
  correct pre-audit test. After this allowed audit write, that exact test is not
  a post-audit validator.

## Future-Citation Rule

Allowed citation:

`spinor_network_surface_v2` is an untracked, all-three-engine
`scratch_diagnostic` packet that mechanically repairs several v1 defects:
in-packet Haar count null `E[K]=7.6069`, structure-sensitive wrong-row control,
persisted Kraus/Choi witness ledger, A33 kinematic ceiling of 33, v1 anchor
reproduction, and validator/pytest/temp-rerun green evidence. It does not raise
the corrected surface floor because its load-bearing identity statistic is
post hoc over pinned Haar-random positives and the three-pattern/random-seed
spurious extension is absent.

Forbidden citations:

- "v2 proves significant family-tied identity against the Haar null";
- "v2 proves bias-free structured Hopf/Weyl recovery";
- "v2 completes the Hopfield spurious-attractor extension";
- "v2 gives full A33 recovery";
- "v2 is canonical by process";
- "v2 admits the spinor network surface beyond scratch diagnostic strength".

## Block K

Gates cited: authority docs; owner doctrine entries f3d3ad1c1, 16f4434f6,
28fc221a1; v1 build/audit/results; Haar and Hopfield research notes; generic
three-engine validator; packet validator; pytest; temp-copy engine regeneration;
independent null, wrong-row, and Kraus/Choi recomputes.

Admission decisions: Haar count null admitted; wrong-row repair admitted;
Kraus/Choi ledger admitted; A33 kinematic ceiling admitted; v1 anchors admitted;
identity-statistic rise blocked; spurious extension blocked; canonical/process
promotion blocked.

Narrative substitutions intercepted: "identity above null" was not allowed to
stand without an independent predicted cell set; "axis-unbiased Haar positives"
was not allowed to become "structured-family surface evidence"; "six spurious
rows" was not allowed to imply three-pattern/random-seed coverage.

Worker claims verified: no external worker claims were accepted as evidence in
this audit. Codex-native subagents were not spawned because the available
subagent tool contract only permits spawning on explicit user request for
delegation/subagents; the Wizard route is therefore partial.

Status label changes to registry: none.

Blocked actions: no git add/commit; no edits outside this audit verdict.
