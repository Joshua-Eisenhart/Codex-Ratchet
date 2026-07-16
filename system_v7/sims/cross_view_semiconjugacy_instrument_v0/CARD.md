# CARD — cross_view_semiconjugacy_instrument_v0

Lane: external review immediate item 3 (cross-view semiconjugacy instrument).
Ceiling: scratch_diagnostic, promotion_allowed=false. No git commits. Append-only results.

## Source citations (build only from these)

- `system_v7/constraint_core/engines/oracle_targets.py` (READ-ONLY): defines the 16-stage
  1-qubit contract operators. Fe = exact-exponential unitary `U = expm(-i*TH/2 * sz)`,
  acting on Bloch vectors as rotation about the z-axis by TH.
- `system_v7/constraint_core/engines/targets.json` (READ-ONLY): frozen constants.
  `TH = 0.7853981633974483` (pi/4), `Q = 0.6321205588285577`.
- Neither file may be modified. The sim reads targets.json at runtime and asserts TH.

## Object

Earn ONE true semiconjugacy Q(T x) = T_d(Q x) on a finite state sample, with an
instrument that provably REJECTS a visually similar false projection.

- T (fine dynamics): the contract's Fe operator as a Bloch map — rotation about
  z by TH = pi/4. Verified against the density-matrix form `U r U†` (from
  oracle_targets.py's construction, re-implemented locally; do NOT import from
  constraint_core) on >= 10 states to 1e-12, so T is the contract's Fe and not
  an ad-hoc rotation.
- State sample X: deterministic, exhaustive over a frozen grid: Fibonacci-sphere
  directions n_dir = 4096, radii {0.25, 0.5, 0.75, 0.99} -> 16384 Bloch states.
  `np.random.default_rng(0)` declared (even if unused). Pure math, structural
  indices only, no labels in code.
- Candidate projection Q_d: a finite partition of the Bloch ball into cells.
  For every candidate the coarse map T_d is constructed the SAME way:
  best-fit induced map T_d(c) = mode over {Q(T x) : x in cell c}. T_d is never
  hand-picked; acceptance means "a coarse dynamics exists for this partition".
- Semiconjugacy defect: fraction of sample states with Q(T x) != T_d(Q x)
  (report also the worst per-cell mismatch fraction).

## Frozen acceptance rule (freeze BEFORE running; never tuned after)

ACCEPT iff  defect_fraction <= 1e-3  AND  H(Q) >= 1.0 bit,
where H(Q) = Shannon entropy (bits) of the cell-occupancy distribution over the
sample (diagnostic index only, licensed at this ceiling as a structural count).

## Three candidates (all through the identical pipeline)

1. GOOD (must ACCEPT): 8 equal azimuthal sectors about the z-axis,
   cell = floor(atan2(y,x) / (pi/4)) mod 8. Rotation by pi/4 about z permutes
   the sectors cyclically, so the true defect is 0 and T_d is a nontrivial
   8-cycle. Assert the recovered T_d is a cyclic shift (structural check).
2. BAD, visually similar (must REJECT on defect): the SAME 8-sector fan but
   erected about the x-axis, cell = floor(atan2(z,y) / (pi/4)) mod 8.
   Anti-vacuity note: an azimuthal OFFSET does not break the conjugacy
   (rotation about z shifts any offset fan exactly), so the bad control must
   break the AXIS, not the offset. Record its defect; require defect > 0.25
   as the control-fired criterion.
3. TRIVIAL (must be flagged UNINFORMATIVE): constant map, one cell. Defect is
   0 by construction; H(Q) = 0 bits; rejected by the information floor.
   The instrument must report information_retained_bits = 0 explicitly.

## Boundary handling

Exclude sample states within 1e-9 (azimuthal radians, in the candidate's own
coordinate) of any cell boundary of the candidate under test; count exclusions
in the result JSON; excluded fraction must be < 0.1%.

## Deliverables

- `semiconjugacy_instrument.py` — standalone, CWD-independent, python3 from
  /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3, numpy only
  (+ json/os/math). Prints headline invariants. Writes
  `result_v0_run<N>.json` where N = first unused integer (append-only).
- Result JSON per candidate: defect_fraction, worst_cell_mismatch,
  information_retained_bits, n_excluded_boundary, accept (bool), and for the
  good candidate the recovered T_d table + is_cyclic_shift (bool).
  Top level: verdict fields good_accepted, bad_rejected, trivial_flagged,
  instrument_pass = all three, claim ceiling fields
  (classification="scratch_diagnostic", promotion_allowed=false).

## STOP conditions

- STOP if the good candidate's defect is not <= 1e-3: report, do not tune.
- STOP if the bad candidate's defect is <= 0.25: the instrument failed its
  decisive requirement; report honestly, do not weaken the control.
- Never edit targets.json, oracle_targets.py, or anything under constraint_core.
