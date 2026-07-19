# Build card: v8 deep-layer manifold (dispatched to codex1, 2026-07-18)

## Goal
Extend `system_v8/manifold/` so the WHOLE manifold runs as one settled
object, down through the deeper layers, under the same executable law the
existing lane uses: propose -> settle(Z + delta) -> compare by witness ->
retain plural frontier -> Purgatory with re-offer.

## Scope (build exactly these, in this order)
New engine modules in `system_v8/manifold/engine/`, each following the
existing pattern (argparse --source/--prior/--output, JSON receipt with
`checks`, `all_pass`, `claim_ceiling`, `result_digest`):

1. `connection_layer.py` — transport between nested layers. Candidates (>=3
   incl. a default): identity transport, parity/sign transport derived from
   `inputs/finite_algebra.py::spinor_memory_report` (density/sign structure),
   permutation transport from the QCA transition tables. Requirement: a
   transported inner state must remain admissible in the outer layer;
   witness = concrete violating (state, transport) pair.
2. `history_layer.py` — ordered relation chains (R2). Candidates: unordered
   set baseline, sequence histories, branching (tree) histories. MUST test
   order: apply transported restrictions in both orders; noncommutation is
   EARNED only if a concrete pair of states distinguishes T2.T1 from T1.T2
   — record the witness pair or `noncommutation_earned: false`.
3. `persistence_layer.py` — R3: which derived distinctions survive every
   allowed history in the current frontier; emits surviving-distinction
   inventory per candidate manifold.
4. `chirality_layer.py` — installed-not-forced discriminator: from
   `finite_algebra.py::octonion_network_report` bracketing (left vs mixed),
   test whether an orientation distinction is (a) expressible, (b) forced,
   (c) merely installable. Record which. Do NOT force it.
5. `whole_manifold_v2.py` — re-run the FULL feedback tournament with the new
   layers in the grammar: every candidate = (base x nesting x geometry x
   connection x history). Settle the complete object, re-offer ALL bases,
   nestings, geometries after each new layer arrives (same revival law that
   readmitted classical_distribution). Plural frontier; no terminal claim.
6. `verify_deep.py` — extends verify_active_results_v8 pattern: semantic
   checks over every new receipt + at least 12 new adversarial mutations
   (each must be rejected); pin schema strings and packet count 9.
7. `deterministic_replay_deep.py` — double in-process replay of the whole
   deep pipeline; digests must match archived results.
8. `RUN_DEEP.sh` at `system_v8/manifold/` — runs 1-7 in order into
   `system_v8/manifold/results/deep/`; exits nonzero on any failure.

## Hard constraints
- Python stdlib only, deterministic (no time, no randomness without fixed
  seed recorded in the receipt).
- Inputs ONLY from: `system_v8/manifold/results/source_packets.json` (9
  packets), vendored `system_v8/manifold/inputs/*` modules, and the existing
  results JSONs. No network, no new external data.
- DO NOT delete, move, or rewrite ANY existing file. New files only, except
  nothing — zero edits to existing files.
- Entropy/geometry stays a LATE layer readout; no probability primitives at
  base; the drive/gradient framing is not asserted as physics.
- Every receipt carries: `promotion_allowed: false`,
  `formal_admission_allowed: false`, packet-relative claim ceiling.
- No candidate called final; beaten candidates go to a Purgatory list with
  a concrete witness and a re-offer rule.
- Language: survived/admitted/excluded/coupled-with; never causes/creates/
  drives/produces.

## Acceptance (all must hold; checked by fresh rerun)
- `bash system_v8/manifold/RUN_DEEP.sh` exits 0 on a fresh run.
- Every stage prints a one-line JSON summary with `all_pass: true`.
- Noncommutation status is COMPUTED with a witness or an explicit negative.
- The deep frontier is plural or a written justification cites the exact
  witnesses that collapsed it.
- Double replay digests match.
- `git status` shows only ADDED files under system_v8/manifold/.

## Deliverable
Working code + receipts in results/deep/ + a `DEEP_RESULTS.md` (<=60 lines)
stating: what ran, the deep frontier, noncommutation status, chirality
status (expressible/forced/installable), open caveats. No process narration.
