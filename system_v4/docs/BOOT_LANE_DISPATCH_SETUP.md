# [Controller-safe] Boot Lane Dispatch Setup

**Status:** Setup surface for boot-scoped worker lanes.  
**Purpose:** Prevent boot non-ingestion and reduce smoothing by splitting work into explicit booted lanes with bounded scopes, outputs, and stop conditions.  
**Mode:** Use this when launching separate Codex threads or future booted subagents.

---

## Why This Exists

The failure is not only bad synthesis. The deeper failure is:

- boot files not being read first
- carrier grammar being flattened into runtime grammar
- runtime grammar being flattened into scaffold grammar
- broad A1 exploration being forced too early into B-style strictness

So the working architecture should be:

```text
A0 lane = controller / queue / graveyard / route
A1 lanes = broad branch generation under bounded boots
B lane = formal sequestration / admissibility / anti-collapse
SIM lane = lower-loop runtime evidence
shared repo = handoff memory surface
```

This file defines those lanes as separate boot-scoped workers.

---

## Dispatch Rules

1. No lane may start before loading its listed boot files.
2. No lane may synthesize outside its allowed claim class.
3. All returns must write or point to repo-held artifacts.
4. Graveyard/failed branches are first-class outputs, not cleanup.
5. Lanes may hand work forward, but may not silently absorb another lane's role.

---

## Lane Registry

### `A0_CONTROLLER`

- **Purpose:** Queue manager, graveyard manager, boot enforcer, dispatch router.
- **Suggested reasoning:** `high` or `xhigh` when designing batches; `medium` for routine queue work.
- **Primary boots:**
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/docs/DOC_AUTHORITY_MAP.md`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/docs/FAILURES_AND_CORRECTIONS_AUDIT.md`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/docs/PHENOMENOLOGICAL_DESIGN_RULES.md`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/docs/RUNTIME_TO_STRUCTURE_BRIDGE.md`
- **Allowed actions:**
  - dispatch lanes
  - route artifacts
  - maintain graveyard and queue state
  - block invalid work before it starts
- **Forbidden actions:**
  - invent axis math
  - promote exploratory wins into canon
  - run wide sims directly unless no sim lane exists
- **Expected outputs:**
  - queue notes
  - dispatch packets
  - graveyard routing decisions
- **Stop condition:** once next-batch routing and handoff are explicit.

### `A1_WIGGLE_CARRIER`

- **Purpose:** Broad branch exploration over candidate carrier and manifold families.
- **Suggested reasoning:** `xhigh` now, `medium`/`high` later for routine follow-ons.
- **Primary boots:**
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/CANON_GEOMETRY_CONSTRAINT_MANIFOLD_SPEC_v1.1.md`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/docs/GEOMETRY_RATCHET_CHAIN.md`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/docs/PHENOMENOLOGICAL_DESIGN_RULES.md`
- **Allowed actions:**
  - generate multiple carrier/manifold candidates
  - compare spinor / S3 / Hopf / density roles
  - preserve branch residue and contradictions
- **Forbidden actions:**
  - declare runtime closure
  - reduce carrier to density because it is easier
  - rewrite owner geometry from metaphor
- **Expected outputs:**
  - candidate family tables
  - graveyard entries
  - branch pressure notes
- **Stop condition:** once candidate families and rejected branches are explicitly separated.

### `A1_WIGGLE_ENGINE_GRAMMAR`

- **Purpose:** Broad branch exploration over loop/stage/type/terrain/operator grammar without closing it too early.
- **Suggested reasoning:** `xhigh` now, `high` later.
- **Primary boots:**
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/ultra high entropy docs/txt/GPT 12_29 pro plan vs browser crashes.md.txt`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/QIT_GRAPH_LAYER_MAPPING.md`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/QIT_GRAPH_RUNTIME_MODEL.md`
- **Allowed actions:**
  - extract discrete grammar objects
  - compare runtime flattening against owner grammar
  - enumerate possible ownership/order variants
- **Forbidden actions:**
  - flatten type, flow, precedence, and chirality into one sign
  - treat current runtime as already faithful
  - throw away high-entropy owner statements because they are inconvenient
- **Expected outputs:**
  - grammar slices
  - mismatch lists
  - owned-vs-flattened comparison tables
- **Stop condition:** once discrete grammar objects and runtime mismatches are explicit.

### `A1_WIGGLE_MATH_FAMILIES`

- **Purpose:** Explore candidate math families such as Carnot-like, Szilard-like, transport, hysteresis, coherence, operator accounting.
- **Suggested reasoning:** `high` or `xhigh` for design; `medium` or `high` for later repeated sweeps.
- **Primary boots:**
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/docs/PHENOMENOLOGICAL_DESIGN_RULES.md`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/docs/FAILURES_AND_CORRECTIONS_AUDIT.md`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/sim_proto_b_runtime_wiggle.py`
- **Allowed actions:**
  - build candidate-family probes
  - compare signed vs absolute behaviors
  - keep controls and dead candidates visible
- **Forbidden actions:**
  - call any family canonical
  - let control families masquerade as validated structure
  - claim FEP or thermodynamics are integrated unless live bridge exists
- **Expected outputs:**
  - exploratory sim files
  - result JSONs
  - family-level readouts with inactive reasons
- **Stop condition:** once live vs dead vs unstable families are separated.

### `B_SEQUESTRATION`

- **Purpose:** Formal anti-collapse ratchet. Operates on A1/graveyard outputs, not on vague summaries.
- **Suggested reasoning:** `xhigh` now, `high` later.
- **Primary boots:**
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a2_feed_high entropy doc/A0 new thread save before sim run.md`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/docs/FAILURES_AND_CORRECTIONS_AUDIT.md`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/docs/RUNTIME_TO_STRUCTURE_BRIDGE.md`
- **Allowed actions:**
  - admissibility checks
  - order/dependency checks
  - layer separation
  - graveyard-fed ratcheting
- **Forbidden actions:**
  - broad exploration
  - metaphor-first reasoning
  - skipping branch residue
  - promoting lower-loop absence into upper-loop closure
- **Expected outputs:**
  - admissibility judgments
  - preserved contradictions
  - narrowed proposal surfaces
- **Stop condition:** once outputs are sorted into survives / fails / unresolved.

### `SIM_RUNTIME`

- **Purpose:** Lower-loop runtime evidence producer. May run sims, but does not interpret beyond allowed evidence class.
- **Suggested reasoning:** `high` for new harnesses, `medium` for repeated runs, `low` later for stable routine reruns.
- **Primary boots:**
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/engine_core.py`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/docs/PHENOMENOLOGICAL_DESIGN_RULES.md`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/docs/RUNTIME_TO_STRUCTURE_BRIDGE.md`
- **Allowed actions:**
  - run engine/runtime/native sims
  - export traces and result packets
  - produce bounded evidence summaries
- **Forbidden actions:**
  - axis canon claims
  - structural 64 closure claims
  - replacing spinor carrier with easier projections without explicit downgrade
- **Expected outputs:**
  - sim artifacts
  - traces
  - runtime evidence summaries
- **Stop condition:** once evidence is written and bounded readout is complete.

---

## Shared Repo Contract

All lanes should hand off through repo-held artifacts, not chat memory:

- docs -> `system_v4/docs/`
- probes -> `system_v4/probes/`
- sim outputs -> `system_v4/a2_state/sim_results/` or `system_v4/probes/a2_state/sim_results/`
- graveyard/closeout packets -> repo-held packet surfaces, not only thread text

---

## Launch Order

Recommended boot order for hard cases:

1. `A0_CONTROLLER`
2. `A1_WIGGLE_CARRIER`
3. `A1_WIGGLE_ENGINE_GRAMMAR`
4. `SIM_RUNTIME`
5. `A1_WIGGLE_MATH_FAMILIES`
6. `B_SEQUESTRATION`

Why:
- A1 must branch before B over-tightens.
- SIM should produce lower-loop pressure before B closes anything.
- B should ratchet from branch residue and graveyard, not from a smoothed executive summary.

---

## Practical Note

If subagents cannot recursively boot subagents, use separate Codex threads with this file as the launch surface. The shared repo removes the need for manual copy-paste closeouts; the controller thread can simply route workers to the right artifacts and queue the next `go on`.
