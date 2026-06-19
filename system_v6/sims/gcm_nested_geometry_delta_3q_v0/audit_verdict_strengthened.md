SUPERSEDED BY audit_verdict_current.md

<!-- This verdict predated the applied fixes; null control is now present and z3/cvc5 are demoted. NEEDS_FIX disposition is resolved. See audit_verdict_current.md for current reconciled state. -->

# Strengthened Audit Verdict - gcm_nested_geometry_delta_3q_v0

Bottom line: NEEDS_FIX. The same-input null control is now genuine, the flip-side controls still move from recomputed carve data, and the engine relabeling is honest. The new z3/cvc5 crossover proof lane is decorative: corrupting a proof input did not flip either solver verdict, so `z3` and `cvc5` must not be labeled `load_bearing` unless the proof is rewired to a real structural polarity check.

Overall verdict: NEEDS_FIX.

Exact fix: demote `z3` and `cvc5` from `TOOL_INTEGRATION_DEPTH=load_bearing` to `supportive`, remove them from `claim_path_tools` as claim-bearing tools, and set `crossover_proofs.*.load_bearing=false`; or replace the current proof with a solver statement that binds variables to independently recomputed measured values and flips under an erased/corrupted value. The current equality-plus-self-contradiction guard is not enough.

Admissible claim ceiling: `scratch_diagnostic_first_flip_controlled_geometry_delta_carrier_and_pins_relative`. This admits only a carrier/pin/probe-relative scratch diagnostic for the A-marginal probe-shell occupation delta. It does not admit manifold, terrain, engine-independence, Axis0, bridge, formal, canonical, or intrinsic geometry claims.

## Falsifier 1 - NULL CONTROL GENUINE

PASS.

Evidence:

- Source rows are recomputed from the 3Q carve source: `rho_ABC` is loaded, partial-traced to `rho_A`, converted to Bloch coordinates, and constraint flags are read from killed rows (`gcm_nested_geometry_delta_3q_v0_common.py:294-318`).
- Deltas are computed from selected free/nested rows, probe-family distributions, and `sum(abs(delta_vector))`, not constants (`gcm_nested_geometry_delta_3q_v0_common.py:370-407`).
- The same-input null is a second `delta_run` with the same free pin, same nested pin, and same probe family as `main`, then compared vector-to-vector (`gcm_nested_geometry_delta_3q_v0_common.py:533-540`, `:563-565`).
- Fresh read-only recompute from the carve source returned:
  - main: `delta_l1=0.021778584397`, nested count `545`, vector sha `b4cbf3e75c8ea2b0aeec2168095378ac7272ddd6668fa7c4d95f886d2f1e07d1`
  - repeat/same-input: `delta_l1=0.021778584397`, nested count `545`, same vector sha
  - same-input vector L1: `0.0`
  - cached Bloch mismatches: `[]`
- Flip side still moves:
  - alternate pin: `delta_l1=0.014519056263`, nested count `547`, `stable=false`, vector L1 vs main `0.007312614262`
  - alternate probe: `delta_l1=0.021778584395`, nested count `545`, `stable=false`, vector L1 vs main `0.043557168792`

Verdict: the null is computed and the flips are data-derived from different pin/probe selections. This falsifier passes.

## Falsifier 2 - CROSSOVER PROOFS LOAD-BEARING vs DECORATIVE

FAIL.

Evidence:

- The proof function builds integer values from the measured deltas/counts, then asserts each solver variable equals that same value and also asserts an OR saying at least one variable is not equal to that same value (`gcm_nested_geometry_delta_3q_v0_common.py:449-481`).
- That proves only that `x=v AND x!=v` is unsatisfiable for the currently supplied values. It does not bind the values to an independently recomputed source object or a real structural erased/corrupt control.
- Fresh polarity test:
  - real values: z3 `unsat`, cvc5 `unsat`
  - corrupted `alternate_pin_delta_l1_scaled=0`: z3 `unsat`, cvc5 `unsat`
  - no verdict flip occurred.
- The source nevertheless marks both proofs as `load_bearing=true` (`gcm_nested_geometry_delta_3q_v0_common.py:482-496`) and `TOOL_INTEGRATION_DEPTH` marks `z3` and `cvc5` as `load_bearing`.

Verdict: decorative. The `TOOL_INTEGRATION_DEPTH` labels for `z3` and `cvc5` are wrong as written and must be demoted to `supportive`, unless the proof is rewritten so corrupting/erasing a measured value flips the proof verdict.

## Falsifier 3 - ENGINE RELABEL HONEST

PASS, with one validator caveat.

Evidence:

- Envelope mode is `julia_python_packet_geometry_with_supportive_jax_pytorch_guards`, with audit order `python_packet`, `julia_local`, `jax_supportive`, `pytorch_supportive` (`write_envelope_spec.py:96-100`).
- Engine ceiling says `no all-three-engine independence claim`; Julia and Python packet geometry are load-bearing, while JAX is `scaled_value_guard` and PyTorch is `packet_vector_l1_recomputation`.
- JAX reads packet values from `build_packet(write_result=False)`, round-trips scaled integers through `jax.numpy`, and labels all packages supportive with empty `aligned_packages_load_bearing` (`gcm_nested_geometry_delta_3q_v0_jax.py:48-83`).
- PyTorch reads packet-built delta vectors from `build_packet(write_result=False)`, computes L1 magnitudes with `torch.func.vmap`, and labels all packages supportive with empty `aligned_packages_load_bearing` (`gcm_nested_geometry_delta_3q_v0_pytorch.py:30-60`).
- `TOOL_INTEGRATION_DEPTH` uses `jax_scaled_value_guard=supportive` and `pytorch_packet_vector_l1=supportive`.

Validator caveat:

- Packet-local validator passed: `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/gcm_nested_geometry_delta_3q_v0/validate_gcm_nested_geometry_delta_3q_v0.py` returned `ok=true`.
- Generic validator failed even without strict flags: `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py system_v6/sims/gcm_nested_geometry_delta_3q_v0/results/gcm_nested_geometry_delta_3q_v0_envelope_results.json` returned `ok=false`, error `jax.aligned_packages_load_bearing must be non-empty`.
- This validator failure is consistent with the honest relabeling but means the envelope is not commit-ready under the generic three-engine validator unless that validator gains a mode-aware supportive-engine path or this packet stops presenting itself as a generic three-engine result.

Verdict: relabeling itself is honest. Do not restore JAX/PyTorch independent-geometry language.

## Falsifier 4 - CEILING HONEST

PASS.

Evidence:

- Result declares `classification=scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`, and the carrier/pin/probe-relative claim ceiling (`gcm_nested_geometry_delta_3q_v0_common.py:595-604`).
- Forward transport is explicitly blocked as intrinsic geometry and limited to carrier-and-pins-relative scratch diagnostic only (`gcm_nested_geometry_delta_3q_v0_common.py:682-685`).
- Backward admissibility is `not_admitted` (`gcm_nested_geometry_delta_3q_v0_common.py:687-690`).
- Claim summary explicitly lists not-claimed: intrinsic tower geometry, formal manifold admission, physics or axis bridge, cross-stable geometry-delta, and three independent geometry engines (`gcm_nested_geometry_delta_3q_v0_common.py:719-728`).
- Schema check passed: `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/gcm_nested_schema_check.py system_v6/sims/gcm_nested_geometry_delta_3q_v0/results/gcm_nested_geometry_delta_3q_v0_results.json` returned `ok=true`.

Verdict: no manifold/terrain/engine/Axis0/bridge admission found in the strengthened result. Ceiling remains honest.

## Overall

NEEDS_FIX.

Keep:

- Same-input stable/null control.
- Alternate pin and alternate probe flip controls.
- JAX/PyTorch supportive relabeling.
- Scratch-only carrier/pin/probe-relative ceiling.

Fix before commit:

- Demote `z3` and `cvc5` to supportive, or rewrite the crossover proof so corrupted/erased measured values flip the solver verdict.
- Resolve the generic validator mismatch for supportive JAX/PyTorch lanes, either by using a mode-aware validator path for this packet or by adjusting the envelope schema so it is not treated as a full generic three-engine load-bearing result.
