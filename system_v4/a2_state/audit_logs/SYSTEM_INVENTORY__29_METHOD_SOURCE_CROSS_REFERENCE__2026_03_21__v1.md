# System Inventory: 29-Method Source Cross-Reference

**Status:** `UNVERIFIED_MANUAL_CROSS_REFERENCE`
**Warning:** The source identification is correct for `29 thing.txt`, but the live-skill and hot-path status claims below have not yet been fully reconciled against the current skill registry and runner. Do not treat this note as authoritative integration truth until that verification pass is completed.
**Generated:** 2026-03-21  
**Live registry count:** 88 skills  
**Source files read:** `29 thing.txt`, `jp graph asuggestions.txt`, `jp graph prompt!!.txt`, `lev_nonclassical_runtime_design_audited.md`

---

## A. The 29 Methods → Skill Status

Each row attempts to map one of the 29 numbered methods from [29 thing.txt](file:///home/ratchet/Desktop/Codex%20Ratchet/core_docs/v4%20upgrades/29%20thing.txt) to a live or proposed skill, but those status columns require explicit registry and hot-path verification.

| # | Method | Live Skill | Status |
|---|--------|-----------|--------|
| 1 | Nested Hopf Tori | [runtime_state_kernel.py](file:///home/ratchet/Desktop/Codex%20Ratchet/system_v4/skills/runtime_state_kernel.py) | ✅ `region`, `phaseIndex`, `phasePeriod`, `loopScale` all present in `RuntimeState` |
| 2 | Topology/Orchestration/Dispatch Split | [run_real_ratchet.py](file:///home/ratchet/Desktop/Codex%20Ratchet/system_v4/skills/run_real_ratchet.py) | ✅ Three-plane split is the live architecture |
| 3 | Graph Topology Thinking | [runtime_graph_bridge.py](file:///home/ratchet/Desktop/Codex%20Ratchet/system_v4/skills/runtime_graph_bridge.py) | ✅ Graph is executable topology |
| 4 | Nonclassical State Space | [runtime_state_kernel.py](file:///home/ratchet/Desktop/Codex%20Ratchet/system_v4/skills/runtime_state_kernel.py) | ✅ Structured state with boundaries, invariants, non-commutative transforms |
| 5 | Phase / Loop-Scale Model | [runtime_state_kernel.py](file:///home/ratchet/Desktop/Codex%20Ratchet/system_v4/skills/runtime_state_kernel.py) | ✅ Phase and loop scale are explicit fields |
| 6 | Karpathy Design Philosophy | [bounded_improve_operator.py](file:///home/ratchet/Desktop/Codex%20Ratchet/system_v4/skills/bounded_improve_operator.py) | ✅ Small visible loop, mutate/eval/keep |
| 7 | Nanochat | [runtime_state_kernel.py](file:///home/ratchet/Desktop/Codex%20Ratchet/system_v4/skills/runtime_state_kernel.py) | ✅ Small-core principle expressed through kernel |
| 8 | Autoresearch | [autoresearch_operator.py](file:///home/ratchet/Desktop/Codex%20Ratchet/system_v4/skills/autoresearch_operator.py) | ✅ Registered, wired into `run_real_ratchet.py` |
| 9 | LLM-Council | [llm_council_operator.py](file:///home/ratchet/Desktop/Codex%20Ratchet/system_v4/skills/llm_council_operator.py) | ✅ Registered, wired into `run_real_ratchet.py` |
| 10 | Bayesian Updating | — | ❌ **No skill.** Retooled pattern exists in doc but no `bayesian_update_operator.py` |
| 11 | Markov Chains | — | ❌ **No skill.** Transform-based state evolution is implicit in kernel but not a named operator |
| 12 | FEP / Active Inference | [fep_regulation_operator.py](file:///home/ratchet/Desktop/Codex%20Ratchet/system_v4/skills/fep_regulation_operator.py) | ⚠️ Skill exists, registered, **not in hot-path** of `run_real_ratchet.py` |
| 13 | Information Geometry | — | ❌ **No skill.** Probe-relative distinguishability is in kernel but no named operator |
| 14 | Algorithmic Information Theory | — | ❌ **No skill.** Trace compression / motif detection not yet a standalone skill |
| 15 | Property-Based Testing | [property_pressure_tester.py](file:///home/ratchet/Desktop/Codex%20Ratchet/system_v4/skills/property_pressure_tester.py) | ⚠️ Skill exists, registered, **not in hot-path** |
| 16 | CEGIS | [z3_cegis_refiner.py](file:///home/ratchet/Desktop/Codex%20Ratchet/system_v4/skills/z3_cegis_refiner.py) | ⚠️ Skill exists, registered, **not in hot-path** |
| 17 | SAT / SMT | [z3_constraint_checker.py](file:///home/ratchet/Desktop/Codex%20Ratchet/system_v4/skills/z3_constraint_checker.py) | ✅ Registered **and** in hot-path |
| 18 | Differential Testing | [differential_tester.py](file:///home/ratchet/Desktop/Codex%20Ratchet/system_v4/skills/differential_tester.py) | ⚠️ Skill exists, registered, **not in hot-path** |
| 19 | Model Checking | [model_checker.py](file:///home/ratchet/Desktop/Codex%20Ratchet/system_v4/skills/model_checker.py) | ⚠️ Skill exists, registered, **not in hot-path** |
| 20 | Abstract Interpretation | — | ❌ **No skill.** Coarse-state abstraction not yet a standalone operator |
| 21 | Fuzzing | [structured_fuzzer.py](file:///home/ratchet/Desktop/Codex%20Ratchet/system_v4/skills/structured_fuzzer.py) | ⚠️ Skill exists, registered, **not in hot-path** |
| 22 | AlphaGeometry-Style Search | [frontier_search_operator.py](file:///home/ratchet/Desktop/Codex%20Ratchet/system_v4/skills/frontier_search_operator.py) | ⚠️ Skill exists, registered, **not in hot-path** |
| 23 | Program Synthesis | — | ❌ **No skill.** Candidate generation is implicit in CEGIS but no standalone synth operator |
| 24 | DreamCoder / Abstraction Learning | — | ❌ **No skill.** Motif mining from traces not yet a standalone skill |
| 25 | Evolutionary Search | — | ❌ **No skill.** Mutation/recombination is in bounded_improve but no standalone evo operator |
| 26 | Constrained Decoding | — | ❌ **No skill.** Typed I/O contracts exist but no standalone constrained-decode skill |
| 27 | Guardrail Pipelines | [b_kernel](file:///home/ratchet/Desktop/Codex%20Ratchet/system_v4/skills) | ✅ Guard/gate logic exists in B kernel |
| 28 | Build / Reproducibility | [run_real_ratchet.py](file:///home/ratchet/Desktop/Codex%20Ratchet/system_v4/skills/run_real_ratchet.py) | ✅ Deterministic rebuild from graph + event spine |
| 29 | Graph Mining / Topology Extraction | [graph_capability_auditor.py](file:///home/ratchet/Desktop/Codex%20Ratchet/system_v4/skills/graph_capability_auditor.py) | ⚠️ Graph mining exists but is audit-only, not a full trace-mining operator |

### Summary
- **✅ Fully live:** 11 of 29
- **⚠️ Skill exists but not in hot-path:** 7 of 29
- **❌ No skill at all:** 7 of 29
- **✅ Implicit in architecture:** 4 of 29

---

## B. JP Graph Suggestions → Skill Status

From [jp graph asuggestions.txt](file:///home/ratchet/Desktop/Codex%20Ratchet/core_docs/v4%20upgrades/jp%20graph%20asuggestions.txt):

| JP Concept | Live Skill | Status |
|---|---|---|
| TLA+ state-machine verification | `z3-constraint-checker` | ✅ Z3 side is live; TLA+ spec generation is not |
| Symbolic model checking (Apalache→Z3) | `z3-constraint-checker`, `z3-cegis-refiner` | ⚠️ Z3 is live; Apalache translation layer missing |
| 10 core invariants | `b-kernel` | ⚠️ Partial — B kernel enforces some, not all 10 |
| `ValidationGateExecutor` | `b-kernel` | ⚠️ Gate enforcement exists but not named this way |
| Agent verification loop | `z3-constraint-checker` → `run_real_ratchet` | ⚠️ Loop exists but counterexample→fix cycle not automated |
| Graph-driven intent runtime prompt | `intent-control-surface-builder`, `intent-runtime-policy` | ✅ Intent primitives are first-class |

From [jp graph prompt!!.txt](file:///home/ratchet/Desktop/Codex%20Ratchet/core_docs/upgrade%20docs/jp%20graph%20prompt%21%21.txt):

| JP Concept | Live Skill | Status |
|---|---|---|
| Intent as first-class primitive | `intent-control-surface-builder` | ✅ |
| Proposal→Patch→Accept lifecycle | `ratchet-verify`, `b-adjudicator` | ✅ |
| Entity lifecycle (create/update/stale/delete) | `runtime-state-kernel` | ✅ |
| Debug/proposal footer pattern | — | ❌ Not yet a runtime output format |

---

## C. External Repos → Integration Status

| Repo / Source | Staged? | Skillized? | In Graph? | In Hot-Path? |
|---|---|---|---|---|
| **Z3** (`Z3Prover/z3`) | ✅ | ✅ `z3-constraint-checker`, `z3-cegis-refiner` | ✅ | ✅ (checker only) |
| **Karpathy/autoresearch** | ✅ | ✅ `autoresearch-operator` | ✅ | ✅ |
| **Karpathy/llm-council** | ✅ | ✅ `llm-council-operator` | ✅ | ✅ |
| **Karpathy/nanoGPT, nanochat** | ✅ | ✅ (implicit in kernel design) | ✅ | ✅ |
| **lev-os/agents** | ✅ staged | ❌ No live skill | ⚠️ graph node only | ❌ |
| **lev-os/leviathan + JP** | ✅ staged | ❌ No live skill | ⚠️ graph node only | ❌ |
| **lev-os org root** | ✅ staged | ❌ | ⚠️ | ❌ |
| **pi-mono** | ✅ staged | ✅ `pimono-evermem-adapter` | ✅ 7 source nodes | ❌ not in hot-path |
| **EverMemOS** | ✅ staged | ✅ `evermem-memory-backend-adapter`, `witness-evermem-sync` | ✅ | ❌ not in hot-path |
| **MSA** | ✅ staged | ❌ | ❌ | ❌ |
| **29 sources / 29 batches** | ✅ staged | ❌ | ✅ cluster in graph | ❌ |

---

## D. Codex's Work vs This Inventory

Codex's `OPUS_DEEP_READ_29_THING.md` ingested `29 thing.txt` into the A2 graph as **9 nodes, 8 edges** — a high-level topic extraction, not the 29-item skill mapping done here. This inventory is the complete cross-reference that was missing.

---

## E. Gap Summary

### 7 methods with NO skill at all
These need new `.py` files, registry entries, and graph nodes:
1. **Bayesian Updating** → `bayesian_update_operator.py`
2. **Markov Chains** → `markov_transition_operator.py`
3. **Information Geometry** → `info_geometry_operator.py`
4. **Algorithmic Information Theory** → `trace_compression_operator.py`
5. **Program Synthesis** → `program_synthesis_operator.py`
6. **DreamCoder / Abstraction Learning** → `motif_library_learner.py`
7. **Evolutionary Search** → `evolutionary_search_operator.py`

### 7 skills NOT in hot-path
These exist on disk and in the registry but `run_real_ratchet.py` does not invoke them:
1. `fep_regulation_operator.py`
2. `property_pressure_tester.py`
3. `z3_cegis_refiner.py`
4. `differential_tester.py`
5. `model_checker.py`
6. `structured_fuzzer.py`
7. `frontier_search_operator.py`

### External repos staged but not skillized
1. `lev-os/agents` → needs workshop intake operator
2. `lev-os/leviathan` → needs JP vision / star-skill packager
3. `MSA` → needs capability audit skill (later)
