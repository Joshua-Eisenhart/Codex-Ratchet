# Workspace Layout v1
Status: DRAFT / NONCANON
Date: 2026-02-20

## Purpose
Keep the repo lean, predictable, and auditable.
Avoid document sprawl by constraining where new artifacts may be written.

## Top-Level Directories (Contract)
- `core_docs/`
  - User-authored core documents and imports.
  - Read-only during engineering runs (no generated artifacts).
- `work/`
  - Legacy/active v2 machine surface (code + state + specs).
  - Treat as read-only during v3 spec rewrite unless explicitly migrating.
- `system_spec_pack_v2/`
  - First-draft v2 spec pack (input reference only).
  - Read-only (no generated artifacts).
- `system_v3/`
  - Current rewrite surface + tooling + runtime.
  - All new v3 artifacts must live here.
- `josh-flowmind-spec/`
  - External proposal pack (high-entropy reference).

## No-New-Roots Rule
No new top-level folders without an explicit naming + purpose decision.

## Allowed Write Targets (Default)
- `system_v3/specs/` (spec edits only)
- `system_v3/specs/reports/` (lint/audit reports)
- `system_v3/tools/` (tooling only)
- `system_v3/runtime/` (canonical runtime code; no generated run artifacts)
- `system_v3/a2_state/` (A2 persistent brain; fixed interface)
- `system_v3/a2_derived_indices_noncanonical/` (optional derived A2 helper indices; regenerable)
- `system_v3/runs/` (controlled run surfaces; append-only + shard)
- `system_v3/runs/_run_templates_v1/` (immutable run template assets)
- `system_v3/conformance/` (versioned fixture packs + expected outcomes)
