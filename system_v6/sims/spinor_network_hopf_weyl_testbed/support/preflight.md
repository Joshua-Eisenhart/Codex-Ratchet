# Spinor-Network Testbed Preflight

Mechanical preflight only. Repo treated read-only; reuse assets were fresh-run from relocated copies under `/tmp/found/sn_preflight_reuse` to avoid touching repo result files.

## PASS/FAIL Table

| Check | Status | Path / command | Value |
|---|---:|---|---|
| kingdon capability receipt | PASS | `system_v4/probes/a2_state/sim_results/kingdon_capability_results.json` | `summary.all_pass=true` |
| pyg isolated capability receipt | FAIL | `system_v4/probes/a2_state/sim_results/sim_capability_pyg_isolated_results.json` | Receipt has no `summary.all_pass`; all `positive.*.pass` entries inspected were `true` |
| e3nn capability receipt | PASS | `system_v4/probes/a2_state/sim_results/e3nn_capability_results.json` | `summary.all_pass=true` |
| e3nn_jax capability receipt | PASS | `system_v4/probes/a2_state/sim_results/e3nn_jax_capability_results.json` | `summary.all_pass=true` |
| gudhi capability receipt | PASS | `system_v4/probes/a2_state/sim_results/gudhi_capability_results.json` | `summary.all_pass=true` |
| toponetx capability receipt | PASS | `system_v4/probes/a2_state/sim_results/toponetx_capability_results.json` | `summary.all_pass=true` |
| xgi capability receipt | PASS | `system_v4/probes/a2_state/sim_results/xgi_family_hypergraph_results.json` | `summary.all_pass=true` |
| geomstats capability receipt | PASS | `system_v4/probes/a2_state/sim_results/geomstats_capability_results.json` | `summary.all_pass=true` |
| sympy capability receipt | PASS | `system_v4/probes/a2_state/sim_results/tool_capability_sympy_results.json` | `summary.all_pass=true` |
| itensors capability receipt | PASS | `system_v4/probes/a2_state/sim_results/itensors_capability_results.json` | `summary.all_pass=true` |
| quimb capability receipt | PASS | `system_v4/probes/a2_state/sim_results/quimb_capability_results.json` | `summary.all_pass=true` |
| z3 capability receipt | PASS | `system_v4/probes/a2_state/sim_results/z3_capability_results.json` | `summary.all_pass=true` |
| cvc5 capability receipt | PASS | `system_v4/probes/a2_state/sim_results/cvc5_capability_results.json` | `summary.all_pass=true` |
| julia_carrier_algebra capability receipt | PASS | `system_v4/probes/a2_state/sim_results/julia_carrier_algebra_capability_results.json` | `summary.all_pass=true` |
| julia_dynamics capability receipt | PASS | `system_v4/probes/a2_state/sim_results/julia_dynamics_capability_results.json` | `summary.all_pass=true` |
| jax_dynamics capability receipt | PASS | `system_v4/probes/a2_state/sim_results/jax_dynamics_capability_results.json` | `summary.all_pass=true` |
| jax_algebra capability receipt | PASS | `system_v4/probes/a2_state/sim_results/jax_algebra_capability_results.json` | `summary.all_pass=true` |
| terrain law conventions | PASS | `system_v5/READ ONLY Reference Docs/terrain math.md:78-83` | Quoted below |
| terrain torus/connection/loops | PASS | `system_v5/READ ONLY Reference Docs/terrain math.md:30-33` | Quoted below |
| fresh-run Julia reuse asset | PASS | `/tmp/found/sn_preflight_reuse/clifford_torus_nested_hopf_foliation.jl` | exit `0`; `parity_status=compared`; `parity_max_diff=1.0658141036401503e-13`; `within_1e-9=true` |
| fresh-run JAX reuse asset | PASS | `/tmp/found/sn_preflight_reuse/jax_clifford_torus_nested_hopf_foliation.py` | exit `0`; `parity_max_diff=1.0658141036401503e-13`; `within_1e-9=true`; `max_diff_key=volume_estimate` |
| Julia strict carrier Quaternions import | PASS | `julia --project=system_v5/julia_carrier -e 'using Quaternions; println("Quaternions import OK")'` | `Quaternions import OK` |
| Julia strict carrier Octonions import | PASS | `julia --project=system_v5/julia_carrier -e 'using Octonions; println("Octonions import OK")'` | `Octonions import OK` |
| canonical Python imports | PASS | `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -c 'import kingdon, torch_geometric, e3nn, e3nn_jax, gudhi, toponetx, xgi, quimb; print("python imports OK")'` | `python imports OK` |

## Terrain Reference Quotes

`system_v5/READ ONLY Reference Docs/terrain math.md:30-33`

```text
| torus family | \(T_\eta^s=\{\psi_s(\phi,\chi;\eta):\phi,\chi\in[0,2\pi)\}\subset S_s^3\) |
| connection | \(A=-i\,\psi_s^\dagger d\psi_s=d\phi+\cos(2\eta)\,d\chi\) |
| inner loop | \(\gamma_{\mathrm{in}}^s(u)=\psi_s(\phi_0+u,\chi_0;\eta_0)\) |
| outer loop | \(\gamma_{\mathrm{out}}^s(u)=\psi_s(\phi_0-\cos(2\eta_0)u,\chi_0+u;\eta_0)\) |
```

`system_v5/READ ONLY Reference Docs/terrain math.md:78-83`

```text
| `Ne / Vortex` | \(X_{Ne,L}(\rho)=-i[H_L,\rho]\) |
| `Ne / Spiral` | \(X_{Ne,R}(\rho)=-i[H_R,\rho]\) |
| `Ni / Pit` | \(X_{Ni,L}(\rho)=\gamma_{Ni,L}D[\sigma_-](\rho)-i\,\varepsilon_{Ni,L}[H_L,\rho]\) |
| `Ni / Source` | \(X_{Ni,R}(\rho)=\gamma_{Ni,R}D[\sigma_+](\rho)-i\,\varepsilon_{Ni,R}[H_R,\rho]\) |
| `Si / Hill` | \(X_{Si,L}(\rho)=-i[\omega_L\,\hat m_L\!\cdot\!\vec\sigma,\rho]+\kappa_L\bigl(P_+^L\rho P_+^L+P_-^L\rho P_-^L-\rho\bigr)\) |
| `Si / Citadel` | \(X_{Si,R}(\rho)=-i[\omega_R\,\hat m_R\!\cdot\!\vec\sigma,\rho]+\kappa_R\bigl(P_+^R\rho P_+^R+P_-^R\rho P_-^R-\rho\bigr)\) |
```

## Command Notes

- Canonical Python env from `Makefile`: `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3`.
- Reuse asset temp outputs:
  - `/tmp/found/sn_preflight_reuse/clifford_torus_nested_hopf_foliation_julia_results.json`
  - `/tmp/found/sn_preflight_reuse/clifford_torus_nested_hopf_foliation_jax_results.json`
- No `system_v6/sims/` access or writes were needed.
