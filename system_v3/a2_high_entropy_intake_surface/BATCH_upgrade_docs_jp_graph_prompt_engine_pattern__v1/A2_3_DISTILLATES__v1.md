# A2_3_DISTILLATES__v1
Status: PROPOSED / NONCANONICAL / OUTER-CACHE DISTILLATE
Batch: `BATCH_upgrade_docs_jp_graph_prompt_engine_pattern__v1`
Extraction mode: `ENGINE_PATTERN_PASS`

## Distillate D1
- statement:
  - this file is a compact graph-first interaction shell, not a runtime spec
- source anchors:
  - source 1: `2-15`
  - source 1: `104-120`
- possible downstream consequence:
  - later reuse should treat it as a proposal-side prompting pattern rather than system law

## Distillate D2
- statement:
  - the core engine pattern is separation between:
    - reasoning
    - proposal
    - patch
    - acceptance
- source anchors:
  - source 1: `27-37`
  - source 1: `52-55`
  - source 1: `88-100`
- possible downstream consequence:
  - high-value lineage for proposal-trace discipline in future interface or tooling work

## Distillate D3
- statement:
  - the required `[DEBUG]` trailer is the doc's main anti-drift mechanism
- source anchors:
  - source 1: `59-100`
  - source 1: `128-139`
- possible downstream consequence:
  - later comparison work can test whether this footer model aligns or conflicts with other intake-side trace surfaces

## Distillate D4
- statement:
  - the prompt tries to force epistemic caution:
    - messages are observations
    - docs are views
    - acceptance cannot be invented
- source anchors:
  - source 1: `8-11`
  - source 1: `49-52`
  - source 1: `94-100`
  - source 1: `125-129`
- possible downstream consequence:
  - useful provenance for later trust-boundary analysis

## Distillate D5
- statement:
  - the prompt likely belongs to the same local family as the `friend's graph/intent prompt` referenced in the previously batched pass extracts
- source anchors:
  - source 1: `2-15`
  - source 1: `42-55`
- possible downstream consequence:
  - candidate comparison target for later A1 mode-control and proposal-surface analysis, but not direct promotion

## Distillate D6
- statement:
  - the doc's biggest unresolved seam is authority:
    - graph as truth
    - chat outputs as proposals/views
    - no real runtime
- source anchors:
  - source 1: `8-11`
  - source 1: `49-55`
  - source 1: `104-120`
- possible downstream consequence:
  - strong reason to quarantine this prompt from active control truth until authority mapping is reconciled
