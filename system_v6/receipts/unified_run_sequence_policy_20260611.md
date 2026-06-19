# Unified-run sequence and seed policy - 2026-06-11

Status: derivation-only receipt. No sims are authorized or run by this receipt.

Purpose: close the premortem's second precondition for extending `manifold_unified_run_v0`: sequence and seed choices must be pre-declared before any unified-run extension results are generated, so extension rows cannot be cherry-picked after seeing outcomes.

## Source anchors

- `6903e0388` - committed `manifold_unified_run_v0`; first bounded unified run over one n=3 seed, one persisted trajectory, one sequence, scratch ceiling.
- `187e96bdd` - committed `ratchet_order_breadth_v0` fix-2; final order-blind sequence convention for the committed four-symbol ratchet alphabet.
- `e2ca51b02` - pre-registered entropy and rigidity expectations: exact entropy anchors, pure-addition monotonicity, and quotient/projection irreversibility.
- `cdf437053` - committed `mct_dynamic_deformation_v0` parent consumed by the unified run for deformation-mode ledger semantics.
- `a54224476` - committed `manifold_entropy_ledger_v0` parent consumed by the unified run for entropy-ledger convention.
- `1b36e4a3c` - committed n=3 terrain/spinor/flux seed parent consumed by the unified run.

## 1. Sequence Family

Committed alphabet:

| token | constraint |
|---|---|
| `L` | `leaf-conditioning` |
| `Z` | `lens quotients` / `Z4_phase_lens` |
| `W` | `phase windows` / descended phase window |
| `T` | `terrain restrictions` / `terrain_restriction_Se_Funnel_L` |

Family rule, not a hand-picked list:

`F_<=3` is every ordered sequence of length 1, 2, or 3 over `{L,Z,W,T}` with no repeated token, accepted by the committed order-breadth fences:

- `W` requires a prior `L`; otherwise it is `M1_phase_without_leaf`.
- `T` requires a prior `L`; otherwise it is `M2_terrain_without_leaf`.
- `Z` after a raw pre-quotient `W` is inadmissible; that is `M3_raw_window_then_Z4`.
- Repeated-token sequences are excluded until a separate idempotence/reapplication fence is committed. The current committed order-breadth packet is a fixed multiset/order diagnostic, not a repetition diagnostic.

Explicit enumeration: `|F_<=3| = 13`.

Length 1:

1. `L` = `leaf-conditioning`
2. `Z` = `lens quotients`

Length 2:

3. `LZ` = `leaf-conditioning -> lens quotients`
4. `LW` = `leaf-conditioning -> phase windows`
5. `LT` = `leaf-conditioning -> terrain restrictions`
6. `ZL` = `lens quotients -> leaf-conditioning`

Length 3:

7. `LZW` = `leaf-conditioning -> lens quotients -> phase windows`
8. `LZT` = `leaf-conditioning -> lens quotients -> terrain restrictions`
9. `LWT` = `leaf-conditioning -> phase windows -> terrain restrictions`
10. `LTZ` = `leaf-conditioning -> terrain restrictions -> lens quotients`
11. `LTW` = `leaf-conditioning -> terrain restrictions -> phase windows`
12. `ZLW` = `lens quotients -> leaf-conditioning -> phase windows`
13. `ZLT` = `lens quotients -> leaf-conditioning -> terrain restrictions`

This family is a prefix-safe extension surface for unified runs. The committed full-four-symbol order-breadth packet remains the authority for all length-4 permutations and reports the 24-ordering table separately; this policy does not re-run or replace that packet.

## 2. Selection Rule For Extension Wave 1

Deterministic order for family members: sort by `(length, token_string)` using token order `L < Z < W < T`.

Extension wave 1 runs the union of:

1. the committed unified-run baseline sequence `LZT`;
2. the lexicographic first six members of `F_<=3`: `L`, `Z`, `LZ`, `LW`, `LT`, `ZL`;
3. every admissible member of `F_<=3` containing both the known noncommuting `Z/W` pair: `LZW`, `ZLW`.

Therefore wave 1 sequence set is fixed before extension:

`{L, Z, LZ, LW, LT, ZL, LZW, LZT, ZLW}`.

Wave 1 size: `9` sequences.

Coverage justification:

- `LZT` is the committed unified-run baseline from `6903e0388`, so the extension remains comparable to the existing trajectory.
- The first six deterministic prefixes cover each single admissible generator and all admissible two-step prefixes before length-3 outcomes are inspected.
- `LZW` and `ZLW` force the known `Z/W` noncommutation surface into the first wave. The committed order-breadth anchor names `LZWT` as alive and `LWZT` as `M3_raw_window_then_Z4`; in the prefix family, `LZW` and `ZLW` are the admissible length-3 probes carrying that pair.
- The deferred admissible members are not killed or hidden: `LWT`, `LTZ`, `LTW`, and `ZLT` stay in `F_<=3` for later waves under the same deterministic order.

No result-dependent substitution is allowed. If a wave-1 sequence is too expensive or blocked, write a blocked row for that exact sequence; do not replace it with a cheaper neighbor.

## 3. Seed Policy

Committed n=3 seed:

- source: `manifold_unified_run_v0`, commit `6903e0388`;
- `seed = 2026061104`;
- `state_object_id = b3f17fa7b1294471d51e917da05219c1b6431908a33e7a4bb05b99af879ac1fd`;
- parent seed source: `terrain_spinor_flux_nest_n3_v0`, commit hint `1b36e4a3c`;
- cost class: `n=3 unified = normal-local`.

Committed n=4 seed:

- seed token: `c36a80f6b`;
- role: pre-declared n=4 unified extension seed;
- cost class: `n=4 unified = heavy-local`;
- resource guard: n=4 unified rows must be routed through the local resource guard before execution. If the guard is red, emit a blocked resource row rather than silently shrinking or swapping the seed.

Per-seed comparison rows:

For every selected sequence and seed, compare the following rows against the same sequence on the other seed and against the baseline `LZT` on the same seed:

| row | compare across seeds | compare to same-seed `LZT` |
|---|---|---|
| `cross_layer_consistency_matrix` by typed row class | pass/finding counts, row-class identities, unexplained disagreements | which cells newly fail, hold, or become not-applicable |
| `s2_holonomy_spectrum_change` | changed flag, changed step, pre/lens/post values | whether the lens step remains the first holonomy-spectrum change |
| `row_family_step_classification` | step-dependent/invariant family names and reasons | whether each selected sequence preserves justified carried rows |
| `deformation_mode` ledger | per-step `BASELINE`, `COMPRESSION`, `WARP`, or explicit blocked/unsupported | whether `WARP` remains tied to quotient/readout, and compression remains tied to conditioning/restriction |
| entropy ledger rows | exact symbolic identity, quotient-count drop, chain-rule defect | whether entropy changes match the active constraint order |
| per-layer erasure controls | fired/not-fired and solver polarity where present | whether controls fail where the selected sequence removes their precondition |

Comparison is row-local. No aggregate trend, scaling, manifold admission, bridge/axis, or `M(C,t)` theorem is earned by matching across n=3/n=4.

## 4. Pre-registered Expectations By Sequence Class

Sequence classes:

- `seed-only`: `L`, `Z`;
- `two-step admissible`: `LZ`, `LW`, `LT`, `ZL`;
- `lens-window class`: `LZW`, `ZLW`;
- `baseline unified class`: `LZT`;
- deferred admissible class: `LWT`, `LTZ`, `LTW`, `ZLT`.

Cross-layer matrix expectations:

- Every executed row must remain typed by row class, not flattened into one tolerance.
- For `LZT`, the n=3 matrix should retain the committed zero-unexplained-disagreement pattern from `6903e0388`.
- For prefixes that omit a layer precondition, rows depending on the omitted constraint must become `not_applicable` or `blocked_by_missing_precondition`, not be carried as if the full sequence ran.
- For `LZW` and `ZLW`, window/quotient ordering must appear as a real row difference, not be normalized away unless the committed order-blind signature explicitly permits that row.

Holonomy-spectrum expectations:

- Any sequence containing `Z` should expose the lens quotient as the holonomy-spectrum change point for `s2_geometry`, matching the committed n=3 pattern where the lens step changes q0 primitive holonomy from `-4.442882938156` to `-1.110720734539`.
- Sequences without `Z` should not claim the lens holonomy-spectrum change. If a spectrum changes anyway, that is either a new sequence-specific mechanism or a machinery defect; it must be isolated before any extension claim is accepted.

Deformation-mode expectations:

Use the committed `mct_dynamic_deformation_v0` semantics:

- baseline seed row: `BASELINE`;
- leaf-conditioning / constraint addition: `COMPRESSION`;
- lens quotient / quotient readout: `WARP`;
- terrain restriction / no-expansion-without-release row: `COMPRESSION`;
- any pure-addition row that expands is forbidden by the pre-registered monotonicity expectation from `e2ca51b02`;
- any erased quotient distinction that is recovered without a phase-refined control is forbidden by the quotient/projection expectation from `e2ca51b02`.

Row-family classification expectations:

- Step-dependent families: `s2_geometry`, `s5_s6_terrain_flow`, `flux_continuity`, `entropy_ledger_row`, `deformation_mode`.
- Step-invariant families when their conditioned object is unchanged: `s3_density_probe`, `spinor_signed_rows`, `s5_s6_leakage_rows`, `s6_taxonomy`.
- A sequence may demote a family to `not_applicable` if its precondition is absent; it may not silently keep a stale row as if recomputed.

## 5. Falsifiable Failure Conditions

These outcomes indict the unified machinery itself, not merely one scientific conjecture:

1. Same `(sequence, seed)` produces multiple `state_object_id` values across layers without an explicit, audited reason.
2. A selected sequence is replaced after results are known, or a blocked row is omitted instead of recorded.
3. A prefix omits a precondition but downstream rows are still reported as if the missing constraint had run.
4. A `Z` sequence fails to localize holonomy-spectrum change to the lens step, and the discrepancy is not explained by a declared sequence-specific row.
5. A non-`Z` sequence reports the committed lens holonomy-spectrum change.
6. A pure-addition/conditioning step expands the admissible set without a release/relax/coarsen row.
7. A quotient-erased phase distinction is recovered without a phase-refined control row.
8. The `row_family_step_classification` says a family is step-dependent but the emitted payload is byte-identical after stripping lineage-only fields, or says invariant while the mathematical object changed.
9. n=3 `LZT` no longer reproduces the committed baseline rows from `6903e0388` under the same source and seed policy.
10. n=4 rows run despite a red heavy-local resource guard, or are silently downsampled while still labeled as the committed `c36a80f6b` seed.

If any failure fires, stop unified-run extension claims at `exists/runs` for the affected rows, write the failure as a receipt, and do not promote, aggregate, or use the row as evidence for a manifold, bridge/axis, or `M(C,t)` claim.
