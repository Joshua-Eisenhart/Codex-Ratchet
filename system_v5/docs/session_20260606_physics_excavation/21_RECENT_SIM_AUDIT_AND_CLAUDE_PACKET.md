# Recent Sim Audit And Claude Packet

Status: Codex live audit packet for Claude follow-on.  
Claim ceiling: selected rows are `formal_scout` or `scratch_diagnostic` only. No physics, `M(C)`, Axis0, QIT-engine, SM, GR, alpha, gravity, chemistry, chirality-doctrine, formal admission, or promotion.  
Generated after Hermes temp-copy audit and Codex live reruns on 2026-06-06.

## What Changed Live

One live hygiene patch was applied:

```text
system_v5/ops/formal_scouts/mp4_fine_structure_explore_jax.py
```

Reason:

```text
The previous direct-NumPy guard scanned raw source text for "import numpy" / "from numpy".
It falsely matched explanatory text saying "no import numpy".
The live patch now uses AST Import / ImportFrom scanning.
```

Effect:

```text
mp4_fine_structure_explore_results.json now has all_pass=true and blockers=[].
alpha status did not improve:
  alpha_value = 0.011490294021831283
  matches_137 = false
  derived = false
  underdetermined = true
  fit_control_matches_137 = true
```

This is a test-truth improvement only. It does not reopen alpha as a derivation.

## New Cross-Row Audit Probe

New source:

```text
system_v5/ops/formal_scouts/sim_discriminator_matrix_cross_row_consistency_probe.py
```

New result:

```text
system_v5/ops/formal_scouts/results/discriminator_matrix_cross_row_consistency_results.json
```

Purpose:

```text
Reconcile the matrix-level branch labels against stricter individual-row verdicts.
If matrix and individual rows disagree by scope, output split_scope rather than letting a broad matrix label over-promote a branch.
```

Fresh result:

```text
all_pass=true
split_scope_count=3
demoted_count=4
```

Key effective ceilings:

| Branch | Effective ceiling |
|---|---|
| associator / nonassociativity | `formal_scout_only_no_promotion` |
| Hopf lifted-vs-density | `real_lifted_data_fence_only` |
| sigma-y / 720 holonomy | `scratch_supported_lifted_holonomy_only` |
| charge ladder | `split_scope_carrier_support_but_physical_derivation_open` |
| QIT face/knot readout | `source_native_real_carrier_but_no_qit_admission` plus `split_scope_repair_needed` |
| knot mass/gravity | `scratch_geometry_readout_not_gravity_derivation` |
| shell capacity | `partial_capacity_not_chemistry` |
| fine-structure alpha | `graveyard_underdetermined_challenger_only` |
| spinor carrier minimality | `real_layer_but_realization_convention` |

## Commands Run

Contract and syntax checks:

```text
/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3 -m py_compile system_v5/ops/formal_scouts/mp4_fine_structure_explore_jax.py
/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3 scripts/lint_sim_contract.py system_v5/ops/formal_scouts/mp4_fine_structure_explore_jax.py
/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3 -m py_compile system_v5/ops/formal_scouts/sim_discriminator_matrix_cross_row_consistency_probe.py
/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3 scripts/lint_sim_contract.py system_v5/ops/formal_scouts/sim_discriminator_matrix_cross_row_consistency_probe.py
```

Selected-source lint:

```text
/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3 scripts/lint_sim_contract.py \
  system_v5/ops/formal_scouts/sim_disc_finite_support_admissibility.py \
  system_v5/ops/formal_scouts/sim_disc_spinor_carrier_minimality_probe.py \
  system_v5/ops/formal_scouts/sim_disc_hopf_lifted_vs_density_probe.py \
  system_v5/ops/formal_scouts/sim_disc_sigma_y_holonomy_probe.py \
  system_v5/ops/formal_scouts/sim_disc_charge_ladder_jax.py \
  system_v5/ops/formal_scouts/sim_disc_qit_source_native_face_knot_shell_discriminator_probe.py \
  system_v5/ops/formal_scouts/sim_disc_gravity_knot_probe.py \
  system_v5/ops/formal_scouts/sim_disc_shell_capacity_2n2_jax.py \
  system_v5/ops/formal_scouts/sim_carrier_readout_discriminator_matrix_probe.py \
  system_v5/ops/formal_scouts/mp4_fine_structure_explore_jax.py \
  system_v5/ops/formal_scouts/sim_discriminator_matrix_cross_row_consistency_probe.py
```

Result:

```text
checked=11
violation_total=0
```

Formal associator validator:

```text
PATH="/opt/homebrew/bin:$PATH" \
/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3 \
  system_v5/ops/formal_scouts/validate_formal_scout_results.py \
  --fresh-rerun \
  --fresh-rerun-timeout 180 \
  system_v5/ops/formal_scouts/results/three_spinor_associator_lifted_bracketing_probe_results.json
```

Result:

```text
all_pass=true
fresh_rerun=true
octonion_spinor_gap=2.0
octonion_density_gap_fro=0.0
parity_max_diff=1.1102230246251565e-16
classification=formal_scout
promotion_allowed=false
```

Selected live rerun batch:

```text
/tmp/codex_recent_sims_live_rerun_20260606_2306.json
```

Result:

```text
all_exit_zero=true
count=11
```

## Live Rerun Scoreboard

| Row | Live rerun verdict | Ceiling |
|---|---|---|
| finite support admissibility | `REAL_LAYER`, all_pass=true | scratch only |
| spinor carrier minimality | `REAL_LAYER`, realization=`CONVENTION` | scratch only; no unique carrier |
| Hopf lifted-vs-density | `REAL_LAYER`, density quotient loses it | scratch lifted-data fence |
| sigma-y / 720 holonomy | `REAL_CARRIER` | scratch chirality discriminator only |
| charge ladder | `CONVENTION` | carrier support but physical derivation open |
| QIT source-native face/knot/shell | `REAL_CARRIER` | no QIT admission |
| gravity/knot | `CONVENTION`, `G_derived=false` | no gravity derivation |
| shell capacity | `PARTIAL`, `2n^2` yes, filling order no | no chemistry derivation |
| carrier-readout matrix | all_pass=true, but broad labels need reconciliation | use cross-row result |
| fine-structure alpha | all_pass=true, `matches_137=false`, `derived=false` | graveyard / challenger only |
| cross-row consistency | all_pass=true, split_scope_count=3 | effective ceilings only |

## Model Read For Claude

The current high-value spine is smaller and cleaner than the earlier broad story:

```text
nonassociativity
+ lifted Hopf/spinor data
+ sigma-y / 720-degree holonomy
```

These are useful because they depend on lifted/carrier structure and die or collapse under meaningful controls.

The demotions remain live:

```text
alpha: not derived
G/gravity: not derived
charge ladder: carrier support, physical derivation open
shell capacity: partial, not chemistry
QIT/SM/GR/M(C)/Axis0: no admission
```

## Claude Next Work

Claude should not launch another broad named-problem sweep yet.

First, Claude should repair the discriminator matrix language and any downstream docs/prompts so they use this effective-ceiling table:

```text
discriminator_matrix_cross_row_consistency_results.json
```

Then Claude can do one of two bounded follow-ons:

1. Build the OPH overlap/probe quotient micro-sim:

```text
finite patches + shared probes + S/~_M quotient
tree vs loop / holonomy control
density-only erasure control
```

2. Harden the sigma-y / 720-degree holonomy row:

```text
bare +/- H0 collapses
density-only collapses
lifted loop survives
trivial/random loop fails
quaternion/octonion/non-associative carrier variants are explicit
```

Either path must preserve:

```text
classification=scratch_diagnostic unless a real formal-scout contract is satisfied
promotion_allowed=false
formal_admission_allowed=false
no physics/admission/constant derivation language
```
