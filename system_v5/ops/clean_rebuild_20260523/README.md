# Clean Rebuild Lane - 2026-05-23

Status: clean-room rebuild workspace, not canonical formal-scout evidence.

This directory is for rerunning the stack after the mixed formal/informal
contamination wave. Artifacts here must not read from:

- `system_v5/grok_sim/`
- `system_v5/ops/formal_scouts/results/`
- `system_v5/ops/external_audits/`
- cross-lane synthesis docs

Initial rebuild policy:

1. Use `system_v5/READ ONLY Reference Docs/` and small inline fixtures.
2. Use torch for nonclassical/QIT checks.
3. Write receipts under this directory's `results/` subdirectory.
4. Keep outputs nonpromotional until the formal estate is explicitly reset.

