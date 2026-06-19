# Audit verdict - round3_s4_heavy_discriminator_v0

Bottom line: VERDICT `GENUINE-WITH-CAVEATS` as the first bounded S4
heavy-local `scratch_diagnostic` discriminator packet. The packet excludes all
four queued S4 heavy candidates and mints no co-survivors. This closes the S4
round-3 discriminator program only for the finite queued rows named by the
registry and the S4 light verdict; it is not S4 uniqueness, canonical
promotion, PyTorch evidence, or permission to generalize beyond the registered
alternative space.

## Verdict

- Repo verdict: `GENUINE-WITH-CAVEATS`.
- Classification: `scratch_diagnostic`.
- `promotion_allowed=false`; `formal_admission_allowed=false`.
- Engine mode: `julia_canon_jax_workhorse`.
- Honest PyTorch omission: accepted. No graph, network, autograd, tensor, or
  PyTorch-specific claim path is scoped by this S4 channel discriminator.
- Julia/JAX verdict maps match. Julia is reference/provenance plus
  QuantumOptics/Z3 route evidence; JAX/Python is the exact SymPy/qutip/z3/cvc5
  workhorse for the Choi, fixed-set, quotient, shell, and commutator rows.
- Packet-local validator on disk is green. Fresh read-only generic validators
  are listed below.

## Exact-Witness Recompute

Fresh scratch recomputation, independent of the packet result JSON, confirmed
the claim-bearing rows requested by the audit.

```text
Anchor Choi spectra:
D_z = (17/20, 3/20, 0, 0)
D_x = (17/20, 0, 0, 3/20)
R_x = (1, 0, 0, 0)
R_z = (1, 0, 0, 0)
```

```text
S4.R3.1 AD_z(gamma=1/5):
Choi spectrum = (9/10, 0, 0, 1/10)
fixed equations =
  x*(-5 + 2*sqrt(5))/5
  y*(-5 + 2*sqrt(5))/5
  -(z - 1)/5
fixed set = {(0,0,1)}
order gap with R_x on z_probe =
  (0, -(-3 + sqrt(5))/5, 1/5)
commutator matrix yz/z y off-diagonal =
  -2*(-2 + sqrt(5))/5
```

```text
S4.R3.3 D_z(lambda) o R_x(pi/2):
lambda=1/2 outputs on same input z-shell points:
  (0,0,1/2) -> (0,-1/4,0)
  (0,1/2,1/2) -> (0,-1/4,1/2)
  z_gap = 1/2; shell_preserved=false

lambda=7/10 outputs:
  (0,0,1/2) -> (0,-7/20,0)
  (0,1/2,1/2) -> (0,-7/20,1/2)
  z_gap = 1/2; shell_preserved=false
```

```text
S4.R3.5 weak nonunital shifts:
weak_shift_z Choi spectrum =
  ((20 - sqrt(197))/40, (sqrt(197) + 20)/40, -1/40, 1/40)
weak_shift_x Choi spectrum =
  (1/40, -1/40, (20 - sqrt(197))/40, (sqrt(197) + 20)/40)
negative Choi eigenvalue = -1/40 in both variants
weak_shift_z fixed equations = (-3*x/10, -3*y/10, 1/10), solution=[]
```

These match the envelope rows for R3.1, R3.3, R3.5, and the anchor spectra in
`results/round3_s4_heavy_discriminator_v0_envelope_results.json`.

## Citable Per-Candidate Table

| Candidate | Registry heavy row | Citable verdict | Citable witness / caveat |
| --- | --- | --- | --- |
| `S4.R3.1_z_amplitude_damping_pair` | N01/commutator and fixed-axis rows | `excluded-by-N01-commutator-and-fixed-axis-rows` | `AD_z(gamma=1/5)` fixed set `{(0,0,1)}` plus exact z-probe order gap `(0, -(-3 + sqrt(5))/5, 1/5)`. Not pin-relative. |
| `S4.R3.2_x_amplitude_damping_pair` | z-probe quotient descent/mortality | `excluded-under-pinned-parent-z-probe-convention-by-z-probe-quotient-descent-mortality` | `AD_x(gamma=1/5)` sends the pinned z-probe to `(1/5,0,sqrt(5)/5)` with mortality break `x=1/5`, `z_delta=(-5 + 2*sqrt(5))/10`. Pin-relative and reopenable if the parent z-probe quotient or S4 role-order convention changes. |
| `S4.R3.3_dephase_rotate_hybrid` | shell preservation/leakage then N01 | `excluded-by-shell-preservation-leakage` | `D_z(1/2) o R_x(pi/2)` maps same-z-shell points to `(0,-1/4,0)` and `(0,-1/4,1/2)`, so `shell_preserved=false` with leakage witness `1/2`; lambda `7/10` leaks analogously. |
| `S4.R3.5_weak_nonunital_pauli_channel` | fixed-axis plus Choi positivity | `excluded-by-Choi-positivity-and-fixed-axis` | Both weak shifts have exact negative Choi eigenvalue `-1/40`; `weak_shift_z` also has no affine fixed-set solution. Choi-positivity row was actually computed. |

Known S4 R3 co-survivor classes after this packet: none.

## Controls

Accepted controls:

- Anchor self-passes every scoped heavy row it defines: exact Choi spectra are
  nonnegative and the anchor N01 row is internally consistent.
- The deliberate reparameterized anchor remains an exact alias:
  `anchor_hash == alias_hash ==
  fcdf80d7299ed39af0fc40357789d2b89688e2a6b3b09470822a8b658a5df597`.
- The S4 light-pass `S4.R3.4_axis_permuted_committed` regression remains
  `excluded-under-pinned-parent-z-probe-convention`, with z-probe delta
  `(0,0,-3/20)`.
- z3, cvc5, and Julia Z3 bind finite computed witness values:
  `S4.R3.1 AD_z(1/5) comm_gap_z_scaled_10 = 2`,
  `S4.R3.2 AD_x(1/5) quotient_x_scaled_10 = 2`, and
  `S4.R3.5 weak_shift choi_negative_scaled_40 = -1`.
  The real negated-erasure assertions are `unsat`; the erased/perturbed controls
  flip to `sat`.

SMT caveat: the SMT rows are load-bearing finite witness bindings, not a proof
of the full symbolic channel canonical form.

Correction annotation (demotion sweep `2ad726598` plus mechanical demotion
sweep 2): the sentence above is corrected to: SMT rows are supportive
hardcoded witness checks with a tautological flip; the SymPy exclusion rows are
the load-bearing evidence.

## Closure Scope

The no-co-survivor result means: within the registry's S4 round-3 finite
alternative space, the light pass already handled the anchor, exact alias
control, and `S4.R3.4`; this heavy-local packet answers the four remaining S4
queued neighbors and excludes all of them by their registry-named teeth.

Therefore the S4 round-3 discriminator queue is closed for the registered rows:

```text
S4.R3.1_z_amplitude_damping_pair - excluded
S4.R3.2_x_amplitude_damping_pair - excluded under pinned parent z-probe convention
S4.R3.3_dephase_rotate_hybrid - excluded
S4.R3.5_weak_nonunital_pauli_channel - excluded
```

This does not prove global S4 uniqueness. The registry explicitly bounds the
alternative space and says no row authorizes global uniqueness language.

## Named Caveats

C1 - Pin-relative R3.2:
`S4.R3.2_x_amplitude_damping_pair` is citable only under the pinned parent
z-probe quotient and S4 role-order convention inherited from the S4 light
verdict. Per the S2 convention-pin rule, changing that pin reopens the row as a
convention-relative alias/neighbor question.

C2 - Julia depth and spectrum order:
Julia and JAX verdict maps match, and Julia carries QuantumOptics plus Z3
reference evidence. Julia lists `R_x` and `R_z` Choi spectra as `(0,0,0,1)`
where JAX lists `(1,0,0,0)`. This is only an eigenvalue-order difference, not a
verdict split, but future citations should treat rotation spectra as multisets.

C3 - Package route depth:
qutip and QuantumOptics are real package-backed route checks over one-qubit
density/channel objects. The exact verdict rows remain SymPy/SMT plus Julia
reference tables; do not overcite qutip/QuantumOptics as independent full
canonical-form proof.

C4 - Rerun freshness:
I did not rerun the JAX lane, Julia lane, envelope builder, or packet-local
validator in place because those scripts rewrite result JSONs and this audit was
read-only except for this file. I instead ran scratch exact recomputation and
fresh read-only generic validators. The existing packet-local validator result
on disk is green with `errors=[]`.

C5 - On-disk state:
`system_v6/sims/round3_s4_heavy_discriminator_v0/` is currently untracked in
this checkout. This verdict accepts current on-disk evidence only; it does not
make the packet committed repo truth.

## Heavy Queue Disposition

The S4 portion of the consolidated heavy queue is now answered by this packet.
The remaining phase-2 heavy queue starts with S5's eight concrete rows next:

```text
S5.R3.1_alpha_mix_rotation_contraction__alpha_1_4 - mirror structure and N01 full signature
S5.R3.1_alpha_mix_rotation_contraction__alpha_1_2 - mirror structure and N01 full signature
S5.R3.1_alpha_mix_rotation_contraction__alpha_3_4 - mirror structure and N01 full signature
S5.R3.2_committed_coeff_epsilon__plus_1_20 - fixed-point/basin and N01 gap
S5.R3.2_committed_coeff_epsilon__minus_1_20 - fixed-point/basin and N01 gap
S5.R3.3_nonunital_weak_shift__plus_1_20 - validity, fixed point, quotient 56/56
S5.R3.3_nonunital_weak_shift__minus_1_20 - validity, fixed point, quotient 56/56
S5.R3.5_basin_preserving_null - quotient survival plus time-flow/N01 row
```

Do not relaunch S4 heavy work for count inflation unless the registry or pinned
convention changes.

## Future-Citation Rule

Future citations may say:

```text
round3_s4_heavy_discriminator_v0 is accepted as a bounded S4 phase-2
heavy-local scratch_diagnostic: the four queued S4 heavy rows were run under the
registry de44219ed teeth; R3.1 is excluded by N01/commutator plus fixed-axis
witnesses; R3.2 is excluded only under the pinned parent z-probe convention by
quotient descent/mortality; R3.3 is excluded by shell leakage; R3.5 is excluded
by Choi positivity/fixed-axis; no S4 R3 co-survivor was minted; the S4 queued
discriminator program is closed for registered rows only.
```

Future citations must not say:

```text
S4 uniqueness is proved; the registry alternative space is exhaustive beyond
its finite declaration; R3.2 is convention-independent; PyTorch evidence exists;
the packet is canonical by process; SMT proved the full symbolic channel
canonical form; qutip/QuantumOptics independently proved every exact row; the
remaining round-3 heavy queue is closed.
```

## Verification Commands

Fresh commands run by this audit:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 - <<'PY'
# scratch exact SymPy recomputation of anchor spectra, R3.1 fixed/order rows,
# R3.3 shell leakage, and R3.5 Choi negativity
PY
```

This scratch recomputation returned the exact values quoted in the
Exact-Witness Recompute section.

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 \
  scripts/validate_three_engine_sim_result.py \
  system_v6/sims/round3_s4_heavy_discriminator_v0/results/round3_s4_heavy_discriminator_v0_envelope_results.json
```

returned:

```json
{"ok": true, "result_json": "system_v6/sims/round3_s4_heavy_discriminator_v0/results/round3_s4_heavy_discriminator_v0_envelope_results.json"}
```

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 \
  scripts/validate_three_engine_sim_result.py --strict-source-backed \
  system_v6/sims/round3_s4_heavy_discriminator_v0/results/round3_s4_heavy_discriminator_v0_envelope_results.json
```

returned `ok=true`.

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 \
  scripts/validate_three_engine_sim_result.py --require-tool-intent \
  system_v6/sims/round3_s4_heavy_discriminator_v0/results/round3_s4_heavy_discriminator_v0_envelope_results.json
```

returned `ok=true`.

Expected PyTorch-scoped negative:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 \
  scripts/validate_three_engine_sim_result.py --require-pytorch \
  system_v6/sims/round3_s4_heavy_discriminator_v0/results/round3_s4_heavy_discriminator_v0_envelope_results.json
```

returned:

```json
{"ok": false, "errors": ["engines.pytorch must be an object"]}
```

## Route-Truth Note

Wizard v4.2 Max Assembly was partial. Two Codex-native read-only sidecars were
spawned for registry/source fidelity and controls/provenance, and both returned
before final closeout. No Claude/Gemini child hierarchy or full nine-parent Max
Assembly topology is claimed. Evidence for this verdict is direct repo
inspection, two completed sidecar receipts, scratch exact recomputation,
existing result files, and fresh read-only generic validator reruns.
