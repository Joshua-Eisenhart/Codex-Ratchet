# Julia Canon Runtime Contract

Status: working runtime contract. This document is subordinate to `AGENTS.md`,
`CODEX.md`, `ENFORCEMENT_AND_PROCESS_RULES.md`,
`LLM_CONTROLLER_CONTRACT.md`, and `LEGO_SIM_CONTRACT.md`. It does not admit
any manifold, bridge, Axis, physics, or formal claim by itself.

## Purpose

Julia Canon is the semantic sidecar for algebra, bracket order, finite carrier
tables, proof tags, and arbitration. The Python runner remains the executable
receipt layer that writes repo result JSON. JAX and PyTorch remain worker
substrates for bounded kernels, witnesses, mirrors, and ablations after the
Julia-owned object and bracket policy are fixed.

The current seed is:

```text
artifact: system_v5/julia_carrier/artifacts/algebra_structure_constants_v1.json
receipt:  system_v5/ops/formal_scouts/results/canon_algebra_artifact_v1_results.json
ceiling:  scratch_diagnostic
```

Do not rebuild this seed by default. Audit it, consume it with hash checks, or
build the next micro-probe around it.

## Required Result Fields

Any result that consumes a Julia Canon artifact should include:

```json
{
  "canon_runtime": {
    "semantic_owner": "julia",
    "artifact_path": "system_v5/julia_carrier/artifacts/algebra_structure_constants_v1.json",
    "artifact_sha256": "...",
    "source_sha256": "...",
    "receipt_path": "system_v5/ops/formal_scouts/results/canon_algebra_artifact_v1_results.json",
    "proof_tag": "...",
    "proof_pass": true,
    "table_version": "...",
    "bracket_convention": "...",
    "consumer_policy": "compute_from_exported_C_tensor_with_fixed_parenthesization"
  },
  "foreign_runtime_manifest": {
    "julia": {"project": "...", "packages": [], "role": "semantic_owner"},
    "jax": {"packages": [], "role": "consumer_or_dynamics_worker"},
    "pytorch": {"packages": [], "role": "consumer_or_support_worker"},
    "tensor_exchange": "dlpack_or_versioned_binary_receipt_only",
    "forbidden_exchange": [".numpy", "np.asarray", "csv", "pickle", "hidden_host_copy"]
  }
}
```

If an existing validator does not yet require these fields, the result can still
be useful as a scratch diagnostic, but it is not a full Canon runtime receipt.

## Consumer Rules

Consumers must verify `source_sha256`, `artifact_sha256`, `proof_tag`,
`proof_pass`, `table_version`, and `bracket_convention` before using the
artifact. They must compute products from exported `C[k][i][j]` and explicit
parenthesization. Hand-typed tables, hidden reassociation, optimizer-as-proof,
or peer-result echo fails the route.

Claim-bearing cross-runtime exchange requires a separate DLPack or versioned
binary tensor receipt. `.numpy()`, `np.asarray`, CSV, pickle, and host-object
bridges may appear only on fenced control or adapter paths with downstream
promotion blocked.

## Ratchet Order

The accepted order for this lane is:

1. Runtime hygiene: prove no hidden host-copy bridge on the claim path.
2. Canon artifact audit: verify the existing Julia algebra artifact and receipt.
3. DLPack or versioned binary exchange micro-probe.
4. JAX consumer equivalence from the exported table and bracket policy.
5. PyTorch consumer equivalence from the exported table and bracket policy.
6. Attractors or dynamics fit probe, with Julia Canon still owning semantics.
7. Proof promotion attempt only after finite table checks and SMT pressure.

Ratchet 2 through 7 do not strengthen Ratchet 1 unless they read and verify the
existing artifact instead of copying its contents.

## Non-Claims

This contract does not make Julia output formal admission. It does not make
JAX/PyTorch agreement proof. It does not make DLPack exchange a manifold
claim. It only defines the minimum runtime receipt shape needed before stronger
gates can even be asked.
