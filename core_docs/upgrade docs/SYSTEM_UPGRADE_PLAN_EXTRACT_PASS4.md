# SYSTEM_UPGRADE_PLAN_EXTRACT_PASS4

VERBATIM INTENT EXTRACTION — NO RESOLUTION

[This pass preserves raw intent, contradictions, and partial thoughts.
No reconciliation. No design.]

--- RAW THEMES ---

- Megaboot is a SINGLE DOCUMENT containing all boots.
- Earlier work mistakenly upgraded split bootpacks instead of megaboot.
- Zips are an UPGRADE to how threads communicate, not a replacement of megaboot concept.
- Determinism core remains: FINITUDE, NONCOMMUTATION.

--- THREAD INTENT (AS STATED, CONFLICTS PRESERVED) ---

- A1:
  - Chatty.
  - Boundary controller.
  - Has explicit MODES to constrain LLM failure modes:
    hallucination, drift, smoothing, narrative, helpfulness.
  - Modes are real behavioral constraints, not labels.
  - Modes are noncommutative.
  - A1 emits proposals only.
  - A1 may need its own context-save / transport mechanism.

- A0:
  - Deterministic.
  - Absorbs Thread S and SIM coordination roles.
  - Orchestrates B and terminal SIM.
  - Compiles proposals deterministically.
  - Must never hallucinate or interpret.

- B:
  - Deterministic canon kernel.
  - Ratchets constraints.
  - Accepts or rejects.

- SIM TERMINAL:
  - External.
  - Deterministic.
  - Executes only approved simulations.

--- ZIP INTENT (RAW) ---

- ZIPs are deterministic, chatless subagents.
- ZIPs never split.
- Docs inside ZIP shard.
- ZIP ingestion = one-line deterministic action.
- ZIPs may contain:
  - machine payload
  - intent
  - manifest
  - contracts
- Confusion occurred between:
  - template ZIPs
  - extracted ZIPs
  - system ZIPs

--- SIM PIPELINE (RAW) ---

- A0 sends SIM_PROPOSAL to B.
- B approves or rejects.
- Approved SIM_RUN goes to terminal.
- Terminal produces results.
- Results go back to A0.
- A0 packages SIM_EVIDENCE to B.

--- GRAVEYARD (RAW) ---

- Graveyard is mandatory.
- Graveyard is never dead.
- ≥50% interaction when non-empty.
- Graveyard is exploration fuel.
- Size: big enough to be useful, not maximal.

--- ROSETTA / MINING (RAW) ---

- Rosetta = experimental overlay.
- Alternative dictionary / weighted labels.
- Mining discovers new ratchetable proposals.
- Rosetta is not canon.
- Validation only via ratchet + sims.

--- FAILURE & CONFUSION LOG ---

- Megaboot vs bootpacks conflated.
- ZIP template vs ZIP extraction conflated.
- Thinking vs instant mode drift.
- LLM summarization destroying density.
- File generation tool sometimes failing to persist artifacts.
- Mode drift during long threads.
- Extraction tools conflated with solution design.

--- META INTENT ---

- Need transport of WORK DONE, not solutions.
- Want bulk detail, contradictions, ambiguity.
- No fixing during extraction.
- Use multiple passes.
- Accept redundancy.
- Avoid Goodhart collapse.

END PASS 4
