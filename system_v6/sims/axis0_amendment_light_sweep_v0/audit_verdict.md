# Independent audit verdict - axis0_amendment_light_sweep_v0

Bottom line: **NOT ACCEPTED under the current binding amendment pins.** The
packet is internally consistent as a `python_exact_amendment_light_sweep`
scratch diagnostic against the older `4f7595a8d` amendment table, but it does
not satisfy the current `AMENDMENT SUPPLEMENT 1` formula pins committed at
`34596316d`. Therefore CP.11 and CP.14 are **not citable co-survivors from this
packet**. They remain formula-pin-blocked/provisional until a supplement-pinned
rerun computes the required formulas.

Family-status sentence:

```text
Within the already-audited CP.3-CP.9 heavy-pass space, the citable status
remains the anchor alias class from c27d3dd39; in the amendment space, CP.11
and CP.14 are not accepted as light co-survivors because this packet fails the
current formula-pin conformance gate, while CP.12 and CP.13 remain open +
queued-heavy.
```

## Verdict Table

| Check | Verdict | Notes |
| --- | --- | --- |
| Packet arithmetic under its own adapter | PASS | Fresh import-only recomputation matched stored JSON: `all_pass=true`, verdict table matches, CP.11 hash matches, CP.14 hash matches, fork row matches. |
| Current adapter pin compliance | FAIL | Current `system_v6/receipts/axis0_registry_amendment_1_20260612.md` Supplement 1 requires different CP.11 and CP.14 formulas than the packet implements. |
| CP.11 label | NOT ACCEPTED | Packet computes terrain-family sign divided by outgoing edge count and scaled by `(1 + cell_id % 3) / 3`; Supplement 1 requires system typed von Neumann entropy of the committed cell state object and one-step `S_after - S_before` majority over the committed generator family. |
| CP.14 label | NOT ACCEPTED | Packet computes a coordinate-derived two-outcome entropy proxy and outgoing scalar gradient; Supplement 1 requires single-cell reduced von Neumann entropy with committed-adjacency directed difference. |
| Fork row arithmetic | PASS as arithmetic only | CP.14-vs-anchor disagreement recomputes to 20 cells, but this does not rescue CP.14 because the CP.14 adapter is not supplement-pinned. |
| Owner guard | PASS | The deliberate chirality tracker is excluded; CP.11 and CP.14 do not track Type1/2 chirality under the packet predicate. |
| SMT | PASS as table integrity only | z3 and cvc5 return positive `unsat` and flip-control `sat`; they bind aggregate computed counts, not the semantic formula pins. |
| Mode honesty | PASS with caveat | `mode=python_exact_amendment_light_sweep`; Julia/JAX are contract mirrors of the exact Python lane, not independent Julia Canon or JAX array implementations; PyTorch is omitted. |
| Claim ceiling | scratch diagnostic only | `classification=scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`; directory is currently untracked. |

## Decisive Pin Failure

The packet binds `AMENDMENT_COMMIT = "4f7595a8d"` and successfully proves that
the original amendment text exists. That is not enough for the current audit
because current HEAD includes `AMENDMENT SUPPLEMENT 1`, which explicitly says
the landed light sweep's CP.11/CP.14 verdicts are provisional until checked
against the formula pins.

Current binding pins:

- CP.11: system typed von Neumann entropy of the cell's committed state object;
  rate is the one-step difference under the committed generator family; sign per
  cell is the majority sign of `S_after - S_before`; no bath terms or new
  channels.
- CP.14: marginal is the single-cell reduced von Neumann entropy; gradient is
  the committed-adjacency directed difference.

Implemented packet formulas:

- CP.11: `entropy_production_raw()` uses terrain family
  `Ne/Ni=+`, `Se/Si=-`, divides by local outgoing edge count, and scales by
  `(1 + cell_id % 3) / 3`.
- CP.14: `marginal_entropy_scalar()` derives a two-outcome entropy from
  coordinate magnitudes `abs(x)+1` versus `abs(y)+abs(z)+2`, then applies the
  outgoing scalar gradient.

Those are deterministic and recomputable, but they are not the supplement-pinned
state-object von Neumann entropy formulas. This is the G7 failure: the packet
has a pinned adapter, but not the currently registered adapter.

## Recomputed Values

Fresh import-only recomputation used the Makefile interpreter with bytecode
disabled. I did not run writer entrypoints for the sim, envelope, or packet
validator because they rewrite result files.

Sample recomputed cells:

| cell | terrain | anchor raw/sign | CP.11 raw/sign | CP.14 raw/sign |
| --- | --- | --- | --- | --- |
| 0 | Ni | `-38/97`, `-1` | `1/18`, `+1` | `943382097/250000000000`, `+1` |
| 16 | Ne | `0`, `0` | `1/9`, `+1` | `0`, `0` |
| 32 | Ne | `-15/97`, `-1` | `1/6`, `+1` | `943382097/250000000000`, `+1` |

Stored/recomputed counts:

```json
{
  "candidate_count": 4,
  "computed_vector_count": 3,
  "queued_heavy_count": 2,
  "co_survivor_count": 2,
  "owner_guard_excluded_count": 1,
  "prior_light_exclusion_count": 3,
  "fork_disagreement_count": 20
}
```

These values show internal consistency only. They do not certify the current
formula pins.

## Co-Survivor Labels

Under the packet's own older adapter:

- CP.11 recomputes as a non-alias 33-cell row with 24 anchor disagreements,
  boundary predicate true, and owner guard survived.
- CP.14 recomputes as a non-alias 33-cell row with 20 anchor disagreements,
  boundary predicate true, and owner guard survived.
- CP.11 and CP.14 are not aliases of each other under the packet's canonical
  pair table.

Under the current audit standard:

- CP.11 is **not** a light co-survivor because the CP.11 formula is not the
  supplement-pinned entropy-production formula.
- CP.14 is **not** a light co-survivor because the CP.14 formula is not the
  supplement-pinned marginal-von-Neumann formula.

Additional vocabulary caveat: the packet field `failed_light_rows` contains
`per-cell-disagreement` for CP.11 and CP.14. In the packet logic that
disagreement is the positive non-alias signal, not an exclusion row. The field
name is misleading and should not be cited as a failed exclusion predicate.

## Fork Row

The fork row is real for the implemented adapter:

```text
fork: marginal_entropy_CP14_vs_correlation_family_anchor_CP0
outcome: disagrees
disagreement_count: 20
disagreement_cells: 0,1,2,3,4,6,7,8,9,10,11,13,17,18,21,23,24,27,31,32
```

Citable only as packet-arithmetic:

```text
The marginal-entropy fork does not collapse into the committed correlation-family anchor under this light adapter.
```

Do **not** cite it as a supplement-pinned CP.14 result.

## Owner Guard

The owner anti-collapse guard is implemented and fires:

- `control.deliberate_chirality_tracker` is excluded by
  `owner-type1-type2-chirality-guard`.
- CP.11 and CP.14 both have `tracks_type1_type2_chirality=false`.
- Their guard witnesses show mixed candidate signs inside both chirality groups,
  so their packet polarities do not collapse to Type1/2 chirality.

This passes the guard, but guard success cannot override formula-pin failure.

## SMT, Validators, And Mode

Fresh checks run:

```text
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest -q -p no:cacheprovider system_v6/sims/axis0_amendment_light_sweep_v0/tests
-> 6 passed

PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-tool-intent system_v6/sims/axis0_amendment_light_sweep_v0/results/axis0_amendment_light_sweep_v0_envelope_results.json
-> ok=true

PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --strict-source-backed --require-tool-intent system_v6/sims/axis0_amendment_light_sweep_v0/results/axis0_amendment_light_sweep_v0_envelope_results.json
-> ok=false; sympy source-token-thin and Julia mirror/source-backed weakness

PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --require-tool-intent system_v6/sims/axis0_amendment_light_sweep_v0/results/axis0_amendment_light_sweep_v0_envelope_results.json
-> ok=false; engines.pytorch missing
```

I did not run:

```text
axis0_amendment_light_sweep_v0.py
axis0_amendment_light_sweep_v0_envelope.py
validate_axis0_amendment_light_sweep_v0.py
```

Their `main()` functions write result JSONs, and the audit write scope allowed
only this verdict file.

## Named Caveats

1. **Formula-pin failure:** the decisive blocker. CP.11 and CP.14 do not
   implement the current Supplement 1 formulas.
2. **Old-commit binding drift:** the packet binds and hashes `4f7595a8d`, but
   current HEAD has `34596316d` supplement pins that explicitly govern this
   audit.
3. **Not true cross-backend:** the envelope's Julia/JAX records are mirrors of
   one exact Python source lane; no independent Julia Canon or JAX array
   computation is claimed.
4. **SMT scope:** z3/cvc5 bind aggregate computed counts and flip controls, not
   the per-cell formula semantics.
5. **Strict-source-backed fails:** the stricter validator rejects thin/mirror
   source evidence.
6. **Untracked packet:** `git status --short -- system_v6/sims/axis0_amendment_light_sweep_v0`
   shows the packet directory as untracked at audit time.
7. **Misleading `failed_light_rows`:** `per-cell-disagreement` is used as a
   non-alias signal, not an exclusion failure.

## Heavy-Pass Queue

The heavy queue remains:

- CP.12: open + queued-heavy; must use Supplement 1 trace-norm prediction-error
  flux pin.
- CP.13: open + queued-heavy; must use the global bipartition coherent
  information convention pin.
- CP.11: requires formula-pinned rerun before any light co-survivor citation.
- CP.14: requires formula-pinned rerun before any light co-survivor citation.

## Final Adjudication

`axis0_amendment_light_sweep_v0` is a useful failed audit packet: it proves its
own older light-adapter arithmetic, fork arithmetic, owner guard, queue labels,
and scratch ceiling. It fails the current amendment formula-pin gate. The
co-survivor labels for CP.11 and CP.14 are rejected for citation until a new
formula-pinned light sweep passes.
