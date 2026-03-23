# TENSION_MAP__v1
Status: PROPOSED / NONCANONICAL / CONTRADICTION-PRESERVING
Batch: `BATCH_work_surface_residual_handoff_and_zipjob_refinery__v1`
Extraction mode: `RESIDUAL_HANDOFF_AND_ZIPJOB_REFINERY_PASS`

## T1) “light” and “lean” packs vs omitted local-state dependencies
- source markers:
  - light pack inventory
  - light `STATE_INPUTS_NOTE.md`
  - auto-built lean pack read-first and inventory
- tension:
  - the light and auto packs are much smaller than the full pack
  - the light note explicitly says the omitted `A1_ROSETTA_v1.json` and `A2_BRAIN_v1.json` must be supplied from local `work/audit_tmp/...` paths
  - the auto lean pack matches the light inventory exactly, so its portability inherits the same omission pattern
- preserved read:
  - pack slimming succeeds mechanically, but some of the burden is pushed onto local side-state rather than removed entirely

## T2) “small delta” language vs broad bundled operator material
- source markers:
  - `PRO_THREAD_UPDATE_PACK__v5_SMALL/00_READ_FIRST.md:1-33`
- tension:
  - the pack says it avoids re-sending full `system_v3/` and `core_docs/`
  - it still carries large issue ledgers, Playwright claw automation, validator tooling, and canon-lock bridge docs
- preserved read:
  - the lane wants delta-scale packaging but still needs enough surrounding operator structure to keep a Pro thread aligned

## T3) portable extract shaping vs overwhelming `SYSTEM_PROCESS` dominance
- source markers:
  - `A2_BRAIN_v1__type_counts.json`
  - `A2_BRAIN_v1__filtered__no_SYSTEM_PROCESS.json`
- tension:
  - `SYSTEM_PROCESS` occupies `4743` of `6536` typed entries
  - the filtered portable slice keeps only `1793` non-`SYSTEM_PROCESS` entries
- preserved read:
  - portable handoff in this lane depends on aggressive type filtering because raw A2 state is process-heavy

## T4) long explicit naming contract vs short-batch and mixed interchange conventions
- source markers:
  - `ZIP_SUBAGENT_SYSTEM_v2_1__CONTROL_PLANE_ALIGNED__LONG_EXPLICIT_NAMING.md`
  - `EXTRACT_TOPIC_v1/INSTRUCTIONS.md`
  - drop-in `v7_2_4` title and runbook
  - outbox alignment reply
- tension:
  - the later system doc demands path names that act as compact definitions
  - the older topic template still uses per-topic folders with short leaf names like `EXTRACTIVE.md`
  - the later alignment reply recommends flat-file portable interchange
  - the later drop-in variant advertises `SHORT_BATCH_NAMING` while still enforcing exact long explicit output paths
- preserved read:
  - naming and interchange are being tightened, but the residue still carries at least three partially overlapping conventions

## T5) sandbox read-only doctrine vs repeated repackaging of active system material
- source markers:
  - sandbox manifest
  - violation report
  - handoff note 25
  - full/light context pack plaques
- tension:
  - the sandbox doctrine says `system_v3/` and `core_docs/` are read-only and sandbox work must stay under `work/`
  - the residual handoff packs repeatedly copy or reference `system_v3/specs/*`, runbooks, and upgrade docs into portable `work/` bundles
- preserved read:
  - the prototype lane respects mutation boundaries but still duplicates large active-system surfaces into handoff packs

## T6) strict single-manifest ambition vs visible manifest/template drift
- source markers:
  - handoff note 25
  - template v3 manifest
  - template v3 realized manifest
  - strict drop-in manifest
- tension:
  - the handoff note explicitly calls out manifest inconsistency and asks for one contract
  - the template, realized template, and strict drop-in show different task counts and output-set sizes
- preserved read:
  - the lane is converging on a single deterministic manifest shape, but the prototype family still shows intermediate contract stages

## T7) one-ZIP return goal vs fenced-file fallback permanence
- source markers:
  - strict drop-in readme
  - strict runbook
  - full pack read-first
  - run launcher
- tension:
  - several plaques prefer one ZIP containing a full `output/` tree
  - the same family retains fenced-file return as the hard fallback and keeps starter messages centered on fenced-file emission
- preserved read:
  - ZIP return is preferred, but mechanical fenced-file interchange remains the actual fail-closed floor
