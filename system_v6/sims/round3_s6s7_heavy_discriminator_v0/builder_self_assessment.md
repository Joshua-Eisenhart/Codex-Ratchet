> PROVENANCE WARNING (controller, 2026-06-11): this file was written by the BUILDER lane and was originally misnamed audit_verdict.md. A builder's verdict on its own work is never evidence. Renamed; the genuine fresh cross-audit verdict is the separate audit_verdict.md.

# Audit verdict - round3_s6s7_heavy_discriminator_v0

Bottom line: VERDICT `GENUINE-WITH-CAVEATS` as a bounded S6/S7 phase-2
`scratch_diagnostic` heavy-local discriminator over exactly the five queued
S6/S7 rows. Cite it only for the five registered S6/S7 heavy rows, the explicit
reparameterized-cycle alias certificate, the N `{8,16,32}` graph/cost and
cover/lens sweeps, and the final per-row exclusions below. Do not cite it as
global S6/S7 uniqueness, formal admission, canonical promotion, or evidence for
any non-S6/S7 heavy queue item.

## Verdict

- Repo vocabulary: `GENUINE-WITH-CAVEATS`.
- Classification: `scratch_diagnostic`.
- `promotion_allowed=false`; `formal_admission_allowed=false`.
- Engine mode: `julia_canon_jax_with_pytorch_graph`.
- Scope: S6/S7 only; exactly five queued heavy-local rows.
- Co-survivors minted: none.
- Size-relative labels: none; every exclusion separated at all three scoped
  sizes `N=8,16,32`.

## Registry Teeth Quoted

```text
S67.R3.1_mobius_reflection_shifted - lens quotient commensurability
S67.R3.2_klein_double_twist - cover-orbit well-definedness then lens row
S67.R3.3_shear_torus - lens descent and S6 leakage taxonomy
S67.R3.4_cycle_with_one_chord - bounded word cost and cycle holonomy
S67.R3.5_ladder_prism_graph - locality cost plus leakage class row
```

## Controls

| Control | Verdict | Receipt |
| --- | --- | --- |
| Anchor self-pass | `anchor` | Anchor cycle and untwisted cover self-pass. |
| Deliberate reparameterized cycle | `alias` | Result JSON includes `mapping_anchor_to_reparameterized`, edge-by-edge checks, and matching mapped/target edge hashes. |
| Round-2 path far-control | `excluded-by-closed-cycle-graph-row` | Degree sequence, cycle rank, and exact charpoly rows separate the path from the closed cycle. |

## Per-Candidate Verdict Table

| Candidate | Registry tooth | Final verdict | N sweep |
| --- | --- | --- | --- |
| `S67.R3.1_mobius_reflection_shifted` | lens quotient commensurability | `excluded-by-lens-quotient-commensurability` | `8,16,32` |
| `S67.R3.2_klein_double_twist` | cover-orbit well-definedness then lens row | `excluded-by-cover-orbit-well-definedness-then-lens-row` | `8,16,32` |
| `S67.R3.3_shear_torus` | lens descent and S6 leakage taxonomy | `excluded-by-lens-descent-and-S6-leakage-taxonomy` | `8,16,32` |
| `S67.R3.4_cycle_with_one_chord` | bounded word cost and cycle holonomy | `excluded-by-bounded-word-cost-and-cycle-holonomy` | `8,16,32` |
| `S67.R3.5_ladder_prism_graph` | locality cost plus leakage class row | `excluded-by-locality-cost-plus-leakage-class-row` | `8,16,32` |

## Validator Commands And Statuses

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/round3_s6s7_heavy_discriminator_v0/round3_s6s7_heavy_discriminator_v0_jax.py
-> {"all_pass": true, "result": "system_v6/sims/round3_s6s7_heavy_discriminator_v0/results/round3_s6s7_heavy_discriminator_v0_jax_results.json"}

/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/round3_s6s7_heavy_discriminator_v0/round3_s6s7_heavy_discriminator_v0_pytorch.py
-> {"all_pass": true, "result": "system_v6/sims/round3_s6s7_heavy_discriminator_v0/results/round3_s6s7_heavy_discriminator_v0_pytorch_results.json"}

JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier system_v6/sims/round3_s6s7_heavy_discriminator_v0/round3_s6s7_heavy_discriminator_v0_julia.jl
-> {"all_pass":true,"result":"system_v6/sims/round3_s6s7_heavy_discriminator_v0/results/round3_s6s7_heavy_discriminator_v0_julia_results.json"}

/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/round3_s6s7_heavy_discriminator_v0/round3_s6s7_heavy_discriminator_v0_envelope.py
-> {"all_pass": true, "result": "system_v6/sims/round3_s6s7_heavy_discriminator_v0/results/round3_s6s7_heavy_discriminator_v0_envelope_results.json"}

/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch system_v6/sims/round3_s6s7_heavy_discriminator_v0/results/round3_s6s7_heavy_discriminator_v0_envelope_results.json
-> {"ok": true, "result_json": "system_v6/sims/round3_s6s7_heavy_discriminator_v0/results/round3_s6s7_heavy_discriminator_v0_envelope_results.json"}

/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed system_v6/sims/round3_s6s7_heavy_discriminator_v0/results/round3_s6s7_heavy_discriminator_v0_envelope_results.json
-> {"ok": true, "result_json": "system_v6/sims/round3_s6s7_heavy_discriminator_v0/results/round3_s6s7_heavy_discriminator_v0_envelope_results.json"}

/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed --require-tool-intent system_v6/sims/round3_s6s7_heavy_discriminator_v0/results/round3_s6s7_heavy_discriminator_v0_envelope_results.json
-> {"ok": true, "result_json": "system_v6/sims/round3_s6s7_heavy_discriminator_v0/results/round3_s6s7_heavy_discriminator_v0_envelope_results.json"}

/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/round3_s6s7_heavy_discriminator_v0/validate_round3_s6s7_heavy_discriminator_v0.py
-> {"ok": true, "validator_ok": true, "errors": []}
```