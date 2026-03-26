# C-Layer Architecture — External Research Automation

> The C layer formalizes external research automation, agent coordination, and swarm-computation tools that operate **outside** the system boundary.
> C-layer tools do NOT govern the system. They are consumers and producers that interact with the system through bounded interfaces.

---

## Layer Hierarchy (Updated)

```
┌─────────────────────────────────────────────────────┐
│  C3: SWARM / RL                                     │
│    MiroFish (multi-agent swarm sim)                  │
│    OpenClaw-RL (RL training)                         │
├─────────────────────────────────────────────────────┤
│  C2: RESEARCH AUTOMATION                            │
│    AutoResearchClaw (idea → paper pipeline)          │
│    autoresearch (existing harness → C2 bridge)       │
├─────────────────────────────────────────────────────┤
│  C1: AGENT COORDINATION / CONTROL SHELL             │
│    pi-mono (primary agent framework)                 │
│    outside_control_shell_operator (existing bridge)   │
├═════════════════════════════════════════════════════╡
│  ← SYSTEM BOUNDARY →                                │
├─────────────────────────────────────────────────────┤
│  QIT_ENGINE: Physics topology layer                  │
│  SKILLS: Skills layer                                │
│  B_LAYER: System graph (accumulation)                │
│  A2_LOW_CONTROL: Kernel / control state              │
│  A2_MID_REFINEMENT: Refinement state                 │
│  A2_HIGH_INTAKE: Intake / extraction state           │
│  A1_JARGONED: Human-readable corpus                  │
└─────────────────────────────────────────────────────┘
```

---

## C1: Agent Coordination / Control Shell

**Purpose**: Bounded agent framework and session management. The primary interface between the system and external agents.

| Tool | Role | Current Status |
|---|---|---|
| **pi-mono** | Primary agent framework (coding-agent, tui, web-ui, agent, pods, ai, mom) | Ingested as reference repo. `outside_control_shell_operator.py` and `pimono_evermem_adapter.py` exist as bounded bridges. |
| **lev-os/agents** | Live-syncing skill source. Skills are diffed against obsidian ingestion state and promoted through the normal intake pipeline. | At `work/reference_repos/lev-os/agents/`. 50+ skills ingested. `levos_skills_sync.py` runs the diff. |
| **outside_control_shell_operator** | Read-only audit of pi-mono session-host evidence | Live, bounded. Does not mutate pi-mono workspaces. |

**Interfaces**:
- C1 → A2_HIGH_INTAKE: session evidence and ingested skills flow downward as intake documents
- C1 → SKILLS: agent-dispatched skill invocations; lev-os skills tested at C layer before promotion
- A2_LOW_CONTROL → C1: kernel decisions emit agent task briefs
- lev-os → C1: `levos_skills_sync.py --pull` pulls latest skills, diffs against existing ingestion

**Constraints**:
- C1 does NOT replace the A2 state machinery
- C1 does NOT own any owner-graph truth
- C1 reads from the system but does not govern it

---

## C2: Research Automation

**Purpose**: Autonomous research pipelines that consume system state and produce research artifacts (papers, experiments, evidence tokens).

| Tool | Role | Current Status |
|---|---|---|
| **AutoResearchClaw** | 23-stage fully autonomous research pipeline (idea → paper). OpenClaw + MetaClaw integration. | Not yet cloned. Registered as future candidate. |
| **autoresearch** (existing) | `autoresearch_sim_harness.py` — the existing 12-problem evaluation harness | Live. Already governs SIM evaluation. This is the **C2 bridge** between the existing A2 research loop and the external automation layer. |

**Interfaces**:
- C2 → A2_HIGH_INTAKE: research outputs (papers, experiment results) flow in as intake documents
- C2 ← A2_LOW_CONTROL: kernel-level problem specs seed the research pipeline
- C2 → SIM_RESULTS: experiment evidence tokens flow into `a2_state/sim_results/`

**Constraints**:
- C2 does NOT modify the engine or owner graph
- C2 consumes problem specs and produces evidence; it does not interpret evidence
- AutoResearchClaw requires LLM API access (OpenAI, Anthropic, etc.)

---

## C3: Swarm / RL

**Purpose**: Multi-agent simulation and reinforcement learning over research strategies. Operates at population level, not individual-agent level.

| Tool | Role | Current Status |
|---|---|---|
| **MiroFish** | Multi-agent swarm simulation (belief propagation, collective intelligence) | Cloned to `work/mirofish/`. Not yet integrated. |
| **OpenClaw-RL** | RL training environment for research automation strategies | Not yet cloned. Registered as future candidate. |

**Interfaces**:
- C3 → C2: swarm-optimized research strategies seed AutoResearchClaw runs
- C3 ← A2_HIGH_INTAKE: swarm fitness evaluation uses intake quality metrics
- C3 → SIM_RESULTS: swarm experiment results flow into the evidence pipeline

**Constraints**:
- C3 does NOT access the owner graph
- C3 does NOT run inside the system boundary
- C3 output is treated as C2 input, never as owner truth

---

## C-Layer General Policy

1. **C-layer tools sit OUTSIDE the system boundary.** They interact through documented, bounded interfaces only.
2. **C-layer cannot create or modify owner-graph nodes.** All C-layer output enters the system through the A2_HIGH_INTAKE pipeline.
3. **C-layer may read system state** through exported JSON, GraphML, or SIM result files.
4. **C-layer tools run in isolated environments** (separate venvs, containers, or remote hosts). They do NOT share the system's Python environment.
5. **Pi-mono (C1) is the primary agent coordination surface.** All other C-layer tools interact with the system through pi-mono or through direct file I/O into `a2_state/`.
6. **C-layer errors must not corrupt system state.** If a C-layer tool crashes, the system continues operating from its last clean owner-graph snapshot.

---

## Verification

```bash
# Verify C1 bridge exists
python3 system_v4/skills/outside_control_shell_operator.py

# Verify C2 bridge exists
python3 system_v4/probes/autoresearch_sim_harness.py

# Verify LightRAG sidecar (bridges C2 → retrieval)
work/lightrag_venv/bin/python3 system_v4/probes/lightrag_smoke_test.py
```
