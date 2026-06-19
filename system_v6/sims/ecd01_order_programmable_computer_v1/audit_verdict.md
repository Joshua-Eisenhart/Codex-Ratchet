# Independent Audit Verdict - ecd01_order_programmable_computer_v1

Audit mode: read-only audit with independent recomputation before builder prose.

Verdict: GENUINE-WITH-CAVEATS.

Bottom line: the v1 repair survives the v0 BY_CONSTRUCTION kill under the pinned plain-Szilard schedule contract. I recomputed the finite schedule space from source before reading `build_card.md` or `builder_self_assessment.md`: 24 candidate four-stroke permutations, 4 dependency-admissible schedules, 2 label-free Szilard channel classes, 3 QIT registered channel classes, margin 1 on the committed 33-cell carrier. The computational discriminator is genuine-with-caveats, but the packet has a standards caveat: its validator/test boundary is green before an audit file exists and not post-audit-idempotent after this legitimate independent verdict is written.

## Freshness And Scope

- Freshness tier: TIER-2. I read source and result JSON, recomputed the table, then read builder prose/card after recomputation.
- Binding standard: `system_v6/receipts/audit_standards_codex_v1.md`.
- Write scope observed: live repo write limited to this `audit_verdict.md`. No git add/commit.
- Classification ceiling: `scratch_diagnostic`; `promotion_allowed=false`; `formal_admission_allowed=false`; claim ceiling `capability_discriminator_only`.

## Recomputed Core

The source pins the plain Szilard baseline as all permutations of:

- `measure_record_one_bit`
- `feedback_isothermal_expansion`
- `erase_record`
- `reset_boundary`

with only the dependency filter `measure < feedback < erase`; `reset_boundary` floats. Recomputing this gives:

- candidate permutations: 24
- admissible schedules: 4
- inadmissible schedules: 20
- admissible channel words: `EUEU`, `EUUE`, `EUUE`, `UEUE`
- Szilard distinct label-free channel hashes: 2
- QIT registered words: `UEUE`, `UUEE`, `UEEU`
- QIT distinct label-free channel hashes: 3
- margin: 1

The baseline and QIT rows use the same fingerprint family: label-free output multisets over the committed 33-cell Axis-4 carrier. The baseline table does not use schedule labels as channel fingerprints; the no-identity-leak control reports `pass`.

## Teeth

1. Enumeration completeness: complete under the pinned plain single-loop Szilard definition. The repair card pins the finite space directly: 24 permutations, `measure < feedback < erase`, floating reset, same fingerprint family. The audit caveat is that this is not completeness over arbitrary four-symbol U/E programs. If the baseline is redefined to include arbitrary QIT-style order words such as `UUEE` and `UEEU`, the result must be reopened because that grants the non-Szilard program switch the packet is trying to distinguish.
2. Same-family recomputation: confirmed. Recomputed QIT `3` and Szilard `2`; Julia scratch rerun also returned QIT `3`, Szilard `2`, margin `1`, and `z3=unsat`.
3. Positive predicate: live. The predicate admits/kills if baseline distinct count reaches QIT count. Synthetic stronger-baseline injection at count `3` reports `actual_admitted=true` and `ecd01_would_die=true`.
4. Dropped-half control: present and sensitive. Dropping half the admissible table changes the predicate input from `2` to `1`.
5. Margin honesty: margin is only `1` on a 33-cell carrier. Distances among QIT words are not numerically tiny (`5.61`, `5.61`, `11.22`), and an audit-only lambda sweep around the committed `0.7` convention kept margin `1` for `0.5..0.9` and collapsed at `lambda=1`. But the packet itself does not commit a perturbation family beyond label shuffle, commuting collapse, and the symbolic `lambda=1` erasure row; cite stability only at that bounded level.
6. Fences: present. The envelope disallows universal quantum computer, Turing-complete computer, QIT engine admission, canonical Axis-4 identity, physics claim, and bridge admission.

## Checks Run

- Import-level source recomputation, no live result rewrite: PASS.
- `validate_ecd01_order_programmable_computer_v1.validate_payload(...)` before writing this audit file: PASS, `error_count=0`.
- `scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed --require-tool-intent ...envelope_results.json`: PASS.
- `python3 -m pytest -q -p no:cacheprovider system_v6/sims/ecd01_order_programmable_computer_v1/tests` before writing this audit file: PASS, `4 passed`.
- Julia lane scratch rerun in `/tmp`, not live repo: PASS.
- JAX/PyTorch `build_result()` import-level recompute, no live result rewrite: PASS.
- Post-audit idempotency check after writing this file: FAIL. Direct validator call reports `builder must not emit audit_verdict.md`; pytest reports one failure on `assert not (SIM_DIR / "audit_verdict.md").exists`. This is a process/test-boundary defect, not a recomputation defect.

## Caveats

- The Python/JAX/PyTorch lanes share `ecd01_order_programmable_computer_v1_common.py` for the decisive table. Their agreement is useful packaging/validator evidence, not three independent derivations of the schedule space. The Julia lane independently rebuilds the finite carrier, schedule enumeration, channel hashes, and SMT inequality.
- The schedule-space fairness claim is only fair under the plain single-loop Szilard contract. It should not be cited as a proof that every conceivable classical controller with the same alphabet and step budget loses.
- The packet violates the post-audit idempotency rule in `audit_standards_codex_v1`: validator/test code still requires live absence of `audit_verdict.md` instead of trusting the build-time `no_builder_audit_verdict` field plus independent-audit header gate. Repair is needed before claiming "validators green" after audit.
- The sim directory is an untracked packet in this checkout at audit time. This does not change the computational verdict, but citation should name the packet path/result files rather than imply committed canonical status unless a later commit records it.

## Citation Rule

Allowed citation:

> `ecd01_order_programmable_computer_v1` is a scratch diagnostic whose v1 discriminator survives its enumerated strongest-form plain single-loop Szilard baseline at margin 1: QIT registered channel diversity `3` versus computed Szilard baseline max `2`, under the same label-free 33-cell Axis-4 fingerprint family.

Required citation caveat:

> This is not QIT-engine admission, not a universal/Turing computation claim, not a bridge/physics claim, and not a proof against arbitrary augmented classical U/E schedulers. The baseline is complete only for the pinned plain Szilard schedule space.

Do not cite:

- "QIT engine can compute universally."
- "The first real QIT computer."
- "Classical computation is beaten in general."
- "All same-alphabet classical schedules were exhausted."
- "Canonical Axis-4/QIT admission."
