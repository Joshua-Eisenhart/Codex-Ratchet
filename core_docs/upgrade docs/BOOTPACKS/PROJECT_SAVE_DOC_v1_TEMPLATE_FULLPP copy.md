# PROJECT_SAVE_DOC v1 (TEMPLATE, FULLPP)

DATE_UTC: 2026-01-30T00:00:00Z  
TIMEZONE: America/Los_Angeles  
PROJECT_ID: <FILL>  
THREAD_B_KERNEL_VERSION: v3.9.x (pin exact on run)  
THREAD_S_LINTER_VERSION: <FILL>  
BUNDLE_VERSION: v2.0.11 (this zip)  

## 0) Purpose

This file is a **single source of truth** you update after each ratchet session.

- It is **not** meant to be pasted into Thread‑B.  
- It is meant to be stored alongside the bundle zip, so you can always reconstruct the current “canon” by replaying a deterministic tape.

## 1) Deterministic reconstruction recipe (no inference)

1) New project / new chat workspace  
2) Load **MEGABOOT** (Thread‑A) and follow it exactly  
3) Boot Thread‑B (enforcement kernel)  
4) Replay `EXPORT_TAPE_v1_LEGACY_PASS_ONLY.txt` (exactly as‑is)  
5) Replay any additional export blocks you added after this bundle (append‑only)  
6) Re-run SIMs and ingest SIM_EVIDENCE blocks (append‑only)

## 2) Current ratchet snapshot (fill after each run)

- ACCEPT_COUNT: <FILL>  
- UNCHANGED_LEDGER_STREAK: <FILL>  
- TERM_REGISTRY counts:
  - TERM_PERMITTED: <FILL>
  - CANONICAL_ALLOWED: <FILL>
- PARK_SET size: <FILL>
- REJECT_SET size: <FILL>
- EVIDENCE_PENDING size: <FILL>

## 3) Canon pointers (fill after each run)

- Latest CAMPAIGN_TAPE: <FILL filename or link>  
- Latest SAVE_SNAPSHOT (if you export one): <FILL>  
- Latest SIM_EVIDENCE pack: <FILL>  

## 4) Bundle file hashes (sha256)

These hashes let you detect corruption / contamination of the bundle itself.

- AXIS_FOUNDATION_COMPANION_v1.2.md: a59c3a1eaf39d80058317a4d36187a134b2a845739da46008c5c6fb332f6f0cf
- CAMPAIGN_TAPE_v1_LEGACY_THREAD_B_v3.9.10.txt: 8205844aa131dc8fe397108bb3402fad5225a6a2c2436cf6035132986a77bc6d
- EXPORT_TAPE_v1_LEGACY_PASS_ONLY.txt: 95c570d231ca562e07eb311932f8c24422abafecb096dd7cbffba5e55d8751fd
- LEGACY_SAVEKIT_v1_THREAD_B_v3.9.10_FULLPP.txt: 6640f863af3d52bb7a8714a8f6a4c10de6db08d9ba0f95399cb27e3cd09e2ba4
- MEGABOOT_RATCHET_SUITE_v7.4.6-PROJECTS.md: e7fd622261d366755cf94f0361cbc5a556deb3d540571bc2750173fcee5886cb
- MEGA_BATCHES_v1.2_QIT_TOPOLOGY_VARIANCE_TERMS.txt: 147222df9c70fa220ee0564b3ccb06953e148c49b9fb0ef447c0be0708e010c7
- SIM_CATALOG_v1.3.md: 0875a516fe8ed7d7ca5724b6655d13c5b07eb4b580829e598dce97e833254748
- SIM_EVIDENCE_PACK_autogen_v1.txt: f7e5e5a1d0a18a5dcd4453bb66c7023241eda5ed33d7855e5da7853362ecdbed
- SIM_RUNBOOK_v1.3.md: f35dd45484d3896e0f129349ee82b91d383dd5764d5292d21d69f32ea4a4d8cb

## 5) Notes / audit log (append-only)

- <YYYY-MM-DD>: <what changed, what was accepted, what was rejected, what was parked, what to do next>

