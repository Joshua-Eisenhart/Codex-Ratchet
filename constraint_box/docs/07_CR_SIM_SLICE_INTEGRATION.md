# CR sim-slice integration

This document defines the first ConstraintBox-owned bridge to the external
Codex-Ratchet (CR) simulation estate. It is an execution and evidence
boundary, not a claim that ConstraintBox validates CR.

## Registered slice

The controller reads `config/cr_sim_slice_v1.json`. A profile expands only to
registered source paths; callers cannot provide arbitrary shell commands,
verdicts, tolerances, or result paths.

| group | registered source | engine | controller level |
| --- | --- | --- | --- |
| `foundation_r1_f01_finitude` | Julia, JAX, PyTorch lanes and three-engine envelope | Julia/Python | source invocation, receipt capture, JSON recheck; envelope is peer-result aware |
| `foundation_r1_n01_noncommutation` | Julia, JAX, PyTorch lanes and three-engine envelope | Julia/Python | source invocation, receipt capture, JSON recheck; envelope is peer-result aware |
| `cr_gksl_fixture` | `system_v7/.../nonunitality_theorem_sim.py` plus CB fixture derivation | Python | source invocation/stdout capture; derivation receipt rechecked |

The three-engine envelope remains a CR artifact. CB can invoke it and check its
declared receipt shape, but it does not become the semantic authority for the
envelope. The CR source tree, its package environment, and its result files are
recorded as external inputs.

## Receipt contract

`constraintbox cr-slice` creates a fresh run directory and writes one receipt
with, for every selected entry:

* source path and SHA-256;
* selected Python or Julia runtime metadata;
* exact argv, return code, elapsed time, bounded stdout/stderr previews and
  digests;
* declared integration level and peer-result dependency;
* result path/digest and a controller-side recheck of `all_pass`, provenance,
  and `promotion_allowed:false` when the entry declares JSON output.

Missing runtimes are `PARKED`; a non-zero source, timeout, malformed result, or
result/source mismatch is `FAIL`. The receipt always carries
`external_system:true`, `kernel_membership:EXTERNAL_NOT_CB_KERNEL`,
`cr_truth_claim:false`, and `promotion_allowed:false`.

This is deliberately not a whole-estate inventory. It is the smallest useful
source-addressed slice that exercises the current foundation lanes and the
real CB-facing CR fixture. More engines or workloads must be added as explicit
manifest entries with their own producer, result, and gate contract.
