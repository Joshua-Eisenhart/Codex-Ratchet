Independent audit verdict - fresh audit, read-only except this file.

Bottom line: VERDICT: CANDIDATE-DEATH ACCEPTED WITH BOUNDARY CAVEATS. `ecd05_instruction_machine_v0` dies at the pinned v0 `program_length=3` budget on this realization: QIT max `816`, strongest same-alphabet classical baseline max `4096`, margin `-3280`, verdict `DIES_v0`. Claim ceiling remains `scratch_diagnostic`; `promotion_allowed=false`; `formal_admission_allowed=false`.

Registry-row language:

> ECD.05 64-slot instruction machine: `DIES_v0` at pinned length-3 on the audited 64-slot realization. The QIT side exhaustively searches schedule-order subsequences without replacement (`C(64,3)=41664`) and reaches `816` label-free output fingerprints. The fair strongest-form classical baseline uses the same 64 slot-operation alphabet for 3 steps with arbitrary order and repetition (`64^3=262144`) and reaches `4096` label-free output fingerprints. This is a bounded v0 death under the packet's metric and baseline pin, not a universal no-instruction-machine result, not QIT-engine admission/failure, not Turing/universal-computation evidence, not substage-semantics evidence, and not physics/basin/64-subsubbasin evidence.

Freshness tier: `TIER-2` under `system_v6/receipts/audit_standards_codex_v1.md`. I read source/result/build surfaces and then independently recomputed the decisive values from source without writing result files. No prior audit verdict for this packet existed before this file.

## Scope And Authority

Binding surfaces read:

- `AGENTS.md`
- `CODEX.md`
- `system_v5/docs/ENFORCEMENT_AND_PROCESS_RULES.md`
- `system_v5/docs/LLM_CONTROLLER_CONTRACT.md`
- `system_v5/docs/LEGO_SIM_CONTRACT.md`
- `system_v6/receipts/audit_standards_codex_v1.md`
- `system_v6/receipts/ecd_registry_supplement_1_20260612.md`
- `system_v6/sims/ecd05_instruction_machine_v0/build_card.md`
- `system_v6/sims/ecd05_instruction_machine_v0/ecd05_instruction_machine_v0_common.py`
- `system_v6/sims/ecd05_instruction_machine_v0/validate_ecd05_instruction_machine_v0.py`
- `system_v6/sims/ecd05_instruction_machine_v0/tests/test_ecd05_instruction_machine_v0.py`
- `system_v6/sims/eng64_stage_fingerprint_ids_v0/eng64_stage_fingerprint_ids_v0.py`
- `system_v6/sims/eng64_stage_fingerprint_ids_v0/results/eng64_stage_fingerprint_ids_v0_results.json`
- `system_v6/sims/engine_64_stage_full_run_v0/results/engine_64_stage_full_run_v0_results.json`
- `system_v6/sims/engine_64_stage_full_run_v0/audit_verdict.md`

This audit accepts the death only under the pinned packet definitions. It does not promote ECD.05, the 64-slot carrier, the fingerprint estate, or any upstream engine surface beyond their own stated ceilings.

## Program-Space Fairness

The asymmetry is real and derived from the pinned definitions:

| Side | Program semantics | Nominal count | Derived count |
|---|---|---:|---:|
| QIT | choose 3 slots from the pinned 64-slot schedule, no replacement, preserving schedule order | `C(64,3)` | `41664` |
| baseline | same 64 slot-operation alphabet, 3 steps, arbitrary order, repetition allowed | `64^3` | `262144` |

This is not a QIT-single versus baseline-search comparison; both sides search. It is also not a symmetric schedule-locked mirror. The baseline is structurally larger because the build card pins a strongest-form classical machine: same operation alphabet and step budget, but free ordering and reuse. I adjudicate that as an honest death baseline under Supplement 1's two-sided doctrine because a candidate death may give the classical side every classical control resource in the pinned alphabet/step budget.

Caveat: this does not kill narrower questions such as a schedule-locked classical mirror, no-repeat classical baseline, longer QIT programs, or normalized diversity per admissible program-space size. Those are reopen lanes, not defects in this pinned v0 death.

## Fresh Recompute

Non-writing recompute command:

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 - <<'PY'
import json, sys
from pathlib import Path
sim_dir = Path('system_v6/sims/ecd05_instruction_machine_v0').resolve()
sys.path.insert(0, str(sim_dir))
import ecd05_instruction_machine_v0_common as c
obj = c.build_instruction_machine_object()
print(json.dumps({
  'all_pass': obj['all_pass'],
  'qit_nominal': obj['qit_side']['nominal_program_count'],
  'qit_count': obj['qit_side']['computed_distinct_channel_count'],
  'baseline_nominal': obj['baseline_side']['nominal_program_count'],
  'baseline_count': obj['baseline_side']['computed_distinct_channel_count'],
  'margin': obj['discriminator']['qit_minus_baseline_margin'],
  'verdict': obj['discriminator']['verdict'],
}, indent=2, sort_keys=True))
PY
```

Fresh result:

```json
{
  "all_pass": true,
  "baseline_count": 4096,
  "baseline_nominal": 262144,
  "margin": -3280,
  "qit_count": 816,
  "qit_nominal": 41664,
  "verdict": "DIES_v0"
}
```

Detailed recompute values:

| Field | Fresh value |
|---|---:|
| QIT frontier unique counts | `[1, 16, 136, 816]` |
| QIT channel table hash | `ccc3b0075ee039dbee0d7217a635322b3e7c1fba6009e7cf0ca3bf282a5d93a1` |
| baseline frontier unique counts | `[1, 16, 256, 4096]` |
| baseline channel table hash | `fd11124cba5c7b025c0240a864f9ace18bcab58fe37f74f2b4f3ee4c110ffd65` |
| order-blind collapse count | `816` |
| dropped-half QIT count | `120` from `C(32,3)=4960` nominal programs |
| dropped-half baseline count | `512` from `32^3=32768` nominal programs |
| scrambled QIT count | `3822` |

The packet-local validator function also passed without writing:

```json
{
  "ok": true,
  "validate_payload_errors": []
}
```

I did not run the packet's pytest in the live tree because `test_validator_delegates_to_builder_audit_boundary_from_birth` writes packet result/envelope files and temporarily writes `audit_verdict.md`. That is acceptable as a builder test shape, but it would violate this audit's read-only boundary. Source inspection confirms the test exercises G.2a by delegating to `scripts/builder_audit_boundary.py`.

## Fingerprint And 4096 Check

The fingerprint family is the same on both sides: compose slot density-channel operations from `eng64_stage_fingerprint_ids_v0` on the deterministic representative L-Weyl density matrix, flatten `rho_out` to eight real/imag floats, round at `1e-7`, and hash only that numeric vector. Slot labels, source-stage labels, engine/direction text, and collapse-pair text are excluded.

The baseline `4096 = 16^3 = 2^12` is not a program-label readout artifact under this metric. I recomputed:

```json
{
  "component_classes": 16,
  "slots_per_component_values": [4],
  "ordered_component_triples": 4096,
  "unique_outputs_from_one_rep_per_component_ordered_triples": 4096,
  "expected_16_pow_3": 4096,
  "expected_multisets_16_len3": 816,
  "qit_component_multiset_count_from_examples": 816
}
```

Interpretation: the QIT schedule-order subsequence side collapses exactly to the 816 length-3 multisets over 16 label-free components. The strongest classical baseline realizes all 4096 ordered length-3 component triples as distinct numeric output fingerprints. That is a real win for the baseline under this diversity metric, not identity leakage.

Caveat: the metric is an output-state fingerprint from a deterministic representative input, not full channel tomography over all possible inputs. It is the pinned metric for this packet and is applied to both sides, but future channel metrics that penalize trivially injective ordered classical readouts or require process-level equivalence can reopen the question.

## Controls

The requested controls fire by computation:

| Control | Verdict | Evidence |
|---|---|---|
| order-blind collapse | fires | component-multiset collapse count `816`, equal to QIT count; no extra order-sensitive QIT channels over component multisets |
| dropped-half sensitivity, QIT | fires | `120` distinct channels from `4960` nominal half-space programs |
| dropped-half sensitivity, baseline | fires | `512` distinct channels from `32768` nominal half-space programs |
| scrambled-schedule regression | fires | scrambled QIT count `3822`, hash `dfa2039de1be223041b8eb8eeba4271e1a9fceced10f868489bc4fd1cf70c417`, differs from pinned QIT count/hash |
| no identity leak | passes | label rename leaves fingerprint ids unchanged; excluded fields include slot/source labels and engine/direction/collapse text |

## Fences

The realization-relativity fence is present and binding:

- all programs run on the same pinned 64-slot realization;
- upstream 64-run hash hint is `23cfa5536`;
- source-admitted substage convention is false;
- no substage-semantics claim is made;
- disallowed claims include universal computer, Turing-complete machine, QIT-engine admission, canonical engine runtime, source-admitted substage semantics, 64-subsubbasin proof, physics claim, and hexagram closure.

The envelope honestly declares `three_engine_mode = not_scoped_for_this_packet` because this is an exhaustive finite program-space search over an already pinned density-channel family, not a Julia/JAX/PyTorch three-engine packet.

## G.2a

G.2a verified. The validator and tests delegate audit-boundary handling to `scripts/builder_audit_boundary.py` from birth:

- result/envelope carry `no_builder_audit_verdict = true`;
- validator calls `builder_audit_boundary_errors(...)` on base payload and envelope;
- pytest contains a negative test that a non-independent `audit_verdict.md` header fails;
- this file's header declares independent/fresh/read-only audit status, so post-audit idempotency should remain green.

## Verdict And Reopen Conditions

Accepted status label: `passes local recompute` for the decisive source-derived counts and `passes validator function` for the current result/envelope, with overall classification still `scratch_diagnostic`.

Candidate status: `DIES_v0` at pinned length-3 on this realization.

Claim ceiling: bounded registry death only. No promotion, no admission, no universal computation, no global instruction-machine impossibility, no substage semantics, no physics/basin/manifold/axis claim.

Reopen conditions suggested by the result itself:

- length-4 or longer QIT program budgets;
- schedule-locked or no-repeat classical baselines as narrower comparators;
- process-level channel metrics instead of deterministic representative output-state fingerprints;
- metrics that penalize trivially injective ordered classical readouts;
- diversity normalized by admissible program-space size;
- alternative realizations or carriers under the same two-sided fair-baseline doctrine.
