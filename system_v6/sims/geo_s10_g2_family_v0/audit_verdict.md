# Audit verdict: geo_s10_g2_family_v0

Scope: fresh codex2 cross-backend audit of `system_v6/sims/geo_s10_g2_family_v0`, read-only except this file. I audited against both preregistrations:

- `system_v6/receipts/cross_model_anchor_recompute_panel3_20260610.md`: `0/3/14`, `1+7+14+27`, `14/21/28` with `Out=S3` order `6`, `168/168/480`, and `SU(3)` stabilizer dimension `8` / coset `6`.
- `/tmp/s10_g2_blind_expectations.md`: row-by-row S10 expectations and the five fabrication risks.

Calibration used: `system_v6/receipts/audit_bar_calibration_20260610.md`, which keeps route genuineness, can-fail controls, capability-probe gates, erasure honesty, scratch ceilings, and fresh-context audits, while allowing one genuine derivation plus independent solver/cross-engine binding when the split is honest.

## Verdict

VERDICT: `GENUINE-WITH-CAVEATS`.

The load-bearing math rows are earned by computation, not by preregistration echo. I independently rebuilt the derivation linear systems from the packet's structure-constant builders and got:

```text
C: nullity 0
H: rank 13, nullity 3
M2R: rank 13, nullity 3
O_compact: rank 50, nullity 14
O_split: rank 50, nullity 14
O_compact_one_sign_flipped: rank 61, nullity 3
```

Ceiling: `scratch_diagnostic S10 G2-family map only`; `promotion_allowed=false`; `formal_admission_allowed=false`; no canonical theorem, bridge, axis, physics, or Standard Model claim is admitted.

Named caveats:

- `G1-mode-label`: the envelope says `engine_contract.mode = all_three_full_sims`, but the JAX and PyTorch lanes are supportive wrappers around the shared exact Python/SymPy builder. This does not kill the math rows, but the honest mode is closer to "Julia carrier + shared exact Python/SymPy/JAX/PyTorch wrappers + Nemo sidecar", not three independent backend derivations of every row.
- `G2-tool-metadata`: `claim_path_tools` is imperfectly one-to-one at the aggregation boundary. The envelope aggregates claim tools while its own top-level `tool_calls` list is empty, and the Nemo sidecar lists `Hecke` in `claim_path_tools` even though `Hecke` is marked supportive and only `Nemo` has a function-level tool call. The actual load-bearing tools do have lane-local function-level receipts, so this is a metadata caveat, not a math failure.
- `G3-triality-scope`: the triality row computes D4 diagram/character-node automorphism order, not explicit intertwiners. This is acceptable for the preregistered `Out(Spin(8)) = S3` order row, but the row must not be widened beyond D4 diagram/character-node automorphism order, not explicit intertwiners.

## Q1 Derivations

Source construction quote: `geo_s10_g2_family_v0_common.py:103-108` defines the Cayley-Dickson split, including "`gamma=-1 gives the division step`" and "`gamma=+1 at H -> O gives the split octonions`". `geo_s10_g2_family_v0_common.py:166-180` builds the derivation matrix for `D(xy)=D(x)y+xD(y)`, and `geo_s10_g2_family_v0_common.py:187-203` records exact rank/nullity via SymPy.

Independent recomputation: I rebuilt the full equation matrix myself from the packet's table constants, without using `derivation_summary`. Results:

```text
O_compact: 512 equations, 64 unknowns, rank 50, nullity 14
O_split: 512 equations, 64 unknowns, rank 50, nullity 14
H: 64 equations, 16 unknowns, rank 13, nullity 3
C/R table: 1 equation, 1 unknown, rank 1, nullity 0
O_compact_one_sign_flipped: 512 equations, 64 unknowns, rank 61, nullity 3
```

Adjudication: `Der(O)=14` is computed. The quaternion designed-fail/control is `3`. The complex/one-dimensional associative control is `0` in the packet-local real scalar table route. The sign-flipped compact table breaks `14` and recomputes to `3`.

## Q2 Split G_2(2)

Source construction quote: `geo_s10_g2_family_v0_common.py:142-143` builds split octonions with `cd_double(table_h(), 1)`. The result labels the real form as "split G_2(2), not finite Chevalley G2(2)" and states the convention "H->O_split with gamma=+1; N(a,b)=N(a)-N(b)" in `geo_s10_g2_family_v0_common.py:879-882`.

Independent recomputation:

```text
compact full norm diag: [1,1,1,1,1,1,1,1]
split full norm diag: [1,1,1,1,-1,-1,-1,-1]
compact full signature: (8,0)
split full signature: (4,4)
compact imaginary signature: (7,0)
split trace-zero signature: (3,4)
```

At least one diverging row verified: wrong-form metric preservation is false both ways, with nonzero residuals. The packet reports `compact_derivations_with_split_metric.preserves=false` and `split_derivations_with_compact_metric.preserves=false`, each with `nonzero_entries=32` and `max_abs_entry=2`. The split zero-divisor witness also recomputed true: `v=[0,1,0,0,1,0,0,0]`, nonzero partner same vector, product zero.

Adjudication: split constants are genuinely different from compact constants; split derivation dimension is computed as `14`; compact-vs-split divergence rows are real.

## Q3 7x7 Decomposition

Source construction quote: `geo_s10_g2_family_v0_common.py:366-431` builds tensor projectors and the Lambda^2 cross-product map from the compact table. It records the computation as "metric trace projector plus octonion cross-product map on Lambda^2".

Independent projector-rank recomputation:

```text
Symmetric projector rank: 28
Antisymmetric projector rank: 21
Trace projector rank: 1
Symmetric trace-free projector rank: 27
Lambda^2 cross-product image rank: 7
Lambda^2 kernel rank: 14
```

Adjudication: the decomposition `7x7 = 1+7+14+27`, total `49`, is computed by projectors/cross-product rank, not just asserted.

## Q4 Chain And Triality

Source construction quote: `geo_s10_g2_family_v0_common.py:461-509` builds the Cayley 4-form action on the `so(8)` basis pairs and computes the Spin(7) stabilizer dimension. `geo_s10_g2_family_v0_common.py:512-545` checks G2 preservation of the Cayley form, closure in the 7d action, and D4 diagram/character-node automorphism order, not explicit intertwiners.

Recomputed/adjudicated rows:

```text
G2 dimension from derivations: 14
Spin(7) stabilizer dimension from Cayley-form action: 21
so(8) basis dimension: 28
difference dimensions: 7, 7, 14
G2 extended derivations preserve Cayley form: true
G2 closure in 7d action: true
D4 automorphism order: 6
```

Adjudication: the chain dimensions and G2 embedding closure checks are computed. Triality is genuine only as D4 diagram/character-node automorphism order, not explicit intertwiners; see `G3-triality-scope`.

## Q5 Finite Structures

Nemo source quote: `geo_s10_g2_family_v0_nemo_hecke.jl:49-81` enumerates all `2x2` matrices over `GF(7)`, counts `SL(2,7)`, quotients by `+/-I`, and computes Borel/unipotent subgroup counts. The tool call at `geo_s10_g2_family_v0_nemo_hecke.jl:111-122` names `Nemo.GF/lift`, input "all 2x2 matrices over GF(7)", and boundary "finite sanity row only, not compact/split Lie-form proof".

Independent recomputation using the same committed probe pattern:

```text
SL(2,7): 336
PSL(2,7): 168
Borel/point stabilizer: 21
Unipotent/Sylow-7: 7
Subgroup chain: [168,21,7,1]
GL(3,2) / PGL(3,2) binary matrix count: 168
```

Orientation enumeration source quote: `geo_s10_g2_family_v0_common.py:611-662` enumerates Fano automorphisms, labelled line systems, valid sign choices, transported table hashes, and phi hashes.

Recomputation:

```text
Fano line count: 7
Fano automorphism order by incidence permutations: 168
labelled Fano triad arrangements: 30
valid sign/orientation choices: 16
orientation family count: 480
transported table hash count: 480
transported phi hash count: 480
associator control: 42 zero Fano-line triples, 168 nonassociating triples, 210 ordered distinct triples
```

Adjudication: `168`, `168`, and `480` are computed. The packet also correctly guards against finite-group substitution: finite rows are sanity rows, not Lie-form proof.

## Q6 Hybrid/Set Rows

Source construction quote: `geo_s10_g2_family_v0_common.py:831-838` computes two compact stabilizer choices and split stabilizer samples by causal class. `geo_s10_g2_family_v0_common.py:299-363` searches a signed automorphism from `e1` to `e2` and verifies conjugacy of stabilizer subspaces.

Recomputation:

```text
compact stabilizer e1: constraint rank 6, stabilizer dim 8, orbit dim 6
compact stabilizer e2: constraint rank 6, stabilizer dim 8, orbit dim 6
conjugacy check: found signed automorphism; conjugate_subspaces_equal=true
split samples: positive, negative, and null vector rows are computed separately; compact SU(3) label is not copied to split rows
```

Nesting-taxonomy row: bounded citation to `system_v6/receipts/nesting_law_audited_20260610.md`; it survives only as group-action / preservation-group / algebra-extension taxonomy support, not as Lie-form proof.

Adjudication: hybrid/set rows are honest and bounded.

## Q7 Controls

Controls source quote: `geo_s10_g2_family_v0_common.py:925-936` names the fabrication controls, sign-flip control, quaternion control, M2R anchor, and z3/cvc5 erased flips.

Recomputed controls:

```text
dimension_echo_without_linear_system_rejected: true
compact_split_conflation_rejected: true
finite_group_substitution_rejected: true
orientation_table_theater_rejected: true
stabilizer_copy_paste_to_split_rejected: true
one_sign_flip_breaks_dim_14: true, with corrupt Der dim 3
quaternion_associative_control_dim_3: true
M2R anchor dim 3: true
z3 erased flip: real UNSAT, erased SAT
cvc5 erased flip: real UNSAT, erased SAT
shuffle/permuted transport control: table hash changed while transported Der dim remains 14; label-only comparison rejected
```

Adjudication: all five blind-sheet fabrication risks are explicitly covered:

- Dimension echo: passed; dims come from linear-system nullities.
- Compact/split collapse: passed; signatures, zero-divisor witness, and wrong-form controls are computed.
- Finite group substitution: passed; PSL rows are bounded as finite sanity only.
- Orientation-table theater: passed; 480 comes from enumeration and hash counts.
- Stabilizer copy-paste: passed; compact stabilizers and split causal samples are separated.

## Q8 Standard / Metadata

What passes:

- Family-map honesty: the envelope disallows "canonical family theorem", "crowned winner among family members", and "bridge, axis, physics, or manifold promotion".
- Ceiling: envelope and lanes preserve `classification=scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`.
- Peer reads: lanes report `reads_peer_result=false`; envelope gate `no_peer_result_reads=true`.
- Seeds: engine lanes record `geo_s10_g2_family_v0_seed_20260610`.
- Capability/project receipts: Julia result records active project `system_v5/julia_carrier/Project.toml`; Nemo sidecar records active project `system_v6/optional/nemo_hecke/Project.toml`.
- Validator: `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/geo_s10_g2_family_v0/geo_s10_g2_family_v0_exact_strength_validator.py` returned `{"ok": true, "mode": "scratch_diagnostic_family_map"}`.

What remains caveated:

- `G1-mode-label`: `all_three_full_sims` overstates the independence of JAX/PyTorch rows; they are supportive wrappers over the shared exact Python/SymPy builder. JAX and PyTorch are not decorative in metadata because they run source probes and mark their own packages supportive, but they are not independent mathematical engines for the decisive rows.
- `G2-tool-metadata`: top-level and Nemo claim-path metadata should be tightened before any later packaging pass. In particular, do not count `Hecke` as claim-bearing without a Hecke function-level tool call, and do not rely on the envelope's aggregate `claim_path_tools` as one-to-one evidence.
- `G3-triality-scope`: the triality computation should stay scoped to D4 diagram/character-node automorphism order, not explicit intertwiners.

Final adjudication: the packet meets the calibrated bar as a `GENUINE-WITH-CAVEATS` scratch diagnostic family map. It earns the panel-3 and blind-sheet numeric targets by computation, but it does not earn promotion, formal admission, canonical status, or a stronger all-three-independent-engine claim.

## Builder Hardening Addendum - 2026-06-11

Bounded hardening result: `G1-mode-label` and `G2-tool-metadata` are closed in the builder output. `G3-triality-scope` is carried as an honest scope fence, not closed by widening: every triality citation is scoped to D4 diagram/character-node automorphism order, not explicit intertwiners.

What changed:

- `G1-mode-label`: envelope `engine_contract.mode` is now `julia_canon_plus_jax_diagnostic`, with declared lanes `["julia", "jax"]`. PyTorch is still fully rerun, but is explicitly a supportive wrapper because this packet has no graph/network/autograd claim path and does not require PyTorch for the declared-mode validator.
- `G2-tool-metadata`: envelope top-level `tool_calls` now aggregates lane-local function-level receipts plus the Nemo sidecar. Nemo sidecar `claim_path_tools` is now `["Nemo"]`; Hecke remains supportive only.
- `G3-triality-scope`: retained as a scope fence. The row says D4 diagram/character-node automorphism order, not explicit intertwiners.

Fresh rerun commands all exited 0:

```text
julia --project=system_v5/julia_carrier system_v6/sims/geo_s10_g2_family_v0/geo_s10_g2_family_v0_julia.jl
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/geo_s10_g2_family_v0/geo_s10_g2_family_v0_jax.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/geo_s10_g2_family_v0/geo_s10_g2_family_v0_pytorch.py
julia --project=system_v6/optional/nemo_hecke system_v6/sims/geo_s10_g2_family_v0/geo_s10_g2_family_v0_nemo_hecke.jl
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/geo_s10_g2_family_v0/geo_s10_g2_family_v0_envelope.py
```

Fresh validator/capability commands all exited 0:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/geo_s10_g2_family_v0/geo_s10_g2_family_v0_exact_strength_validator.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --strict-source-backed system_v6/sims/geo_s10_g2_family_v0/results/geo_s10_g2_family_v0_envelope_results.json
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/verify_load_bearing_has_capability_probe.py --sim system_v6/sims/geo_s10_g2_family_v0/geo_s10_g2_family_v0_julia.jl
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/verify_load_bearing_has_capability_probe.py --sim system_v6/sims/geo_s10_g2_family_v0/geo_s10_g2_family_v0_jax.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/verify_load_bearing_has_capability_probe.py --sim system_v6/sims/geo_s10_g2_family_v0/geo_s10_g2_family_v0_pytorch.py
```

Quoted results:

```text
packet validator: {"ok": true, "mode": "julia_canon_plus_jax_diagnostic"}
declared-mode validator: {"ok": true}
capability helpers: Julia, JAX, and PyTorch returned "violations": []
```

Audited exact rows stayed stable on rerun:

```text
compact nullity/rank: 14/50
split nullity/rank: 14/50
control nullities H/M2R/corrupt_O: 3/3/3
tensor blocks and sum: [1, 7, 14, 27] -> 49
PSL/Fano/orientation counts: 168/168/480
triality order: 6, scoped to D4 diagram/character-node automorphism order, not explicit intertwiners
```
