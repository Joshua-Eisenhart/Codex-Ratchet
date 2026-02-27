# SYSTEM UPGRADE WORK — STATE EXTRACTION (PASS 1)

MODE: STATE_EXTRACTION_ONLY
SOURCE: Entire preceding conversation (authoritative)

---

## CORE INTENT (RAW)

- Upgrade the **existing megaboot** (single document containing all boots).
- Introduce **ZIP-first communication** between threads (A0, B, SIM), without redesigning core constraints.
- Preserve sacred constraints:
  - FINITUDE
  - NONCOMMUTATION
- Shift from conservative / proof-first reasoning to **mass constraint exploration → basin convergence**.
- Increase scale, speed, and batch size of ratcheting.
- Avoid LLM drift toward classical reasoning patterns.

---

## THREAD MODEL — INTENDED STATE (AS DISCUSSED)

### A1 (Meta / Boundary / Chatty)
- Chatty, non-deterministic internally.
- Controls LLM failure modes:
  - hallucination
  - drift
  - smoothing
  - narrative bias
  - helpfulness bias
- Uses **explicit modes** to constrain behavior.
- Modes are REAL constraints, not labels.
- Mode changes are non-commutative.
- A1 emits **proposals only**, never canon.
- A1 must assert active mode on output.
- A1 will eventually need:
  - context-save / transport capability
  - ability to confirm its own load state
- Friend’s graph/intent prompt discussed as a way to act as “reins” on A1 behavior.

### A0 (Deterministic Orchestrator)
- Fully deterministic.
- Absorbs former Thread S and Thread SIM coordination roles.
- Orchestrates:
  - ratchet batches
  - graveyard interaction
  - sim approval and routing
- Cannot hallucinate, interpret, or narrate.
- Accepts or refuses A1 proposals explicitly.
- Loads B with only required material.
- Confirms B load.
- Coordinates SIM TERMINAL.

### B (Canon Kernel)
- Deterministic.
- Enforces ratchet constraints.
- Approves or rejects:
  - ratchet proposals
  - sim proposals
- Holds canonical state.
- Does not need megaboot; only its own boot + loaded state.

### SIM TERMINAL
- External, non-LLM.
- Deterministic executor.
- Executes only approved SIM_RUN artifacts.
- Returns results as artifacts (never interpretation).

---

## ZIP AS COMMUNICATION PRIMITIVE

- ZIPs are:
  - atomic
  - deterministic
  - chatless subagents
- ZIPs never split.
- Documents inside ZIPs may shard (size limits).
- ZIP ingestion is a **single-line deterministic action**.
- ZIPs may contain:
  - proposals
  - evidence
  - sim runs
  - state transports
- Discussion that ZIPs function like deterministic subagents or “frozen processes”.

---

## SIM PIPELINE (AS DESCRIBED)

- SIM flow:
  1. A0 creates SIM_PROPOSAL artifact.
  2. B approves or rejects.
  3. Approved proposal → SIM_RUN artifact.
  4. SIM TERMINAL executes.
  5. Results returned as artifacts.
  6. A0 packages evidence.
  7. B ingests evidence.

- Two ZIPs per sim:
  - SIM_PROPOSAL_ZIP (to B)
  - SIM_RUN_ZIP (to terminal)

- Hash binding discussed:
  - baseline state
  - proposal
  - input
- SIM never invents or interprets.

---

## GRAVEYARD PHILOSOPHY (RAW)

- Graveyard is mandatory.
- Graveyard is never dead.
- ≥50% of batches must interact with graveyard when non-empty.
- Graveyard is exploration fuel, not failure.
- Graveyard size:
  - not maximal
  - “big enough to be useful”
- Dead branches are valuable.
- Attempting to revive dead branches is desirable.

---

## ROSETTA / MINING (RAW)

- Rosetta ≠ canon.
- Rosetta = experimental overlay + mining.
- Acts as:
  - alternative dictionary
  - weighted labeling system
- Can propose ratchetable terms.
- Must not directly modify canon.
- Validation only via ratchet + sims.
- Rosetta originally conflated with Thread S; later corrected.
- Possible future need to validate Rosetta overlays via sims.

---

## BOOT / LOAD SEQUENCE (AS DISCUSSED)

- A1 loads:
  - full++ or equivalent context.
- A1 confirms load.
- A0 loads B with required material only.
- A0 confirms B.
- A0 orchestrates remaining initialization.
- Legacy Thread S assumptions explicitly rejected.

---

## SCALE CONSIDERATIONS (RAW NOTES)

- System must scale to:
  - very large ratchets
  - huge artifact sets
- ZIP sharding needed.
- LLMs struggle with long files.
- Multi-LLM compatibility required (Claude, Kimi, etc.).
- Human-usable now; automatable later.
- Extraction and transport of context itself identified as a core unsolved problem.

---

## CONTRADICTIONS / OPEN CONFUSION (PRESERVED)

- Thread S role:
  - sometimes demoted
  - sometimes absorbed by A0
  - sometimes reintroduced accidentally
- Megaboot confusion:
  - megaboot is a **single document**
  - was mistakenly treated as split or ZIP-based during attempts
- Difficulty controlling LLM mode deterministically.
- Extraction tooling drifting into summarization.
- Whether A0 should fully absorb SIM coordination vs keep SIM distinct.
- How to reliably confirm LLM mode changes.
- How to prevent context drift in very long threads.

---

## META OBSERVATIONS (RECORDED, NOT RESOLVED)

- LLMs drift toward classical proof reasoning by default.
- Constraint-based exploration is counter to LLM instincts.
- Strong emotional language and model switching used to force implicit mode shifts.
- A1 mode control seen as “horseback riding”, not deterministic engineering.
- Extraction itself identified as a system feature, not just a tooling step.

---

END OF PASS 1
