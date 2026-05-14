# V5 Clean Rebuild Charter

Status: working rule
Scope: new SIM/QIT/geometric-constraint-manifold work

## Decision

Use `system_v4/probes` as a reference corpus and evidence mine. Build clean new
work in `system_v5`.

This means `system_v4/probes` is not the default write target for exploration,
generated waves, provider proposals, formal scouts, or rough manifold towers.

## Why

`system_v4/probes` contains useful formal legos, but it is also a large mixed
surface:

- canonical/reference sims;
- generated weak fixtures;
- source-only files;
- unlinked result files;
- naming-contaminated files;
- stale or deleted tracked files;
- admission receipts with mixed claim ceilings.

The clean rebuild needs smaller, auditable v5 surfaces with explicit contracts.

## Authority Split

### V4 Reference Corpus

Use `system_v4/probes` for:

- finding existing formal legos;
- importing real callables through `importlib`;
- checking prior result receipts;
- mining graveyard variants;
- mapping candidate tower layers to existing math.

Do not use `system_v4/probes` for:

- new exploratory generated waves;
- provider-generated proposals;
- formal-scout manifold assemblies;
- rough tower experiments;
- new files with rosetta, axis, engine, type, or target-system names.

### V5 Clean Surfaces

Use these v5 locations:

| Surface | Purpose |
|---|---|
| `system_v5/docs/` | contracts, plans, indexes, support docs |
| `system_v5/ops/formal_scouts/` | exploratory but receipt-bound tower harnesses |
| `system_v5/ops/quarantine/` | generated or legacy material that should not contaminate clean work |
| `system_v5/ops/queue_cleanup/` | cleanup plans, inventories, and batch manifests |
| `system_v5/evidence/` | curated evidence manifests and clean result indexes |
| `system_v5/grok_sim/` | separate informal proposal/failure-pattern lab only |

## New Work Rule

Every new v5 executable or result must answer:

1. What math is being simulated?
2. Which v4 reference files or v5 clean files does it call?
3. What observable is computed?
4. What is the pass/fail predicate?
5. What nearby variants die?
6. What is the claim ceiling?
7. Where is the result receipt?
8. Why is this not being written into `system_v4/probes`?

## Naming Rule

Names are definitions. New executable names must describe the math directly.

Avoid in new executable names:

- `axis`;
- `engine`;
- `gstack`;
- `rosetta`;
- `type1` / `type2`;
- personal/domain labels;
- target-system labels.

Historical files may keep old names until reused. When a historical file is
reused, either wrap it from v5 with a clean name or rename it with a manifest.

## Probe Folder Cleanup Rule

Do not broadly delete or rename `system_v4/probes`.

First create inventories:

- tracked modified/deleted files;
- untracked generated files;
- naming-contaminated files;
- admitted/reference files;
- source-only files;
- result-only or unlinked result files.

Then move or rename only by manifest, with before/after counts and a receipt.

## Formal-Scout Rule

Geometric-constraint-manifold exploration belongs in:

`system_v5/ops/formal_scouts/`

Formal scouts may import v4 callables but must write v5 receipts and must set:

- `classification: formal_scout`;
- `promotion_allowed: false`;
- non-empty `claim_ceiling`;
- non-empty graveyard companions.

Formal scouts can guide promotion but cannot promote themselves.
