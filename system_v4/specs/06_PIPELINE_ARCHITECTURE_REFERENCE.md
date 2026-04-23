# Pipeline Architecture Reference — Anti-Drift Guide

This document captures the **actual** pipeline architecture constraints from
MEGABOOT_RATCHET_SUITE_v7.4.9 and direct user corrections. This exists to
prevent future A2 threads from drifting into classical-biased thinking.

## Core Principle: Nothing Is Canon Until It Ratchets

- All ideas, axes, engine orders, topologies are **rough proposals**
- The system **discovers** what ratchets through exploration, not pre-decision
- Do NOT hardcode axis orderings, engine structures, or topology choices
- Do NOT treat user proposals as specifications — they are fuel for exploration

## Layer Roles

### A1 — The Branching Engine (LLM / Narrative)
- Makes **lots** of different narratives and branches
- Spawns "lawyers" to argue things OUT of the graveyard
- Maximally exploratory and creative
- Generates diverse candidate structures for A0 to compile

### A0 — The Unbiased Compiler (Deterministic)
- Has **no bias** about what should ratchet
- **Wants it all** — compiles everything A1 produces
- Emits large exploratory batches, not conservative ones (MEGABOOT line 533)
- Must target >= 50% graveyard rescue share in batches (MEGABOOT line 51)

### B — Structural Adjudicator (Deterministic)
- Mechanical structural checking only
- ACCEPT / PARK / REJECT verdicts
- No opinions, no inference

### SIM — Terminal Executor (Deterministic, Non-LLM)
- Tests constructs deterministically
- Packages evidence
- Does NOT contain the science method or engine stages

### Graveyard — Living Recycling System
- **Mandatory and never dead** (MEGABOOT line 49)
- Must be **larger** than active ratcheted canon (MEGABOOT line 50)
- Dead branches are **signal**, not waste (MEGABOOT line 538)
- Continuously mined for rescue attempts (MEGABOOT line 538)

### Holodeck — DEFERRED
- Built after the system stabilizes
- Reflects attractor basins and QIT engines
- The 16 stages = 8 engine stages × 2 engine types
- NOT the same as SIM
- Like eyes having a direct brain connection vs other senses

## Anti-Drift Rules
1. Do not pre-decide what ratchets
2. Do not treat rough ideas as canon specifications
3. Do not hardcode axis orders (even 0-6-5-3-4-1-2 is just a proposal)
4. Do not filter at the A0 level — A0 wants everything
5. The Graveyard is a courtroom, not a cemetery
6. There may be 0-12 axes, not 0-6 — the other 6 mirror the first 6
7. Engine loop orders must ALL be tested, not pre-selected
