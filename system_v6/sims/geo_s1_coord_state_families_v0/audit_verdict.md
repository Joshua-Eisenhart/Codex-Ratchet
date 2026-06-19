# Fresh Audit Verdict - geo_s1_coord_state_families_v0

Audit date: 2026-06-10

Scope: read-only audit of the packet, with this `audit_verdict.md` as the only write. Calibration bar: `system_v6/receipts/audit_bar_calibration_20260610.md`. Geometry program receipt: `system_v6/receipts/geometry_sim_program_canonical_20260610.md`.

## Bottom Line

VERDICT: `GENUINE-WITH-CAVEATS`.

The packet is a genuine S1 `QUOTIENTED` scratch diagnostic for coordinate-dependent state-family entropy rows: the GHZ-W family consumes the shell coordinate through `t = sin(eta)^2`, exact symbolic endpoint anchors are emitted, numerical curves match independent recomputation, the GHZ-W separability crossing is absent by recomputation, quotient rows separate phase/weight survival, and controls can fail.

It does not fully close lifted-rung G7. It closes only the S1 scratch-diagnostic portion of G7, and even that closure carries a named per-site-coordinate caveat: the W-site-weighted row uses symbolic weights `w_i` and records `w_i=eta_i^2` in the family string, but it does not expose an executable amplitude-vector constructor that consumes an `eta_i` shell-coordinate vector.

Ceiling: `scratch_diagnostic`; `promotion_allowed=false`; `formal_admission_allowed=false`; no canonical, admitted, bridge, axis-level, or lifted-rung closure claim.

## Sources Quoted

Coordinate entry for the scalar GHZ-W family is executable:

> `eta = sp.symbols(f"eta_{n}", real=True)`
>
> `t = sp.sin(eta) ** 2`
>
> `a = (1 - t) / 2 + t * sp.Rational(n - 1, n)`
>
> `d = (1 - t) / 2 + t * sp.Rational(1, n)`
>
> `offdiag_sq = (1 - t) * t / (2 * n)`

Source: `system_v6/sims/geo_s1_coord_state_families_v0/geo_s1_coord_state_families_v0_common.py:55-60`.

The W-site-weighted family is weight-symbolic and only declares the eta mapping in the emitted family string:

> `weights = sp.symbols(" ".join(f"w{n}_{i}" for i in range(n)), nonnegative=True)`
>
> `p = sp.simplify(weight / total)`
>
> `"|W(eta_i)> = sum_i sqrt(w_i/sum_j w_j)|0..1_i..0>, with w_i=eta_i^2 in numeric rows"`

Source: `system_v6/sims/geo_s1_coord_state_families_v0/geo_s1_coord_state_families_v0_common.py:97-115`.

The declared quotient/ceiling is explicit:

> `"stage": "S1",`
>
> `"mode": "QUOTIENTED",`
>
> `"classification": CLASSIFICATION,`
>
> `"promotion_allowed": PROMOTION_ALLOWED,`
>
> `"formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,`

Source: `system_v6/sims/geo_s1_coord_state_families_v0/geo_s1_coord_state_families_v0_common.py:180-185`.

## Q1 - Genuine Coordinate Coupling

Adjudication: PASS for scalar GHZ-W coordinate coupling; PARTIAL for per-site `eta_i`.

The GHZ-W family is not a label join. The source constructs reduced-density entries from `t = sin(eta)^2`, and the numerical lanes recompute those rows over a 17-point eta grid. Changing eta changes `a`, `d`, `offdiag_sq`, determinant, eigenvalues, and entropy.

The W-site-weighted family is not pure prose because its site probabilities and entropies are symbolic functions of `w_i/(sum_j w_j)`. But the packet does not executable-bind `w_i = eta_i^2` in the symbolic rows, nor does it expose a state-vector constructor like `psi(eta_vec) -> amplitudes`. That leaves G1 below.

## Q2 - Exact Curves And Recomputations

Adjudication: PASS.

The JAX/Sympy lane emits exact entropy expressions and endpoint checks for `n=3` and `n=4`; the Julia and JAX numeric curves agree at checked rows. I independently recomputed from the determinant formula, without importing the packet helper.

Recomputed GHZ-W determinant rows:

| n | det(u) | det(0) | det(1/2) | det(1) | roots in [0,1] |
| --- | --- | ---: | ---: | ---: | --- |
| 3 | `(5*u^2 - 6*u + 9)/36` | `1/4` | `29/144` | `2/9` | none |
| 4 | `(u^2 - 2*u + 4)/16` | `1/4` | `13/64` | `3/16` | none |

Hand recomputed entropy points:

| n | eta | t | lambda_min | S |
| --- | ---: | ---: | ---: | ---: |
| 3 | `0` | `0` | `0.5` | `0.693147180559945` = `ln(2)` |
| 3 | `pi/4` | `0.5` | `0.279520724077951` | `0.592500089834324` |
| 3 | `pi/2` | `1` | `1/3` | `0.636514168294813` = `-2*log(2)/3 + log(3)` |
| 4 | `0` | `0` | `0.5` | `0.693147180559945` = `ln(2)` |
| 4 | `pi/4` | `0.5` | `0.283493649053890` | `0.596222739415007` |
| 4 | `pi/2` | `1` | `0.25` | `0.562335144618808` = `log(4*3**(1/4)/3)` |

Stored rows match these recomputations at the checked endpoint and interior points.

## Q3 - Separability Boundary

Adjudication: PASS for GHZ-W absence of crossing; PASS for W-weighted product boundary row with G1 scope.

For GHZ-W, recomputation gives positive determinant over `[0,1]`; there are no roots in the closed interval. The packet's z3/cvc5 rows report `unsat` for `det == 0` over `0 <= u <= 1`, with z3 positive controls reporting `sat`. This supports "no one-site separability crossing" for the GHZ-W interpolation.

For W-weighted, the emitted boundary is `p_excited in {0,1}` and "one nonzero coordinate weight." Independent recomputation for weights `[1,0,0]` gives probabilities `[1,0,0]` and entropies `[0,0,0]`. This is computed at the probability/weight level; the `eta_i` amplitude-constructor caveat remains.

## Q4 - Density Quotient

Adjudication: PASS.

The packet is consistent with committed B1: global phase is erased by `rho = psi psi^dagger`; weights survive; relative phase can survive in off-diagonal density entries but the entropy row is phase-independent.

Relevant emitted rows:

- `phase_survives_rho_offdiag: true`
- `entropy_phase_independent: true`
- `erased_by_rho: ["global phase alpha(eta)"]`
- `survives_rho: ["relative GHZ/W phase in offdiagonal rho entries"]`
- W-weighted rows keep `p_excited = w_i / sum_j w_j`.

## Q5 - Controls Fire

Adjudication: PASS WITH G2.

The flat control is able to fail the coupling claim: it emits a constant `ln(2)` curve with `max_minus_min = 0` and names failure semantics as "flat entropy curve means this control did not couple the state to shell coordinate eta."

The permutation control fires when weights are site-dependent. Independent recomputation for `[1,2,3]` versus `[3,2,1]` gives probabilities `[0.0714285714, 0.2857142857, 0.6428571429]` versus `[0.6428571429, 0.2857142857, 0.0714285714]`; entropy vectors reverse accordingly. The equal-weight curve remains unchanged.

The erased-phase family collapses under the quotient and has a flat entropy curve. This can fail if the quotient row stops erasing global phase.

G2: controls are present and can fail at the row level, but they are not all full reruns of a state-vector construction under mutated shell-coordinate inputs. They are adequate for this S1 scratch diagnostic, not for lifted-rung closure.

## Q6 - Mode, Tooling, Seeds, Ceilings

Adjudication: PASS WITH G3.

The geometry mode `QUOTIENTED` is honest for this packet. The geometry program defines `QUOTIENTED` as seeing a layer through lower quotients and asks what survives, such as density quotient erasure. This packet's actual rows are density quotient rows over `rho_A`, endpoint anchors, and phase/weight survival.

Seeds and pins are present:

- `seed = coord_state_families_seed_v0_exact_eta_grid_0_pi_over_2_17`
- pin includes `stage=S1`, `mode=QUOTIENTED`, `anchors=GHZ_ln2,Wn_H((n-1)/n)`, `density_quotient_phase_erasure`, `classification=scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`.

Tooling:

- Normal validator passed: `scripts/validate_three_engine_sim_result.py --require-pytorch --require-source-backed ...` returned `ok=true`.
- Strict validator failed on one narrow source-backed issue: `pytorch: strict source-backed audit requires no thin declared claims: declared load-bearing packages imported but source-token-thin: sympy`.
- Source-backed lane classification from `scripts/audit_three_engine_source_claims.py`: JAX `source_backed_rich_tool_claim`; Julia `source_backed_rich_tool_claim`; PyTorch `mixed_source_backed_with_thin_claims`.
- Source hashes recorded in lane JSON match current source files for JAX, Julia, PyTorch, and envelope.
- `reads_peer_result=false` is recorded for the lanes, and the envelope's divergence comparison is cross-lane comparison rather than cross-run parity evidence.

G3: PyTorch should demote its `sympy` load-bearing declaration to supportive, or add a real PyTorch-lane Sympy call that gates the endpoint check. This does not break the packet because `torch.func` is source-backed and the exact symbolic work is already carried by the JAX/Sympy lane.

G4: Julia's local Z3 receipt is a trivial unsat polarity check by source comment: "the continuous determinant boundary proof is carried by the Python z3/cvc5 lane." Do not overstate Julia Z3 as an independent continuous-boundary proof. The Python z3/cvc5 proof is the load-bearing boundary proof.

## Q7 - G7 Closure

Adjudication: S1 G7 `GENUINE-WITH-CAVEATS`; lifted-rung G7 still OPEN.

This packet closes the old G7 caveat only at the S1 scratch-diagnostic level: it demonstrates coordinate-parameterized entropy families rather than merely fixed GHZ/W carrier states with shell placement labels. It does not close G7 for the lifted n=3/n=4 rungs.

Lifted-rung G7 closure would additionally need:

1. An executable amplitude constructor `psi(eta_vec, phase_vec, topology/shell data)` for n=3 and n=4, not only reduced-density formulas.
2. Direct binding to the lifted-rung shell-coordinate receipts, including per-site eta rows and aggregate shell/network coordinate rows.
3. Mutation controls that rerun the lifted-rung construction under changed/permuted/erased coordinates, rather than only row-level probability controls.
4. Exact quotient ledger showing which lifted-shell parameters survive `rho`, which are erased, and which affect entropy, with B1 phase-erasure consistency.
5. Endpoint recovery back to the committed GHZ/W anchors after the lifted constructor, not by separately writing the known anchor formulas.
6. Fresh audit of the lifted packet against those rows before any "G7 closed for lifted rungs" claim.

## Named Caveats

G1 - Per-site eta amplitude-constructor gap. The scalar GHZ-W family executable-consumes eta. The W-site-weighted family executable-consumes symbolic weights and records `w_i=eta_i^2`, but does not expose a runnable `eta_i -> amplitude vector` construction.

G2 - Control depth gap. Controls can fail at row/probability/quotient level, but they are not all full reruns under mutated shell-coordinate state constructors.

G3 - Thin PyTorch Sympy load-bearing declaration. Strict source-backed validation fails because PyTorch declares `sympy` load-bearing but source evidence is thin. Demote PyTorch `sympy` to supportive or make it actually gate the PyTorch endpoint row.

G4 - Julia Z3 overcount risk. Julia Z3 is a trivial polarity receipt; the real determinant-boundary proof is Python z3/cvc5. Count Julia Z3 only as a local polarity check.

## Final Verdict

`GENUINE-WITH-CAVEATS`.

Accepted claim: this is a real S1 `QUOTIENTED` scratch diagnostic that repairs the fixed-state-only failure mode enough to show coordinate-dependent entropy families with exact endpoints, recomputed interior rows, quotient behavior, boundary checks, and fail-capable controls.

Rejected/blocked claim: this does not canonize the state families, does not promote the result beyond scratch diagnostic, does not close lifted-rung G7, and does not prove a full eta-per-site lifted amplitude construction.

## Builder Hardening Addendum - G1-constructor

Addendum date: 2026-06-10.

Scope: one bounded hardening round for `G1-constructor` only. The fresh verdict above stands as the controlling audit verdict. This addendum does not promote the packet, does not claim canonical status, and does not close lifted-rung G7.

Closed item: `G1-constructor` is closed for this S1 `QUOTIENTED` scratch diagnostic. The W-site-weighted family now exposes executable amplitude-vector constructors that consume a per-site shell-coordinate vector `eta_vec = [eta_1, ..., eta_n]` and return basis-ordered W-state amplitudes with `w_i = eta_i^2` and `p_i = w_i / sum_j w_j`.

What changed:

- `geo_s1_coord_state_families_v0_common.py` now exposes `w_site_weighted_amplitudes_from_eta(eta_vec)` and `w_site_entropy_vector_from_constructor(eta_vec)`.
- Exact W-site symbolic rows now use `eta_i^2 / sum_j eta_j^2` directly instead of pre-baked symbolic `w_i` probability weights.
- W equal-eta and product-boundary rows are recomputed through the constructor receipts.
- JAX/Python and PyTorch lanes consume the shared constructor receipts; PyTorch also emits a torch-native `torch_w_amplitudes_from_eta` constructor receipt.
- Julia now emits its own `w_site_weighted_amplitudes_from_eta` and `w_site_constructor_controls` receipts.
- The envelope now gates `w_site_constructor_controls_pass`, `julia_w_site_constructor_controls_pass`, and `pytorch_w_site_constructor_controls_pass`.

Mutation controls added and rerun:

- Single input mutation: one constructor input site changes, the full W constructor reruns, and the entropy response identifies the mutated site as the unique largest entropy response. Because W normalization is shared, non-target probabilities are allowed to move; the receipt records this normalization coupling instead of claiming non-target invariance.
- Permutation: permuting `eta_vec` reruns the constructor and permutes the entropy vector accordingly.
- Equal eta: equal `eta_vec` reruns through the constructor and reduces to the already committed symmetric W anchors.

Fresh checks:

- Full JAX leg rerun: exit 0.
- Full PyTorch leg rerun: exit 0.
- Full Julia leg rerun: exit 0.
- Full envelope rerun: exit 0.
- Exact/symbolic subset stability check across an additional full rerun: `3921a52b43c1a2be557366a667434bc5aa8b63b33a046b0521952b9e66ab507a` before and after; `exact_subset_stable=True`.
- `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch system_v6/sims/geo_s1_coord_state_families_v0/results/geo_s1_coord_state_families_v0_envelope_results.json` returned `{"ok": true}`.

Still open:

- Lifted-rung G7 remains open. This hardening closes only the S1 per-site eta amplitude-constructor caveat for `geo_s1_coord_state_families_v0`.
- The existing verdict caveats outside `G1-constructor` are not claimed closed by this addendum.
