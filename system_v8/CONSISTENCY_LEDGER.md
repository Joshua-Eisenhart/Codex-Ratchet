# Cross-receipt consistency ledger — system_v8

Read-only sweep. Enumerated every `*receipt*.json` under `system_v8/` (find, sorted, 132 files
including 36 `unified/` per-layer receipts). For each quantity named in the task plus quantities
surfaced while scanning, every receipt+value is listed. No receipt was edited.

Status key: CONSISTENT (same quantity, matching value across receipts) / DIVERGENT (same quantity,
different value, not explained by different config) / INCOMPARABLE (different run config — noted
why) / TAINTED-SOURCE (value comes from a receipt already known-tainted per prior owner findings —
divergence expected, not re-litigated).

## 1. Chirality flux split (radians)

| Receipt | Value | Note |
|---|---|---|
| `deep_integration/results/full_sim/receipt.json` (`data.flux.split`, final tick) | 1.7642652937935317 | `checks.C3_erase_chirality_split_dies = True`, `checks.flux_opposite_sign_every_cycle = True` |
| `deep_integration/results/full_sim_run1_receipt_order_flux_negative/receipt.json` | same series (order-negative variant of full_sim) | negative-control sibling, not re-litigated here |
| `schedule_tournament/results/schedule_tournament_v0/receipt.json` (`flux_split`) | 2.498001805406602e-16, and 0.0 repeated across other rows | degenerate — flat/zero split |

**Verdict: DIVERGENT.** 1.76 rad (full_sim) vs ~2.5e-16 / 0.0 (schedule_tournament) — a
13-order-of-magnitude gap on a quantity both receipts name `flux_split`/`split` on the same
chirality-flux construction. This is the pair named in the task as the one that caught the
schedule-tournament apparatus failure; flagging it here, not re-litigating the root cause.

## 2. S_master (entropy at gamma*, engine-estate integration)

| Receipt | Value |
|---|---|
| `engine_estate/results/integration/handoff_julia.json` (`S_master`) | 4.7995040632334325 |
| `engine_estate/results/integration/receipt.json` (`S_master_julia`) | 4.7995040632334325 |
| `engine_estate/results/integration/receipt.json` (`S_control`, `S_control_numpy`) | 4.799504063233417 |
| `engine_estate/results/integration/handoff_jax.json` (`S_at_gamma_star`) | 4.799504063233417 |
| `engine_estate/results/integration/handoff_julia.json` (`S_dev_vs_jax`) | 1.509903313490213e-14 |

**Verdict: CONSISTENT.** Julia value and JAX/numpy control value agree to ~1.5e-14 (the receipt's
own `S_dev_vs_jax` states the cross-engine delta). Matches the task's cited anchor
`4.799504063233`.

## 3. Chance / baseline accuracy 0.4956

| Receipt | Value (`computed_chance_accuracy`) |
|---|---|
| `loop3_senses/results/carrier_tournament_v1/receipt.json` | 0.4956268221574344 |
| `loop3_senses/results/senses_v2_slow_memory/receipt.json` | 0.4956268221574344 |
| `loop3_senses/results/loop2_retest_fixed_senses/receipt.json` | 0.4956268221574344 |
| `loop2_world/results/intelligence/receipt.json` (prose line) | "computed baseline 0.4956" |

**Verdict: CONSISTENT.** Exact match to 13 significant figures across all three JSON receipts;
loop2_world's prose summary rounds to the same value.

## 4. Occluded accuracy 0.8776 (Bayes-filter ceiling anchor)

| Receipt | Value |
|---|---|
| `loop3_senses/results/carrier_tournament_v1/receipt.json` (`estimate`, 5 occurrences) | 0.8775510204081632 |
| `loop3_senses/results/carrier_tournament_v1/receipt.json` (prose) | "senses_v2_anchor: occluded accuracy 0.8776" |
| `loop3_senses/results/senses_v2_slow_memory/receipt.json` (`occluded_accuracy`, `estimate`) | 0.8775510204081632 |
| `loop3_senses/results/senses_v2_slow_memory/receipt.json` (prose) | "Slow-memory occluded accuracy 0.8776" |
| `loop2_world/results/intelligence/receipt.json` (`acc`) | 0.8775510204081632 |
| `loop2_world/results/intelligence/receipt.json` (prose) | "Bayes-filter ceiling 0.8776" |

**Verdict: CONSISTENT.** Same 343-test-slot ceiling value carried through senses_v2 → carrier
tournament → loop2 intelligence, exact to 16 s.f.

## 5. Hartley capacity ~2^166

| Receipt | Value |
|---|---|
| `deep_integration/results/full_sim/receipt.json` (prose) | "60-tick chained big-int count = 111697137929291483880703182306362004825162274308096 (~2^166.256); cumulative Hartley capacity 166.255997 bits; exact match gate passed = True" |
| `deep_integration/results/full_sim_run1_receipt_order_flux_negative/receipt.json` | identical string |

**Verdict: CONSISTENT** (matches task's `2^166` anchor). Both receipts are the same sim family
(order-negative control shares the base capacity computation), so this is expected agreement, not
an independent cross-check.

## 6. Coherent information, nested-cut ladder (L11 / entanglement_gradient)

| Receipt | Value(s) |
|---|---|
| `entanglement_gradient/results/coherent_information_ladder_v0/receipt.json` (`qutip_cut2_SAB` / `torch_cut2_SAB`, per-tick series) | 1.0121, ..., 1.7882, ..., 1.9685 (qutip and torch agree exactly at each shared tick) |
| `unified/results/manifold_unified_v2/layers/L11/receipt.json` (`coherent_information_bits`, repeated 4x per config) | 1.9128440131119842 / 1.9128440131119848, 1.8635526670215554 / ...576, 1.9310738327124286 / ...264, 1.819584863029506 / ...5066 |
| `unified/results/manifold_unified_v2/receipt.json` (rolled up from L11) | same 4 values |

**Verdict: INCOMPARABLE at the exact-value level, CONSISTENT at the engine-agreement level.**
`entanglement_gradient` reports its own qutip/torch pair agreeing internally (no numeric overlap
with L11's specific values — different cut construction, not the same run). Within
`unified/.../L11`, torch and qutip (or whichever second engine backs the `...848` vs `...842`
pair) agree to ~1e-15 on all four listed values — consistent with the task's cited anchor "1.91
bits L11" (1.9128440131119842/48 rounds to 1.91). The 4 distinct values (1.86–1.93) are 4 different
sub-configs within L11, not 4 disagreeing measurements of one quantity — flagged INCOMPARABLE
across sub-configs, CONSISTENT within each engine pair.

## 7. qutip cross-engine agreement deltas (deep_integration/qit_referee)

| Receipt | Field | Value |
|---|---|---|
| `deep_integration/results/qit_referee/receipt.json` | `A_max_step_increase_qutip` | -0.0003635713029760401 |
| same | `A_nullspace_dim_qutip` | 1 |
| same | `A_rho_ss_min_eig_qutip` | 0.008890821517515636 |
| same | `D_max_step_increase_qutip` | -6.008890920394805e-07 |
| same | `U_max_dS_qutip` | 5.2871929057118905e-11 |

**Verdict: single-source, no cross-receipt duplicate found.** No other receipt under
`system_v8/` carries these exact qutip-referee field names or values — searched
`tool_ledger/battery_batch1-4`, `histories_referee/mcwf_referee_v0`, `axis0_front/r1`. Listed here
because it's the only qutip-agreement quantity block in the estate; nothing to compare it against,
so it cannot be marked CONSISTENT or DIVERGENT — INCOMPARABLE (no second receipt uses this
quantity).

## 8. Torch/nested-manifold flux family (context, not a task-named anchor but recurring)

`flux` (nested_manifold/manifold_one) = 0.3450351997992214 — single occurrence, no duplicate.
`flux_left`/`flux_right`/`telescoped_flux` (nested_manifold/rungA) = ∓2.9025821900968336 —
single occurrence, no duplicate. `flux` series in `unified/manifold_unified_v1` and
`unified/manifold_unified_v2` (33-tick series, -1.82 to -2.36) match each other value-for-value
between v1 and v2 layer-rollup receipts (v1 and v2 are declared-related runs — expected
agreement, not independent).

**Verdict: CONSISTENT** between v1/v2 (same run family); **INCOMPARABLE** against
`nested_manifold` flux values (different sim/apparatus, no shared config).

## Known-tainted sources (not re-litigated)

- `unified/results/manifold_unified_v1/**` and its 18 per-layer receipts — flagged tainted per
  prior owner record. Values pulled above (flux series, capacity_drive) are reproduced for the
  ledger but any divergence involving v1 should be read through that taint, not treated as a fresh
  finding.
- `nested_manifold/results/stage64/receipt.json` — flagged tainted per prior owner record; not
  used as a comparison anchor above.

## Divergent rows (summary, for the calling report)

1. **Chirality flux split**: `deep_integration/results/full_sim/receipt.json` = 1.7643 rad vs
   `schedule_tournament/results/schedule_tournament_v0/receipt.json` = 2.5e-16 / 0.0 — the known
   schedule-tournament apparatus failure, confirmed present in the current receipt set.

No other DIVERGENT rows found among the quantities checked (S_master, chance 0.4956, occluded
accuracy 0.8776, Hartley capacity 2^166, L11 coherent information engine-pairs) — all CONSISTENT
or INCOMPARABLE-by-config.
