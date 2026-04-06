# Intense External Swarm Batch 01

**Date:** 2026-03-29  
**Purpose:** Second-wave external-thread batch for adversarial audits, rival readings, and contradiction-preserving stress tests.  
**Discipline:** These lanes are intentionally aggressive, but they are still bounded. None may change doctrine by themselves.

---

## 1. How To Use This Batch

Each external thread should:

1. read exactly one boot packet
2. write exactly one return packet
3. stop

Use this thread as controller for acceptance, fencing, rejection, or archive decisions.

Core workflow:

- [EXTERNAL_THREAD_SWARM_WORKFLOW.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/EXTERNAL_THREAD_SWARM_WORKFLOW.md)
- [EXTERNAL_THREAD_INGEST_AND_CLEANUP.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/EXTERNAL_THREAD_INGEST_AND_CLEANUP.md)

---

## 2. Recommended Model Routing

Use these model classes:

- `Gemini 3.1 Pro (High)`
  - rival doctrine reads
  - owner-packet gap hunts
  - anti-smoothing stress tests
- `Claude Opus 4.6 (Thinking)`
  - deep derivation attacks
  - contradiction-preserving synthesis
- `Claude Sonnet 4.6 (Thinking)`
  - focused structure attacks
  - overreach audits
- `Gemini 3.1 Pro (Low)`
  - duplicate / leak / staging overstatement audits
- `Gemini 3 Flash`
  - inventories
  - citation maps
  - naming drift clusters

---

## 3. Batch Lanes

| Lane | Boot file | Best model |
|---|---|---|
| Rival stack audit | `BOOT__RIVAL_STACK_AUDIT__2026_03_29__v1.md` | Gemini High |
| Ax0 rival doctrine read | `BOOT__AX0_RIVAL_DOCTRINE_READ__2026_03_29__v1.md` | Gemini High |
| Owner packet gap hunt | `BOOT__OWNER_PACKET_GAP_HUNT__2026_03_29__v1.md` | Gemini High |
| Sim-to-doctrine mismatch audit | `BOOT__SIM_TO_DOCTRINE_MISMATCH_AUDIT__2026_03_29__v1.md` | Opus |
| Ax1-Ax4 chain attack | `BOOT__AX1_AX4_CHAIN_ATTACK__2026_03_29__v1.md` | Opus |
| Anti-smoothing stress test | `BOOT__ANTI_SMOOTHING_STRESS_TEST__2026_03_29__v1.md` | Opus |
| Thread B overreach hunt | `BOOT__THREAD_B_OVERREACH_HUNT__2026_03_29__v1.md` | Sonnet |
| Lexeme-term-permit leak audit | `BOOT__LEXEME_TERM_PERMIT_LEAK_AUDIT__2026_03_29__v1.md` | Gemini Low |
| Duplicate family collapse plan | `BOOT__DUPLICATE_FAMILY_COLLAPSE_PLAN__2026_03_29__v1.md` | Sonnet |
| Alternate axis mapping audit | `BOOT__ALTERNATE_AXIS_MAPPING_AUDIT__2026_03_29__v1.md` | Gemini High |
| Citation map inventory | `BOOT__CITATION_MAP_INVENTORY__2026_03_29__v1.md` | Gemini Flash |
| Naming drift cluster audit | `BOOT__NAMING_DRIFT_CLUSTER_AUDIT__2026_03_29__v1.md` | Gemini Flash |

---

## 4. Stop Rules

All lanes must stop if they would need to:

- decide canon or permit status
- rewrite bridge/cut doctrine
- outrank the controller stack
- mutate runtime code or probes

---

## 5. Controller Use

Best use of this batch:

- launch many fresh threads
- collect raw returns in `system_v4/thread_returns/`
- ingest only accepted or accepted-with-fence results
- then run local `codex-autoresearch` on the surviving residue
