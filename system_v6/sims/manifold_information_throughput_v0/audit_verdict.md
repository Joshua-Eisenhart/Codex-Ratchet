# Fresh audit verdict: manifold_information_throughput_v0

Auditor: codex1 cross-backend auditor.
Date: 2026-06-11.
Scope: read-only audit of the codex2-built `manifold_information_throughput_v0` packet, with this `audit_verdict.md` as the only intended write. No `git add` or commit was performed.

## Source standard

- Calibration bar: exactness-class stability, source-backed quotes, recomputation, can-fail controls, and scratch ceilings.
- Typed entropy discipline: `manifold_entropy_ledger_v0` / `a54224476` separates differential, mixed differential-plus-discrete, von Neumann, and lattice/counting entropy; no cross-type sum is allowed without an explicit product/bookkeeping convention.
- No entropy-as-primitive framing: entropy/information rows are readouts of channel, quotient, carrier, and record structure, not the primitive object.
- Active packet ceiling: `classification="scratch_diagnostic"`, `promotion_allowed=false`, `formal_admission_allowed=false`.

## Commands and checks run

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 \
  system_v6/sims/manifold_information_throughput_v0/validate_manifold_information_throughput_v0.py
# -> ok: true; nested validate_three_engine_sim_result.py --require-source-backed ok: true

/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 \
  scripts/validate_three_engine_sim_result.py \
  system_v6/sims/manifold_information_throughput_v0/results/manifold_information_throughput_v0_envelope_results.json \
  --require-source-backed
# -> {"ok": true, "result_json": "system_v6/sims/manifold_information_throughput_v0/results/manifold_information_throughput_v0_envelope_results.json"}
```

Independent recomputation one-shot returned:

```text
Z4 state_loss_without_record = ln(4) = 1.3862943611198906
Z4 retained_record coefficient = ln(4) = 1.3862943611198906
Z4 extended_account_defect = 0.0
D_z six-state Holevo = 0.411341122022618
D_z six-state killed = 0.28180605853732726
D_z dephasing quantum capacity = 0.2704380927539544
stage 3 delta = 0.411341122022618 - 0.31463929237730087 = 0.09670182964531715
720 density output = 0.019959213845365253
720 density destroyed = 0.67318796671458
spinor sign-record row = ln(2) = 0.6931471805599453
```

## Q1 - conservation row, adjudicated hard

Verdict: `PARTIAL_PASS_WITH_HARD_RECORD_OBJECT_CAVEAT`.

The arithmetic row passes, but the stronger "record side is independently constructed in this packet as a Z4 syndrome/preimage object" bar is not fully met.

What the target packet actually computes:

- Source sets `lens_loss = math.log(4)` and emits `state_loss_without_record_nats = lens_loss`, `record_retained_nats = lens_loss`, and `extended_account_defect_nats = 0.0` (`manifold_information_throughput_v0_jax.py:401-416`).
- The z3/cvc5 rows bind integer coefficients: `after == before - 2`, `record == 2`, and assert the negated conservation identity is UNSAT, with erased-record SAT controls (`manifold_information_throughput_v0_jax.py:442-510`; `manifold_information_throughput_v0_julia.jl:85-110`).
- The envelope mirrors the row: `Z4_lens.record_retained_nats = 1.3862943611198906`, `state_loss_without_record_nats = 1.3862943611198906`, `extended_account_defect_nats = 0.0` (`results/manifold_information_throughput_v0_envelope_results.json:1485-1490`).

The explicit quotient structure exists in parent evidence:

- `ratchet_deep_chain_v0` constructs the step-2 object as a `Z4 quotient torus chart`, with `Z4_generator = alpha += pi/2` and `orbit_order = 4` (`ratchet_deep_chain_v0.py:349-355`; `ratchet_deep_chain_v0_envelope_results.json:900-920`).
- The deep-chain step says the Z4 finite phase lens excludes `three of four global-phase representatives per orbit` and has `quotient_order = 4` (`ratchet_deep_chain_v0.py:423-429`; `ratchet_deep_chain_v0_envelope_results.json:880-897`).

The broader record object also exists in the compression-flow parent:

- `compression_flow_radiated_record_v0` constructs emitted `record_entries`; `raw_row` entries carry full canonical support/probe rows, while `quotient_class` entries carry density-only quotient class ids (`compression_flow_radiated_record_v0_jax.py:181-199`, `:228-293`).
- Its quotient-mode killed-information object is named as `raw-row identity within P_density quotient classes`, computed by `sum_emitted ln(|P_density_class|)` (`compression_flow_radiated_record_v0_jax.py:300-351`; `compression_flow_radiated_record_v0_jax_results.json:697-715`).

Hard caveat:

`CAVEAT_Q1_RECORD_SIDE_NOT_PACKET_LOCAL_Z4_SYNDROME`. The target packet does not construct a Z4 syndrome table, preimage table, or per-orbit record payload for the Z4 lens. It assigns `record_retained_nats = lens_loss` and solver-checks the coefficient identity. The independent object support is therefore: quotient-order/preimage structure in `ratchet_deep_chain_v0` plus a broader emitted-row record construction in `compression_flow_radiated_record_v0`. That is enough for a computed quotient-order conservation account, but not enough to say the target packet itself computed a non-circular Z4 record object.

Recomputed account:

- Z4 quotient preimage size: `4`.
- State loss without record: `ln(4) = 1.3862943611198906`.
- Inferred syndrome record capacity: `ln(4) = 1.3862943611198906`.
- Extended defect: `ln(4) - ln(4) = 0.0`.
- State-only defect: `ln(4)`, matching the packet's `state_level_without_record_defect_nats`.

Accepted wording: "first computed quotient-order conservation account with an inferred Z4 syndrome-record coefficient and parent record anchor."

Rejected wording: "fully constructed Z4 radiated-record object" or "record side independently computed inside this packet."

## Q2 - capacity rows

Verdict: `PASS_WITH_ROW_SCOPE_LIMITS`.

The S4 dephasing rows are exact where claimed:

- Source fixes `lambda = 7/10`, `p = 3/20`, exact dephasing Holevo, and exact dephasing quantum capacity (`manifold_information_throughput_v0_jax.py:195-220`).
- Recompute:
  - `H2((1+0.7)/2) = H2(0.85) = 0.4227090878059909`.
  - Six-state Holevo: `ln(2) - (2/3)H2(0.85) = 0.411341122022618`.
  - Information killed: `ln(2) - 0.411341122022618 = 0.28180605853732726`.
  - Dephasing quantum capacity: `ln(2) + 0.15 ln(0.15) + 0.85 ln(0.85) = 0.2704380927539544`.
- These match `D_z` / `D_x` envelope rows (`results/manifold_information_throughput_v0_envelope_results.json:613-668`).

The unitary anchors are exact:

- `R_x` and `R_z` are labeled `lossless_unitary_exact`; classical and quantum capacities are `ln(2)`, six-state Holevo is `ln(2)`, and killed information is `0` (`manifold_information_throughput_v0_jax.py:221-232`; envelope `R_x/R_z` rows).
- Julia QuantumOptics agrees with Python on all four S4 six-state rows with `max_divergence = 0.0` (`results/manifold_information_throughput_v0_envelope_results.json:136-145`).

The S5 terrain rows are honestly labeled:

- `Ne_*`: `lossless_unitary_exact`.
- `Si_*`: dephasing-like rows with exact dephasing-axis capacity, up to unitary rotation.
- `Se_*`: `classical_covariant_exact_quantum_bound_only`; quantum capacity is not claimed exact.
- `Ni_*`: `certified_bounds_only`; classical capacity is a pinned-six-state lower bound with `ln(2)` upper bound, and coherent information is a maximally mixed lower bound (`manifold_information_throughput_v0_jax.py:252-316`; envelope S5 rows).

Named caveat:

`CAVEAT_CAPACITY_EXACTNESS_PER_ROW_ONLY`. Exact capacity is earned only for unitary/dephasing-class rows and the covariant classical rows explicitly labeled that way. There is no all-affine terrain capacity theorem.

## Q3 - stage-word curve and 720 row

Verdict: `PASS`.

The source composes the committed eight-stage word over the pinned six-state ensemble (`manifold_information_throughput_v0_jax.py:325-381`):

```text
D_z, R_z, D_z, R_z, D_x, R_x, D_x, R_x
```

Per-stage unitarity split is channel-derived, not stage-name-derived:

- `R_*` rows preserve the current pinned-ensemble information.
- `D_*` rows destroy off-axis information.

Independent recomputation matched the emitted curve:

```text
stage 1 output 0.411341122022618, delta 0.28180605853732726
stage 2 output 0.411341122022618, delta 0.0
stage 3 output 0.31463929237730087, delta 0.09670182964531715
stage 4 output 0.31463929237730087, delta 0.0
stage 5 output 0.1519531185317815, delta 0.16268617384551937
stage 6 output 0.1519531185317815, delta 0.0
stage 7 output 0.0932927444282512, delta 0.05866037410353031
stage 8 output 0.0932927444282512, delta 0.0
```

The 720 row is split correctly:

- Density-channel double traversal: `output_information_nats = 0.019959213845365253`, `destroyed_from_initial_nats = 0.67318796671458`.
- Spinor-lift record: sign record processes `ln(2)`, while density-accessible sign information is `0.0`; this is a cited parent anchor plus fresh information-account row, not a fresh spinor-lift rebuild inside this packet (`manifold_information_throughput_v0_jax.py:368-380`; envelope `stage_word_throughput.double_traversal_720_*`).

Named caveat:

`CAVEAT_720_SPINOR_ROW_PARENT_ANCHOR`. The density 720 value is recomputed by reapplying the eight-stage density channel. The spinor sign-record row is anchored in `engine_readout_spinor_lift_v0` and accounted here as throughput, not reconstructed from scratch here.

## Q4 - type discipline and no-primitive framing

Verdict: `PASS_WITH_EXPLICIT_Q1_TYPE_CAVEAT`.

Type evidence:

- Build card states all entropy and information units are natural nats, exact capacities are row-scoped, general affine terrain rows are bounds, and entropy rows are readouts, not primitive doctrine (`build_card.md:31-38`).
- Parent entropy type table separates:
  - measure differential entropy;
  - mixed differential plus discrete Shannon for conditioning bands/unions;
  - von Neumann entropy for carrier rows;
  - lattice/counting entropy for terrain restrictions (`manifold_entropy_ledger_v0_envelope_results.json:533-556`).
- Parent chain-rule check is exact zero: `h(S^3)=h(eta)+E[h(T_eta)]`, `defect_exact = 0` (`manifold_entropy_ledger_v0_envelope_results.json:673-678`).
- Parent controls include wrong log base, wrong eta marginal, wrong lens group order, and SMT erased conditional checks.

Target entropy/information object types:

- S4/S5 `six_state.holevo_nats`: Holevo information on the pinned uniform six-state Pauli ensemble.
- S4/S5 `information_killed_from_identity_nats`: pinned-ensemble loss relative to identity.
- Dephasing/unitary capacity rows: channel capacity formulas in nats; exactness only where row class earns it.
- Coherent-information rows: maximally mixed coherent-information lower bounds for non-exact terrain rows.
- Ratchet finite quotient rows: finite quotient coefficient/account rows in nats.
- Compression-flow anchor: finite set / quotient-class record rows from the parent compression packet.
- 720 density row: density-channel pinned-ensemble Holevo after double traversal.
- 720 spinor row: sign-record throughput from the spinor-lift parent, accounted in nats.

No primitive-framing violation found:

- Grep hits for `entropy as primitive` occur only in blocked claims (`manifold_information_throughput_v0_envelope.py:76-81`; result blocked claims).
- No `universal information scalar`, `master variable`, or `entropy-as-master` promotion wording was found in the target packet.

Named caveat:

`CAVEAT_Q1_RECORD_TYPE_NEEDS_PRODUCT_CONVENTION`. The Q1 conservation row combines a quotient-state loss coefficient with an inferred record coefficient. It is admissible only as an explicitly extended state-plus-record product account. It must not be read as a universal entropy scalar or as a cross-type sum outside that convention.

## Q5 - standard/process checks

Verdict: `PASS_WITH_PROCESS_CAVEATS`.

Passes:

- Packet validator passed with the Makefile sim-stack interpreter.
- `validate_three_engine_sim_result.py --require-source-backed` passed.
- Build card exists and states ceiling, scope, parent lineage, computation contract, and expected artifacts (`build_card.md:1-52`).
- Julia leg is real and load-bearing for S4 throughput: `QuantumOptics.SpinBasis`, `QuantumOptics.dm`, `QuantumOptics.DenseOperator`, and `QuantumOptics.entropy_vn` are used in source (`manifold_information_throughput_v0_julia.jl:40-74`, `:153-182`).
- SMT rows have erased flips:
  - z3 real `unsat`, erased `sat`;
  - cvc5 real `unsat`, erased `sat`;
  - Julia Z3 real `unsat`, erased `sat`.
- Parent lineage is hash-bound to committed `HEAD:<path>` blobs; owner `a54224476` is retained as context but the local blob pins are authoritative (`manifold_information_throughput_v0_jax.py:77-92`; envelope parent lineage).
- Capability receipts and one-to-one tool calls exist for `sympy`, `z3`, `cvc5`, `QuantumOptics`, and Julia `Z3`.
- Target packet grep found no literal `fixture` wording; validator blocks fixture/audit-verdict wording in the result surface (`validate_manifold_information_throughput_v0.py:58-60`).
- JAX result records deterministic symbolic seed: `manifold_information_throughput_v0:20260611:light-symbolic`.

Process caveats:

1. `CAVEAT_ENVELOPE_HELPER_NOT_USED`: the standard helper `scripts/build_three_engine_envelope.py` exists, but this packet's envelope is hand-rolled in `manifold_information_throughput_v0_envelope.py`. The shape validator accepts it, so this is process drift, not a numeric failure.
2. `CAVEAT_SEED_NOT_TOP_LEVEL`: the JAX leg has a deterministic symbolic seed, but the envelope top level and Julia leg do not carry a seed field.
3. `CAVEAT_TWO_LANE_NOT_FULL_THREE_ENGINE`: the envelope schema is `three_engine_sim_result_v1`, but the engine contract is `julia_canon_plus_jax_diagnostic`; PyTorch is explicitly excluded as not scoped.
4. `CAVEAT_UNTRACKED_PACKET`: the whole target packet is currently untracked working-tree state. This verdict does not imply committed repo truth.
5. `CAVEAT_MAX_ASSEMBLY_PARTIAL`: this audit used controller recomputation plus three Codex parent audit lanes. It did not run the full v4.2 nine-parent/child topology or nested child subsubagents.

## Q6 - closure

Earned:

- A typed throughput table over committed S4/S5 channels, the eight-stage density word, the 720 density/spinor split, and finite ratchet quotient accounts.
- Exact dephasing/unitary capacity rows where the channel class earns exactness.
- Pinned-ensemble Holevo and information-killed rows for the stated channels.
- Honest coherent-information lower-bound labeling for non-exact terrain rows.
- A first computed quotient-order conservation account for finite quotient rows: state loss `ln(4)` plus inferred retained-record coefficient `ln(4)` gives extended defect `0.0`.
- Real Julia QuantumOptics S4 crosscheck and real z3/cvc5/Julia-Z3 erased flips.

Not earned:

- No universal information scalar.
- No entropy-as-primitive or entropy-as-master-variable result.
- No formal admission, canonical theorem, bridge, axis, physics, or manifold-completion claim.
- No all-affine terrain capacity theorem.
- No packet-local construction of a Z4 syndrome/preimage record table. The radiated-record framing is supported at the quotient-step/account level only, with parent-anchor support from compression-flow record construction.

## Verdict

VERDICT: `ACCEPTED_AS_SCRATCH_DIAGNOSTIC_WITH_HARD_Q1_CAVEAT`.

The packet is genuine enough to keep as a typed information-throughput scratch diagnostic. The capacity rows, stage-word curve, 720 split, type discipline, tool receipts, Julia leg, SMT erased flips, lineage, and validator checks pass at the stated ceiling.

The headline conservation row must be worded carefully: it is a computed quotient-order conservation account, not proof of a packet-local radiated-record object. The safe closure is:

> Z4 quotient state loss is `ln(4)` and an inferred Z4 syndrome-record coefficient has capacity `ln(4)`, so the extended state-plus-record coefficient account has defect `0.0`; the target packet does not independently construct the Z4 record object beyond quotient order plus parent record anchoring.

Ceiling restated:

`classification=scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`. The owner vocabulary remains interpretation over the computed account. The radiated-record framing is supported only at the quotient-step level here; no universal information scalar, no entropy primitive, no canonical manifold theorem, no bridge/axis/physics claim.
