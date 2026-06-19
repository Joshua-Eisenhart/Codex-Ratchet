# Independent Audit Verdict - fiber_augmented_cover_v1

Bottom line: `fiber_augmented_cover_v1` is a genuine scratch diagnostic packet for the repaired object, with caveats. The winding witness is nontrivial under the correct lifted full-turn definition, faithfulness recomputes on the new `33 x 3 = 99` cover, and the law result is: `b6=-b0*b3` fails on this faithful nontrivial cover at chance (`46/99` agreements, `53/99` violations, two-sided binomial `p=0.546713483598813`). This supports the registry language: `unsupported at chance on the first faithful nontrivial cover (this carrier, these pinned realizations)`.

Verdict: `GENUINE-WITH-CAVEATS`.

Claim ceiling: `axis_readout_candidate_only + nontrivial_cover_faithful_fiber_augmented_cover_b6_law_test_v1`; `promotion_allowed=false`; `formal_admission_allowed=false`.

Freshness tier: `TIER-2` for the v1 packet. The prompt exposed builder claims and required the v0 audit commit `cf7fe65c4` plus panel 9 commit `27b52fc64`; those were treated as source anchors, not as v1 verdict evidence.

## Scope And Boundary

- Audit standard: `system_v6/receipts/audit_standards_codex_v1.md`, including G.2a.
- Required anchors read: v0 audit at `cf7fe65c4`; panel 9 at `27b52fc64`.
- Live repo write boundary honored: this file only. No `git add`, commit, or result rewrite was run.
- Subagent route: not run. The available native spawn tool is restricted to explicit user requests for delegation; this audit therefore used local source/result recomputation and tools only.

## Winding Arithmetic

The packet pins the correct witness definition: sum lifted fiber phase transitions around the closed equatorial base loop, then divide by `|F|`. For this packet the lifted shifts are `[1, 1, 1, 0]`, their integer sum is `3`, `|F|=3`, and the directed winding/Euler witness is `3/3 = 1`.

The mod-3 residue is `0`, but that only says the lifted path closes in the fiber after one complete turn. It is not the Chern/winding witness. Reading only the residue would erase exactly the degree that panel 9 Q2 asked the packet to preserve: one full rotation gives `+/-1`; the trivial product gives `0` turns.

Recomputed loop facts:

| item | result |
|---|---|
| loop | `20 -> 17 -> 12 -> 15 -> 20` |
| scaled coordinates | `[0,1,0] -> [0,0,1] -> [0,-1,0] -> [0,0,-1] -> [0,1,0]` |
| closed directed base loop | yes |
| committed base edges | edge ids `125, 107, 77, 95`, all generator `R_x` |
| lifted shifts on loop | `[1, 1, 1, 0]` |
| total lifted shift | `3` |
| directed winding / Euler witness | `1` |
| witness gate | passed before law rows |

The seam-crossing degree-1 clutching is the pinned transition map for the loop edges: the three nonzero projection transitions each lift across three fiber states, producing `9` nonzero base-lift cover edges. The packet has `585` zero-shift and `9` shift-1 base-lift edges.

## Trivial Regression Control

The v0 zero-shift product-bundle regression fired:

| control tooth | recomputed result |
|---|---|
| zero-shift witness | `directed_winding=0` |
| v1 law gate on trivial product | law table refused |
| historical v0 law reference | `60/132`, `72` violations, at-chance, two-sided `p=0.3383802389` |

That is the right negative control: the trivial product is not allowed to masquerade as the repaired object.

## Faithfulness On The New Cover

Faithfulness was recomputed on the `|F|=3` cover; v0 faithfulness was not carried over.

| axis | recomputed result | verdict |
|---|---:|---|
| Axis0 pullback | `mismatch_count=0`, projects to committed Axis0 | pass |
| Axis3 finite-fiber native adapter | `gamma_in_rows=33`, `gamma_out_rows=66`, `predicate_mismatch_count=0` | pass |
| Axis6 pullback | `mismatch_count=0`, projects to committed Axis6 | pass |

Axis3 is computed from the committed `gamma_in` / `gamma_out` predicates on pinned finite fiber phases. It is not a quotient-only label.

## Law Adjudication

The law table row unit is `cover_state`, not base cell. The row-count change is exactly the fiber-size change: v0 had `33 x 4 = 132`; v1 has `33 x 3 = 99`.

| law | agreements | violations | two-sided p vs 0.5 | classification |
|---|---:|---:|---:|---|
| `b6=-b0*b3` | `46/99` | `53/99` | `0.546713483598813` | at-chance |

Nonneutral rows also stay at chance: `43/96` agreements, `53/96` violations, two-sided `p=0.3583976321916262`.

All eight sign variants were present and at-chance. The agreement counts are only `44/99` or `46/99`; no sign convention rescues the relation.

| variant class | variants | agreements | two-sided p | classification |
|---|---:|---:|---:|---|
| lower count | 4 | `44/99` | `0.31487989103762243` | at-chance |
| higher count | 4 | `46/99` | `0.546713483598813` | at-chance |

Therefore the exact universal relation fails on this computed table, but the rate is not a statistically significant exclusion or anti-law signal. The result is unsupported at chance, not globally disproven.

## Controls And Identity Leak

Computed controls fired:

| control | recomputed result | verdict |
|---|---:|---|
| convention flip `b6=+b0*b3` | `44/99`, two-sided `p=0.31487989103762243` | at-chance, no rescue |
| scrambled b6 hash signs | `42/96` nonzero-expected agreements, two-sided `p=0.26146943628638786` | at-chance |
| v0 unfaithful Hopf transplant contrast | `16/48`, expected contrast | pass as contrast only |
| v1 unfaithful 33-cell proxy contrast | `16/33`, expected contrast | pass as contrast only |

Identity-leak check, recomputed audit-side:

| predictor | accuracy for `relation_holds` | note |
|---|---:|---|
| `row_id` or `cover_state_id` | `1.0` | excluded row identity |
| `projection_cell_id + fiber_phase_slot` | `1.0` | excluded cover-state identity |
| direct output fingerprint `b0,b3,b6` | `1.0` | excluded direct relation data |
| `projection_cell_id` alone | `0.7171717171717171` | below 1.0 |
| `fiber_phase_slot` / phase family alone | `0.5353535353535354` | chance-majority level |

This is enough for the law-table audit because no independence claim is promoted. Caveat G1: the packet does not emit top-level `identity_leak_detected`, `identity_leak_excluded_best_accuracy`, and `identity_leak_exclusion_rule` fields, so do not cite it as a standalone no-identity-leak independence packet.

## G.2a Boundary

G.2a passes from birth. The packet uses `scripts/builder_audit_boundary.py`; the packet boundary module delegates audit verdict handling to the shared helper; the build card names the helper; and no hard permanent `audit_verdict.md` absence assertion was found. This verdict header declares independent/fresh/read-only audit status, so the post-audit idempotency helper remains satisfiable.

## Verification Run

Checks run without writing packet result files:

```text
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 - <<'PY'
from pathlib import Path
import sys, json
sim=Path('system_v6/sims/fiber_augmented_cover_v1').resolve()
sys.path.insert(0, str(sim))
import fiber_augmented_cover_v1_common as common
import validate_fiber_augmented_cover_v1 as validator
payload=common.load_json(common.RESULT_PATH)
errors=validator.validate_payload(payload)
print(json.dumps({'ok': not errors, 'errors': errors}, indent=2, sort_keys=True))
PY
```

Result: `ok=true`, `errors=[]`.

```text
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest -q -p no:cacheprovider system_v6/sims/fiber_augmented_cover_v1/tests
```

Result: `5 passed in 4.19s`.

Lint caveat G2: I could not locally verify the builder's lint-green claim. `python -m ruff` in the sim-stack interpreter failed with `No module named ruff`, and no `ruff` binary was available on PATH. This is a tooling-availability caveat, not a math/result caveat.

## Status Language

Accepted registry/status language:

```text
unsupported at chance on the first faithful NONTRIVIAL cover (this carrier, these pinned realizations)
```

Still open:

- other carriers;
- other realization pins;
- other admissible finite-fiber or clutching choices;
- other axis-adapter choices that are pinned before evaluation;
- any later formal-admission route.

Must not be said:

- `the b6=-b0*b3 law is disproven globally`;
- `Axis0/Axis3/Axis6 are killed`;
- `this is formal admission`;
- `this result is canonical by process`;
- `this proves axis independence`.

## Citation Rule

Future citations should say:

> `fiber_augmented_cover_v1` is a scratch diagnostic repaired-object test. It computes a nontrivial lifted full-turn winding witness on the committed equatorial loop (`[1,1,1,0]`, total `3`, `|F|=3`, witness `1`) before law rows; the zero-shift product control computes witness `0` and refuses v1 law rows; Axis0, Axis3, and Axis6 faithfulness recompute on the `33 x 3 = 99` cover; the exact scaffold relation `b6=-b0*b3` fails on this faithful nontrivial cover with `46/99` agreement and `53/99` violations, two-sided binomial `p=0.546713483598813`; all eight sign variants are at-chance, so there is no convention rescue. Status: unsupported at chance on the first faithful nontrivial cover, this carrier and these pinned realizations only. Ceiling: `axis_readout_candidate_only + nontrivial_cover_faithful_fiber_augmented_cover_b6_law_test_v1`; no promotion; no formal admission; not a global disproof.
