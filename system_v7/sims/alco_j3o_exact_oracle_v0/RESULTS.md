# RESULTS

## Verdict

- Classification: `scratch_diagnostic`
- Accepted status: `passes local rerun`
- Validation: `23/23` gates passed
- Upstream ALCO tests: `0` failures in `6` files
- Promotion allowed: `false`
- Formal admission allowed: `false`

ALCO has no spectral log, entropy, channel, DPI, engine, Axis0, perception, object, or physics authority.

## Gates

| Gate | Verdict |
|---|---|
| `schema` | PASS |
| `classification` | PASS |
| `promotion_fences` | PASS |
| `authority_exclusions` | PASS |
| `package_metadata` | PASS |
| `coordinate_map` | PASS |
| `simple_eja_4_8_boundary` | PASS |
| `oracle_execution` | PASS |
| `upstream_alco_tests` | PASS |
| `case_set` | PASS |
| `input_reproduction` | PASS |
| `product` | PASS |
| `trace` | PASS |
| `determinant` | PASS |
| `minimal_polynomial` | PASS |
| `quadratic_representation` | PASS |
| `quadratic_identities` | PASS |
| `corrupted_product_kill` | PASS |
| `alco_commit_pin` | PASS |
| `alco_install_binding` | PASS |
| `alco_tracked_sources_clean` | PASS |
| `source_dependency_hashes` | PASS |
| `deterministic_contract` | PASS |

## Exact cases

- Seeded cases: `7`, `29`, `101`, `20260709`
- Structured kill: `kill_fano_e1_e2`
- Compared surfaces: product, trace, determinant, generic cubic minimal polynomial, `U_x(y)`, `U_y(x)`, Cayley-Hamilton, quadratic homogeneity, determinant covariance, and the fundamental formula.
- Boundary: `SimpleEuclideanJordanAlgebra(4,8)=fail`

## Artifact hashes

- `alco_j3o_exact_oracle_result.json`: `0e911bcc4aa04820a34337f6acfb7fbff209e660b6f5fa15b62f5138af0c1d91`
- `alco_j3o_exact_oracle_validation.json`: `d319180ce11075c017723d2329bdcb6020c5862ece8a8f7140746c20a81d7c76`

Every named source and dependency hash is recorded and rechecked in the JSON provenance gate. `RESULTS.md` is generated after those artifacts and is intentionally not included in the self-referential source manifest.

## Role ceiling

- Builder: GAP oracle and Python exact-formula controller ran.
- Mechanical gatekeeper: `validate_oracle.py` ran exact comparisons and provenance checks.
- Fabrication control: corrupted-product kill ran and flipped the structured witness.
- Independent fresh-context semantic auditor: not run.
- Canonical/admission gates: not run and not applicable to this packet's requested ceiling.
