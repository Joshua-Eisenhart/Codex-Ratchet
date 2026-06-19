# Audit Verdict - fiber_augmented_cover_v0

Bottom line: the packet is green as a scratch execution and the faithfulness rows pass, but the stronger load-bearing negative does not survive the audit teeth. The exact scaffold law `b6=-b0*b3` fails as a universal relation on this computed table, yet the observed `60/132` agreement is statistically at-chance and the packet does not compute the required nontrivial bundle winding/Euler witness. Verdict: `PASS_WITH_CAVEATS`; claim ceiling remains `axis_readout_candidate_only + faithful_fiber_augmented_cover_b6_law_test_v0`; no promotion, no formal admission.

## Scope

- Audit standard: `system_v6/receipts/audit_standards_codex_v1.md`.
- Freshness tier: `TIER-2` results-available. The prompt exposed builder claims and result counts; no prior audit verdict was read because none existed in this packet before this file.
- Write boundary honored: live repo writes limited to this `audit_verdict.md`. The validator entrypoint was rerun with its sidecar output redirected to `/tmp/fiber_augmented_cover_v0_validator_results_audit.json`.
- Packet status before this verdict: `system_v6/sims/fiber_augmented_cover_v0/` is untracked in git; no `git add` or commit was run.

## Validator And Recompute

Commands/checks run:

```text
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 - <<'PY'
from pathlib import Path
import sys
sys.path.insert(0, str(Path('system_v6/sims/fiber_augmented_cover_v0').resolve()))
import fiber_augmented_cover_v0_common as common
common.VALIDATOR_RESULT_PATH = Path('/tmp/fiber_augmented_cover_v0_validator_results_audit.json')
import validate_fiber_augmented_cover_v0 as validator
raise SystemExit(validator.main())
PY
```

Result: `ok=true`, `errors=[]`.

```text
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest -q -p no:cacheprovider system_v6/sims/fiber_augmented_cover_v0/tests
```

Result: `5 passed in 4.96s`.

Independent source rebuild matched the live result for `state_object_id`, `cover`, `quotient_projection`, `faithfulness`, `relation_table`, `relation_sign_vector`, `relation_sign_vector_sha256`, `b6_law_test`, `controls`, `smt_rows`, `TOOL_MANIFEST`, `TOOL_INTEGRATION_DEPTH`, and `all_pass`.

## Faithfulness First

Faithfulness passes, so the law table is not void on this tooth:

| axis | recomputed result | verdict |
|---|---:|---|
| Axis0 pullback | `mismatch_count=0`, `projects_to_committed_axis0=true` | pass |
| Axis3 finite-fiber predicate adapter | `gamma_in_rows=66`, `gamma_out_rows=66`, `predicate_mismatch_count=0`, source-backed adapter true | pass |
| Axis6 pullback | `mismatch_count=0`, `projects_to_committed_axis6=true` | pass |

This supports a faithful readout-table test at scratch ceiling. It does not by itself certify a nontrivial bundle.

## Bundle Tooth

The packet pins `FIBER_PHASE_COUNT=4`, so it avoids the panel's binary `|F|=2` parity-only concern. That does not settle the panel divergence, because the source does not compute the required directed winding/Euler-class witness around a closed base loop.

Recomputed transition facts:

| transition family | phase-shift counts |
|---|---:|
| base-lift edges | `{0: 792}` |
| vertical fiber-cycle edges | `{1: 132}` |

All base-lift edges preserve the fiber phase slot. The only nonzero shifts are vertical fiber-cycle edges inside each projection fiber. Therefore the packet is compatible with the trivial product cover over the base, and no computed witness distinguishes nontrivial `S^3`-like bundle (`±1`) from trivial `S^2 x S^1` product (`0`). This is the main blocker to calling the negative load-bearing against the intended bundle object.

## Chance Adjudication

The exact law row is:

| law | agreements | violations | two-sided binomial p vs 0.5 | lower-tail p | classification |
|---|---:|---:|---:|---:|---|
| `b6=-b0*b3` | `60/132` | `72/132` | `0.3383802389` | `0.1691901195` | at-chance / unsupported |
| nonneutral only | `56/128` | `72/128` | `0.1846826271` | not decisive | at-chance / unsupported |
| `b6=+b0*b3` | `60/132` | `72/132` | `0.3383802389` | `0.1691901195` | at-chance / unsupported |

So the exact universal scaffold relation fails on the computed table, but the rate does not significantly exclude the law and is not significantly anti-aligned. The sign-flip alternative is equally at-chance. There are `16` nonneutral rows where `b6=0`, so both the negative and positive product laws fail on those rows.

## Sign-Convention Sweep

All eight signed variants were recomputed from the row table with `s6*b6 = -(s0*b0)*(s3*b3)`.

| s0 | s3 | s6 | agreements | nonneutral agreements | verdict |
|---:|---:|---:|---:|---:|---|
| `+1` | `+1` | `+1` | `60/132` | `56/128` | at-chance |
| `+1` | `+1` | `-1` | `60/132` | `56/128` | at-chance |
| `+1` | `-1` | `+1` | `60/132` | `56/128` | at-chance |
| `+1` | `-1` | `-1` | `60/132` | `56/128` | at-chance |
| `-1` | `+1` | `+1` | `60/132` | `56/128` | at-chance |
| `-1` | `+1` | `-1` | `60/132` | `56/128` | at-chance |
| `-1` | `-1` | `+1` | `60/132` | `56/128` | at-chance |
| `-1` | `-1` | `-1` | `60/132` | `56/128` | at-chance |

No sign convention variant holds far above chance. The result is not rescued as a convention-relative positive.

## Controls

Controls fire for computed reasons:

| control | recomputed result | verdict |
|---|---:|---|
| v0 unfaithful Hopf transplant regression | `16/48`, nonneutral `16/32`, matches expected v0 negative | pass as contrast |
| v1 unfaithful 33-cell proxy regression | `16/33`, nonneutral `15/32`, matches expected v1 proxy | pass as contrast |
| convention flip `b6=+b0*b3` | `60/132` | pass as at-chance control, not rescue |
| scrambled b6 hash signs | `59/128` nonzero-expected agreement | pass as chance-level control |
| z3 / cvc5 selected row checks | real contradictions `unsat`, erased flips `sat` | pass for row-local binding only |

The solver checks bind selected row values and relation-status contradictions; they do not compute bundle topology or statistical exclusion.

## What Died / What Did Not

Died on this packet:

- The scaffold proposal `b6=-b0*b3` as an exact universal relation on this computed faithful-cover table under the pinned conventions.
- Any stronger claim that this result is a statistically significant exclusion or anti-aligned structure.
- Any claim that this packet has certified the intended nontrivial fiber bundle; the required winding/Euler witness is missing.

Did not die:

- Axis0, Axis3, or Axis6 as readout axes.
- The finite `33 x 4 = 132` state cover/projection machinery at scratch ceiling.
- The faithful pullback/adapted readout table itself.
- The broader possibility that a later nontrivial-bundle carrier with a computed winding/Euler witness could retest the scaffold relation.

## Citation Rule

Future citations should say:

> `fiber_augmented_cover_v0` is a scratch diagnostic faithful readout-table test. Validator and tests pass; Axis0/Axis3/Axis6 faithfulness rows pass; exact `b6=-b0*b3` fails on the computed table (`60/132` agreement, `72/132` violations), but the rate is at-chance (`two-sided p=0.3384`) and all eight sign variants are at-chance. The packet pins `|F|=4` but does not compute a nontrivial winding/Euler-class witness; base-lift phase shifts are all zero, so the load-bearing negative against the intended nontrivial bundle is not accepted. Ceiling: `axis_readout_candidate_only + faithful_fiber_augmented_cover_b6_law_test_v0`; no promotion or formal admission.

## Source Citations

- Build ceiling and expected commands: `system_v6/sims/fiber_augmented_cover_v0/build_card.md:6-13`, `system_v6/sims/fiber_augmented_cover_v0/build_card.md:87-93`.
- Object and faithful-realization contract: `system_v6/sims/fiber_augmented_cover_v0/build_card.md:24-46`.
- Law and control contract: `system_v6/sims/fiber_augmented_cover_v0/build_card.md:48-68`.
- Boundary contract: `system_v6/sims/fiber_augmented_cover_v0/build_card.md:70-85`.
- Source pins and `|F|=4`: `system_v6/sims/fiber_augmented_cover_v0/fiber_augmented_cover_v0_common.py:30-78`.
- Base-lift and fiber-cycle construction: `system_v6/sims/fiber_augmented_cover_v0/fiber_augmented_cover_v0_common.py:268-333`.
- Quotient projection: `system_v6/sims/fiber_augmented_cover_v0/fiber_augmented_cover_v0_common.py:352-383`.
- Law computation: `system_v6/sims/fiber_augmented_cover_v0/fiber_augmented_cover_v0_common.py:386-445`.
- Faithfulness computation: `system_v6/sims/fiber_augmented_cover_v0/fiber_augmented_cover_v0_common.py:467-525`.
- Controls computation: `system_v6/sims/fiber_augmented_cover_v0/fiber_augmented_cover_v0_common.py:530-609`.
- Packet object/all-pass fields: `system_v6/sims/fiber_augmented_cover_v0/fiber_augmented_cover_v0_common.py:721-801`.
- Validator checks: `system_v6/sims/fiber_augmented_cover_v0/validate_fiber_augmented_cover_v0.py:35-66`.
- Result summary and controls: `system_v6/sims/fiber_augmented_cover_v0/results/fiber_augmented_cover_v0_results.json:30-128`.
- Result faithfulness and quotient fields: `system_v6/sims/fiber_augmented_cover_v0/results/fiber_augmented_cover_v0_results.json:16134-16207`.
- SMT row-local checks: `system_v6/sims/fiber_augmented_cover_v0/results/fiber_augmented_cover_v0_results.json:20250-20339`.
- Panel 9 bundle and chance targets: `system_v6/receipts/panel9_blind_altviews_wave_targets_20260612.md:31-57`.
- Audit standard freshness/pre-registration/builder-boundary rules: `system_v6/receipts/audit_standards_codex_v1.md:109-172`.
