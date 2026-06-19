# Fresh audit verdict: basin_information_fusion_v0

VERDICT: PARTIAL PASS AS A FINITE PARTITION-INFORMATION ACCOUNT; FAIL/HOLD AS A REAL JOINT BASIN-INFORMATION-FLOW OBJECT.

The packet is not decorative-only: it computes a real derived table over the committed `G0`-`G5` generating-set rows, including support deltas, terminal-class deltas, may/must size deltas, typed counting entropy deltas, per-class-size distribution entropy deltas, responsible generator differences, selected parent flux/current annotations, null controls, and solver-checked class-count arithmetic.

It does not compute the stronger object requested in the prompt. There is no packet-local joint object linking basin structure to information flow in the sense of per-class channel capacities, entropy production along actual `R_C` orbits, record retention at merges, omega-limit retention, trapping/escape recomputation, or basin-conditioned throughput. The accepted ceiling is:

`scratch_diagnostic`: finite chart-relative partition-information accounting over committed basin/sweep parents; not a basin theorem, not invariant geometry, not packet-local record retention, not a throughput-capacity-per-basin object, and not formal admission.

No `git add` or commit was run.

## Source standard

- Basin contract: `system_v6/receipts/attractor_basin_criterion_20260611.md`.
- Typed entropy discipline: `manifold_entropy_ledger_v0` at `a54224476`; differential entropy, von Neumann entropy, mixed entropy, and lattice/counting entropy remain distinct unless a convention is explicit.
- Basin parent caveats:
  - `basin_rc_transition_graph_v0`: terminal-class language is earned, but strict omega-basin wording is held.
  - `basin_generating_set_sweep_v0`: finite 33-cell terminal-class splits are genuine with caveats.
  - `basin_grid_refinement_control_v0`: `G1` is finite chart-relative structure, killed as invariant geometry.
- Throughput parent caveat: `manifold_information_throughput_v0` is `PARTIAL_PASS_WITH_HARD_RECORD_OBJECT_CAVEAT`; Z4 record-side language is not packet-local without `CAVEAT_Q1`.

## Checks run

Read-only/no-result-rewrite checks:

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 - <<'PY'
import json
from pathlib import Path
import sys
sys.path.insert(0, 'system_v6/sims/basin_information_fusion_v0')
import validate_basin_information_fusion_v0 as v
p = Path('system_v6/sims/basin_information_fusion_v0/results/basin_information_fusion_v0_envelope_results.json')
payload = json.loads(p.read_text())
print(json.dumps({'ok': not v.validate(payload), 'errors': v.validate(payload)}, sort_keys=True))
PY
# {"errors": [], "ok": true}

/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 \
  scripts/validate_three_engine_sim_result.py \
  --require-source-backed \
  system_v6/sims/basin_information_fusion_v0/results/basin_information_fusion_v0_envelope_results.json
# {"ok": true, "result_json": ".../basin_information_fusion_v0_envelope_results.json"}
```

The stored packet validator result also says `ok: true`, `errors: []`. I did not run validator `main()` because it rewrites `results/basin_information_fusion_v0_validator_results.json`.

## Adjudication

### Q1 - Joint object versus decorative fusion

PARTIAL PASS / HOLD.

The packet computes more than a prose juxtaposition: `build_fusion()` rebuilds/loads the sweep rows, constructs seven transition rows, and emits numeric deltas and hashes. The synthesis correctly gives `G0->G1` as `log(3)` nats of counting partition information.

But it is not a real joint basin-information-flow object under the hard bar. Evidence:

- `build_card.md` says `manifold_information_throughput_v0` was untracked at build time and that committed parent rows are used directly.
- The packet does not consume throughput capacity rows, Holevo rows, record-retention rows, or the Z4 conservation caveat-bearing object.
- `fusion_table` rows are class-count and size-distribution accounting rows, plus selected parent flux/current annotations. They are not per-class capacities, entropy production along `R_C` orbits, or record retention at merges.
- The `G1->G2` "conservation" row is `log(3)=log(1)+log(3)`, an accounting identity over terminal-class counts. It is not record conservation and not a Z4 record-side construction.

Named caveat: `CAVEAT_JOINT_OBJECT_NOT_EARNED`.

Accepted phrase: "finite partition-information accounting over committed basin/sweep rows."

Rejected phrase: "joint basin-information-flow object" unless a successor packet binds actual basin classes/orbits to throughput, record, or capacity rows.

### Q2 - Typed entropy

PASS for table rows; FAIL for one synthesis row.

Every `fusion_table[*].entropy_type_delta` row declares the emitted types:

- `counting_entropy_log_class_count.type = counting_entropy`.
- `per_class_size_distribution_entropy.type = finite_distribution_entropy_over_terminal_class_sizes`.
- The counting rows cite `typed_parent = manifold_entropy_ledger_v0:a54224476`.

The packet also correctly flags a deliberate bad expression:

`counting_entropy_delta + distribution_entropy_delta`

as a cross-type sum, with the `a54224476` typed-discipline reason.

However, `synthesis_row.g2_remerge_conservation` emits `class_information_before`, `class_information_after`, and `merged_information` without a `type`, `typed_as`, or explicit convention field. Because the row is a headline "conservation" row, this is not just cosmetic.

Named caveat: `CAVEAT_REMERGE_SYNTHESIS_TYPE_MISSING`.

Future repair: type that row as `counting_entropy_delta_over_terminal_class_count` and state that it is class-count accounting only, not record or throughput conservation.

### Q3 - Chart-relativity and CAVEAT_Q1 inheritance

FAIL for `G1` chart-relative inheritance.

The target packet cites `G1` as "rotations-only active DoFs" and says the one-class anchor splits into three terminal classes. It does not carry the required chart-relative label from `basin_grid_refinement_control_v0`. I found no `chart-relative` or equivalent label in the target packet.

Named caveat: `CAVEAT_G1_CHART_RELATIVE_LABEL_MISSING`.

Correct inherited wording:

`G1` has three finite chart-relative terminal classes in the original 33-cell chart family; the split persists under declared 2x/3x containment refinements but changes under the pinned non-axis rotated chart, so it must not be cited as invariant geometry.

Z4/CAVEAT_Q1 status: no explicit Z4 conservation account row is present in this packet. That avoids a direct missing-CAVEAT_Q1 row, but it also confirms the packet did not fuse the hard record-retention object from `manifold_information_throughput_v0`.

Named caveat: `CAVEAT_NO_Z4_RECORD_RETENTION_FUSION`.

### Q4 - Basin guard

PASS only by parent anchoring; FAIL as packet-local basin evidence.

The packet uses committed finite basin/sweep parents that contain terminal-class and may/must basin evidence. But the fusion packet itself does not recompute or emit trapping, no-exit, escape, omega-containment, leakage, Morse edges, or Lyapunov evidence.

This is admissible only if cited as a parent-anchored accounting table over already-committed finite basin partitions. It is not a new basin object and not a new basin proof.

Named caveat: `CAVEAT_BASIN_GUARD_PARENT_ONLY`.

Forbidden reading: "clustering/MI agreement proves a basin." The target packet does not appear to make that exact mistake, but its basin vocabulary must stay tied to the parent finite graph evidence.

### Q5 - Standard controls, schema, engines, SMT

PASS with narrow-control caveats.

Accepted:

- Envelope schema is `three_engine_sim_result_v1`; no envelope schema fork found.
- Ceilings are present: `classification=scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`.
- JAX/Python and Julia both run and agree on the key summary; `divergence.max_divergence = 0.0`.
- Full `fusion_signature_agreement` is false, but the envelope explicitly treats that as non-critical serialization and gates acceptance on key-summary agreement.
- Byte-exact partition anchor, type-mixing control, and null transition control are true.
- z3, cvc5, and Julia Z3 all return real `unsat` and erased-flip `sat`.

SMT binding answer: yes, z3/cvc5 bind computed row values, not only hardcoded literal verdict strings. The Python proof binds `before`, `after`, and `delta` from each transition row and asserts that some row violates `after == before + delta`; the erased flip changes the `G1_to_G2` delta and flips to `sat`.

Narrowness caveat: `delta` is itself computed from `after - before`, so the solver proves internal arithmetic consistency of the emitted class-count deltas. It does not independently prove terminal classes, trapping, entropy typing, or information-flow coupling.

Named caveat: `CAVEAT_SMT_NARROW_CLASS_COUNT_ARITHMETIC`.

Control caveat: I found no shuffled/erased-label control in this packet. The packet has an erased class-delta SMT flip, type-mixing flag, byte anchor, and null transition, but not a shuffled-control row.

Named caveat: `CAVEAT_NO_SHUFFLED_CONTROL`.

Engine caveat: this is a Julia plus JAX/Python diagnostic. PyTorch is explicitly omitted as not scoped, so do not cite it as a full Julia/JAX/PyTorch result.

Named caveat: `CAVEAT_TWO_LANE_DIAGNOSTIC`.

## Named caveats

1. `CAVEAT_JOINT_OBJECT_NOT_EARNED`: computes finite partition-information accounting, not per-class capacity/orbit entropy/record-retention fusion.
2. `CAVEAT_REMERGE_SYNTHESIS_TYPE_MISSING`: `g2_remerge_conservation` lacks explicit entropy/information type/convention.
3. `CAVEAT_G1_CHART_RELATIVE_LABEL_MISSING`: G1 rows omit required chart-relative inheritance.
4. `CAVEAT_NO_Z4_RECORD_RETENTION_FUSION`: no Z4 record-retention account is fused; do not import the throughput parent's record language without `CAVEAT_Q1`.
5. `CAVEAT_BASIN_GUARD_PARENT_ONLY`: basin vocabulary is parent-anchored; trapping/escape evidence is not packet-local.
6. `CAVEAT_SMT_NARROW_CLASS_COUNT_ARITHMETIC`: SMT binds computed values but only proves class-count delta consistency.
7. `CAVEAT_NO_SHUFFLED_CONTROL`: erased flip exists; shuffled/label-erasure control is absent.
8. `CAVEAT_TWO_LANE_DIAGNOSTIC`: Julia plus JAX/Python only; PyTorch omitted.
9. `CAVEAT_WORKTREE_ONLY_PACKET`: target packet is untracked worktree state at audit time.
10. `CAVEAT_WIZARD_MAX_ASSEMBLY_PARTIAL`: audit used controller reads plus three Codex parent sidecars, not the full v4.2 nine-parent/child topology.

## Future-citation rule

Allowed citation:

`basin_information_fusion_v0` is a `scratch_diagnostic` finite chart-relative partition-information accounting table over committed basin/sweep rows. It computes per-transition support/class/may/must deltas, typed counting and finite-distribution entropy deltas, responsible-generator differences, selected parent flux/current annotations, null controls, and narrow class-count SMT identities, with Julia and JAX/Python key-summary agreement.

Required qualifiers:

- `G1` must always be called finite chart-relative original-33-cell structure, not invariant geometry.
- The `G1->G2` re-merge row must be called counting terminal-class accounting only unless its type convention is repaired.
- Any future use of Z4 conservation or record retention must carry `CAVEAT_Q1_RECORD_SIDE_NOT_PACKET_LOCAL_Z4_SYNDROME` from `manifold_information_throughput_v0`.
- Basin vocabulary must cite the parent trapping/no-exit/escape evidence; this packet does not recompute it.

Forbidden citation:

Do not cite this packet as a real joint basin-information-flow object, per-class capacity table, entropy-production-along-orbits result, record-retention-at-merges result, invariant geometric basin result, universal information scalar, bridge/axis/physics claim, formal basin theorem, or full three-engine result.
