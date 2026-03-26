# Repo Layout — Codex Ratchet

> Canonical map of the repository structure. Updated 2026-03-26.

---

## Active Layers

```
/
├── core_docs/                  # A1 human-readable corpus + QIT sync cluster + C-layer docs
│   ├── QIT_GRAPH_*.md         # QIT graph front-door documentation
│   ├── C_LAYER_ARCHITECTURE.md # C1/C2/C3 external layer spec
│   └── a1_refined_Ratchet Fuel/ # A1 refined knowledge
│
├── system_v4/                  # Active system
│   ├── skills/                # Owner graph builders, sidecars, adapters, sync tools
│   ├── probes/                # SIMs, smoke tests, engine code, audits
│   │   └── a2_state/sim_results/ # ← CANONICAL SIM results path
│   ├── a2_state/              # A2 state: graphs, audit logs, doc index
│   │   └── graphs/            # Layer graphs, QIT engine graph, nested graph
│   ├── research/              # Research compiler specs
│   ├── tests/                 # Unit tests, fuzz tests
│   └── docs/                  # SIM catalog, axes docs
│
├── obsidian_vault/            # Ingested knowledge graph nodes (3000+)
│
├── .github/workflows/         # CI: lint, test, security
│
└── .gitattributes             # Line endings + LFS patterns (LFS not yet installed)
```

## Gitignored / External

```
├── work/                       # 3.7 GB — gitignored
│   ├── reference_repos/       # lev-os, pi-mono, etc
│   ├── lightrag_venv/         # LightRAG Python venv
│   ├── lightrag_smoke/        # LightRAG corpus + manifests
│   ├── mirofish/              # MiroFish clone (C3)
│   └── c_layer/               # C-layer sync manifests
│
├── archive/                    # 252 MB — gitignored
│   ├── mutants/               # Dead (179 MB, can delete)
│   ├── overlay_projector/     # Historical (67 MB)
│   └── zips/, threads/        # Small archives
│
├── system_v3/                  # 31 MB — gitignored (legacy, superseded)
│
└── system_v4/runtime_state/    # Regenerable runtime state — gitignored
```

## Key Paths

| What | Path |
|---|---|
| QIT Owner Graph | `system_v4/a2_state/graphs/qit_engine_graph_v1.json` |
| Nested Graph | `system_v4/a2_state/graphs/nested_graph_v1.json` |
| SIM Results (canonical) | `system_v4/probes/a2_state/sim_results/` |
| Owner Schemas | `system_v4/skills/qit_owner_schemas.py` |
| Graph Builder | `system_v4/skills/qit_engine_graph_builder.py` |
| Nested Builder | `system_v4/skills/nested_graph_builder.py` |
| Front-Door Sync | `core_docs/QIT_GRAPH_SYNC_README.md` |
| C-Layer Spec | `core_docs/C_LAYER_ARCHITECTURE.md` |
| Lev-OS Sync | `system_v4/skills/levos_skills_sync.py` |
| LightRAG Smoke | `system_v4/probes/lightrag_smoke_test.py` |

## Git Health Rules

1. **No files >500KB** in new commits without review
2. **PDFs, CSVs, .pages**: Will go through LFS after `brew install git-lfs`
3. **Regenerable state** (runtime_state, telemetry, sim_results): stays gitignored or committed selectively
4. **SIM results**: committed in batches, not individually per run
5. **Archive**: gitignored, local-only storage for historical artifacts
