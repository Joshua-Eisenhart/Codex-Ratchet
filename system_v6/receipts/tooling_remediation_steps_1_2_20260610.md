# Tooling Remediation Steps 1-2 Report

Date: 2026-06-10

Scope: queue steps 1 and 2 from `system_v6/receipts/tooling_presumption_audit_20260610.md`.

Bottom line: Step 1 demoted failing Python tool declarations to `supportive`; Step 2 added Julia capability probes and result JSONs for the requested packages. No scientific claim strings or claim values were intentionally changed.

## Step 1 Demotions

| Packet | File leg(s) | Demoted from `load_bearing` to `supportive` |
|---|---|---|
| `bloch_root_admissibility_discriminator_v0` | JAX, PyTorch, envelope metadata | `jax`, `jax.numpy`, `torch.func` |
| `geo_s1_exact_closure_v0` | PyTorch | `torch.func` |
| `geo_s1_finite_phase_lens_v0` | JAX, PyTorch | `jax`, `torch.func` |
| `geo_s1_five_qubit_safety_margin_exact_v0` | none | no demotion; envelope rerun only |
| `geo_s1_four_qubit_support_exact_v0` | PyTorch | `torch.func` |
| `geo_s1_negative_models_v0` | JAX, PyTorch | `jax`, `torch.func` |
| `geo_s1_quaternion_model_v0` | JAX, PyTorch | `jax`, `torch.func` |
| `geo_s1_scaling_stress_678q_exact_v0` | JAX | `jax`, `jax.numpy` |
| `geo_s1_spinor_hopf_free_v0` | JAX, PyTorch | `jax`, `torch.func` |
| `geo_s1_three_qubit_floor_exact_v0` | PyTorch | `torch.func` |
| `geo_s1_two_qubit_boundary_exact_v0` | none | no demotion; envelope rerun only |
| `geo_s2_connection_flux_foliation_v0` | PyTorch | `torch.func` |
| `geo_s2_negative_models_v0` | JAX, PyTorch | `jax`, `torch.func` |
| `geo_s3_density_observable_v0` | PyTorch | `torch.func` |
| `geo_s4_operator_stage_v0` | PyTorch | `torch.func` |
| `geo_s5_terrain_flows_v0` | PyTorch | `torch.func` |
| `geo_s6_stacked_flows_hopf_v0` | PyTorch | `torch.func` |
| `geo_s7_discrete_refinement_v0` | PyTorch | `torch.func` |
| `mct_nonassoc_weld_packet_v0` | JAX | `jax`, `jax.numpy` |

Metadata updated with the demotion:

- `TOOL_INTEGRATION_DEPTH`
- `TOOL_MANIFEST` reason text where it said load-bearing for the demoted API
- `aligned_packages_load_bearing`
- `claim_path_tools`
- demoted `torch.func` `tool_calls` gate lists, where present

## Step 2 Julia Capability Probes

Probe runner:

- `system_v6/probes/julia/julia_load_bearing_capability_probes.jl`

Result JSONs:

| Tool | Result JSON | Active project | Result |
|---|---|---|---|
| `Symbolics` | `system_v6/probes/julia/results/symbolics_capability_results.json` | `system_v5/julia_carrier/Project.toml` | `all_pass:true` |
| `IntervalArithmetic` | `system_v6/probes/julia/results/intervalarithmetic_capability_results.json` | `~/.julia/environments/codex-ratchet-tensorkit-v1.12/Project.toml` | `all_pass:true` |
| `DifferentialEquations` | `system_v6/probes/julia/results/differentialequations_capability_results.json` | `system_v5/julia_carrier/Project.toml` | `all_pass:true` |
| `CliffordAlgebras` | `system_v6/probes/julia/results/cliffordalgebras_capability_results.json` | `system_v5/julia_carrier/Project.toml` | `all_pass:true` |
| `Quaternions` | `system_v6/probes/julia/results/quaternions_capability_results.json` | `system_v5/julia_carrier/Project.toml` | `all_pass:true` |
| `Z3` | `system_v6/probes/julia/results/z3_capability_results.json` | `system_v5/julia_carrier/Project.toml` | `all_pass:true` |

Each probe result includes positive, negative/erased, boundary, and demotion cases. `IntervalArithmetic` is not declared by the strict carrier project, so its passing receipt is explicitly scoped to the documented optional `@codex-ratchet-tensorkit-v1.12` project.

## Verification Outcomes

Commands/checks run:

- `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/codex_runtime_env_doctor.py`
  - `ok=True install_state=stable_observed`
- strict Julia carrier import check
  - `Symbolics`, `DifferentialEquations`, `CliffordAlgebras`, `Quaternions`, `Z3` loaded in carrier
  - `IntervalArithmetic` did not load in carrier and was probed in the optional project
- `scripts/verify_load_bearing_has_capability_probe.py --sim <changed source>`
  - 23 changed JAX/PyTorch files checked
  - failures: 0
- changed JAX/PyTorch leg reruns
  - 23 files rerun
  - failures: 0
- audited packet envelope reruns
  - 19 envelopes rerun
  - failures: 0
- packet-local exact-strength validators
  - 8 validators rerun
  - all returned `ok:true`
- claim-value stability comparator
  - 42 result JSONs checked against `HEAD`
  - after stripping metadata/hashes/runtime/tool-depth fields, scientific-value diffs: 0

## Boundaries

No stage-rebuild work was performed. Queue items 3-7 remain separate.

