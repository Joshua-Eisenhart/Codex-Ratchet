# A2_2_REFINED_CANDIDATES__v1
Status: PROPOSED / NONCANONICAL / OUTER A2-MID REDUCTION ARTIFACT
Batch: `BATCH_A2MID_refinedfuel_nonsims_simulation_protocol_controller_fences__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Candidate RC1: `PROTOCOL_STATUS_CANNOT_GATE_KERNEL_ADMISSIBILITY_OR_KERNEL_MEANING`
- candidate read:
  - controller reads should treat run status, protocol success, and protocol outputs as non-gating relative to kernel admissibility and kernel meaning
- why candidate:
  - this is the cleanest compression of the parent's top-level anti-gating quarantine
- parent dependencies:
  - `CLUSTER_MAP__v1:1`
  - `TENSION_MAP__v1:1`
  - `A2_3_DISTILLATES__v1`

## Candidate RC2: `INPUTS_OVERLAYS_AND_DERIVED_PAYLOADS_REQUIRE_EXPLICIT_SEPARABLE_LINEAGE`
- candidate read:
  - controller use must keep kernel, overlay, and protocol artifacts explicitly separated, with no undeclared inputs, no in-place input mutation, and explicit lineage for derived payloads
- why candidate:
  - this preserves the parent's strongest anti-hidden-dependency and anti-mutation handling
- parent dependencies:
  - `CLUSTER_MAP__v1:1`
  - `CLUSTER_MAP__v1:2`
  - `TENSION_MAP__v1:2`
  - `A2_3_DISTILLATES__v1`

## Candidate RC3: `REPLAY_REQUIRES_DECLARED_FINITE_SCHEDULES_COMPLETE_TAPES_AND_NO_HIDDEN_STATE`
- candidate read:
  - controller reads must require explicit finite step schedules, declared nondeterminism and environment, complete tape entries, replay by tape order rather than clocks, and no hidden intermediates or cross-run state
- why candidate:
  - this turns the parent's replayability spine into a practical controller fence against opaque runtime doctrine
- parent dependencies:
  - `CLUSTER_MAP__v1:3`
  - `CLUSTER_MAP__v1:4`
  - `CLUSTER_MAP__v1:7`
  - `TENSION_MAP__v1:2`
  - `A2_3_DISTILLATES__v1`

## Candidate RC4: `FAILURE_HANDLING_AND_DIAGNOSTICS_STAY_EXPLICIT_NON_BINDING_AND_NON_VERDICTAL`
- candidate read:
  - controller reads must block silent auto-repair, silent truncation, implicit halt/continue policy, correctness verdicts, and diagnostic artifacts being promoted into kernel structure or admission control
- why candidate:
  - this is the strongest controller-facing compression of the parent's anti-completion-theater and anti-diagnostic-authority posture
- parent dependencies:
  - `CLUSTER_MAP__v1:5`
  - `CLUSTER_MAP__v1:6`
  - `TENSION_MAP__v1:3`
  - `TENSION_MAP__v1:4`
  - `A2_3_DISTILLATES__v1`

## Candidate RC5: `CACHES_SUMMARIES_AND_EXPORTS_REMAIN_LOSS_AWARE_TAPE_GROUNDED_AND_NON_AUTHORITATIVE`
- candidate read:
  - controller reads must keep caches, lossy summaries, export bundles, and overlay stripping explicitly marked, replay-grounded, and unable to outrank the tape or mutate kernel artifacts
- why candidate:
  - this compresses the parent's final replay/export close into a controller-usable fence
- parent dependencies:
  - `CLUSTER_MAP__v1:7`
  - `CLUSTER_MAP__v1:8`
  - `TENSION_MAP__v1:4`
  - `TENSION_MAP__v1:5`
  - `A2_3_DISTILLATES__v1`

## Quarantined Q1: `PROTOCOL_LANGUAGE_AS_CORRECTNESS_VALIDATION_OR_KERNEL_AUTHORITY`
- quarantine read:
  - do not treat run completion, diagnostics, or protocol success language as evidence of correctness, truth, admissibility, or kernel authority
- why quarantined:
  - the parent explicitly permits protocol bookkeeping while denying those escalations
- parent dependencies:
  - `CLUSTER_MAP__v1:1`
  - `CLUSTER_MAP__v1:5`
  - `CLUSTER_MAP__v1:6`
  - `TENSION_MAP__v1:1`
  - `TENSION_MAP__v1:4`

## Quarantined Q2: `REPLAY_AND_EXPORT_LANGUAGE_AS_COVER_FOR_HIDDEN_STATE_OR_SUMMARY_SUPREMACY`
- quarantine read:
  - do not let replay, cache, bundle, or summary language hide undeclared state, silent loss, missing artifacts, or summary-over-tape authority
- why quarantined:
  - the parent is valuable precisely because it keeps replay vocabulary available while blocking opaque runtime and summary substitution drift
- parent dependencies:
  - `CLUSTER_MAP__v1:3`
  - `CLUSTER_MAP__v1:4`
  - `CLUSTER_MAP__v1:7`
  - `CLUSTER_MAP__v1:8`
  - `TENSION_MAP__v1:2`
  - `TENSION_MAP__v1:4`
