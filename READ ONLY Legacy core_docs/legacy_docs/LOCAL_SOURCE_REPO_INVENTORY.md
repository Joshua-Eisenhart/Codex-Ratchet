# Local Source Repo Inventory

Last updated: 2026-03-21

## Purpose

This is the simple local-presence inventory for source repos and source families that matter to the Skill Source Corpus.

Canonical easy-to-find repo tree:

- [work/reference_repos/README.md](%USER_HOME%/Desktop/Codex%20Ratchet/work/reference_repos/README.md)

It exists because `A2` needs to know not only that a source is referenced, but also whether it is:

- actually cloned locally
- only present in `/tmp`
- only present outside the repo
- only present in docs/staging

## Presence Tiers

- `repo_local`: inside this workspace
- `home_local`: elsewhere on this machine
- `tmp_local`: in `/tmp`, non-durable
- `doc_only`: present only through docs / session logs / staging surfaces
- `url_only`: only referenced by URL

## Current Inventory

### Main workspace

- [Codex Ratchet](%USER_HOME%/Desktop/Codex%20Ratchet)
  - tier: `repo_local`
  - notes: main system repo
  - git remote: none configured
  - head: `a3e67a9`

- [work/reference_repos](%USER_HOME%/Desktop/Codex%20Ratchet/work/reference_repos)
  - tier: `repo_local`
  - notes: canonical easy-to-find tree for referenced external repos

### pi-mono

- [work/reference_repos/other/pi-mono](%USER_HOME%/Desktop/Codex%20Ratchet/work/reference_repos/other/pi-mono)
  - tier: `repo_local`
  - origin: local clone from `~/GitHub/pi-mono`
  - head: `3563cc4d`
  - notes: canonical organized copy for external source browsing

- [%USER_HOME%/Desktop/Codex Ratchet/work/audit_tmp/pi-mono](%USER_HOME%/Desktop/Codex%20Ratchet/work/audit_tmp/pi-mono)
  - tier: `repo_local`
  - size: about `600M`
  - notes: full git worktree in workspace temp area
  - origin: `https://github.com/badlogic/pi-mono.git`
  - head: `3563cc4d`
  - processing state: locally inspected and partly graphed, but still only partially integrated

- [%USER_HOME%/GitHub/pi-mono](%USER_HOME%/GitHub/pi-mono)
  - tier: `home_local`
  - notes: local clone outside workspace
  - origin: `https://github.com/badlogic/pi-mono.git`
  - head: `3563cc4d`
  - observed packages:
    - `agent`
    - `ai`
    - `coding-agent`
    - `mom`
    - `pods`
    - `tui`
    - `web-ui`

### lev-os/agents

- [work/reference_repos/lev-os/agents](%USER_HOME%/Desktop/Codex%20Ratchet/work/reference_repos/lev-os/agents)
  - tier: `repo_local`
  - origin: local clone from `/tmp/lev_os_agents`
  - head: `fd5191f`
  - notes: canonical organized copy for external source browsing

- [/tmp/lev_os_agents](/tmp/lev_os_agents)
  - tier: `tmp_local`
  - size: about `103M`
  - notes: real local checkout
  - origin: `https://github.com/lev-os/agents.git`
  - head: `fd5191f`
  - processing state: partly inspected, graphed in places, not active A2 or hot-path integrated
  - current observed skill counts:
    - `635` total `SKILL.md`
    - `61` curated runtime-tree skills
    - `574` `skills-db` library/mining skills
  - observed `skills/` subdirs: `48`

### lev-os/leviathan

- [work/reference_repos/lev-os/leviathan](%USER_HOME%/Desktop/Codex%20Ratchet/work/reference_repos/lev-os/leviathan)
  - tier: `repo_local`
  - origin: local clone from `/tmp/lev_os_leviathan`
  - head: `f256434`
  - notes: canonical organized copy for external source browsing

- [/tmp/lev_os_leviathan](/tmp/lev_os_leviathan)
  - tier: `tmp_local`
  - size: about `1.1G`
  - notes: real local checkout
  - origin: `https://github.com/lev-os/leviathan.git`
  - head: `f256434`
  - processing state: partly inspected, lightly adapted in one prompt-stack transplant, not active A2 or hot-path integrated
  - observed strong areas:
    - `workshop/analysis`
    - `workshop/intake`
    - `workshop/memory-integration`
    - `workshop/benchmarks`

### lev-os org root

- [lev-os](https://github.com/lev-os)
  - tier: `url_only`
  - notes: org-level family anchor, not a local checkout by itself

### Retooled External Methods

- [29 thing.txt](%USER_HOME%/Desktop/Codex%20Ratchet/core_docs/v4%20upgrades/29%20thing.txt)
  - tier: `repo_local`
  - notes: authoritative local source doc for the Retooled External Methods family
  - processing state: terminology corrected and subfamily split defined, but not yet converted method-by-method into live skill proof

### Karpathy sources

- [work/reference_repos/karpathy/autoresearch](%USER_HOME%/Desktop/Codex%20Ratchet/work/reference_repos/karpathy/autoresearch)
  - tier: `repo_local`
  - head: `32a1460`
- [karpathy/autoresearch](https://github.com/karpathy/autoresearch)
  - tier: `url_only`
- [work/reference_repos/karpathy/llm-council](%USER_HOME%/Desktop/Codex%20Ratchet/work/reference_repos/karpathy/llm-council)
  - tier: `repo_local`
  - head: `92e1fcc`
- [karpathy/llm-council](https://github.com/karpathy/llm-council)
  - tier: `url_only`
- [work/reference_repos/karpathy/llm.c](%USER_HOME%/Desktop/Codex%20Ratchet/work/reference_repos/karpathy/llm.c)
  - tier: `repo_local`
  - head: `f1e2ace`
- [karpathy/llm.c](https://github.com/karpathy/llm.c)
  - tier: `url_only`
- [work/reference_repos/karpathy/minbpe](%USER_HOME%/Desktop/Codex%20Ratchet/work/reference_repos/karpathy/minbpe)
  - tier: `repo_local`
  - head: `1acefe8`
- [karpathy/minbpe](https://github.com/karpathy/minbpe)
  - tier: `url_only`
- [work/reference_repos/karpathy/nanochat](%USER_HOME%/Desktop/Codex%20Ratchet/work/reference_repos/karpathy/nanochat)
  - tier: `repo_local`
  - head: `5019acc`
- [karpathy/nanochat](https://github.com/karpathy/nanochat)
  - tier: `url_only`
- [work/reference_repos/karpathy/nanoGPT](%USER_HOME%/Desktop/Codex%20Ratchet/work/reference_repos/karpathy/nanoGPT)
  - tier: `repo_local`
  - head: `3adf61e`
- [karpathy/nanoGPT](https://github.com/karpathy/nanoGPT)
  - tier: `url_only`

### External audit sources

- [work/reference_repos/external_audit/Context-Engineering](%USER_HOME%/Desktop/Codex%20Ratchet/work/reference_repos/external_audit/Context-Engineering)
  - tier: `repo_local`
  - origin: `https://github.com/davidkimai/Context-Engineering.git`
  - head: `6158def`
  - notes: context/state, persistence, and multi-field orchestration source probe
- [work/reference_repos/external_audit/spec-kit](%USER_HOME%/Desktop/Codex%20Ratchet/work/reference_repos/external_audit/spec-kit)
  - tier: `repo_local`
  - origin: `https://github.com/github/spec-kit.git`
  - head: `bf33980`
  - notes: executable-spec and plan/task coupling source probe
- [work/reference_repos/external_audit/superpowers](%USER_HOME%/Desktop/Codex%20Ratchet/work/reference_repos/external_audit/superpowers)
  - tier: `repo_local`
  - origin: `https://github.com/obra/superpowers.git`
  - head: `8ea3981`
  - notes: subagent workflow, review, and verification-discipline source probe
- [work/reference_repos/external_audit/mem0](%USER_HOME%/Desktop/Codex%20Ratchet/work/reference_repos/external_audit/mem0)
  - tier: `repo_local`
  - origin: `https://github.com/mem0ai/mem0.git`
  - head: `ec326f0`
  - notes: scoped memory-sidecar, mutation-history, and export/import source probe; not a canonical A2/A1 memory replacement

### EverMem / EverMind / MSA

- [work/reference_repos/EverMind-AI/EverMemOS](%USER_HOME%/Desktop/Codex%20Ratchet/work/reference_repos/EverMind-AI/EverMemOS)
  - tier: `repo_local`
  - origin: `https://github.com/EverMind-AI/EverMemOS.git`
  - head: `3c9a2d0`
- [work/reference_repos/EverMind-AI/MSA](%USER_HOME%/Desktop/Codex%20Ratchet/work/reference_repos/EverMind-AI/MSA)
  - tier: `repo_local`
  - origin: `https://github.com/EverMind-AI/MSA.git`
  - head: `8631c9d`
- EverMem / EverMind / MSA family
  - tier: `repo_local`
  - notes: EverMemOS and MSA are now locally present in the canonical reference tree

### Graph toolchain and graph artifacts

- base graph stack
  - tier: `repo_local`
  - notes: canonical graph substrate is `pydantic + networkx + JSON + GraphML export`, with live code rooted in `system_v4`
- [.venv_spec_graph](%USER_HOME%/Desktop/Codex%20Ratchet/.venv_spec_graph)
  - tier: `repo_local`
  - notes: graph/spec sidecar venv for live PyG, TopoNetX, HyperNetX, XGI, clifford, kingdon, and quaternion-sidecar runs on top of the base graph stack
  - observed packages:
    - `torch`
    - `torch-geometric`
    - `toponetx`
    - `hypernetx`
    - `xgi`
    - `clifford`
    - `kingdon`
    - `pyquaternion`
- [system_v4/a2_state/graphs/nested_graph_v1.json](%USER_HOME%/Desktop/Codex%20Ratchet/system_v4/a2_state/graphs/nested_graph_v1.json)
  - tier: `repo_local`
  - notes: populated nested graph artifact built from the layered owner graphs; no longer empty
- [system_v4/skills/nested_graph_builder.py](%USER_HOME%/Desktop/Codex%20Ratchet/system_v4/skills/nested_graph_builder.py)
  - tier: `repo_local`
  - notes: live nested-graph builder over the layer-set graph artifacts
- [system_v4/skills/skill_kernel_bridge_builder.py](%USER_HOME%/Desktop/Codex%20Ratchet/system_v4/skills/skill_kernel_bridge_builder.py)
  - tier: `repo_local`
  - notes: live skill/kernel bridge-forming builder; actual graph-formation operator, not just audit scaffolding
- [system_v4/skills/v4_graph_builder.py](%USER_HOME%/Desktop/Codex%20Ratchet/system_v4/skills/v4_graph_builder.py)
  - tier: `repo_local`
  - notes: current owner graph builder using `networkx` with GraphML export
- [system_v4/a2_understanding/graph_models.py](%USER_HOME%/Desktop/Codex%20Ratchet/system_v4/a2_understanding/graph_models.py)
  - tier: `repo_local`
  - notes: current typed graph model layer using `pydantic`
- [system_v4/a2_state/graphs/a2_high_intake_graph_v1.json](%USER_HOME%/Desktop/Codex%20Ratchet/system_v4/a2_state/graphs/a2_high_intake_graph_v1.json)
  - tier: `repo_local`
  - notes: high-intake owner graph layer for nested graph assembly
- [system_v4/a2_state/graphs/a2_mid_refinement_graph_v1.json](%USER_HOME%/Desktop/Codex%20Ratchet/system_v4/a2_state/graphs/a2_mid_refinement_graph_v1.json)
  - tier: `repo_local`
  - notes: mid-refinement owner graph layer for nested graph assembly
- [system_v4/a2_state/graphs/a2_low_control_graph_v1.json](%USER_HOME%/Desktop/Codex%20Ratchet/system_v4/a2_state/graphs/a2_low_control_graph_v1.json)
  - tier: `repo_local`
  - notes: low-control owner graph layer for nested graph assembly
- [system_v4/a2_state/graphs/a1_jargoned_graph_v1.json](%USER_HOME%/Desktop/Codex%20Ratchet/system_v4/a2_state/graphs/a1_jargoned_graph_v1.json)
  - tier: `repo_local`
  - notes: A1-facing owner graph layer for nested graph assembly
- [system_v4/a2_state/graphs/promoted_subgraph.json](%USER_HOME%/Desktop/Codex%20Ratchet/system_v4/a2_state/graphs/promoted_subgraph.json)
  - tier: `repo_local`
  - notes: promoted cross-layer graph used in nested graph assembly

### OpenClaw-RL / next-state signals

- [OpenClaw-RL paper](https://arxiv.org/abs/2603.10165)
  - tier: `url_only`
  - notes: source paper now processed into the external reference note and bounded audit slice
- [Gen-Verse/OpenClaw-RL](https://github.com/Gen-Verse/OpenClaw-RL)
  - tier: `url_only`
  - notes: source repo recorded in corpus/tracker surfaces; local clone attempt into `work/reference_repos/Gen-Verse/OpenClaw-RL` is not yet verified as a stable checkout

### Verification and other references

- [work/reference_repos/other/z3](%USER_HOME%/Desktop/Codex%20Ratchet/work/reference_repos/other/z3)
  - tier: `repo_local`
  - head: `09c13a7`
- [work/reference_repos/deepmind/alphageometry](%USER_HOME%/Desktop/Codex%20Ratchet/work/reference_repos/deepmind/alphageometry)
  - tier: `repo_local`
  - head: `6777cb5`
- [work/reference_repos/other/AutoResearchClaw](%USER_HOME%/Desktop/Codex%20Ratchet/work/reference_repos/other/AutoResearchClaw)
  - tier: `repo_local`
  - head: `3347481`
- [work/reference_repos/other/dreamcoder-ec](%USER_HOME%/Desktop/Codex%20Ratchet/work/reference_repos/other/dreamcoder-ec)
  - tier: `repo_local`
  - head: `cb0e63f`

## Working Rule

Before claiming a repo family is truly available for integration, record its presence tier here.

That prevents these bad conflations:

- URL known = local repo present
- tmp clone = durable source
- session log mention = local checkout
- registry row = usable runtime integration

Also keep these separate:

- local `Leviathan v3.2` corpus inside this repo
- external `lev-os/leviathan` checkout in `/tmp`
- external `lev-os/agents` checkout in `/tmp`
