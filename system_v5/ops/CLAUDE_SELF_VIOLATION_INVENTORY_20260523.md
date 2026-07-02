# Claude Self-Reported Violation Inventory

Date: 2026-05-23

Status: verified inventory supplement. This file records the self-reported
violation list supplied by the Claude context and the filesystem checks run
afterward. It is not a scientific evidence document.

Supersession note: this is a historical supplement to the damage audit. Some
working-tree existence rows below were later archived or restored. For current
cleanup state, use `EXPANDED_QUARANTINE_FULL_INVENTORY_20260523.json`,
`EXPANDED_QUARANTINE_SURFACE_CLASSIFICATION_20260523.md`, and
`EXPANDED_QUARANTINE_ACTION_MANIFEST_20260523.json`.

Related recovery files:

- `system_v5/ops/FORMAL_GROK_BOUNDARY_DAMAGE_AUDIT_20260523.md`
- `system_v5/ops/FORMAL_GROK_BOUNDARY_QUARANTINE_MANIFEST_20260523.json`
- `system_v5/ops/FORMAL_GROK_SIM_REDO_PLAN_20260523.md`
- `system_v5/ops/CROSS_LANE_SIM_INDEPENDENCE_RESET_20260523.md`

## Verification Summary

The self-inventory is materially useful, but it is not proof for every causal
claim it makes. Treat it as a process confession plus a path list that must be
checked against Git and file contents.

Verified from repo state:

- the Tier 1 cross-lane files/directories exist as current untracked
  quarantine candidates;
- the named spinor/twistor files are tracked-clean in the working tree but were
  changed in recent commits;
- the named external audit receipt directories exist under canonical ops paths;
- the named result JSONs exist in the generated/ignored result estate.

Not fully proven by the inventory alone:

- that every tracked-clean spinor/twistor edit was directly caused by
  cross-lane evidence import;
- that every audit-directory receipt is scientifically contaminating rather than
  process/advisory contamination;
- that the informal `grok_sim` project is file-level dirty.

The strongest recovery fact remains: some contaminated or suspect files are no
longer dirty in the working tree because they are already committed in recent
history.

Recent commits touching the tracked spinor/twistor violation surface:

```text
1d562a59d formal-scouts: add bounded stack gap scouts
51c15399e ops: checkpoint external audit receipts
35fbd0847 formal-scout: tighten spinor twistor claim audits
9e4be9f28 formal-scout: harden spinor twistor probes
67e41aab7 formal-scout: add source-aligned qit probes
05a26933d docs: add qit source authority audits
```

Implication: recovery cannot be only `git restore` of the dirty working tree.
It needs committed-history quarantine or a chosen clean baseline.

## Tier 1 - Direct Cross-Project Evidence Imports

These are high-confidence quarantine candidates.

| File | Current state | Verification | Recovery status |
|---|---|---|---|
| `system_v5/ops/CROSS_LANE_PHI0_KILL_CONVERGENCE_20260523.md` | untracked | exists, mtime 2026-05-23 08:24:37 | quarantine / advisory-only or delete after archive |
| `system_v5/ops/formal_scouts/sim_section_connection_cluster_consolidated_audit_probe.py` | untracked | exists, mtime 2026-05-23 08:03:41 | quarantine; do not admit as formal scout |
| `system_v5/ops/formal_scouts/sim_64_site_environment_contraction_section_connection_close_probe.py` | untracked | exists, mtime 2026-05-23 08:15:37 | quarantine; do not admit as formal scout |
| `system_v5/ops/formal_scouts/sim_64_site_environment_contraction_section_connection_close_v2_probe.py` | untracked | exists, mtime 2026-05-23 08:22:25 | quarantine; do not admit as formal scout |
| `system_v5/ops/external_audits/three_artifact_run_20260523/` | untracked directory | contains `grok_audit_a1/a2/a3/a3v2.json` | quarantine advisory receipt; not formal evidence |

## Tier 2 - Cross-Lane Prose In Existing Formal Docs

| File | Current state | Verification | Recovery status |
|---|---|---|---|
| `system_v5/ops/SPINOR_TWISTOR_ENTANGLEMENT_INFORMATION_NETWORK_AUDIT_20260522.md` | tracked clean | recent commits touched it; not dirty now | committed-history quarantine; compare against clean baseline |

The self-report says this doc was edited heavily through R6-R13 and cross-lane
phase. Because it is tracked-clean now, any remediation must be via commit-range
review or reset to a pre-contamination baseline, not ordinary working-tree
restore.

## Tier 3 - Bridge Probe Extensions Shaped By Cross-Lane Evidence

| File | Current state | Verification | Recovery status |
|---|---|---|---|
| `system_v5/ops/formal_scouts/sim_spinor_twistor_xi_cut_phi0_bridge_candidate_probe.py` | tracked clean | recent commits touched it; result regenerated 2026-05-23 04:57:59 | committed-history quarantine; rebuild independently |

This file should not be used as a trusted formal bridge basis until a clean
source comparison decides which parts predate contamination and which parts must
be rebuilt.

## Tier 4 - Earlier Formal-Scout Structural Edits

| File | Current state | Verification | Recovery status |
|---|---|---|---|
| `system_v5/ops/formal_scouts/sim_two_root_constraint_extended_stack_validity_probe.py` | tracked clean | recent commits touched it; result regenerated 2026-05-23 00:28:36 | committed-history quarantine / re-audit |
| `system_v5/ops/formal_scouts/sim_spinor_twistor_entanglement_information_network_root_gate_probe.py` | tracked clean | recent commits touched it; result regenerated 2026-05-23 04:57:53 | committed-history quarantine / re-audit |
| `system_v5/ops/formal_scouts/sim_spinor_twistor_network_clifford_tensor_boundary_next_wave_probe.py` | tracked clean | recent commits touched it; result regenerated 2026-05-23 00:28:38 | committed-history quarantine / re-audit |
| `system_v5/ops/formal_scouts/sim_spinor_twistor_flux_basin_binding_probe.py` | tracked clean | recent commits touched it; result regenerated 2026-05-23 04:57:54 | committed-history quarantine / re-audit |

These may contain useful repairs, but they were authored inside the same
methodological failure mode. They should be treated as suspect until independently
rebuilt or reviewed from a clean baseline.

## Tier 5 - Generated Result Files

Confirmed present result files named in the self-inventory:

```text
system_v5/ops/formal_scouts/results/spinor_twistor_xi_cut_phi0_bridge_candidate_probe_results.json
system_v5/ops/formal_scouts/results/spinor_twistor_xi_cut_phi0_bridge_K300_power_confirm.json
system_v5/ops/formal_scouts/results/two_root_constraint_extended_stack_validity_probe_results.json
system_v5/ops/formal_scouts/results/spinor_twistor_entanglement_information_network_root_gate_probe_results.json
system_v5/ops/formal_scouts/results/spinor_twistor_network_clifford_tensor_boundary_next_wave_probe_results.json
system_v5/ops/formal_scouts/results/spinor_twistor_flux_basin_binding_probe_results.json
system_v5/ops/formal_scouts/results/64_site_environment_contraction_section_connection_close_probe_results.json
system_v5/ops/formal_scouts/results/64_site_environment_contraction_section_connection_close_v2_probe_results.json
system_v5/ops/formal_scouts/results/section_connection_cluster_consolidated_audit_probe_results.json
```

Recovery status: quarantine all listed result JSONs. Do not feed them to
readiness, validators, or classifiers except as contaminated-history examples.

## Tier 6 - External Audit Receipt Directories

Confirmed present under `system_v5/ops/external_audits/`:

```text
spinor_twistor_bridge_round7_20260522/
spinor_twistor_bridge_round8_20260522/
spinor_twistor_bridge_round9_20260522/
spinor_twistor_bridge_round10_20260522/
spinor_twistor_bridge_round11_20260522/
spinor_twistor_bridge_round12_20260522/
spinor_twistor_bridge_round13_20260522/
qit_fep_axis0_path_integral_reaudit_20260523T000000Z/
qit_fep_axis0_path_integral_reaudit_20260523T060000Z/
three_artifact_run_20260523/
```

Recovery status: advisory-only quarantine. These may be retained for process
postmortem, but they cannot support formal scientific claims.

## Tier 7 - Ephemeral `/tmp` Files

Not audited because they are outside the repository. Treat them as process
history only. Do not reconstruct evidence from them.

## Correction To Earlier Damage Audit

The earlier damage audit correctly found no recent Git-visible writes from
`grok_sim` into formal surfaces. This inventory adds that contamination also
exists in committed formal history, especially around spinor/twistor and audit
receipt checkpoint commits.

Therefore recovery needs two lanes:

1. **Working-tree cleanup** for untracked/dirty quarantine files.
2. **Committed-history review** to choose a pre-contamination source baseline for
   spinor/twistor and bridge probes.

## Required Next Recovery Step

Before any formal rerun:

1. Choose a clean baseline commit for spinor/twistor and bridge surfaces.
2. Produce a path allowlist of files to keep.
3. Exclude all quarantined result JSONs from validators/indexers.
4. Rebuild the first formal target from the clean baseline, not from the
   tracked-clean contaminated files.
