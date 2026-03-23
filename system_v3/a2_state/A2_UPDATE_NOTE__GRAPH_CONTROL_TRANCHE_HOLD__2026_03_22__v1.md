# A2 Update Note — Graph Control Tranche Hold

- date: `2026-03-22`
- surface_class: `DERIVED_A2`
- scope: `system_v4 graph/control-substrate line / controller-truth alignment`

What changed:

- the current graph/control sidecar tranche was re-audited for live admission:
  - `pyg-heterograph-projection-audit`
  - `control-graph-bridge-gap-auditor`
  - `control-graph-bridge-source-auditor`
  - `toponetx-projection-adapter-audit`
  - `survivor-kernel-bridge-backfill-audit`
  - `skill-kernel-link-seeding-policy-audit`
  - `clifford-edge-semantics-audit`
  - `edge-payload-schema-audit`
  - `edge-payload-schema-probe`
- all nine slices remain repo-held with emitted outputs
- all nine slices remain intentionally outside the active admitted skill registry and dispatch table

Meaning:

- this tranche is real support-side graph/control work, not fake or abandoned work
- it is still not live runtime capability
- the standing fence remains:
  - sidecar-only
  - read-only
  - non-training
  - no canonical graph replacement
  - no runtime mutation claim

Required continuity:

- front-door and controller surfaces should say explicitly that the tranche is held out of live admission for now
- no `A1` consequence is created by this hold
