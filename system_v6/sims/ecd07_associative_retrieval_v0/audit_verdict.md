# Independent audit verdict - ecd07_associative_retrieval_v0

Freshness tier: `TIER-2 results-available`. Auditor read source, build card, standards, registry doctrine, committed results, and recomputed the discriminator from source without rewriting result JSON. Write scope for this audit: this file only.

## Bottom Line

`ECD.07` is a **real below-ceiling tie/death for the implemented searched policies**, not an `UNINFORMATIVE-CEILING` row.

The exact tie is real: QIT/surface best accuracy is `0.9`, the implemented classical best is `0.9`, the prediction-table hash is identical, the full corruption curve ties pointwise, and capacity margin is `0`. But the pinned finite corruption family is **not capped at 0.9**: a finite Bayes/plurality classifier over the emitted cue rows reaches `1.0` accuracy overall and at every corruption level. Therefore 0.9 is not an environment ceiling.

Registry language should not say "no separation observable because the corruption family tops out at 0.9." It should say:

> **ECD.07 associative retrieval: DIES_TIE_v0 below ceiling, with baseline-search caveat.** On the pinned surface-pattern carrier and corruption metric, the best QIT/surface policy and implemented equal-information classical nearest-lookup policy tie exactly at mean accuracy `0.9`, pointwise across the full curve, with capacity margin `0`. This is not an environment-ceiling tie: finite Bayes ceiling on the pinned emitted cue family is `1.0`. The packet therefore shows no QIT edge in the implemented searched class, but the stronger claim "strongest possible equal-information classical baseline is 0.9" is not earned because trainable/Bayes cue classifiers are not implemented.

Claim ceiling remains `scratch_diagnostic`; `promotion_allowed=false`; `formal_admission_allowed=false`. No QIT-engine admission, no global quantum-Hopfield theorem, no surface-doctrine closure, no physics/AGI claim.

## Adjudication

### 1. Tie Nature

Recomputed from `ecd07_associative_retrieval_v0_common.py`:

- QIT best: `surface_basin_nearest_after_committed_cue`, mean accuracy `0.9`.
- Classical best: `classical_nearest_neighbor_lookup`, mean accuracy `0.9`.
- Margin: `0.0`.
- Prediction table: identical SHA-256, `c74f6c0fd7a1e21a1f63d9d62b4a8242fad93f0f081bf9f0a7a9a5197c13a27f`.

Bayes/ceiling recompute over the 160 emitted cue rows:

- cue-only finite Bayes ceiling: `1.0`.
- cue + corruption ceiling: `1.0`.
- cue + corruption + replicate ceiling: `1.0`.
- ceiling curve: `1.0` at `0.0`, `0.125`, `0.25`, `0.375`, and `0.5`.

So the observed `0.9` tie is below available headroom. The discriminator is informative as a no-edge/death for the implemented policies, not an uninformative ceiling test.

### 2. Full Curve

The full curve exists and the tie holds pointwise:

| corruption | QIT max | classical max | margin |
|---:|---:|---:|---:|
| `0.0` | `1.0` | `1.0` | `0.0` |
| `0.125` | `1.0` | `1.0` | `0.0` |
| `0.25` | `1.0` | `1.0` | `0.0` |
| `0.375` | `0.84375` | `0.84375` | `0.0` |
| `0.5` | `0.65625` | `0.65625` | `0.0` |

This is not a single-level tie hiding a curve split.

### 3. Capacity

Capacity rows are present for pattern counts `1..6` at threshold `0.75`.

| patterns | QIT | classical | margin |
|---:|---:|---:|---:|
| `1` | `1.0` | `1.0` | `0.0` |
| `2` | `0.9875` | `0.9875` | `0.0` |
| `3` | `0.941666666667` | `0.941666666667` | `0.0` |
| `4` | `0.9` | `0.9` | `0.0` |
| `5` | `0.85` | `0.85` | `0.0` |
| `6` | `0.816666666667` | `0.816666666667` | `0.0` |

Both sides pass through `6`; capacity margin is `0`.

### 4. Baseline Strength

Implemented classical candidates:

- `classical_nearest_neighbor_lookup`
- `classical_component_majority_associator`
- `classical_hopfield_sync_steps_1`
- `classical_hopfield_sync_steps_2`
- `classical_hopfield_sync_steps_3`
- `classical_hopfield_sync_steps_5`

This covers lookup and Hopfield step-count variants. It does **not** implement the build-card's promised "trainable classical associative structures." It also does not include a Bayes/classifier row over the pinned finite cue family, which would reach `1.0` on the emitted row estate.

That does not rescue QIT. The QIT best is also only `0.9`, and the best QIT policy is the same nearest-cue retrieval table as the classical lookup. But it does mean the phrase "strongest equal-information classical baseline is 0.9" is too strong. The admissible wording is "implemented searched equal-information classical class ties QIT at 0.9; a stronger finite cue classifier has headroom."

### 5. Information Parity And Leak Controls

Information parity is present and symmetric in the result:

- both sides receive `stored_pattern_bits`, `corrupted_cue_bits`, `corruption_level`, and `replicate_seed`;
- asymmetric access lists are empty;
- forbidden predictor inputs include target-at-prediction-time, surface-v3 cell identity, chart cell label, and row-id lookup.

No-identity-leak fields are present:

- `identity_leak_detected=true`
- `identity_inclusive_predictor_accuracy=1.0`
- `identity_leak_excluded_best_accuracy=0.9`
- direct output fingerprint disallowed.

G.2a is wired through `builder_audit_boundary_errors(...)`, the validator accepts the post-audit boundary path, and the builder result emits `no_builder_audit_verdict=true`.

### 6. Controls

Controls are present:

- storage nontriviality: passed at corruption `0.125`, both sides `1.0` over chance `0.25`;
- pinned random base rate: `0.25`;
- dropped-half both sides: first half and second half both run, both sides `1.0`;
- scrambled-pattern regression: margin/table moved; scrambled tie at `0.9375`;
- z3/cvc5: both prove the finite scaled relation `qit_accuracy <= classical_accuracy` by UNSAT of its negation.

### 7. Spurious Attractors

ECD.07 reports `4` spurious pair-mixture terminals over denominator `6`; v1 floor reported `6/6`.

This is a side-row only. Four pair labels overlap the v1 spurious set (`L/R`, `L/entangled`, `L/random`, `R/random`), while two v1-spurious pairs now land on stored terminals (`R/entangled`, `entangled/random`). Exact same-attractor fingerprint equality is not established because v1 persists semantic spurious IDs while ECD.07 persists terminal hashes.

## Verification Commands

Read-only/source recompute commands run:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=system_v6/sims/ecd07_associative_retrieval_v0 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 - <<'PY'
# imported ecd07_associative_retrieval_v0_common, recomputed comparison,
# capacity, finite Bayes ceilings, controls, and solver fields without writes
PY
```

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=system_v6/sims/ecd07_associative_retrieval_v0 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 - <<'PY'
import validate_ecd07_associative_retrieval_v0 as v
import ecd07_associative_retrieval_v0_common as c
print(v.validate_payload(c.load_json(c.RESULT_PATH)))
PY
```

Result: `[]`.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=system_v6/sims/ecd07_associative_retrieval_v0 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest -q -p no:cacheprovider system_v6/sims/ecd07_associative_retrieval_v0/tests
```

Result: `4 passed in 2.91s`.

## Route Truth

Wizard v4.2 Max Assembly status: `PARTIAL/local-audit`. The v4.2 packet, skill manifest, and MMM inventory were loaded for route discipline, but Codex-native subagent fanout was not used because the available subagent tool contract only permits spawning when the user explicitly asks for sub-agents or parallel agent work. This verdict therefore rests on direct artifact reads, source recomputation, validator import, and pytest.

## Block K

Gates cited: user request; `AGENTS.md`; `CODEX.md`; `system_v5/docs/ENFORCEMENT_AND_PROCESS_RULES.md`; `system_v5/docs/LLM_CONTROLLER_CONTRACT.md`; `system_v5/docs/LEGO_SIM_CONTRACT.md`; `system_v6/receipts/audit_standards_codex_v1.md`; `system_v6/receipts/ecd_registry_supplement_1_20260612.md`; `system_v6/receipts/engine_capability_differentiators_20260612.md`; ECD.07 build card/source/result/envelope/validator/tests; spinor surface v1/v3 doctrine/results for ceiling and spurious side-row.

Admission decisions: scratch diagnostic only; `DIES_TIE_v0 below ceiling` accepted for the implemented searched policies; `UNINFORMATIVE-CEILING` rejected; "strongest possible classical baseline is 0.9" not admitted.

Narrative substitutions intercepted: exact tie was not treated as environment ceiling; green validators were not treated as proof of baseline maximality.

Worker claims verified: builder headline numbers, curve, capacity, parity fields, controls, and validator green state were checked against source/result paths.

Worker claims not verified: no independent all-three backend numerical recomputation beyond the packet's own envelope; engine lanes are smoke/guard lanes that merge the same base discriminator values.

Status label changes to registry: none written.

Blocked actions: no git add/commit; no edits outside this verdict; no promotion/admission language.

Next admissible step: add a v1 repair row that includes a finite Bayes/trained cue classifier baseline under the same equal-information rule, then rerun on a corruption family with explicit train/eval split or larger pattern sets where cue-level headroom and generalization are both measurable.
