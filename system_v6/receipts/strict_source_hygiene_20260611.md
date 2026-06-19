# Strict-source hygiene receipt - 2026-06-11

Scope: bounded remediation for the two shape-validator failures and seven strict-source gaps named in the user worklist. No git add or git commit was run.

## Disposition table

| packet | before validator | diagnosis | action | rerun | after validator | disposition |
| --- | --- | --- | --- | --- | --- | --- |
| `geo_s1_negative_models_v0` | `--require-pytorch`: `pytorch.aligned_packages_load_bearing must be non-empty`; `--require-pytorch --strict-source-backed`: same shape error plus `pytorch: source-backed audit failed (no_load_bearing_claim)` | Shape-only defect. PyTorch source already used `torch.func.vmap`; envelope/result declared no aligned load-bearing PyTorch package. | Set PyTorch lane `aligned_packages_load_bearing` to `["torch.func"]` and align `TOOL_INTEGRATION_DEPTH["torch.func"]` to `load_bearing`. | Full Julia, JAX, PyTorch, and envelope rerun returned `ok:true`. | `--require-pytorch`: `ok:true`; `--require-pytorch --strict-source-backed`: `ok:true`. | CLOSED_SHAPE_ONLY |
| `geo_s2_negative_models_v0` | `--require-pytorch`: `pytorch.aligned_packages_load_bearing must be non-empty`; `--require-pytorch --strict-source-backed`: same shape error plus `pytorch: source-backed audit failed (no_load_bearing_claim)` | Shape-only defect. PyTorch source already used `torch.func.vmap`; envelope/result declared no aligned load-bearing PyTorch package. | Set PyTorch lane `aligned_packages_load_bearing` to `["torch.func"]` and align `TOOL_INTEGRATION_DEPTH["torch.func"]` to `load_bearing`. | Full Julia, JAX, PyTorch, and envelope rerun returned `ok:true`. | `--require-pytorch`: `ok:true`; `--require-pytorch --strict-source-backed`: `ok:true`. | CLOSED_SHAPE_ONLY |
| `geo_s1_coord_state_families_v0` | `--require-pytorch --strict-source-backed`: `pytorch: strict source-backed audit requires no thin declared claims: declared load-bearing packages imported but source-token-thin: sympy` | Token-heuristic gap. Source uses `sp.Rational` and `sp.log` for exact endpoint anchors, but validator only recognized other SymPy token shapes. | Additive validator token patterns for `sp.Rational(...)` and `sp.log(...)`; added fake-route-still-fails test. | Not a packet rerun case; existing envelope revalidated under stricter source audit. | `--require-pytorch --strict-source-backed`: `ok:true`. | CLOSED_VALIDATOR_HEURISTIC |
| `mct_dynamic_admissibility_packet_v0` | `--require-pytorch --strict-source-backed`: `jax: strict source-backed audit requires no thin declared claims: declared load-bearing packages imported but source-token-thin: jax.scipy.linalg` | Token-heuristic gap. Source imports `jax.scipy.linalg as jsp_linalg` and uses matrix exponential route, but validator had no token pattern for that package string. | Additive validator token pattern for `jsp_linalg.expm(...)` and direct `jax.scipy.linalg.*(...)`; added fake-route-still-fails test. | Not a packet rerun case; existing envelope revalidated under stricter source audit. | `--require-pytorch --strict-source-backed`: `ok:true`. | CLOSED_VALIDATOR_HEURISTIC |
| `spinor_network_hopf_weyl_testbed` | `--require-pytorch --strict-source-backed`: `julia: strict source-backed audit requires no thin declared claims: declared load-bearing packages imported but source-token-thin: Symbolics` | Genuinely thin route. `Symbolics` was declared load-bearing but the source only loaded it and reported `string(Symbolics)`. | Changed Julia `symbolic_identity()` to use `@variables` plus `Symbolics.simplify` in the commutator residual gate. | Full Julia, JAX, PyTorch, and envelope rerun returned `all_pass:true`. | `--require-pytorch --strict-source-backed`: `ok:true`. | CLOSED_SOURCE_BACKED_RERUN |
| `terrain_generator_sheet_packet` | `--require-pytorch --strict-source-backed`: `jax: strict source-backed audit requires no thin declared claims: declared load-bearing packages imported but source-token-thin: jax.scipy.linalg` | Token-heuristic gap, same `jax.scipy.linalg` route shape as MCT. | Same additive validator token pattern and fake-route-still-fails test. | Not a packet rerun case; existing envelope revalidated under stricter source audit. | `--require-pytorch --strict-source-backed`: `ok:true`. | CLOSED_VALIDATOR_HEURISTIC |
| `terrain_weyl_spinor_lr_v0` | `--require-pytorch --strict-source-backed`: `engines.pytorch must be an object`; also before token patch: `julia: ... source-token-thin: Grassmann` | Mixed disposition. Grassmann was a token-heuristic gap (`@basis` macro was real but the regex used an impossible word boundary before `@`). PyTorch is an honest two-engine mode issue: envelope declares `julia_canon_plus_python_exact_diagnostic` with lanes `["julia", "jax"]`, so forced `--require-pytorch` should not bind. | Additive Grassmann `@basis` token fix plus fake-route-still-fails test. Did not fabricate a PyTorch lane. | Not forced into a three-engine rerun. | Mode-aware strict command without `--require-pytorch`: `ok:true`; forced `--require-pytorch --strict-source-backed` still fails only with `engines.pytorch must be an object`. | CLOSED_HEURISTIC_PLUS_HONEST_TWO_ENGINE_DISPOSITION |

## Negative-packet computed subtree hashes

Stable subtree used for byte-identical check:

```text
{negative_models, positive_control, selectivity_matrix, engine_negative_receipts, measured_failure_magnitudes, build_gates, divergence}
```

| packet | before subtree sha256 | after subtree sha256 | status |
| --- | --- | --- | --- |
| `geo_s1_negative_models_v0` | `e448495d106c0be2dfeb35eec8132d66303a58f2f381d3187e9b8cb5ec5f6667` | `e448495d106c0be2dfeb35eec8132d66303a58f2f381d3187e9b8cb5ec5f6667` | byte-identical |
| `geo_s2_negative_models_v0` | `08600d55f0efcaedb0b4887f48128aedc3c7e8ed9743d74bfd326cd85cd4d3ea` | `08600d55f0efcaedb0b4887f48128aedc3c7e8ed9743d74bfd326cd85cd4d3ea` | byte-identical |

Post-rerun envelope file hashes:

| packet | envelope sha256 |
| --- | --- |
| `geo_s1_negative_models_v0` | `f371b5e79e36bddb465cdf19ae0e339f876ad546b794e5775c70030887829b95` |
| `geo_s2_negative_models_v0` | `c3ed97ed58c7b388b7bb1b86404804aa63ae7f8d6760e86a4c93ca693239828c` |
| `spinor_network_hopf_weyl_testbed` | `aee966643e3c54f0dd8ed46f490ab09df17b5bb49339f558fe32cb5866efa649` |

## Regression matrix

Tracked envelope matrix:

```text
git ls-files 'system_v6/sims/*/results/*_envelope_results.json' -> 70 envelopes
mode-aware strict validation -> count=70 fail=0
```

Matrix rule used:

- `--require-pytorch --strict-source-backed` when `engine_contract.mode` is `all_three_full_sims` or `engine_contract.lanes` includes `pytorch`.
- `--strict-source-backed` for honest two-engine envelopes where PyTorch is not in the declared contract.

Matrix receipt hash:

```text
27db77c37d76c593b1edda3de5f43c307900d2b1dd9b5fd65ced3bd07578e70e  /tmp/strict_source_hygiene_20260611_matrix.tsv
```

## Test receipts

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest system_v5/tests/test_three_engine_sim_result_validator.py -q
10 passed in 0.89s
```

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/codex_runtime_env_doctor.py
ok=True install_state=stable_observed
No repo-local env pollution, missing expected modules, or active installers observed.
```
