---
name: pytorch-sim
description: Use when writing or auditing the PyTorch side of a Codex Ratchet sim so PyTorch graph/network/autograd/existing machinery can be first-class when scoped, while never replacing Julia Canon arbitration.
---

MIRROR: authoritative copy is .claude/skills/pytorch-sim/SKILL.md; sync direction .claude -> codex_skills.

# PyTorch Sim

PyTorch is first-class when the claim path needs graph/network/autograd/existing torch machinery. Its strongest roles are `torch_geometric` message passing, `torch.func`/`functorch` transforms, differentiable geometric computation, torch-backed geometry/equivariance, ODE/candidate tools, and proof checks over torch-derived finite values. PyTorch is not the semantic arbiter for Julia Canon artifacts: bare array-value agreement is lower authority than Julia-arbitrated Canon evidence. For explicit all-three envelopes or user-directed all-three tasks, PyTorch is required; for other packets, scope it when a real torch-native role exists and mark it `not_scoped` when it does not.

## Step 1: Use Proper Environment

Before package-dependent work or any install proposal, read
`system_v5/docs/RUNTIME_LIBRARY_LOCATION_MAP_20260608.md` and run:

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/codex_runtime_env_doctor.py --skip-julia
```

If a package is absent from bare `python3` but present in the canonical venv,
it is not missing. If it is absent from the canonical venv, create an install
intent instead of installing.

Run with the Codex Ratchet Python:

```bash
env NUMBA_CACHE_DIR=/private/tmp/codex_numba_cache /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 <script.py>
```

Validation: command exits 0.

On failure: mark PyTorch blocked or not_scoped; do not replace it with numpy, and do not classify a PyTorch-scoped or all-three result as passing.

## Step 1a: Package Risk Guard

Current 2026-06-08 local import status:

- `torch`, `torch_geometric`, `torchdiffeq`, `xitorch`, `cvxpylayers`, `torch_ga`, `geomstats`, `e3nn`, `z3`, and Python `cvc5` are usable candidates when a micro-receipt proves the specific API surface.
- `dgl`, `torch_scatter`, and `torch_sparse` are not installed in the current Python environment. `torchode`, `torchdiffeq`, `xitorch`, and `cvxpylayers` import in the current env but remain candidate/witness tools unless exact finite/SMT/interval/Julia Canon certification discharges the claim.
- Do not add `dgl`, `torch_scatter`, `torch_sparse`, `pyg-lib`, `torch-cluster`, or `torch-spline-conv` as assumed requirements without a pinned wheel/container receipt.

`torchdiffeq`, `xitorch`, `cvxpylayers`, and training frameworks are candidate or witness generators, not proof backbones. A PyTorch optimization result must be certified by exact finite checks, SMT/cvc5/Z3, interval/reachability/SOS, or Julia Canon before it can support a stronger claim.

## Step 2: Set Geomstats Backend

If using `geomstats`, set the backend before import:

```bash
env GEOMSTATS_BACKEND=pytorch NUMBA_CACHE_DIR=/private/tmp/codex_numba_cache /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 <script.py>
```

Validation: a backend check prints or records `geomstats.pytorch`, and distances are torch tensors.

On failure: geomstats is not a torch-side check and cannot be load-bearing for PyTorch.

## Step 2a: Tool-Integration Receipt Rule

`load_bearing` = the tool output gates a control, quotient, proof, `all_pass`
condition, divergence value, or demotion condition. A real import/call that
only emits a side readout is `supportive`, NOT `load_bearing`.

Every claimed `load_bearing` tool emits a function-level `tool_calls` entry:
`{tool, qualified_api/function, input_object, output_object, positive_case,
negative/erased_control, boundary_case, demotion_condition, gates: which of
all_pass/divergence/quotient/proof}`. A `load_bearing` claim with no gate is
downgraded to `supportive`.

PyTorch API footguns:

- Set `GEOMSTATS_BACKEND=pytorch` before importing `geomstats`; record the
  backend and torch tensor return type if geomstats is claimed.
- PyG `MessagePassing` earns the network-engine `load_bearing` label only when
  the routed aggregate carries the noncommutative octonion edge update and that
  output gates a control, quotient, divergence value, or `all_pass`.

## Step 3: Make A Tool Load Bearing

Canon-table consumer rule: if the PyTorch lane consumes a Julia algebra artifact, load `C[k][i][j]`, `table_version`, `bracket_convention`, and `proof_tag` from the artifact. Implement products as explicit fixed-order contractions over `C`; never re-associate `(a*b)*c` to `a*(b*c)` unless the proof tag covers that exact case. Do not use `.numpy()`, `np.asarray`, CSV, pickle, or host-object serialization on the claim/data path. DLPack or an explicitly versioned binary tensor bridge requires its own bridge receipt before it becomes claim-bearing.

Use at least one distinct PyTorch-side tool:

- `torch_ga` for torch-native differentiable geometric algebra and autograd through GA objects.
- `clifford` for geometric algebra, rotors, gamma matrices, chirality checks.
- `geomstats` with torch backend for manifold distances/geodesics.
- `e3nn` for SO(3)/SU(2) irreps and equivariance.
- `torch_geometric` for graph message passing.
- `torch.func` or `functorch` for batched Jacobians/Hessians.
- `z3`, `cvc5`, or `sympy` as crossover proof/symbolic checks on torch-derived finite values.

Validation: `aligned_packages_load_bearing` contains at least one of those packages, and a differentiable claim uses `torch_ga`, `torch.func`, or `functorch` instead of plain tensor arithmetic.

On failure: PyTorch is decorative. A PyTorch-scoped or all-three packet is blocked until a real torch-side role exists; a non-PyTorch packet records `not_scoped_by_mode`.

## Step 4: Emit Engine Receipt

Result fragment:

```json
"pytorch": {
    "ran": true,
    "source_path": "...",
    "packages_used": ["torch", "torch_ga", "geomstats", "e3nn"],
    "aligned_packages_load_bearing": ["torch_ga", "torch.func"],
    "reads_peer_result": false
}
```

Validation: PyTorch does not read Julia or JAX output as input for its own result.

On failure: do not pass the result as a PyTorch-scoped or all-three envelope; use `--require-pytorch` only once the PyTorch leg is real and mode-declared.

## DEPRECATED / DO-NOT-USE

Deprecation authority: capability_matrix receipts + owner 2026-06-09; a deprecated tool needs a passing capability probe + owner sign-off to return.

| Status | Tools / surfaces | Rule |
| --- | --- | --- |
| REPLACE | `torch_ga` (0.0.6 hobby-tier; `kingdon` under test as successor), `clifford` (design-frozen) | Do not use for new PyTorch sim claim paths. `clifford` is legacy fallback only. |
| PRUNE FROM PROMISES | `cma`, `deap`, `evotorch`, `optuna`, `pymoo`, `ribs`, `datasketch`, `hdbscan`, `hypothesis`, `pynndescent`, `sklearn`, `umap`, `igraph` | No matrix cell. |
| UNCHANGED RULE | `numpy`, `scipy`, `mpmath` | Control-lane only; never claim-path or load-bearing. |
