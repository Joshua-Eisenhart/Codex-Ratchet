
# SYSTEM UPGRADE PLAN — EXTRACT PASS 3

## Scope
Bulk extraction of discussed upgrade intent, unresolved issues, contradictions, and partially specified mechanisms.
No design, no fixes, no summarization beyond structural grouping.

## Core Intent Repeated
- Upgrade MEGABOOT (single authoritative document) to encode:
  - ZIP-based communication
  - Deterministic A0/B/SIM boundary
  - A1 mode control and non-deterministic containment
- Preserve sacred constraints:
  - FINITUDE
  - NONCOMMUTATION

## Recurrent Problems Identified
- Drift during upgrades
- Conflation of:
  - template vs output
  - A1 vs general tools
  - Rosetta vs Save vs Mining
- Loss of authoritative megaboot during split attempts
- Version numbers reused accidentally
- Inability to reliably transport large conversational state

## Thread Architecture (As Discussed, Not Resolved)
- A1:
  - Chatty
  - Mode-driven
  - Controls hallucination, drift, smoothing, narrative, helpfulness
- A0:
  - Deterministic
  - Orchestrates B and SIM
  - Absorbs Thread S and SIM coordination
- B:
  - Canon kernel
- SIM:
  - External terminal executor

## ZIP Usage
- ZIPs as deterministic, chatless subagents
- ZIP never splits
- Docs inside ZIP shard with size limits
- ZIP ingestion must be single-line

## Graveyard
- Mandatory
- Never dead
- >=50% interaction when non-empty
- Exploration fuel, not failure

## SIM Pipeline (Repeated, Sometimes Inconsistent)
- A0 -> B approval -> SIM terminal -> results -> A0 -> B
- Two ZIPs:
  - SIM_PROPOSAL_ZIP
  - SIM_RUN_ZIP

## Unresolved / Conflicting Areas
- Whether Thread S exists at all
- Whether Rosetta is merged into A1 or separate
- Whether A0 can validate full++
- Whether A1 emits proposed full++
- How to enforce LLM mode changes deterministically
- Whether mode confirmation is possible or only probabilistic

## Extraction Process Issues
- LLM collapses intent into summaries
- Large context causes unintended compression
- Manual “go on” loop required
- Percentage-complete indicators drift
- File generation intermittently fails

## Explicitly Unclear
UNSPECIFIED — DO NOT INFER

## Notes on Process
- Extraction itself identified as future system feature
- Multi-pass extraction preferred over single-pass
- Redundancy accepted to reduce Goodhart collapse
- Contradictions intentionally preserved

END OF PASS 3
