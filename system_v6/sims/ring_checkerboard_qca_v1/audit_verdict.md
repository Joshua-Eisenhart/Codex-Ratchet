# Audit verdict - ring_checkerboard_qca_v1

Audit mode: fresh read-only independent audit. This verdict file is the only audit-lane write; it is not builder output.

BOTTOM LINE: REJECT as an earned QCA/GNVW index result. The packet is internally consistent as a fenced `scratch_diagnostic`, and its result validators/tests pass, but the central "computed index" is not a genuine invariant computed from a realized local quantum rule. It is a shift/wire-flow parameter supplied in the rule table and read back as `right_wires - left_wires`. Under the 28fc221a1 correction lens, this is the same failure mode as the classical period headline: a value forced by the realization choices, not discovered from the rule.

Repo vocabulary verdict: `scratch_diagnostic_failed_adjudication_for_index_claim`. Do not promote. Do not cite as an earned GNVW/index invariant, an earned doctrine expectation 2 result, canonical QCA admission, v4 coupling-law admission, or quantum-mechanical derivation of L/R flux.

## Scope And Route Truth

Allowed write used: this file only.

Target audited: `system_v6/sims/ring_checkerboard_qca_v1/`.

Authority lens applied:

- `system_v6/receipts/owner_doctrine_cellular_automata_ring_checkerboard_20260611.md`, including the 28fc221a1 correction at lines 66-82.
- Classical floor `fe06d49bd` as corrected: period-2 vs period-4 is implementation-correctness only; the surviving structural row is transient SCC topology.
- `system_v6/sims/ring_checkerboard_qca_v1/build_card.md`.
- Standard-math GNVW/index labeling only, never owner-source.

Route truth: partial Max Assembly audit, not full v4.2. Three Codex-native sidecar auditors completed: index/gauge, calibration/classical/locality, and quantum/tools/schema. No child subsubagents were launched. Controller performed the decisive recomputations and owns this verdict.

## Index Computation Reality

Verdict: FAIL.

The exact procedure used is table arithmetic:

- `raw_index_fraction(right_wires, left_wires)` returns `Fraction(QUBIT_DIM**right_wires, QUBIT_DIM**left_wires)` in `ring_checkerboard_qca_v1_common.py:163`.
- `index_row(...)` sets `signed = right_wires - left_wires`, emits `right_support_algebra_rank = 2**right_wires`, `left_support_algebra_rank = 2**left_wires`, `standard_index_ratio`, and `signed_log2_index` in `ring_checkerboard_qca_v1_common.py:167-207`.
- `index_table()` manually constructs the rows with supplied wire counts: right shift `(1,0)`, left shift `(0,1)`, onsite `(0,0)`, L `(0,1)`, R `(1,0)`, gauge right shift `(1,0)`, paired block `(1,1)` in `ring_checkerboard_qca_v1_common.py:210-295`.
- The Julia backend hard-codes the shorter index table directly in `ring_checkerboard_qca_v1_julia.jl:158-165`.
- JAX and PyTorch read the packet table and validate those values, rather than deriving them from a QCA map, in `ring_checkerboard_qca_v1_jax.py:68-98` and `ring_checkerboard_qca_v1_pytorch.py:36-57`.

The packet's cited standard definition is labeled correctly as standard math: the object says `signed_log2_index = log2(dim(right support algebra)/dim(left support algebra))` and `index_definition_status = standard_math_alignment_not_owner_source` in `ring_checkerboard_qca_v1_common.py:619-627`. The doctrine also says QCA/GNVW is standard-math alignment, not owner-source, in `owner_doctrine_cellular_automata_ring_checkerboard_20260611.md:21-27`.

The labeling is acceptable. The computation is not.

Controller recomputation of the right-shift calibration:

```text
right shift: right_cross=1, left_cross=0, signed_log2=1, ratio=2/1
left shift:  right_cross=0, left_cross=1, signed_log2=-1, ratio=1/2
onsite:      right_cross=0, left_cross=0, signed_log2=0, ratio=1/1
```

This confirms the calibration for a partitioned shift convention, but it does not rescue the packet. The packet does not compute crossing support algebras from an implemented local unitary/CPTP rule. It declares the crossing wires.

Gauge/local-basis invariance:

```text
packet base row:  calibration_right_shift signed_log2_index=1 ratio=2/1
packet gauge row: gauge_reparameterized_right_shift signed_log2_index=1 ratio=2/1
controller test:  changing basis metadata leaves index unchanged
```

This is not a real invariance test. The basis field is metadata and the index function ignores it. A local-basis reparameterization cannot make the computation fail unless the manually supplied wire counts are changed. Therefore the decisive gauge/local-basis invariance gate is not earned.

## Expectation 2 - L/R Opposite Index Signs

Verdict: NOT EARNED.

Internal rows:

```text
calibration_right_shift = +1
calibration_left_shift = -1
calibration_nonshifting_onsite = 0
engine_L_flux_in_left = -1
engine_R_flux_out_right = +1
engine_L_index0_control = 0
engine_R_index0_control = 0
paired_block_index0 = 0
```

The signs are internally consistent and the index-0 controls show no L/R distinction under the same table probe. But that probe is the assigned wire-flow table, not an invariant recomputed from realized QCA dynamics.

The falsifier branch is also table-local: `force_R_engine_to_left_shift` changes the assigned R sign to `-1`, so the opposite-sign predicate fails. That proves a boolean can flip after mutating the table. It does not prove the realized rule can be perturbed and have its index recomputed from support algebras.

Adjudication: expectation 2 remains open. The packet may be cited only as an internally consistent chirality assignment table with +1/-1/0 calibrations, not as an earned L/R QCA index invariant.

## Expectation 3 - Locality Changes Coupling

Verdict: PARTIAL SCRATCH ONLY.

Controller recomputation:

```text
matched_state_count = 6400
local_brickwork: state_count=6400, scc_count=1600, terminal_class_count=1600, period_histogram={"4": 6400}
global_v3_style: state_count=6400, scc_count=160, terminal_class_count=160, period_histogram={"40": 6400}
```

This is not a size-count artifact within the packet: both compared maps use 6400 states. The local-vs-synthetic-global functional graph difference is real for the two maps implemented in `locality_graph()`.

But it is not enough for the doctrine's coupling-law claim:

- `global_v3_style` is an ad hoc comparator inside this v1 packet, not the committed v2/v3/v4 carrier.
- The sidecar audit found the committed v3 result uses a different state count (`1024`) and current v4 flux rows expect joint counts at `4096`, so this is not matched to the live coupling-law state surfaces.
- The packet's order-shuffle control is a false-positive pass. `order_shuffle_changes_local_structure` compares whole signatures that include the `kind` label. Controller recomputation found the local and order-shuffle metric payloads are equal after removing `kind`: same state count, edge count, SCC count, terminal count, terminal sizes, and period histogram.

Adjudication: expectation 3 survives only as a bounded local-vs-synthetic-global functional-graph contrast. It does not earn v4 coupling admission, and the registered flipping/control story needs repair.

## Classical Limit

Verdict: FAIL under the corrected doctrine lens.

The packet's classical-limit check imports the current worktree `ring_checkerboard_automaton_v0_common` and calls `v0.build_packet()`. It stores:

```text
alternating_period_histogram = {"2": 576}
paired_period_histogram = {"4": 576}
phase_structure_reproduced = true
```

That is exactly the row demoted by the 28fc221a1 correction. The correction says the period-2 vs period-4 headline is definitionally forced and should be cited only as implementation-correctness. The surviving v0 structural content is transient SCC topology.

Controller recomputed the v0 row from the current source:

```text
alternating: state_count=576, scc_count=464, terminal_class_count=112, terminal_state_count=224, period={"2": 576}
paired:      state_count=576, scc_count=240, terminal_class_count=112, terminal_state_count=448, period={"4": 576}
transient_scc: alternating=352, paired=128, ratio=2.75
```

The QCA packet does not carry or compare the corrected transient-SCC row. It also does not demonstrate a dephased restriction of an implemented quantum channel that reproduces the corrected v0 structure. It simply reuses the v0 builder packet and checks the old period headline.

Adjudication: continuity with `fe06d49bd` is not earned as a dephased QCA classical limit. At most, the packet reproduces the old period implementation check.

## Quantum Reality

Verdict: THIN / NOT LOAD-BEARING FOR THE INDEX.

There is real package execution:

- Julia uses QuantumOptics for a one-qubit density/entropy row and QuantumClifford for an `S"X"` stabilizer token in `ring_checkerboard_qca_v1_julia.jl:214-228`.
- JAX/qutip verifies H, SWAP, and dephase-Z local gate/CPTP checks in `ring_checkerboard_qca_v1_jax.py:41-65`.
- PyTorch uses `torch_geometric.data.Data` for a small ring-incidence check and `torch.func.jacrev` for a zero-gradient check against the expected signed-index vector in `ring_checkerboard_qca_v1_pytorch.py:60-105`.

These are real calls, but they do not compute the claimed QCA index. The index path is classical table arithmetic plus SMT consistency over table values. QuantumOptics, QuantumClifford, qutip, torch.func, and torch_geometric do not derive support-algebra ranks from a realized local quantum channel.

Tool-depth caveat: QuantumClifford should not be called load-bearing here. Its observable is a package-liveness stabilizer token, not a pass/fail constraint on the index or locality result.

## Validators, Schema, Fences, And File Boundary

Fresh commands run:

```bash
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed --require-tool-intent system_v6/sims/ring_checkerboard_qca_v1/results/ring_checkerboard_qca_v1_envelope_results.json
# ok: true

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=system_v6/sims/ring_checkerboard_qca_v1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest -q -p no:cacheprovider system_v6/sims/ring_checkerboard_qca_v1/tests
# 6 passed

PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/lint_sim_contract.py system_v6/sims/ring_checkerboard_qca_v1/ring_checkerboard_qca_v1_common.py system_v6/sims/ring_checkerboard_qca_v1/ring_checkerboard_qca_v1_jax.py system_v6/sims/ring_checkerboard_qca_v1/ring_checkerboard_qca_v1_pytorch.py system_v6/sims/ring_checkerboard_qca_v1/ring_checkerboard_qca_v1_envelope.py
# violation_total: 11
# C2_manifest_missing: 4
# C3_depth_missing: 4
# C1_classification_missing: 3
```

Not rerun fresh:

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/ring_checkerboard_qca_v1/validate_ring_checkerboard_qca_v1.py --phase post_audit
```

Reason: that packet validator writes `results/ring_checkerboard_qca_v1_validator_results.json`. The existing stored validator result is `ok: true`, phase `post_audit`, but this audit kept repo writes limited to `audit_verdict.md`.

Fences held in the envelope:

- `classification = scratch_diagnostic`
- `promotion_allowed = false`
- `formal_admission_allowed = false`
- disallows canonical QCA admission, full all-cells binary enumeration, v4 coupling-law admission, owner-source GNVW/index status, and physics/cosmology/consciousness claims

File-boundary caveat: the whole `system_v6/sims/ring_checkerboard_qca_v1/` packet is currently untracked in git. This audit does not stage or commit it.

## Named Caveats

1. Table-derived index caveat: every index value is forced by supplied wire counts.
2. Gauge caveat: the local-basis invariance check is metadata-invariant, not rule-invariant.
3. Classical correction caveat: the packet preserves the demoted period headline, not the corrected transient-SCC classical floor.
4. Synthetic-global caveat: expectation 3 compares a local map against a packet-local `global_v3_style` map, not the committed v2/v3/v4 coupling surface.
5. Order-shuffle caveat: the QCA order-shuffle control passes because the signature includes `kind`; the metric payload is unchanged.
6. Quantum-depth caveat: quantum packages run, but they do not compute the index invariant.
7. Process caveat: result validators pass, but source static lint fails and the packet is untracked.

## Future Citation Rule

Allowed future citation:

> `ring_checkerboard_qca_v1` is a failed audit case showing internally consistent +1/-1/0 chirality table rows, real package-level gate/liveness checks, and a bounded 6400-state local-vs-synthetic-global functional-graph contrast, but no earned QCA/GNVW index invariant.

Forbidden future citation:

- "The L/R QCA index was computed."
- "Doctrine expectation 2 was earned."
- "GNVW/index alignment survived gauge/local-basis invariance."
- "The dephased QCA limit reproduces the corrected v0 classical floor."
- "Locality-changes-coupling is admitted for v4."
- "QuantumOptics/QuantumClifford computed the index."
- "The packet is canonical/admitted/promotable."
