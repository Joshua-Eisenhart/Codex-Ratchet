# TENSION_MAP__v1
Status: PROPOSED / NONCANONICAL / CONTRADICTION-PRESERVING
Batch: `BATCH_upgrade_docs_directed_extraction_family_contradiction_reprocess__v1`
Extraction mode: `CONTRADICTION_REPROCESS_PASS`

## T1) “These are not contradictions” vs actual answer-variant divergence
- source markers:
  - source 3: `32`
  - source 1: `13-62`
  - source 2: `4-47`
  - source 1: `103-156`
  - source 2: `85-126`
- tension:
  - the audit says the six gaps are not contradictions
  - the two answer sheets still diverge materially on multiple answers
- preserved read:
  - the gap statements may not be contradictions, but the answer surfaces became contradiction-bearing

## T2) ZIP enumeration closed vs ZIP enumeration still proposal-side
- source markers:
  - source 1: `15-62`
  - source 2: `5-47`
- tension:
  - source 1 closes with “No additional ZIP types were enumerated without ambiguity”
  - source 2 adds `SIM_FAILURE_ZIP` and `ROSETTA_OVERLAY_ZIP (PROPOSED)`
- preserved read:
  - keep the extra ZIP names as variant extraction, not settled transport law

## T3) FULL+ confirmation specified vs unresolved
- source markers:
  - source 1: `107-119`
  - source 2: `88-96`
- tension:
  - source 1 says confirmation means structural sanity and completeness and that refusal was explicitly discussed
  - source 2 says confirmation meaning and refusal behavior were not finalized
- preserved read:
  - do not collapse this into one resolved FULL+ confirmation rule

## T4) FULL++ confirmation structural/content-blind vs unresolved
- source markers:
  - source 1: `127-139`
  - source 2: `102-111`
- tension:
  - source 1 says confirmation is structural, content-blind, and FULL++ can exist as unconfirmed
  - source 2 says required vs optional and structural vs content-blind remain unresolved
- preserved read:
  - preserve that the stronger answer in source 1 is not backed by source 2

## T5) Shard by manageability vs richer sharding considerations
- source markers:
  - source 1: `88-99`
  - source 2: `73-82`
  - source 3: `68-79`
- tension:
  - source 1 narrows sharding toward manageability rather than semantics
  - source 2 keeps semantic separation / chronology / failure-domain considerations in play
- preserved read:
  - sharding remained qualitatively constrained, but not to one clean heuristic

## T6) Batch-scale policy qualitative vs stronger concrete markers
- source markers:
  - source 1: `70-80`
  - source 2: `53-67`
  - source 3: `49-60`
- tension:
  - source 1 stays mostly qualitative
  - source 2 preserves stronger local markers:
    - `1000 things from a0 to b in one doc`
    - `≥50% of batches must interact with graveyard when non-empty`
- preserved read:
  - concrete-looking numbers exist in the family, but their status remains ambiguous

## T7) Audit says no redesign vs v2 introduces proposed overlay naming
- source markers:
  - source 3: `138`
  - source 2: `42-45`
- tension:
  - the audit explicitly says “Do not design new ZIPs”
  - source 2 includes `ROSETTA_OVERLAY_ZIP (PROPOSED)`
- preserved read:
  - treat that label as proposal-side extraction residue, not a confirmed discussed ZIP

## T8) Folder-order answers-first vs semantic audit-first
- source markers:
  - family-level ordering
- tension:
  - actual folder order begins with answers
  - semantic interpretation order begins with the audit/questions file
- preserved read:
  - this family should be read as answers-to-an-audit even though the files appear in the reverse order
