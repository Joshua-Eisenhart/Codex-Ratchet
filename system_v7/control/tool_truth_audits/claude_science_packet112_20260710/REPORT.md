# Claude Science Packet 112 Tool-Truth Audit

Status: mechanically green external harness; failed as a multi-engine evidence
estate.

## Exact Inventory

The isolated packet contains 144 Python scripts in `sims_and_scripts`:

| import root | source files | share of 144 |
|---|---:|---:|
| NumPy | 136 | 94.4% |
| SciPy | 66 | 45.8% |
| JAX | 2 | 1.4% |
| Torch | 1 | 0.7% |
| Julia sources | 0 | 0% |

Counts overlap. This is substantially more NumPy-heavy than the advisory WebUI
estimate.

None of the 144 sources declares `TOOL_MANIFEST` or
`TOOL_INTEGRATION_DEPTH`. None of the 72 result JSONs carries `tool_calls`,
`claim_path_tools`, either tool declaration, or top-level `all_pass`.

The canonical isolated `143 pass / 0 fail / 0 skip` rerun is real as a local
harness event. The harness predominantly decides success through expected
stdout `contains` and regex/approximate matches. It is not structured evidence
that Julia/JAX/PyTorch QIT engines performed nonredundant work.

## Engine Files

Only these Python sources import an engine framework:

- `flux_nesting_ablation_jax.py`
- `manifold_build_ladder.py`
- `quantum_hopfield_memory_sim.py`

They still lack function-level receipts in the packet result schema. Their
presence cannot be multiplied across the other 141 scripts.

## Verdict

```text
NUMPY_DOMINATED_UNRECEIPTED_EXTERNAL_SCRIPT_ESTATE_NOT_A_REAL_MULTI_ENGINE_RUN
```

Claim ceiling:

```text
packet_112_143_0_0_is_a_local_console_harness_rerun_not_evidence_that_qit_or_dual_ratchet_engines_ran
```

This does not mean every NumPy calculation is false. It means the packet does
not establish engine execution, cross-runtime corroboration, learned dynamics,
unique stage intelligence, perception, object formation, or cross-domain
unification.

## Repair Order

1. Replace console-string success with structured, closed result receipts.
2. Make Julia the semantic owner where algebra, QIT, attractor, or formal
   dynamics require its native packages.
3. Use JAX for batched parameter/state/control sweeps with qualified API
   receipts and deterministic reruns.
4. Use PyTorch only for a nonredundant graph/autograd/learned role and test that
   removing it demotes the claim.
5. Require positive, boundary, erased, and mutation controls for every
   load-bearing API.
6. Keep NumPy/SciPy as baseline/control machinery unless a bounded classical
   claim specifically makes them load-bearing.
