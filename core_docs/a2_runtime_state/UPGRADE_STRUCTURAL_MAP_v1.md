==================================================
UPGRADE_STRUCTURAL_MAP_v1
==================================================

DOCUMENT: DIRECTED_EXTRACTION_ANSWERS.md

# DIRECTED EXTRACTION — ANSWERS FROM THREAD CONTEXT
MODE: STATE_EXTRACTION_ONLY
## QUESTION SET A — ZIP ENUMERATION
The following ZIP types were explicitly discussed or repeatedly implied in the thread:
1. MEGABOOT_ZIP
2. RATChet_BUNDLE_ZIP
3. FULL_LEDGER_ZIP (also called FULL+)
4. FULL++_ARCHIVE_ZIP
5. ZIP_JOB (generic)
6. SIM_PROPOSAL_ZIP
7. SIM_RUN_ZIP
8. SIM_RESULTS_ZIP
9. SIM_EVIDENCE_ZIP
No additional ZIP types were enumerated without ambiguity.
## QUESTION SET B — A0 BATCH SCALE
## QUESTION SET C — SHARDING HEURISTICS
- ZIPs must not split.
- Documents inside ZIPs must shard.
## QUESTION SET D — FULL+ CONFIRMATION
## QUESTION SET E — FULL++ CONFIRMATION
## QUESTION SET F — PHASE TRANSITION SIGNALS
## EXTRACTION NOTES
- Mode drift and LLM behavior control were repeatedly discussed as unresolved.

DOCUMENT: DIRECTED_EXTRACTION_ANSWERS_v2.md

# DIRECTED EXTRACTION — ANSWERS (DENSE)
## QUESTION SET A — ZIP ENUMERATION
- **ZIP_JOB / ZIP as subagent**
- **FULL_LEDGER_ZIP (FULL+)**
- **FULL++ (ROSETTA AUGMENTED) ZIP**
- **SIM_PROPOSAL_ZIP**
- **SIM_RUN_ZIP**
- **SIM_RESULTS_ZIP / SIM_FAILURE_ZIP**
- **SIM_EVIDENCE_ZIP**
- **ROSETTA_OVERLAY_ZIP (PROPOSED)**
## QUESTION SET B — A0 MASSIVE BATCH POLICY
## QUESTION SET C — SHARDING STRATEGY HEURISTICS
- "ZIP never splits; docs inside ZIP shard."
## QUESTION SET D — FULL+ CONFIRMATION
## QUESTION SET E — FULL++ CONFIRMATION
## QUESTION SET F — PHASE TRANSITION SIGNALS
- "Need explicit phase change tokens in protocol."
## EXTRACTION NOTES
- "Mode control is needed because LLM cannot deterministically obey mode."

DOCUMENT: DIRECTED_EXTRACTION_AUDIT_AND_QUESTIONS.md

# DIRECTED EXTRACTION — AUDIT AND OPEN QUESTIONS
## OBSERVED FAILURE MODES
- VERSION inconsistency across artifacts
## QUESTIONS (OPEN)
### ZIP ENUMERATION / TRANSPORT
- Does THREAD_A0 own ZIP packaging authority or is it delegated?
- Does THREAD_B ingest ZIPs directly or only derived ledger shards?
### VERSIONING
- What is the authoritative MEGABOOT version string format?
- Does every integration step require a MEGABOOT version bump?
- Are VERSION references inside older docs treated as historical or as active constraints?
### MODE CONTROL
- How are MODE declarations enforced if LLM cannot deterministically stay in a mode?
### BOOT / REBOOT
- What is the minimal BOOT sequence for A2 rehydration?
- Should BOOT always begin with ZIP_INDEX enumeration?
### THREAD TOPOLOGY
- Is THREAD_A2 already defined in MEGABOOT or only in external context?
- Where does THREAD_A2 sit relative to THREAD_A1 in boot order?

DOCUMENT: SYSTEM_UPGRADE_PLAN_EXTRACT_PASS1.md

# SYSTEM UPGRADE PLAN — EXTRACTION PASS 1
## PRIMARY TARGET
- MEGABOOT upgrade to include THREAD_A2 formally
## KNOWN STATE
- MEGABOOT_RATCHET_SUITE v7.4.9 in archive
- THREAD_A2 not yet formally integrated
## REQUIRED INSERTIONS (HIGH LEVEL)
- Add THREAD_A2 to thread topology
- Add A2 boot / spec section
- Preserve root constraints and existing bootpacks
## VERSIONING
- Every integration requires VERSION bump and full document output
## ZIP TRANSPORT
- ZIP_JOB already present in MEGABOOT 7.4.9
- ZIP as deterministic subagent container
## MODE DISCIPLINE
- Explicit MODE declarations required to avoid silent drift
## FAILURE MODES
- Silent mode switching
- Authority leakage across THREAD boundaries
## NOTES
- Boot order and topology must be consistent in MEGABOOT

DOCUMENT: SYSTEM_UPGRADE_PLAN_EXTRACT_PASS2.md

# SYSTEM UPGRADE PLAN — EXTRACTION PASS 2
## A2 INTEGRATION TARGETS
- THREAD_A2 definition
- A2_SYSTEM_SPEC placement into MEGABOOT
## MEGABOOT EDIT RULES (AS DISCUSSED)
- Preserve all existing content verbatim
- Only bounded insertions with VERSION bump
## THREAD TOPOLOGY REQUIREMENTS
- THREAD_A2 positioned above THREAD_A1
- THREAD_B retains canonical authority
## BOOT ORDER REQUIREMENTS
- Add THREAD_A2 into boot thread list
## ZIP PROTOCOL
- Formalize ZIP transport pathway across threads
## MODE CONTROL (A1/A2)
- Need explicit MODE declarations
- Need drift detection hooks
## VERSION REFERENCES
- Avoid VERSION reuse across upgrades

DOCUMENT: SYSTEM_UPGRADE_PLAN_EXTRACT_PASS3.md

# SYSTEM UPGRADE PLAN — EXTRACTION PASS 3
## CORE PROBLEM IDENTIFIED
- Version numbers reused accidentally
## REQUIRED CONTROL SURFACE
- Explicit MODE declarations
## ZIP PIPELINE
- ZIP export packs for A2 continuity
- ZIP job format for deterministic ingestion
## VERSION DISCIPLINE
- One VERSION per integration step, no reuse
## THREAD BOUNDARY
- THREAD_B canon only
- THREAD_A0 deterministic executor only
- THREAD_A1 proposal / translation only
- THREAD_A2 structural generation only
## MODE FAILURE VECTORS
- How to enforce LLM MODE changes deterministically

DOCUMENT: SYSTEM_UPGRADE_PLAN_EXTRACT_PASS4.md

# SYSTEM UPGRADE PLAN — EXTRACTION PASS 4
## MIGRATION STATE
- Archive created as full-state freeze prior to new-thread migration
## REQUIRED READ ORDER
- ZIP index first
- Memory spine docs next
- Upgrade docs next
## BOOT DISCIPLINE
- BOOT must precede any further integration work
## MODE DISCIPLINE
- MODE must be declared explicitly
## VERSION REFERENCES
- Preserve historical versions; avoid ambiguous version replacement
## THREAD A2 ROLE
- THREAD_A2 operates as construction / generation only

DOCUMENT: SYSTEM_UPGRADE_PLAN_EXTRACT_PASS5.md

# SYSTEM UPGRADE PLAN — EXTRACTION PASS 5
## A0 BOTTLENECK
- A0 batching too conservative
## THREAD B ALREADY CONSERVATIVE
## ZIP SHARDING POLICY
- ZIP never splits
- Docs inside ZIP shard
## MODE DISCIPLINE
- MODE drift treated as system failure mode
## VERSIONING
- VERSION references must be coherent across reboot kit and topology sections

DOCUMENT: SYSTEM_UPGRADE_PLAN_EXTRACT_PASS6.md

# SYSTEM UPGRADE PLAN — EXTRACTION PASS 6
## REBOOT PROCESS
- A2 needs a formal reboot loop using saved “brain” docs
## ZIP EXPORT PACKS
- A2 export pack ZIP for continuity
- FULL+ / FULL++ ZIP layering referenced
## MODE REQUIREMENTS
- MODE declarations required per turn / per pass
- MODE gate to prevent drift
## VERSION POLICY
- VERSION bump required when MEGABOOT changes
## THREAD BOUNDARIES
- THREAD_A2 has no canonical authority
- THREAD_A2 has no elimination authority
- THREAD_A2 has no simulation authority
## BOOT ORDER
- BOOT requires read-first discipline before upgrades

DOCUMENT: SYSTEM_UPGRADE_PLAN_EXTRACT_PASS7.md

# SYSTEM UPGRADE PLAN — EXTRACTION PASS 7
## SIM ROLE (DETERMINISTIC)
## SIM APPROVAL FLOW (AS DISCUSSED)
## HASH / BINDING REQUIREMENTS (PARTIAL, NOT FINAL)
## DETERMINISM BOUNDARY
## FAILURE MODES IDENTIFIED
## OPEN AMBIGUITIES
- Whether SIM artifacts are always ZIPs

DOCUMENT: SYSTEM_UPGRADE_PLAN_EXTRACT_PASS8.md

# SYSTEM_UPGRADE_PLAN_EXTRACT_PASS8
MODE: VERBATIM / DENSE AGGREGATION
SECTION: A1 MODES AND LLM FAILURE VECTORS
- A1 modes discussed as REAL behavioral constraints, not labels.
- Mode changes are NONCOMMUTATIVE.
- Deterministic enforcement of mode change may not be possible.
- Confirmation of mode change is required even if deterministic enforcement fails.

DOCUMENT: SYSTEM_UPGRADE_PLAN_EXTRACT_PASS9.md

# SYSTEM UPGRADE PLAN — EXTRACTION PASS 9
## MEGABOOT STATUS (AS OF ARCHIVE)
## A2 STATUS
- THREAD_A2 not formally integrated into MEGABOOT
## REQUIRED DELTAS
- Add THREAD_A2 definition
- Add A2_SYSTEM_SPEC numbered section
- Update boot order to include THREAD_A2
## MODE CONTROL
## VERSIONING
## ZIP PIPELINE
## BOOT DISCIPLINE
