# System V4 Specification Manifest

## System Boundary Definitions

### system_v3 — Legacy Runtime
- **Role**: Bootpack kernel, A0 compiler, A1 bridge/strategy, sim engine, B-adjudicator
- **Specs**: `system_v3/specs/` — 88 numbered spec files (00–79)
- **Runtime**: `system_v3/runtime/bootpack_b_kernel_v1/`
- **State**: `system_v3/a2_state/` (canonical brain: memory.jsonl, doc_index.json, a1_brain.jsonl)
- **Status**: Stable. Not under active development. Referenced by v4 for bridge operations.

### system_v4 — Graph-Native Skill System
- **Role**: Skill registry, graph refinery, nested/layer graphs, probes, operators, intent control
- **Specs**: `system_v4/specs/` (this directory)
- **Skills**: `system_v4/skills/` — 131 skill modules, 123 registered in SkillRegistry
- **Tests**: `system_v4/tests/` — 93 test files
- **Runners**: `system_v4/runners/` — 18 entry-point scripts
- **Probes**: `system_v4/probes/` — 14 graph analysis/verification scripts
- **Graphs**: `system_v4/a2_state/graphs/` — 12 graph files (53K nodes, 159K edges)
- **State**: `system_v4/a2_state/` — live runtime state (intent control, daemon, session ledger, memory)
- **Skill Specs**: `system_v4/skill_specs/` — 88 per-skill spec directories
- **Status**: Active development. Primary system.

### system_v5 — Placeholder
- **Role**: Not yet defined
- **Contents**: 1 test file (`test_nested_graph_worker_chain_smoke.py`)
- **Status**: Empty. Not started.

---

## V4 Spec Index

| # | File | Scope |
|---|------|-------|
| 00 | `00_MANIFEST.md` | This file — system boundaries and spec index |
| 01 | `01_V4_SYSTEM_SPEC.md` | Core v4 system specification |
| 02 | `02_V4_BUILD_ORDER.md` | Build sequence and dependencies |
| 03 | `03_V4_SKILL_CLUSTER_SPEC.md` | Skill cluster definitions |
| 04 | `04_V4_IMPORTED_SKILL_CLUSTER_MAP.md` | External skill source mapping |
| 05 | `05_V4_SPEC_AUDIT.md` | Spec conformance audit results |
| 06 | `06_PIPELINE_ARCHITECTURE_REFERENCE.md` | Pipeline/refinery architecture |

---

## V4 Directory Structure

```text
system_v4/
  specs/                 7 spec files (this directory)
  skills/              131 .py skill modules
  tests/                93 test files
  runners/              18 runner scripts
  probes/               14 probe/analysis scripts
  skill_specs/          88 per-skill spec directories
  docs/                  9 planning/tracking docs
  a2_state/
    graphs/                  12 graph files (DVC-tracked)
    audit_logs/             201 reports
    launch_bundles/          20 nested graph build dirs
    thread_context_extracts/  9 context files
    process_docs/             9 reference/process docs (clean boundary)
    session_logs_archive/   120 historical session traces (archived)
    cartridges/               1 cartridge
    quarantine/               2 state files
    experiments/              2 files
    stack_sessions/           1 dir
    [live state files]        ~10 JSON/JSONL files
  a1_state/             16 files (A1 brain, routing, eval, rosetta)
  a2_understanding/      5 files
  runtime_state/        61 batch output files
```

## Known Issues

1. `nested_graph_v1.json` is empty (0 nodes, 0 edges) — needs rebuild
2. 4 graph invariant test failures (duplicate edges, subset violation, edge count mismatch)
