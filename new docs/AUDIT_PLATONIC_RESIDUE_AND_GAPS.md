# Audit: Platonic Residue and Gaps in Clean Docs

Date: 2026-04-05 (updated with process doc audit and missing doc notes)
Purpose: Self-audit of ALL clean docs for LLM bias residue, causal language
         leaks, missing/flattened content, and suggested fixes.

NOTE: Do not delete content based on this audit. Add fixes alongside existing
text, or note the issue for the next rewrite pass. The audit identifies
problems — it does not authorize mass changes.

---

## Platonic Identity Residue ("X IS Y")

Every "IS" in the thesis doc is Platonic identity — asserting essential sameness.
Nominalist restatements below.

| Line | Platonic | Nominalist restatement |
|---|---|---|
| 15 | "QIT engines ARE the universal pattern" | Under every probe applied across scales, the engine's statistical correlation structure has not been distinguished from patterns found at other scales. No probe has killed the indistinguishability. |
| 64 | "Statistics IS Causality" | Statistical structure and what humans label "causality" have never been distinguished under any empirical probe. The separation does not survive probing. |
| 86 | "Subject and Object Are the Same Thing" | No probe has measured a boundary between observer and observed that survives independent of the observer's probe family. |
| 220 | "one primitive substance" | All distinguishable things, under maximally broad probing, resolve into correlations within a single indistinguishable substrate. |

---

## Causal Language Residue ("X creates Y", "X drives Y")

| Line | Causal | Nominalist |
|---|---|---|
| 129 | "Positive feedback creates conditions that trigger negative feedback" | Pos and neg feedback are statistically coupled. Neither "creates" the other. Their correlation is not yet killed. |
| 154 | "positive feedback cascades across scales" | At power-law scales, the neg/pos coupling signature is scale-free. The correlation extends, it doesn't cascade. |
| 177 | "Chirality → statistics → power laws → ratcheting → everything" | These five have not been distinguished under any independence-testing probe. They co-vary. Arrows are notational. |
| 301 | "Many possible futures create the present" | The admissible refinement set and the present are statistically inseparable. Probing one without reference to the other has not survived. |

---

## Missing Content / Flattened Nuance

### 1. a=a iff a~b is undercooked

Only 3 implications listed (lines 474-477). Should include:
- Kills primitive identity (no self without contrast under a probe)
- Kills primitive equality (no "same" without a probe family declaring it)
- Kills primitive causality (correlation iff distinguishability — can't have
  deterministic cause without statistical correlation)
- Creates subject=object collapse (probe and probed are regions of same substrate)
- Connects to FEP (prediction = probe configuration; error = distinguishability
  under that probe; update = probe reconfiguration)
- Oracle vs Turing distinction (oracle supplies probe set Π that fixes what
  equivalence classes mean; Turing operates within those classes)
- How it makes statistics fundamental (identity IS statistical
  indistinguishability; therefore statistics is prior to identity, not
  a tool applied to pre-existing identities)

### 2. Coupled feedback loop dynamics are shallow

The doc says neg/pos feed on each other but doesn't capture HOW with
specificity. Missing:
- The specific statistical structure of the coupling
- How the coupling becomes scale-free (transition to power laws)
- The relationship between coupling strength and Axis 0's signed kernel
- Whether the coupling IS what the engine's dual-loop grammar mechanizes

### 3. Power law → identity derivation is asserted not derived

The chain should be:
  indistinguishability is default (a=a only iff a~b)
  → distinguishability requires contrast
  → contrast is asymmetry
  → asymmetry at one scale is a broken symmetry (one event)
  → asymmetry preserved across scales is a power law
  → power laws are the statistical signature of identity itself
  → therefore: where power laws emerge, identity is being created

This derivation is missing from the doc.

### 4. Rosetta section is flat

Lists notation systems but doesn't explain WHY the mapping is natural.
The claim is: these are all probes by human subjects (made of M(C)) into
M(C) itself. The mapping is natural because probe and probed are the same
material recognizing itself through different probe families. This is
deeper than "translation layer" and should be stated.

### 5. Cosmology doesn't connect to feedback loops

White hole = positive entropy (max expansion) = extreme pos feedback
Black hole = negative entropy (max binding) = extreme neg feedback
Universe lifecycle = neg/pos feedback cycle at cosmological scale
This connection is unstated.

### 6. 4F/IGT section is thin

Says "all one structure, not analogy" but doesn't give the structure.
The 4F strategies as specific neg/pos feedback configurations under
specific probe families would make it falsifiable. Currently assertion
without mechanism.

### 7. Which symmetries specifically?

The max-falsifiable prediction (standard model = engine attractor basin)
doesn't specify which gauge group structure the engine produces. If not
yet known, state as the open question. If partially known, list what
the engine's symmetry structure currently looks like.

---

## Most Falsifiable Claims (ranked by killability)

Restated in max-nominalist, anti-Platonic framing:

1. MOST FALSIFIABLE: The engine's symmetry structure, when probed against the
   standard model's gauge groups (SU(3)×SU(2)×U(1)), will show statistical
   indistinguishability. If any gauge group has no correlate in the engine's
   constraint-surviving symmetries, the claim is killed.

2. HIGHLY FALSIFIABLE: Under any probe family applied to both the engine's
   64-step cycle and biological evolutionary dynamics, the correlation
   structure will not be distinguishable. If any scale-specific probe kills
   the indistinguishability, the universality claim narrows.

3. HIGHLY FALSIFIABLE: The engine's dual-chirality (Type1/Type2) when probed
   against spacetime's observed parity violation will show statistical
   correlation. If the engine's L/R structure has no correlate in observed
   parity violation, the chirality claim is killed.

4. FALSIFIABLE: The neg/pos feedback coupling in the engine, when probed at
   transition points, will produce power-law statistics. If the engine
   produces only bell-curve statistics at all scales, the ratchet claim
   is killed.

5. FALSIFIABLE: The FEP active inference loop, when derived from F01+N01
   without classical probability, will be statistically indistinguishable
   from Friston's FEP. If the derivation requires smuggling in Bayesian
   priors, the FEP-from-constraints claim is killed.

6. FALSIFIABLE: Probing the Rosetta mapping (QIT ↔ Jung ↔ IGT ↔ I-Ching)
   for statistical independence between the notation systems will fail.
   If any two notation systems can be probed as independent (uncorrelated),
   the "same structure" claim for that pair is killed.

7. HARDER TO FALSIFY: The identity axiom a=a iff a~b, when taken as
   foundational, will produce all extended axioms (no primitive time, no
   primitive causality, etc.) as derivable consequences. If any extended
   axiom requires an independent assumption beyond a=a iff a~b + F01 + N01,
   the self-sufficiency of the axiom set is weakened.

---

## What This Audit Found

The thesis doc has:
- Platonic "IS" language throughout (should be probe-relative indistinguishability)
- Causal arrows and "creates/drives/triggers" language (should be correlation)
- The identity axiom undercooked (3 implications listed, ~10 needed)
- Missing derivation chain from a=a iff a~b → power laws → identity
- Missing cosmology ↔ feedback loop connection
- Thin Rosetta and 4F sections (assertion without mechanism)
- Max-falsifiable prediction stated but gauge groups not specified

The thesis doc preserves the owner's voice and core claims accurately.
The framing has LLM bias residue that should be cleaned in the next pass.

---

## PROCESS DOC AUDIT (CONSTRAINT_SURFACE_AND_PROCESS.md)

### Platonic Residue

Line 11: "Two root constraints DEFINE an admissible surface M(C)"
- "define" implies the constraints are prior to and separate from the surface
- Nominalist fix: the constraints and the surface are not separate — the
  surface is the constraints. "M(C) is the constraints" not "defined by" them.

Line 19: "M(C) = {x : x SATISFIES F01 and N01...}"
- Set-builder notation with "satisfies" implies a test against an external
  standard. This is formal math notation and may be unavoidable, but the
  framing should note: the constraints are not external judges, they are
  the structure itself.

Line 51: "The ratchet IS F01 and N01 applied to themselves"
- "IS" — Platonic identity. Better: the ratchet and F01+N01 applied to
  themselves have not been distinguished. But this may be a case where
  the owner's intended meaning IS identity (same material), not Platonic
  identity (abstract essence). Flag for owner review.

Line 76-79: Candidate described as a sequence with arrows (→)
- Arrows imply construction sequence / causal chain. The doc says
  elsewhere (line 201) that tiers are resolution levels, not floors.
  But the candidate description still uses arrow notation. Suggested
  fix: note that the arrows are notational convenience for a finite
  agent's exploration order, not ontological sequence.

Lines 205-213: Tier list formatted as numbered list (0-8)
- Still visually looks like a ladder despite the disclaimer on line 215.
  Suggested fix: present as an unordered set with a NOTE that the
  numbering is exploration convenience, or use a different visual format
  (table, unordered bullets with resolution labels).

### Causal Language

Line 46: "The order of exploration matters (checking A then B ≠ checking B then A)"
- This is N01 correctly stated. Not causal — operational. OK.

Line 48: "Kills are irreversible within a pass — a point shown to be
off-surface stays off"
- "Stays off" implies temporal persistence. Better framing: within a
  single pass, a kill is not reversed. The kill is a measurement result,
  not a temporal event.

Line 229: "The constraints CORRECT the prediction by KILLING what doesn't fit"
- "correct" and "killing" are both active verbs implying agency in the
  constraints. Constraints don't act — they are the structure. What
  doesn't fit is distinguished from M(C), which is a measurement outcome,
  not an action.

### Structural Issues

Line 47: "Information flows in one direction" derived from N01
- This derivation is a STRETCH (noted in earlier audit). N01 says
  composition order matters, not that information flow is one-directional.
  The downward-blind rule is sound practice motivated by N01 + anti-salience,
  but claiming it's a strict N01 consequence is overclaiming.
  Suggested fix: present as "motivated by N01" not "derived from N01."

Lines 219-236: FEP Alignment section uses "IS" three times
- "The candidate IS the prediction" — identity assertion
- "The constraint chain IS the sensory error-correction" — identity assertion
- Better: these are mappings/correspondences that have not been
  distinguished under the relevant probes, not identities.
  But "under probing" was flagged as meaningless mantra — so use the
  actual formal concept: these are STRUCTURAL CORRESPONDENCES (a real
  term in comparative mathematics) not IDENTITIES.

Line 331-332: Source Chain lists "Owner corrections in session 2026-04-04/05"
TWICE — duplicate entry. Remove one.

---

## OWNER THESIS DOC — ADDITIONAL AUDIT NOTES

### Constraint on Distinguishability is buried

The derivation chain (constraint → matter/energy/geometry/dynamics/information
→ entropy as later measure → entropic monism as doctrine name) appears at
lines 218-244 but is buried as one section among 15+. This should be the
OPENING of the doc — it is the primitive from which everything else derives.
Currently the doc opens with "The Foundational Claim" (QIT engines are the
universal pattern) which is the CONCLUSION, not the foundation.

Suggested structural fix: open with constraint on distinguishability as
the primitive, THEN derive the downstream identifications, THEN present
the engine claim as what this primitive produces.

### "One Thing, Many Perspectives" section (lines 197-214)

This section lists correlations but doesn't explain WHY they're correlated.
The methodology (perspective rotation until multiplicity resolves to unity)
is stated but the derivation from constraint on distinguishability is missing.
WHY does constraint on distinguishability produce these correlations?
The answer (a=a iff a~b — identity requires contrast, which generates all
the dual-pair structures) is not stated in this section.

---

## MISSING DOCS (items 1-4 from validation)

### 1. Constraint on Distinguishability Formal Reference — NOT YET WRITTEN

Research agent running. This is the MOST CRITICAL missing doc.
Should cover: trace distance, operational equivalence, Blackwell order,
data processing inequality, Fisher information, identity of indiscernibles,
coarse-graining, resource theory of distinguishability.

Status: research agent launched, doc will be written when results return.

### 2. LLM Bias Formal Reference — NOT YET WRITTEN

Research agent running. Should cover with ACTUAL PAPER CITATIONS:
sycophancy (Perez 2022, Sharma 2023), hallucination (Ji 2023),
narrative smoothing, summary bias (Liu 2023 Lost in the Middle),
calibration (Kadavath 2022), RLHF reward hacking (Gao 2023),
context window effects, mitigations.

Status: research agent launched, doc will be written when results return.

### 3. Mapping Between Reference Traditions and System — NOT YET WRITTEN

9 reference docs exist. None map their concepts onto the system.
This is a SYNTHESIS doc, not a research doc — it requires holding
the system and the external traditions simultaneously and finding
the structural correspondences. High risk of smoothing/flattening.

Should probably be written AFTER items 1 and 2, and AFTER the owner
reviews the existing reference docs against their own model.

### 4. Boot Prompt Templates (The Actual Harness) — NOT YET WRITTEN

Discussed as meta-goal. No actual templates exist. Each boot type
(A0/A1/A2/B/SIM) needs a concrete prompt template that an agent
(Hermes or human) can use to launch a Claude terminal.

Depends on: items 1-3 (need the formal vocabulary before writing prompts)
and the philosophical harness work (nominalism + Chinese philosophy +
owner's specific twists).
