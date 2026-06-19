# Independent audit verdict - topology_parity_cell_model_v1

Bottom line: `REJECT` for the earned independent guard claim. The arithmetic checks pass, but the packet fails the audit's primary kill question: the load-bearing 2-cell/3-cell chain rule is not derived tightly enough from the committed `fiber_augmented_cover_v1` cover construction. It replaces the committed 33-cell/198-edge cover object with a new 33-face cellular S2 bundle model whose boundary choices are exactly Betti-load-bearing.

Verdict: `REJECT_TARGET_BETTI_FITTING_RISK`.

Claim ceiling: arithmetic scratch fixture only. It may be cited as "a no-write audit recomputed the packet's chain-complex arithmetic and found the numbers internally consistent, but rejected the independent guard claim because the load-bearing cell rules are not construction-derived from the committed cover." It must not be cited as an earned independent homology certificate for `fiber_augmented_cover_v1`.

Freshness tier: `TIER-2 results-available`. I read the build card, source, stored results, standards surface, v0 honest-null commit metadata, and cover-v1 audit/source surfaces before final adjudication. I did not run the packet writer or envelope writer because those rewrite result JSON files.

## Scope And Boundary

- Audit request boundary: read-only except this file. Honored.
- No `git add`, commit, or result rewrite was run.
- The packet directory is currently untracked in this checkout: `git status --short -- system_v6/sims/topology_parity_cell_model_v1` reports `?? system_v6/sims/topology_parity_cell_model_v1/`.
- Binding commits exist and were checked by `git show --stat --oneline`: `ce9628302` for `topology_parity_micro_v0` and `80860aa4f` for `fiber_augmented_cover_v1`.
- Native Codex subagent route was not run. The available spawn tool permits subagents only on explicit user request for delegation, so this audit used local source/result inspection and local recomputation.

## Primary Kill Question - Target-Betti Fitting

The seam degree itself is construction-derived:

- `fiber_augmented_cover_v1_common.py` pins `EXPECTED_BASE_STATE_COUNT = 33`, `FIBER_PHASE_COUNT = 3`, `EQUATOR_LOOP_CELLS = [20, 17, 12, 15]`, and `EQUATOR_LIFTED_CLUTCHING_STEPS = {(20,17):1, (17,12):1, (12,15):1, (15,20):0}`.
- `topology_parity_cell_model_v1_common.py` extracts the same loop from `cover_v1_common.build_cover(...)` and computes shifts `[1,1,1,0]`, total `3`, `|F|=3`, degree `1`.
- The zero-shift product branch computes shifts `[0,0,0,0]`, total `0`, degree `0`.

That part survives.

The load-bearing cell model does not survive the stop condition. The committed cover-v1 construction is a finite 33-state, 198-base-edge, 99-cover-state object with base-lift edges and fiber-cycle edges. It does not commit the 33 base states as 33 oriented 2-faces in a cellular S2 with:

- `C0(base)=<south,north>`;
- `C1(base)=<meridian_0,...,meridian_32>`, each `south -> north`;
- `C2(base)=<face_0,...,face_32>`, with `d(face_i)=meridian_{i+1}-meridian_i`.

Those rules are introduced in the new build card and implemented in `expanded_bundle_chain()`. They are not recovered from the cover's actual 198-edge adjacency, pole rows, transition rows, or a committed 2-cell incidence table. The only construction-side inputs consumed by the homology chain are `BASE_FACE_COUNT=33` and the seam degree.

This is Betti-load-bearing. With the introduced chain rule, degree `1` gives ranks `{d1:1,d2:34,d3:32}` and Betti `[1,0,0,1]`; degree `0` gives ranks `{d1:1,d2:33,d3:32}` and Betti `[1,1,1,1]`. The desired distinction is produced by the introduced cellular model plus one clutching entry, not by a boundary matrix derived from committed cover cells.

Audit classification: target-Betti fitting risk is decisive under the prompt's rule:

```text
Any rule choice that lacks a construction-side justification and happens to be Betti-load-bearing = fitting = REJECT.
```

## Independent Arithmetic Recompute

I independently rebuilt the displayed chain matrices from the source formulas and recomputed integer ranks over the chain complexes without using the stored result fields as evidence.

Result:

| row | dims | ranks | Betti | d^2 |
|---|---:|---:|---:|---|
| expanded v1 degree 1 | `[2,35,66,33]` | `{1:1,2:34,3:32}` | `[1,0,0,1]` | zero |
| expanded product degree 0 | `[2,35,66,33]` | `{1:1,2:33,3:32}` | `[1,1,1,1]` | zero |
| explicit S3 degree 1 reference | `[1,1,1,1]` | `{1:0,2:1,3:0}` | `[1,0,0,1]` | zero |
| explicit S2xS1 degree 0 reference | `[1,1,1,1]` | `{1:0,2:0,3:0}` | `[1,1,1,1]` | zero |
| degree-2 torsion trap | `[1,1,1,1]` | `{1:0,2:1,3:0}` | `[1,0,0,1]` | zero |

The degree-2 Smith normal form diagonal is `[2]`, so the torsion trap correctly exposes `H1 = Z/2` while the Betti vector remains `[1,0,0,1]`.

These arithmetic checks are real, but they do not rescue the guard because the primary construction-derived-cell rule fails.

## Reference Gate

The reference gate is independent of the cover in the narrow sense that it uses abstract reduced Euler-class CW complexes, not cover complexes relabeled:

- explicit `S3`: reduced oriented circle bundle over S2 with degree `1`;
- explicit `S2xS1`: same reduced machinery with degree `0`.

The gate recovers the known profiles `[1,0,0,1]` and `[1,1,1,1]`.

Caveat: this is a machinery sanity gate for Euler-class CW complexes. It is not evidence that the committed cover-v1 finite carrier itself has supplied the required 2-cell/3-cell incidence structure.

## Wrong-Gluing Control

The wrong-gluing control is exactly seam erasure at the degree level:

- v1 seam shifts `[1,1,1,0]` are replaced by `[0,0,0,0]`;
- the degree changes from `1` to `0`;
- the recomputed Betti profile changes from `[1,0,0,1]` to `[1,1,1,1]`, matching the product row.

This control confirms the introduced chain model is sensitive to the seam degree. It does not prove that the introduced chain model is construction-derived from cover-v1.

## Torsion Honesty

The degree-2 trap passes:

- Betti profile: `[1,0,0,1]`;
- Smith normal form diagonal for the load-bearing `d2=[2]`: `[2]`;
- reported torsion: `H1=Z/2`;
- `betti_only_underpowered=true`.

The caveat is carried into the result controls. That means even a future accepted Betti row would need a torsion-aware citation boundary for degree-2 or other torsion regimes.

## G.2a

G.2a passes. The packet carries `no_builder_audit_verdict=true`, `no_builder_audit_verdict_envelope_gate=true`, and delegates audit-file handling through `scripts/builder_audit_boundary.py` in `topology_parity_cell_model_v1_boundary.py` and the validator. This independent audit file has the expected independent-audit header.

## Verification Commands

No-write validator import:

```text
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 - <<'PY'
from pathlib import Path
import sys, json
sim=Path('system_v6/sims/topology_parity_cell_model_v1').resolve()
sys.path.insert(0, str(sim))
import topology_parity_cell_model_v1_common as common
import validate_topology_parity_cell_model_v1 as validator
payload=common.load_json(common.RESULT_PATH)
errors=validator.validate_payload(payload)
print(json.dumps({'ok': not errors, 'errors': errors}, indent=2, sort_keys=True))
PY
```

Result: `ok=true`, `errors=[]`.

No-cache pytest:

```text
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest -q -p no:cacheprovider system_v6/sims/topology_parity_cell_model_v1/tests
```

Result: `6 passed in 5.54s`.

Independent rank/SNF recompute:

```text
expanded_v1_degree1: Betti [1,0,0,1], ranks {1:1,2:34,3:32}
expanded_product_degree0: Betti [1,1,1,1], ranks {1:1,2:33,3:32}
explicit_s3_degree1: Betti [1,0,0,1]
explicit_s2xs1_degree0: Betti [1,1,1,1]
torsion_degree2: Betti [1,0,0,1], Smith diagonal [2]
```

## Citation Rule

Do not cite `topology_parity_cell_model_v1` as an earned independent homology guard for `fiber_augmented_cover_v1`.

Allowed citation:

> `topology_parity_cell_model_v1` is a rejected scratch arithmetic fixture. A fresh audit recomputed its chain-complex ranks, reference profiles, seam-erasure control, and degree-2 torsion trap as internally consistent, but rejected the independent guard claim because the load-bearing 33-face S2 cellular boundary model is introduced by the packet and not derived from the committed `fiber_augmented_cover_v1` cover incidence data.

The cover-v1 bundle claim still has the existing winding witness certificate from `fiber_augmented_cover_v1` (`80860aa4f`). It does not yet have a second accepted homology-profile certificate.

What remains open:

- derive an actual cellular boundary complex from the committed cover-v1 carrier data, or commit a source-side 2-cell incidence structure before Betti evaluation;
- rerun the degree-one/product/wrong-gluing/torsion checks on that construction-derived complex;
- keep the degree-2/torsion regime separate from Betti-only claims;
- test other carriers and other pinned cover constructions separately.
