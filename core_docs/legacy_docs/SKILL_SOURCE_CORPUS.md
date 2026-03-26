# Skill Source Corpus

Last updated: 2026-03-21

## What This Is

This is the umbrella corpus for the broad source material we keep trying to turn into:

- skills
- operators
- adapters
- skill clusters
- graph identities
- runtime integrations

This is not one source doc.
It is not only the things mentioned most recently.
It is the growing set of repos, docs, method corpora, processed internal corpora, runtime substrate files, and imported skill corpora that should feed system skill building.

Front-door companion surfaces:

- [REPO_SKILL_INTEGRATION_TRACKER.md](/home/ratchet/Desktop/Codex%20Ratchet/REPO_SKILL_INTEGRATION_TRACKER.md)
- [SKILL_CANDIDATES_BACKLOG.md](/home/ratchet/Desktop/Codex%20Ratchet/SKILL_CANDIDATES_BACKLOG.md)
- [LOCAL_SOURCE_REPO_INVENTORY.md](/home/ratchet/Desktop/Codex%20Ratchet/LOCAL_SOURCE_REPO_INVENTORY.md)
- [SYSTEM_SKILL_BUILD_PLAN.md](/home/ratchet/Desktop/Codex%20Ratchet/SYSTEM_SKILL_BUILD_PLAN.md)
- [A2_SKILL_SOURCE_CORPUS_OPERATING_MODEL.md](/home/ratchet/Desktop/Codex%20Ratchet/A2_SKILL_SOURCE_CORPUS_OPERATING_MODEL.md)
- [A2_V4_RECOVERY_AUDIT.md](/home/ratchet/Desktop/Codex%20Ratchet/A2_V4_RECOVERY_AUDIT.md)
- [work/reference_repos/README.md](/home/ratchet/Desktop/Codex%20Ratchet/work/reference_repos/README.md)

Important rules:

- no single source doc stands in for the whole corpus
- [lev_nonclassical_runtime_design_audited.md](/home/ratchet/Desktop/Codex%20Ratchet/core_docs/v4%20upgrades/lev_nonclassical_runtime_design_audited.md) is an audited / reorganized rendering of the same `Retooled External Methods` family rooted in [29 thing.txt](/home/ratchet/Desktop/Codex%20Ratchet/core_docs/v4%20upgrades/29%20thing.txt), not an independent second method source
- [29 thing.txt](/home/ratchet/Desktop/Codex%20Ratchet/core_docs/v4%20upgrades/29%20thing.txt) remains the literal source filename, but the preferred system term is `Retooled External Methods`
- being in this corpus does not mean something is already integrated or live

## Current bounded source-family selection

- `SKILL_CLUSTER::context-spec-workflow-memory` now has a first bounded landed slice:
  - `a2-context-spec-workflow-pattern-audit-operator`
  - and a second bounded landed selector slice:
    - `a2-context-spec-workflow-follow-on-selector-operator`
  - and a third bounded landed continuity-shell slice:
    - `a2-append-safe-context-shell-audit-operator`
  - and a fourth bounded landed post-shell selector slice:
    - `a2-context-spec-workflow-post-shell-selector-operator`
  - current next step is `hold_cluster_after_append_safe_shell`
  - first standby follow-on if explicitly reopened later is `a2-executable-spec-coupling-audit-operator`
  - `scoped_memory_sidecar` remains blocked behind current EverMem/backend reachability
- `SKILL_CLUSTER::karpathy-meta-research-runtime` now has a first bounded landed slice:
  - `a2-autoresearch-council-runtime-proof-operator`
  - current next step: `hold_first_slice_as_runtime_proof_only`
- current selector result:
  - no bounded source-family lane is currently eligible for explicit reselection
- there is no current bounded fallback while the other non-lev lanes remain held

## Column Guide

- `corpus_state`: `saved`, `partial`, `undercaptured`, or `missing`
- `integration_state`: `saved`, `graphed`, `registry`, `runtime`, `partial`, or `broken`
- `local_presence`: `repo_local`, `home_local`, `tmp_local`, `doc_only`, or `url_only`

## Master Registry

| Corpus ID | Label | Source Kind | Primary Source | Local Presence | Corpus State | Integration State | Target Skill Family / System Role | Evidence / Next Action |
|---|---|---|---|---|---|---|---|---|
| `OWNER::REQ_LEDGER` | `system_v3` requirements ledger | `owner_law` | [01_REQUIREMENTS_LEDGER.md](/home/ratchet/Desktop/Codex%20Ratchet/system_v3/specs/01_REQUIREMENTS_LEDGER.md) | `repo_local` | `saved` | `saved` | owner-law grounding for `v4` | keep indexed in canonical A2 and keep standing A2 brain aligned |
| `OWNER::OWNERSHIP_MAP` | `system_v3` ownership map | `owner_law` | [02_OWNERSHIP_MAP.md](/home/ratchet/Desktop/Codex%20Ratchet/system_v3/specs/02_OWNERSHIP_MAP.md) | `repo_local` | `saved` | `saved` | owner-law grounding for A2/A1 write boundaries | keep indexed in canonical A2 and keep standing A2 brain aligned |
| `OWNER::A2_OPERATIONS` | A2 operations law | `owner_law` | [07_A2_OPERATIONS_SPEC.md](/home/ratchet/Desktop/Codex%20Ratchet/system_v3/specs/07_A2_OPERATIONS_SPEC.md) | `repo_local` | `saved` | `saved` | A2 persistent-brain law | keep indexed in canonical A2 and use as boot law |
| `OWNER::A2_PERSISTENT_BRAIN` | A2 persistent-brain contract | `owner_law` | [19_A2_PERSISTENT_BRAIN_AND_CONTEXT_SEAL_CONTRACT.md](/home/ratchet/Desktop/Codex%20Ratchet/system_v3/specs/19_A2_PERSISTENT_BRAIN_AND_CONTEXT_SEAL_CONTRACT.md) | `repo_local` | `saved` | `saved` | persistent-brain law for memory/seal/retention | keep indexed in canonical A2 and use as schema target |
| `BOOT::A2_BOOT_READ_ORDER` | A2 boot read order | `boot_surface` | [A2_BOOT_READ_ORDER__CURRENT__v1.md](/home/ratchet/Desktop/Codex%20Ratchet/system_v3/a2_state/A2_BOOT_READ_ORDER__CURRENT__v1.md) | `repo_local` | `saved` | `saved` | bounded A2 boot path | keep indexed and refresh when front-door corpus changes |
| `BOOT::A2_KEY_CONTEXT_APPEND` | A2 key context append log | `boot_surface` | [A2_KEY_CONTEXT_APPEND_LOG__v1.md](/home/ratchet/Desktop/Codex%20Ratchet/system_v3/a2_state/A2_KEY_CONTEXT_APPEND_LOG__v1.md) | `repo_local` | `saved` | `partial` | recurring context retention for this whole lane | keep corrective updates current so stale truths do not persist |
| `BOOT::A2_SKILL_SOURCE_INTAKE` | A2 skill-source intake procedure | `boot_surface` | [A2_SKILL_SOURCE_INTAKE_PROCEDURE__CURRENT__v1.md](/home/ratchet/Desktop/Codex%20Ratchet/system_v3/a2_state/A2_SKILL_SOURCE_INTAKE_PROCEDURE__CURRENT__v1.md) | `repo_local` | `saved` | `partial` | corpus-to-A2 intake bridge | direct-index front-door corpus docs and keep procedure current |
| `METHOD_CORPUS::RETOOLED_EXTERNAL_METHODS` | Retooled External Methods | `method_bundle` | [29 thing.txt](/home/ratchet/Desktop/Codex%20Ratchet/core_docs/v4%20upgrades/29%20thing.txt) | `repo_local` | `saved` | `graphed` | primary method-to-skill conversion source | canonical source file for the 29-method family; keep method-level conversion backlog visible instead of flattening to one noun |
| `DOC::LEV_NONCLASSICAL_RUNTIME_DESIGN` | Lev nonclassical runtime design (audited rendering) | `architecture_note` | [lev_nonclassical_runtime_design_audited.md](/home/ratchet/Desktop/Codex%20Ratchet/core_docs/v4%20upgrades/lev_nonclassical_runtime_design_audited.md) | `repo_local` | `saved` | `partial` | audited / reorganized rendering of the same Retooled External Methods family | treat as a structured derivative of `29 thing.txt`, useful for read order and implementation framing, not as a distinct second method corpus |
| `DOC::LEVIATHAN_V3_2_LOCAL` | Leviathan v3.2 local corpus | `doc` | [Leviathan v3.2 word.txt](/home/ratchet/Desktop/Codex%20Ratchet/core_docs/a2_feed_high%20entropy%20doc/Leviathan%20v3.2%20word.txt) | `repo_local` | `saved` | `partial` | local JP/Leviathan source grounding | keep distinct from external `lev-os/leviathan` repo |
| `DOC::HOLODECK_WORKSHOP_EXPORT` | Holodeck memory / world-model workshop export | `doc` | [holodeck docs.md](/home/ratchet/Desktop/Codex%20Ratchet/core_docs/a2_feed_high%20entropy%20doc/holodeck%20docs.md) | `repo_local` | `saved` | `undercaptured` | memory / world-model workshop source | promote into tracker and backlog explicitly |
| `FAMILY::BOOTPACK_AUTHORITY` | Bootpack / EM / external handoff docs | `doc_family` | [BOOTPACK_THREAD_B_v3.9.13.md](/home/ratchet/Desktop/Codex%20Ratchet/core_docs/upgrade%20docs/BOOTPACK_THREAD_B_v3.9.13.md) | `repo_local` | `saved` | `undercaptured` | bootpack authority, external model handoff, rosetta bundle source | keep this family explicit instead of leaving it in entropy piles |
| `CORPUS::LOCAL_LEVIATHAN_V3_2_PROCESSED` | local Leviathan v3.2 processed corpus | `processed_internal_corpus` | [system_v3](/home/ratchet/Desktop/Codex%20Ratchet/system_v3) | `repo_local` | `saved` | `partial` | processed internal Lev/JP source layer | keep separate from external `lev-os` repos |
| `CORPUS::LEV_OS_AGENTS_CURATED` | `lev-os/agents` curated skill corpus | `imported_skill_corpus` | [skills](/home/ratchet/Desktop/Codex%20Ratchet/work/reference_repos/lev-os/agents/skills) | `repo_local` | `saved` | `partial` | imported skill corpus for intake/build/workflow/research clusters | `61` curated skills; next bounded lev promotion is now being selected through a repo-held promotion audit |
| `CORPUS::LEV_OS_AGENTS_LIBRARY` | `lev-os/agents` library skill corpus | `imported_skill_corpus` | [skills-db](/home/ratchet/Desktop/Codex%20Ratchet/work/reference_repos/lev-os/agents/skills-db) | `repo_local` | `saved` | `partial` | mining corpus for patterns, verification, diagnosis, system reasoning | `574` library skills; mine patterns, do not import flat |
| `REPO::LEV_OS_LEVIATHAN` | `lev-os/leviathan` | `repo` | [work/reference_repos/lev-os/leviathan](/home/ratchet/Desktop/Codex%20Ratchet/work/reference_repos/lev-os/leviathan) | `repo_local` | `saved` | `partial` | outside wrapper, orchestration, memory-support mine | first bounded continuity slice now exists as `outer-session-ledger`; keep separate from local processed Leviathan corpus |
| `FAMILY::KARPATHY` | Karpathy source family | `repo_family` | [work/reference_repos/karpathy](/home/ratchet/Desktop/Codex%20Ratchet/work/reference_repos/karpathy) | `repo_local` | `saved` | `partial` | research, council, minimal-core, tokenizer, runtime pattern source | keep repo-level entries explicit below |
| `REPO::AUTORESEARCH` | `karpathy/autoresearch` | `repo` | [work/reference_repos/karpathy/autoresearch](/home/ratchet/Desktop/Codex%20Ratchet/work/reference_repos/karpathy/autoresearch) | `repo_local` | `saved` | `registry` | meta-skill search / research operator source | make live discovery honest and keep runtime proof explicit |
| `REPO::LLM_COUNCIL` | `karpathy/llm-council` | `repo` | [work/reference_repos/karpathy/llm-council](/home/ratchet/Desktop/Codex%20Ratchet/work/reference_repos/karpathy/llm-council) | `repo_local` | `saved` | `registry` | deliberation / adjudication operator source | make live discovery honest and keep runtime proof explicit |
| `REPO::NANOCHAT` | `karpathy/nanochat` | `repo` | [work/reference_repos/karpathy/nanochat](/home/ratchet/Desktop/Codex%20Ratchet/work/reference_repos/karpathy/nanochat) | `repo_local` | `saved` | `partial` | controller and chat-shell pattern source | keep as source family member instead of dropping it |
| `REPO::NANOGPT` | `karpathy/nanoGPT` | `repo` | [work/reference_repos/karpathy/nanoGPT](/home/ratchet/Desktop/Codex%20Ratchet/work/reference_repos/karpathy/nanoGPT) | `repo_local` | `saved` | `partial` | minimal-core model/runtime pattern source | keep as source family member instead of dropping it |
| `REPO::LLM_C` | `karpathy/llm.c` | `repo` | [work/reference_repos/karpathy/llm.c](/home/ratchet/Desktop/Codex%20Ratchet/work/reference_repos/karpathy/llm.c) | `repo_local` | `saved` | `undercaptured` | low-level runtime/minimal-core pattern source | promote from inventory into tracker/backlog explicitly |
| `REPO::MINBPE` | `karpathy/minbpe` | `repo` | [work/reference_repos/karpathy/minbpe](/home/ratchet/Desktop/Codex%20Ratchet/work/reference_repos/karpathy/minbpe) | `repo_local` | `saved` | `undercaptured` | tokenizer / boundary / compression pattern source | promote from inventory into tracker/backlog explicitly |
| `REPO::CONTEXT_ENGINEERING` | `davidkimai/Context-Engineering` | `repo` | [work/reference_repos/external_audit/Context-Engineering](/home/ratchet/Desktop/Codex%20Ratchet/work/reference_repos/external_audit/Context-Engineering) | `repo_local` | `saved` | `partial` | append-safe context/state, persistence, protocol-shell, and multi-field orchestration source | local checkout verified at `6158def`; mine structured state, persistence, and hierarchical orchestration patterns without admitting field/quantum rhetoric as owner-law |
| `REPO::SPEC_KIT` | `github/spec-kit` | `repo` | [work/reference_repos/external_audit/spec-kit](/home/ratchet/Desktop/Codex%20Ratchet/work/reference_repos/external_audit/spec-kit) | `repo_local` | `saved` | `partial` | spec-driven / executable-spec / plan-task coupling source | local checkout verified at `bf33980`; mine spec/plan/task and spec-runtime coupling patterns without replacing Ratchet owner-law or A2 |
| `REPO::SUPERPOWERS` | `obra/superpowers` | `repo` | [work/reference_repos/external_audit/superpowers](/home/ratchet/Desktop/Codex%20Ratchet/work/reference_repos/external_audit/superpowers) | `repo_local` | `saved` | `partial` | skill workflow, subagent review, and verification-discipline source | local checkout verified at `8ea3981`; mine skill/workflow/testing discipline without importing plugin/marketplace assumptions wholesale |
| `REPO::MEM0` | `mem0ai/mem0` | `repo` | [work/reference_repos/external_audit/mem0](/home/ratchet/Desktop/Codex%20Ratchet/work/reference_repos/external_audit/mem0) | `repo_local` | `saved` | `partial` | scoped memory-sidecar, mutation-history, export/import, and graph-backed memory pattern source | local checkout verified at `ec326f0`; mine user/agent/run-scoped memory, append-history, export/import, and graph-backed memory patterns without importing hosted-memory doctrine, canonical-brain claims, or external graph-db assumptions as substrate law |
| `REPO::PI_MONO` | `pi-mono` | `repo` | [work/reference_repos/other/pi-mono](/home/ratchet/Desktop/Codex%20Ratchet/work/reference_repos/other/pi-mono) | `repo_local` | `saved` | `partial` | outside claw/control-shell and host pattern source | first bounded outside-control-shell/session-host slice now exists; keep package seams explicit rather than one flat repo label |
| `SUBCORPUS::PI_MONO_PACKAGES` | `pi-mono` package seam set | `subcorpus` | [/home/ratchet/GitHub/pi-mono](/home/ratchet/GitHub/pi-mono) | `home_local` | `saved` | `partial` | `agent`, `ai`, `coding-agent`, `mom`, `pods`, `tui`, `web-ui` seams | keep controller, memory, and UI seams explicit |
| `FAMILY::EVERMIND_AI` | EverMind-AI family | `repo_family` | [work/reference_repos/EverMind-AI](/home/ratchet/Desktop/Codex%20Ratchet/work/reference_repos/EverMind-AI) | `repo_local` | `saved` | `partial` | memory and long-context family | keep EverMemOS and MSA split below |
| `REPO::EVERMEMOS` | EverMemOS | `repo` | [work/reference_repos/EverMind-AI/EverMemOS](/home/ratchet/Desktop/Codex%20Ratchet/work/reference_repos/EverMind-AI/EverMemOS) | `repo_local` | `saved` | `partial` | outside memory/control support and witness backend source | durable witness-sync state/report now exist; bounded witness-memory retrieval is landed and currently held at `hold_at_retrieval_probe`; bounded backend-reachability audit is landed and currently held at `start_docker_daemon`; keep this as a side-project lane unless local reachability is actually earned |
| `REPO::MSA` | Memory Sparse Attention | `repo` | [work/reference_repos/EverMind-AI/MSA](/home/ratchet/Desktop/Codex%20Ratchet/work/reference_repos/EverMind-AI/MSA) | `repo_local` | `saved` | `partial` | later long-context backend candidate | keep as later backend lane, not first A2 repair |
| `REPO::Z3` | Z3 | `repo` | [work/reference_repos/other/z3](/home/ratchet/Desktop/Codex%20Ratchet/work/reference_repos/other/z3) | `repo_local` | `saved` | `runtime` | formal verification family | strongest currently proven runtime lane from broader corpus |
| `REPO::ALPHAGEOMETRY` | AlphaGeometry | `repo` | [work/reference_repos/deepmind/alphageometry](/home/ratchet/Desktop/Codex%20Ratchet/work/reference_repos/deepmind/alphageometry) | `repo_local` | `saved` | `undercaptured` | geometry / theorem / synthesis pattern source | promote from inventory into tracker/backlog explicitly |
| `REPO::AUTORESEARCHCLAW` | AutoResearchClaw | `repo` | [work/reference_repos/other/AutoResearchClaw](/home/ratchet/Desktop/Codex%20Ratchet/work/reference_repos/other/AutoResearchClaw) | `repo_local` | `saved` | `undercaptured` | outside-claw / research-controller pattern source | promote from inventory into tracker/backlog explicitly |
| `REPO::DREAMCODER_EC` | DreamCoder EC | `repo` | [work/reference_repos/other/dreamcoder-ec](/home/ratchet/Desktop/Codex%20Ratchet/work/reference_repos/other/dreamcoder-ec) | `repo_local` | `saved` | `undercaptured` | program synthesis / library growth pattern source | promote from inventory into tracker/backlog explicitly |
| `PAPER::OPENCLAW_RL_2603_10165` | OpenClaw-RL paper | `paper` | [arXiv 2603.10165](https://arxiv.org/abs/2603.10165) | `url_only` | `saved` | `registry` | next-state signal adaptation / directive correction source | external reference note now exists and first bounded audit slice is landed as `a2-next-state-signal-adaptation-audit-operator` |
| `REPO::OPENCLAW_RL` | `Gen-Verse/OpenClaw-RL` | `repo` | [Gen-Verse/OpenClaw-RL](https://github.com/Gen-Verse/OpenClaw-RL) | `url_only` | `saved` | `partial` | paper-aligned runtime / training pattern source | treat as source family only; local checkout attempt is not yet verified as stable in this workspace |
| `TOOLCHAIN::BASE_GRAPH_STACK` | base graph stack | `toolchain` | [system_v4/skills](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/skills) | `repo_local` | `saved` | `runtime` | canonical graph substrate built on `pydantic`, `networkx`, JSON, and GraphML export | this is the real current graph owner stack and must be named explicitly before any sidecar graph tools |
| `FORMAT::GRAPHML` | GraphML export layer | `format` | [v4_graph_builder.py](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/skills/v4_graph_builder.py) | `repo_local` | `saved` | `partial` | graph interchange/export format for the current owner graph stack | keep explicit as export/interchange only; do not confuse GraphML with the full semantic owner of rich graph structure |
| `TOOLCHAIN::SPEC_GRAPH_VENV` | graph/spec toolchain venv | `toolchain` | [.venv_spec_graph](/home/ratchet/Desktop/Codex%20Ratchet/.venv_spec_graph) | `repo_local` | `saved` | `partial` | runnable graph-tool environment for PyG, TopoNetX, HyperNetX, XGI, clifford, kingdon, and quaternion sidecars | keep this explicit so graph-tool availability is not confused with canonical graph integration; use it for live projection/probe runs against repo-held graph artifacts |
| `TOOL::PYDANTIC` | pydantic | `tool` | [graph_models.py](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/a2_understanding/graph_models.py) | `repo_local` | `saved` | `runtime` | typed graph schema and model-validation base for the current graph substrate | base graph law/tooling, not optional sidecar |
| `TOOL::NETWORKX` | networkx | `tool` | [v4_graph_builder.py](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/skills/v4_graph_builder.py) | `repo_local` | `saved` | `runtime` | canonical in-memory graph engine for the current graph substrate | base graph engine, not optional sidecar |
| `TOOL::PYTORCH_GEOMETRIC` | PyTorch Geometric | `tool` | [.venv_spec_graph](/home/ratchet/Desktop/Codex%20Ratchet/.venv_spec_graph) | `repo_local` | `saved` | `partial` | tensor-valued heterograph projection and trainable graph sidecar | installed and runnable through `pyg-heterograph-projection-audit`; keep read-only until bridge structure is stronger |
| `TOOL::TOPONETX` | TopoNetX | `tool` | [.venv_spec_graph](/home/ratchet/Desktop/Codex%20Ratchet/.venv_spec_graph) | `repo_local` | `saved` | `partial` | higher-order topology / cell-complex / nested-graph sidecar | installed and runnable through `toponetx-projection-adapter-audit` and `nested_graph_builder`; still sidecar-only, not canonical substrate |
| `TOOL::HYPERNETX` | HyperNetX | `tool` | [.venv_spec_graph](/home/ratchet/Desktop/Codex%20Ratchet/.venv_spec_graph) | `repo_local` | `saved` | `undercaptured` | hypergraph / higher-order relation sidecar candidate | installed in graph venv but not yet given a first bounded live repo slice |
| `TOOL::XGI` | XGI | `tool` | [.venv_spec_graph](/home/ratchet/Desktop/Codex%20Ratchet/.venv_spec_graph) | `repo_local` | `saved` | `undercaptured` | hypergraph and multiway relation sidecar candidate | installed in graph venv but not yet given a first bounded live repo slice |
| `TOOL::CLIFFORD` | clifford | `tool` | [.venv_spec_graph](/home/ratchet/Desktop/Codex%20Ratchet/.venv_spec_graph) | `repo_local` | `saved` | `partial` | graded / noncommutative edge-algebra sidecar | installed and runnable through `clifford-edge-semantics-audit`; keep as math sidecar, not canonical edge owner |
| `TOOL::KINGDON` | kingdon | `tool` | [.venv_spec_graph](/home/ratchet/Desktop/Codex%20Ratchet/.venv_spec_graph) | `repo_local` | `saved` | `partial` | PyTorch-coupled geometric algebra bridge candidate | installed and runnable, but still optional bridge tooling rather than primary semantic owner |
| `GRAPH::NESTED_GRAPH_V1` | nested graph artifact | `graph_artifact` | [nested_graph_v1.json](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/a2_state/graphs/nested_graph_v1.json) | `repo_local` | `saved` | `partial` | graph-of-graphs artifact spanning high-intake, mid-refinement, low-control, A1, and promoted layers | no longer empty; built with live cross-layer structure and graph-tool support, but not yet the governing canonical substrate |
| `GRAPH::LAYER_SET__A2_A1_PROMOTED` | layered graph owner set | `graph_artifact_family` | [system_v4/a2_state/graphs](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/a2_state/graphs) | `repo_local` | `saved` | `partial` | owner graph layer family for nested graph assembly | includes `a2_high_intake_graph_v1`, `a2_mid_refinement_graph_v1`, `a2_low_control_graph_v1`, `a1_jargoned_graph_v1`, and `promoted_subgraph`; keep explicit as the live layer inputs to nested graph work |
| `GRAPH::SKILL_KERNEL_BRIDGE_BUILDER` | skill/kernel bridge builder | `graph_operator` | [skill_kernel_bridge_builder.py](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/skills/skill_kernel_bridge_builder.py) | `repo_local` | `saved` | `partial` | direct graph-formation operator for binding skills into kernel structure | live builder exists and has already injected bridge edges, but the resulting bridge quality still needs stronger owner-grounded semantics |
| `GRAPH::NESTED_GRAPH_BUILDER` | nested graph builder | `graph_operator` | [nested_graph_builder.py](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/skills/nested_graph_builder.py) | `repo_local` | `saved` | `partial` | graph-of-graphs builder over the owner layer set | live builder exists and produced `nested_graph_v1.json`; keep this on the main graph line instead of burying it under sidecar audit prose |
| `SUBSTRATE::V4_RUNTIME_CORE` | `system_v4` runtime substrate | `runtime_substrate` | [system_v4/skills](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/skills) | `repo_local` | `saved` | `partial` | runtime kernel, witness, graph bridge, refinery, intent-control core | keep these explicit corpus members, not invisible “just code” |
| `REPO::HIPPORAG` | `OSU-NLP-Group/HippoRAG` | `repo` | [OSU-NLP-Group/HippoRAG](https://github.com/OSU-NLP-Group/HippoRAG) | `url_only` | `saved` | `registry` | associative memory, multi-hop reasoning, "brain" persistence graph | candidate for A2 persistent brain and cross-document reasoning |
| `REPO::LIGHTRAG` | `HKUDS/LightRAG` | `repo` | [HKUDS/LightRAG](https://github.com/HKUDS/LightRAG) | `url_only` | `saved` | `registry` | operational graph-RAG, incremental updates, speed, multi-storage | candidate for live witness-corpus retrieval and high-frequency graph updates |
## Imported Skill Corpora

### `lev-os/agents`

- Local reality: `635` `SKILL.md` files total
- Curated/runtime-tree corpus: `61` skills under [skills](/home/ratchet/Desktop/Codex%20Ratchet/work/reference_repos/lev-os/agents/skills)
- Library/mining corpus: `574` skills under [skills-db](/home/ratchet/Desktop/Codex%20Ratchet/work/reference_repos/lev-os/agents/skills-db)
- Immediate `keep` intake/build/workflow set:
  - [skill-builder](/home/ratchet/Desktop/Codex%20Ratchet/work/reference_repos/lev-os/agents/skills/skill-builder/SKILL.md)
  - [skill-discovery](/home/ratchet/Desktop/Codex%20Ratchet/work/reference_repos/lev-os/agents/skills/skill-discovery/SKILL.md)
  - [lev-intake](/home/ratchet/Desktop/Codex%20Ratchet/work/reference_repos/lev-os/agents/skills/lev-intake/SKILL.md)
  - [work](/home/ratchet/Desktop/Codex%20Ratchet/work/reference_repos/lev-os/agents/skills/work/SKILL.md)
  - [lev-plan](/home/ratchet/Desktop/Codex%20Ratchet/work/reference_repos/lev-os/agents/skills/lev-plan/SKILL.md)
  - [workflow](/home/ratchet/Desktop/Codex%20Ratchet/work/reference_repos/lev-os/agents/skills/workflow/SKILL.md)
- Immediate `adapt` set:
  - [lev-research](/home/ratchet/Desktop/Codex%20Ratchet/work/reference_repos/lev-os/agents/skills/lev-research/SKILL.md)
  - [autodev-loop](/home/ratchet/Desktop/Codex%20Ratchet/work/reference_repos/lev-os/agents/skills/autodev-loop/SKILL.md)
  - [agentping](/home/ratchet/Desktop/Codex%20Ratchet/work/reference_repos/lev-os/agents/skills/agentping/SKILL.md)
- Immediate `mine` seeds:
  - [cdo](/home/ratchet/Desktop/Codex%20Ratchet/work/reference_repos/lev-os/agents/skills/cdo/SKILL.md)
  - [current-reality-tree](/home/ratchet/Desktop/Codex%20Ratchet/work/reference_repos/lev-os/agents/skills-db/thinking/patterns/current-reality-tree/SKILL.md)
  - [system-traps](/home/ratchet/Desktop/Codex%20Ratchet/work/reference_repos/lev-os/agents/skills-db/thinking/patterns/system-traps/SKILL.md)
  - [fault-tree-analysis](/home/ratchet/Desktop/Codex%20Ratchet/work/reference_repos/lev-os/agents/skills-db/thinking/patterns/fault-tree-analysis/SKILL.md)
  - [property-based-testing](/home/ratchet/Desktop/Codex%20Ratchet/work/reference_repos/lev-os/agents/skills-db/thinking/patterns/property-based-testing/SKILL.md)

## First Cluster Map

- `Skill-source intake cluster`: `lev-intake`, `skill-discovery`, `skill-builder`
  - first Ratchet-native slice: `a2-skill-source-intake-operator`
  - cluster map: [V4_IMPORTED_SKILL_CLUSTER_MAP__CURRENT.md](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/V4_IMPORTED_SKILL_CLUSTER_MAP__CURRENT.md)

## Current lev-os/agents Promotion Read

- current promotion audit slice:
  - `a2-lev-agents-promotion-operator`
- `SKILL_CLUSTER::lev-formalization-placement` now has seven bounded landed slices:
  - `a2-lev-builder-placement-audit-operator`
  - `a2-lev-builder-formalization-proposal-operator`
  - `a2-lev-builder-formalization-skeleton-operator`
  - `a2-lev-builder-post-skeleton-readiness-operator`
  - `a2-lev-builder-post-skeleton-follow-on-selector-operator`
  - `a2-lev-builder-post-skeleton-disposition-audit-operator`
  - `a2-lev-builder-post-skeleton-future-lane-existence-audit-operator`
  - core refs: `lev-builder`, `arch`, `work`
  - background only: `lev-plan`, `stack`
  - the proposal slice remains proposal-only and non-migratory
  - the skeleton slice remains scaffold-only and non-migratory
  - the readiness slice remains selector-admission-only, non-migratory, and non-runtime-live
  - current admission decision: `admit_for_selector_only`
  - the follow-on selector slice remains selector-only, non-migratory, and non-runtime-live
  - current selected follow-on branch: `post_skeleton_follow_on_unresolved`
  - the disposition slice remains branch-governance-only, non-migratory, and non-runtime-live
  - current disposition: `retain_unresolved_branch`
  - the future-lane existence slice remains branch-governance-only, non-migratory, and non-runtime-live
  - current future-lane existence decision: `future_lane_exists_as_governance_artifact`
  - current bounded outcome: `hold_at_disposition`
  - any migration/runtime/imported-runtime-ownership follow-on remains separately gated and unresolved
  - refreshed selector truth now treats this cluster as landed and parked at disposition
- `SKILL_CLUSTER::lev-autodev-exec-validation`
  - first bounded slice now exists: `a2-lev-autodev-loop-audit-operator`
  - keep it audit-only, non-migratory, and non-runtime-live
- `SKILL_CLUSTER::lev-architecture-fitness-review`
  - first bounded slice now exists: `a2-lev-architecture-fitness-operator`
  - keep it audit-only, non-migratory, and non-runtime-live
- current lev selector state:
  - `has_current_unopened_cluster = False`
  - admit any further lev slice only after explicit audit
- `Tracked work / planning cluster`: `work`, `lev-plan`, `workflow`
  - first bounded slice now exists: `a2-tracked-work-operator`
  - `work` = adapt, `lev-plan` = mine, `workflow` = skip
- `Research / deliberation cluster`: `lev-research`, `cdo`, cited-research and reverse-engineer-specs workflow leaves
  - first bounded slice now exists: `a2-research-deliberation-operator`
  - `lev-research` = adapt, `cdo` = mine, workflow leaves = mine later
  - current emitted report:
    - [A2_RESEARCH_DELIBERATION_REPORT__CURRENT__v1.json](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/A2_RESEARCH_DELIBERATION_REPORT__CURRENT__v1.json)
    - [A2_RESEARCH_DELIBERATION_REPORT__CURRENT__v1.md](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/A2_RESEARCH_DELIBERATION_REPORT__CURRENT__v1.md)
- `Workshop analysis / gating cluster`: `lev-workshop`, `lev-align`, `work`
  - first bounded slice now exists: `a2-workshop-analysis-gate-operator`
  - `lev-workshop` = adapt, `lev-align` = adapt, `work` = mine
  - current emitted outputs:
    - [A2_WORKSHOP_ANALYSIS_GATE_REPORT__CURRENT__v1.json](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/A2_WORKSHOP_ANALYSIS_GATE_REPORT__CURRENT__v1.json)
    - [A2_WORKSHOP_ANALYSIS_GATE_REPORT__CURRENT__v1.md](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/A2_WORKSHOP_ANALYSIS_GATE_REPORT__CURRENT__v1.md)
- `FlowMind / outer-session durability cluster`: session continuity + receipts + resume semantics
  - first bounded slice now exists: `outer-session-ledger`
  - current emitted outputs:
    - [OUTER_SESSION_LEDGER_STATE__CURRENT__v1.json](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/a2_state/OUTER_SESSION_LEDGER_STATE__CURRENT__v1.json)
    - [OUTER_SESSION_LEDGER_REPORT__CURRENT__v1.json](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/OUTER_SESSION_LEDGER_REPORT__CURRENT__v1.json)
    - [OUTER_SESSION_LEDGER_REPORT__CURRENT__v1.md](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/OUTER_SESSION_LEDGER_REPORT__CURRENT__v1.md)
- `Outside control-shell / session-host cluster`: `pi-mono` control-shell seam
  - first bounded slice now exists: `outside-control-shell-operator`
  - keep it read-only and repo-held as report + packet only
  - current emitted outputs:
    - [A2_PIMONO_OUTSIDE_SESSION_HOST_REPORT__CURRENT__v1.json](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/A2_PIMONO_OUTSIDE_SESSION_HOST_REPORT__CURRENT__v1.json)
    - [A2_PIMONO_OUTSIDE_SESSION_HOST_REPORT__CURRENT__v1.md](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/A2_PIMONO_OUTSIDE_SESSION_HOST_REPORT__CURRENT__v1.md)
    - [A2_PIMONO_OUTSIDE_SESSION_HOST_PACKET__CURRENT__v1.json](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/A2_PIMONO_OUTSIDE_SESSION_HOST_PACKET__CURRENT__v1.json)
- `Meta-skill improvement cluster`: `autoresearch-operator`, `llm-council-operator`, `skill-improver-operator`
  - current maintenance-side bounded progression now includes `a2-skill-improver-dry-run-operator`, first-target proof, and second-target admission audit
  - current bounded result is still one admitted proven target class only; broader second-target classes remain unadmitted
- `Outside memory cluster`: `evermem-memory-backend-adapter`, `witness-evermem-sync`, `witness-memory-retriever`, `a2-evermem-backend-reachability-audit-operator`, `pimono-evermem-adapter`
  - current bounded slices are durable/auditable `witness-evermem-sync`, bounded `witness-memory-retriever`, and bounded `a2-evermem-backend-reachability-audit-operator`
  - current repo-held outputs:
    - [EVERMEM_WITNESS_SYNC_STATE__CURRENT__v1.json](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/a2_state/EVERMEM_WITNESS_SYNC_STATE__CURRENT__v1.json)
    - [EVERMEM_WITNESS_SYNC_REPORT__CURRENT__v1.md](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/EVERMEM_WITNESS_SYNC_REPORT__CURRENT__v1.md)
    - [WITNESS_MEMORY_RETRIEVER_REPORT__CURRENT__v1.md](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/WITNESS_MEMORY_RETRIEVER_REPORT__CURRENT__v1.md)
    - [A2_EVERMEM_BACKEND_REACHABILITY_AUDIT_REPORT__CURRENT__v1.md](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/A2_EVERMEM_BACKEND_REACHABILITY_AUDIT_REPORT__CURRENT__v1.md)
  - keep this cluster as a side project unless live backend reachability is actually earned
- `SKILL_CLUSTER::next-state-signal-adaptation`: OpenClaw-RL paper/repo -> Ratchet witness and bounded-improvement seams
  - first bounded slice now exists: `a2-next-state-signal-adaptation-audit-operator`
  - second bounded slice now exists: `a2-next-state-directive-signal-probe-operator`
  - current repo-held outputs:
    - [A2_NEXT_STATE_SIGNAL_ADAPTATION_AUDIT_REPORT__CURRENT__v1.json](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/A2_NEXT_STATE_SIGNAL_ADAPTATION_AUDIT_REPORT__CURRENT__v1.json)
    - [A2_NEXT_STATE_SIGNAL_ADAPTATION_AUDIT_REPORT__CURRENT__v1.md](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/A2_NEXT_STATE_SIGNAL_ADAPTATION_AUDIT_REPORT__CURRENT__v1.md)
    - [A2_NEXT_STATE_DIRECTIVE_SIGNAL_PROBE_REPORT__CURRENT__v1.json](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/A2_NEXT_STATE_DIRECTIVE_SIGNAL_PROBE_REPORT__CURRENT__v1.json)
    - [A2_NEXT_STATE_DIRECTIVE_SIGNAL_PROBE_REPORT__CURRENT__v1.md](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/A2_NEXT_STATE_DIRECTIVE_SIGNAL_PROBE_REPORT__CURRENT__v1.md)
    - [A2_NEXT_STATE_IMPROVER_CONTEXT_BRIDGE_AUDIT_REPORT__CURRENT__v1.json](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/A2_NEXT_STATE_IMPROVER_CONTEXT_BRIDGE_AUDIT_REPORT__CURRENT__v1.json)
    - [A2_NEXT_STATE_IMPROVER_CONTEXT_BRIDGE_AUDIT_REPORT__CURRENT__v1.md](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/A2_NEXT_STATE_IMPROVER_CONTEXT_BRIDGE_AUDIT_REPORT__CURRENT__v1.md)
    - [A2_NEXT_STATE_FIRST_TARGET_CONTEXT_CONSUMER_ADMISSION_AUDIT_REPORT__CURRENT__v1.json](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/A2_NEXT_STATE_FIRST_TARGET_CONTEXT_CONSUMER_ADMISSION_AUDIT_REPORT__CURRENT__v1.json)
    - [A2_NEXT_STATE_FIRST_TARGET_CONTEXT_CONSUMER_ADMISSION_AUDIT_REPORT__CURRENT__v1.md](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/A2_NEXT_STATE_FIRST_TARGET_CONTEXT_CONSUMER_ADMISSION_AUDIT_REPORT__CURRENT__v1.md)
  - current bounded result of the directive probe is now `ok`
  - the current bridge result is `admissible_as_first_target_context_only`
  - `skill-improver-operator` now exposes an explicit first-target context contract
  - the current consumer result is `candidate_first_target_context_consumer_admissible`
  - a fifth bounded slice now exists: `a2-next-state-first-target-context-consumer-proof-operator`
  - current proof result is `ok`
  - current next step there is `hold_consumer_proof_as_metadata_only`
  - keep it audit-only and proposal-only; do not widen it into OpenClaw runtime, online RL, live mutation claims, or graph-backfill claims
- `Context/spec/workflow/memory source set`: `Context-Engineering`, `spec-kit`, `superpowers`, `mem0`
  - current role is source-family pressure for richer append-safe context, live spec coupling, low-bloat continuity, disciplined subagent workflows, and scoped memory-sidecar patterns
  - do not treat these repos as replacement owner-law, canonical A2/A1 brain, plugin runtime dependencies, or direct doctrine
- `Graph toolchain / nested-graph source set`: base stack `pydantic + networkx + JSON + GraphML export`, plus `.venv_spec_graph`, `PyG`, `TopoNetX`, `HyperNetX`, `XGI`, `clifford`, `kingdon`, `nested_graph_builder`, `skill_kernel_bridge_builder`, and the layered owner graphs
  - current role is live graph formation, schema validation, graph persistence/export, higher-order projection, bridge shaping, and graded-edge experimentation over real repo-held graph artifacts
  - do not treat sidecar tool installation or projections by themselves as proof that the canonical graph is already nested, governing, or fully integrated
- `Formal verification cluster`: `z3-constraint-checker`, `z3-cegis-refiner`, `property-pressure-tester`, `structured-fuzzer`, `model-checker`

## Still Undercaptured

- the root corpus docs are now directly indexed in canonical A2, but that indexing needs to stay current as the corpus grows
- `llm.c`, `minbpe`, `alphageometry`, `AutoResearchClaw`, and `dreamcoder-ec` were local but underrepresented in the umbrella until this pass
- `Leviathan v3.2 word.txt`, `holodeck docs.md`, and the bootpack / EM handoff doc family also belong in the broad corpus instead of disappearing into high-entropy doc piles
- the `system_v4` runtime substrate belongs in this corpus as an explicit source family because it is part of the system skill build loop
- the graph toolchain and nested-graph artifacts also belong in this corpus as explicit source/tool/artifact members because they are part of the intended graph-first build loop, not just optional experiments
- graph presence and registry rows still need to be kept separate from runtime proof

## Append Rule

When a new repo, doc, method corpus, processed internal corpus, runtime substrate, or imported skill corpus matters enough to keep:

1. append or update its row here
2. append integration reality in [REPO_SKILL_INTEGRATION_TRACKER.md](/home/ratchet/Desktop/Codex%20Ratchet/REPO_SKILL_INTEGRATION_TRACKER.md)
3. append candidate skills or clusters in [SKILL_CANDIDATES_BACKLOG.md](/home/ratchet/Desktop/Codex%20Ratchet/SKILL_CANDIDATES_BACKLOG.md)
4. update local presence in [LOCAL_SOURCE_REPO_INVENTORY.md](/home/ratchet/Desktop/Codex%20Ratchet/LOCAL_SOURCE_REPO_INVENTORY.md)
5. route durable significance into [A2_KEY_CONTEXT_APPEND_LOG__v1.md](/home/ratchet/Desktop/Codex%20Ratchet/system_v3/a2_state/A2_KEY_CONTEXT_APPEND_LOG__v1.md) through [A2_SKILL_SOURCE_INTAKE_PROCEDURE__CURRENT__v1.md](/home/ratchet/Desktop/Codex%20Ratchet/system_v3/a2_state/A2_SKILL_SOURCE_INTAKE_PROCEDURE__CURRENT__v1.md)
6. only then call it `saved`
