# CLUSTER_MAP__v1
Status: PROPOSED / NONCANONICAL / ENGINE-PATTERN CLUSTER EXTRACT
Batch: `BATCH_upgrade_docs_jp_graph_prompt_engine_pattern__v1`
Extraction mode: `ENGINE_PATTERN_PASS`

## C1) Graph-truth and proposal-first stance
- source anchors:
  - source 1: `2-15`
- cluster read:
  - the prompt centers one operating picture:
    - graph is privileged truth surface
    - chat is proposal-first rather than conversation-first
    - nothing is final until accepted

## C2) First-class ontology and lifecycle states
- source anchors:
  - source 1: `18-39`
- cluster read:
  - the doc defines a compact runtime ontology:
    - message and intent are separated
    - proposal, patch, and view are distinct artifacts
    - accepted/rejected/stale are explicit state markers

## C3) Intent inference and constrained progression
- source anchors:
  - source 1: `42-55`
- cluster read:
  - the main interaction discipline is:
    - infer intent vectors without assuming fixed goals
    - move one meaningful graph step at a time
    - keep reasoning, proposal, patch, and acceptance distinct

## C4) Mandatory debug/proposal trailer
- source anchors:
  - source 1: `59-100`
- cluster read:
  - the strongest operational mechanism is the required `[DEBUG]` footer
  - it forces per-turn reporting of:
    - observations
    - inferred intent
    - touched entities
    - proposed changes
    - patch status
    - next possible ticks

## C5) Simulated runtime identity
- source anchors:
  - source 1: `104-120`
- cluster read:
  - the prompt is not pretending to be a full system
  - it explicitly frames itself as:
    - L2/L3 boundary simulation
    - execution-aware UX
    - graph OS without a real runtime

## C6) Failure-prevention and reconstructability
- source anchors:
  - source 1: `124-145`
- cluster read:
  - the doc tries to prevent:
    - explanation-only collapse
    - user-decision substitution
    - skipped trace output
    - invented continuity
  - success is defined as reconstructability from the debug trail
