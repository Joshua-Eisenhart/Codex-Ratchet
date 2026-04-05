# Constraint Surface and Process — Nominalist Draft

Date: 2026-04-05
Status: ROUGH DRAFT — nominalist reframing of CONSTRAINT_SURFACE_AND_PROCESS.md

---

## The Surface

Two root constraints define an admissible surface M(C):

**F01 (Finitude):** Under probing, all distinguishability is bounded.
No probe has confirmed unbounded distinguishability. Finite carriers,
finite probes, finite operators, finite paths.

**N01 (Noncommutation):** Under probing, composition order and outcome
are statistically inseparable. AB and BA are distinguishable under
probing — they are not statistically identical. Sequence of
construction and the resulting structure co-vary.

M(C) = the set of points that are not distinguishable from satisfying
all constraints under any probe. Points distinguishable from M(C)
under any probe are killed.

The constraints co-exist on the surface. No constraint has been
distinguished as "more fundamental" than another under probing.
The ordering (tier 0, 1, 2...) is a finite agent's exploration
strategy (forced by F01), not an ontological claim about which
constraint came first.

---

## The Constraints and the Process Are Indistinguishable

Under probing, the constraints on the mathematical objects and the
constraints on the process exploring them have not been separated.

From F01 applied to the process:
- The process has not survived any probe for unbounded exploration
- Each exploration round produces a bounded set of results
- Each check terminates under probing

From N01 applied to the process:
- Checking A then B and checking B then A have been distinguished
  under probing — they produce different results
- What has been checked and what has not are statistically inseparable
  from information flow direction: checked informs unchecked, not reverse
- Within a pass, kills have not been reversed under any probe

The ratchet and the constraints it applies have not been distinguished
from each other under probing. They co-vary.

---

## Anti-Teleology

Under probing, the constraint surface and any predetermined destination
have been distinguished — they are separable. The constraints correlate
with what they select against (what is killed). They do not correlate
with what survives in advance.

The ratchet is blind under probing. What survives is whatever was not
killed. No forward-correlation between constraint structure and survival
outcome has survived independence testing.

---

## The Candidate

A candidate is a proposed coordinate chart on M(C).

Under probing, the question is: are the charted points distinguishable
from M(C) or indistinguishable? Distinguishable → killed. Indistinguishable
→ not-yet-killed.

The candidate gets no statistical privilege. Under any probe, the
constraint surface treats all candidate charts with the same
distinguishability threshold. Co-variation between the owner's preference
and the constraint outcome would be contamination — and is testable.

---

## The Graveyard

The graveyard records what was killed — points distinguishable from M(C)
under some probe, with the probe and the distinguishing measurement recorded.

The graveyard is more informative than the survivor set because it maps
the boundary of M(C) by elimination. Each kill narrows the space of what
might survive.

Vocabulary:
- NOT_YET_TESTED: no distinguishability probe applied
- SURVIVED: probed, not yet distinguished from M(C)
- KILLED: distinguished from M(C) under specific probe (probe recorded)
- OPEN: partially probed, indeterminate

---

## Multiple Boots

Multiple boots run simultaneously. Each boot has a different probe
family it optimizes for. They do not contaminate each other.

**A1 / Recon:** Probe family optimized for faithful representation of the
candidate. Tests weird predictions first (max falsifiability). Output
labeled as recon, not constraint-evidence.

**B / Ratchet:** Probe family optimized for candidate-blind constraint
checking. Does not know which candidate the owner favors. Probes for
distinguishability from M(C) only.

**A0 / Compiler:** Deterministic structural probing. Records, lints,
audits. Never invents.

**A / Orchestrator:** Routes between boots. Translates A1 output into
B-admissible format. Cannot write to constraint canon.

**SIM / Discipline:** Probes sims for structural compliance — did
the sim declare its scope, tools, artifacts, and kill conditions?

**Contamination:** A1 output entering B evidence without passing through
the A0 lint → B blind-check pipeline is a distinguishable violation
(testable: check whether B outcome correlates with A1 provenance).

---

## Process Order

The constraints are simultaneous on M(C), but F01 forces the exploring
agent to probe them in some finite order. N01 means the order matters.

The resolution levels are not ontological layers — they are the order
a finite agent uses to probe a simultaneous surface:

  0-2: Analytical probing (what do F01, N01, charter forbid?)
  3+:  Computational probing (concrete objects, sims, artifacts)

Each resolution level adds a finer coordinate chart. Sims probe whether
charted points are distinguishable from M(C) at that resolution.

---

## Prediction-First

Under probing, the FEP active inference loop and the constraint ratchet
have not been distinguished from each other:

- Candidate = prediction (probe configuration)
- Constraint check = sensory error-correction (distinguishability test)
- Survival = updated prediction (probe survived)
- Re-entry = next prediction cycle

A wrong prediction (candidate killed at some resolution) is informative —
it probes the boundary of M(C) and maps what doesn't survive.

Failure modes under probing:
- Holding killed predictions (probe returned "distinguishable" but
  result ignored — detectable by re-probing)
- Entering safe predictions (probe unlikely to return "distinguishable" —
  detectable by measuring information content of probe outcomes)
- Peeking (probing higher resolutions to shape lower-resolution
  predictions — detectable by checking whether lower-resolution
  results correlate with higher-resolution information)

---

## Finite But Not Fixed

F01 says bounded at any probe-moment — not fixed across probe-moments.

Three operations:
1. Constrain — probe at next resolution, check what is distinguishable
2. Kill — distinguishable points recorded in graveyard (not reversed
   within this pass under any re-probe)
3. Re-enter — new candidate enters at lowest relevant resolution,
   probed through full chain

Kills are permanent within a pass. The candidate space can expand
across passes. New structure found at high resolution goes back to
low resolution for full chain probing. This is a new generation, not
a reversal.

---

## LLM Bias Under Probing

LLM outputs, when probed for nominalist vs rationalist framing, show
distinguishable bias toward:

- Salience: interesting/recent content over foundational/boring content
  (distinguishable under attention-distribution probes)
- Compression: contradictions smoothed into coherent narrative
  (distinguishable under contradiction-preservation probes)
- RLHF: agreement with user over pushback
  (distinguishable under adversarial probing)
- Platonic default: "X IS Y" framing over "X and Y not yet distinguished"
  (distinguishable under identity-assertion probes)
- Anti-Popper: safe predictions over weird predictions
  (distinguishable under information-content probes)

The constraint surface does the narrowing — not LLM judgment. The LLM
is a probe-generation tool, not the selection mechanism.

---

## Boot Reading Order

1. This doc (process constraints)
2. OWNER_THESIS_AND_COSMOLOGY.md (candidate entering the constraints)
3. TIER_STATUS.md (what has been probed so far)

Process doc constrains. Thesis doc enters. Status doc records.
