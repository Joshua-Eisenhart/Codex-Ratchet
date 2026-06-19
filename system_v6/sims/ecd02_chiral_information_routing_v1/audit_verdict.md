Independent audit verdict; read-only audit; independent recomputation.

Bottom line: VERDICT = CANDIDATE DEATH STANDS, bounded to this packet's carrier and readout. `ecd02_chiral_information_routing_v1` honestly kills ECD.02 as a Szilard-vs-QIT capability differentiator on the current QCA-v3 open-chain carrier: QIT computes `R=+1.0`, `L=-1.0`, `scrambled=0.0`, while the strongest same-alphabet one-step classical endpoint-policy search reaches `abs(current)=5.0`; therefore `registry_contract_pass=false` and `ecd02_status=DIES`.

Claim ceiling: `scratch_diagnostic`; `promotion_allowed=false`; `formal_admission_allowed=false`; `claim_ceiling=capability_discriminator_only`. This is not finite-ring QCA admission, all-cells QCA admission, physics chirality, axis closure, bridge/manifold evidence, or QIT-engine admission.

Freshness tier: TIER-2/TIER-3 mixed. I recomputed from source and result JSON in this turn, but the user prompt included builder claims and death context, so this is not blind.

Write scope honored: read-only except this file. No git add/commit.

## What Died

What died:

`ECD.02` as a capability differentiator on this carrier under the v1 fair-baseline contract. The registry contract says Szilard must fail computed and QIT must pass computed, or ECD.02 dies. The v1 result records QIT pass but strongest Szilard non-failure:

- QIT computed witness passes: `qit_engine_pass_computed=true`.
- Strongest Szilard baseline does not fail: `strongest_szilard_baseline_fail_computed=false`.
- Registry contract fails: `registry_contract_pass=false`.
- Candidate status: `ecd02_status=DIES`.

What did not die:

- The computed QIT L/R routing rows themselves. They remain real computed rows on this open-chain QCA-v3 fixture.
- The parent QCA-v3 fixture.
- The I Ching / axis / symbolic schedule structure.
- Any future stronger QIT configuration space not enumerated by this packet.
- Any finite-ring, all-cells, physics-chirality, bridge, manifold, or full QIT-engine claim, because none is admitted here.

## Recomputed Core Values

Fresh no-write recompute with the Makefile interpreter:

```text
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 - <<'PY'
from validate_ecd02_chiral_information_routing_v1 import validate
import ecd02_chiral_information_routing_v1_common as common
...
PY
```

Result:

```text
validator_errors = []
core_all_pass = true
computed_flux_by_engine = {"R_engine": 1.0, "L_engine": -1.0, "scrambled_schedule_control": 0.0}
qit_abs_directed_current = 1.0
strongest_szilard_abs_directed_current = 5.0
searched_policy_count = 36
same_alphabet_size = 6
same_step_budget = 1
registry_contract_pass = false
ecd02_status = "DIES"
```

Source/result anchors:

- QIT MI/current computation: `ecd02_chiral_information_routing_v1_common.py:124-219`.
- QIT selected rows: `ecd02_chiral_information_routing_v1_common.py:222-255`.
- Classical policy search: `ecd02_chiral_information_routing_v1_common.py:262-301`.
- Death logic: `ecd02_chiral_information_routing_v1_common.py:349-437`.
- Envelope values: `results/ecd02_chiral_information_routing_v1_envelope_results.json:176-180`, `:746-772`, `:832-837`.

## Reverse-Fairness Adjudication

The classical side did get a max-over-policy search. It enumerates all 36 deterministic endpoint-copy policies over `labels = range(6)`, computes `target_label - source_label`, and takes the best positive/negative policy. The best policies are `0 -> 5` and `5 -> 0`, both with `abs(current)=5.0`.

The QIT side in the packet did not run a global search over all future schedules, stage orders, axis settings, or possible QIT-engine configurations. The source selects only:

- `engine_R_flux_OUT_right_O1`
- `engine_L_flux_IN_left_O1`
- `calibration_nonshifting_onsite`

That would be unfair in reverse if the death were claimed as a global QIT impossibility.

I therefore ran an extra no-write QIT-side sweep over the available `ring_checkerboard_qca_v3.build_rules()` realized-rule family consumed by this packet. It covered 10 realized rules, including the L/R engines, gauge row, index-0 controls, calibrations, and the real-unitary falsifier branch. The maximum absolute average directed current over all available realized rules was:

```text
all_rule_count = 10
all_rules_max_abs_avg_current = 1.000000000000004
engine_like_count = 6
engine_like_max_abs_avg_current = 1.000000000000004
```

This gives the needed bounded carrier answer: within the packet's available QCA-v3 realized-rule carrier/readout family, the strongest QIT-side current is structurally one label-step up to floating tolerance. The death is not voided for this packet's carrier.

But this is not a theorem over every possible future QIT schedule, stage order, axis setting, full 64-stage engine, or all-cells/finite-ring QCA. The accepted death language must stay: "ECD.02 died as a capability differentiator on this carrier under this v1 current metric."

## Alphabet, Step Budget, And Readout Family

Same alphabet size: satisfied at the packet level. The classical search records `same_alphabet_size=6`; QIT L/R rows also operate on six label slots, with open-chain boundary labels shifted by one.

Same step budget: satisfied only in the packet's declared one-run/current metric. The classical baseline records `same_step_budget=1`; QIT current is a one-run directed information-current row over the realized QCA unitary.

Same readout family: partially satisfied, not identical. The QIT row computes projective left/right readout distributions and an MI center over output labels. The classical row is an abstract endpoint-copy `target_readout` policy with `I_source_target_readout_bits=1.0`. They share directed-current label units, but not the same dynamical readout construction. This is acceptable only because the baseline is intentionally the strongest same-alphabet classical endpoint policy; cite that strength explicitly.

## V0 Contract Fulfillment

The v0 audit's missing teeth were actually run in v1 as packet-local computations:

- Real MI rows: present. `I(source; left_readout)` and `I(source; right_readout)` are computed from joint distributions; result gates record `real_mi_rows_computed=true`.
- Grok two-bit joint-state entropy test: present as packet-local computation. Rows include initial source/memory entropy, final projective left/right readout entropy, entropy delta, posterior reduction proxy, and joint-state shape.
- Gemini equal-temperature flux test: present as packet-local computation. Rows set `thermal_gradient=0.0` and compute directed information current from projective dynamics.
- Fair strongest Szilard/classical baseline: present as a 36-policy endpoint search.
- Honest either-way verdict: present; the packet records death rather than softening the baseline.

Caveat: these are not fresh external Grok/Gemini worker reruns. They are implemented and rerun locally in the packet source/results.

## Controls

Controls that pass:

- Mirror flip: `R_engine=+1.0`, `L_engine=-1.0`; `mirror_control_flips_computed_flux_sign=true`.
- Scrambled schedule: `scrambled_schedule_control=0.0`; `scrambled_schedule_control_kills_signal=true`.
- No signed-index consumption in v1 QIT MI rows: the discovery design forbids `signed_index`, `rule_id`, `engine_side`, `chirality_label`, and endpoint-arrival indicators as witness sources.
- Policy-search no chirality-label leak: the classical policy search loops only over source and target labels and does not read chirality/rule/sign labels.

Control caveat:

The packet's no-identity-leak row is weaker than `audit_standards_codex_v1.md`. The source/result carry `no_identity_leak_check=true` and the validator checks that MI rows do not contain `signed_index` or `chirality`, but the packet does not emit the required standards fields:

- `identity_leak_detected`
- `identity_leak_excluded_best_accuracy`
- `identity_leak_exclusion_rule`

This does not rescue ECD.02 from death, because the death is driven by a stronger classical baseline. It does cap future citation of the no-identity-leak control: cite it as "no signed-index/chirality-label leak found in the MI rows and endpoint-policy search," not as a full standards-grade identity-leak analysis.

## Cross-Backend Status

The envelope and strict validator are green:

```text
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed --require-tool-intent system_v6/sims/ecd02_chiral_information_routing_v1/results/ecd02_chiral_information_routing_v1_envelope_results.json
=> {"ok": true, "result_json": "system_v6/sims/ecd02_chiral_information_routing_v1/results/ecd02_chiral_information_routing_v1_envelope_results.json"}
```

Focused tests are green:

```text
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest -q -p no:cacheprovider system_v6/sims/ecd02_chiral_information_routing_v1/tests/test_ecd02_chiral_information_routing_v1.py
=> 6 passed
```

Packet-local validator imported no-write returned `validator_errors=[]`.

Backend caveat:

The Julia leg is a death-boundary SMT leg over fixed integer current rows (`qit=1000`, `baseline=5000`), not an independent Julia recomputation of the MI distributions. JAX/Python and PyTorch consume the Python core/current rows; PyTorch adds a `torch.func` margin/Jacobian check. The cross-backend claim is therefore: three-engine death-boundary/envelope agreement, not three independent full MI-distribution implementations.

## Registry Row Language

Do not edit the registry from this audit; write scope is this file only. The current registry still lists ECD.02 as `ready for packet`.

Candidate-death replacement row language:

```text
| `ECD.02` | chiral information routing | fable-candidate + committed evidence; tested by `ecd02_chiral_information_routing_v1` | v1 computes QIT L/R directional-current and MI rows on the QCA-v3 open-chain carrier, but the strongest same-alphabet one-step classical endpoint policy reaches `abs(current)=5.0` versus QIT carrier max `1.0`; `registry_contract_pass=false`; `ecd02_status=DIES` | medium | P1 | died as capability differentiator at `scratch_diagnostic` / `capability_discriminator_only`; no finite-ring/all-cells QCA, physics chirality, axis, bridge, manifold, or QIT-engine admission |
```

Allowed citation:

`ecd02_chiral_information_routing_v1` is a fresh-audited `scratch_diagnostic` candidate-death packet: it computes real QIT L/R MI/current rows on the QCA-v3 open-chain carrier and then honestly kills ECD.02 as a capability differentiator because the strongest same-alphabet one-step classical endpoint policy reaches `abs(current)=5.0`, exceeding the QIT carrier-bound `1.0` current under this metric.

Forbidden citation:

Do not cite this as a global proof that QIT engines cannot route chirally; do not cite it as finite-ring or all-cells QCA evidence; do not cite it as physics chirality, axis admission, bridge/manifold evidence, or QIT-engine admission; do not cite the no-identity-leak control as standards-complete without adding the missing identity-leak fields.

## Route Truth

Wizard v4.2 Max Assembly was partial, not full. Main thread loaded v4.2 runtime/material and ran local source/result recomputation. Three Codex-native explorer sidecars returned read-only receipts for (1) reverse-fairness/QIT-vs-classical, (2) v0-contract controls, and (3) registry language. No child subsubagent hierarchy or full nine-parent v4.2 matrix ran. Counts should therefore be cited as partial sidecar audit evidence, not FULL Wizard topology.
