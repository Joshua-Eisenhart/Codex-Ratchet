# Audit Verdict: terrain_spinor_shell_nest_v0

Scope: fresh cross-backend audit of codex1-built `terrain_spinor_shell_nest_v0`. Read-only except this file. No git add or commit was run.

Verdict: GENUINE-WITH-CAVEATS; rung 2 is PARTIAL, not full-earned under the exact owner card. The three-level nest is computed for the required terrain rows, the controls fire, and the standard validator passes. The caveats are structural: the mirror-law packet is not in target parent lineage, the rung-1 quantum-jump convention is hash-bound but not text-pinned identically, the `4/25` anchor is inherited from rung 1 rather than recomputed in this packet, and the PyTorch leg over-labels some capability rows as load-bearing.

Ceiling: `scratch_diagnostic`; `promotion_allowed=false`; `formal_admission_allowed=false`. This audit does not promote to canonical, formal, bridge, flux/manifold nesting, or four-level integration.

## Commands And Recomputations

- Read calibration: `system_v6/receipts/audit_bar_calibration_20260610.md`.
- Read target sources/results and parent results under `system_v6/sims/terrain_spinor_shell_nest_v0`, `terrain_weyl_spinor_lr_v0`, `stage_lifted_spinor_shell_n3_v0`, `geo_s5_terrain_flows_v0`, `geo_disintegration_machinery_v0`, and `terrain_exact_mirror_finder_v0`.
- Verified parent commits: `a706208c4` is the rung-1 terrain Weyl/spinor packet; `81b38c3e6` is the family-local mirror-law packet.
- Ran general validator read-only:
  - `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py system_v6/sims/terrain_spinor_shell_nest_v0/results/terrain_spinor_shell_nest_v0_envelope_results.json`
  - Result: `{"ok": true, "result_json": "system_v6/sims/terrain_spinor_shell_nest_v0/results/terrain_spinor_shell_nest_v0_envelope_results.json"}`.
- Recomputed `build_core_nest()` read-only from `terrain_spinor_shell_nest_v0_common.py`.
  - `core_all_pass=true`.
  - `smt_identity_values` matched the envelope.
  - `pin_sha256` recomputed as `2b118e84fc9da568f3ba625e673fd1a15390e86db62a277ef75c8518abde3160`, matching the envelope.
  - Stage parent SHA recomputed as `8ae7744db3336104166e882b79159d51c94cfadf44e8261a17a9866c87eeebdc`, matching target lineage.
  - Exported q0 site canonical hash recomputed as `825761916e76c2a819f73197ec0ef0813cba76ec1c6cfea815cf859b1bcfa731`.
- Recomputed the PyTorch leg in-memory without writing result files.
  - `all_pass=true`.
  - `torch.func.jacrev/vmap` leakage derivative: `z_dot=[-0.070710678119, 0.04, -0.014142135624]`, `nonzero_count=3`.
  - Package versions in component: `torch=2.11.0`, `torch-geometric=2.7.0`, `geomstats=2.8.0`, `e3nn=0.6.0`, `clifford=1.5.1`, `sympy=1.14.0`, `z3-solver=4.16.0.0`, `cvc5=1.3.3`.

## Q1 Nest Genuineness

Source quotes:

- Target pin, `terrain_spinor_shell_nest_v0_common.py:75-82`: `levels=(a:committed S5 Bloch affine terrain flow,b:rung-1 Weyl spinor L/R lift,c:n=3 shell-placed spinors plus shell leakage and conditioned gamma5 readout)` and `si_frame=own_z_x_frames_not_H0_forced`.
- Rung-1 source, `terrain_weyl_spinor_lr_v0.py:4-6`: it consumes committed S5 affine Bloch generators by hash and lifts them to one explicit quantum-jump unraveling; the source states the unraveling is a convention and density flow is load-bearing.

Finding: the nest is genuine as a computation, because `build_core_nest()` consumes the committed S5 rows, the committed n=3 shell sites, and the rung-1 family pairs, then computes level-a/level-b/level-c rows together. The stage parent hash and q0 exported site hash recompute cleanly.

Caveat G1: the target does not text-pin the exact rung-1 quantum-jump unraveling string identically. It hash-binds `terrain_weyl_spinor_lr_v0` through parent lineage and names the `rung-1 Weyl spinor L/R lift`, but the exact convention sentence is not repeated in the target pin.

Caveat G2: the owner card included the mirror-law packet `81b38c3e6` as a hash-bound parent. The target parent lineage lists only four parents and does not include `terrain_exact_mirror_finder_v0`.

## Q2 Levels x Properties Matrix

The load-bearing matrix is computed, not just narrated, for `Se_Funnel_L`, `Ni_Pit_L`, `Si_Hill_L`, and `Se_Cannon_R`.

Recomputed Se row:

- Level (a), Bloch: initial q0 Bloch `[0.707106781187, 0.0, 0.707106781186]`; flow t=1 `[0.380797333679, 0.016720521208, 0.237929260135]`; S5 `A,b` copied from committed parent.
- Level (b), +spinor: `gamma5_odd_sigma_z_L_minus_R` at q0 is `0.618726593813`; spinor-blind quotient-first control gives `0.0`.
- Level (c), +shell: leakage class rows are all `leave_foliation`; q0 `z_dot=-0.728984741135`, `purity_derivative=-1.6`; on-shell minus off-shell gamma5 deltas are `[0.411027318965, 0.110972094483, -0.700329558083]`.

Per-terrain level-c recompute summary:

| Terrain | Level-a flow t=1 | Signed q0 row | Shell classes | Max shell gamma5 shift |
| --- | --- | ---: | --- | ---: |
| `Se_Funnel_L` | `[0.380797333679, 0.016720521208, 0.237929260135]` | `0.618726593813` | `leave_foliation` | `0.700329558083` |
| `Ni_Pit_L` | `[0.597622463704, 0.082341617371, -0.078805752204]` | `0.061367173122` | `leave_foliation` | `0.927155609287` |
| `Si_Hill_L` | `[0.436571720374, 0.184579562867, 0.707106781186]` | `1.14367850156` | `projected_shell_preserve_but_Hopf_leave` | `1.561751491317` |
| `Se_Cannon_R` | `[0.237929260135, 0.016720521208, 0.380797333678]` | `0.618726593813` | `leave_foliation` | `0.700329558083` |

Undefined/degenerate matrix entries are justified as follows:

- `lr_signed_separation.level_a=undefined`: bare S5 density/Bloch rows have no L/R spinor sheet assignment. The spinor-blind quotient control returning zero exhibits this.
- `shell_leakage_class.level_a=undefined` and `.level_b=undefined`: leakage class depends on per-site shell etas and shell placement; the computed level-c count is `12` non-preserve terrain-site rows.
- `shell_conditioned_gamma5_shift.level_b=degenerate`: signed rows exist at level (b), but the on-shell/off-shell comparison needs the committed n=3 shell etas. Level (c) exhibits four terrain rows with nonzero shell-conditioned shifts.
- `conditioned_fixed_point_structure.level_a/level_b=degenerate`: the parent naive singleton conditioning fails as `0/0 -> nan`; target level (c) uses shell placement to give finite site-conditioned readouts.

Caveat G3: the byte-exact S5 parent hash is checked in target, and the rung-1 parent contains the `4/25` Se anchor. This target packet does not independently recompute or re-emit the literal `4/25` anchor; it inherits that via `terrain_weyl_spinor_lr_v0`.

## Q3 Si Frame Row

Finding: reconciled honestly. The target records `honest_status=own_frame_computed`, `Si_Hill_L_frame=z dephasing frame`, `Si_Citadel_R_frame=x dephasing frame`, and `H0_sheet_override_forced=false`.

Cross-check against mirror-law packet `81b38c3e6`: `terrain_exact_mirror_finder_v0` says Si's solution set is `{M in O(3): M*e_z = det(M)*e_x}` and that Si is a z-frame to x-frame terrain map, not a global H0 chirality map. That agrees with the target's own-frame treatment. There is no forced rescue of the rung-1 H0 sheet mismatch.

## Q4 Controls

All requested controls fire in the envelope and recomputation:

- Level-(a)-only byte-exact S5: parent path hash `8c5474786973f067e55c0200392c1a27cbe8bf5d71cfd632b507d066b6cc9b1e`; pass.
- Spinor-blind quotient-first: `kills_signed_rows=true`, `max_abs_signal_after_quotient=0.0`; pass.
- Shell-blind no-placement: `kills_leakage_rows=true`, `leakage_rows_without_sites=0`; pass.
- Permuted etas: real signature differs from permuted signature; pass.
- Naive conditioning fails: cites `geo_disintegration_machinery_v0`; failure is `P(A and T_eta)/P(T_eta) is 0/0, returned by SymPy as nan`; pass.
- Extra controls also fire: duplicate etas reduce unique eta count to `2`; collapsed etas reduce unique z count to `1`.

## Q5 Standard / Tools / Schema

Standard schema: pass. Envelope has `schema_version="three_engine_sim_result_v1"` as a field and `standard_schema_mode="FIELD"`.

Validator status:

- General three-engine validator: ok.
- Packet-local validator result from builder phase: `ok=true`, no errors. Note that this validator contains a builder-only assertion that `audit_verdict.md` must not exist. After this audit file exists, rerunning that specific packet-local validator will fail that builder-only check unless the validator is adjusted or run against pre-audit state.

Real legs:

- Julia ran and owns the semantic/capability row: `QuantumOptics`, `Grassmann`, and `Z3`; `reads_peer_result=false`.
- JAX/Python ran: `diffrax`, `sympy`, `z3`, `cvc5`, and finite matrix checks; `reads_peer_result=false`.
- PyTorch ran: the real nest-relevant torch check is `torch.func.jacrev/vmap` over shell etas with nonzero leakage derivative. `torch_geometric`, `geomstats`, `e3nn`, and `clifford` are real API calls and useful capability/support rows, but they do not independently arbitrate the three-level nesting claim.

Caveat G4: PyTorch `TOOL_INTEGRATION_DEPTH` labels too many capability rows `load_bearing`. For the nesting claim, `torch.func` plus SMT checks are load-bearing; `torch_geometric`, `geomstats`, `e3nn`, and `clifford` are better classified as support/capability receipts unless a later gate makes those rows decisive.

SMT/proofs:

- z3 and cvc5 bind `actual_non_preserve_shell_site_count=12` and `erased_no_placement_non_preserve_count=0`.
- Real identity `actual == erased` is `unsat`.
- Erased control is `sat`.
- Julia Z3 mirrors the same contradiction.

Other standard checks:

- Parent lineage: hash-bound for four target parents, but missing mirror-law parent. See G2.
- Capability receipts: present for all legs.
- Tool calls: 15 flattened envelope rows; one-to-one rows present.
- Fixture wording: no fixture strings found in envelope scalar values.
- Versions: present in component result JSONs; not flattened into envelope engine records.
- Seeds: component legs carry `seed=2026061007`; envelope lacks a top-level seed field.

Caveat G5: versions and seed are recoverable from component legs, but the envelope should flatten them if the standard card requires envelope-local inspection.

## Q6 Closure

Computed nesting-dependency facts now earned:

- `bloch_flow` needs level (a): committed S5 `A,b` and finite Bloch flow are enough.
- `lr_signed_separation` needs level (b): it exists only after spinor L/R lift; quotient-first kills it.
- `shell_leakage_class` needs level (c): per-site shell etas and shell placement produce 12 non-preserve rows; shell-blind placement erases leakage rows.
- `shell_conditioned_gamma5_shift` needs level (c): all four required terrain rows have nonzero on-shell/off-shell gamma5 shifts.
- `Si` is not forced into the H0 sheet law: it is computed in its own z/x frame and cross-checks against the family-local mirror-law packet.

Still open:

- Full mirror-law lineage in this packet: target should add `terrain_exact_mirror_finder_v0` to parent lineage if the owner card treats it as a hash-bound parent.
- Exact textual pinning of the rung-1 quantum-jump convention in the target pin.
- Independent target-level recomputation of the rung-1 `4/25` anchor, if the audit card requires it inside rung 2 rather than by parent hash.
- Flux/manifold nesting remains in the committed two-shell and three-shell packets, not here.
- Full four-level integration remains open.
- `conditioned_fixed_point_structure` is only supported through the parent disintegration rule plus site-conditioned readout; target does not solve a new fixed-point theorem.

## Named Caveats

- G1: Rung-1 quantum-jump convention is hash-bound but not text-pinned identically in the target.
- G2: Mirror-law packet `81b38c3e6` is missing from target `parent_lineage`.
- G3: `4/25` anchor is inherited from rung 1, not recomputed inside this target packet.
- G4: PyTorch capability rows are over-labeled as load-bearing; the direct PyTorch nesting contribution is the derivative/eta row plus SMT mirrors.
- G5: Envelope does not flatten component package versions or a top-level seed, though component legs carry them.
- G6: Packet-local validator's builder-only `audit_verdict.md must not exist` check will fail after this audit file is present.

## Final Verdict

GENUINE-WITH-CAVEATS / RUNG 2 PARTIAL. The owner nesting claim is computed for the three-level terrain nest as a scratch diagnostic: level (a) Bloch flow, level (b) spinor signed rows, and level (c) shell leakage/gamma5 conditioning are separated by real controls. It is not a full rung-2 closure under the exact card until the missing mirror-law lineage, exact convention pin, internal `4/25` recheck, and PyTorch load-bearing scope are hardened.

## Builder-Hardening Addendum

This hardening round targets closure of G1, G2, G3, G5-torch, and G6 only. The target packet must rerun all three legs plus the envelope, preserve exact rows byte-stable, and keep the audit verdict at PARTIAL pending a fresh re-audit.

- G1 target: text-pin the exact rung-1 quantum-jump unraveling convention in the packet pin while retaining the hash binding.
- G2 target: add `terrain_exact_mirror_finder_v0` committed at `81b38c3e6` to packet parent lineage with its result hash.
- G3 target: recompute and emit the packet-local `Se_Funnel_L` literal `4/25` anchor, not inherited through rung 1.
- G5-torch target: demote PyTorch capability rows without gating function-level receipts to `supportive`; keep `torch.func`, `sympy`, `z3`, and `cvc5` load-bearing.
- G6 target: make the packet-local validator phase-aware so builder phase asserts `audit_verdict.md` absence and post-audit reruns skip that builder-only check.

## Focused Re-Audit Addendum - G1/G2/G3/G5-torch/G6 Hardening

Scope: read-only re-audit of the hardening for G1, G2, G3, G5-torch, and G6 only, except this appended addendum. The original earned core remains `GENUINE-WITH-CAVEATS`; rung 2 remains `PARTIAL`, not full-earned.

- G1 closed. Rung-1 source row, `terrain_weyl_spinor_lr_v0.py:502`: `standard quantum-jump unraveling: K_eff=-iH-1/2 sum_j L_j^dagger L_j for no-jump drift, jump maps psi -> L_j psi/||L_j psi||, ensemble density obeys the Lindblad generator. This is a choice; the density generator is the invariant object.` Target pin row, `terrain_spinor_shell_nest_v0_envelope_results.json:2290` / `rung1_unraveling_convention_text_pin`: `standard quantum-jump unraveling: K_eff=-iH-1/2 sum_j L_j^dagger L_j for no-jump drift, jump maps psi -> L_j psi/||L_j psi||, ensemble density obeys the Lindblad generator. This is a choice; the density generator is the invariant object.` Recompute check: `pin_contains_convention True`; `text_pin_equals_pin_slice True`.
- G2 closed. `parent_lineage.consumed_inputs` now includes `terrain_exact_mirror_finder_v0` with `commit_hint=81b38c3e6`. Recomputed file hash for `system_v6/sims/terrain_exact_mirror_finder_v0/results/terrain_exact_mirror_finder_v0_envelope_results.json`: `8f39bfd83253e0d847d95c268da9bb7f5d86ffb0953ede963c185bc3ee449b06`; lineage records the same hash; check quoted: `hash_match True`.
- G3 closed. Recomputed from the packet row/formula, not the flag: `formula=4*(1/5)^2`, `hamiltonian_coeff=1/5`, recompute `4/25`; recorded `bloch_angular_frequency_squared=4/25`, `computed_in_packet=True`, `inherited_via_rung1=False`, `pass=True`.
- G5-torch closed. Demoted non-gating PyTorch capability rows are now `torch_geometric=supportive`, `geomstats=supportive`, `e3nn=supportive`, `clifford=supportive`, and `torch=supportive`. Remaining PyTorch load-bearing rows genuinely gate: `torch.func` has `jacrev/vmap` leakage derivative with `z_dot=[-0.070710678119, 0.04, -0.014142135624]`, `nonzero_count=3`, `pass=true`; `sympy` has `identity_residual=0`, `pass=true`; `z3` and `cvc5` both bind computed non-preserve counts and return `verdict=unsat`, `erased_control_verdict=sat`, `pass=true`.
- G6 closed. Packet-local validator is phase-aware. To preserve the read-only boundary, I ran its post-audit path against a `/tmp` copy of the packet/root layout. Exit `0`; output: `{"errors": [], "ok": true, "result_path": "system_v6/sims/terrain_spinor_shell_nest_v0/results/terrain_spinor_shell_nest_v0_validator_results.json"}`. Existing packet validator receipt also records `phase=post_audit`, `ok=true`, `errors=[]`.
- Exact result bytes stable against the envelope hash table. Check quoted: `engine_result_sha_check {'jax': ('d02d7d588956169e3bfbaa97d74fa5c1846d5ded0417c4c6e5539199f28ad161', 'd02d7d588956169e3bfbaa97d74fa5c1846d5ded0417c4c6e5539199f28ad161', True), 'julia': ('e28afc6e3488eaf7236b532ffc952f1c0a5edf97d1e51197718a404d2ed898d5', 'e28afc6e3488eaf7236b532ffc952f1c0a5edf97d1e51197718a404d2ed898d5', True), 'pytorch': ('e22628d912f6b823db5fc0914bc60181ca178cb50b13827796db00d4d0a00f14', 'e22628d912f6b823db5fc0914bc60181ca178cb50b13827796db00d4d0a00f14', True)}`.
- Validators green. Required validator command: `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch system_v6/sims/terrain_spinor_shell_nest_v0/results/terrain_spinor_shell_nest_v0_envelope_results.json`; exit `0`; output: `{"ok": true, "result_json": "system_v6/sims/terrain_spinor_shell_nest_v0/results/terrain_spinor_shell_nest_v0_envelope_results.json"}`.

Conclusion: hardening caveats G1, G2, G3, G5-torch, and G6 are closed; the verdict remains `GENUINE-WITH-CAVEATS / rung-2-PARTIAL` at one-qubit/3-node scope only, the network-level integration remains the next packet rather than this one, and the ceiling remains `scratch_diagnostic` with `promotion_allowed=false` and `formal_admission_allowed=false`.
