Bottom line: OVERALL `SWEEP_CLEAN`. The post-audit freshness gap from the tool-honesty demotion sweep is closed for all six scoped packets: every scoped post-audit change traces to the sweep's named demotion/rewording/annotation/validator-hardening items, the named anchors match their audit-time committed values, and fresh scratch reruns plus validators are green.

# Focused post-sweep freshness audit - 2026-06-11

Scope:

- `round3_s4_heavy_discriminator_v0`
- `round3_s5_heavy_discriminator_v0`
- `basin_information_fusion_v1`
- `manifold_super_sim_v0`
- `z4_syndrome_record_v0`
- `manifold_family_b_integrated_v0`

Baseline: audit-time parent of the demotion sweep, `2ad726598^` = `3d1932d8f29c607ff4c38d6d898a77fc13566f00`.

Sweep commit: `2ad726598204e01b883c76ce988355ada188e5c2`.

Current HEAD checked: `0dc215ad30cf591ee40d6f59982a1420bd30b47e`.

Route truth: partial Wizard v4.2 / Max Assembly attempt. Three Codex sidecar agents completed read-only diff/anchor audits over independent packet pairs; controller performed scratch reruns, validator checks, synthesis, and this single receipt write. No git add/commit.

Write boundary: live repo writes were limited to this receipt. Packet entrypoints and writer validators were rerun in scratch clone `/tmp/codex-ratchet-freshness.4VjhW3/repo`; live scoped packet paths were verified clean after restoring accidental timestamp-only S4/S5 result drift from this audit run.

Freshness gate checks:

- `git diff --name-only 2ad726598..HEAD -- <six scoped packet dirs> scripts/validate_three_engine_sim_result.py`: no output.
- `git diff --name-status 2ad726598^ 2ad726598 -- <scope>`: only the demotion sweep paths.
- Live no-write hygiene after restoration: no diff in the six scoped packet dirs or `scripts/validate_three_engine_sim_result.py`.

## Packet verdicts

| Packet | Diff trace | Anchor result | Validator/rerun result | Verdict |
|---|---|---|---|---|
| `round3_s4_heavy_discriminator_v0` | `qutip`, `z3`, `cvc5` demoted/narrowed to supportive where applicable; z3/cvc5 flips marked `tautological_flip`; validator expects tautological solver flips and preserves Julia Z3 `sat` flip. No out-of-scope change found. | S4 witness anchors byte-match audit-time values: candidate verdict table, positive/negative rows, S4 witnesses, Julia/JAX divergence rows, z3/cvc5 witness values. | Scratch rerun: Julia leg ok, JAX leg ok, envelope ok. `validate_three_engine_sim_result.py --strict-source-backed --require-tool-intent ...`: ok true. Packet validator: ok true. | `SWEEP_CLEAN` |
| `round3_s5_heavy_discriminator_v0` | `torch_geometric` demoted/narrowed to supportive container/metadata role; SCC remains handrolled Kosaraju; graph-row wording scoped; validator no longer treats PyG as load-bearing. No out-of-scope change found. | S5 anchor rows byte-match audit-time values: candidate verdict table, stability pairs, source backing probes, divergence engine values. | Scratch rerun: Julia/JAX/PyTorch legs ok, envelope ok. `validate_three_engine_sim_result.py --require-pytorch --strict-source-backed --require-tool-intent ...`: ok true. Packet validator: ok true. | `SWEEP_CLEAN` |
| `basin_information_fusion_v1` | `Graphs`, `torch.func`, and `torch_geometric` demoted/narrowed to supportive/probe surfaces; observable wording now states what each package actually computes; validator hardening is shared. No out-of-scope change found. | Fusion regimes and flow anchors byte-match audit-time values: `record_retention_at_g1_merge`, `engine_key_summary`, `basin_conditioned_flow`. | Scratch rerun: Julia/JAX/PyTorch legs ok, envelope ok. `validate_three_engine_sim_result.py --require-pytorch --strict-source-backed --require-tool-intent ...`: ok true. Packet validator logic imported without writer side effect: ok true. | `SWEEP_CLEAN` |
| `manifold_super_sim_v0` | `torch.func` and `torch_geometric` demoted/narrowed to supportive source-backing probes; observable wording updated; audit verdict closure annotations added for prior G1/G2 closure and citation suffix. Julia rerun metadata changed under Graphs.jl version drift, but anchors/source hash stayed stable. No object/anchor drift found. | `weld_anchors` byte-match audit-time values, including G0 graph sha, G1 partition, D_z information, stage-word endpoint, fusion regimes, and SMT rows. | Scratch rerun: Julia/JAX/PyTorch legs ok, spec writer ok, envelope rebuilt with positional `scripts/build_three_engine_envelope.py <spec>` ok. `validate_three_engine_sim_result.py --require-pytorch --strict-source-backed --require-tool-intent ...`: ok true. Packet validator: ok true. | `SWEEP_CLEAN` |
| `z4_syndrome_record_v0` | Only closure annotation for `CAVEAT_JULIA_RECORD_COUNTS_LITERAL` plus shared validator hardening; no result/source drift in packet. No out-of-scope change found. | Z4 regimes byte-match audit-time values: envelope byte-identical; `regime_hashes`, `regimes.positive`, `negative_erased_record`, `negative_partial_record`, and `boundary_trivial_quotient` unchanged. | Scratch rerun: Julia/JAX/PyTorch legs ok, envelope ok. `validate_three_engine_sim_result.py --require-pytorch --strict-source-backed --require-tool-intent ...`: ok true. Packet validator: ok true. | `SWEEP_CLEAN` |
| `manifold_family_b_integrated_v0` | Only audit-verdict wording annotation for order-control/N01 precision plus shared validator hardening; no result/source drift in packet. No out-of-scope change found. | Family B anchors byte-match audit-time values: envelope, trajectory artifact, state object id, B1/B2/B3/B4 row signatures, B2 hash-chain heads, `hash_chain_heads_match_parent=true`, and `weld_anchors`. | Scratch rerun: Julia/JAX/PyTorch legs ok, spec writer ok. Important command shape: envelope must be rebuilt exactly as expected, `scripts/build_three_engine_envelope.py system_v6/sims/manifold_family_b_integrated_v0/manifold_family_b_integrated_v0_envelope_spec.json > system_v6/sims/manifold_family_b_integrated_v0/results/manifold_family_b_integrated_v0_envelope_results.json`; with that, generic strict validator ok true and packet validator ok true. | `SWEEP_CLEAN` |

## Validator command summary

All commands below were run in scratch clone `/tmp/codex-ratchet-freshness.4VjhW3/repo` using `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3` and `/opt/homebrew/bin/julia`.

- S4: Julia, JAX, envelope, strict source-backed/tool-intent validator, packet validator: pass.
- S5: Julia, JAX, PyTorch, envelope, strict require-pytorch/source-backed/tool-intent validator, packet validator: pass.
- Basin fusion: Julia, JAX, PyTorch, envelope, strict require-pytorch/source-backed/tool-intent validator: pass; packet validator logic imported no-write: pass.
- Super-sim: Julia, JAX, PyTorch, spec writer, envelope builder, strict require-pytorch/source-backed/tool-intent validator, packet validator: pass.
- Z4: Julia, JAX, PyTorch, envelope, strict require-pytorch/source-backed/tool-intent validator, packet validator: pass.
- Family B: Julia, JAX, PyTorch, spec writer, expected redirected envelope build, strict require-pytorch/source-backed/tool-intent validator, packet validator: pass.

## Overall line

`SWEEP_CLEAN`: no scoped regression found; freshness exception satisfied by fresh-context verification.
