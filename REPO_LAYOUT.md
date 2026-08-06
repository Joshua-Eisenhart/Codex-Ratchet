# Repo Layout — Codex Ratchet

> Canonical map of the repository structure. Updated 2026-08-06 for v9.

V9 is a boundary and integration overlay. It does not erase the v4-v8 corpus;
it identifies independent products, current entry points, bridge contracts, and
the evidence ceiling of migrated sources.

## V9 authority overlay

```
/
├── system_v9/                 # Stack manifest, CR boundary, bridge contracts, verifier
├── constraint_box/            # Lean deterministic CB product; exact five-tool core
├── claimgate_plugin/          # Canonical ClaimGate product
├── claimgate/                 # Legacy/reference ClaimGate material
├── sim_engines/               # Portable install profiles, tool registry, live doctor
├── holodeck/                  # Independent world-model/perception product scaffold
├── system_v4/ ... system_v8/  # Historical source/evidence strata, not auto-promoted
└── scripts/                   # Shared repository operations and legacy runners
```

The v9 product boundaries are literal:

| Product | Owns | Does not own |
|---|---|---|
| ConstraintBox | deterministic orchestration and its five-tool Python core | ClaimGate, Julia, JAX, PyTorch, QIT, Holodeck |
| ClaimGate | claim admission and evidence policy | simulation or orchestration |
| Sim Engines | external numerical, symbolic, graph, QIT, and formal runtimes | claim admission or CR doctrine |
| Codex Ratchet | schedules, candidate construction, and system-level protocols | the internals of CB or engines |
| Holodeck | trainable world-model and perception surfaces | QIT-engine or CR authority |

Every cross-product call must route through `system_v9/bridges/`. Direct legacy
imports remain migration debt until a bridge has its own test and receipt.

The sections below describe the historical v4/v5 layout retained for source
continuity.

---

## Root

```
/
├── README.md                   # Entry point
├── CLAUDE.md                   # Session instructions (operating principles, lane rules)
├── REPO_LAYOUT.md              # This file
├── Makefile                    # Build + run entrypoints (defines PYTHON env)
├── LICENSE
├── pyproject.toml / setup.cfg / package.json
├── requirements-*.txt          # Dep pins (core, dev, runtime, security, sim-stack)
├── .gitignore / .gitattributes / .dvcignore
├── imessage_bot.py             # Active iMessage integration
└── telegram_bot.py             # Active Telegram integration
```

## Docs — `system_v5/`

All human-readable docs live here.

```
system_v5/
├── docs/
│   └── plans/                  # Handoffs, coverage matrices, runner scripts, lane specs
├── docs/                   # Numbered research docs (00–17+) + enforcement/contracts
│   ├── ENFORCEMENT_AND_PROCESS_RULES.md   ← read first
│   ├── LLM_CONTROLLER_CONTRACT.md         ← read first
│   ├── LEGO_SIM_CONTRACT.md               ← read first
│   ├── AGENT_WORKFLOW_AND_BOOT_ARCHITECTURE.md
│   └── plans/
├── READ ONLY Reference Docs/   # Axes, entropic monism, engine schedules
└── tests/                      # System-level test harness
```

## Active system code — `system_v4/`

```
system_v4/
├── probes/                     # SIMs (Lane A capability-probes, Lane B classical_baseline, Lane C canonical)
│   ├── SIM_TEMPLATE.py         # Required starting point for every sim
│   └── a2_state/sim_results/   # ← CANONICAL SIM results
├── skills/                     # Graph builders, sidecars, adapters, sync tools
├── a2_state/graphs/            # QIT engine graph, nested graph, layer graphs
├── research/                   # Research compiler specs
├── tests/                      # Unit + fuzz tests
└── runtime_state/              # Gitignored, regenerable
```

## Tooling — `scripts/`

```
scripts/
├── overnight_two_runner.sh     # Two-lane runner
├── queue_claim.py              # Atomic O_EXCL queue claim
├── seed_queue.py / claim_lane.py
├── lint_sim_contract.py        # C1–C6 SIM contract gate
├── check_classification.py / check_witnesses.py
├── verify_load_bearing_has_capability_probe.py
├── divergence_index.py
├── classical_baseline_report.py
└── lane_b_coverage_matrix.py
```

## Runtime output — `overnight_logs/`

Per-run artifacts: NDJSON events, heartbeats, tool-capability state, per-worker logs, queue manifests.

## Gitignored / local-only

```
├── work/                       # Large scratch, audit temp, reference repos
├── archive/                    # Historical artifacts (incl. loose_root_files_2026-04-14/)
├── system_v3/                  # Legacy, superseded
├── obsidian_vault/             # Ingested knowledge graph nodes
└── system_v4/runtime_state/    # Regenerable
```

## Key paths

| What | Path |
|---|---|
| Read-first docs | `system_v5/docs/{ENFORCEMENT_AND_PROCESS_RULES,LLM_CONTROLLER_CONTRACT,LEGO_SIM_CONTRACT}.md` |
| Sim template | `system_v4/probes/SIM_TEMPLATE.py` |
| Sim results | `system_v4/probes/a2_state/sim_results/` |
| QIT owner graph | `system_v4/a2_state/graphs/qit_engine_graph_v1.json` |
| Nested graph | `system_v4/a2_state/graphs/nested_graph_v1.json` |
| Overnight runner | `scripts/overnight_two_runner.sh` |
| Runner logs | `overnight_logs/` |

## Rules

1. **No random files at root.** Root = entry-point metadata only.
2. **No `docs/` or `docs/` at root.** Those live under `system_v5/`.
3. **Sim results are never touched by hand.** Written only by sim probes.
4. **Loose scratch → `archive/`**, not root.
5. **Every new sim starts from `system_v4/probes/SIM_TEMPLATE.py`** and must pass `scripts/lint_sim_contract.py`.
