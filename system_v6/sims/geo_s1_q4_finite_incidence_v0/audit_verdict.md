# Fresh Audit Verdict: geo_s1_q4_finite_incidence_v0

Bottom line: VERDICT = GENUINE-WITH-CAVEATS.

This is a real `PG(3,4)` finite-incidence follow-up over `GF(4)`. The field route is genuine on the JAX/galois claim path and independently mirrored by Julia GF(4) arithmetic; the exact counts, projective quotient, pair-line uniqueness, line-intersection graph, reconstruction persistence, Frobenius boundary, and q=2/q=3 comparisons survive fresh recomputation.

Ceiling: `scratch_diagnostic`; `promotion_allowed=false`; `formal_admission_allowed=false`; finite incidence discriminator only; no canonical, bridge, axis, manifold, spacetime, GR, physics, or Penrose-validation claim.

Audit note: I did not build this sim and did not rerun the sim legs because this audit was read-only except this file. I read the sources/results, ran the read-only validator, and ran scratch recomputation from field arithmetic with `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3`.

## Source Boundary

- Audit bar: the calibrated bar keeps finite receipts/presentations, can-fail controls, capability-probe/load-bearing honesty, route genuineness, erasure honesty, scratch ceilings, and fresh-context audits as constraint-grounded requirements (`system_v6/receipts/audit_bar_calibration_20260610.md:5`).
- Build card claim: q=4 must persist the committed q=2/q=3 finite-incidence behavior over first non-prime `GF(4)`, expose a stronger quotient boundary, and test char-2 Frobenius (`build_card.md:3`, `:17-22`).
- JAX source quote: `field_model` is `"galois.GF(4), primitive polynomial x^2 + x + 1"` and the quotient is `GF(4)^*={1,alpha,alpha+1}` (`geo_s1_q4_finite_incidence_v0_jax.py:43-49`).
- JAX load-bearing path: it imports `galois`, sets `GF = galois.GF(Q)`, uses `GF(rows).row_space()`, scalar multiplication, projective orbit canonicalization, span construction, and Frobenius squaring (`geo_s1_q4_finite_incidence_v0_jax.py:14-22`, `:38-40`, `:91-130`, `:345-376`).
- Julia independent field path: it does not use integer mod-4 arithmetic. It defines char-2 XOR addition and multiplication with `alpha^2 = alpha + 1`, then uses those operations for quotient classes, rank, spans, and Frobenius (`geo_s1_q4_finite_incidence_v0_julia.jl:38-56`, `:82-138`, `:327-362`).
- Committed precedent: q=2 audit accepted narrow finite reconstruction only and flagged q=3 as the quotient discriminator (`system_v6/sims/twistor_incidence_finite_packet_v0/audit_verdict.md:13-17`, `:57-65`); q=3 audit accepted `80 -> 40`, `130` lines, pair-line uniqueness, reconstruction, and degree `48` (`system_v6/sims/geo_s1_q3_finite_incidence_v0/audit_verdict.md:23-31`, `:35-41`).

## Per-Check Results

1. PASS - Q1 `GF(4)` is genuine on the claim path. Fresh field checks with `galois.GF(4)` gave `x+x=0` for all four elements, nonzero multiplicative group `{1,2,3}` of size `3` with orders `{1:1, 2:3, 3:3}`, and Frobenius squares `{0:0, 1:1, 2:3, 3:2}`. Frobenius was additive and multiplicative and fixed `GF(2)={0,1}`. This is not `GF(2)xGF(2)` or `Z/4`: the Julia source explicitly uses `alpha^2 = alpha + 1`, and the JAX source uses `galois.GF(4)` on scalar multiplication, row-space, quotient, and Frobenius.

2. PASS - Q2 exact counts recompute. Hand counts: raw nonzero vectors are `4^4 - 1 = 255`; projective points are `(4^4 - 1)/(4 - 1) = 255/3 = 85`; lines are `[4 choose 2]_4 = ((4^4-1)(4^3-1))/((4^2-1)(4-1)) = (255*63)/(15*3) = 357`. Fresh enumeration independently returned `255` raw vectors, `85` projective classes, `357` lines, every line size `5`, `3570` point pairs, and pair-line count min/max `1/1`. The envelope reports the same values for both engines (`results/geo_s1_q4_finite_incidence_v0_envelope_results.json:45-74`, `:157-197`, `:275-329`).

3. PASS - Q2 quotient class size is exactly `3`. Fresh class example: vector `(0,0,1,1)` has scalar orbit `[(0,0,1,1), (0,0,2,2), (0,0,3,3)]`, canonical class `(0,0,1,1)`, size `3`. The emitted drop-quotient control records `raw_nonzero_vector_count=255`, `projective_class_count=85`, `raw_to_projective_ratio=3.0`, `same_readouts_as_projective=false`, and `q4_discriminator_fired=true` (`results/geo_s1_q4_finite_incidence_v0_jax_results.json:241-248`).

4. PASS - Q2 pair-line uniqueness and line-intersection degree. Every unordered point pair lies on exactly one line by fresh enumeration. For a fixed projective line in `PG(3,4)`, there are `q+1 = 5` points; through each point are `q^2+q+1 = 21` lines, so other lines through that point are `20`; no other line shares two points with the fixed line, so degree is `5*20 = 100`. Edges are `357*100/2 = 17850`. Fresh enumeration returned degree min/max `100/100` and edge count `17850`; the envelope reports the same (`results/geo_s1_q4_finite_incidence_v0_envelope_results.json:181-197`, `:551-555`).

5. PASS - Q3 quotient ablation is stronger than q=3 like-for-like. The comparison is computed as ratios on the same raw-nonzero-vector/projective-class readout: q=2 `15/15 = 1.0`, q=3 `80/40 = 2.0`, q=4 `255/85 = 3.0`. The q4 result stores q2/q3 anchors and the q4 separation row with `status_vs_q3="strengthens"` (`results/geo_s1_q4_finite_incidence_v0_envelope_results.json:571-596`, `:608-626`). That is a real strengthening of the quotient discriminator, not a prose assertion.

6. PASS - Q4 persist/strengthen honesty. The emitted `separation_table` has four rows: projective quotient strengthens, reconstruction strengthens, line-intersection graph scale strengthens, and char-2 Frobenius is marked `new_boundary_not_like_for_like_strength` rather than forced into a like-for-like strengthening bucket (`results/geo_s1_q4_finite_incidence_v0_envelope_results.json:608-682`). No emitted row says `weakens` or `weakens_or_flat`; the envelope summary's "no weakening observed" is computed over the emitted rows, not a cherry-picked subset (`results/geo_s1_q4_finite_incidence_v0_envelope_results.json:264-269`).

7. PASS - Q5 Frobenius boundary can fail. The row would fail if Frobenius did not permute projective points, did not map lines to lines, did not preserve incidence, moved zero projective points, or failed involution. The emitted row checks exactly those conditions and reports `moved_projective_point_count=70`, `point_permutation=true`, `line_permutation=true`, `incidence_preserved=true`, and `involution_on_points=true` (`results/geo_s1_q4_finite_incidence_v0_jax_results.json:252-263`, `:300-311`). This is a real char-2 boundary: in `GF(4)`, labels `2` and `3` swap under squaring while `0` and `1` are fixed.

8. PASS - Q5 solver controls can fail. Valid pair-line uniqueness asserts the existence of a computed point pair with incident-line count not equal to `1`; z3 and cvc5 both return `unsat`. The scrambled-incidence control changes pair count min/max to `0/2` and flips both solvers to `sat` in JAX (`results/geo_s1_q4_finite_incidence_v0_jax_results.json:267-273`, `:6927-6962`). Julia also flips its Z3 control to `sat` (`results/geo_s1_q4_finite_incidence_v0_julia_results.json:254-259`).

9. PASS-WITH-CAVEATS - Q6 standard. Declared mode is honest: `julia_canon_plus_jax_diagnostic`, lanes are Julia and JAX, and PyTorch is omitted because there is no graph/network/autograd claim path (`results/geo_s1_q4_finite_incidence_v0_envelope_results.json:339-348`). Normal validator and `--require-source-backed` both return `ok:true`. Seeds are emitted. Capability/tool manifests are present. Caveat 1: optional `--strict-source-backed` fails the current source-token heuristic for `galois` and `julia_gf4_stdlib`; source inspection shows those routes are real, so this is a named validator/reporting caveat, not a mathematical rejection. Caveat 2: JAX emits function-level `tool_calls`, but the Julia result does not emit a `tool_calls` array even though the Julia source and manifest identify the GF(4)/Z3 functions. That keeps the verdict at `GENUINE-WITH-CAVEATS`, not clean `GENUINE`.

## Hand Recomputations

- Field check: `GF(4)` has characteristic 2 because every label satisfies `x+x=0`; nonzero group size is `3`; nonidentity nonzero labels have order `3`; Frobenius `x -> x^2` is `{0:0, 1:1, 2:3, 3:2}` and fixes `GF(2)`.
- Point count: nonzero vectors in `GF(4)^4` are `4^4 - 1 = 255`; quotient by the three nonzero scalars gives `255/3 = 85` projective points.
- One quotient class: `(0,0,1,1)` has orbit `[(0,0,1,1), (0,0,2,2), (0,0,3,3)]`, so the class size is `3`.
- Line count: `[4 choose 2]_4 = ((4^4-1)(4^3-1))/((4^2-1)(4-1)) = (255*63)/(15*3) = 357`.
- Pair-line uniqueness: fresh enumeration over `3570` unordered point pairs gave incident-line count min/max `1/1`.
- Intersection graph degree: each line has `5` points; each point has `21` lines through it; excluding the fixed line gives `5*(21-1)=100`.
- Edge count: `357*100/2 = 17850`.
- q=2/q=3/q=4 quotient ratios: `15/15=1.0`, `80/40=2.0`, `255/85=3.0`.

## Named Caveats

- Strict source-backed heuristic caveat: `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --strict-source-backed system_v6/sims/geo_s1_q4_finite_incidence_v0/results/geo_s1_q4_finite_incidence_v0_envelope_results.json` returned `ok:false` with thin-claim errors for `galois` and `julia_gf4_stdlib`. Manual source inspection resolves the mathematical route, but the packet is not clean under that optional strict heuristic.
- Julia function-level reporting caveat: the Julia result has `TOOL_MANIFEST` and `TOOL_INTEGRATION_DEPTH`, but no emitted `tool_calls` list. JAX has the function-level `galois`, `z3`, and `cvc5` rows.
- q4 is an alt-math finite-incidence discriminator only. The line graph row must stay "incidence/intersection graph scale", not physics/null-light, and the Frobenius row is a new boundary row, not a like-for-like q=3 strengthening.

## Verdict

VERDICT: GENUINE-WITH-CAVEATS.

Accepted claim: `PG(3,4)` finite incidence is exactly built over genuine `GF(4)` arithmetic; the projective quotient is load-bearing with a `3:1` raw/projective ratio; pair-line uniqueness, reconstruction persistence, line-intersection graph invariants, q=2/q=3 comparisons, and the char-2 Frobenius boundary hold under the declared two-engine diagnostic ceiling.

Rejected/promotional claim boundary: this is not canonical evidence, not formal admission, not a bridge/axis/manifold result, and not a twistor-to-physics, spacetime, GR, or Penrose-validation claim.

Ceiling restated: `scratch_diagnostic`; `promotion_allowed=false`; `formal_admission_allowed=false`; finite incidence / finite projective quotient discriminator only.

## Builder-Hardening Addendum - 2026-06-10

Caveat 2 is closed. The Julia leg now emits a function-level `tool_calls` array with one load-bearing `julia_gf4_stdlib` route for GF(4) arithmetic/quotient/rank/span/Frobenius functions and one load-bearing `Z3` route for the computed pair-line uniqueness proof. Each row uses the required `{tool, qualified_api, input_object, output_object, positive_case, negative_control, boundary_case, demotion_condition, gates}` shape.

Fresh rerun status: full Julia leg reran with `all_pass=true`, `points=85`, `lines=357`, `planes=85`, `z3=unsat`, and `frob=true`; the envelope reran with `all_pass=True`, `max_divergence=0.0`, validator record `ok=True`, and `kill=False`. The normal validator and `--require-source-backed` validator both returned `ok:true`. The exact result-row stability hashes for the Julia leg and envelope remained unchanged across the rerun for `{values, separation_table, gates, controls, crossover_proofs}`.

Caveat 1 is carried unchanged as a separate validator-heuristic finding for a tools pass. This hardening round did not attempt to repair the optional `--strict-source-backed` token heuristic.

Ceiling unchanged: `scratch_diagnostic`; `promotion_allowed=false`; `formal_admission_allowed=false`; finite incidence / finite projective quotient discriminator only.
