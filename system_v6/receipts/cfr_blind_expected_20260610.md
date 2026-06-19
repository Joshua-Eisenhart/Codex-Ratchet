# BLIND expected-values: compression_flow_radiated_record_v0

Lane: BLIND expected-values. I did not read, list, or glob the appearing build directory. Inputs used: `/tmp/cfr_build_card_20260610.md`, its cited read-first sources, and committed `system_v6/sims/mct_dynamic_admissibility_packet_v0/results/`.

Ceiling: these are predictions from the build card PIN and committed carrier numbers only. Exact values that depend on the builder's three predicate choices are marked `depends_on_builder_pin`.

Carrier facts used:

- `support_size = 384`.
- `carrier_lineage pin_block_sha256 = f64f2c3624658fb522c8e5363ae2bb1a38b2a626d9da5e283ef05025a0e13161`.
- `support_table_hash = 5727f366d2e4081549095d62741e25179aa6e561042617ba70970173b74bc2a8`.
- density-only quotient: `12` classes of size `32` over `384`.
- sheet-refined quotient without phase: `24` classes of size `16` over `384`.
- committed envelope/legs report `q_without_phase = 24`, `q_with_phase = 192`, `classification = scratch_diagnostic`, `promotion_allowed = false`, `formal_admission_allowed = false`.

PIN/source lines:

- Build card claim and ceiling: `/tmp/cfr_build_card_20260610.md:3-14`.
- Build card read-first and carrier reuse: `/tmp/cfr_build_card_20260610.md:16-21`.
- Build card PIN: `/tmp/cfr_build_card_20260610.md:23-28`.
- Gates G1-G8: `/tmp/cfr_build_card_20260610.md:30-38`.
- Controls and acceptance: `/tmp/cfr_build_card_20260610.md:40-54`.
- v6 ceiling/evidence rules: `system_v6/README.md:5-13`, `system_v6/README.md:51-65`.
- Candidate math not on file: `system_v6/receipts/shell_flow_radiated_information_mine_20260610.md:160-175`, `:180-226`.
- Existing carrier object map: `system_v6/receipts/shell_flow_radiated_information_mine_20260610.md:228-270`.
- Compression/readout discipline: `/Users/joshuaeisenhart/wiki/concepts/field-wide-compression-probe-contract.md:123-163`, `:165-232`.
- M(C,t) killed-information / quotient discipline: `system_v6/receipts/mct_reconciled_spec_20260609.md:60-75`, `:77-99`.
- MCT carrier build card PIN and gates: `system_v6/sims/mct_dynamic_admissibility_packet_v0/build_card.md:23-42`, `:44-63`.

## 1. Ledger arithmetic shape

Prediction:

For each step `t`, if the step is implemented as:

```text
Delta R_t = {x in P_t : c_t(x) excludes x}
P_{t+1} = P_t \ Delta R_t
```

then the exact identity is:

```text
|P_t| = |P_{t+1}| + |Delta R_t|
```

because `P_{t+1}` and `Delta R_t` are disjoint and partition `P_t`.

Under the prompt's terminal-label convention:

```text
|P_0| = |P_2| + sum_t |Delta R_t| = 384
```

More generally, if the builder treats the three predicates `c_0,c_1,c_2` as three transitions, the terminal set would usually be labeled `P_3`, giving:

```text
|P_0| = |P_3| + |Delta R_0| + |Delta R_1| + |Delta R_2| = 384
```

The arithmetic is invariant to that label choice; the receipt must make the terminal index explicit.

Predictable before builder pin:

- `|P_0| = 384`.
- Every valid nontrivial step has `1 <= |Delta R_t| <= |P_t|-1`.
- If every predicate is nonempty proper on the current live set, all intermediate survivor sets are nonempty.
- Telescoping total emitted rows is `384 - |P_terminal|`.

Not predictable before builder pin:

- Exact `|Delta R_t|` values.
- Exact `|P_t|` trajectory.
- Whether the three predicates overlap on the original carrier.
- Whether a shuffled step-tag test has a strong effect.

Derivation sketch: the card defines survivors as advancing inward and excluded samples as emitted `Delta R_t`; conservation is a required gate. This is finite-set partition arithmetic, not a standing doctrine result.

PIN/source line: `/tmp/cfr_build_card_20260610.md:23-28`, `:30-38`; candidate-math status from `system_v6/receipts/shell_flow_radiated_information_mine_20260610.md:160-175`.

## 2. Raw-record reconstruction

Prediction:

Raw set-equality reconstruction should succeed by construction:

```text
reconstructed_P0 = P_terminal union Delta R_0 union Delta R_1 union Delta R_2
mismatch_count = 0
```

provided every emitted raw row is recorded and the terminal live set is raw-row identified.

The non-trivial content therefore cannot be the raw union itself. It must live in:

- the uniqueness proof over the computed record and terminal set;
- the quotient-mode failure;
- the erasure/lossy controls;
- the injected conservation violation catch;
- the order/shuffle control where overlap makes order observable.

Expected SMT shape:

```text
raw mode:
  assert P_0' consistent with P_terminal and full raw record
  assert P_0' != P_0
  verdict: UNSAT in z3 and cvc5

dropped-rows control:
  drop at least one emitted raw row from the record
  assert P_0' consistent with weakened record and P_0' != P_0
  verdict: SAT, model exhibits an omitted row choice
```

Minimum dropped-record fraction for SAT:

```text
1 / |R_total|
```

where:

```text
|R_total| = sum_t |Delta R_t| = 384 - |P_terminal|
```

This is `depends_on_builder_pin`. Reason: the full raw record must cover every row in `P_0 \ P_terminal`; dropping one emitted row leaves at least one uncovered raw row and admits a different candidate initial set under the weakened observation. If the solver additionally enforces fixed total cardinality by drawing replacements from the carrier complement, the same one-row drop is still the minimum ambiguity trigger as long as a replacement or omission model is allowed by the encoded consistency relation. The build should report the exact fraction after the predicates pin `|R_total|`.

PIN/source line: raw reconstruction and solver gates from `/tmp/cfr_build_card_20260610.md:30-38`; controls from `:40-41`; no-free-invertibility counterweight from `system_v6/receipts/shell_flow_radiated_information_mine_20260610.md:146-158`, `:198-218`.

## 3. Quotient-mode mismatch scale

Prediction:

If the emitted record carries only quotient class IDs, raw-row reconstruction is underdetermined inside each class. For a quotient partition with class capacities `n_i`, emitted count vector `m_i`, and known terminal raw survivors `l_i`, the number of raw emitted sets consistent with the class-ID record is:

```text
N_consistent = product_i binom(n_i - l_i, m_i)
```

If the ambiguity calculation ignores terminal survivor identities and counts only the class-ID record against the full carrier class capacities, the upper/count-vector form is:

```text
N_consistent_record_only = product_i binom(n_i, m_i)
```

Committed carrier evaluations:

Density-only record, `12` classes of size `32`:

```text
N_density = product_{i=1}^{12} binom(32 - l_i, m_i)
record-only upper/count-vector form = product_{i=1}^{12} binom(32, m_i)
```

Sheet-refined class record, `24` classes of size `16`:

```text
N_sheet = product_{i=1}^{24} binom(16 - l_i, m_i)
record-only upper/count-vector form = product_{i=1}^{24} binom(16, m_i)
```

Exact quotient-mode mismatch count is `depends_on_builder_pin` because `m_i` and `l_i` come from the chosen predicates and terminal set.

Scale examples from committed class sizes:

- If one emitted row is recorded in each density-only class and no terminal survivor is subtracted in the ambiguity factor: `32^12 = 2^60 = 1152921504606846976` possible raw emitted sets.
- If one emitted row is recorded in each sheet-refined class: `16^24 = 2^96 = 79228162514264337593543950336` possible raw emitted sets.
- If half of every density-only class is emitted: `binom(32,16)^12`, about `2^349.9558` possibilities.
- If half of every sheet-refined class is emitted: `binom(16,8)^24`, about `2^327.6414` possibilities.

Expected verdict:

- quotient-level reconstruction succeeds;
- raw reconstruction fails unless every involved quotient class has ambiguity factor `1`;
- the killed-information ledger is the gap between raw uniqueness and quotient consistency.

PIN/source line: quotient record mode from `/tmp/cfr_build_card_20260610.md:23-28`, quotient failure gate from `:34-35`; committed quotient behavior from `system_v6/receipts/shell_flow_radiated_information_mine_20260610.md:246-250`; quotient/killed-information discipline from `system_v6/receipts/mct_reconciled_spec_20260609.md:64-75`, `:93-99`.

## 4. Erasure baseline

Prediction:

For a register that holds emitted rows for a step and is reset/erased at the boundary, the erasure cost depends on the number of distinguishable possible register states. If the step emits exactly `r_t = |Delta R_t|` raw rows from the finite carrier and the reset erases their row identities, then:

```text
bits_erased_t = log2 N_register_t
environment_charge_nats_t = ln(2) * bits_erased_t = ln N_register_t
```

For a simple row-ID register with one distinguishable state per emitted row:

```text
N_register_t = r_t
bits_erased_t = log2 |Delta R_t|
environment_charge_nats_t = ln |Delta R_t|
```

For an ordered/list register of all emitted raw rows, the builder must state the exact register state space. If the register state is the emitted set itself and only one computed set occurred, the thermodynamic baseline should instead charge the reset of the information-bearing memory distribution specified by the variant. The card specifically asks for `log2 |Delta R_t|` dependence for a register holding emitted rows, so the expected arithmetic is:

```text
Q_env_total_nats = sum_t ln(2) * log2 |Delta R_t|
                 = sum_t ln |Delta R_t|
```

This total is `depends_on_builder_pin` through `|Delta R_t|`.

Radiative variant:

```text
internal_erasure_charge = 0
ledger balance is carried by append-only record
```

Erasure baseline:

```text
internal reconstruction fails
books balance only after adding Q_env_total_nats
```

PIN/source line: erasure baseline and ln2 charge from `/tmp/cfr_build_card_20260610.md:27-28`, `:35-36`; Landauer-style existing bookkeeping source boundary from `system_v6/receipts/shell_flow_radiated_information_mine_20260610.md:272-298`.

## 5. Entropy ledger directions

Named object:

```text
H_live(t) = - sum_c p_t(c) ln p_t(c)
```

where `c` ranges over density-probe quotient classes and:

```text
p_t(c) = |P_t intersect class_c| / |P_t|
```

Computable in advance:

- Initial full-carrier density-only class distribution is uniform over `12` classes of size `32`, so:

```text
H_live(0) = ln(12) = 2.4849066497880004
```

- If the sheet row is included in the quotient family, the full-carrier initial distribution is uniform over `24` classes of size `16`, so:

```text
H_live_sheet(0) = ln(24) = 3.1780538303479458
```

- If phase is included as in the committed carrier's `q_with_phase = 192` with class size `2`, the full-carrier class entropy is:

```text
H_live_phase(0) = ln(192) = 5.2574953720277815
```

Predicate-dependent:

- `H_live(t>0)`.
- Whether `H_live` rises, falls, or stays flat as `P_t` shrinks.
- `H_record`, because record composition depends on which classes are excluded at each step.

Direction rule:

- If exclusions are class-balanced, `H_live` can remain unchanged while support shrinks.
- If exclusions concentrate in a few classes, `H_live` usually decreases.
- If exclusions remove overrepresented classes relative to the live distribution, `H_live` can increase.

Therefore the honest blind prediction is not monotone. The build must report the computed trajectory and name the object every time.

PIN/source line: entropy object names from `/tmp/cfr_build_card_20260610.md:27`; field-wide readout discipline from `/Users/joshuaeisenhart/wiki/concepts/field-wide-compression-probe-contract.md:211-232`; MCT entropy naming rule from `system_v6/sims/mct_dynamic_admissibility_packet_v0/build_card.md:33-42`.

## 6. Shuffle/order

Prediction:

Step-tag shuffling changes reconstruction only when the emitted rows and predicates make step order observable. Sufficient conditions for a strong order test:

- At least two predicates overlap on the original carrier, so a row could have been excluded at different first-hit steps depending on order.
- Later predicates are evaluated only on survivors, so first-hit step tags encode causal/order information.
- The record includes step tags and the reconstruction/proof checks tag consistency with the predicate sequence, not just the final raw union.

If the three predicates are disjoint in effect on the original carrier, shuffling step tags may leave the raw reconstructed set unchanged:

```text
P_terminal union unordered_record_rows = P_0
```

In that case the order test weakens. It may still catch tag/predicate inconsistency if the proof encodes "row emitted at step t iff c_t first excludes it", but plain set reconstruction will not change.

Card-level risk:

The builder must pin predicates with enough overlap or order-dependence for G7 to be load-bearing. If the pinned predicates are disjoint in effect, the receipt should report:

```text
record_shuffle_raw_set_changed = false
order_test_strength = weak_disjoint_effect
```

and rely on predicate/tag-consistency SMT or choose an overlap-bearing predicate set if the card requires a strong order result.

PIN/source line: order gate from `/tmp/cfr_build_card_20260610.md:37`; anti-order-collapse rule from the provided lane contract; MCT order/readout discipline from `system_v6/receipts/mct_reconciled_spec_20260609.md:55-58`, `:90-91`; readout time/shuffle contract from `/Users/joshuaeisenhart/wiki/concepts/field-wide-compression-probe-contract.md:223-230`.

## Blind acceptance checks to compare after build

- Ledger: every step has zero defect; telescoped terminal plus emitted total equals `384`.
- Raw mode: set mismatch `0`; z3 and cvc5 uniqueness verdicts `UNSAT`.
- Dropped raw-row control: `SAT` after at least one emitted row is dropped; minimum fraction should be `1 / (384 - |P_terminal|)`.
- Quotient mode: quotient reconstruction succeeds; raw reconstruction fails unless predicate choices accidentally make every ambiguity factor `1`.
- Quotient ambiguity formula: density-only `product binom(32 - l_i, m_i)` or sheet-refined `product binom(16 - l_i, m_i)`.
- Erasure baseline: charge reported as `sum_t ln(2) * log2 |Delta R_t| = sum_t ln |Delta R_t|` under the card's row-register convention.
- Entropy: `H_live(0)` should match `ln(12)` for density-only, `ln(24)` for sheet-refined, or `ln(192)` for phase-included; later values are predicate-dependent.
- Shuffle: strong only if predicates overlap/order-affect first-hit tags; weak if disjoint in effect.
