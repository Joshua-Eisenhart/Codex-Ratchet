# QIT Graph Sync README

> Front-door file for any IDE, agent, or human working on the QIT graph lane.
> Read this first to understand what is real, what is bounded, and what is not yet admitted.

---

## Where Things Live

| File | Purpose |
|---|---|
| `core_docs/QIT_GRAPH_LAYER_MAPPING.md` | Conceptual Rosetta stone: which physics concept lives in which graph layer |
| `core_docs/QIT_GRAPH_SCHEMA.md` | Canonical node and edge inventory (6 live node types + 1 schema-ready type, 9 edge types, 41 nodes, 185 edges) |
| `core_docs/QIT_GRAPH_SIDECAR_POLICY.md` | What each sidecar may and may not do |
| `core_docs/QIT_GRAPH_RUNTIME_MODEL.md` | Structure vs state vs history graph separation |
| `core_docs/QIT_GRAPH_PROMOTION_GATES.md` | When a concept moves from sidecar to owner truth |
| `core_docs/QIT_COMPRESSION_FUTURE_REFERENCES.md` | Later-only compression references (QJL, TurboQuant, PolarQuant) and revisit triggers |
| `core_docs/C_LAYER_ARCHITECTURE.md` | C1/C2/C3 external layer: pi-mono, AutoResearchClaw, MiroFish, OpenClaw-RL |
| `system_v4/skills/qit_engine_graph_builder.py` | Builds the QIT engine graph layer |
| `system_v4/skills/qit_graph_stack_runtime.py` | Rebuilds the QIT owner graph, exports GraphML, and runs the bounded sidecars into one status report |
| `system_v4/skills/qit_owner_schemas.py` | Pydantic contracts for all owner-layer types |
| `system_v4/a2_state/graphs/qit_engine_graph_v1.json` | The live QIT engine graph (41 nodes, 185 edges) |

---

## What Is Owner Truth (Read These First)

The **owner stack** is `Pydantic → JSON → NetworkX → GraphML`. These are real:

- ✅ Engine type identities (Deductive / Inductive)
- ✅ 16 macro-stage nodes with terrain attributes
- ✅ 4 fixed subcycle operators (Ti → Fe → Te → Fi)
- ✅ 3 nested Hopf torus identities
- ✅ 7 proven load-bearing axes (0–6)
- ✅ 9 negative witness nodes (graveyard kills)
- ✅ 185 structural edges (stage sequence, operator acts-on, torus nesting, chirality coupling, etc.)
- ✅ GraphML export as an owner-stack interoperability view
- ⚠️ `WEYL_BRANCH` is schema-ready, but not yet instantiated in the live owner graph

---

## What Is Bounded / Not Yet Admitted

| Sidecar | Current Status | What It Does |
|---|---|---|
| **TopoNetX** | Bounded read-only projection | Builds CellComplex, identifies cycles and 2-cells from owner data |
| **clifford** | Bounded read-only sidecar | Computes Cl(3,0) multivector edge payloads from owner edge types |
| **PyG** | Bounded read-only sidecar | Builds HeteroData tensor projections from owner data |
| **LightRAG** | Installed, smoke-tested | Retrieval over corpus + SIM results (needs embedding config) |
| **kingdon** | Not yet integrated | Optional GA-Torch bridge for differentiable algebra |

**None of these sidecars are semantic owners yet.** They are the correct *next* semantic carriers for their respective domains, pending promotion gates.

---

## What Is NOT Real Yet

- ❌ Runtime state graph (engine position during execution) — still in `engine_core.py` dataclass, not a graph
- ❌ History/evidence graph — still flat JSON files in `a2_state/sim_results/`
- ❌ LightRAG retrieval over SIM results
- ❌ Live TopoNetX torus 2-cells in the owner graph
- ❌ Live clifford chirality payloads in the owner graph
- ❌ Any promotion gate fully passed
- ❌ Any live compression layer over QIT graph state, retrieval embeddings, or history graph

---

## How to Read Order

If you are a new IDE or agent encountering this for the first time:

1. **Start here** — you're reading it
2. `QIT_GRAPH_SCHEMA.md` — learn the node and edge types
3. `QIT_GRAPH_LAYER_MAPPING.md` — understand where physics concepts map
4. `QIT_GRAPH_SIDECAR_POLICY.md` — know what you may and may not do
5. `QIT_GRAPH_RUNTIME_MODEL.md` — understand structure vs state vs history
6. `QIT_GRAPH_PROMOTION_GATES.md` — know when things move inward
7. `QIT_COMPRESSION_FUTURE_REFERENCES.md` — know which compression papers matter later and why they are not build-now work

---

## Verification

```bash
# Validate Pydantic schemas
python3 system_v4/skills/qit_owner_schemas.py

# Rebuild the QIT engine graph
python3 system_v4/skills/qit_engine_graph_builder.py

# Rebuild the owner graph, export GraphML, and run bounded sidecar status
python3 system_v4/skills/qit_graph_stack_runtime.py

# Rebuild the full nested graph (includes QIT as 6th layer)
python3 system_v4/skills/nested_graph_builder.py
```
