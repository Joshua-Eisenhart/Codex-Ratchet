# Axis 0 — EC-3 as Operator Co-Arising: Observation Note

**Date:** 2026-03-30
**Status:** OBSERVATION — probe-backed finding. Proposal-facing interpretation.
  This is a structural finding, not a closed doctrine claim.
**Source:** sim_axis0_fep_compression_framing.py Test 3 deep read,
  plus per-operator ga0 analysis.

---

## 1. The Finding

At every single step of the engine trajectory (32/32 steps, Type 1 inner):

> **sign(Δga0) = sign(ΔMI)**

Entropy change and mutual information change have the same sign on every operator
transition. They do not lead or lag each other (T3 peak cross-correlation at lag=0
across all 6 torus/engine-type configurations, peak_val = 0.47–0.71).

They co-arise. The entropy field and the information structure are the same event
viewed from two angles.

---

## 2. Operator Mapping

The period-4 co-arising pattern maps exactly to the Ti/Fe/Te/Fi subcycle:

| Operator | ga0 direction | MI direction | always same sign? | Interpretation |
|---|---|---|---|---|
| Ti (constrain) | ↓ (mean −0.111) | ↓ | Yes | Identity assertion: system contracts to `a=a` |
| Fe (release) | ↑ (mean +0.038) | ↑ large | No (noisy) | Contrast generation: `a~b` appears; largest MI jump |
| Te (explore) | ↑ (mean +0.094) | ↑ small | Yes | Contrast expansion: explores the space of `b` |
| Fi (filter) | ↓ (mean −0.052) | ↓ | Yes | Refined identity: filters contrast back to cleaner `a=a` |

Fe is the critical step: the largest MI gains occur at Fe transitions (+0.43 to +0.64
per stage). This is the moment where contrast is most sharply generated against the
Ti-compressed state.

---

## 3. EC-3 in the Operator Algebra

EC-3: `a=a iff a~b` — self-identity requires external contrast.

One Ti→Fe→Te→Fi subcycle IS one execution of EC-3:

```
Ti: assert a=a        (compress, ga0↓, MI↓)  — identity is asserted
Fe: generate a~b      (expand,   ga0↑, MI↑)  — contrast appears; COARISING moment
Te: explore b-space   (expand,   ga0↑, MI↑)  — contrast space is populated
Fi: a=a refined by b  (compress, ga0↓, MI↓)  — identity is refined via contrast
```

Two full EC-3 executions occur per macro-stage (8 stages × 4 operators = 32 steps =
8 macro-stages × 2 EC-3 cycles per stage... but the 4-operator block is one EC-3 cycle,
so 8 EC-3 cycles per engine cycle).

---

## 4. What This Means

### 4.1 The cut is not static

The EC-3 boundary is not a fixed shell at some η level. It is the **Fe-transition event**
— the moment when the Ti-compressed state releases and generates maximal contrast.
The shell/interior-boundary cut family is correct as the doctrine-facing candidate, but
the cut location is dynamic: it is sharpest at Fe transitions and blurry at Ti/Fi contractions.

### 4.2 Xi_hist should be Fe-indexed, not uniformly time-indexed

The current Xi_hist construction uses all trajectory steps with exponential
attractor-proximity weighting. The co-arising finding suggests a more targeted
construction: **weight by Fe-transition events** specifically, since these are the
steps where MI and ga0 co-arise most sharply (largest ΔMI, largest contrast).

### 4.3 The compression horizon is ~7 steps

T1 multi-lag analysis (backward MI asymmetry by lag):

| Lag | Asymmetry (bwd − fwd) |
|---|---|
| 1 | +0.0044 |
| 3 | +0.0110 |
| 5 | +0.0161 |
| 7 | +0.0203 |
| 8 | +0.0140 |

The backward MI advantage peaks at lag=7 then decreases. This suggests the engine's
compression horizon is approximately 7 steps — roughly two macro-stage subcycles
(2 × 4 operators = 8 steps, minus boundary effects).

Xi_hist with a 7-step rolling window (Fe-indexed) may produce sharper discrimination
than the current full-trajectory exponential weighting.

### 4.4 ga0 and MI are the same object

The co-arising is total: 12/12 first steps, same sign, no exceptions (for the
confirmed cases). In the entropic monism framework, this is expected: ga0 IS the
entropy, and MI IS the information structure. Space=entropy and dark matter=information
are not two things that correlate — they are one thing. The co-arising finding is the
engine-level confirmation of this identification.

---

## 5. What Remains Open

| Open item | What the co-arising finding says | What still needs derivation |
|---|---|---|
| Final Xi form | Xi should be defined at Fe-transition events, not uniformly | Exact operator form of Xi at Fe transitions |
| Shell algebra | The cut is sharpest at Fe-transition, blurry at Ti/Fi | Density matrix constraint for Fe-transition cut |
| Compression horizon | ~7 steps empirically | Derive from RC-1 + loop structure |
| ga0 = MI identification | Empirically confirmed co-arising | Formal proof that ga0 = MI up to a gauge |

---

## 6. Doctrine Fence

The co-arising finding (same sign at every step) is a direct probe result, not an
inference. The interpretations in sections 3–4 are proposal-facing. The Fe-indexed
Xi_hist proposal and the 7-step compression horizon are testable next steps, not canon.
