# Wolfram TOE / M_RPF(C) Wizard v4.3 Multimodel Audit

Status: completed bounded audit + one follow-through sim.

This artifact records the corrected multimodel pass requested by the owner:
Grok, Gemini, Opus, mass Sonnet, Codex-native scouts, and Wizard v4.3 object
preservation. It is not a physics proof, not Axis0/FEP admission, not PEPS3D
closure, and not final manifold progress.

## Route Truth

- Wizard v4.3 object packet validation: pass.
- Wizard v4.3 self-test: pass, including rejection of Axis0 proxy promotion,
  FEP analogy promotion, missing shell fields, root/extended constraint
  collapse, and underdefined `jk fuzz`.
- Codex-native scouts: 2 completed.
- Claude Bridge corrected wave: 1 Opus + 5 Sonnet completed.
- Claude Bridge first wave: 1 Opus + 6 Sonnet completed but demoted because
  the controller prompt extracted top-level null fields instead of
  `primary_object_card`.
- Grok direct xAI API: completed with model
  `grok-4.20-0309-non-reasoning`.
- Gemini CLI: failed with `ModelNotFoundError`.
- Gemini direct API retry: completed with `gemini-3.5-flash`.

## Converged Finding

Wolfram-style machinery is useful only as a typed adapter for the front half of
the object:

```text
Omega_r branch generation
branch/history/event provenance
merge/reconvergence pressure
branchial same-shell relations
rule-family/rulial variant atlas
observer/coarse quotient tests
```

It must not become the primary object. It must not become proof, Axis0,
FEP/Holodeck, scalar entropy, PEPS3D closure, flux, physics, or final manifold
truth.

The missing step identified by the corrected council was not another generic
Wolfram feature pass. It was:

```text
Omega_r branches
-> explicit PEPS3D site/edge/face/cell support anchors
-> compatibility weights
-> rho_present_K
-> outward_record_K
```

## Follow-Through Sim

Wrote:

```text
system_v5/ops/formal_scouts/sim_wolfram_hypergraph_peps3d_support_fit_probe.py
system_v5/ops/formal_scouts/results/wolfram_hypergraph_peps3d_support_fit_probe_results.json
```

Finite map:

```text
W_hyper_peps_support:
  (event_x, Sigma_r, K=(V,E,F,C), finite hypergraph rewrite rules R_H,
   shell_orientation, branch PEPS3D support tensors)
  ->
  Omega_r hypergraph event table,
  per-branch PEPS3D support anchors,
  compatibility weights,
  rho_present_K,
  outward_record_K,
  QIT/order readout vector,
  controls,
  blocked consumers
```

The sim uses local Python Wolfram-style hypergraph rewriting, not Wolfram
Language. It records Wolfram Language runtime availability separately.

## Result Summary

```json
{
  "all_pass": true,
  "final_branch_count": 128,
  "max_peps3d_sites": 64,
  "max_peps3d_bond_dim": 2,
  "path_entropy_bits": 6.962323697,
  "noncommuting_order_gap": 0.673406158,
  "commuting_order_gap": 0.0,
  "uniform_density_gap": 0.027213055,
  "support_scramble_density_gap": 0.083400903,
  "orientation_density_gap": 0.007124254,
  "promotion_allowed": false,
  "wolfram_runtime_available": false
}
```

What improved over the prior Wolfram scouts:

- every final branch has explicit PEPS3D support anchors;
- all v4.3 primary object fields are present in the output object table;
- compatibility weights produce a valid torch density `rho_present_K`;
- `outward_record_K` is emitted as branch provenance, not prose;
- support scramble, scalar-site-floor-only, uniform-weight, orientation-erased,
  single-argmax, and proxy-promotion controls all remain active;
- downstream consumers remain blocked.

## Still Blocked

The following remain blocked:

```text
PEPS3D closure
layer stacking
bridge
flux
Xi/Phi0
Axis0
Holodeck/FEP
physics
gravity proof
final manifold
```

## Model-Specific Notes

- Opus and most Sonnet lanes were strict: the prior scouts preserved
  `Omega_r` and order sensitivity, but not shell orientation, compression,
  `rho_present`, or outward record. This drove the follow-through sim.
- Grok was more permissive and treated reconvergence/provenance as preserving
  more fields than the repo evidence really earned. Its risk warning still
  aligned: do not let Wolfram replace literal shell orientation or the primary
  retrocausal compression object.
- Gemini direct retry accepted the new sim with reservation and flagged
  `path_entropy_bits` as the strongest remaining scalar-proxy risk.
- The first Claude wave usefully caught a controller packaging failure:
  presenting top-level null fields instead of `primary_object_card` made the
  whole council attack a nonexistent null object packet. That wave is not used
  as evidence.

## Next Bounded Sim

Run a shell-shear stress packet:

```text
W_hyper_peps_shell_shear:
  (Omega_r branches, PEPS3D support anchors, compatibility weights,
   nonuniform shell-collapse schedule)
  ->
  rho_present_K stability curve,
  outward_record_K preservation,
  control gaps for path-entropy-only, uniform weighting, shell-erased,
  orientation-erased, and support-scrambled variants
```

Goal: test whether compatibility-weight compression remains stable when outer
shells collapse nonuniformly, without letting path entropy become the primary
readout.

Stop if:

- the survivor can be predicted by scalar path entropy alone;
- shell orientation removal does not weaken the compression;
- support scrambling does not change the survivor;
- any downstream consumer is unlocked.

## Validation

Commands run:

```text
python3 scripts/lint_sim_contract.py system_v5/ops/formal_scouts/sim_wolfram_hypergraph_peps3d_support_fit_probe.py
python3 system_v5/ops/formal_scouts/validate_formal_scout_results.py --fresh-rerun system_v5/ops/formal_scouts/results/wolfram_hypergraph_peps3d_support_fit_probe_results.json
python3 scripts/wizard_v4_3_object_preservation.py validate --input system_v5/ops/formal_scouts/retrocausal_shell_field_v43_object_packet_20260527.json
python3 scripts/wizard_v4_3_object_preservation.py selftest --out /tmp/codex_ratchet_wolfram_v43_multimodel/v43_selftest_final.json
git diff --check -- system_v5/ops/formal_scouts/sim_wolfram_hypergraph_peps3d_support_fit_probe.py system_v5/ops/formal_scouts/results/wolfram_hypergraph_peps3d_support_fit_probe_results.json
```

All passed.
