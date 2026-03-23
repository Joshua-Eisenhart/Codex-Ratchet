# A2_2_REFINED_CANDIDATES__v1
Status: PROPOSED / NONCANONICAL / OUTER A2-MID REDUCTION ARTIFACT
Batch: `BATCH_A2MID_stage2_public_conformance_controller_fences__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Candidate RC1: `DELIVERY_GATE_STACK_BEFORE_PROMOTION`
- candidate read:
  - promotion or release claims should be read through the explicit tuning, build, run-surface, and fixture gate stack before the controller treats a packet as ready
- why candidate:
  - this is the parent's clearest late-stage delivery reduction for controller use
- parent dependencies:
  - `CLUSTER_MAP__v1:Cluster A`
  - `A2_3_DISTILLATES__v1:D1`
  - `A2_2_CANDIDATE_SUMMARIES__v1:C1`

## Candidate RC2: `PROVISIONAL_CONTROLLER_PROCESS_USE_RULE`
- candidate read:
  - the controller process is active enough to route work, but provisional enough that it must stay revisable and artifact-tested rather than treated as closed architecture
- why candidate:
  - this is the strongest controller-specific boundary inside the parent
- parent dependencies:
  - `CLUSTER_MAP__v1:Cluster B`
  - `A2_3_DISTILLATES__v1:D2`
  - `TENSION_MAP__v1:T5`
  - `A2_2_CANDIDATE_SUMMARIES__v1:C3`

## Candidate RC3: `CONFORMANCE_VECTOR_DRIFT_SIGNATURE_CAPTURE`
- candidate read:
  - fixture-pack expectations should be preserved as concrete drift probes, especially where they diverge from earlier owner-tag fences
- why candidate:
  - this gives the controller a small, testable contradiction packet rather than a vague “conformance matters” reminder
- parent dependencies:
  - `CLUSTER_MAP__v1:Cluster D`
  - `A2_3_DISTILLATES__v1:D4`
  - `TENSION_MAP__v1:T1`
  - `A2_2_CANDIDATE_SUMMARIES__v1:C2`

## Candidate RC4: `SCHEMA_STUBS_ARE_NOT_ENFORCEMENT`
- candidate read:
  - stage2 schemas, stage3 bundle flow, and browser ZIP loops remain useful hardening declarations, but not proof of implemented enforcement by themselves
- why candidate:
  - this gives the controller a direct filter against overstating schema or browser-path readiness
- parent dependencies:
  - `CLUSTER_MAP__v1:Cluster C`
  - `A2_3_DISTILLATES__v1:D3`
  - `A2_2_CANDIDATE_SUMMARIES__v1:C4`

## Candidate RC5: `PUBLIC_BOUNDARY_OVERLAY_BELOW_INTERNAL_BOOTSET`
- candidate read:
  - public-facing docs can preserve boundary explanations, but they must stay below thicker internal A2 boot and control surfaces
- why candidate:
  - this is the cleanest reduction of the parent's public-boundary discipline for controller use
- parent dependencies:
  - `CLUSTER_MAP__v1:Cluster E`
  - `A2_3_DISTILLATES__v1:D5`
  - `TENSION_MAP__v1:T4`
  - `A2_2_CANDIDATE_SUMMARIES__v1:C5`

## Quarantined Q1: `WORK_PATH_STAGE3_AS_CURRENT_WRITE_POSTURE`
- quarantine read:
  - do not treat late-stage `work/` bundle paths as already reconciled current write posture
- why quarantined:
  - the parent preserves a real `system_v3`-centric posture versus late `work/` path spillover tension
- parent dependencies:
  - `TENSION_MAP__v1:T2`
  - `A2_2_CANDIDATE_SUMMARIES__v1:C6`
  - `A2_3_DISTILLATES__v1:D6`

## Quarantined Q2: `PUBLIC_HOSTING_AND_BROWSER_PATH_AS_KERNEL_AUTHORITY`
- quarantine read:
  - do not let public host explanations or browser-mediated orchestration paths self-promote into kernel or internal control authority
- why quarantined:
  - the parent keeps orchestration expansion pressure below sealed kernel and internal boot boundaries
- parent dependencies:
  - `TENSION_MAP__v1:T7`
  - `TENSION_MAP__v1:T4`
  - `A2_2_CANDIDATE_SUMMARIES__v1:C5`
