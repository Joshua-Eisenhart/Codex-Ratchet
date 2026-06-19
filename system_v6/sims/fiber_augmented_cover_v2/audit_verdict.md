# Independent audit verdict - fiber_augmented_cover_v2

Bottom line: `fiber_augmented_cover_v2` is `GENUINE` at its bounded scratch ceiling. The cellular carrier checks pass, the degree-1 seam witness recomputes as `3/3 = 1`, the law table recomputes fresh from the v2 cover as `46/99` with two-sided binomial `p=0.546713483598813`, and the exact match to v1 is expected because the law row object is the same `33 x 3 = 99` cover-state/sign realization while the carrier cell/face structure is different.

Verdict: `GENUINE`, with citation caveat G1: the v2 packet directory is currently untracked in this checkout, so cite the local path/audit until a later commit gives it a commit id.

Claim ceiling: `axis_readout_candidate_only + cellular_cover_law_test_v2_no_admission`; `promotion_allowed=false`; `formal_admission_allowed=false`; no Betti, homology, `S3`, `S2xS1`, bridge, physics, manifold, axis-independence, canonical-process, or global-disproof claim is admitted.

Freshness tier: `TIER-3 annotation-verify`. The prompt exposed the builder claims and required prior audit/guard commits; I treated those as binding context and recomputed the load-bearing rows from v2 source instead of trusting stored result prose.

## Scope And Boundary

- Audit mode: fresh read-only audit; live write boundary honored except this `audit_verdict.md`.
- No `git add`, commit, result writer, envelope writer, or validator `main()` was run.
- The normal packet writer scripts were intentionally not invoked because they rewrite result JSON files.
- Native Codex subagents were not spawned because the available spawn tool requires an explicit user request for delegation; this audit used local source inspection, no-write recomputation, and no-cache tests.
- Current worktree state before writing this verdict: `?? system_v6/sims/fiber_augmented_cover_v2/`.

## Law Identity Adjudication

The v2 law was recomputed directly from v2 source by building:

`build_cellular_base()` -> `build_cellular_cover(base, zero_shift=False)` -> `compute_bundle_witness(...)` -> `v1_common.relation_rows(cover)` -> `relation_summary(table, witness)`.

Recomputed result:

| row | value |
|---|---:|
| agreements | `46/99` |
| violations | `53/99` |
| two-sided binomial p | `0.546713483598813` |
| classification | `at_chance` |
| v2 status | `fails_on_cellular_nontrivial_cover` |
| sign vector hash | `51b0fff5e8be355d13648cccc40253e08e9633463d9d225c35a7949ca9008c39` |

This is expected, not suspicious copying. The law rows are cell-based over the same `99` cover states with the same pinned Axis0, Axis3, and Axis6 realizations. The new v2 cellular face/edge structure changes the carrier topology object and consumer chain complexes; it does not enter the `b6=-b0*b3` row formula.

I also replaced `v1_comparison_row()` in-memory with a sentinel row (`agreement_count=-1`) and rebuilt the v2 object. The v2 law remained `46/99`, `p=0.546713483598813`, and `all_pass=true`. That confirms the v1 result JSON is used only as the explicit comparison row, not as the v2 law computation source. Source inspection matches that: `v1_comparison_row()` reads `fiber_augmented_cover_v1_results.json`; the v2 law path computes `table = v1_common.relation_rows(cover)` from the freshly built v2 cover.

Accepted status language:

`b6=-b0*b3` is unsupported at chance, replicated across two independent carrier constructions (graph-lift v1 plus cellular v2), for these shared `99` cover-state rows and pinned axis realizations only.

## Cellular Carrier

The base CW arithmetic recomputes:

| object | counts | chi | chain check |
|---|---:|---:|---|
| cellular base | `C0=33, C1=92, C2=61` | `2` | `d1*d2` entry count `0` |
| total space | `C0=99, C1=375, C2=459, C3=183` | `0` | `d1*d2=0`, `d2*d3=0` |

The face set traces to the construction rules pinned in the build card: seam loop, south pole, north pole, and a deterministic staircase band over the remaining band cycle. Recomputed role counts:

| face role | count |
|---|---:|
| `south_pole_cap_triangle` | `4` |
| `band_triangle` | `29` |
| `band_quad` | `1` |
| `north_pole_cap_triangle` | `27` |

That gives `60` triangles and `1` quad. All faces carry `committed_as_construction_data=true`, every cellular edge is incident to exactly two faces, and every face transition sum closes mod `|F|=3`. I found no face introduced by "sphere must close" prose, target Betti profile, or the rejected topology-v1 33-face model.

## Winding And Fence

The committed cellular seam is `20 -> 17 -> 12 -> 15 -> 20`. The lifted clutching steps recompute as `[1, 1, 1, 0]`; total lifted shift is `3`; `|F|=3`; directed winding is `1`. The zero-shift regression recomputes winding `0` and refuses law rows.

The adjacency fence is present and real:

- v1 dense distinguishability graph: `198` edges.
- v2 cellular 1-skeleton: `92` edges.
- only `22` v2 cellular edges are also v1 dense graph edges.
- packet language keeps the dense graph as distinguishability/generator transition structure and the v2 cellular adjacency as the surface structure.

Faithfulness recomputes on v2:

| axis | result |
|---|---|
| Axis0 | projects to committed Axis0, `mismatch_count=0` |
| Axis3 | source-backed adapter, `gamma_in=33`, `gamma_out=66`, `predicate_mismatch_count=0` |
| Axis6 | projects to committed Axis6, `mismatch_count=0` |

## Controls

Controls fired:

| control | result |
|---|---|
| zero-shift v2 cover | winding `0`, law table refused |
| convention flip `b6=+b0*b3` | `44/99`, `p=0.31487989103762243`, at chance |
| scrambled b6 | `56/96` nonzero-expected agreements, `p=0.1253456971884925`, at chance |
| sign variants | all eight variants present; only `44/99` or `46/99`, all at chance |
| SMT rows | `z3` and `cvc5` real contradictions `unsat`; erased flips `sat` |

These controls support "no convention rescue" and "law row genuinely evaluated"; they do not promote the result beyond the scratch law-test ceiling.

## Consumer Fence And G.2a

Betti is genuinely absent from the builder packet:

- `betti_computed=false`;
- no top-level `betti` field;
- `betti_lane_status=chain_complexes_emitted_for_guard_v2_consumer_no_betti_in_builder_packet`;
- blocked consumers include `formal_admission`, `axis_triple_relation_admission`, `homology_certificate`, and `bridge_or_physics_or_manifold_claim`.

The validator delegates the audit-file boundary to `scripts/builder_audit_boundary.py`, and this verdict header declares independent audit status. That satisfies G.2a/post-audit idempotency from birth.

## Verification

No-write recompute via imported source functions:

```text
base chi=2
base d1*d2 entries=0
total chi=0
total d1*d2 entries=0
total d2*d3 entries=0
winding=1
law=46/99, p=0.546713483598813
validator_errors=[]
all_pass=true
```

No-cache test run:

```text
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest -q -p no:cacheprovider system_v6/sims/fiber_augmented_cover_v2/tests
```

Result: `4 passed in 4.39s`.

## Citation Rule

Future citations should say:

> `fiber_augmented_cover_v2` is a scratch diagnostic cellular-cover replication of the `b6=-b0*b3` law test. It commits a packet-local cellular sphere carrier with `C0=33, C1=92, C2=61`, `chi=2`, edge incidence two-sided, and `d1*d2=0`; builds a `|F|=3` degree-1 cellular cover on the committed seam with lifted steps `[1,1,1,0]`, total `3`, winding `1`; emits hash-pinned total-space cellular chains with `C0=99, C1=375, C2=459, C3=183`, `chi=0`, and `d^2=0`; recomputes Axis0/Axis3/Axis6 faithfulness on the v2 cover; and recomputes the law table as `46/99` agreements, `53/99` violations, two-sided `p=0.546713483598813`, all sign variants at chance. Status: `b6=-b0*b3` is unsupported at chance, replicated across graph-lift v1 and cellular v2 carrier constructions, for these shared `99` cover-state rows and pinned axis realizations only. Ceiling: `axis_readout_candidate_only + cellular_cover_law_test_v2_no_admission`; no Betti, homology, topology, admission, bridge, physics, manifold, axis-independence, or global-disproof claim.

Named next consumer: `fiber_augmented_cover_v2_guard_or_betti_consumer` / guard v2 lane, specifically Betti on the committed base and total-space chain complexes emitted here. That lane must consume the pinned complexes; it must not cite Betti from this builder packet.
