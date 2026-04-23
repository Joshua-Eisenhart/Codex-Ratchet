# Operator Basis Proof Surface Feasibility Packet

Date: 2026-04-04
Produced by: Claude Code (terminal C)
Grounded in: `operator_basis_search_results.json`, `operator_basis_graph_artifact.json`,
  prior crosscheck/graph reviews, `sim_operator_basis_search.py`,
  `validate_operator_basis_packet.py`, installed tool status
  (`CURRENT_TOOL_STATUS__INSTALLED_VS_MISSING_VS_NOT_WIRED.md`)

---

## Current B3 Gate Summary

| Gate | Result | Measure | Nature |
|---|---|---|---|
| B3.1 basis remap kills grammar | PASS | gap_change_fraction = 17.18 | purely numerical threshold |
| B3.2 coord-change preserves grammar | PASS | gap_change_fraction ≈ 7.25e-15 | numerically zero — analytically provable |
| B3.3 noncomm ablation degrades grammar | PASS | gap_change_fraction = 0.324, noncomm_ratio ≈ 0 | numerical threshold; noncomm structure is symbolic |
| B3.4 rep demotion is explicit | PASS | all 4 operators load-bearing | purely numerical threshold |

All four gates pass numerically. The remaining blocker is: no symbolic or formal backing for any gate. The question is which gate(s) can be meaningfully formalized with currently installed tools.

---

## Installed Tool Availability (relevant subset)

- `z3` — installed and importable (`/opt/homebrew/lib/python3.13/site-packages/z3/`)
- `sympy` — installed and importable
- `cvc5` — NOT installed under canonical interpreter
- `numpy` — available (already in use)

z3 and sympy are the only formal tools available now.

---

## Gate-by-Gate Proof Feasibility

### B3.2 — Coordinate-change invariance (HIGHEST FEASIBILITY)

**Current state:** gap_change_fraction ≈ 7.25e-15 — this is numerically zero to machine precision, not just small. This is not a coincidence; it follows directly from two exact algebraic facts:
1. Frobenius norm is unitarily invariant: `||UρU† - UσU†||_F = ||ρ - σ||_F`
2. Von Neumann entropy is unitarily invariant: `S(UρU†) = S(ρ)`

Both facts hold for any unitary U, any density matrices ρ, σ. They follow from the trace cyclic property and the fact that eigenvalues are preserved under unitary conjugation.

**What formal backing would mean:** sympy can prove `Tr((UρU†)²) = Tr(ρ²)` symbolically for 2×2 symbolic matrices, and can prove that eigenvalues of `UρU†` are the same as eigenvalues of `ρ`. This transforms B3.2 from "numerically confirmed" to "analytically proven: a consistent global unitary conjugation of states AND operators cannot change the grammar, by unitary invariance."

**Tool needed:** sympy (no z3 required for this gate). z3 is not the right tool here because the statement is a continuous algebraic identity, not a satisfiability/SMT problem.

**Effort:** small. A standalone sympy verification for 2×2 symbolic unitaries can be added as a ~30-line function that the probe optionally calls.

**Honest limit:** sympy verification here proves the mathematical identity, not that the *implementation* correctly reflects it. That's fine — the gate is already confirming the numerical result; the sympy proof backs the *reason* the result is expected.

---

### B3.3 — Noncommutation structure (MODERATE FEASIBILITY)

**Current state:** `noncomm_ratio ≈ 6.95e-17` (essentially zero). The commuting collapse (all-z-family) kills essentially all measurable noncomm residual on the test states, and the grammar degrades. The concern from the prior review: "gap degradation mechanism (channel structure vs. algebraic noncomm) is not fully characterized."

**What formal backing would mean:** z3 or sympy can verify the following structural claim:
- `[apply_Ti, apply_Fe](ρ_diag) = 0` for diagonal ρ — these operators commute on diagonal states (the "commuting on diagonals" claim in the docstring is provable symbolically)
- `[apply_Ti, apply_Fi](ρ) ≠ 0` for general ρ — these cross-axis operators genuinely do not commute

This is a symbolic matrix algebra check. sympy handles it cleanly for 2×2 parametric density matrices. z3 could handle it via bitvector encoding but sympy is more natural here.

**Tool needed:** sympy preferred. z3 can be used if a satisfiability framing is wanted (e.g., "does there exist ρ such that [Ti,Fi](ρ) = 0?" — z3 would answer unsat for the right class of ρ).

**Honest limit:** The gap degradation itself (gap_change_fraction = 0.324) is still an empirical numerical result. The formal backing covers the *structural reason* — that the commuting collapse actually collapses algebraic noncomm — not the specific threshold. The formal proof and the numerical gate remain separate surfaces; the proof doesn't eliminate the gate.

**What z3 specifically enables here:** z3's quantifier-free real arithmetic can encode the commutativity condition as an admissibility constraint: "an operator family is admissible as a noncomm basis only if at least one cross-axis pair satisfies [op_A, op_B](ρ) ≠ 0 for symbolic ρ." This is the correct framing for z3 in this context.

---

### B3.1 — Basis remap (LOW FEASIBILITY for formal proof; better as structural constraint)

**Current state:** gap_change_fraction = 17.18 — a 17× change when x-family and z-family assignments are swapped across fiber/base loops. This is an enormous empirical gap.

**What formal backing would mean:** The underlying structural claim is: "x-axis operators (Ti, Fe) and z-axis operators (Te, Fi) are not interchangeable on Hopf fiber vs. base loops because their action is geometrically non-equivalent on those surfaces." This is a claim about the geometry, not a purely algebraic claim.

**Tool needed:** This gate is least amenable to z3/sympy in a bounded pass. The gap measurement is over sampled density matrices on Hopf loops — continuous geometry. Formally proving that the Frobenius gap changes requires bounding the geometry, which is a harder problem than B3.2 or B3.3.

**Practical formal option:** Encode the operator-family assignment as a z3 boolean constraint: "fiber loop operators must come from {Te, Fi} (x-family) and base loop operators must come from {Ti, Fe} (z-family) for grammar to be preserved." This is a structural admissibility check, not a proof of the numerical gap. It is z3-feasible as a 2-variable boolean constraint, but it is declarative rather than derived — it asserts what the probe already knows rather than proving it.

**Recommendation:** Leave B3.1 as numerical only for now. The declarative z3 constraint is too shallow to be a meaningful proof surface here.

---

### B3.4 — Representation demotion (LOW FEASIBILITY for formal proof)

**Current state:** All 4 operators load-bearing by the 20% gap-drop threshold (Fe=3.02×, Te=1.72×, Ti=1.02×, Fi=0.28×).

**What formal backing would mean:** Formally proving that each operator is non-redundant requires proving that removing it from a composite channel changes the channel's action in a way that affects the fiber/base gap. This is a continuous numerical property — not directly encodeable in z3 without heavy approximation.

**Practical formal option:** sympy could verify that the four operator channels are pairwise non-equivalent (distinct as completely positive maps) — which is a necessary but not sufficient condition for load-bearing status. This is feasible but weak.

**Recommendation:** Leave B3.4 as numerical only for now. Non-redundancy proofs for specific threshold gaps require a tighter mathematical framing than currently justified by the probe's scope.

---

## Summary Map: What Can and Cannot Be Formalized Now

| Gate | Can be formalized now? | Recommended tool | What is proven | What remains numerical |
|---|---|---|---|---|
| B3.2 coord-change | **Yes — high confidence** | sympy | Unitary invariance of Frobenius norm and VN entropy (exact algebraic identity) | Nothing — gate is fully explainable analytically |
| B3.3 noncomm structure | **Yes — moderate** | sympy (or z3 for SAT framing) | [Ti,Fe](ρ_diag) = 0; [Ti,Fi](ρ) ≠ 0 for general ρ | Gap degradation magnitude (0.324) |
| B3.1 basis remap | **No — not meaningfully** | — | — | Gap magnitude (17.18×); geometry is continuous |
| B3.4 rep demotion | **No — not yet** | — | — | Gap drop per operator; load-bearing threshold |

---

## Is z3 Sufficient, or is Another Tool Needed?

z3 is sufficient for the B3.3 structural encoding if a satisfiability framing is used (e.g., "does there exist ρ such that [Ti,Fe](ρ) ≠ 0?"). z3's quantifier-free nonlinear real arithmetic can handle this for 2×2 matrices with symbolic entries.

However, **sympy is better suited than z3 for both B3.2 and B3.3**:
- B3.2 is a pure algebraic identity (unitary invariance) — sympy's symbolic simplification proves it directly without encoding as SAT
- B3.3 commutativity is a matrix algebra fact — sympy's `Matrix.commutator()` or direct symbolic multiplication handles it cleanly

z3 adds value primarily if an admissibility guard layer is wanted: "given operator assignments, check whether the assignment satisfies the structural constraint that cross-axis pairs are non-commuting." This is a correct z3 use but it is a shallow guard, not a deep proof.

**Conclusion:** For the smallest realistic proof surface, sympy is the primary tool. z3 is secondary and optional for the B3.3 structural guard.

---

## Recommended Next Bounded Implementation Handoff

**Title:** `claude__operator_basis_b32_b33_sympy_proof`

**Scope:**
1. Add a `verify_b32_invariance_sympy()` function that uses sympy to prove unitary invariance of Frobenius norm and VN entropy for 2×2 symbolic matrices. Emits a `b32_sympy_proof_verified: true/false` field in the JSON output.
2. Add a `verify_b33_noncomm_structure_sympy()` function that uses sympy to verify `[apply_Ti, apply_Fe](ρ_diag) = 0` and `[apply_Ti, apply_Fi](ρ_general) ≠ 0` symbolically. Emits `b33_sympy_noncomm_verified: true/false`.
3. Both functions are additive — they do not replace the numerical gates; they add a `sympy_proof` subsection to the sim output.
4. If either sympy proof fails, the field is `false` with a reason string — honest failure behavior.
5. No z3 in this handoff; no changes to gate thresholds or existing numerical logic.

**Effort estimate:** 2 small functions (~40 lines total), one additional JSON subsection. No architectural changes. Both sympy calls are bounded to 2×2 symbolic matrix operations.

**What this closes:** The proof surface blocker for B3.2 (fully) and B3.3 (partially — structural fact confirmed, gap magnitude still numerical). B3.1 and B3.4 remain numerical only.

---

## What Should Not Be Attempted Yet

- Formal proof of the B3.1 remap gap — requires formalizing continuous geometry over Hopf loop sampling; out of scope for a bounded pass
- Formal proof of per-operator load-bearing thresholds (B3.4) — requires bounding composite channel action; premature
- cvc5 — not installed; no path to use it under canonical interpreter without installation
- z3 as the primary proof tool for B3.2/B3.3 — sympy is more appropriate for these algebraic identity checks and less likely to hit z3 nonlinear arithmetic timeouts
