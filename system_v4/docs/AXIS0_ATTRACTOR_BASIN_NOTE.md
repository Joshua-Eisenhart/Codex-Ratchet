# Axis 0 — Attractor Basin Characterization Note

**Date:** 2026-03-30
**Status:** FINDING — probe-backed. Updates and corrects the attractor claim from
  the co-arising stress test verdict (TRAJECTORY-SPECIFIC).
**Source:** sim_axis0_attractor_basin_boundary.py

---

## 1. What was open

The co-arising stress test found that sign(Δga0) = sign(ΔMI) is
TRAJECTORY-SPECIFIC, not operator-algebraic. The stress test showed Ti: 80.2%,
Fe: 51.1%, Te: 35.8%, Fi: 100% on random states. The question was: what property
of the attractor trajectory restores near-universal co-arising?

Two paradoxes required resolution:

1. **Te paradox**: Te has 35.8% agreement on random states. On the attractor,
   Te steps have norm_cyz = −1 (perfectly anti-parallel y-z Bloch vectors) —
   the exact condition that most strongly predicts Te anti-arising. Yet the
   trajectory shows co-arising for Te.

2. **lr_asym invariance paradox**: Earlier investigation found lr_asym = 1.0 for
   all coarse-graining levels on clean Hopf states. This suggested ΔMI_inst = 0
   everywhere, and the co-arising was entirely "cross-temporal." But lr_asym
   actually varies on the trajectory (mean 0.94, min 0.62).

---

## 2. Probe Findings

### 2.1 lr_asym on the trajectory (Q1)

lr_asym is NOT constant. Across all configurations:

| Engine / Torus | mean lr_asym | std | min | max |
|---|---|---|---|---|
| Type 1 / inner | 0.941 | 0.096 | 0.633 | 0.999 |
| Type 1 / outer | 0.944 | 0.096 | 0.621 | 1.000 |
| Type 2 / inner | 0.939 | 0.103 | 0.613 | 1.000 |
| Type 2 / outer | 0.941 | 0.104 | 0.596 | 1.000 |

Instantaneous MI changes are real (not zero). But lr_asym is systematically HIGH,
well above the Ti failure threshold.

### 2.2 The correct MI measure for T3 co-arising (Q2)

The FEP probe T3 computes: `ct_mi[t] = MI(rho_L[t], rho_R[t+1])`
This is the **forward** cross-temporal bridge — L at step t paired with R at step
t+1 (not the same step).

Per-step forward co-arising on the attractor:

| Operator | Forward co-arising | lr_asym mean |
|---|---|---|
| Ti | 7/7 (100%) | 0.807 |
| Fe | 7/8 (87.5%) | 0.982 |
| Te | 6–7/8 (75–87.5%) | 0.986–0.989 |
| Fi | 7/8 (87.5%) | 0.999 |
| **Total** | **27–28/31 (87–90%)** | |

The "12/12" result in the FEP T3 cross-correlation refers to the peak-at-lag=0
result across 6 configurations — a weaker and different claim from per-step
co-arising. 87–90% per-step is sufficient to produce the cross-correlation result.

### 2.3 Ti universality condition (Q3)

Ti fails (random states) when lr_asym_before is LOW — the two spinors start
near-aligned (L ≈ R), and Lüders dephasing can project them to DIFFERENT
computational-basis states, increasing their separation.

**Boundary:** lr_asym_before < 0.05 predicts Ti failure with 93.4% accuracy.

On the attractor: minimum lr_asym observed = 0.596 ≫ 0.05.
Therefore **Ti never fails on the attractor** — 100% per-step co-arising confirmed.

Failure examples (from stress test): ga0_base=0.35, ga0_before ∈ [0.1, 0.3],
random low-lr_asym states. None of these occur on the Hopf trajectory.

### 2.4 Te inversion mechanism (Q4)

On all attractor Te steps:
- norm_cyz = −1.000 (perfectly anti-parallel y-z Bloch vectors)
- Δlr_asym(isolated) = −0.002 to −0.075 (always negative)

Te DECREASES lr_asym when applied in isolation. Yet 75–87.5% of Te steps
co-arise in the forward MI measure.

**Resolution**: The forward bridge is MI(rho_L_after_Te, rho_R_at_{t+1}).
The rho_R at step t+1 is the Fi-processed right spinor. The Ti→Fe→Te→Fi
orbit is periodic and phased: Fi follows Te, and Fi's right spinor maintains
high lr_asym contrast with the Te-processed left spinor. The forward pairing
is not measuring the isolated Te effect — it is measuring the relationship
between the current operator's output and the NEXT operator's right spinor,
which is the Fi-selection state in the orbit.

The Te anti-arises in isolation but co-arises in sequence because the Fi step
that follows it "re-establishes" the forward cross-temporal alignment.

---

## 3. Attractor Basin Characterization

The co-arising is an attractor ORBIT property, not an operator algebraic property.
Three conditions jointly produce the 87–90% forward co-arising rate:

**Condition A — High baseline lr_asym (~0.94)**
The Hopf attractor drives L and R to maximally separated Bloch configurations.
This keeps instantaneous MI near the Bell-injection maximum and keeps Ti and Fi
in their success regimes (both require high lr_asym to co-arise reliably).

**Condition B — Ti never reaches failure threshold**
The attractor's minimum lr_asym (0.60) is far above the Ti failure boundary
(< 0.05). Ti is 100% reliable on the trajectory.

**Condition C — The Ti→Fe→Te→Fi sequence produces forward-pairing alignment**
The forward bridge MI(L[t], R[t+1]) is systematically aligned with the ga0 orbit
because the 4-step period creates a deterministic phase relationship between the
current left spinor's operator output and the NEXT step's right spinor.
Te can anti-arise instantaneously but still co-arise in the forward sequence because
Fi (the next step) brings R[t+1] into the configuration that makes MI(L_Te, R_Fi) track ga0.

---

## 4. Fi Lemma — Summary

See AXIS0_FI_LEMMA.md for the full proof. Key result:

> Fi (U_x(θ)) with the right-spinor conjugate rule produces the SAME U_x rotation
> for both L and R spinors (because σ_x commutes with U_x). Therefore lr_asym is
> exactly preserved: lr_asym after Fi = lr_asym before Fi. Proof: algebraic.
> Confirmed: 1995/1995 random trials (100.0%), zero failures.

---

## 5. Anti-Smoothing

- The 87–90% forward co-arising is NOT 100% — there are ~4 failures per 32-step cycle.
- The "12/12" result from the FEP T3 test is a cross-correlation peak claim, not
  per-step universality — these are consistent but not equivalent.
- Ti is 100% on the attractor but that is a contingent property of the high lr_asym
  baseline, not an algebraic necessity.
- The Te resolution (Fi "re-establishes" alignment) is a structural observation about
  the orbit, not a derived theorem — the exact mechanism requires the periodic orbit
  characterization that is OPEN.
- lr_asym varies on the trajectory — the "constant at 1.0" hypothesis was WRONG.
  The invariance seen earlier was for clean Hopf state SNAPSHOTS at exactly the
  attractor fixed point, not for the full 32-step orbit.

---

## 6. Open Items Updated

| Item | Status |
|---|---|
| ga0 = MI formal proof | OPEN — co-arising is 87-90% forward per-step; algebraic proof requires orbit characterization |
| Ti universality on attractor | CLOSED (contingent) — lr_asym > 0.05 always; boundary = 93.4% accurate |
| Te inversion mechanism | PARTIALLY CLOSED — Fi re-establishes; full orbit proof OPEN |
| Fi algebraic invariance | CLOSED — see AXIS0_FI_LEMMA.md |
| Forward vs backward pairing | CLOSED — forward (L[t]⊗R[t+1]) is the FEP T3 measure; backward gives lower co-arising |

---

## 7. 2026-03-31 Addendum — Current Understanding And Build Plan

This section preserves the current 2026-03-31 understanding after the bridge,
engine-state, guard, admissibility, and graph-law audits. It is intentionally
separate from the probe-specific findings above.

### 7.1 What Axis 0 is currently understood to require

Axis 0 is no longer treated as a probe-local scalar. The current working claim
is that Axis 0 should be the information entropy of the active joint state,
measured from the inside of the model:

- the model should carry a primary joint state `rho_AB`
- marginals `rho_L`, `rho_R` are derived by partial trace
- `ga0_level` should be read as `S(Tr_R(rho_AB))`
- transitions should be admitted by internal law, not by external patching

This means Axis 0 sits at the meeting point of:

- engine ontology
- bridge / cut construction
- graph admissibility
- operator semantics
- nonclassical guard enforcement

### 7.2 Stable discrete grammar that remains in force

The clear engine grammar has not been discarded:

- two engine types: `type1`, `type2`
- two loops per engine: `outer`, `inner`
- four terrain stages per loop
- `type1`: outer = deductive, inner = inductive
- `type2`: outer = inductive, inner = deductive
- deductive bundle = `Fe + Ti`
- inductive bundle = `Te + Fi`

The symbolic/Jung-facing language is secondary. The operator bundles and loop
grammar are the actual mathematical scaffold.

### 7.3 Ring-checkerboard hypothesis status

The ring-checkerboard model is treated as a geometry hypothesis, not canon by
declaration. The current status is:

- the hypothesis is partially formalized and testable
- the terrain perimeter law is consistent with the current `STEP_SEQUENCE`
- `64/64` `STEP_SEQUENCE` edges are admissible under the four-rule checkerboard law
- the missing `Fi -> Ti` transitions were identified as lawful `ring carry`
  operations, not geometry contradictions
- Weyl handedness aligns with ring traversal direction:
  - `type1`: b-loop clockwise, f-loop counter-clockwise
  - `type2`: exact mirror

The current conclusion is that the graph/cell complex is under-encoded, not
that the checkerboard geometry has failed.

### 7.4 Constraint-first stance

The system should be understood and rebuilt from the inside of the model:

- constraints are native law, not post-hoc validators
- legal action should be derived from admissibility, not authored externally
- the ring-checkerboard geometry should be seen from inside the state space,
  not imposed from outside as metaphor
- positive-path constructs must be justified by the model or remain provisional

This is the current epistemic rule:

- vision supplies hypotheses
- corpus tools formalize or falsify them
- runtime only adopts what survives that process

### 7.5 Corpus tools currently judged most relevant

The current appropriate tools for this phase are:

- `z3`: formal admissibility and anti-classical constraint testing
- `TopoNetX`: cell-complex and missing-face/topology checks
- `PyG`: live tensor graph runtime after legality is established
- `clifford`: orientation, chirality, and geometric algebra structure
- `codex-autoresearch`: bounded ratchet/controller work

Other corpus tools may matter later, but the current work should stay centered
on the set above.

### 7.6 Two parallel tracks that must converge

The current build plan is explicitly two-track, not single-track:

1. Engine track
   - stabilize the attractor basin
   - keep Axis 0 bounded and probe-backed
   - rebuild joint-state ontology
   - align bridge/cut law with nonclassical constraints
   - make operator semantics and graph dynamics load-bearing

2. System track
   - build the canonical system graph
   - formalize admissibility as graph law
   - use the skills/proof/graph corpus as active support
   - preserve candidate geometries, test outcomes, and surviving rules
   - later converge into graph/skill-native control

These tracks should share:

- the same constraints
- the same geometry vocabulary
- the same graph law
- the same nonclassical fail-closed philosophy

The goal is convergence, not a later rewrite.

### 7.7 Immediate next steps (preserved)

The current next-step order is:

1. treat checkerboard/ring position mapping as an explicit construction surface
2. encode admissibility, including ring-carry, directly in `z3`
3. rebuild the cell complex to include the 16 lawful carry faces
4. keep Axis 0 hot-path guard execution real and fail-closed
5. tighten operator semantics so deductive/inductive behavior is not only an
   effect of combined channels
6. continue making `PyG` and edge-state dynamics actually load-bearing

### 7.8 Anti-drift note

This addendum exists to prevent loss of the current understanding:

- Axis 0 is not "just a probe"
- the ring-checkerboard hypothesis is not random imagery anymore; it has a
  partially formalized, test-backed role
- the engine grammar remains intact
- the broader target is still a graph-and-skill-based system built from
  constraints first

If future work drifts, this section should be used as the preserved checkpoint
for what is currently believed, what is provisional, and what the plan is.
