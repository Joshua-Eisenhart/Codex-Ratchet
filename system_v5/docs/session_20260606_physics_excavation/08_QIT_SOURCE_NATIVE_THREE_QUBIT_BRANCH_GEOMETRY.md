# QIT Source-Native Three-Qubit Branch Geometry

Claim ceiling: completed QIT source-native three-qubit branch geometry scratch diagnostic. The completed JAX receipt is:

`/Users/joshuaeisenhart/Codex-Ratchet/system_v5/ops/formal_scouts/results/qit_source_native_three_qubit_branch_geometry_probe_results.json`

The source is:

`/Users/joshuaeisenhart/Codex-Ratchet/system_v5/ops/formal_scouts/sim_qit_source_native_three_qubit_branch_geometry_probe.py`

This doc corrects the toy-knot drift. The QIT-engine branch object must use the proposed QIT math and geometry: finite spinor network, three-qubit minimum, left/right Weyl sheets, Hopf fiber/base loops, density/probe readouts, source-native terrain/operator schedule, and Axis-6 signed precedence.

It does not admit a QIT engine, physics, gravity, Axis0, `M(C)`, PEPS3D, bridge promotion, final manifold closure, or dark-sector claims.

## Source Boundary

Primary source anchors:

- `/Users/joshuaeisenhart/Codex-Ratchet/system_v5/ops/formal_scouts/canonical_qit_engine_specs.py`
- `/Users/joshuaeisenhart/Codex-Ratchet/system_v5/ops/QIT_ENGINE_FULL_EXPLICIT_MATH_PACKET_20260522.md`
- `/Users/joshuaeisenhart/Codex-Ratchet/system_v5/docs/CONSTRAINT_ON_DISTINGUISHABILITY_FULL_MATH.md`
- `/Users/joshuaeisenhart/Codex-Ratchet/system_v5/docs/CLAUDE_THREAD_HANDOFF_QIT_ENGINES_OPERATIONAL_MANIFOLD_PRIMARY_20260515.md`
- `/Users/joshuaeisenhart/Codex-Ratchet/system_v5/docs/CLAUDE_THREAD_HANDOFF_FLUX_TERRAIN_AXIS_OPERATOR_DISCIPLINE_20260515.md`

Correction boundary:

- `/Users/joshuaeisenhart/Codex-Ratchet/system_v5/ops/formal_scouts/results/knot_mass_gravity_rung_results.json` is not consumed by this scout.
- The knot rung remains toy-scale scratch diagnostic only: graph-distance falloff over a finite line, not QIT-engine geometry.

## State

`COMPLETED`.

Receipt fields:

| Field | Value |
|---|---:|
| `schema` | `QIT_SOURCE_NATIVE_THREE_QUBIT_BRANCH_GEOMETRY_PROBE_v1` |
| `classification` | `scratch_diagnostic` |
| `all_pass` | `true` |
| `formal_admission_allowed` | `false` |
| `promotion_allowed` | `false` |
| `n_qubits_minimum` | `3` |
| `hilbert_dimension` | `8` |
| `branch_response_rank_3q` | `4` |
| `branch_response_rank_4q` | `4` |

## Object

The finite object is a source-native branch probe over:

- primitive carrier: finite 3-qubit spinor-network state `psi in (C^2)^3`;
- qubit roles: left Weyl sheet, right Weyl sheet, cut/shell memory spinor;
- derived layer: density `rho`, marginals, mutual information, and Bloch readouts;
- geometry: Hopf spinor chart with fiber loop and lifted-base loop;
- schedule: source-native QIT terrain/operator schedule from `canonical_qit_engine_specs.py`;
- Axis-6: signed precedence from the source operator-slot specs.

The scout also runs a 4-qubit branch check as a non-promotion scaling sanity check.

## Branches Tested

| Branch | Role |
|---|---|
| `source_native` | Full source-native left/right Weyl Hopf/density terrain-loop schedule branch. |
| `sign_only_control` | Keeps signs while removing terrain/loop substance; must be insufficient. |
| `axis6_erased_control` | Erases Ax6 signed precedence; must differ from source-native. |
| `phase_quotient_control` | Removes spinor-network phase entanglement; must differ from source-native. |
| `reverse_schedule_control` | Reverses the source schedule; must differ from source-native. |
| `2-qubit floor control` | Removes the third cut/shell spinor; must fail the carrier floor. |

## Result Summary

| Readout | Value |
|---|---:|
| `branch_response_rank_3q` | `4` |
| `branch_response_rank_4q` | `4` |
| `axis6_gap` | `0.1474270857183994` |
| `phase_quotient_gap` | `0.6646577237288537` |
| `two_qubit_floor_gap` | `1.1172236810802714` |
| `fiber_density_stationary_gap` | `6.206335383118183e-17` |
| `base_density_visible_gap` | `0.47101707546014354` |

## Controls

| Control | Completed result |
|---|---|
| 3-qubit floor | Pass: left Weyl, right Weyl, and cut/shell memory spinor require `n_qubits=3`, Hilbert dimension `8`. |
| 2-qubit floor failure | Pass: sheet-only control changes the branch signature with gap `1.1172236810802714`. |
| Hopf loop distinction | Pass: fiber loop is density-stationary to `6.2e-17`; lifted-base loop is density-visible with gap `0.47101707546014354`. |
| branch rank | Pass: source/control branch matrix has rank `4` at the 3-qubit floor. |
| Ax6 load-bearing | Pass: Ax6-erased control differs from source-native with gap `0.1474270857183994`. |
| phase quotient load-bearing | Pass: phase-quotient control differs from source-native with gap `0.6646577237288537`. |
| sign-only insufficient | Pass: sign-only control differs from source-native with gap `0.8891430152921135`. |
| reverse schedule differs | Pass: reverse schedule differs from source-native with gap `0.3552642048022905`. |
| toy-knot exclusion | Pass: knot-mass-gravity result is not consumed. |

## Branch Readings

The old QIT handoff preserves three live readings. This scout keeps all three open:

| Reading | Status In This Scout |
|---|---|
| `R1` information-preserving channel | `open_supported`: unitary/operator portions preserve finite density validity and rearrange mutual-information signatures, but dissipative terrain is also active. |
| `R2` basin-fall dissipation | `open_supported`: terrain and ladder channels change purity/entropy and make `source_native` differ from sign-only. |
| `R3` non-abelian schedule behavior | `open_supported`: reverse schedule control differs at the 3-qubit floor; not promoted to canonical-cycle closure. |

No reading is promoted to winner.

## Audit State

Repo-local verification:

- `py_compile` passed.
- Fresh JAX rerun passed and wrote the result receipt.
- Result JSON reports `all_pass=true`.

External audit:

- Grok CLI is not installed in this shell, so no Grok verdict is claimed for this new rung.
- Gemini audit returned `GENUINE`: the result is supported by controls that isolate the claim; the simpler 2-qubit version and altered Ax6-erased version fail/differ, so the finding is not just trivial label relabeling or true by construction under the stated scout-only fence.

## Fence

The passing result supports:

- the QIT-source-native branch object must be at least 3 qubits for this test;
- source-native branch controls separate at the 3-qubit floor;
- Hopf fiber/base loop distinction is visible in density readouts;
- Ax6 signed precedence and spinor-network phase/cut structure are load-bearing in this scout;
- 4-qubit scaling remains noncollapsed in the same bounded diagnostic.

It does not support:

- QIT engine admission;
- physics admission;
- gravity admission;
- Axis0 admission;
- `M(C)` admission;
- PEPS3D admission;
- bridge promotion;
- final manifold closure;
- Standard Model or dark-sector claims.

## Next Hardening Step

Build an independent Julia mirror that reimplements the same 3-qubit source-native branch from formulas rather than importing the Python source. Then run label-blind branch scrambling and alternate carrier-parameter sweeps.
