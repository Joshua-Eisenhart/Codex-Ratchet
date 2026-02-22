# Public-Facing Layered Architecture and Entropy Boundary (v1)
Status: PUBLIC / NONCANON (explanatory only)
Date: 2026-02-20

This system is intentionally split into layers by entropy (degrees of freedom / ambiguity). The boundary between “high-entropy thinking” and “low-entropy canon” is the key discipline.

## Named Layers (A/B Labels → Intent Names)
These names are intended to be more descriptive than “Thread A/B/C.”

- **A2 = Miner / Prospector (High Entropy)**
  - Function: mine candidate ideas, patterns, alternative formulations, and “fuel.”
  - Outputs: notes, queues, proposed targets, alternative framings.
  - Not allowed: declaring canon.

- **A1 = Rosetta / Translator (Medium-High Entropy)**
  - Function: take a domain model (often jargon-heavy) and produce:
    - a *cold-core* formal candidate (minimal primitives, explicit dependencies)
    - optional Rosetta overlays (multiple vocabularies pointing to the same cold core)
  - Not allowed: smuggling domain assumptions into kernel artifacts.

- **A0 = Deterministic Compiler / Canonicalizer (Low Entropy; Hard Boundary)**
  - Function: compile/validate A1/A2 proposals into strict kernel-eligible artifacts.
  - The law: **only compiled artifacts may touch the kernel.**
  - Not allowed: inventing or “helpfully rewriting” meaning outside of deterministic compilation rules.

- **B = Constraint Kernel / Admission Judge (Ultra-Low Entropy; Canon Authority)**
  - Function: deterministic staged evaluation (ADMIT / PARK / REJECT).
  - Owns: canonical constraint surface + ordering + policy gates.
  - Not allowed: running sims or free-form interpretation.

- **SIM = Evidence Engine / Deterministic Executor (Low Entropy)**
  - Function: execute sims and emit structured evidence artifacts.
  - Produces: positive evidence, negative evidence, stress evidence; all replayable.
  - Not allowed: mutating canon directly; evidence is ingested via kernel rules.

## The Entropy Compression Boundary
The boundary is the transition from:
- high-entropy proposals (natural language, mixed metaphors, field-specific jargon)
to
- low-entropy artifacts (strict grammar, explicit dependencies, deterministic evaluation)

Practical enforcement:
- Kernel-facing artifacts use a strict container grammar.
- Free English is not permitted to “accidentally become” active lexemes in canon.
- Every dependency is explicit.
- Every survivor must be evidence-backed (SIM) and contrasted against failed alternatives (graveyard).

## Feedback Loops (High-Level)
1. Miner finds candidate structure families and failure modes.
2. Rosetta translates to cold-core candidates + optional overlay dictionaries.
3. Compiler emits strict artifacts.
4. Kernel admits/parks/rejects, producing canon state updates and graveyard entries.
5. Evidence engine runs sims; emits positive + negative evidence.
6. Kernel ingests evidence deterministically, tightening the constraint surface.

## Where FlowMind Fits (Conceptual Mapping)
If you think in “kernel + translator boundary + provenance” terms:
- A2/A1 resemble high-entropy “FlowMind modules” operating on messy inputs.
- A0 is the translator boundary where outputs become kernel-safe.
- B is the admission kernel (not a scheduler).
- SIM is a deterministic execution harness.

