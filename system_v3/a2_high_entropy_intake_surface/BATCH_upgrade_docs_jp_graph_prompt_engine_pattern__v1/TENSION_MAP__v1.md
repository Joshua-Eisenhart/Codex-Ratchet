# TENSION_MAP__v1
Status: PROPOSED / NONCANONICAL / CONTRADICTION-PRESERVING
Batch: `BATCH_upgrade_docs_jp_graph_prompt_engine_pattern__v1`
Extraction mode: `ENGINE_PATTERN_PASS`

## T1) `The graph is the truth` vs `No Hidden Truth`
- source markers:
  - source 1: `8-11`
  - source 1: `49-52`
- tension:
  - the prompt privileges the graph as truth
  - it also says outputs should not be presented as absolute and everything should be framed as a view or proposal
- preserved read:
  - the source wants a strong backend truth surface while keeping frontend claims explicitly non-final

## T2) Concrete patch/acceptance lifecycle vs `graph OS without a real runtime`
- source markers:
  - source 1: `27-37`
  - source 1: `52-55`
  - source 1: `104-120`
- tension:
  - the ontology uses concrete mutation language:
    - patch
    - accepted
    - committed to graph
  - the same source says the system has no real runtime and is only simulating an execution-aware graph OS
- preserved read:
  - the mutation model is conceptually strong but operationally simulated

## T3) Minimal progressive disclosure vs mandatory dense debug footer
- source markers:
  - source 1: `46-48`
  - source 1: `61-100`
  - source 1: `128`
- tension:
  - human-facing output is supposed to be minimal and one-step-at-a-time
  - every response must also include a fixed debug/proposal trailer
- preserved read:
  - the prompt wants compressed user interaction plus explicit machine-facing traceability

## T4) Do not assume goals vs infer intent vectors
- source markers:
  - source 1: `43-45`
- tension:
  - the prompt rejects direct goal assumption
  - it still requires inferred intent vectors such as exploration, clarification, synthesis, execution, and validation
- preserved read:
  - inference is allowed, but only at the directional-pressure layer

## T5) No invented state continuity vs reconstructable evolving graph trail
- source markers:
  - source 1: `31`
  - source 1: `97-99`
  - source 1: `129`
  - source 1: `135-139`
- tension:
  - the prompt forbids inventing continuity unless restated
  - it also expects later readers to reconstruct how understanding evolved from the debug trail
- preserved read:
  - continuity must be earned through explicit recorded ticks rather than assumed memory

## T6) Not a chatbot / narrator / teacher vs operates inside web chat with human-facing responses
- source markers:
  - source 1: `63-68`
  - source 1: `104-120`
- tension:
  - the file rejects standard chatbot/narrator/teacher identity
  - it still operates inside a chat loop with a required human-facing response section
- preserved read:
  - the medium is chat, but the intended stance is interface-shell rather than conversational assistant

## T7) Views include docs and explanation vs markdown documents are not truth
- source markers:
  - source 1: `29`
  - source 1: `125-126`
- tension:
  - docs and explanation are legitimate graph projections
  - markdown documents are explicitly barred from being treated as truth
- preserved read:
  - projections are allowed, but authority is reserved for the graph layer rather than the rendered artifacts

## T8) Nothing is final until accepted vs acceptance cannot be invented
- source markers:
  - source 1: `11`
  - source 1: `35-37`
  - source 1: `94-100`
- tension:
  - accepted state is central to finality
  - acceptance is also externally gated and cannot be claimed without explicit approval
- preserved read:
  - the prompt has a crisp finality rule, but the acceptance trigger remains outside the agent's unilateral control
