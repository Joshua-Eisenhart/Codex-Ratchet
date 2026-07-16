# L5 data-driven re-audit v1 — frozen card

Status: preregistered build card. This file is written before `reaudit.py` and
must not be tuned after the first execution.

Ceiling: `scratch_diagnostic`; `promotion_allowed=false`;
`formal_admission_allowed=false`. A passing run is a finite data-driven
re-audit receipt only. It does not restore the withdrawn L5 claim, admit a
manifold layer, prove a hidden generator, or replace the required fresh audit.

## Audit-kill boundary

Read first:

- `system_v7/constraint_core/ratchet/runs/L5_REAUDIT_AUDIT_KILLED_NOTE.md`
- `system_v7/constraint_core/external_packet_audits/fresh_audit_v0_4_engine_20260711.md`

The prior receipt is killed because most positive candidates restated the
ground-truth formula, its split was algebraic/synthetic, and two controls were
hardcoded. This build may consume only copied finite rows. It must not import
the old re-audit, its `truth` helper, the source generator script, or any closed
form of the generator.

## Frozen data and interface

- Read-only source:
  `system_v7/constraint_core/sims_and_scripts/manifold_L5_nested_shells_schmidt_strata_sim_results.json`
- Required source SHA-256:
  `ba96e5888e42851798925572b238d564ca0c1797b07362c4c876a97e4af04116`
- Local copied input: the same basename in this directory, byte-for-byte.
- Row surface: the nine objects in `dual_ratchet_sweep`.
- Feature available to predictors: `a` only.
- Ordered prediction vector:
  `[shell_radius, marg_entropy_bits, purity, negativity]`.
- No predictor receives a row object or any heldout readout.

## Frozen split

For each seed, start with source indices `0..8`, run
`random.Random(seed).shuffle(indices)`, take the first six shuffled indices as
fit and the remaining three as heldout, then sort each partition by source
index for fitting and scoring. The primary split uses seed `0`. Stability uses
seeds `0`, `1`, and `2`. This is a seeded random row split, never an alternating,
threshold, midpoint, or other algebraic split.

## Frozen score and verdict

- Per-readout RMSE is computed on heldout rows.
- Pooled heldout RMSE is the square root of the mean squared error over all
  heldout rows and all four readouts, with no post-run rescaling or weights.
- Numerical identity tolerance: `1e-12`.
- Practical-equivalence tolerance: `0.01` pooled RMSE, fixed as one percent of
  the unit-scale readout range before execution.
- `NESTED_SHELL_BEATS_SCALAR` iff
  `scalar_rmse - nested_rmse > 0.01`.
- `SCALAR_BEATS_NESTED_SHELL` iff
  `nested_rmse - scalar_rmse > 0.01`.
- Otherwise the verdict is `INDISTINGUISHABLE_WITHIN_FROZEN_TOLERANCE`.
- The verdict string must be identical for seeds `0`, `1`, and `2`; otherwise
  the split-stability control fails and the overall run is red.

## Seven candidates

Every candidate is fitted anew from the six fit rows only. Hyperparameters
below are frozen; no heldout selection is allowed.

1. `k_nearest_neighbor_lookup`: store fit angles/readout vectors; predict the
   unweighted mean of the two nearest fit rows, breaking distance ties by source
   index.
2. `polynomial_degree3`: independent least-squares polynomials of degree three
   or less from angle to each readout. Angle normalization uses fit minimum and
   fit span only.
3. `monotone_piecewise_linear`: infer each readout's monotone direction from
   the sign of fit-only angle/readout covariance, apply deterministic PAVA
   isotonic fitting, and linearly interpolate/extrapolate the fitted knots.
4. `scalar_stratum`: fit one scalar readout, `shell_radius`, as a degree-three
   angle polynomial. From fit rows only, fit degree-three maps from the observed
   fit scalar to each of the other three readouts. At inference, predict the
   scalar from angle and pass that predicted scalar through the learned maps.
   Heldout scalar labels are never inputs.
5. `nested_shell_structured`: fit the shell radius as a cubic Bernstein curve
   in fit-normalized angle. Estimate its four control radii by least squares,
   infer monotone direction from fit-only covariance, and project the controls
   into that monotone order by deterministic PAVA. From fit rows only, fit the
   same three degree-three scalar-to-readout maps used by candidate 4. These
   four ordered control radii and twelve readout-map coefficients are the fitted
   free parameters of a monotone nested-radius surrogate. The source contains
   no topology or embedding fields, so this candidate must not be described as
   full nested-shell geometry.
6. `constant_mean_baseline`: predict the four fit-column means. It must lose on
   primary heldout RMSE to the best of candidates 1–5 by more than `0.01`.
7. `deliberate_high_degree_overfit`: independently interpolate each readout at
   all six fit angles, then add a degree-six nullspace product that is exactly
   zero at every fit angle. Its signed amplitude is derived only from the fit
   column range and a frozen gain of `1000`; no heldout value is used. It must
   have fit RMSE at most `1e-12`, win the fit ranking, and have heldout RMSE more
   than `0.01` worse than the best of candidates 1–5.

## Source-leakage gate

The build fails before fitting if the exact token `cos(2` appears anywhere in
the delimited candidate implementation block. The scanner constructs its token
dynamically so it does not match itself. The same block is AST-scanned to ban
trigonometric calls and references named `truth`, `generator`, `heldout`,
`all_rows`, or `source_sweep`. Runtime inference accepts angle arrays only.

This token gate is necessary but not sufficient: the candidate block may not
load files, import the old sim, receive heldout labels, or call a helper outside
the audited numeric-helper whitelist.

## Executed controls

1. `label_erasure`: on each seed, deterministically permute the six fit label
   vectors with `random.Random(913 + seed).shuffle`, keep angles fixed, refit
   candidates, and score against the untouched true heldout rows. Candidate 4
   and candidate 5 must each degrade by more than `0.01`; the mean baseline must
   remain numerically identical because label marginals are preserved.
2. `split_reshuffle`: execute the full primary comparison on seeds `0`, `1`,
   and `2`; all three nested-vs-scalar verdicts must match.
3. `overfit_flip`: candidate 7 must win fit and lose heldout under the frozen
   rules above.
4. `mean_baseline_loses`: candidate 6 must lose to the best regular candidate
   on primary heldout by more than `0.01`.
5. `inference_interface`: predictions must be functions of angle arrays only;
   no heldout readout can be passed to a predictor.

No control delta may be authored as a literal result; every delta is computed
from refitted candidate predictions.

## Weakness witnesses

Candidate records must expose actual fitted numeric parameter arrays and count
their scalar entries mechanically. Assumption sets are explicit data, but
assumption count alone never creates an edge. A valid projection may reduce or
preserve parameter count; the recorded count delta must never be invented.

The required candidate-5-to-candidate-4 projection converts fitted Bernstein
controls `[c0,c1,c2,c3]` to power-basis coefficients
`[c0, 3(c1-c0), 3(c0-2c1+c2), -c0+3c1-3c2+c3]`, preserves the three fitted
readout maps, and drops the monotone-control/nested-radius assumptions. Execute
that projected scalar representation on both fit and heldout angles and compare
it with the fitted candidate-5 predictions. Record:

- source and target parameter counts and their computed delta;
- source and target assumption sets and the computed strict-subset test;
- the concrete dropped parameter names;
- fit and heldout projection RMSE.

The weakness edge is witnessed only if target parameter count is no greater
than source parameter count, target assumptions are a strict subset, and both
projection RMSE values are at most `1e-12`. Report whether it is a
parameter-reducing edge or an equal-parameter assumption weakening. Otherwise
the edge is absent; it must not be asserted in prose.

## Determinism and append-only result

Interpreter:
`/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3`.

`results_v1.json` is an append-only JSON-Lines receipt despite its historical
`.json` suffix. Each run canonicalizes one complete result record with sorted
keys, compact separators, no NaN, and no timestamp/run index, validates every
existing line, opens with `O_APPEND`, writes exactly one line, and `fsync`s.
Run twice: stdout and the two newly appended record lines must be byte-identical.
Existing lines are never rewritten, deleted, or moved.

The script prints the primary heldout RMSE table, the three seed verdicts, the
control status, the final verdict, and the append path. Stop after the two-run
freeze. A fresh-context audit is explicitly next and is not part of this build.
