# Panel 9 — Blind Alt-View Pass on the In-Flight Wave Targets (2026-06-12)

```yaml
receipt_kind: blind_panel
panel_number: 9
routes: [grok-4.3 API (temperature 0), gemini TUI (auto-gemini-3)]
protocol: same questions both routes, NO repo values shared, math-only answers
pre_registration_status: written WHILE the target packets were in flight and unread —
  fiber_augmented_cover_v0 (building), iching_symmetry_match_v0 (building),
  axis0_cosurvivor_heavy_v0 (building)
question_file: /tmp/panel9_questions.txt (Q1 iching groups, Q2 fiber cover, Q3 b6 product law, Q4 CP.11-vs-CP.14)
raw_outputs: /tmp/panel9_grok.json, /tmp/panel9_gemini.txt
claim_ceiling: advisory alt-views only; no admission, no promotion; the packets adjudicate
promotion_allowed: false
```

## Q1 — I Ching transformation groups (target: iching_symmetry_match_v0)

CONVERGENT (both routes, independent):
- Single-line flips generate (Z_2)^6, order 64.
- Reversal + complement commute and generate the Klein four-group V_4, order 4.
- A homomorphism into the 6-cube symmetry group (Z_2)^6 ⋊ S_6 must preserve the
  Hamming/adjacency structure: a line flip must map to a single-coordinate change.
- Random-relabeling control: agreement collapses (grok: stabilizer probability ~1/64!;
  gemini: single-step Hamming distance thermalizes to the mean 3.0).

DIVERGENT falsifying invariant (both computable; the packet can run both):
- grok: multiset of orbit sizes on the 32 antipodal pairs / cycle index on weight-3 vectors.
- gemini: the weight-transition spectrum (a flip must change Hamming weight by exactly ±1).

## Q2 — fiber-augmented cover conditions (target: fiber_augmented_cover_v0)

CONVERGENT:
- Fibers must be equicardinal away from singular cells; chart transitions must act by
  cyclic shifts of the discrete fiber, constant along each fiber; poles need explicit
  singularity handling (pinning or accumulated-phase bookkeeping).
- THE WITNESS both routes name: a computed winding/Euler-class certificate — sum the fiber
  phase transitions around a closed base loop (equator): nontrivial S^3-like bundle = ±1,
  trivial S^2×S^1 product = 0. (grok phrases it as odd-vs-even pole linking / finite Euler
  class ±1; gemini as the discrete winding number mod |F|.)

DIVERGENT (LIVE — do not collapse): minimal fiber size carrying Chern number 1 faithfully —
grok says |F|=2 (binary phases, odd linking detectable), gemini says |F|=3 (smallest cyclic
group supporting a DIRECTED nontrivial winding). The packet's pinned fiber size adjudicates:
if the cover uses |F|=2, the orientation/direction information gemini flags must be shown
recoverable or the witness weakens to parity-only.

## Q3 — b6 = -b0*b3 chance rates and confounds (target: the cover's law table)

CONVERGENT:
- Independent random signs satisfy the product law at exactly 50% per cell.
- Confound: any readout algebraically defined from the other two = trivial satisfaction.
- gemini's significance row: on N=33 cells, one-tailed binomial 95% needs ≥23 agreeing
  cells; a perfect-law subsample of n=5 already reaches p<0.05.
- grok's structural check: the three readouts must stay linearly independent over F_2 on
  every coordinate-subset restriction of size ≥3. gemini adds: variance>0 per readout
  (constant-readout confound) and low I(b0;b3) (linear-aliasing confound).

## Q4 — CP.11 vs CP.14 alias/disagreement conditions (target: axis0_cosurvivor_heavy_v0)

CONVERGENT SHAPE: the two readouts alias under degree-1/linear-gradient-flow structure;
they are FORCED apart by multi-neighbor mixed-sign structure.
- grok's minimal forcing example: the star K_{1,3} with three leaves carrying distinct
  positive increments (majority sign ≠ any single directed edge).
- gemini's minimal forcing example: a generator that scrambles internal degrees of freedom
  (dS/dt ≠ 0) while moving nothing across the committed adjacency (directed difference = 0).
Both predict: if the 33-cell carrier's committed generators include degree-≥3 mixed-sign
vertices or boundary-flow-free scrambling, CP.11 and CP.14 should come apart somewhere —
i.e., a GENUINE CO-SURVIVOR outcome is structurally available, not just alias.

## Standing rule applied

Alt-views ride alongside; they assign nothing and decide nothing. The three in-flight
packets adjudicate against their own pinned contracts; this receipt exists so their
audits can check the panel's pre-registered expectations AFTER the results land.
