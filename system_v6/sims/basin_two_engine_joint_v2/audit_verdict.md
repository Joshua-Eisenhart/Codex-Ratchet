# Fresh Cross-Backend Audit Verdict - basin_two_engine_joint_v2

Auditor: independent Codex audit of codex1 builder packet.
Scope: read-only audit except this verdict file. No `git add` or commit.
Standard: basin contract `system_v6/receipts/attractor_basin_criterion_20260611.md`, amended prediction registration `system_v6/receipts/owner_prediction_64_subsubbasins_20260611.md`, and v0 kill verdict `system_v6/sims/basin_two_engine_joint_v0/audit_verdict.md`.

## Bottom Line

VERDICT: GENUINE-WITH-CAVEATS.

Named caveats:

- G1: Realization-relative. The four-substage transition law is explicitly `underdetermined_by_committed_sources`; v2 pins a cyclic convention for this packet, but that convention is not source-admitted.
- G2: Cross-engine scope. Julia independently recomputes the primary row counts with Graphs.jl/Z3.jl. JAX and PyTorch have real tool checks, but their full lattice payload comes through the shared Python common module, so the full quotient lattice is not three fully independent implementations.

The reported `discovery_result = no_primary_64_terminal_level` is genuine for the v2 realization. The design did not repeat the v0 failure of manufacturing 64 as state identity or marginal partition intersection. It gave 64 a fair chance as a terminal/SCC count over the 1024 fine-state joint object and over natural quotient rows, then found zero primary 64 levels.

Prediction-adjudication sentence:

`The pre-registered 64 = 2 engines x 2 loops x 4 stages x 4 substages prediction is unconfirmed under the basin_two_engine_joint_v2 cyclic-substage realization: v2 genuinely finds no source-backed primary 64 terminal/SCC level from the 1024-state joint dynamics, but the prediction remains open pending a source-pinned four-substage transition convention.`

Future-citation rule:

`Cite basin_two_engine_joint_v2 only as realization-relative negative evidence under the declared cyclic-substage convention; do not cite it as a canonical disproof of the owner prediction, and do not cite any class as a basin/subbasin/subsubbasin unless the citation includes the exact generator row plus terminal closure/no-exit or escape evidence.`

## What Was Checked

- Read the basin criterion, owner prediction registration, v0 audit verdict, v2 build card, all v2 sources, engine result summaries, validator result, and envelope result.
- Recomputed v2 row and quotient counts in-memory from `basin_two_engine_joint_v2_common.py` using `PYTHONDONTWRITEBYTECODE=1` and the Makefile sim-stack Python.
- Ran the generic validators:
  - `scripts/validate_three_engine_sim_result.py --require-pytorch --require-source-backed system_v6/sims/basin_two_engine_joint_v2/results/basin_two_engine_joint_v2_envelope_results.json`
  - `scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed system_v6/sims/basin_two_engine_joint_v2/results/basin_two_engine_joint_v2_envelope_results.json`
- Both validators returned `{"ok": true, "result_json": "system_v6/sims/basin_two_engine_joint_v2/results/basin_two_engine_joint_v2_envelope_results.json"}`.

## Adjudication

1. No primary 64 terminal level is genuine for this realization.

The build card requires 64 to be discovered from the `32 x 32 = 1024` state object, not accepted as a state count or partition intersection. It also requires SCCs, terminal closed classes, absent-exit proofs, may/must rows, and Morse edges for every row.

The source builds explicit source-backed and conditioned generator rows:

```text
source_sync_full_tick
source_l_only_full_tick
source_r_only_full_tick
source_async_lr_union_full_tick
source_all_interleavings_full_tick
conditioned_sync_loop_advance
conditioned_sync_stage_progression
conditioned_sync_substage_cycling
conditioned_sync_coordinate_generators
conditioned_async_coordinate_generators
```

Fresh recomputation of primary terminal counts:

```text
source_sync_full_tick                    32 classes, size 32
source_l_only_full_tick                  32 classes, size 32
source_r_only_full_tick                  32 classes, size 32
source_async_lr_union_full_tick           1 class,  size 1024
source_all_interleavings_full_tick        1 class,  size 1024
conditioned_sync_loop_advance           512 classes, size 2
conditioned_sync_stage_progression       256 classes, size 4
conditioned_sync_substage_cycling        256 classes, size 4
conditioned_sync_coordinate_generators    32 classes, size 32
conditioned_async_coordinate_generators    1 class,  size 1024
```

Fresh recomputation of natural quotient terminal counts:

```text
loop_stage_pair:  1, 8, 8, 1, 1
loop_pair:        1, 2, 2, 1, 1
stage_pair:       1, 4, 4, 1, 1
substage_pair:    4, 4, 4, 1, 1
phase_offset:    32, 1, 1, 1, 1
```

No primary row and no natural quotient row has terminal count 64. The z3/cvc5 proof row checks the measured primary counts and flips to SAT when a synthetic erased 64 is appended, so the no-64 proof is bound to the measured count list rather than only to a hardcoded boolean.

The main design caveat is not by-construction exclusion of 64. It is realization scope: the cyclic substage convention determines the 32-state per-engine cycle. A different source-pinned substage transition law could change the terminal lattice.

2. The v1 replication control is correctly held as by-construction.

The v0 verdict killed the previous packet because the 64 layer was singleton state identity from intersecting L-only and R-only partitions on a 64-state carrier. V2 reproduces the coarse 8x8 intersection only in `controls.v1_replication`, labels it `by_construction_baseline`, sets `accepted_as_primary_evidence=false`, and explains that marginal component intersection is not a transition relation.

That control is therefore correctly demoted. It proves the old artifact can still be reproduced; it does not count toward primary evidence.

3. The prediction is not canonically falsified.

The owner registration says the primary candidate is specifically the product `2 x 2 x 4 x 4`, and that the honest test result should be reported rather than forced to 64. V2 reports no primary 64, but also reports `substage_convention.source_status = underdetermined_by_committed_sources`.

So the right adjudication is not "the owner prediction is false." It is: unconfirmed under this realization, still open pending a source-pinned substage convention.

4. What the dynamics earned.

Earned, row-relative statements:

- `source_sync_full_tick`: 32 row-relative terminal closed communicating classes / Morse classes. These are the 32 fine offset classes of two coupled 32-cycles. Each class is terminal under the sync full-tick row with absent-exit proof.
- `source_l_only_full_tick`: 32 row-relative terminal closed communicating classes, exposing held R-state invariants under L-only full tick.
- `source_r_only_full_tick`: 32 row-relative terminal closed communicating classes, exposing held L-state invariants under R-only full tick.
- `source_async_lr_union_full_tick` and `source_all_interleavings_full_tick`: one terminal closed communicating class of size 1024. Under these generator rows the fine carrier is one communicating component, not a 64 split.
- `conditioned_sync_loop_advance`: 512 row-relative terminal closed classes of size 2.
- `conditioned_sync_stage_progression` and `conditioned_sync_substage_cycling`: 256 row-relative terminal closed classes of size 4.
- `conditioned_sync_coordinate_generators`: 32 row-relative terminal closed classes of size 32.
- `conditioned_async_coordinate_generators`: one terminal closed class of size 1024.

Do not cite these as canonical basins without the row label. The correct vocabulary is terminal closed SCC / invariant Morse class / row-relative sure omega class. "Basin" language is only admissible when tied to the specific row and its terminal closure/no-exit evidence. There is no global 64-subsubbasin object here.

5. Standard checks.

Pass:

- Schema is `three_engine_sim_result_v1`; mode is a field, not a schema fork.
- Envelope classification and ceilings are `scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`.
- JAX, Julia, and PyTorch all report `primary_64_level_count=0` and control terminal count 64.
- Julia independently recomputes the decisive primary row counts with Graphs.jl and Z3.jl.
- The dissipative reset control fires: it merges below 1024 and produces 64 terminal singletons, but is explicitly `accepted_as_primary_evidence=false`.
- Label permutation, root-off, decode, v1-replication, z3/cvc5 erased-flip, and generic three-engine validators pass.
- Tool manifests and tool integration depths are present, with load-bearing graph/proof tools named.

Caveat:

- JAX and PyTorch are not full independent reimplementations of every lattice and quotient row. They use the shared Python payload for full lattice contents, while adding JAX/networkx and PyTorch/torch_geometric/torch.func checks around the decisive sync/full-tick and proof surfaces. This is acceptable for `GENUINE-WITH-CAVEATS`, not for a stronger fully independent three-implementation claim.

## Source Anchors

- Prediction product and product-standard requirement: `system_v6/receipts/owner_prediction_64_subsubbasins_20260611.md:11-21`.
- Honest test and falsifier: `system_v6/receipts/owner_prediction_64_subsubbasins_20260611.md:28-36`.
- Basin finite-lattice method and recompute-not-name rule: `system_v6/receipts/attractor_basin_criterion_20260611.md:175-205`.
- V0 kill: `system_v6/sims/basin_two_engine_joint_v0/audit_verdict.md:9-24`.
- V2 state object, underdetermined substage convention, rows, discovery rule, controls, and tools: `system_v6/sims/basin_two_engine_joint_v2/build_card.md:14-52`.
- Generator rows: `system_v6/sims/basin_two_engine_joint_v2/basin_two_engine_joint_v2_common.py:93-141`.
- SCC, terminal closure, absent-exit, may/must, and Morse computation: `system_v6/sims/basin_two_engine_joint_v2/basin_two_engine_joint_v2_common.py:369-470`.
- Natural quotient construction: `system_v6/sims/basin_two_engine_joint_v2/basin_two_engine_joint_v2_common.py:503-586`.
- No-primary-64 summary logic: `system_v6/sims/basin_two_engine_joint_v2/basin_two_engine_joint_v2_common.py:608-636`.
- V1 baseline demotion and reset control: `system_v6/sims/basin_two_engine_joint_v2/basin_two_engine_joint_v2_common.py:689-725`.
- Substage convention and prediction adjudication fields: `system_v6/sims/basin_two_engine_joint_v2/basin_two_engine_joint_v2_common.py:885-918`.
- Cross-engine comparison and gates: `system_v6/sims/basin_two_engine_joint_v2/basin_two_engine_joint_v2_envelope.py:94-207`.
