# Fresh audit verdict: z4_syndrome_record_v0

Bottom line: `ACCEPTED_AS_SCRATCH_DIAGNOSTIC_WITH_CAVEATS`. The packet does construct a packet-local Z4 syndrome/preimage record object, and the conservation row is not merely `record := loss` at the packet level. `CAVEAT_Q1_RECORD_SIDE_NOT_PACKET_LOCAL_Z4_SYNDROME` is closed for future scratch-diagnostic citations of `manifold_information_throughput_v0`'s Z4 conservation row, provided citations also cite this packet and keep the finite-counting state-plus-record convention explicit.

This is not formal admission, not a canonical theorem, and not a universal entropy scalar. Ceiling remains `classification=scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`.

## Scope

Auditor: independent Codex cross-backend auditor.
Date: 2026-06-11.
Write boundary: this `audit_verdict.md` only. No `git add` or commit performed.

Read/audited surfaces:

- `system_v6/sims/manifold_information_throughput_v0/audit_verdict.md`
- `system_v6/sims/z4_syndrome_record_v0/build_card.md`
- `system_v6/sims/z4_syndrome_record_v0/z4_syndrome_record_v0_jax.py`
- `system_v6/sims/z4_syndrome_record_v0/z4_syndrome_record_v0_pytorch.py`
- `system_v6/sims/z4_syndrome_record_v0/z4_syndrome_record_v0_julia.jl`
- `system_v6/sims/z4_syndrome_record_v0/z4_syndrome_record_v0_envelope.py`
- `system_v6/sims/z4_syndrome_record_v0/validate_z4_syndrome_record_v0.py`
- `system_v6/sims/z4_syndrome_record_v0/results/*envelope*.json`
- relevant parent snippets from `ratchet_deep_chain_v0` and `manifold_entropy_ledger_v0`

Wizard/worker route truth: partial local audit only. Codex-native subagents were not spawned because the available `spawn_agent` tool is restricted to turns where the user explicitly asks for subagents/delegation. This verdict is therefore controller plus local-tool evidence, not a full v4.2 Max Assembly topology receipt.

## Decisive question

Verdict: the packet does not smuggle `record := loss` back in as its decisive computation.

The state-loss path and record-retention path are materially distinct in the JAX/Python and PyTorch legs:

- JAX constructs 24 rows by enumerating 6 pinned orbit ids times 4 phase representatives, with syndrome bits and `alpha += pi/2` (`z4_syndrome_record_v0_jax.py:75-95`).
- JAX state loss is computed from quotient preimage cardinalities via `quotient_loss_from_preimages`, grouping rows by `quotient_output` and averaging `log(fiber size)` (`z4_syndrome_record_v0_jax.py:115-132`).
- JAX record retention is computed from the constructed syndrome table distribution via `Counter(row["syndrome"] for row in table)` and Shannon entropy over those counts (`z4_syndrome_record_v0_jax.py:98-112`, `:167-176`).
- PyTorch state loss is computed through a `torch_geometric.data.Data` incidence graph and `torch.bincount(graph.edge_index[0])` (`z4_syndrome_record_v0_pytorch.py:95-129`).
- PyTorch record retention is computed separately from `Counter(row["syndrome"] for row in rows)` and exact SymPy entropy (`z4_syndrome_record_v0_pytorch.py:80-92`, `:164-170`).

The packet-level result records distinct code paths:

- JAX: `quotient_preimage_cardinalities_to_average_log_fiber_size` versus `distribution_counts_to_shannon_entropy`.
- PyTorch: `torch_geometric_incidence_graph_indegree_to_average_log_fiber_size` versus `torch_counts_to_sympy_shannon_entropy`.
- Julia: `Graphs.SimpleDiGraph_outdegree_preimage_counts_to_average_log_fiber_size` versus `julia_count_distribution_to_shannon_entropy`.

Named caveat: `CAVEAT_JULIA_RECORD_COUNTS_LITERAL`. The Julia leg builds the 24-row table and computes state-loss preimage counts through `Graphs.SimpleDiGraph` (`z4_syndrome_record_v0_julia.jl:46-100`), but its record rows are passed as literal count vectors `[6, 6, 6, 6]`, `[24]`, and `[12, 12]` rather than derived from the table by a Julia-side `count(row["syndrome"])` pass (`z4_syndrome_record_v0_julia.jl:141-147`). This weakens the all-three-engine record-computation claim. It does not reopen the original Q1 caveat because JAX, PyTorch, the envelope, and independent recomputation support the packet-local record side.

## Syndrome table and reconstruction

Pass.

The packet enumerates 24 representatives: 6 pinned orbits, each with syndrome values `{0,1,2,3}`. The envelope exposes the table, and the validator requires 24 rows, 6 orbits, and all 4 syndromes per orbit (`validate_z4_syndrome_record_v0.py:48-56`).

Reconstruction checks are real:

- JAX uses `(quotient_output, syndrome)` lookup and compares recovered representative ids (`z4_syndrome_record_v0_jax.py:135-152`).
- PyTorch uses `torch.func.vmap` over `(orbit, syndrome)` representative codes (`z4_syndrome_record_v0_pytorch.py:132-150`).
- Julia reconstructs representative codes from `orbit_index * 4 + syndrome` (`z4_syndrome_record_v0_julia.jl:103-120`).
- The validator requires bit-exact roundtrip for all three engines and quotient-alone ambiguity 4 (`validate_z4_syndrome_record_v0.py:75-82`).

Independent recomputation from the envelope:

```text
rows = 24
preimage_counts = [4, 4, 4, 4, 4, 4]
syndrome_counts = [6, 6, 6, 6]
state_loss = ln4 = 1.3862943611198906
record_entropy = ln4 = 1.3862943611198906
defect = 0.0
roundtrip_failures = 0
quotient_alone_ambiguity = 4
partial_record_entropy = ln2 = 0.6931471805599453
partial_defect = ln2 = 0.6931471805599453
erased_defect = ln4 = 1.3862943611198906
```

## Regimes and controls

Pass with the Julia caveat above.

The three demanded regimes are present and not byte-identical:

- full record: loss `ln4`, record `ln4`, defect `0`.
- partial one-bit record: loss `ln4`, record `ln2`, defect `ln2`.
- erased record: loss `ln4`, record `0`, defect `ln4`.
- boundary trivial quotient: loss `0`, record `0`, defect `0`.

The validator enforces the expected values and typed labels (`validate_z4_syndrome_record_v0.py:58-72`) and distinct regime hashes (`validate_z4_syndrome_record_v0.py:74`). The envelope reports `regime_hashes_distinct=true` and zero cross-engine deltas for the checked numeric fields.

The shuffled-syndrome control is not decorative: the validator requires failure rate `1.0` for all three engines (`validate_z4_syndrome_record_v0.py:84-86`).

## SMT and solver binding

Pass with binding-strength caveats.

JAX has the strongest SMT lane:

- z3 binds `loss`, `record`, and `defect` to computed row coefficients, checks negated zero-defect conservation, and also checks `loss != record + defect` defect-account controls (`z4_syndrome_record_v0_jax.py:220-253`).
- cvc5 independently binds the same coefficients and polarity matrix (`z4_syndrome_record_v0_jax.py:256-292`).
- Stored controls have full record UNSAT, erased SAT, partial SAT, and defect-account rows UNSAT.

PyTorch binds torch-derived row coefficients into z3/cvc5 and gets the required full UNSAT, erased SAT, and partial SAT polarity (`z4_syndrome_record_v0_pytorch.py:216-269`). Julia Z3 binds graph-derived loss and record coefficients and gets full UNSAT plus erased/partial SAT (`z4_syndrome_record_v0_julia.jl:189-220`).

Named caveat: `CAVEAT_SMT_BINDS_COEFFICIENTS_NOT_RAW_TABLES`. The solvers bind integer log2 coefficients already computed by the host languages. They do not ingest the raw syndrome table or preimage table directly. This is acceptable for this scratch diagnostic because the host computations are inspected and independently recomputed, but future proof-language must not cite the SMT rows as raw-table formalization.

Named caveat: `CAVEAT_PYTORCH_AND_JULIA_SMT_NO_DEFECT_ACCOUNT_ROW`. The JAX z3/cvc5 lane includes explicit `loss == record + defect` negation checks. The PyTorch and Julia solver rows check only `loss == record`/negated equality for the zero-defect conservation polarity. This is sufficient for the Q1 closure, but weaker than a uniform all-engine SMT proof matrix.

## Standard/process checks

Pass at scratch-diagnostic ceiling.

Commands run:

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 \
  system_v6/sims/z4_syndrome_record_v0/validate_z4_syndrome_record_v0.py
# -> ok: true

/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 \
  scripts/validate_three_engine_sim_result.py \
  --require-pytorch \
  --strict-source-backed \
  system_v6/sims/z4_syndrome_record_v0/results/z4_syndrome_record_v0_envelope_results.json
# -> ok: true

/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 \
  scripts/validate_three_engine_sim_result.py \
  --require-pytorch \
  --strict-source-backed \
  --require-tool-intent \
  system_v6/sims/z4_syndrome_record_v0/results/z4_syndrome_record_v0_envelope_results.json
# -> ok: true
```

Standard fields:

- Envelope schema is `three_engine_sim_result_v1`.
- Engine mode is `all_three_full_sims`.
- All three engine results are present.
- `classification="scratch_diagnostic"`.
- `promotion_allowed=false`.
- `formal_admission_allowed=false`.
- `typed_entropy_discipline.all_rows_label="finite_counting_entropy_nats"`.
- Standard envelope helper `build_three_engine_envelope` is used (`z4_syndrome_record_v0_envelope.py:1-18`, `:109-180`).

Tool honesty:

- Graphs.jl is load-bearing for Julia state-loss preimage counts, but not for Julia record entropy. Future citation must say this plainly.
- `torch_geometric` is load-bearing for PyTorch preimage counts via the incidence graph.
- `torch.func` is load-bearing for PyTorch roundtrip/shuffled reconstruction checks.
- z3/cvc5 are load-bearing for coefficient-level conservation/control polarity, not raw-table formal proof.

## Closure decision

`CAVEAT_Q1_RECORD_SIDE_NOT_PACKET_LOCAL_Z4_SYNDROME`: `CLOSED_WITH_CAVEATS`.

What is now earned:

- packet-local Z4 syndrome/preimage table over the pinned six-state family;
- quotient output has computed ambiguity 4 without syndrome;
- quotient output plus syndrome reconstructs representatives exactly;
- state loss comes from quotient preimage cardinalities;
- retained record comes from syndrome distribution in JAX/Python and PyTorch, with independent auditor recomputation from the envelope;
- full/partial/erased/trivial regimes compute the expected `0`, `ln2`, and `ln4` defects;
- z3/cvc5 rows flip with erased/partial controls at coefficient level;
- validators pass with `--require-pytorch`, `--strict-source-backed`, and `--require-tool-intent`.

What is not earned:

- no formal admission;
- no canonical theorem;
- no universal entropy scalar;
- no cross-type entropy conservation outside finite counting state-plus-record bookkeeping;
- no claim that every engine computes record entropy from the syndrome table with equal strength;
- no raw-table SMT formalization.

Future-citation rule:

`manifold_information_throughput_v0` may cite its Z4 conservation row as packet-locally supported only in this form:

> The Z4 quotient loss row has packet-local record support from `z4_syndrome_record_v0`: a 24-row pinned syndrome/preimage table computes state loss `ln4` from quotient preimage cardinalities and retained record `ln4` from syndrome distribution, with quotient-plus-syndrome roundtrip, quotient-alone ambiguity 4, erased defect `ln4`, partial defect `ln2`, and scratch-diagnostic validators green.

Required caveat suffix:

> Ceiling remains `scratch_diagnostic`; solver proof is coefficient-level; Julia record entropy uses literal count vectors rather than deriving counts from the Julia table; do not cite as formal admission, universal entropy, canonical manifold theorem, or cross-type conservation.

## Closure Annotation - Hardening 7481c3fd6

`CAVEAT_JULIA_RECORD_COUNTS_LITERAL`: `CLOSED_BY_HARDENING_7481c3fd6`.

Closure evidence: hardening `7481c3fd6` moved Julia record counts to `counts_from_rows` table-derived counts; the emitted values are reproduced exactly from the row table.

Still open: `CAVEAT_SMT_BINDS_COEFFICIENTS_NOT_RAW_TABLES` and `CAVEAT_PYTORCH_AND_JULIA_SMT_NO_DEFECT_ACCOUNT_ROW`.
