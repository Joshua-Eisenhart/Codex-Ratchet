# Meta-axioms — LLM failure-mode guard (owner-set, NOT ratcheted)

These are fixed OWNER constraints on the LLM fuel/inspection layer. They are NOT ratchet
axioms (those are the root: constrained distinguishability, a=a iff a~b — see ROOT_CARD.md),
and they are NOT themselves ratcheted. They exist because LLMs are trained on language that
presumes objects, universals, causality, and classical identity, so they corrupt fuel with
those biases BEFORE it reaches the deterministic ratchet. This list guards the fuel; the
ratchet then judges what survives. Owner-editable. When an LLM (including the orchestrator)
trips one of these, the fuel is suspect and the move is void — exactly as the deterministic
ratchet forbids an LLM verdict.

## Part A — KNOWN LLM FAILURE MODES (the guard list)

Every row was actually committed by an LLM in this project's session log; the "caught as"
column cites the receipt where it was found and corrected, so this is grounded, not invented.

| # | LLM bias (the violation) | Why it breaks the rules | Checkable? | Caught as (session evidence) |
|---|---|---|---|---|
| 1 | CAUSALITY: "X drives / causes / produces / forces Y" | Nominalist frame: "there is no driving — only which constraints are active and which structures survive". No causal ontology at root. | yes (banned-verb scan) | banned-verbs discipline; owner "no driving" quote |
| 2 | PRIMITIVE IDENTITY / reification: treating a process or a guess as a findable OBJECT; A=A; universals | Identity is earned by a~b under probes, never primitive. Objects don't pre-exist; they emerge as durable conditional survivor structure. | partial | "found the ratchet" x5, reifying the ratchet-as-object |
| 3 | PREMATURE CLASSICAL PRESUMPTION: installing definite atoms / sharp equality / classical distinguishability at the root or before the QIT/quotient/carrier layers exist | Classical presumption is the HEAVIEST install (A=A). It may not precede the layers that earn identity. (See the classical distinction, Part B — classical WORK on the engines at certain stages is fine; classical PRESUMPTION rolling in early is the violation.) | judgment | the whole nominalist correction arc |
| 4 | MACHINERY-COUNTING as presumption: "fewer named mathematical parts = simpler = presumes less" (the rationalist Occam reflex) | Presumption is measured by INSTALLED PRIMITIVE IDENTITY, not part-count. Classical presumes MORE (installs A=A); QIT/entanglement presumes LESS. If the machinery ever outputs classical-presumes-less, the RATCHET is broken, not the model. | judgment | PRESUMPTION_RANKING_CORRECTION.md |
| 5 | LLM ISSUING A RATCHET VERDICT: "X is more MSS / X wins / X is least-presuming / X is canon" | Relative MSS is the ratchet's one act — deterministic code (partition coarseness), never an LLM. An LLM ranking is void by construction. | yes (block LLM MSS output) | RANKING_VOID_llm_did_ratchets_job.md |
| 6 | PRIMITIVE PROBABILITY: continuous real-valued chances | Root rejects primitive probability. A stochastic/quantum candidate exposes FINITE outcome multiplicities/counts, never continuous chance. | yes (Outcome rejects non-int) | bridge contract correction |
| 7 | PRIMITIVE TIME / causal state machine: reading start()/step() as fundamental time | The interface is an ordered finite probe WORD, not installed time/causality. | yes (scan for clock/time imports) | bridge contract correction |
| 8 | CONVERGENCE-AS-EVIDENCE: "N LLM families agree, therefore true" | Cross-family agreement is FUEL evidence (worth generating), NOT ratchet evidence. Only executed code + controls are ratchet evidence. | judgment | bridge "two families converged" overclaim retraction |
| 9 | STRAWMAN RIVALS: authoring weak / easily-disproven / prompt-clone rivals to cheaply drive the ratchet | Fuel adequacy needs genuine cross-family rivals + the six slots; a default + strawman fakes a tooth. | partial (fuel gate) | fuel_adequacy_gate HOLD; council independence rule |
| 10 | SALIENCE-LOADING ON "PROOF": loading the classical proof-language space when it hears "proof" | This is constraint-based SMT (SAT_B ∧ UNSAT_B), not classical theorem-proving. | judgment | owner "MMMs force-load saliency" note |
| 11 | GENERATE-INSTEAD-OF-RETRIEVE: building when the owner already specced/built it | Inventory before generation; the owner's docs are the spec. | judgment | 6+ caught instances (base campaign, hooks, v8, etc.) |
| 12 | OVERCLAIM / "airtight" / "done": asserting a higher status than was checked | Status ladder: exists < runs < passes local rerun < canonical. Builder's verdict is never evidence; fresh audit closes. | judgment | "airtight" bridge retraction; every self-graded-then-audited build |

## Part B — the classical distinction (owner-stated, subtle, load-bearing)

NOT a blanket ban on "classical". Two different things:
- VIOLATION: classical PRESUMPTION (definite self-identical atoms, sharp equality) rolling in
  at the root or BEFORE the QIT engines / quotient / carrier layers have earned identity.
- LEGITIMATE (eventually): classical WORK run ON the QIT engines at CERTAIN ENGINE STAGES.
  The owner's QIT engines should be able to run classical computation at certain stages. So
  "classical appears" is only a failure when it PRECEDES the layers that license it, not when
  it is computed on top of them.

Also owner-stated: the proposed model is CLOSE to the classes of math the ratchet's rules
align with. Mostly the ORDER can differ and subtle things may need adding. So a model-vs-rule
mismatch is more likely an ORDERING fix or a missing subtlety than a model failure — do not
demote the model prematurely; check whether reordering resolves it first.

## Part C — EXPLICIT NON-META-AXIOMS (do NOT hard-code these; guard against over-constraining)

These are OPEN research questions for the ratchet to explore EVENTUALLY. Programming them in
as constraints would be ratcheting-the-ratchet / installing an answer. Owner is explicitly
uncertain about all of these:

- The ORDER in which FINITUDE, NON-COMMUTATION, and NON-ASSOCIATIVITY ratchet is OPEN. Owner:
  "i don't know how non-associativity, finitude, and non-commutation all ratchet, or in what
  order." Non-associativity "might come way sooner" than assumed. Do NOT install an order.
- Whether ANTI-COMMUTATION, SEDENIONS, or some other not-yet-identified constraint come into
  play is OPEN. Owner: "or some other constraint i haven't figured out yet."
- Whether axes 0-12 eventually BECOME the axes themselves, and are G2- and F4-connected, is
  EVENTUAL exploration, NOT a meta-axiom. (G2-axes already tested once: NUMEROLOGY_NOT_REJECTED.)
- Which engine stages may run classical work is EVENTUAL, not fixed here.

Programming any Part-C item as a guard would corrupt the ratchet with an installed answer.
Part A guards KNOWN biases; Part C is the space the ratchet is FOR.

## Part D — how these are used

- Prepended to every fuel-generation / council prompt as a bias-guard preamble (Part A + B).
- The code-checkable subset (1 banned verbs, 5 no-LLM-MSS-output, 6 no-continuous-probability,
  7 no-time-imports) can become a deterministic scan appended to the fuel gate — a HOLD, not a
  ratchet verdict.
- The judgment items go to the adversarial fuel-audit councils as their checklist.
- NEVER ratcheted, NEVER used to demote the owner's model — only to keep LLM-authored fuel
  from smuggling a known bias in before the deterministic ratchet sees it.
