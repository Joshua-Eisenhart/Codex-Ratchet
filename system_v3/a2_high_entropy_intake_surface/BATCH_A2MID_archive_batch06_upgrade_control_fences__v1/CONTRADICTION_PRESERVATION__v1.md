# CONTRADICTION_PRESERVATION__v1
Status: PROPOSED / NONCANONICAL / CONTRADICTION-PRESERVING REDUCTION NOTE
Batch: `BATCH_A2MID_archive_batch06_upgrade_control_fences__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Preserved contradiction set

### CP1) Output-only upgrade packet vs absent payload, meta, and schema supports
Pole A:
- the package preserves compact retained outputs over bootpacks and upgrade-plan extracts

Pole B:
- the payload sources, meta seed, and schemas it depends on are absent from the zip

Preserved read:
- this is a historical result packet, not a self-sufficient authority bundle

### CP2) Restored exact lock rows vs absent seed authority
Pole A:
- exact Type-1 and Type-2 mapping locks return in retained outputs

Pole B:
- those locks point back to an absent meta seed

Preserved read:
- preserve the lock lineage, but do not treat this zip as primary seed authority

### CP3) Template-struct pass vs no in-bundle schemas
Pole A:
- all three stage-2 JSON bindings report `PASS_TEMPLATE_STRUCT`

Pole B:
- the authoritative schemas are not packaged in the zip

Preserved read:
- structural pass is useful history, but weaker than bundle-contained schema validation

### CP4) Thread S absorbed by A0 vs Thread S repeatedly reintroduced
Pole A:
- one strand absorbs Thread S into A0 and SIM coordination

Pole B:
- another strand keeps reintroducing or retaining Thread S

Preserved read:
- Thread S instability remains the package's central architecture contradiction

### CP5) ZIP as chatless subagent vs ZIP as template, tool, or container
Pole A:
- ZIPs are described as deterministic chatless subagents

Pole B:
- ZIP meaning later collapses into templates, extraction tools, and generic containers

Preserved read:
- preserve this as a definition conflict rather than stable ZIP doctrine

### CP6) Strict bootpack enforcement vs output-contract validation drift
Pole A:
- bootpack doctrine insists on rigid message typing and fail-closed enforcement

Pole B:
- the portable output contract records `NO` across listed rejection flags while still presenting fail-closed framing

Preserved read:
- this is an archive-level enforcement drift signal

### CP7) Thread A no-choice policy vs option boxing
Pole A:
- Thread A says it must not ask the user to choose a mode

Pole B:
- Thread A still requires multi-option intent sandboxing

Preserved read:
- preserve as a framework contradiction between friction avoidance and option-explicit teaching

### CP8) Graveyard and Rosetta exploration vs partial historical conflation cleanup
Pole A:
- graveyard and Rosetta are positioned as noncanon exploration support

Pole B:
- earlier formulations partially conflated Rosetta with Thread S or save-mining behavior

Preserved read:
- keep this as partial correction rather than resolved boundary law
