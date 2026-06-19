# Fresh audit verdict - ecd01_order_programmable_computer_v0

Bottom line: `BY_CONSTRUCTION` as the ECD.01 Szilard-vs-QIT capability discriminator. The QIT/order-programmability witness is real at scratch strength: the same Axis-4 carrier computes three distinct label-free order-channel outputs, all three backend lanes agree, and the commuting/order-erased control collapses. But the Szilard baseline failure is not a fully computed strongest-form baseline: the packet source sets `distinct = 1` for the plain single-loop baseline and derives `fails_ecd01` from `1 < qit_distinct_count`, rather than computing a baseline channel table over all admissible strongest-form Szilard schedules. Therefore do not cite this packet as an earned ECD.01 capability discriminator pass.

Verdict: `BY_CONSTRUCTION`

Claim ceiling: `scratch_diagnostic`; more specifically, "same-carrier Axis-4 order-programmability witness only." `promotion_allowed=false`; `formal_admission_allowed=false`; no QIT-engine admission, no 64-stage engine claim, no physics, no consciousness/AGI, no bridge/manifold/axis closure.

Citation rule: This packet may be cited only as: "fresh-audited scratch diagnostic: registered Axis-4 order words `UEUE`, `UUEE`, and `UEEU` compute three distinct label-free channel outputs on the 33-state carrier, with pairwise distances 5.61, 5.61, and 11.22 and a commuting-generator collapse control." It must not be cited as "Szilard baseline fairly defeated," "ECD.01 passed," "QIT engine capability earned," "universal/Turing computer," or any physics/consciousness/bridge result.

## Audit Scope

Freshness tier: `TIER-2` results-available audit. I read the source, result JSONs, registry, standards, and build card before writing this verdict, and I reran validators in a scratch clone to preserve the live checkout read-only boundary.

Write scope: this file only, `system_v6/sims/ecd01_order_programmable_computer_v0/audit_verdict.md`.

Authority surfaces:

- ECD registry: `system_v6/receipts/engine_capability_differentiators_20260612.md`, pinned in packet source as `7c3f4b48d`.
- Standards: `system_v6/receipts/audit_standards_codex_v1.md`.
- Build card: `system_v6/sims/ecd01_order_programmable_computer_v0/build_card.md`.

Important live-state caveat: the whole `ecd01_order_programmable_computer_v0/` packet is currently untracked in git. That does not invalidate the local audit, but it means citations must name this as working-tree scratch evidence until the packet is committed or otherwise receipted.

## Fresh Validator Runs

To avoid writing generated result JSONs in the live checkout, I copied the repo to `/tmp/ecd01_audit.Gtx5ka/Codex-Ratchet` and reran the packet there.

Commands run fresh in scratch:

```text
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/ecd01_order_programmable_computer_v0/ecd01_order_programmable_computer_v0_jax.py
JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=/tmp/ecd01_audit.Gtx5ka/Codex-Ratchet/system_v5/julia_carrier system_v6/sims/ecd01_order_programmable_computer_v0/ecd01_order_programmable_computer_v0_julia.jl
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/ecd01_order_programmable_computer_v0/ecd01_order_programmable_computer_v0_pytorch.py
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/ecd01_order_programmable_computer_v0/ecd01_order_programmable_computer_v0_envelope.py
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/ecd01_order_programmable_computer_v0/validate_ecd01_order_programmable_computer_v0.py
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed --require-tool-intent system_v6/sims/ecd01_order_programmable_computer_v0/results/ecd01_order_programmable_computer_v0_envelope_results.json
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest system_v6/sims/ecd01_order_programmable_computer_v0/tests
```

Fresh results:

- JAX lane: `all_pass=true`.
- Julia lane: `all_pass=true`.
- PyTorch lane: `all_pass=true`.
- Envelope: `all_pass=true`.
- Packet-local validator: `ok=true`, `errors=[]`.
- Generic three-engine validator with PyTorch, strict source backing, and tool intent: `ok=true`.
- Pytest: `3 passed`.

Scratch/live consistency: the scratch envelope and live envelope match on `all_pass`, `capability_metric`, `channel_hash_classes`, `channel_distinguishability_matrix`, `controls`, `szilard_baseline`, `smt_rows`, `divergence`, and engine summaries.

Post-audit idempotency caveat: the packet-local validator currently contains a hard pre-audit assertion that `audit_verdict.md` must not exist. That was valid before this audit file was written. After this file exists, the packet-local validator will need a post-audit idempotency repair if it is expected to pass in-place.

## Independent Recomputations

I recomputed load-bearing values from the Axis-4 source pins and carrier, not from the builder's reported metric:

```text
axis4_state_count = 33
qit_distinct_channel_count = 3
qit_pairwise_distances:
  UEUE->UUEE = 5.61
  UEUE->UEEU = 5.61
  UUEE->UEEU = 11.22
commuting_control_distinct_count = 1
szilard_admissible_order_count = 1
szilard_admissible_orders = [('measure', 'feedback', 'erase')]
szilard_invalid_order_count = 5
commutator_nonzero_entries =
  [[0.0, 0.0, 0.0],
   [0.0, 0.0, -0.3],
   [0.0, -0.3, 0.0]]
```

These agree with the live envelope's QIT channel diversity, pairwise matrix, and commuting collapse.

## Teeth Findings

1. Szilard baseline fairness: not fully satisfied. The registry defines the plain Szilard baseline as one measurement-memory-feedback-erasure loop without independent D/I loops, 64-slot schedule, chirality, prediction-first objective, or external oracle. Under that definition, the baseline is not a strawman. However, this packet does not compute a strongest-form baseline channel table. In `ecd01_order_programmable_computer_v0_common.py`, `szilard_baseline_result()` directly sets `distinct = 1` and reports failure by comparing that value to the QIT count. This makes the discriminator pass depend on the registry boundary, not on a computed adversarial baseline. That is the reason for `BY_CONSTRUCTION`.

2. Order-programmability witness: satisfied at scratch strength. The packet computes three registered same-carrier order words, hashes label-free output multisets, and computes pairwise L1 output distances. The QIT witness is not just row naming: independent recomputation gives three distinct output multisets and all three pairwise distances are positive.

3. Order-blind control: satisfied. Replacing `E` with `U` collapses the three registered words to one output class. The shuffled-label control preserves diversity and distance multiset, so the witness is not merely spelling order labels back.

4. Identity leak: no load-bearing identity leak found for the QIT readout. The result is keyed by `order_word`, but the pass metric uses label-free output multisets and output distances. The readout hash is computed from sorted outputs over carrier cells, not from the word string. The program encoding necessarily drives the channel computation; that is intended, not a readout leak.

5. Discriminator honesty: partially satisfied. The packet's allowed/disallowed claims and result ceiling are honest, and validators are green. But the field `would_die_if_szilard_distinct_count_gte_qit` is hardcoded with `or True`; this is not load-bearing for the actual metric or SMT rows, but it is a validator weakness and should not be cited as evidence that the baseline positive predicate was genuinely implemented.

6. Fences and labels: satisfied. Result labels are `classification="scratch_diagnostic"`, `promotion_allowed=false`, `formal_admission_allowed=false`, and `claim_ceiling="capability_discriminator_only"`. The packet explicitly disallows universal/Turing computer, QIT-engine admission, canonical Axis-4 identity, physics claim, and bridge admission.

## Circularity Species

- `frozen-factor echo`: not found. No frozen complementary-factor count is promoted as moving-object structure.
- `definitional circularity`: present for the Szilard baseline failure. The baseline distinct count is fixed as `1`; the actual QIT channel diversity is computed, but the baseline fail is not a computed strongest-form adversary.
- `rule-table readback`: not found for the QIT channel witness. The channel hashes and distances are computed from realized matrices on carrier cells, not read from the registry table.
- `post-hoc statistic`: not found. The order words are registered/pinned before the run; no observed-positive target set is selected after inspection.
- `shift-relabeling`: not found. The shuffled-label control preserves the distance multiset, and the commuting control changes the actual output class count.
- `structure-by-symmetry`: not found for the claimed QIT order witness. The packet does not infer structure from a 64/symmetry label; it computes three finite channel rows. Do not extend this to a full 64-stage schedule.

## Final Classification

Accepted evidence:

- computed same-carrier QIT order-channel diversity on the Axis-4 fixture;
- three-backend agreement on the registered order hashes;
- commuting generator collapse control;
- z3/cvc5 integer bindings for the computed diversity inequality with erased flips.

Rejected stronger claim:

- fair, strongest-form, computed Szilard-vs-QIT ECD.01 capability discriminator pass.

Required next repair:

Build a real Szilard baseline table over the same carrier: enumerate every admissible strongest-form plain Szilard stroke schedule, compute its label-free channel/readout outputs under the same fingerprint family, include a positive predicate that could admit a stronger baseline if it matches or exceeds QIT diversity, and rerun the discriminator. Only then can this move from `BY_CONSTRUCTION` toward `GENUINE-WITH-CAVEATS` or `GENUINE`.
