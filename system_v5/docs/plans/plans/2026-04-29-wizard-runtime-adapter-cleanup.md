# Wizard Runtime Adapter Cleanup

Date: 2026-04-29

## Current Split

Active repo behavior should live in:

- `AGENTS.md`
- `CODEX.md` as Codex overlay/reference
- `system_v5/docs/plans/plans/2026-04-29-wizard-output-regression-checklist.md`

Current v3.4 packet is the active cohort (staged 2026-04-29):

- `MMM_WIZARD_CLEAN_SYSTEM_PACKET_v3_4/`

v3.3 packet assets retained at repo root as archive/provenance, not active:

- `MMM_WIZARD_CLEAN_SYSTEM_PACKET_v3_3/`
- `MMM_WIZARD_CLEAN_SYSTEM_PACKET_v3_3_DOWNLOADABLE.zip`
- `MMM_WIZARD_CLEAN_SYSTEM_PACKET_v3_3_DOWNLOADABLE.zip.sha256`

## Keep As Active Utilities

These scripts are useful because they enforce receipt truth or behavior checks without pretending to spawn workers:

- `scripts/codex_harness_adapter.py`
- `scripts/wizard_behavior_harness.py`
- `scripts/run_wizard_proof_manifest.py`

## Treat As Legacy Or Candidate Until Updated

These appear tied to older packet-generation or v2.7-style synthetic runs:

- `scripts/run_wizard_system.py`
- `scripts/package_wizard_candidate.py`
- `scripts/run_wizard_general_bakeoff.py`
- `scripts/refine_wizard_mmm_language.py`

Do not use legacy runner/package scripts as the live Wizard runtime unless they are updated to v3.4 and tested against the regression checklist.

