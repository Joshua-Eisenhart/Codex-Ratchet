# A2_GRAPH_REFINERY_PROCESS__v2
Status: PROPOSED
Date: 2026-03-17
Supersedes: `A2_GRAPH_REFINERY_PROCESS__v1.md` (retains all v1 rules, adds autonomous worker protocol)

## 0) What Changed from v1
- **Autonomous Worker Protocol** — Gemini runs 3-5 hour unattended extraction sessions
- **Opus Audit Protocol** — Opus reviews each session's output for quality/coherence
- **Enriched Extraction Templates** — each extraction mode now has a concrete prompt template
- **Test Run Escalation** — start small, grow to full autonomy
- **Document Queue** — all 36+ source docs organized into processing waves

---

## 1) Two-Agent Architecture

### Gemini Worker (Extractor)
- **Job:** Read documents, extract concepts, write graph nodes/edges via `a2_graph_refinery.py`
- **Why Gemini:** Massive context window handles full documents without chunking loss
- **Mode:** Unattended. Reads its boot → reads docs → produces batches → saves graph → moves to next doc
- **Session length:** 3-5 hours per run
- **Output:** Updated `system_graph_a2_refinery.json`, `refinery_batch_index.json`, session log

### Opus Auditor (Reviewer)
- **Job:** Read Gemini's output, check quality, flag problems, selectively promote
- **Why Opus:** Stronger reasoning, better at catching contradictions and hallucinated connections
- **Mode:** Post-session review (30-60 min after each Gemini run)
- **Output:** Audit report, promoted A2-2 concepts, contradiction flags, A2-1 kernel candidates

### Interaction Flow
```
Gemini Worker → A2-3 intake batches → save to disk
                                         ↓
                        Opus Auditor reads output
                                         ↓
              Opus promotes to A2-2 / flags problems / promotes to A2-1
                                         ↓
                        Next Gemini session picks up where last left off
```

---

## 2) Gemini Worker Boot Sequence

A fresh Gemini session should read these files **in this exact order**:

1. `system_v4/a2_state/A2_BOOT__v1.md` — identity and hard rules
2. **This document** — process and protocol
3. `system_v4/skills/a2_graph_refinery.py` — the API it calls
4. `system_v4/a2_state/refinery_batch_index.json` — where the last session left off
5. `system_v4/a2_state/REFERENCE_REPOS.md` — pattern catalog

Then begin processing the next wave in the document queue (Section 5).

---

## 3) Enriched Extraction Templates

Each extraction mode now has a concrete template. The Gemini worker fills these templates per document.

### SOURCE_MAP_PASS
For each document, extract:
```
- Document identity: what is it, who wrote it, when, what context
- 5-15 core concepts (name + 2-3 sentence description + tags)
- Key claims made (as explicit propositions, not summaries)
- Dependencies: what other docs/concepts does this reference or assume
- Open questions or ambiguities the document leaves unresolved
```

### TERM_CONFLICT_PASS
For each document pair or cluster:
```
- Term: the word/phrase used differently across sources
- Definition A: how source A uses it (with source reference)
- Definition B: how source B uses it (with source reference)
- Nature of conflict: semantic drift / genuine disagreement / scope difference
- Resolution status: unresolved / resolvable / fundamental tension
```

### ENGINE_PATTERN_PASS
For each loop/cycle/engine found:
```
- Pattern name: what to call this engine
- Loop structure: the steps in order (A → B → C → A)
- Energy source: what drives it (input that sustains the loop)
- Termination condition: what stops or transforms the loop
- Instances: where this pattern appears in the source material
- Retoolable: can this be used in V4? How?
```

### MATH_CLASS_PASS
For each mathematical structure found:
```
- Structure name: what it is (group, algebra, manifold, etc.)
- Definition: the formal or semi-formal definition given
- Role in system: what job it does in the user's framework
- Classical vs nonclassical: does it import classical assumptions? How?
- Connections: what other structures does it relate to
```

### QIT_BRIDGE_PASS
For each physics/QIT connection:
```
- Physical concept: from the user's physics model
- QIT analog: the quantum information theory equivalent
- Bridge logic: why these map onto each other
- Strength: strong analogy / weak analogy / exact isomorphism
- Open issues: what doesn't map cleanly
```

### PERSONALITY_ANALOGY_PASS
For each personality/cognitive mapping:
```
- Cognitive function: the strategy or operator
- Mathematical operator: Te/Ti/Fe/Fi mapping
- Topological location: where on S3/Hopf/Bloch
- Entropy signature: positive/negative × high/low
- Behavioral prediction: what this predicts about behavior
```

### CONTRADICTION_REPROCESS_PASS
For each existing CONTRADICTS edge:
```
- Current contradiction: the tension as stated
- New evidence: anything from this pass that changes the picture
- Verdict: still contradictory / resolved / deepened / split into sub-contradictions
- Action: preserve / update description / create new edges
```

---

## 4) The Three Graph Layers (unchanged from v1)

| Layer | Trust Zone | Admissibility | Purpose |
|-------|-----------|---------------|---------|
| A2-3 | `A2_3_INTAKE` | `PROPOSAL_ONLY` | Outer. Raw extraction from source docs |
| A2-2 | `A2_2_CANDIDATE` | `PROPOSAL_ONLY` | Mid. Cross-doc synthesis, contradiction preservation |
| A2-1 | `A2_1_KERNEL` | `ADMITTED` | Inner. Highest-confidence control memory |

Promotion rules unchanged. Contradictions are edges, not errors.

---

## 5) Document Queue (Processing Waves)

**Entropy gradient principle:** Process most-refined material first, raw fuel last.
The graph builds its formal skeleton from CANON/specs before raw material arrives,
so contradictions between raw claims and established specs get caught automatically.

```
LOWEST ENTROPY ──────────────────────────────────────────────── HIGHEST ENTROPY
Wave 0   Wave 1      Wave 2       Wave 3-4    Wave 5      Wave 6    Wave 7     Wave 8-9   Wave 10-11
test     specs +     sims +       Axis/CANON  archived    v4 design prior V3   high-       future
run      megaboot    Thread S     + constraint A2 state   + audit   batches    entropy     even rawer
                     (old jargon) ladder                  + upgrade             raw docs
```

### Wave 0: Test Run (1-3 docs, ~30 min)
Purpose: Validate the pipeline works before committing to long runs.
```
1. core_docs/a2_feed_high entropy doc/x grok chat TOE.txt (small, 14K — already done)
2. core_docs/v4 upgrades/THREAD_CONTEXT_EXTRACT__MAX__2026_03_17__v1.md
3. core_docs/v4 upgrades/29 thing.txt
```
Expected: ~15-20 concept nodes, 2-3 contradiction edges.

### Wave 1: System Specs & Megaboot (LOWEST entropy, ~60 min)
**The most formal, refined material in the entire system.**
```
4. system_v3/specs/ (all spec docs — layer law, constraints, protocols)
5. core_docs/upgrade docs/BOOTPACKS/MEGABOOT_RATCHET_SUITE_v4.8 copy.md (core ratchet suite)
```

### Wave 2: Sims & Thread S Save (Very low entropy, ~60 min)
**Ratchet run results from web UI. Very low entropy but uses OLD term system.**
⚠️ Warning: old jargon throughout — user demanded no jargon later. Run TERM_CONFLICT_PASS after.
```
6. core_docs/a1_refined_Ratchet Fuel/sims/ (simulation results — hard data)
7. core_docs/a1_refined_Ratchet Fuel/THREAD_S_FULL_SAVE/ (full ratchet run snapshot)
```

### Wave 3: Refined Fuel — Axis 0 & CANON Specs (~60-90 min)
**Formal mathematical specifications.** Respect authority: CANON > DRAFT > NONCANON overlay.
```
8.  core_docs/a1_refined_Ratchet Fuel/CANON_GEOMETRY_CONSTRAINT_MANIFOLD_SPEC_v1.0.md (CANON)
9.  core_docs/a1_refined_Ratchet Fuel/AXES_MASTER_SPEC_v0.2.md (CANON)
10. core_docs/a1_refined_Ratchet Fuel/AXIS0_SPEC_OPTIONS_v0.3.md (latest version)
11. core_docs/a1_refined_Ratchet Fuel/AXIS0_PHYSICS_BRIDGE_v0.1.md
12. core_docs/a1_refined_Ratchet Fuel/AXIS_FOUNDATION_COMPANION_v1.4.md
13. core_docs/a1_refined_Ratchet Fuel/PHYSICS_FUEL_DIGEST_v1.0.md
14. core_docs/a1_refined_Ratchet Fuel/AXIS0_SPEC_OPTIONS_v0.1.md (earlier, for lineage)
15. core_docs/a1_refined_Ratchet Fuel/AXIS0_SPEC_OPTIONS_v0.2.md (earlier, for lineage)
```

### Wave 4: Refined Fuel — Constraint Ladder (~2-3 hours)
**50+ admissibility specs.** The constraint manifold formalized.
```
16. core_docs/a1_refined_Ratchet Fuel/constraint ladder/Constraints.md (base)
17. core_docs/a1_refined_Ratchet Fuel/constraint ladder/Base constraints ledger v1.md
18. core_docs/a1_refined_Ratchet Fuel/constraint ladder/Constraints. Entropy.md
19. core_docs/a1_refined_Ratchet Fuel/constraint ladder/CONSTRAINT_MANIFOLD_DERIVATION_v1.md
20. core_docs/a1_refined_Ratchet Fuel/constraint ladder/Axis 0.md
21. core_docs/a1_refined_Ratchet Fuel/constraint ladder/Axes 0 - 6 5 3 - 4 1 2.md
22. core_docs/a1_refined_Ratchet Fuel/constraint ladder/*_ADMISSIBILITY_v1.md (batch ~20 specs)
23. core_docs/a1_refined_Ratchet Fuel/constraint ladder/*contract*.md (batch contracts)
24. core_docs/a1_refined_Ratchet Fuel/constraint ladder/*rosetta*.md (batch rosetta mappings)
25. core_docs/a1_refined_Ratchet Fuel/constraint ladder/Axis *.md (remaining axis docs)
```

### Wave 5: Archived A2 Runtime State (~30 min)
**Archived old A2 state.** Prior system understanding, lower entropy than raw docs.
```
26. core_docs/a2_runtime_state archived old state/A2_SYSTEM_SPEC_v1.md
27. core_docs/a2_runtime_state archived old state/A2_INTENT_MANIFEST_v1.md
28. core_docs/a2_runtime_state archived old state/STRUCTURAL_MEMORY_MAP_v2.md
29. core_docs/a2_runtime_state archived old state/UPGRADE_STRUCTURAL_MAP_v1.md
30. core_docs/a2_runtime_state archived old state/A2_LOW_ENTROPY_LIBRARY_v4.md
31. core_docs/a2_runtime_state archived old state/ (remaining files)
```

### Wave 6: V4 Design Material & Upgrade Docs (~60-90 min)
**Design decisions, upgrade instructions, recent build waves.**
```
32. core_docs/v4 upgrades/lev_nonclassical_runtime_design_audited.md
33. core_docs/v4 upgrades/jp lev web outputs.txt
34. core_docs/v4 upgrades/jp graph suggestions.txt
35. core_docs/v4 upgrades/THREAD_CONTEXT_EXTRACT__MAX_RAW__2026_03_17__v1.md
36. core_docs/upgrade docs/ (bootpacks, extraction passes — batch as group)
37. work/audit_tmp/ (recent V4 build waves, Codex drafts)
```

### Wave 7: System V3 Tools & State (~60 min)
**Lower entropy than raw docs.** Tools and active state (specs already done in Wave 1).
```
38. system_v3/tools/ (all tool scripts as a batch)
39. system_v3/a2_state/ (owner surfaces as a batch)
```

### Wave 8: Prior V3 Refinery Output (~60 min)
**Already refined once** (V3 flat markdown batches). Lower entropy than raw docs.
```
40. system_v3/a2_high_entropy_intake_surface/ (421 existing batches — strongest only)
```

### Wave 9: High-Entropy Fuel (~2-3 hours)
**Highest entropy currently in the system. Process after everything above.**
```
41. core_docs/a2_feed_high entropy doc/Leviathan v3.2 word.txt (280K)
42. core_docs/a2_feed_high entropy doc/grok unified phuysics nov 29th.txt (407K)
43. core_docs/a2_feed_high entropy doc/holodeck docs.md (108K)
44. core_docs/a2_feed_high entropy doc/grok eisenhart model .txt
45. core_docs/a2_feed_high entropy doc/grok toe redo save.txt
46. core_docs/a2_feed_high entropy doc/axes math. apple notes dump.txt
47. core_docs/a2_feed_high entropy doc/apple notes save. pre axex notes.txt
48. core_docs/a2_feed_high entropy doc/grok gemini having digested the model.md
49. core_docs/a2_feed_high entropy doc/branchthread extract chat gpt.txt
50. core_docs/a2_feed_high entropy doc/branch part 2.txt
51. core_docs/a2_feed_high entropy doc/gpt thread a1 trigram work out .txt
52. core_docs/a2_feed_high entropy doc/thread b 3.4.2 .txt
53. core_docs/a2_feed_high entropy doc/thread b save.txt
54. core_docs/a2_feed_high entropy doc/A0 new thread save before sim run.md
```

### Wave 10: Cross-Wave Synthesis
```
55. TERM_CONFLICT_PASS across all A2-3 nodes
56. ENGINE_PATTERN_PASS across all A2-3 nodes
57. CONTRADICTION_REPROCESS_PASS on all CONTRADICTS edges
58. Opus-led A2-2 promotion of strongest cross-wave syntheses
59. Opus-led A2-1 kernel admission for highest-confidence concepts
```

### Wave 11: Future High-Entropy Material (added when system stabilizes)
**Placeholder.** Even higher entropy docs not yet in the repo.
Added by user as the attractor basin solidifies and can absorb more raw material.

---

## 6) Gemini Session Protocol

Each Gemini session follows this loop:

```
1. Boot (read boot docs + batch index + this process doc)
2. Pick next document from queue
3. Read the full document
4. Run appropriate extraction template
5. Call a2_graph_refinery.ingest_document() with extracted concepts
6. Log: batch_id, nodes added, edges added, layer totals
7. If time remains, go to step 2
8. At session end: save final graph state + write session summary
```

### Session Summary Format
After each session, the worker writes a summary to:
`system_v4/a2_state/session_logs/SESSION_{YYYY-MM-DD}_{NNN}.md`

Contents:
```
- Session ID and timestamp
- Documents processed (with batch IDs)
- Total nodes/edges added this session
- Running graph totals (A2-3 / A2-2 / A2-1)
- Key findings or surprises
- Contradictions discovered
- Next document in queue
```

---

## 7) Opus Audit Protocol

After each Gemini session, Opus reads:
1. The session summary
2. The latest `refinery_batch_index.json`
3. A sample of the new graph nodes (random or targeted)

Opus checks:
- **Concept quality:** Are extracted concepts meaningful or trivially obvious?
- **Compression quality:** Are concepts properly compressed (not copy-paste of source text)?
- **Contradiction detection:** Did Gemini miss obvious contradictions?
- **Hallucination check:** Did Gemini invent connections not in the source?
- **Consistency check:** Do new nodes properly reference existing ones?
- **Promotion candidates:** Which A2-3 nodes deserve A2-2 promotion?

Opus outputs:
- Audit report to `system_v4/a2_state/audit_logs/AUDIT_{SESSION_ID}.md`
- Direct A2-2 promotions via `promote_to_a2_2()` calls
- A2-1 kernel promotions (rare, only highest confidence)
- Annotations on existing nodes (properties updates)

---

## 8) Test Run Escalation Plan

| Run | Duration | Docs | Purpose | Gate to Next |
|-----|----------|------|---------|-------------|
| **Test 0** | 15 min | 1 doc (TOE chat, already done) | Verify pipeline | Graph has nodes ✓ |
| **Test 1** | 30 min | 3 docs (Wave 0) | Validate templates | Opus review passes |
| **Test 2** | 60 min | Wave 1 (specs + megaboot) | Core skeleton | Quality meets bar |
| **Test 3** | 60 min | Wave 2-3 (sims + Axis 0) | Formal math in graph | Opus audit clean |
| **Test 4** | 2-3 hrs | Waves 4-6 (constraint ladder + state + v4 design) | First long run | Opus audit clean |
| **Full Auto** | 3-5 hrs | Waves 7-9 (V3 tools + prior + high-entropy) | Production runs | Iterative refinement |

Each gate requires Opus audit approval before escalating.

---

## 9) All v1 Rules Still Apply

- One batch = one extraction mode (no mixing)
- Do not copy source text into node descriptions (compress)
- Do not modify A2-1 kernel without explicit promotion justification
- Contradictions are signal, not errors
- Graph is cumulative — later passes add, not replace
- Batch ID format: `BATCH_V4_{extraction_mode}_{subject}_{NNN}`

---

## 10) Outer Shell Architecture

The A2 refinery is the **inner core engine**. It does not run on or inside any external system. External systems sit on the **outermost shell** and interact with the refinery through its API.

```
┌─────────────────────────────────────────────────┐
│  OUTER SHELL (orchestration / infrastructure)   │
│                                                 │
│  Leviathan OS ─── the platform this system      │
│                   runs ON when finished.         │
│                   Shared constraints/philosophy. │
│                   Own graph adapters, evolve-    │
│                   memory, semantic runtime.      │
│                                                 │
│  AutoResearchClaw ─ chat UI / mobile interface. │
│                     Monitor long runs from phone.│
│                     Queue new sessions.          │
│                     See progress in real time.   │
│                                                 │
│  pi-mono ───────── agentic tooling packages.    │
│                     Session scheduling,          │
│                     Gemini↔Opus handoff.         │
│                                                 │
├─────────────────────────────────────────────────┤
│  INNER CORE (refinery engine)                   │
│                                                 │
│  a2_graph_refinery.py ─ graph builder API       │
│  Extraction templates ─ concept compression     │
│  Promotion gates ────── trust zone boundaries   │
│  A2-3 / A2-2 / A2-1 ── nested graph layers     │
│                                                 │
└─────────────────────────────────────────────────┘
```

**Rules:**
- Outer shell tools **never write to the graph directly** — they call the refinery API
- Leviathan's constraints mirror Codex Ratchet's but are its own — shared philosophy, separate enforcement
- Claw provides the user's window into long runs — status checks, queue management, not graph mutation
- Inner core is self-contained and runnable without any outer shell tools

---

## 11) Iterative Refinement

This process document itself is living infrastructure:
- After each Opus audit, update this doc with lessons learned
- Add new extraction modes as needed
- Adjust templates based on what works
- The method refines itself through use
