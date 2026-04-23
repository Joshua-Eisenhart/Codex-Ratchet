# GPT Pro Architecture Audit

> **Source**: GPT Pro analysis, 2026-03-22. Saved as durable reference for A2 architecture decisions.

## Core Thesis

**Make the LLM a temporary actuator over a permanent self-graph.**
A2 maintains the self-graph, A1 shapes disposable branch context from it, and only A0/B/SIM are allowed to turn soft geometry into hard ratchet truth.

## Two-Body Architecture

### Body 1: Hard Ratchet Graph (discrete, typed, append-only, authority-aware)
- Persists, rehydrates, survives model/thread death
- Canonical state: `memory.jsonl`, `doc_index.json`, `fuel_queue.json`, `rosetta.json`, `constraint_surface.json`
- Runtime image: `canonical_ledger/`, `snapshots/`, `current_state/`, `cache/`

### Body 2: Soft Geometry Field (quaternions, tensors, Hopf-torus, correlation fields)
- Explore, route, visualize, score — **not** the source of truth
- Projects downward into typed claims before A0/B sees it

## 12 Nested Graphs

| # | Graph | Purpose |
|---|-------|---------|
| 1 | Root-constraint | F01_FINITUDE, N01_NONCOMMUTATION, derived-only guards |
| 2 | Authority/boot | A2→A1→A0→B→SIM operational routes |
| 3 | Intent | Goals, preferences, tensions, priority shifts |
| 4 | Self-model | System beliefs about itself: components, limits, modes, blind spots |
| 5 | Target | Thing being ratcheted: concepts, invariants, open questions |
| 6 | Artifact/provenance | Docs, zips, patches, saves, hashes, lineage |
| 7 | Concept/invariant | Terms, math defs, sims, constraints, allowed/blocked states |
| 8 | Skill | Every skill as a node with preconditions, outputs, cost, authority, evidence |
| 9 | Proposal/branch | A1 lanes, alternatives, attacks, rescues, contradiction maps |
| 10 | Runtime/session | Live runs, state snapshots, active lanes, mode declarations |
| 11 | Evidence/graveyard | SIM evidence, kill signals, neg classes, rescue paths |
| 12 | Latent geometry | Quaternions, tensors, Hopf-torus, attractors (**never primitive canon**) |

> Graphs 1–11 matter to ratchet truth. Graph 12 helps route but must project into typed claims first.

## Rich Edge Schema

```
edge = {
  relation_type, sign, corr, anti, tension, confidence,
  pos_evidence, neg_evidence, graveyard_pressure, projector
}
```

- `projector` = the rule that turns soft edge into hard claim

## A2 Mode Routing (hard modes)

| Mode | Function |
|------|----------|
| REHYDRATE | Restore from artifacts |
| MAP | Scan for structural understanding |
| DIFF | Detect structural deltas only |
| PACKETIZE | Emit packets for A1 |
| AUDIT | Verify self-model integrity |

## A1 Role: Packet Generator, Not Prose Reasoner

Always emit: steelman / alt-formalism / boundary-repair / adversarial-neg / rescuer lanes.

## 4 Required Deltas Per Persistent Append

1. **Intent delta** — what you want changed
2. **Self delta** — what the system believes about itself changed
3. **Target delta** — what the ratcheted object changed
4. **Evidence delta** — what justified the change

## Build Priority

1. Lock persistence substrate (keep current A2 canonical files)
2. Define 12 graph schemas (JSON/JSONL-backed typed objects)
3. Make skills first-class nodes ← **CURRENT STEP**
4. Implement A2 mode routing
5. Make A1 a true branch orchestrator
6. Add geometry layer last
