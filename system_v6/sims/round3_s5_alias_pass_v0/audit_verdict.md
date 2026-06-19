# Fresh Audit Verdict: round3_s5_alias_pass_v0

Bottom line: VERDICT `ACCEPTED_WITH_NAMED_CAVEATS` as current on-disk
`scratch_diagnostic` S5 light-symbolic alias-pass evidence. The S4 correction
binds here: every not-run heavy-local S5 row labeled `co-survivor-open` in the
packet is citable only as `open + queued-heavy-local`. There are no accepted
new S5.R3 known co-survivors in this verdict.

This audit was read-only except for writing this file. I did not `git add` or
commit.

## Verdict

Accepted:

- `classification=scratch_diagnostic`.
- `promotion_allowed=false` and `formal_admission_allowed=false`.
- Honest mode `julia_canon_plus_jax_diagnostic` is legitimate for this
  light-symbolic exact canonicalization pass: no graph/network/autograd/tensor
  claim path exists, PyTorch omission is explicit, and the generic validator
  passes without `--require-pytorch`.
- `S5.R3.0_committed_8` self-classifies as anchor.
- Deliberate reparameterization control classifies as alias.
- Far wrong-sign `A` control dies on the first
  `eigenstructure/charpoly comparison` teeth row.
- `S5.R3.4_pairwise_LR_mirror_preserver` is accepted as a light-symbolic
  exclusion by the registry's Ni/Si mirror row, with caveat C3 below.
- The phase-2 queue contains exactly the eight heavy-local representatives.

Rejected or demoted:

- S5 uniqueness.
- Heavy-local S5 completion.
- New basin theorem, chart-independent basin class, or basin-preservation
  claim.
- PyTorch graph/tensor/autograd evidence.
- SMT proof of full surd canonical forms.
- Full independent Julia canonical-tuple rebuild.
- Any future citation of the not-run heavy-local rows as `co-survivor-open`.

## Corrected Per-Candidate Table

| Candidate | Packet verdict | Audit citable verdict |
| --- | --- | --- |
| `S5.R3.0_committed_8` | `anchor` | `anchor` |
| `S5.R3.1_alpha_mix_rotation_contraction__alpha_1_4` | `co-survivor-open` | `open + queued-heavy-local` |
| `S5.R3.1_alpha_mix_rotation_contraction__alpha_1_2` | `co-survivor-open` | `open + queued-heavy-local` |
| `S5.R3.1_alpha_mix_rotation_contraction__alpha_3_4` | `co-survivor-open` | `open + queued-heavy-local` |
| `S5.R3.2_committed_coeff_epsilon__plus_1_20` | `co-survivor-open` | `open + queued-heavy-local` |
| `S5.R3.2_committed_coeff_epsilon__minus_1_20` | `co-survivor-open` | `open + queued-heavy-local` |
| `S5.R3.3_nonunital_weak_shift__plus_1_20` | `co-survivor-open` | `open + queued-heavy-local` |
| `S5.R3.3_nonunital_weak_shift__minus_1_20` | `co-survivor-open` | `open + queued-heavy-local` |
| `S5.R3.4_pairwise_LR_mirror_preserver` | `excluded-by-Ni-Si-mirror-classification` | `excluded-by-Ni-Si-mirror-frame-row` / registry row `Ni/Si mirror classification` |
| `S5.R3.5_basin_preserving_null` | `co-survivor-open` | `open + queued-heavy-local` |

The table above is the S5 vocabulary normalization. The only S5.R3 survivor
vocabulary allowed after this audit is `open + queued-heavy-local` unless a
future receipt runs the registry-named heavy teeth or cites a prior known
co-survivor receipt. The prior `B_hamiltonian_only` context remains cited only
to `geo_s5_alternative_flow_families_v0`; it does not make any current R3 row a
known co-survivor.

## Canonical-Form Reality

The claim path is exact-symbolic. The Python/SymPy lane parses the pinned
`geo_s5_terrain_flows_v0` `A,b` rows over exact rationals/surds, emits canonical
tuples with `A_exact`, `b_exact`, `fixed_point_exact`, `mirror_class`,
`N01_signature`, `eigenstructure_charpoly`, and trapping coefficients, and
compares canonical hashes before verdicting.

Fresh scratch recomputation matched the controls:

```text
anchor canonical hash equals self: true
control.alias_reparameterized_committed -> alias
control.wrong_sign_A -> excluded-by-eigenstructure-charpoly-comparison
```

Wrong-sign first teeth row on `Se_Funnel_L`:

```text
anchor charpoly    = (5*mu + 4)*(5*mu**2 + 8*mu + 4)/25
candidate charpoly = (5*mu - 4)*(5*mu**2 - 8*mu + 4)/25
anchor A01         = -2*sqrt(3)/15
candidate A01      =  2*sqrt(3)/15
gap                =  4*sqrt(3)/15
```

## Exact Witness Checks

R3.2 coefficient perturbation, plus `1/20`, on `Ne_Spiral_R`:

```text
registry row       = fixed-point/basin and N01 gap
verdict            = open + queued-heavy-local
anchor A01         = 2*sqrt(3)/3
candidate A01      = (3 + 40*sqrt(3))/60
gap                = 1/20
anchor charpoly    = mu*(mu**2 + 4)
candidate charpoly = (30*mu**3 + sqrt(3)*mu + 120*mu - 2)/30
anchor fixed set   = kernel_dimension_1, basis [1, 1, 1]
candidate fixed    = single_point at [0, 0, 0]
anchor trapping    = [0]
candidate trapping = [-1/40, 1/40, 0]
```

R3.3 nonunital weak shift, plus `1/20`, on `Ni_Pit_L`:

```text
registry row       = validity, fixed point, quotient 56/56
verdict            = open + queued-heavy-local
anchor b_z         = -1/2
candidate b_z      = -9/20
gap                = 1/20
anchor fixed       = [-8*(8 + 5*sqrt(3))/203, 8*(-8 + 5*sqrt(3))/203, -139/203]
candidate fixed    = [-36*(8 + 5*sqrt(3))/1015, 36*(-8 + 5*sqrt(3))/1015, -1251/2030]
anchor trapping    = [-1/4, -1/2]
candidate trapping = [-1/4, -1/2]
```

R3.5 basin-preserving-null row on `Se_Funnel_L`:

```text
registry row       = quotient survival plus time-flow/N01 row
verdict            = open + queued-heavy-local
fixed point equal  = true, both [0, 0, 0]
anchor charpoly    = (5*mu + 4)*(5*mu**2 + 8*mu + 4)/25
candidate charpoly = (5*mu + 4)*(735*mu**2 + 1176*mu + 28*sqrt(3) + 603)/3675
anchor A01         = -2*sqrt(3)/15
candidate A01      = -(15 + 14*sqrt(3))/105
gap                = -1/7
trapping coeffs    = [-4/5] for both
```

This is exactly why R3.5 must not be cited as basin-preserving evidence. The
same fixed point is not enough; transient/time-flow/N01 heavy-local teeth are
still queued.

R3.4 mirror-preserver stress:

```text
packet verdict     = excluded-by-Ni-Si-mirror-classification
registry row       = Ni/Si mirror classification
exact split field  = Ni_Pit_L.A_exact
anchor A01         = -2*sqrt(3)/15
candidate A01      = -(-1 + 4*sqrt(3))/30
gap                = 1/30
```

Named caveat C3 applies: the packet's coarse `mirror_class` labels remain the
same for anchor and candidate, so future citations should name the exact Ni/Si
frame-row split, not claim that the coarse `mirror_class` string changed.

## Controls And Solvers

Controls pass:

- Anchor self-classifies.
- Deliberate exact reparameterization is alias.
- Wrong-sign `A` dies on the first charpoly/eigenstructure row.

z3, cvc5, and Julia Z3 all report the same finite rational witness polarity:

```text
positive nonzero-negation: unsat
erased/zero flip: sat
witnesses:
  r3_2_open_coeff_gap_times_20 = 1
  r3_4_mirror_gap_times_60 = 2
  wrong_sign_gap_squared_times_75 = 16
```

SMT depth caveat: this is a finite rational nonzero-witness cross-check. It
does not prove the full surd canonical tuples or run the heavy-local time-flow,
basin, Choi, or topology-style rows.

## Named Caveats

C1 - On-disk state:
`system_v6/sims/round3_s5_alias_pass_v0/` is untracked in this checkout. This
verdict accepts current on-disk evidence only; it does not make the packet
committed repo truth until checkpointed.

C2 - S4 vocabulary normalization:
All heavy-local rows that survived the light pass are `open +
queued-heavy-local`, not `co-survivor-open`, because no prior co-survivor
receipt is cited for these exact S5.R3 rows and their heavy-local teeth were
not run.

C3 - R3.4 witness wording:
`S5.R3.4_pairwise_LR_mirror_preserver` is accepted as a light-symbolic
exclusion under the registry's Ni/Si mirror row, but the exact evidence is an
`A_exact` Ni/Si frame-row perturbation. The coarse `mirror_class` labels do not
change in the scratch recomputation.

C4 - Julia depth:
Julia is a verdict-map plus Z3.jl finite-witness sidecar. It does not
independently rebuild the full canonical terrain tuple.

C5 - SMT depth:
SMT binds finite rational witnesses with flip controls. Surd comparisons,
charpolys, fixed-point rows, and trapping coefficients remain CAS-backed.

C6 - Basin/chart discipline:
Any class, basin, or fixed-point language is chart-relative and open unless
receipt-backed by the heavy-local row. R3.5 shares a fixed point and trapping
coefficient with the anchor row but changes transient charpoly/A rows; cite it
only as `open + queued-heavy-local`.

C7 - Validator scope:
I did not rerun `validate_round3_s5_alias_pass_v0.py` because it writes
`results/round3_s5_alias_pass_v0_validator_results.json`. The existing
packet-local validator result is green. Fresh read-only generic validators are
listed below.

## Verification Commands

Fresh read-only validators:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py system_v6/sims/round3_s5_alias_pass_v0/results/round3_s5_alias_pass_v0_envelope_results.json
-> {"ok": true, "result_json": "system_v6/sims/round3_s5_alias_pass_v0/results/round3_s5_alias_pass_v0_envelope_results.json"}

/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-source-backed system_v6/sims/round3_s5_alias_pass_v0/results/round3_s5_alias_pass_v0_envelope_results.json
-> {"ok": true, "result_json": "system_v6/sims/round3_s5_alias_pass_v0/results/round3_s5_alias_pass_v0_envelope_results.json"}

/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --strict-source-backed system_v6/sims/round3_s5_alias_pass_v0/results/round3_s5_alias_pass_v0_envelope_results.json
-> {"ok": true, "result_json": "system_v6/sims/round3_s5_alias_pass_v0/results/round3_s5_alias_pass_v0_envelope_results.json"}

/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-tool-intent system_v6/sims/round3_s5_alias_pass_v0/results/round3_s5_alias_pass_v0_envelope_results.json
-> {"ok": true, "result_json": "system_v6/sims/round3_s5_alias_pass_v0/results/round3_s5_alias_pass_v0_envelope_results.json"}
```

Expected PyTorch-scoped negative:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch system_v6/sims/round3_s5_alias_pass_v0/results/round3_s5_alias_pass_v0_envelope_results.json
-> {"ok": false, "errors": ["engines.pytorch must be an object"]}
```

Packet-local validator on disk reports `ok=true`, `validator_ok=true`, no
errors, exactly eight heavy-local queued rows, and no current known
co-survivors not heavy-queued.

## Phase-2 Disposition

Phase 2 for S5 is exactly the registry heavy-local queue:

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

Do not relaunch a broad S5 battery for count inflation. The next admissible S5
work is a narrow phase-2 heavy-local packet over those eight rows, with R3.5
held to chart-relative time-flow/N01 discipline and no basin-class promotion.

## Future-Citation Rule

Future citations may say:

```text
round3_s5_alias_pass_v0 is accepted with named caveats as on-disk
scratch_diagnostic S5 phase-1 light-symbolic evidence: exact canonical-form
anchor and alias controls passed; far wrong-sign A dies on first
charpoly/eigenstructure row; S5.R3.4 is excluded by the registry Ni/Si mirror
row via exact Ni/Si frame-row perturbation; heavy-local S5.R3.1, R3.2, R3.3,
and R3.5 remain open + queued-heavy-local under the S4 vocabulary correction.
```

Future citations must not say:

```text
S5 is unique; S5 heavy-local is complete; S5.R3.1/R3.2/R3.3/R3.5 are known
co-survivors; S5.R3.5 is a basin-preserving survivor; R3.4 changed the coarse
mirror_class labels; PyTorch evidence exists; SMT proved the full canonical
tuple; Julia independently rebuilt the full canonical tuple; numeric closeness
established alias status.
```

## Route-Truth Note

Wizard v4.2 Max Assembly was partial. The available subagent tool in this
runtime permits spawning only when the user explicitly asks for subagents or
delegation, so no worker plurality, child hierarchy, or full Max Assembly
topology is claimed. Evidence for this verdict is direct repo inspection,
scratch exact recomputation, existing packet result files, and fresh read-only
generic validator reruns.
