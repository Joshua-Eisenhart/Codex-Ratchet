---
title: Wizard v4.3 MMM Reservoir
created: 2026-06-13
updated: 2026-06-13
packet: v4.3
authority_status: canonical-runtime-pointer
type: mmm_index
framing: current
---

# Wizard v4.3 MMM Reservoir

This folder is the v4.3-owned MMM reservoir for `../packet-v4-3-current/`.

## Boot surfaces

- `FULL_MMM_v4_3.md` — full main-agent salience reservoir.
- `COMPACT_MMM_v4_3.md` — compact main-agent salience reservoir when context is tight.
- `mini/MEMBER_MINI_MMM_REGISTRY_v4_3.md` — route/member mini-MMM registry.

## Source lineage

These files are seeded from the v4.2 MMM reservoir and copied into v4.3 so current Wizard no longer has to route through `packet-v4-2-current/` for active MMM boot.

Historical v4.1/v4.2 slice filenames and phrases may remain inside copied mini-MMM material as provenance. Retuning every mini slice is a later behavior-calibration task. The active boot path is still v4.3 because the files live here and the manifest/read order points here.

## Candidate overlays

`SALIENCY_TRANCHE_*` files are reference-only overlays unless a later behavior/conformance pass admits them as boot material.
