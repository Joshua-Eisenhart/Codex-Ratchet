# A2_2_REFINED_CANDIDATES__v1
Status: PROPOSED / NONCANONICAL / A2-2 REFINED CANDIDATES
Batch: `BATCH_A2MID_archive_run_signal_0005_bundle_controller_fences__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Candidate RC1: `RUN_SIGNAL_0005_BUNDLE_IS_A_HISTORICAL_SELF_CONTAINED_EXPORT_KIT_NOT_CURRENT_CONTROL_AUTHORITY`
- candidate read:
  - controller reads should preserve that `RUN_SIGNAL_0005_bundle.zip` is a richer archive export kit with embedded evidence bodies, strategies, snapshots, reports, outbox blocks, and packet lattice, but it remains historical archive material rather than a current control surface
- why candidate:
  - this is the parent's cleanest archive-side authority fence
- parent dependencies:
  - `CLUSTER_MAP__v1.md:1`
  - `CLUSTER_MAP__v1.md:7`
  - `A2_3_DISTILLATES__v1.md`
  - `MANIFEST.json`

## Candidate RC2: `SIXTY_PASS_RUNTIME_ALIGNMENT_DOES_NOT_ERASE_PENDING_EVIDENCE_OR_PARKED_PROMOTION_DEBT`
- candidate read:
  - controller reads should preserve that the embedded runtime-facing surfaces align on `60` passes and `960` accepted items, while embedded state still keeps `60` pending canonical evidence items and `360` `PARKED` sim promotion states
- why candidate:
  - this is the parent's strongest anti-clean-counter overread
- parent dependencies:
  - `CLUSTER_MAP__v1.md:2`
  - `CLUSTER_MAP__v1.md:3`
  - `TENSION_MAP__v1.md:1`
  - `A2_3_DISTILLATES__v1.md`

## Candidate RC3: `DETERMINISTIC_REPLAY_STAYS_DERIVATIVE_WHEN_ITS_FINAL_HASH_DIVERGES_FROM_RUN_FINAL_HASH`
- candidate read:
  - controller reads should preserve replay audit as a useful derivative layer, not as stronger closure authority, because replay determinism still lands on `ed1a34...` while summary/state bind to `0045ff...`
- why candidate:
  - this is the parent's clearest replay-authority boundary
- parent dependencies:
  - `CLUSTER_MAP__v1.md:4`
  - `CLUSTER_MAP__v1.md:5`
  - `TENSION_MAP__v1.md:3`
  - `A2_3_DISTILLATES__v1.md`

## Candidate RC4: `BUNDLE_RICHNESS_DOES_NOT_COLLAPSE_THREE_WAY_CLOSURE_DIVERGENCE`
- candidate read:
  - controller reads should preserve that richer retained structure does not resolve closure, because summary/state, the event endpoint, and replay audit still end on three different final hashes
- why candidate:
  - this is the parent's strongest anti-richness-equals-closure rule
- parent dependencies:
  - `CLUSTER_MAP__v1.md:1`
  - `CLUSTER_MAP__v1.md:5`
  - `TENSION_MAP__v1.md:2`
  - `TENSION_MAP__v1.md:7`
  - `A2_2_CANDIDATE_SUMMARIES__v1.md`

## Candidate RC5: `CONSUMED_400001_LANE_AND_SIGNAL_AUDIT_NULLS_REQUIRE_FAIL_CLOSED_LINEAGE_READS`
- candidate read:
  - controller reads should preserve that the `400001` consumed strategy lane is not interchangeable with the embedded `000001` family, and that `SIGNAL_AUDIT.json` must stay fail-closed where `MATH_DEF` counts coexist with omitted math-kill totals
- why candidate:
  - this is the parent's narrowest controller fence for packet-lineage and audit-null seams
- parent dependencies:
  - `CLUSTER_MAP__v1.md:6`
  - `CLUSTER_MAP__v1.md:8`
  - `TENSION_MAP__v1.md:6`
  - `TENSION_MAP__v1.md:8`
  - `A2_3_DISTILLATES__v1.md`

## Quarantined Q1: `ZERO_PARK_AND_ZERO_REJECT_PACKET_COUNTERS_AS_PROOF_OF_SEMANTIC_CLOSURE`
- quarantine read:
  - do not treat the clean packet counters in summary and soak surfaces as proof that the bundle is semantically closed
- why quarantined:
  - embedded state still preserves unresolved evidence and promotion debt
- parent dependencies:
  - `CLUSTER_MAP__v1.md:3`
  - `TENSION_MAP__v1.md:1`
  - `A2_3_DISTILLATES__v1.md`

## Quarantined Q2: `REPLAY_DETERMINISM_AS_FINAL_HASH_AUTHORITY`
- quarantine read:
  - do not let replay determinism outrank the run-final surfaces when the replay final hash itself diverges
- why quarantined:
  - the parent preserves determinism and divergence together
- parent dependencies:
  - `CLUSTER_MAP__v1.md:5`
  - `TENSION_MAP__v1.md:3`
  - `A2_3_DISTILLATES__v1.md`

## Quarantined Q3: `400001_CONSUMED_STRATEGY_PACKETS_AS_INTERCHANGEABLE_WITH_000001_EMBEDDED_PACKETS`
- quarantine read:
  - do not infer packet identity or strategy equivalence from filename order when fifty-nine of sixty same-position pairs differ byte-for-byte
- why quarantined:
  - the parent explicitly preserves the lane split and dominant byte mismatch
- parent dependencies:
  - `CLUSTER_MAP__v1.md:6`
  - `TENSION_MAP__v1.md:6`
  - `A2_3_DISTILLATES__v1.md`

## Quarantined Q4: `RICH_ARCHIVE_BUNDLE_AS_PERMISSION_TO_TREAT_HISTORICAL_EXPORT_AS_LIVE_RUNTIME_CANON`
- quarantine read:
  - do not let the bundle's retained bodies and overlays become permission to treat a historical export as current runtime canon or active mutation authority
- why quarantined:
  - the parent is archive-side evidence only and carries an explicit downstream-consequence-only policy
- parent dependencies:
  - `CLUSTER_MAP__v1.md:1`
  - `TENSION_MAP__v1.md:7`
  - `MANIFEST.json`
