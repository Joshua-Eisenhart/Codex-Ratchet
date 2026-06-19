# Carrier-Readout Discriminator Matrix

Date: 2026-06-06

Purpose: convert Hermes' recent-sims synthesis into a bounded discriminator packet. This document is model-routing and audit work only. It does not promote any receipt.

## Claim Ceiling

Allowed:

- The recent receipts support a finite owner-carrier -> many readouts research program.
- Some rows are clean scratch diagnostics, one associator/lifted-bracketing receipt currently passes the formal-scout validator, and some rows are graveyard or partial.
- JAX/Julia parity is a diagnostic and a useful implementation-discriminator.

Blocked:

- no physics admission;
- no Standard Model, GR, Yang-Mills, baryogenesis, chemistry, biology, or fine-structure derivation claim;
- no final `M(C)` admission;
- no Axis0, bridge, QIT-engine, PEPS3D, or manifold completion claim;
- no "canonical by process" claim for the scratch tranche.

## Route Truth

Hermes' synthesis is directionally right: the useful object is not a bigger named-problem scoreboard. It is a discriminator matrix:

```text
finite owner carrier / support object
-> finite maps, probes, controls, and quotients
-> readout families
-> branch survival or branch death under carrier mutation / erasure / backend split
```

Codex route check:

- `scripts/wizard_v4_2.py --level low --dry-run` returned `BLOCKED`, not `FULL`.
- No real parent/child Wizard topology is claimed here.
- This document relies on local file reads, result JSONs, fresh command receipts, and contract gates only.

## Corrections To Carry Forward

Hermes' model sentence is useful, but two details need sharpening:

1. `three_spinor_associator_scout` in the current post-cleanup repo result is `classification=scratch_diagnostic`, `all_pass=true`, with tight Julia parity. It is not a JAX boundary failure in its current file.
2. A separate older/lifted-bracketing associator receipt, `three_spinor_associator_lifted_bracketing_probe_results.json`, is `classification=formal_scout` and passes the formal-scout validator, including fresh rerun. That is the strongest current associator discriminator receipt, but its source still fails the newer static sim-contract lint.

Therefore the associator branch is not "JAX failed, Julia succeeded." The cleaner reading is:

```text
associator/lifted-bracketing has a formal-scout receipt that reruns,
and a newer scratch scout that reruns with JAX/Julia parity,
but the source-contract/static-lint trail is split and must be repaired before stronger indexing.
```

## Fresh Commands

Formal-scout validator on lifted-bracketing associator:

```text
/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3 \
  system_v5/ops/formal_scouts/validate_formal_scout_results.py \
  --fresh-rerun --fresh-rerun-timeout 120 \
  system_v5/ops/formal_scouts/results/three_spinor_associator_lifted_bracketing_probe_results.json

all_pass=true
rerun returncode=0
validator errors=[]
```

Fresh Julia peer for lifted-bracketing associator:

```text
/opt/homebrew/bin/julia --project=system_v5/julia_carrier \
  system_v5/julia_carrier/three_spinor_associator_lifted_bracketing.jl

all_pass=true
octonion_density_gap_fro=0.0
octonion_spinor_gap=2.0
```

Static lint over the associator/fine-structure priority set:

```text
/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3 \
  scripts/lint_sim_contract.py \
  system_v5/ops/formal_scouts/three_spinor_associator_scout.py \
  system_v5/ops/formal_scouts/mp4_fine_structure_explore_jax.py \
  system_v5/ops/formal_scouts/sim_three_spinor_associator_lifted_bracketing_probe.py

checked=3
violation_total=5
offender=sim_three_spinor_associator_lifted_bracketing_probe.py
rules=C3_depth_invalid_value,C5_missing_probe,C8_nonclassical_requires_local_pytorch_load_bearing
```

Fine-structure split:

```text
/opt/homebrew/bin/julia --project=system_v5/julia_carrier \
  system_v5/julia_carrier/mp4_fine_structure_explore_julia.jl

exit=0
all_pass=true
alpha_value=0.011490294021831287
matches_137=false
derived_not_fit=false
```

```text
/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3 \
  system_v5/ops/formal_scouts/mp4_fine_structure_explore_jax.py

exit=2
all_pass=false
alpha_value=0.011490294021831283
matches_137=false
derived_not_fit=false
```

Interpretation: fine-structure is not a backend disagreement on the scalar. JAX and Julia agree numerically to parity, but JAX writes the repo-facing all-pass false because the target derivation fails. Julia's local mechanism pass must not be read as an alpha derivation.

## Discriminator Matrix

| Row | Owner carrier / support | Mutated or erased control | JAX state | Julia state | Branch survives | Branch dies | Ceiling |
|---|---|---|---|---|---|---|---|
| associator / nonassociativity | 3-spinor lifted bracketing; octonion-style bracket-sensitive readout | quaternion associative subalgebra, repeated-input alternativity, density-only erasure, raw matrix composition, two-qubit/two-operation boundary | `three_spinor_associator_scout`: scratch, all_pass true, parity `1.11e-16`; lifted-bracketing formal validator fresh-rerun passes via Python source | lifted-bracketing Julia peer all_pass true; scout Julia peer all_pass true | nonzero lifted spinor/bracket readout survives | density-only quotient and associative controls die | best current discriminator; one formal-scout receipt exists, but source-contract lint split blocks stronger indexing |
| charge ladder | Cl(0,6)/octonion owner carrier and ladder occupation divided by 3 | non-integer ladder weights; erased owner carrier | scratch, all_pass true | Julia peer all_pass true | representation-consistency witness for charge grid | independent physical derivation of charge values | scratch diagnostic; by-construction risk remains |
| chirality survival | Weyl handedness / carrier-derived chirality bias | erased carrier, erased golden state, mirror flip, mixed density, no-bias racemic, no-ratchet | scratch, all_pass true, parity `2.24e-44` | Julia peer all_pass true | finite chirality-selection mechanism | baryogenesis, biology, chemistry, or homochirality derivation | mechanism witness only |
| entropy arrow | finite owner carrier with entropy-increase ratchet | owner-carrier erasure, reverse-conjugate schedule, unitary-only recovery | scratch, all_pass true, parity `2.99e-15` | Julia peer all_pass true | monotone finite entropy/readout mechanism | named arrow-of-time solution | mechanism witness only |
| knot mass/gravity | finite knot readout over spinor-network carrier | flatten control, shape-decoupling control, diagnostic 1/r^2 not forced | scratch, all_pass true, parity `1.29e-14` | Julia peer all_pass true | mass-like and gravity-like readouts co-arise and can decouple as functionals | gravity, `G`, physical mass derivation | readout lane only |
| shell capacity | nested Hopf/S3 spinor-shell capacity proxy | erased Hopf shell, non-shell carrier, target-not-used control | scratch, all_pass true, parity `1.11e-16` | Julia peer all_pass true | shell capacity proxy `[2,8,18,32]` | chemistry filling order / 2-8-8 recovery | partial mechanism witness |
| QIT face/knot readout | canonical 3-qubit QIT engine readout vocabulary | two-qubit insufficient, flat-fuzz, knot-coupling, decoupling, distinct-probe controls | scratch, all_pass true, parity `7.99e-15`; result omits `source_path` | Julia peer all_pass true | 3-qubit readout rank and branch separation | QIT engine admission, physics readout admission | scratch diagnostic with metadata repair needed |
| fine-structure identifiability | owner carrier scalar from geometry/coupling ingredients | carrier erasure, flat carrier, explicit target-fit control | repo JAX exits 2, writes all_pass false; parity `2.66e-15`; `matches_137=false`, `derived_not_fit=false` | Julia local mechanism all_pass true but same scalar miss | carrier scalar is computable and ablatable | alpha derivation; target match without fitting | graveyard / underdetermination row |

## Best Next Substantive Move

Do not launch another broad named-problem sweep first.

First priority:

```text
Repair and harden the associator row as the carrier-readout discriminator.
```

Required work:

1. Decide whether `three_spinor_associator_lifted_bracketing_probe_results.json` or `three_spinor_associator_scout_results.json` is the row owner.
2. Add missing `source_path` / peer metadata where absent.
3. Make the chosen source pass the current static source-contract lint without adding decorative PyTorch or changing the claim ceiling.
4. Preserve the formal-scout validator pass for the lifted-bracketing receipt if that receipt remains the owner.
5. Add a mutated-carrier matrix output: owner carrier, quaternion restriction, density-only quotient, raw associative matrix composition, two-qubit/two-operation boundary.
6. Keep blocked consumers explicit: no `M(C)`, no PEPS3D, no Axis0, no QIT engine, no physics, no bridge.

Second priority:

```text
Turn fine-structure into an identifiability test, not a constant derivation.
```

Required work:

1. Keep `all_pass=false` for target derivation unless a new untuned derivation appears.
2. Vary carrier ingredients and quantify the dimension of the underdetermined family.
3. Record how many different scalars can be made to approximate `1/137` under allowed versus forbidden target-fit controls.
4. Use the row as evidence that the system can graveyard seductive constants cleanly.

## Message To Claude

Use Hermes' synthesis, but do not repeat the JAX/Julia split loosely.

The current repo evidence says:

- The broad positive model signal is finite owner carrier -> many readouts.
- The whole batch remains fenced, mostly scratch-diagnostic.
- The associator branch is the best next discriminator, but its route truth is split:
  - `three_spinor_associator_lifted_bracketing_probe_results.json` is a formal-scout-classified receipt and passes fresh formal-scout validator rerun.
  - `three_spinor_associator_scout_results.json` is the post-cleanup scratch row, all_pass true, with tight JAX/Julia parity.
  - The lifted-bracketing source still fails current static source-contract lint, so do not call the trail clean until repaired.
- Fine-structure is an underdetermination/graveyard row:
  - JAX repo result exits 2 and writes all_pass false.
  - Julia local mechanism checks pass, but the scalar misses `1/137` and `derived_not_fit=false`.
  - Do not read Julia local pass as alpha evidence.

Build the carrier-readout discriminator matrix next. The goal is not another problem sweep. The goal is to identify which readouts survive only on the intended owner carrier and which die under mutated-carrier, density-only, associative, reduced-qubit, or target-fit controls.
