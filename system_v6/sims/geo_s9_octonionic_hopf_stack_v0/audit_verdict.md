# Audit verdict: geo_s9_octonionic_hopf_stack_v0

Scope: fresh read-only audit of `system_v6/sims/geo_s9_octonionic_hopf_stack_v0/`, except this `audit_verdict.md`.

Calibration: `system_v6/receipts/audit_bar_calibration_20260610.md` keeps convention/order pins, can-fail controls, load-bearing capability probes, route genuineness, erasure honesty, scratch ceilings, and fresh-context audits. It allows one genuine derivation plus independent solver/cross-engine binding where the split is honest.

Advisory pre-registration only: `system_v6/receipts/cross_model_anchor_recompute_panel3_20260610.md` predicts `S15 -> S8`, fiber `S7` not a Lie group, Adams termination, and `tau(GHZ_3)=1` / `tau(W_3)=0`. This packet earns those rows by computation; the panel is not counted as proof.

Wizard route note: native Codex subagent fanout was not run because the available `spawn_agent` tool contract in this session allows delegation only when explicitly requested by the user. This audit therefore uses controller-local source archaeology plus executable/tool recomputation and is not a FULL Wizard topology receipt.

## Verdict

PASS, with named caveats below. The packet earns a `scratch_diagnostic` result for the third Hopf fibration stack row:

- `classification=scratch_diagnostic`
- `promotion_allowed=false`
- `formal_admission_allowed=false`
- no formal admission, no canonical geometry admission, no principal `S7` connection/Chern row, no fifth Hopf rung, and no physics/SM/bridge/axis claim.

Fresh source-backed validator:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py system_v6/sims/geo_s9_octonionic_hopf_stack_v0/results/geo_s9_octonionic_hopf_stack_v0_envelope_results.json --require-source-backed
-> {"ok": true, "result_json": "system_v6/sims/geo_s9_octonionic_hopf_stack_v0/results/geo_s9_octonionic_hopf_stack_v0_envelope_results.json"}
```

## Q1. The map

Verdict: PASS.

Pinned convention is explicit in both legs and the envelope. Source quote from `geo_s9_octonionic_hopf_stack_v0_jax.py:37-43`:

```text
C8~=O2 by right-C_e1 convention: O basis over C_e1 is (e0,e2,e4,e5), complex i acts by right multiplication by e1
o1=C4(z0..z3),o2=C4(z4..z7)
Hopf_O=(2*o1*conj(o2),abs2(o1)-abs2(o2)) in OxR=S8
```

The coordinate formula is also emitted in the result: `(a0,b0,a1,-b1,a2,a3,b3,b2) for z_k=a_k+i*b_k`.

Fresh recomputation imported the Python exact leg without writing result files, normalized three deterministic rational-complex sample points, and recomputed `H_O(o1,o2)`. The base norm squared was exactly `1` for seeds `11`, `23`, and `37`.

Stored receipt agrees: named rows `north_product_000`, `south_product_100`, `equator_GHZ`, `W_3`, and the complex convention-control row all have `base_norm_squared=1`; the wrong-pairing control fires with nonzero diff norm.

## Q2. Moufang, not group

Verdict: PASS.

The nonassociativity witness is recomputed from the packet's table:

- triple `(e1,e2,e4)`
- `(e1*e2)*e4 = -e5`
- `e1*(e2*e4) = +e5`
- delta `-2e5`
- gap norm squared `4`

Controls collapse as required:

- quaternion subalgebra control `(e1,e2,e3)` gap norm squared `0`
- repeated-input alternativity control `(e1,e1,e4)` gap norm squared `0`

The Moufang identity row is derived from structure constants, not asserted. Source quote from `geo_s9_octonionic_hopf_stack_v0_jax.py:431-460`: the row builds `good_residuals = moufang_residuals(table)`, corrupts the table by flipping `e1*e2`, runs z3 and cvc5, and returns the identity `(x*y)*(z*x) == x*((y*z)*x)` over all basis units.

Fresh recomputation:

- basis triples checked: `512`
- residual components checked: `4096`
- z3 positive identity: `unsat`
- cvc5 positive identity: `unsat`
- z3 flipped-table control: `sat`
- cvc5 flipped-table control: `sat`

This supports the bounded statement: unit octonions form a Moufang loop, not a group. It ties cleanly to the committed associator direction as same-kind bracketing evidence, but it does not promote to formal algebra admission.

## Q3. Entanglement finding

Verdict: PASS, and this is the packet's strongest honesty row.

Source quote from `geo_s9_octonionic_hopf_stack_v0_jax.py:296-345`: the packet builds `GHZ_3`, `W_3`, two product states, and two biseparable states; emits `base_point_OxR`, `base_norm_squared`, `octonion_vector_norm_squared`, `R_coordinate`, `rho_A`, `one_tangle_A_BC`, and `tau_3`; and returns the finding that the base point is an `O2/A|BC` decomposition readout and "does not determine genuine tripartite tau".

Fresh recomputed rows:

| state | base point summary | one-tangle A|BC | tau_3 |
|---|---|---:|---:|
| `GHZ_3` | vector norm `1`, `R=0` | `1` | `1` |
| `W_3` | vector norm `8/9`, `R=1/3` | `8/9` | `0` |
| `product_000` | north pole, `R=1` | `0` | `0` |
| `product_plus_plus_plus` | equator `e0`, `R=0` | `0` | `0` |
| `biseparable_Bell_AB_tensor_0C` | vector norm `1`, `R=0` | `1` | `0` |
| `biseparable_0A_tensor_Bell_BC` | north pole, `R=1` | `0` | `0` |

The statement "what the map sees vs misses" matches the rows exactly: `GHZ_3` and `Bell_AB tensor 0C` both have equator vector norm `1` and one-tangle `1`, but `tau_3` differs `1` vs `0`. `W_3` has `tau_3=0` while the `A|BC` one-tangle is `8/9`. There is no oversell in this packet as a genuine tripartite tau detector.

## Q4. No-connection honesty

Verdict: PASS.

The packet states the standard principal-connection boundary: no `U(1)`/`Sp(1)`-style principal connection row applies because the fiber `S7` unit octonions are not a Lie group.

Replacement geometry is computed with Spin dimensions:

- `dim Spin(9)=36`
- `dim Spin(8)=28`
- `dim Spin(7)=21`
- `Spin(9)-Spin(8)=8`, matching `S8`
- `Spin(9)-Spin(7)=15`, matching `S15`

Fresh recomputation matched these integers. The result explicitly records `no_c4_or_chern_row=true`; grep found no fake `c4`/Chern decorative invariant in this packet.

## Q5. Sedenion convention adjudication

Verdict: PASS for this packet, with a cross-receipt correction finding.

Source quote from `geo_s9_octonionic_hopf_stack_v0_jax.py:537-553`: the packet recomputes both products under its Cayley-Dickson convention, requires the committed same-class `e5/e14` witness to be zero, requires the requested `e4/e13` spelling to be nonzero, and records an honesty note.

Fresh recomputation:

- `(e1+e10)(e4+e13)` product terms: `e5 - e7 + e12 - e14`; product norm squared `4`; zero product `false`.
- `(e1+e10)(e5+e14)` product terms: empty; product norm squared `0`; zero product `true`.

The packet pins the doubling rule in source: `first = a*c - conj(d)*b`, `second = d*a + b*conj(c)` (`geo_s9_octonionic_hopf_stack_v0_jax.py:139-143`), with basis ordering inherited from Cayley-Dickson doubling.

Cross-receipt correction finding: committed receipts elsewhere do cite `(e1+e10)(e4+e13)=0`.

- `system_v6/sims/bloch_root_admissibility_discriminator_v0/audit_verdict.md:45` records that spelling as a packet witness with zero product.
- `system_v6/sims/bloch_root_admissibility_discriminator_v0/audit_verdict.md:341` and `:373` clarify it as zero under that packet's doubled table/convention.
- `system_v6/receipts/nesting_law_audited_20260610.md:41` and `system_v6/receipts/nesting_law_audit_20260610.md:218` repeat the committed-packet spelling as convention-relative.

Correction needed outside this packet: do not port the Bloch packet's `(e1+e10)(e4+e13)=0` spelling into this S9 packet's committed Cayley-Dickson convention. The invariant safe claim is sedenion norm/fiber-law failure with convention-pinned witnesses; the zero witness for this packet is `(e1+e10)(e5+e14)=0`.

## Q6. Foliation

Verdict: PASS.

The packet derives `|o1|=cos(eta)`, `|o2|=sin(eta)`, generic leaf `S7_{cos eta} x S7_{sin eta}`, leaf volume

```text
pi**8*sin(eta)**7*cos(eta)**7/9
```

and exact total volume `pi**8/2520`.

Fresh recomputation:

- `integral_0^{pi/2} cos(eta)^7 sin(eta)^7 d eta = 1/280`
- total volume `pi**8/2520`
- normalized `eta` density `280 sin(eta)^7 cos(eta)^7`
- for `r=|o1|^2`, density `140*r^3*(1-r)^3`
- marginal normalization `integral_0^1 140*r^3*(1-r)^3 dr = 1`
- mean `1/2`
- degenerate endpoint controls fire with leaf volume `0` at `eta=0` and `eta=pi/2`

## Q7. Adams and ladder boundary

Verdict: PASS.

The packet names the Adams Hopf invariant one theorem, lists allowed base dimensions `[1,2,4,8]`, and states the four-rung ladder:

- `S0->S1->S1`
- `S1->S3->S2`
- `S3->S7->S4`
- `S7->S15->S8`

It explicitly says no fifth division-algebra sphere Hopf fibration `S15->S31->S16` or `S31` continuation. No fifth-fibration claim was found.

## Q8. Standard packet checks

Verdict: PASS with caveats.

Closed from the start:

- N01 label present in source and results.
- Principal-connection/holonomy honesty is fenced: no principal `S7` connection row; Spin replacement row computed.
- Solver/CAS versions recorded: Python `sympy 1.14.0`, `qutip 5.2.3`, `z3 4.16.0`, `cvc5 1.3.3`; Julia `1.12.6`, `Octonions 0.2.3`, `Z3 1.0.4`, `JSON 1.6.1`.
- Controls fire: product-state locus, bracketing shuffle, wrong-convention sign/coordinate flip, degenerate foliation endpoints, SMT erasure/flip, and requested sedenion display control.
- Mode is honest: `julia_canon_plus_jax_diagnostic`; PyTorch excluded because there is no graph, network, or autograd claim path.
- Capability receipts and one-to-one tool calls are present for claim-path tools: Julia `Octonions`, `Z3`; Python `sympy`, `qutip`, `z3`, `cvc5`.
- No `fixture` wording found in the packet.
- Seeds are deterministic: `rng=none`, named states/basis identities/exact symbolic integrals.
- No physics, Standard Model, bridge, axis, or formal-admission claim was found.

Named caveats:

1. `wizard_topology_deferred`: this audit is not a FULL Wizard v4.2 Max Assembly/subagent topology receipt because the callable subagent tool was contract-blocked without explicit delegation request.
2. `sedenion_cross_receipt_spelling_correction`: other committed receipts use or discuss `(e1+e10)(e4+e13)=0`; this S9 packet correctly rejects that spelling under its pinned convention and preserves `(e1+e10)(e5+e14)=0`.
3. `scratch_ceiling`: the result is a strong scratch diagnostic only. It is not canonical geometry admission, not formal scout admission, and not a bridge/physics result.
4. `qit_negative_boundary`: the octonionic base readout is useful for the pinned `O2/A|BC` split but must not be cited as a genuine tripartite entanglement detector.

## Final ceiling

Accepted ceiling: `passes local source-backed validator for a scratch diagnostic packet`.

Blocked consumers: formal admission, canonical geometry admission, principal-connection/Chern consumers, fifth-fibration ladder claims, tripartite tau-detector claims, bridge/axis/physics consumers.

Next admissible move: if this packet is to be strengthened, reconcile the cross-receipt sedenion spelling convention in a separate correction receipt without editing this packet's computed rows, then run any broader geometry-admission gate explicitly. This audit does not authorize promotion.
