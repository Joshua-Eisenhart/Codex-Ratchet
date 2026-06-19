# BUILD CARD - z4_syndrome_record_v0

Original card copied into this packet:

```text
# BUILD CARD — z4_syndrome_record_v0 (resolve CAVEAT_Q1: the packet-local Z4 record object)

You are codex2 (builder). Repo: /Users/joshuaeisenhart/Codex-Ratchet. Build EVERYTHING inside the new dir system_v6/sims/z4_syndrome_record_v0/ (file-disjoint). NO git add/commit. Copy this card into the packet as build_card.md.

## Why
manifold_information_throughput_v0 (commit 39682dd87) carries CAVEAT_Q1_RECORD_SIDE_NOT_PACKET_LOCAL_Z4_SYNDROME: its conservation row (Z4 quotient loss ln4 = record ln4, defect 0) ASSIGNED record := lens_loss instead of constructing the record. Read its audit_verdict.md first. This packet constructs the record object and recomputes the row honestly.

## Read first
- system_v6/sims/manifold_information_throughput_v0/ (sources + audit_verdict.md, esp. the Q1 section)
- system_v6/sims/ratchet_deep_chain_v0/ (the parent Z4 quotient: generator alpha += pi/2, orbit_order 4)
- system_v6/sims/compression_flow_radiated_record_v0/ (the emitted-record row pattern)
- The typed-entropy discipline (manifold_entropy_ledger_v0, commit a54224476)
- sim-wizard SKILL (TOOL_INTENT_MATRIX mandatory; envelope via scripts/build_three_engine_envelope.py)

## The object
1. Construct the Z4 syndrome table PACKET-LOCALLY: for the pinned state family, enumerate the 4 global-phase representatives per orbit; the syndrome = which representative (2 bits / ln4 nats of counting entropy, COMPUTED from the table's distribution, not asserted).
2. The conservation row recomputed with BOTH sides computed: state_loss_without_record from the quotient map's preimage cardinalities; record_retained from the constructed syndrome distribution; defect = computed difference. The two sides must be computed by DIFFERENT code paths (no shared variable).
3. Reconstruction check: from quotient output + syndrome, reconstruct the input representative exactly (bit-exact roundtrip); from quotient output alone, reconstruction must FAIL with computed ambiguity 4.
4. SMT: z3+cvc5 bind the COMPUTED preimage counts and syndrome entropy (negated conservation UNSAT); erased-record control flips to SAT with computed defect ln4; partial-record control (1 of 2 bits) yields computed defect ln2 — three distinct computed regimes, never byte-identical.

## Controls: erased-record (defect ln4), partial-record (defect ln2), shuffled-syndrome (reconstruction failure rate computed), trivial-quotient boundary (loss 0, record 0).

## Engineering contract
Same as repo standard: three engines (Julia reference w/ real aligned packages + package_observables, JAX, PyTorch), TOOL_INTENT_MATRIX in build_card.md, envelope ONLY via scripts/build_three_engine_envelope.py, validate --require-pytorch --strict-source-backed ok:true, classification scratch_diagnostic, promotion_allowed=false, typed entropy labels on every row, positive+negative+boundary sections. End by listing validator commands + ok statuses.
```

## TOOL_INTENT_MATRIX

| engine | load-bearing tool | exact observable/proof | gates |
| --- | --- | --- | --- |
| Julia | Graphs | `Graphs.SimpleDiGraph` quotient-to-representative incidence; in-degree preimage counts are the state-loss source | quotient preimage counts, quotient-alone ambiguity, all_pass |
| Julia | Z3 | `Z3.Solver` binds computed integer log2 coefficients for full conservation and erased-record SAT flip | SMT conservation, erased control, all_pass |
| JAX/Python | sympy | `sp.log`, `sp.Rational`, and exact simplification produce typed counting-entropy expressions from table-derived distributions | typed entropy rows, defect rows |
| JAX/Python | z3 | `z3.Solver` binds computed preimage and syndrome entropy coefficients | full UNSAT, erased SAT, partial SAT, trivial boundary |
| JAX/Python | cvc5 | `cvc5.Solver` independently binds the same computed coefficients | full UNSAT, erased SAT, partial SAT, trivial boundary |
| PyTorch | torch_geometric | `torch_geometric.data.Data` encodes quotient-to-representative support graph; graph degrees compute preimage counts | quotient preimage counts, ambiguity 4 |
| PyTorch | torch.func | `torch.func.vmap` applies the roundtrip reconstruction check across encoded representatives | reconstruction success/failure rates |
| PyTorch | sympy | exact typed counting-entropy expressions from torch-derived counts | typed entropy rows, defect rows |
| PyTorch | z3 | solver control over torch-derived coefficients | full UNSAT and erased/partial controls |
| PyTorch | cvc5 | independent solver control over torch-derived coefficients | full UNSAT and erased/partial controls |

Ceiling: `classification=scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`.

Engine mode: `all_three_full_sims`.

Typed entropy convention: all finite quotient/record rows are `finite_counting_entropy_nats` with `log_base=e`; no differential, von Neumann, or cross-type entropy is summed here.

## Hardening round 1 - CAVEAT_JULIA_RECORD_COUNTS_LITERAL

Date: 2026-06-11.

Addressed caveat: `CAVEAT_JULIA_RECORD_COUNTS_LITERAL`.

Change: the Julia leg now derives full, erased, partial, and trivial record count vectors from the constructed 24-row syndrome table through a Julia-side counting pass over row values. The state-loss side remains the independent `Graphs.SimpleDiGraph` preimage/outdegree computation path.

Derived Julia record counts after rerun:

- full record: `[6, 6, 6, 6]`
- erased record: `[24]`
- partial one-bit record: `[12, 12]`
- trivial quotient record: `[24]`

Validator statuses:

- `JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier system_v6/sims/z4_syndrome_record_v0/z4_syndrome_record_v0_julia.jl` -> `ok:true`
- `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/z4_syndrome_record_v0/z4_syndrome_record_v0_envelope.py` -> `ok:true`
- `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/z4_syndrome_record_v0/validate_z4_syndrome_record_v0.py` -> `ok:true`
- `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed --require-tool-intent system_v6/sims/z4_syndrome_record_v0/results/z4_syndrome_record_v0_envelope_results.json` -> `ok:true`

Numeric regimes unchanged: full defect `0`, erased defect `ln4`, partial defect `ln2`, trivial defect `0`.
