# Independent Audit Verdict - gcm_ratchet_order_matrix_v1

Audit mode: read-only audit / fresh audit. Write scope: this file only. No git
add/commit. I did not run the packet writer, pytest, or the packet validator CLI
because those commands rewrite result artifacts. I used in-memory recomputation
and read-only helper CLI checks instead.

## Bottom Line

VERDICT: GENUINE-WITH-CAVEATS.

The core v1 matrix survives audit as a scratch diagnostic: the full Part-C
alphabet is present as `S/Q/W/F/T/O/D`, the result covers 49 ordered rows, the
matrix recomputes exactly from source in memory, the v0 20 off-diagonal rows are
reproduced, and the measured counts are `SELF=7`, `COMMUTE=2`,
`DIRECTIONAL=12`, `NOT_COMPARABLE=28`. The six unique forced edges recompute:
`S->W`, `S->F`, `S->T`, `S->D`, `Q->O`, and `Q->D`.

The stronger builder language does not fully survive. The current worktree
`scripts/gcm_substrate_check.py` hash does not match the helper hash pinned in
the result JSON, and two of the 13 controls are still too weak to cite as fully
genuine C6 controls: `label_shuffle` is row-reversal/status-multiset invariance,
not a semantic label shuffle, and `local_only_replacement` is a source-hash
refusal, not an executed replacement route.

Accepted claim ceiling: `scratch_diagnostic`,
`full_part_c_alphabet_1q_carrier_and_pins_relative`,
`promotion_allowed=false`, `formal_admission_allowed=false`. It is not a global
ratchet sequence theorem, not a formal proof, not manifold/physics admission,
not true StageRegion operator residency, and not a 2Q order matrix.

Citation rule: cite this only as "a scratch diagnostic full-alphabet GCM order
matrix that recomputed 49 pair rows on the frozen 1Q carrier, reproduced v0, and
found six unique forced edges with strict two-step typing caveats." Future
citations must co-cite this audit file and
`results/gcm_ratchet_order_matrix_v1_results.json`; they must not cite it as
strict-green C6-complete, canonical, admitted, global, or current-helper-pinned
unless the helper pin is refreshed and the weak controls are replaced.

## What I Checked

Fresh direct checks:

- `git status --short`: v1 is untracked; `scripts/gcm_substrate_check.py` is
  modified.
- In-memory recomputation with
  `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3`.
- `validate_payload(payload)`: `[]`.
- `boundary_errors(payload)`: `[]`.
- `compute_matrix(load_context(), step_registry()) == payload["pairwise_matrix"]`:
  `True`.
- `all_controls_pass_current`: `True` under the current helper and current
  source.
- Read-only helper CLI:
  - positive result JSON returned rc `0`, `ok=true`;
  - lineage-free negative returned rc `1`, `ok=false`;
  - wrong-substrate negative returned rc `1`, `ok=false`.

I did not run `validate_gcm_ratchet_order_matrix_v1.py` or pytest because both
can rewrite `results/gcm_ratchet_order_matrix_v1_validator_results.json`, which
is outside the requested write scope.

## Matrix Recompute

The packet source computes the pair status by running both two-step composites
from the same initial state and classifying exact final signatures, survivor
sets, witness sets, or mortality. The relevant implementation is
`classify_pair()` and `compute_matrix()` in
`gcm_ratchet_order_matrix_v1_common.py`.

Recomputed status counts:

```text
SELF_PAIR: 7
COMMUTES_ORDER_FREE: 2
DIRECTIONAL_ENABLE: 12
NOT_COMPARABLE: 28
```

No `NONCOMMUTES_NUMERIC` rows were found. The measured order DAG is acyclic by
both `networkx` and `rustworkx` in the result.

The v0 regression claim holds. `v0_regression.checked_ordered_pair_count` is 20,
`reproduced` is `true`, and `mismatches` is empty. The v0 anchors remain:
`SHELL_PI_OVER_4 -> BRICKWORK_AB`, `SHELL_PI_OVER_4 -> FLUX_HOLONOMY_LOCK`,
`PHASE_DENSITY_QUOTIENT -> CHANNEL_DZ_RX`, with shell/quotient still exact null.

## Forced Edges

All six unique new/full-alphabet forced edges recomputed with the claimed
direction:

- `SHELL_LEAF_CONDITIONING -> LOCAL_WINDOW_SUPPORT_RESTRICTION`: reverse dies
  because local window support needs `occupied_T_eta_stratum`.
- `SHELL_LEAF_CONDITIONING -> FLUX_HOLONOMY_LOCK`: reverse dies because flux
  locking needs shell-conditioned strip values.
- `SHELL_LEAF_CONDITIONING -> TERRAIN_CONDITIONING`: reverse dies because the
  terrain row is consumed only after a shell-conditioned survivor slice exists.
- `SHELL_LEAF_CONDITIONING -> DEPTH_LADDER_CLIMB`: reverse dies with
  `depth_mismatch_after_climb`; the 1Q shell row cannot be applied after the
  packet has climbed to its 2Q cross-rung embedding state.
- `QUOTIENT_LENS_EQUIVALENCE -> OPERATOR_RESIDENCY_PRECEDENCE`: reverse dies
  because O is typed on phase/density quotient readouts.
- `QUOTIENT_LENS_EQUIVALENCE -> DEPTH_LADDER_CLIMB`: reverse dies with
  `depth_mismatch_after_climb`; the 1Q quotient row cannot be applied after D.

`S/Q` and `Q/S` both recompute as exact `COMMUTES_ORDER_FREE` with numeric gap
`0`.

## NOT_COMPARABLE Honesty

The sampled `NOT_COMPARABLE` rows are honest under v1's strict two-step matrix
typing:

- `Q,W`: both orders fail on missing `occupied_T_eta_stratum`.
- `W,D`: one side needs `occupied_T_eta_stratum`, the other side reaches a 2Q
  state where the 1Q W row is not defined.
- `O,D`: one side needs `phase_density_quotient`, the other side reaches a 2Q
  state where the 1Q O row is not defined.
- `T,F`: both orders fail before a shell-conditioned survivor slice exists.

This is correct-strict for the two-step matrix, but not the end of the research
space. Natural v2 rows should add prefix/adapted contexts rather than weakening
v1:

- `S + Q/W` to test whether quotient and local window commute after shell
  conditioning.
- `S + T/F` to test terrain versus flux after an occupied shell exists.
- `S + W/D`, `S + F/D`, and `S + T/D` to test whether post-shell 1Q refinements
  can be lifted through a 2Q-adapted version of W/F/T rather than killed by the
  current 1Q-only row typing.

These are v2 comparability rows, not v1 errors.

## Blocked Components

The `blocked_no_realization` handling is consistent with the repo state. The
packet explicitly records true StageRegion operator residency as blocked, and O
is only channel-application typing. That matches
`system_v6/receipts/truestate_map_codex2_20260612.md`, which says resident
stage regions are `0/16` admitted, and
`system_v6/sims/engine_16_stage_correspondence_v1/audit_verdict.md`, which
confirms `0/16` exact component matches for the current correspondence test.

Therefore O is admissible only as `channel_application_typing_only` with
`true_stage_region_residency=blocked_no_realization`.

## Controls

I reran the controls path in memory and sampled helper CLI positives/negatives.
The following are genuinely biting enough for the v1 ceiling:

- reversed order;
- quotient erasure;
- missing-layer failure;
- wrong-substrate lineage;
- commuting-pair zero control;
- mortality replay;
- depth-ladder cross-rung embedding;
- entropy readout ablation;
- lineage-free negative;
- terrain-conditioning source hash;
- StageRegion residency blocked-no-realization.

Two controls should not be cited as full C6 fixes:

- `label_shuffle`: the implementation compares a sorted status-key multiset
  against the same rows reversed. This tests row-order invariance, not a real
  label permutation through the step semantics.
- `local_only_replacement`: the implementation checks that a source hash exists
  and is not the literal string `local_only_uncommitted_replacement`. That is a
  hash refusal, not an executed local replacement route.

So v1 improves the v0 declarative-controls problem, but it is not
strict-green/full-C6-complete.

## Depth Step D

D is meaningful at the stated ceiling. It consumes the committed 1Q-to-2Q
cross-rung product embedding from
`gcm_constraint_carve_2q_v0/results/gcm_constraint_carve_2q_v0_results.json`,
where `product_control_embedding_count=16`,
`product_control_embedding_all_survive=true`, and
`partial_trace_A_image_equals_1q_survivor_set=true`.

The phrase "shell before depth" means: apply 1Q shell conditioning while the
state is still a 1Q carved state, then climb to the cross-rung 2Q product
embedding. The reverse order fails because the v1 packet has no 2Q-adapted shell
row. The computation says exactly that:

- `S -> D` lives, reaches `2Q_cross_rung_product_embedding`, and keeps 4
  shell-selected survivors.
- `D -> S` dies with `depth_mismatch_after_climb` and missing
  `1Q_carved_state`.

Caveat: D remains a cross-rung embedding step only, not a 2Q order-matrix
closure. The depth readout still reports the full 16-row product embedding even
when a prior 1Q filter has reduced the survivor set, so v2 should make
post-filter 2Q image counts row-local.

## Helper Pin And Substrate

Substrate behavior is green/red/wrong-red under the current helper:

- positive payload: `ok=true`;
- lineage-free negative: `ok=false`;
- wrong-substrate negative: `ok=false`.

But the helper pin is stale relative to the current worktree:

```text
pinned helper sha256: 8b22bb90384cbfab07b08b4c9d0a9ca162e9211bca1bdb90c46673ffb4a25610
current helper sha256: 855cc579487bc6b5b77af3245012bdeb7d6e44c32730b57fe709de9d03f66ddf
pinned git blob: b85679c81074f8368ef928ced4890846d6722df7
current git blob: e25700eb24e927ea463324b3b1f8932b3ab6aaac
```

This does not kill the matrix, because the helper still validates the payload
and rejects both negatives. It does kill the claim that the result is pinned to
the current runnable helper version.

## G.2a And Coordinates

G.2a boundary checks are green in memory: `boundary_errors(payload)` returned
`[]`, and this file is an independent audit surface. Row-local coordinates are
present for all seven steps, with `geometric_layer`, `nesting_state`, and
`qubit_depth`. The D row is correctly labeled as the qubit-ladder vertical
dimension and still bounded to a 1Q-to-2Q cross-rung embedding step.

## Final Classification

Keep:

- full-alphabet 49-row scratch diagnostic;
- six unique forced edges;
- exact S/Q null;
- v0 20-row regression reproduction;
- substrate positive and negative behavior under current helper;
- StageRegion residency blocked-no-realization honesty.

Audit further:

- helper pin drift;
- label-shuffle and local-only-replacement controls;
- row-local 2Q image counts after prior 1Q filters;
- v2 prefix/adapted comparability rows for the strict `NOT_COMPARABLE` set.

Demote / do not cite:

- strict-green C6-complete;
- current-helper-pinned;
- true operator residency;
- 2Q order matrix;
- global ratchet order theorem;
- canonical/admitted/manifold/physics claim.
