SUPERSEDED BY audit_verdict_strengthened.md

<!-- This verdict predates applied fixes (null control now present, z3/cvc5 demoted to supportive). See audit_verdict_current.md for current reconciled state. -->

# Audit Verdict - gcm_nested_geometry_delta_3q_v0

Bottom line: GENUINE_WITH_CAVEATS. The core geometry-delta numbers are genuinely recomputed from the 3Q carve carrier under different registry-pin/probe inputs, and the ceiling is honest. Two caveats remain: there is no explicit same-input stable/null geometry control, and the all-three engine claim is not genuinely independent because JAX mirrors scaled packet values and PyTorch recomputes L1 from packet-built delta vectors.

Exact admissible claim ceiling: `scratch_diagnostic_first_flip_controlled_geometry_delta_carrier_and_pins_relative`. This may support only a carrier/pin/probe-relative scratch diagnostic that the A-marginal probe-shell occupation delta moves under the tested alternate registry pin and alternate probe family. It does not admit intrinsic nested geometry, manifold/terrain, engine, bridge, Axis0, or formal/canonical claims.

## Falsifier 1 - Real Computed Numbers

PASS.

Evidence:

- The packet loads upstream state from `gcm_constraint_carve_3q_v1_results.json`, reconstructs `rho_ABC`, partially traces to `rho_A`, and recomputes Bloch coordinates before binning (`gcm_nested_geometry_delta_3q_v0_common.py:264-288`).
- Registry pins are different selectors: free is `C1`, main is `C1+C2+C3`, and alternate pin is `C1+C2` (`gcm_nested_geometry_delta_3q_v0_common.py:291-302`).
- Probe families are different axes: `M_xz` uses x/z and `M_prime_xy` uses x/y (`gcm_nested_geometry_delta_3q_v0_common.py:305-317`).
- Deltas are built from free and nested distributions, with `delta_l1 = sum(abs(delta_vector))` (`gcm_nested_geometry_delta_3q_v0_common.py:337-379`).
- Fresh read-only recompute from the upstream carve result returned:
  - main: free `551`, nested `545`, L1 `0.021778584397`
  - alternate pin: free `551`, nested `547`, L1 `0.014519056263`
  - alternate probe: free `551`, nested `545`, L1 `0.021778584395`

Verdict: the alternate-pin and alternate-probe paths use genuinely different inputs. This is not the runtime-flux-style `L = reverse(R)` tautology.

## Falsifier 2 - Flip Control Genuine

FAIL.

Evidence:

- Flip cases are real: `alternate_registry_pin` changes the nested selector to `alternate_C1_C2_pin_without_C3`; `alternate_probe_family` changes the probe to `M_prime_xy`; `scrambled_pin` uses a same-cardinality alternate pin (`gcm_nested_geometry_delta_3q_v0_common.py:479-504`).
- The negative control is not a no-op. It expects killed-candidate count to be pin-relative and passes because main removed `6` rows while alternate pin removed `4` rows (`gcm_nested_geometry_delta_3q_v0_common.py:512-521`; result JSON `negative_control_status`).
- The scrambled-pin control also exercises a moving path: `stable_against_main=false`, `delta_l1_between_vectors=0.022018348623`, `pass=true`.

Failure reason:

- I found no explicit stable/null geometry control where the same pin/probe or an intentionally equivalent pin/probe should produce delta approximately `0` and does. The tests assert flip movement and negative-control movement, but not a same-input stable/null control (`tests/test_gcm_nested_geometry_delta_3q_v0.py:52-80`).

## Falsifier 3 - Stability Verdict Backed By Values

PASS.

Evidence:

- `cross_pin_stability` and `cross_probe_stability` are computed by comparing delta-vector hashes and by recording L1 distance between delta vectors (`gcm_nested_geometry_delta_3q_v0_common.py:382-392`).
- The stability class is derived in code: `cross_stable` only if both comparisons are stable; otherwise `probe_relative` if the probe comparison moved; otherwise `pin_relative` (`gcm_nested_geometry_delta_3q_v0_common.py:502-510`).
- Recorded values support the verdict:
  - cross pin: `stable=false`, vector L1 distance `0.007312614262`, main L1 `0.021778584397`, alternate-pin L1 `0.014519056263`
  - cross probe: `stable=false`, vector L1 distance `0.043557168792`, main L1 `0.021778584397`, alternate-probe L1 `0.021778584395`
  - class: `probe_relative`

Note: the gate is hash/vector-equality based, not a numeric-threshold gate. It is still computed from the generated delta vectors, not merely hand-set schema text.

## Falsifier 4 - Three-Engine Genuine

FAIL.

Evidence:

- Julia genuinely recomputes from the carve result: it parses `gcm_constraint_carve_3q_v1_results.json`, rebuilds row constraints, bins by probe family, computes delta vectors/L1s, and builds Graphs occupied-bin incidence observables (`gcm_nested_geometry_delta_3q_v0_julia.jl:113-175`).
- JAX does not independently rebuild geometry. It calls `build_packet(write_result=False)`, extracts `engine_claim_values`, places three scaled L1 integers into a `jax.numpy` vector, and runs rational/solver guards on those values (`gcm_nested_geometry_delta_3q_v0_jax.py:48-83`).
- PyTorch is stronger than JAX but still not independent of the packet. It calls `build_packet(write_result=False)`, extracts packet delta vectors, then uses `torch.func.vmap` to recompute row L1 magnitudes from those vectors (`gcm_nested_geometry_delta_3q_v0_pytorch.py:30-60`).
- `max_divergence` is a real comparison over normalized engine result fields (`write_envelope_spec.py:46-66`, `:69-104`), and the recorded envelope has `max_divergence=0`; however, that parity is partly parity against common packet-derived values, not three independent geometry computations.

Verdict: the strict validator passes, but the all-three-engine genuineness claim fails this adversarial audit. Accept only Julia plus Python packet recomputation as genuine geometry computation; treat JAX as scaled-value guard and PyTorch as packet-vector L1 recomputation.

## Falsifier 5 - Ceiling Honest

PASS.

Evidence:

- The result declares `classification="scratch_diagnostic"`, `promotion_allowed=false`, and `formal_admission_allowed=false` (`gcm_nested_geometry_delta_3q_v0_common.py:55-59`, `:537-540`).
- The build card states the packet is not a manifold admission, intrinsic geometry claim, bridge claim, or axis-level claim (`build_card.md:14`).
- The result explicitly blocks intrinsic transport/admission and lists as not claimed: intrinsic tower geometry, formal manifold admission, physics or axis bridge, and cross-stable geometry-delta (`gcm_nested_geometry_delta_3q_v0_common.py:615-659`).
- Fresh read-only checks passed:
  - `scripts/gcm_nested_schema_check.py system_v6/sims/gcm_nested_geometry_delta_3q_v0/results/gcm_nested_geometry_delta_3q_v0_results.json` -> `ok=true`
  - `scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed --require-tool-intent system_v6/sims/gcm_nested_geometry_delta_3q_v0/results/gcm_nested_geometry_delta_3q_v0_envelope_results.json` -> `ok=true`

## Overall

GENUINE_WITH_CAVEATS.

Keep:

- Core computed geometry-delta diagnostic values.
- Alternate registry-pin and alternate-probe movement as real packet evidence.
- Scratch-only, carrier/pin/probe-relative claim ceiling.

Do not keep:

- Independent all-three-engine geometry-computation language.
- Any claim that the packet has a stable/null geometry control.
- Any manifold, terrain, engine, Axis0, bridge, canonical, or formal-admission upgrade.
