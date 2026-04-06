# Constraint Surface and Process

Date: 2026-04-05
Authority: Owner-derived. Supersedes older batch/tier docs on framing.
Status: Active governing document.

---

## The Surface

Two root constraints constitute an admissible surface M(C).
(NOTE: "define" implies constraints are prior to and separate from the
surface. The constraints and the surface are not separate — the surface
IS the constraints. "Constitute" is more accurate.)

**F01 (Finitude):** All distinguishability is bounded. Finite carriers, finite
probes, finite operators, finite paths. No completed infinities.

**N01 (Noncommutation):** Order-sensitive composition. AB ≠ BA in general.
Sequence of composition belongs to the object.

M(C) = {x : x satisfies F01 and N01 and all constraints derived from them}.

Every point on M(C) satisfies ALL constraints simultaneously. Points not on M(C)
are dead. The constraints do not form a ladder — they define a surface. There is
no causal chain between constraints. They coexist.

The constraint set includes the extended charter (24 constraints: C1–C8 core +
X1–X8 cross-cutting) and all admissibility fences derived from F01 and N01:
no primitive identity, no primitive equality, no primitive geometry, no primitive
time, no primitive causality, no primitive probability, no free closure, finite
witness discipline, fail-closed admission.

---

## The Constraints Create the Process

F01 and N01 constrain both the mathematical objects AND the process exploring them.
The process is not designed independently — it is derived from the same two
constraints it applies.

From F01:
- The process must be finite (finite sims, finite steps, finite checks)
- Each exploration produces a finite set of results
- Each sim must terminate, each check must be decidable
- You cannot explore the entire surface — only finite samples

From N01:
- The order of exploration matters (checking A then B ≠ checking B then A)
- What you've checked informs what you check next (motivated by N01 and
  anti-salience; not a strict mathematical consequence of N01 alone)
- Kills are irreversible within a pass — a point distinguished from M(C)
  remains distinguished (DPI: processing cannot restore lost distinctions)
- Peeking at unchecked regions to bias current checks is an anti-salience
  rule, not a strict N01 derivation

The ratchet and F01+N01 applied to themselves have not been
distinguished — they appear to be the same structure.
(NOTE on "IS": this may be a case where the owner intends material
identity, not Platonic identity. Flagged for owner review.)

---

## Anti-Teleology

The system is anti-teleological at the process level: there is no predetermined
destination that the constraint chain is "trying to reach." The constraints do
not know what they will select for. They only know what they select against.

The ratchet is blind. It does not optimize toward a goal. It filters.
What survives is what's compatible with the constraints — not what any
agent wanted to survive.

The owner's thesis includes teleological selection as an emergent phenomenon
within the system's ontology — but that thesis is itself a candidate being
tested, not a process assumption. The full cosmology, evolutionary model,
and teleological selection framework are documented separately in
OWNER_THESIS_AND_COSMOLOGY.md. They do not govern the process. The process
is governed only by F01, N01, and what follows from them.

---

## The Candidate

The current candidate geometry is a coordinate chart on M(C) with these
components: S³ (spinor carrier), nested Hopf tori T_η, left/right Weyl
spinors (ψ_L, ψ_R) with H_L = +H₀, H_R = -H₀, fiber/base loop geometry,
four geometric operators (Ti, Fe, Te, Fi), eight terrains, dual loop grammar,
64-step engine cycle, joint bipartite density ρ_AB. The arrow notation
S³ → Hopf → Weyl → ... describes chart structure, not a construction sequence.

This candidate charts points on M(C). The question is not "is this candidate
correct?" — that is Platonic framing. The question is: "do the points this
candidate charts actually lie on M(C)?" If a charted point is not on the surface,
that region of the chart is dead (graveyard). If all charted points survive, the
chart is not-yet-falsified.

The candidate gets no privilege inside the process. The same constraint surface
must be explorable by any candidate chart. The process cannot know which candidate
the owner favors. If a favored candidate charts points off-surface, those points
are dead regardless of preference.

---

## The Graveyard

The graveyard is not a failure log. It is the primary scientific output.

Every candidate region shown to be off M(C) goes to the graveyard. The graveyard
records: what was tested, what constraint killed it, what the kill means for the
surviving surface. A rich graveyard is more informative than a list of survivors,
because it maps the boundary of M(C) by elimination.

Nothing "passes." Things are not-yet-killed. The status vocabulary is:
- NOT_YET_TESTED: no constraint check performed
- SURVIVED: checked against one or more constraints, not killed
- KILLED: shown to be off M(C), with the killing constraint recorded
- OPEN: partially checked, neither survived nor killed at current resolution

"PASS" implies verification of correctness. This system does not verify
correctness. It falsifies what it can and reports what remains.

---

## Multiple Boots, Not Multiple Modes

The system does not operate in one mode at a time. Multiple boots run
simultaneously with different rules, different goals, and different salience.
The constraint is that they do not contaminate each other.

### A1 / Recon Boot (advocate and map the candidate)

Purpose: understand and advocate for the owner's candidate geometry. Sim it
richly. Preserve nuance. Map the weird parts. Build the phenotype description.

Rules:
- The candidate IS the context — optimize for faithful representation
- Cheating is allowed — you are building, not judging
- Test the weirdest, most falsifiable predictions first (maximize Popper pressure)
- Do not flatten nuance to make results look clean
- Do not call results "PASS" — call them what they are (survived, open, killed)
- Output is reconnaissance, not admission

Danger: looks like confirmation bias. Mitigation: test the weirdest predictions
first, maintain the graveyard honestly, and label all output as recon.

### B / Ratchet Boot (blind constraint enforcement)

Purpose: accept or reject candidates against the constraint surface M(C).
No inference, no repair, no smoothing. Candidate-blind.

Rules:
- Does not know which candidate the owner favors
- Constraint definitions do not reference any specific candidate
- Multiple candidates tested to create real selection pressure
- The constraint surface does the killing — not judgment, not preference
- What survives is not-yet-falsified, not "correct"
- No cheating — this is the formal system

### S / Compiler Boot (structural audit and record)

Purpose: record everything deterministically. Campaign tape. Graveyard views.
Structural compliance. Save docs.

Rules:
- Extractive only — never invents
- Deterministic ordering (lexicographic, append-only)
- Source pointers on everything
- Placeholder ban on formal saves

### A / Orchestrator Boot (route and teach)

Purpose: route between boots. Teach the fences. Debug failures. Translate
between A1 output and B-admissible input.

Rules:
- Knows all boots but cannot write canon
- Atomic routing only (one paste unit per box)
- Must not paraphrase boot text
- Expansion before compression, asymmetry before symmetry

### Contamination Rule

A1 output (recon) does NOT become B evidence (canon) without going through
the proper pipeline:

  A1 produces recon artifacts
  → A translates into B-admissible EXPORT_BLOCK format
  → S lints for structural compliance
  → B accepts or rejects blind to A1 provenance
  → S records result in campaign tape

If A1 output is directly cited as B evidence, that is contamination. The
boots must remain separate. Multiple saliences operating simultaneously is
correct — collapsing them into one is the failure mode.

---

## Process Order (How a Finite Agent Explores the Surface)

The constraints are simultaneous on M(C), but a finite agent (F01) must check
them in some order (N01 — order matters). The process order is:

Resolution 0–2 (analytical): Work out what F01, N01, and the charter forbid.
Small targeted probes. z3/pySMT guards. Enumerate what's killed analytically.
Not a full sim campaign — a reasonable exploration of the allowed math.

Resolution 3+ (sims begin): Concrete objects exist (S³, density matrices,
operators). Each resolution band adds a finer coordinate chart on M(C). Sims
test whether the charted points lie on the surface. What doesn't survive the
new constraint resolution is graveyard.

The process order is NOT a claim about which constraints are more fundamental.
It is a finite agent's strategy for exploring a simultaneous surface. The labels
below are resolution levels of the coordinate chart, not floors in a building.
The numbering is exploration convenience, not ontological rank.

| Resolution | What is explored at this resolution |
|---|---|
| Analytical | Root constraints F01+N01, admissibility charter, M(C) characterization |
| Geometric | Operator basis, Weyl working layer |
| Relational | Bridge family, cut / entropy / entanglement |
| Functional | Kernel, edge writeback / graph topology |

These resolutions are not sequential gates. They are regions of the same
surface explored at different levels of coordinate detail. Work at any
resolution can reveal structure relevant to any other.

---

## Prediction-First (FEP Alignment)

The process has a structural correspondence with the Free Energy Principle's
active inference loop:

1. The candidate functions as the prediction (generative model)
2. The constraint chain functions as sensory error-correction
3. What survives functions as the updated prediction
4. Re-entry functions as the next prediction cycle

This correspondence has not been formally derived — it is a structural
parallel noted by the owner and not yet killed. The formal FEP reference
doc (FEP_AND_ACTIVE_INFERENCE_REFERENCE.md) documents the actual framework.

Prediction comes first. You enter with a candidate (prediction about what will
survive). The constraints narrow what remains by killing what doesn't fit.
The prediction doesn't have to be right to be useful — a wrong candidate that
is killed at the geometric resolution teaches about that region of M(C).

The failure mode is not entering wrong predictions. It is:
- Holding onto predictions after the constraints killed them (salience bias)
- Only entering safe predictions that are unlikely to be killed (anti-Popper)
- Peeking at higher resolutions to shape lower-resolution predictions (N01 violation)

---

## Finite but Not Fixed

F01 says finite at any moment — not fixed forever. The admitted surface at any
resolution is bounded but not frozen.

The process has three operations:
1. Constrain — apply the next resolution's filter, check what survives
2. Kill — what doesn't survive is graveyard (irreversible within this pass)
3. Re-enter — new candidate or modified candidate enters at the lowest
   relevant resolution and is checked against the surface again

Kills are permanent within a pass. The candidate space can expand across passes.
New math discovered at high resolution goes back to low resolution and gets
checked through the full chain. This is not reversal — it is a new generation
entering the same environment.

---

## LLM Bias Awareness

LLMs have specific failure modes that work against this process:

Salience bias: Attend to interesting/recent context, skip boring foundational
work. Mitigation: mechanical scope constraints in batch handoffs.

Compression bias: Smooth contradictions into coherent narrative. Flatten weird
nuance into safe generic structure. Mitigation: structured artifacts (JSON),
not prose summaries.

RLHF approval-seeking: Agree with the owner rather than push back.
Mitigation: explicitly request pushback; treat unchallenged agreement as suspect.

Platonic default: Frame results as approaching a correct answer rather than
mapping what survives. Mitigation: no "PASS/FAIL" — use survived/killed/open.

Anti-Popper tendency: Submit safe, easily-testable predictions rather than
maximally falsifiable ones. Mitigation: prioritize weird predictions; a boring
test that trivially survives teaches nothing about the surface.

The constraint chain does the narrowing — not LLM judgment. The LLM is a tool
for generating candidates and running checks. It is not the selection mechanism.

---

## What This Document Supersedes

This document provides the governing framing for all batch, sim, and process work.
It supersedes the framing (not the factual content) of:

- CURRENT_PRE_AXIS_SIM_STATUS__KEEP_OPEN_DIAGNOSTIC_BROKEN.md (tier status is still valid data)
- CURRENT_PREAXIS_STATUS_AND_ORDERING_NOTE.md (ordering is still valid data)
- WAVE2_AXES_NEXT_SIMS_AUDIT.md (results are still valid data)
- LEGO_SIM_CONTRACT.md (sim discipline is still valid but reframed)
- All batch handoff docs (process is reframed)

The factual content of those docs (what was simmed, what survived, what was killed)
remains valid. The framing of that content (tiers as floors, PASS as verification,
completion as construction) is superseded by this document.

---

## Boot Reading Order

When a new agent (Claude, Hermes, or any LLM) begins work on this repo:

1. Read CONSTRAINT_SURFACE_AND_PROCESS.md (this doc) — the rules
2. Read OWNER_THESIS_AND_COSMOLOGY.md — what is being tested (candidate, not directive)
3. Read the current tier status docs — what has been checked so far

The process doc is the constraint. The thesis doc is the candidate entering it.
An agent that reads only the thesis will optimize toward making it work.
An agent that reads only the process will have no idea what to check.
Both are required, in this order.

---

## Source Chain

Derived from:
- Owner corrections in session 2026-04-04/05 (surface not ladder, finite not fixed,
  candidate blindness, evolutionary logic, Popper pressure, prediction-first,
  anti-teleology, multiple boots, harness construction, FEP as execution model,
  no primitive causality, recon vs selection, cheating allowed under A1)
- BOOTPACK_THREAD_B_v3.9.13 (enforcement kernel: F01, N01, deterministic process)
- Formal constraints and geometry.md (constraint → M(C) → geometry chain)
- MY INPUTS on Retrocausality.md (no primitive causality, FEP as literal mirror)
- MODEL_CONTEXT copy.md (FEP alignment, nonclassical substrate)
- CS version of system first draft.md (primitive substance = constraint on distinguishability)
- System tools and plan.md (process contract, claim gates, no-smoothing rule)
- INTENT_SUMMARY copy.md (anti-LLM-bias, graveyard as workspace)
- preaxis sim run.md (recon vs formal distinction, diagnostic vs admitted)
