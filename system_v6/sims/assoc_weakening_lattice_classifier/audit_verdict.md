# Fresh-Context Audit Verdict

Scope: read-only audit of `system_v6/sims/assoc_weakening_lattice_classifier/` and `system_v6/sims/pg32_sedenion_incidence/`.

Commands/checks run:

- Read source and result JSON for Julia, JAX, PyTorch, and envelope legs in both sims.
- Ran independent pure-Python recomputation scripts from the shell without importing the sim modules.
- Ran:
  - `python3 scripts/validate_three_engine_sim_result.py --require-pytorch system_v6/sims/assoc_weakening_lattice_classifier/results/assoc_weakening_lattice_classifier_envelope_results.json`
  - `python3 scripts/validate_three_engine_sim_result.py --require-pytorch system_v6/sims/pg32_sedenion_incidence/results/pg32_sedenion_incidence_envelope_results.json`

Both validators returned `ok: true`.

## A. `assoc_weakening_lattice_classifier`

Verdict: **GENUINE-WITH-CAVEATS**

This is genuine as a scratch diagnostic / finite structure-constant classifier harness. It is not an admitted or canonical algebra result, and the files themselves correctly set `classification: scratch_diagnostic`, `promotion_allowed: false`, and `formal_admission_allowed: false`.

Audit findings:

1. O associativity failure is real.
   Independent recompute from a Cayley-Dickson-built octonion table:
   - witness: `(e1, e2, e4)`
   - `(e1 e2) e4 = e7`
   - `e1 (e2 e4) = -e7`
   - residual: `2 e7`

2. S alternativity failure is real.
   Independent recompute using the same fixed generic witness shape as the JAX SMT cell:
   - `x = [-1, 1, 3, -2, 0, 2, -3, -1, 1, 3, -2, 0, 2, -3, -1, 1]`
   - `y = e1`
   - `(xx)y - x(xy)` has support `26 e10 - 10 e11 + 2 e12 - 22 e13 + 18 e14`
   - max absolute residual: `26`

3. S Artin seat is computed, not assumed.
   Source inspection shows `find_artin_basis_pairs` computes generated indices for every basis pair, then checks associativity over every basis triple in that generated subalgebra. My independent pure-Python recompute of that basis-pair subalgebra test returned `true` for S. I found no reliance on Cayley-Dickson theorem prose for this Artin classification.

4. Kill-control K is a valid finite algebra table and genuinely fails flexibility.
   The table is closed on a 3-element basis with bilinear structure constants. Nonzero products:
   - `e0` is a two-sided identity.
   - `e1 e1 = e1`
   - `e1 e2 = e1`
   - `e2 e2 = e2`
   Flexibility witness:
   - `x=e1`, `y=e2`
   - `(xy)x - x(yx) = e1`
   So K is not merely a malformed table; it is a closed algebra control that kills flexibility.

5. Matrix hash identity across engines is not a peer-read echo.
   The envelope compares matching matrix hash `01f8b66ce07d1923988510da10a153c806b41e7cada73799d36b0b160c59a21b` across Julia/JAX/PyTorch and matching position hash `a092eab494537d3cf6a39a5d173ac4520a34a6f59948d48d6d7f6286f7c31fa3`. Each engine result records `reads_peer_result: false`. Source inspection shows separate Julia, JAX, and PyTorch table construction/classification code paths; only the envelope reads peer result JSON for comparison.

6. SMT cells derive in solver.
   JAX binds all table coefficients into Z3/cvc5 variables before forming associator/alternativity products. Julia binds table coefficients into Z3 variables for the O/H associativity cell. The decisive envelope cells are:
   - O associativity violation: Z3 `sat`, cvc5 `sat`, Julia Z3 `sat`.
   - H associativity control: all `unsat`.
   - S alternativity violation: Z3 `sat`, cvc5 `sat`.
   - H alternativity control: Z3/cvc5 `unsat`.

Caveats / hardening:

- The alternativity classifier and several non-SMT identity checks use basis vectors plus six generic samples, not a full symbolic universal quantifier over arbitrary coefficients. That is acceptable for the current scratch diagnostic but should be named more explicitly.
- Julia SMT covers O/H associativity but does not mirror the S alternativity SMT cell; add a Julia Z3 S alternativity derivation if the envelope wants symmetric solver coverage.
- Add a compact audit fixture that prints the decisive O and S witness residuals directly, so future reviewers do not need to reconstruct them manually.
- Keep the current ceiling: `scratch_diagnostic`; do not promote to canonical/admitted from this packet alone.

## B. `pg32_sedenion_incidence`

Verdict: **GENUINE-WITH-CAVEATS**

This is genuine as a scratch diagnostic for sedenion-derived PG(3,2) incidence, plane split, and two-term zero-divisor graph. It should not be promoted beyond that ceiling without stronger formal packaging.

Audit findings:

1. Sedenion table is built, not hard-coded.
   All three source legs define an octonion table from the seven oriented triples and then compute `sedenion_table()` as `cd_double(octonion_table())`. The sedenion multiplication lines are not hard-coded as a static 16x16 product list.

2. Line count and pair axiom recompute cleanly.
   Independent recompute over points `1..15`:
   - line count: `35`
   - every pair exactly one line: `true`
   - pair violations: `0`
   Five deterministic spot pairs:
   - `(4,10)` lies on `(4,10,14)`, count `1`
   - `(12,15)` lies on `(3,12,15)`, count `1`
   - `(2,12)` lies on `(2,12,14)`, count `1`
   - `(5,10)` lies on `(5,10,15)`, count `1`
   - `(4,9)` lies on `(4,9,13)`, count `1`

3. Plane split recompute cleanly.
   Independent recompute:
   - total planes: `15`
   - genuine octonion planes: `8`
   - closed non-alternative sedenion planes: `7`
   Spot checks:
   - genuine plane `(1,2,3,4,5,6,7)`: closed `true`, no alternativity witness found.
   - non-alternative plane `(1,2,3,12,13,14,15)`: closed `true`, right linearized alternativity witness `(x,y,z)=(1,2,12)` with residual `-2 e15`.

4. One zero-divisor product is verified directly from the table.
   Independent witness:
   - `(e1 + e10)(e5 + e14) = 0`
   Product terms:
   - `e1 e5 = -e4`
   - `e1 e14 = e15`
   - `e10 e5 = -e15`
   - `e10 e14 = e4`
   The sum cancels to zero.

5. Zero-divisor graph component count recomputes cleanly.
   Independent recompute over two-term nodes `(a,b)` with `1 <= a < b <= 15`:
   - ordered zero-divisor pair count: `84`
   - component count: `7`
   - component sizes: `[6, 6, 6, 6, 6, 6, 6]`

6. Controls behave as claimed.
   Octonion restriction:
   - line count: `7`
   - pair axiom violations: `0`
   - ordered zero-divisor pair count: `0`
   Scrambled signed-entry control:
   - line count becomes `37`
   - pair axiom violations: `6`
   - first violations include `(1,2)`, `(1,3)`, `(1,4)`, `(1,5)`, `(2,5)` each with line count `2`

7. Solver cells derive in solver.
   JAX Z3/cvc5 and Julia Z3 bind table entries into solver variables for line/non-line and zero-product checks. Envelope SMT verdicts match:
   - claimed non-line closure: Z3 `unsat`, cvc5 `unsat`, Julia Z3 `unsat`
   - zero-product derivation: Z3 `sat`, cvc5 `sat`, Julia Z3 `sat`

8. Cross-engine agreement is not peer-read echo.
   The envelope compares shared scalar spreads across Julia/JAX/PyTorch with `max_divergence: 0.0`; no scalar spread mismatches were present. Each engine result records `reads_peer_result: false`. Source inspection shows separate Julia, JAX, and PyTorch implementations that each build the table and scan incidence/planes/zero-divisor structure.

Caveats / hardening:

- The octonion seed table is constructed from a fixed oriented triple list. That is fine, but the result should say "sedenion table built by Cayley-Dickson from a hard-coded oriented octonion seed," not imply the entire construction is theorem-free or seed-free.
- Plane alternativity is checked over basis triples plus identity for each 7-plane, via linearized alternativity. For this finite basis-subspace claim that is useful, but the precise scope should be stated: basis-level/linearized finite subspace check, not a full proof assistant certificate.
- The SMT line cells prove selected line/non-line and zero-product facts, not the full 35-line pair axiom or full 7-component graph inside SMT. Keep the solver claim scoped to those cells.
- Add a small read-only audit script or fixture that emits the 35-line count, five pair spot checks, the two plane witnesses, and the zero-product cancellation in one command.
- Keep the current ceiling: `scratch_diagnostic`; no canonical/admitted language.

## Overall

Both sims are **genuine-with-caveats**. I found no decorative peer-result echo, no hard-coded sedenion product table, and no broken kill-control. The main hardening need is claim-scope precision: distinguish finite executable scratch diagnostics and selected SMT cells from formal/canonical admission.
