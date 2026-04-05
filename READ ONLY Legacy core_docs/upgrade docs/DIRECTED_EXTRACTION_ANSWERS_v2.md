
# DIRECTED EXTRACTION — ANSWERS (DENSE)

## QUESTION SET A — ZIP ENUMERATION
ZIP kinds explicitly discussed or implied in this thread (verbatim phrases preserved where possible):

- **ZIP_JOB / ZIP as subagent**
  - Producer: A0 / A1 / B (context-dependent)
  - Consumer: A0, B, SIM TERMINAL
  - Purpose: "ZIPs are deterministic, chatless subagents"; "ZIPs are atomic (never split)"; "ZIP ingestion is a single-line deterministic action".

- **FULL_LEDGER_ZIP (FULL+)**
  - Producer: B (compiled), sometimes via A0
  - Consumer: A0 (confirm), restore path to B
  - Purpose: Canon restore carrier; "FULL+ save could be done by B, then sent to A0 to be confirmed".

- **FULL++ (ROSETTA AUGMENTED) ZIP**
  - Producer: A1 (rosetta/mining overlay)
  - Consumer: A0 (structural confirmation), A1 reload
  - Purpose: "A1 will do the FULL++ save with the rosetta, but needs A0 to also confirm".

- **SIM_PROPOSAL_ZIP**
  - Producer: A0
  - Consumer: B
  - Purpose: Approval gate; binds baseline + proposal + input.

- **SIM_RUN_ZIP**
  - Producer: A0
  - Consumer: SIM TERMINAL
  - Purpose: Deterministic execution package; terminal only executes.

- **SIM_RESULTS_ZIP / SIM_FAILURE_ZIP**
  - Producer: SIM TERMINAL
  - Consumer: A0
  - Purpose: Results or failure returned; no invention.

- **SIM_EVIDENCE_ZIP**
  - Producer: A0
  - Consumer: B
  - Purpose: Evidence ingestion after execution.

- **ROSETTA_OVERLAY_ZIP (PROPOSED)**
  - Producer: A1
  - Consumer: A0
  - Purpose: "Alternative dictionary / weighted labeling"; proposals only; never canon.

UNSPECIFIED — DO NOT INFER


## QUESTION SET B — A0 MASSIVE BATCH POLICY
Extracted statements (dense):

- "A0 is failing due to small batches."
- "Force a0 to make big batches."
- "A0 always has something."
- "Batches dont need to be conservative."
- "Constraint systems begin with a massive set of things. Then converge towards attractor basins."
- "≥50% of batches must interact with graveyard when non-empty."
- "Massive exploratory batching required."
- Numbers:
  - "1000 things from a0 to b in one doc" (example appears; ambiguity preserved).

Ambiguity:
- Whether 1000 is hard target or illustrative.
- Phase-dependence (exploration vs convergence) mentioned but not numerically fixed.

UNSPECIFIED — DO NOT INFER


## QUESTION SET C — SHARDING STRATEGY HEURISTICS
Extracted statements:

- "Docs inside ZIP need size limits. Llms dont like long files."
- "ZIP never splits; docs inside ZIP shard."
- "Shards is one aspect of scale."
- "Sharding must be good for LLM usage."

Implicit heuristics mentioned (without final resolution):
- Semantic separation vs chronology vs failure domains (discussed as considerations).
- No hard token/line limits finalized.

UNSPECIFIED — DO NOT INFER


## QUESTION SET D — FULL+ CONFIRMATION
Extracted statements:

- "FULL+ save is fine. B can make it afterall."
- "A0 can validate a full ++ formatting. Send back to a1 if wrong."
- "A0 loads B with only the save material it needs."

Ambiguity:
- Confirmation meaning (hash vs completeness vs sanity) not finalized.
- Refusal behavior discussed conceptually but not operationally fixed.

UNSPECIFIED — DO NOT INFER


## QUESTION SET E — FULL++ CONFIRMATION
Extracted statements:

- "FULL++ feeds both a1 and a0."
- "A1 only sends proposals. A0 must be sensitive and strict with that."
- "A1 emits proposed full++?" (explicit clarification requested).
- "A1 will do the FULL++ save with the rosetta, but needs A0 to also confirm."

Ambiguity:
- Required vs optional confirmation unresolved.
- Structural vs content-blind confirmation unresolved.

UNSPECIFIED — DO NOT INFER


## QUESTION SET F — PHASE TRANSITION SIGNALS
Extracted statements:

- "Exploration phase" vs "convergence phase" explicitly distinguished.
- "Strong basin attractors emerge."
- "Identifying those systematically independent of my rosetta overlays would be interesting."
- "Graveyard cant be as big as possible. But must be bigger than the ratcheted terms."

Ambiguity:
- Metrics (acceptance ratio, churn) mentioned but not locked.
- Human judgment acknowledged.

UNSPECIFIED — DO NOT INFER

