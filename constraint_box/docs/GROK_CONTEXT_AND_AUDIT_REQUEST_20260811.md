# ConstraintBox continuation packet for Grok

Read this before continuing. It corrects thread drift and defines the evidence
ceiling for this discussion.

## 1. Project frame

ConstraintBox (CB) is a local, single-machine control-plane project for LLM
work. Portability is a design goal with no multi-OS evidence in this packet.
Its target job is narrow: decide whether a candidate artifact or transition
meets declared finite constraints and carries a recomputable receipt. The target
disposition set is admit, hold, park, refuse, or a bounded negative report. It
is not a truth oracle, ranking engine, policy engine, or physics engine.

LLMs may propose candidates and probes. Deterministic code must own the verdict.
The harness that constrains LLMs must not itself be controlled by an LLM.

CB Light and CB Heavy are literal separate domains:

- **CB Light** is the contained local Python control-plane work described
  below.
- **CB Heavy** is the reserved name for a separate simulation domain. This
  packet makes no claim about its current state or readiness. Nothing about
  Light establishes Heavy readiness, and Heavy paths/environments must not
  leak into Light claims.

Any sentence that does not name Light or Heavy is ambiguous and should be
rewritten.

## 2. Current local CB Light evidence

This is local, one-machine evidence only. It is not portability, release, or
adoption evidence.

- Owner-supplied current accounting: **91 roots**, **86 selected**, **5 held**,
  and **15 excluded before installation**. Falsifier: a fresh contained
  evaluator/ledger run whose `selection_counts` block does not reproduce this
  partition (compare against
  [`cb_light_hook_run_v1.json`](../receipts/cb_light_hook_run_v1.json)) makes
  this section stale; do not repeat the numbers with a stronger status.
- On 2026-08-11, the local contained evaluation receipt
  [`cb_light_hook_run_v1.json`](../receipts/cb_light_hook_run_v1.json) recorded
  `evaluation_allowed=true`, `selected_for_work=86`,
  `hold_missing_evidence=5`, and `preinstall_excluded=15`.
  It licenses local evaluation only; `completion_allowed` and
  `promotion_allowed` remain false.
- The locally exercised base formal tools are **Z3, cvc5, SymPy, Rustworkx,
  and Maude**, with bounded local core-contract exercises. This does not claim
  that every tool is fully integrated into every gate or that each is portable.
- **Pydantic 2.12.5** and **jsonschema 4.26.0** belong to a separate typed
  control-plane venv/profile on this same machine. Do not fold them into the
  CB Light formal-kernel claim or infer a separate machine from this boundary.
- Exact locked versions for the five base formal tools exist in the local
  row-level ledger, but this packet does not export them. Do not supply or
  assume a version unless the current ledger receipt is attached.
- ClaimGate is legacy material: an older patch attempt, not current CB
  architecture.
- MMMs are saliency/context bias: clouds of particulars that may influence
  model attention. They are not rules, verdict sources, or truth stores.

Nothing here establishes real provider swarms, a live self-improving loop,
CB Heavy simulation, multi-OS portability, adoption, promotion, release, or
any claim about physics.

## 3. Build order and non-negotiable constraints

The intended order is fixed:

1. Deterministic gates with real positive and negative controls.
2. A real consumer route: operation -> gate -> disposition -> SQLite receipt
   -> replay or an explicitly bounded non-replay report.
3. Only then bounded probes, waves, councils, and provider integration.

Each real gate needs all of the following:

- a declared finite input/domain and explicit invariant set;
- a positive witness and a reason-specific negative;
- boundary, order, and severance probes where relevant;
- exact interpreter, package, import, version, input, output, and reason-code
  evidence;
- a receipt that says what was actually checked, not what the system wishes it
  had checked;
- a consumer that cannot bypass the gate;
- no promotion above its evidence ceiling.

An absence of a counterexample is a bounded negative result, never a
"proof of resilience." A solver verdict applies only to the declared encoding;
it does not prove unencoded invariants or external truth.

## 4. Calibration of earlier conversation

Some ideas in the supplied discussions are useful and should remain live:

- wide, diverse generation at gates paired with strict deterministic
  acceptance;
- separation between the probe generator and the gate;
- mandatory negative probes and receipt-bound replay;
- waves that eventually cover induction, deduction, falsification, and
  project-level context repair;
- using MMMs to counter recency and context rot without turning them into a
  rule engine.

But these corrections are equally important:

- Do not treat sample code, a package list, an import, a solver `sat`, or a
  green-looking receipt as a working gate.
- Do not copy a Claude Code hook payload or decision contract into Codex.
  Codex has lifecycle hooks, but the actual installed version's event,
  payload, trust, timeout, and enforcement behavior must be tested directly.
  A hook is a guardrail, not complete enforcement by itself.
- Do not represent Rustworkx graph density as information-theoretic entropy,
  or a lossy ASCII display symbol as a replayable hash. These can be
  heuristics or visualizations only when their limits are explicit.
- Do not convert finite sampling of proposed futures into a claim that all
  possible futures were modeled.
- Sophisticated Inference is useful research context: it uses recursive
  expected-free-energy reasoning over future belief states. It does not prove
  retrocausality, collapse, gravity, or a CB implementation of that machinery.
  Those are design metaphors or separate research hypotheses, not CB Light
  capabilities.
- Never use "production-ready," "proven," "exactly specified," footprint
  numbers, repository inventories, version pins, or citations unless you can
  attach a current source or run receipt.

## 5. What I need help with now

Research and planning only. Do not propose a new framework, install packages,
write code, or promote a capability unless asked. At most one pattern may be
proposed for R1 and at most three claim blocks may answer each R item. Naming a
component, module, or subsystem not already named in this packet is a violation
unless it is labelled `PROPOSED-NEW-SURFACE` and ends with an explicit
owner-decision gate.

### R1 — receipt-bearing consumer route

Find the best primary/open-source patterns for content-addressed,
recomputable execution evidence (for example, provenance and reproducible-run
patterns). Map one minimal pattern onto:

`operation -> deterministic gate -> HOLD/REFUSE/ADMIT -> SQLite receipt -> independent replay`.

State which parts are directly reusable and which are merely analogy.
Also state the result that would show the proposed pattern is not worth adopting.

### R2 — hook capability matrix

Using official Codex hook documentation, specify a one-event smoke test for a
CB Light hook. You do not know the installed Codex version. Step zero is the
command that would establish it (for example, `codex --version`); every
version-specific payload, timeout, or enforcement detail remains `proposed`
until that local check runs. Give a procedure for latency measurement, including
clock points and a pass threshold; do not report a latency number.

- one known-good input that is allowed;
- one known-bad input that is blocked or held;
- a malformed-input/failure behavior that fails closed;
- proof that the real target caller cannot bypass it;
- a latency measurement for the actual event.

Do not assume a hook is working because a script runs manually.

### R3 — dual-solver disagreement

Research finite, practical treatment of Z3/cvc5 disagreement, timeout
asymmetry, `unknown`, and encoding drift. Recommend an explicit CB Light
disposition for each case. Solver disagreement is a defect signal to
investigate, not a source of complementary truth.

### R4 — MMM saliency experiment

Design the smallest one-machine A/B experiment that can distinguish
"MMM changes style" from "MMM improves an actual downstream task." Specify
neutral prompts, source packs, controls, sample count, metrics, null result,
and the pre-registered kill condition. A vocabulary shift alone is not enough.

### R5 — wave readiness (deferred)

The prerequisite gate route does not yet exist. Either answer
`DEFERRED: precondition unmet`, or answer the following schema questions with
every claim labelled `proposed`. Do not describe any wave as currently ready.
For each candidate wave, state:

- the input and bounded output schema;
- the deterministic consumer and gate;
- required negative probes;
- what would show the wave adds value over a single strong model pass at equal
  budget;
- what result would remove the wave from the design.

## 6. Required response format

For every substantive claim, use this exact structure:

```text
CLAIM:
STATUS: owner-supplied | cited | inferred | proposed
EVIDENCE: current receipt, direct primary source, or explicit reasoning
LIMITS / UNKNOWNS:
FALSIFIER:
NEXT FINITE TEST: tool, input, pass/fail condition
LIGHT / HEAVY BOUNDARY:
```

Rules:

- `owner-supplied` means a fact supplied in this packet. You have no local
  machine access; never relabel it `observed`.
- `cited` requires that you actually opened the primary anchor in this session,
  quoted it briefly, and supplied its locator (URL plus section, or paper plus
  page). If you did not open it, write `ANCHOR UNAVAILABLE` and use
  `proposed` instead.
- `inferred` requires all named premises to be `owner-supplied` or `cited`.
  A claim resting on any `proposed` premise is itself `proposed`.
- If evidence is absent, label the statement `proposed`.
- Do not merge CB Light and CB Heavy inside a claim.
- Preserve competing readings when evidence does not discriminate; do not
converge for tidiness.
- Start with a `CLAIM` block. Do not preface the response with praise or an
assessment of this packet.
- Describe unrun tests in imperative form. Never report an unrun result in
past tense.
- `FALSIFIER` must name a concrete observation. `More testing` fails.
- `NEXT FINITE TEST` must name a tool, concrete input, machine-checkable
pass/fail condition, and bounded anticipated duration. `Benchmark` or
`evaluation` alone fails.
- `LIGHT / HEAVY BOUNDARY` must state what the claim does and does not license
about Heavy in a sentence; a bare label fails.
- End with: assumptions not given; every source actually opened with locators;
and every R item deferred or unanswered with its reason. Any `cited` claim
without a locator in that list must be relabelled `proposed`.
- Treat disagreement as useful only when it produces a testable distinction.

## 7. Primary anchors for the research pass

- Codex hooks: <https://learn.chatgpt.com/docs/hooks>
- Friston et al., *Sophisticated Inference*: <https://arxiv.org/abs/2006.04120>

These sources establish only their own documented scopes. They do not certify
any local CB capability.

If an anchor cannot be opened or is not OpenAI-published / primary for the
claim at hand, say so and downgrade every dependent statement to `proposed`.
