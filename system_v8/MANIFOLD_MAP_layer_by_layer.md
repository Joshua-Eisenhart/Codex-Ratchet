# Manifold map, layer by layer

Readable map, not a gated receipt. Bottom (frontier, least presuming) to top
(most presuming, or purely speculative). For each layer: the formal object,
the entropy face, the geometry face, which engines ran it, and a status tag.

Read this alongside `ROOT/ROOT_CARD.md` (the owner's verbatim ratchet core)
and `ratchet_contract/ratchetings/results/*.json` (the receipts this map
cites). Every citation below names its receipt file — check the file, not
this prose, before relying on a claim.

## Status tags

- **EARNED** — a committed, gated, one-way arrow with a real witness pair and
  a passing local rerun. Ceiling is still `tool_lego_fit_probe`,
  `promotion_allowed: false` — EARNED means the arrow's one-way claim is
  proven on its carrier, not that the layer's position in the overall
  ordering is canonical. Every receipt cited below carries
  `ordering_status: "PROPOSED not canon"` even where the arrow itself is
  EARNED. Do not read EARNED as canonical.
- **PROPOSED** — a build card exists (cites owner doc sections, scopes the
  three engines, states the expected verdict) but the sim has not run.
- **SPECULATIVE** — synthesis from the pasted Gemini thread, classified by a
  six-model NVIDIA panel run on 2026-07-21. Real math ingredients, no
  derivation of the specific claim. Not part of the ratchet_contract chain.
- **NUMEROLOGY** — same panel, but the plurality or an exact split of models
  called it likely-wrong / coincidence-matching rather than merely unbuilt.

A cross-cutting caveat applies to every EARNED row: the 2026-07-21 systemic
audit (three fresh opus skeptics) found the z3/cvc5 legs across all six
originally-committed arrows were a generic single-valued-function tautology
(`recover(k)==A AND ==B -> unsat`, true for any `A != B`, independent of the
actual mechanism). This was fixed same day (commit `4fcd539d6`): SMT
downgraded to `smt_role: supportive_nonvacuity_only` and dropped from every
`core_ok` conjunction; the load-bearing evidence is the direct numpy/sympy
witness recompute named in each row below. One exception:
`magma_smt_genuine.py` encodes the actual magma table as z3 `Function`
constraints, so its UNSAT genuinely depends on the table (verified by
perturbation) — the one case where z3 is correctly load-bearing.

---

## Layer 0 — root: identity is probe-relative

**Formal object.** `a = a` iff `a ~ b`, where `~` is indistinguishability
under an active probe family `M`. Identity is not primitive; the quotient
`S/~_M` is. No probe family `M`, admissibility check, and quotient — no
substantive claim.

**Entropy face.** None yet — this is pre-entropy. Entropy is a typed readout
introduced at later layers, not the root.

**Geometry face.** None yet — the quotient `S/~_M` is the only structure.

**Engines.** N/A — this is a stated axiom (harness root), not a sim. Per
standing doctrine ("don't ratchet the ratchet"), axioms are not proof
targets.

**Status.** Presumption floor, given not provable.

**Held-open negatives (2026-07-21 NVIDIA panel, two-model coverage,
llama-3.3-70b + qwen3-next-80b — do not collapse, they attack opposite
failure directions):**
- llama: an impoverished/non-injective `M` over-merges distinct elements
  into one class.
- qwen3: `M`-incompleteness under global phase — `|psi>` and
  `e^{i theta}|psi>` are identified under `M` if `M` is only projective
  measurements, yet interferometry distinguishes them; no finite `M` is
  provably maximal, so "iff" quietly assumes an unstated completeness axiom.

Neither negative has a sim built against it yet. Recorded as open pressure
on the root, not as a refutation.

---

## Layer 1 — bare magma frontier

**Formal object.** A finite carrier with one binary operation and no other
law — the least-presuming algebraic object on the ladder (below octonions,
below G2, below any claim of associativity, commutativity, identity, or
inverse).

**Arrow: magma -> [+associativity] -> semigroup.**
`magma_to_semigroup.py`, verdict `DROP_ONE_WAY`. The associativity
congruence quotient `S_assoc` (union-find over `(ab)c ~ a(bc)`) collapses
distinct bracketing histories; `S_assoc` cannot recover which bracketing
produced a given class. Structural-entropy drop `S_assoc_drop = 5.75`.
Genuine control: a Z/3Z table, not a tautology. Geometry face: combinatorial
(Cayley graph / bracketing tree) — the "vanishing curvature" reading some
proposals assume does not apply until the density-matrix layer.

**Supporting mechanism-encoded SMT.** `magma_smt_genuine.py`, verdict
`MECHANISM_ENCODED_UNSAT`. Pins the actual magma table as 9 z3 `Function`
constraints plus the associativity congruence; perturbing the table flips
the UNSAT, and the unsat core is a subset of the ground-truth
non-associative triples. cvc5 cross-checked, erased-table control flips to
SAT. This is the one SMT leg in the whole set that is genuinely load-bearing
on the mechanism, not the generic tautology.

**Engines.** sympy (load-bearing, union-find quotient), z3 + cvc5
(supportive_nonvacuity_only on `magma_to_semigroup`; z3 load-bearing on the
separate `magma_smt_genuine` mechanism sim). numpy, jax, julia: not run.

**Status.** EARNED (arrow), ordering PROPOSED not canon.

**Held-open negative (qwen3, sharpest across the whole panel):** for small
finite carriers (`|S| <= 4-5`), the associator map
`(a,b,c) -> (ab)c - a(bc)` is a finite 3-cochain; storing the full set of
associativity-violation triples alongside the quotient reconstructs the
original table, so "one-way" holds only if that violation metadata is
discarded — a choice about what counts as "the quotient," not a structural
impossibility. Not yet tested against the committed sim code. Flagged as the
strongest, most concrete flip candidate in the panel run; worth a direct
build (small explicit magma, store `S_assoc` plus the violation-triple set,
check recoverability).

---

## Layer 2 — algebra ladder: identity, inverse, associativity, commutativity

**Formal object.** The four group-law candidates tested individually on one
fixed carrier (`|S| = 4`), each as its own forgetful map from the free
structure.

`algebra_ladder.py`, verdict `LADDER_ONE_WAY`. Honest 2-of-4: associativity
(drop `ln4 - ln3`, witness pair `{1,3}`) and inverse (drop `ln3 - ln2`,
witness pair `{0,2}`) proven one-way. Identity and commutativity are honestly
computed bijections on this carrier — zero drop, not forced one-way.
Exhaustive search (400k perturbations, carriers up to size 6) found no
carrier where all four laws drop onto a nontrivial group; left open, not
smoothed over.

**Engines.** sympy (load-bearing), z3 (supportive), cvc5 (supportive).
numpy, jax, julia: not run.

**Status.** EARNED (2 of 4 sub-arrows; the other 2 are honestly not-earned
on this carrier), ordering PROPOSED not canon.

---

## Layer 3 — presumption order on {associativity, commutativity}

**Formal object.** The question of which law to impose first, made
computable, kept strictly separate from whether the two orders land on the
same destination.

`law_order_branch.py`, verdict `REMERGE_PATH_DEPENDENT` (commit `c9fed6057`).
Two questions, not one:
1. **Endpoints re-merge.** Associativity-then-commutativity and
   commutativity-then-associativity both reach the same 2-element
   semilattice — genuine isomorphism, brute-forced over all label
   permutations, not just matched cardinality.
2. **Paths are order-dependent (N01).** Associativity-first trajectory
   `[4,3,2]` drops `[0.288, 0.405]`; commutativity-first trajectory `[4,2,2]`
   drops `[0.693, 0.0]`. Same destination, different structural-entropy cost
   per step.

**Contrast pair (genuine non-re-merging branch, same machinery).**
Textbook non-commuting `S`/`H` class operators: `S`-then-`H` gives a
3-element result, `H`-then-`S` gives a 2-element null result — non-isomorphic.
The detector is pinned at both poles (chain / re-merge / genuine branch); the
primary verdict on `{associativity, commutativity}` was not hard-wired.

**Engines.** sympy (load-bearing), z3 (supportive). numpy, jax, julia: not
run.

**Status.** EARNED, ordering PROPOSED not canon. This is the binding answer
to the "presumption ordering" open question for this one law pair — it does
not settle the wider open set below.

**PROPOSED extension (not yet run).** `system_v8/candidates/cards/CARD_assoc_sign_order_branch.md`
asks the same three-pole question (chain / re-merge / genuine branch) for
`{associativity, sign-symmetrization}`, chaining the already-committed
`magma_to_semigroup` and `anticommutation_rung` arrows on one fixed signed
2-generator Grassmann-basis carrier. Expected verdict one of
`CHAIN` / `REMERGE_PATH_DEPENDENT` / `GENUINE_BRANCH`, computed not assumed.
Status **PROPOSED**.

---

## Layer 4 — anticommutation rung: Clifford, Grassmann, commutative

**Formal object.** Clifford algebra (has a metric) -> `[g -> 0]` ->
Grassmann algebra (metric-free, anticommuting) -> `[symmetrize, forget
sign]` -> commutative algebra.

`anticommutation_rung.py`, verdict `ANTICOMM_ARROWS_ONEWAY`. Grassmann is
the `g -> 0` degenerate case of Clifford (Clifford presumes a metric
Grassmann does not — entrywise structure-constant table equality).
Symmetrization is a one-way forget of sign: witness
`theta1*theta2` vs `theta2*theta1` are distinct (opposite sign) but share
the same symmetrized image. Control: genuine `n=1` bijection, not a
tautology.

**Engines.** sympy (load-bearing, exact structure-constant tables), z3 +
cvc5 (supportive). numpy, jax, julia: not run.

**Status.** EARNED, ordering PROPOSED not canon.

**Held-open negative (qwen3, truncated mid-argument):**
`AB = (1/2){A,B} + (1/2)[A,B]` — symmetrization discards the commutator
`[A,B]`, but if the generating set's anticommutation relations are known
independently, the commutator part might be reconstructible from structure
constants rather than from the symmetrized product alone. Same
discard-the-metadata pattern as the magma negative above. Not yet tested
against the committed sim code.

---

## Layer 5 — quantum entropy axis: pure, von Neumann, Shannon

**Formal object.** Pure states (`CP^1`, Fubini-Study, `S = 0` everywhere) ->
`[partial trace]` -> mixed states (Bloch ball, BKM metric, von Neumann
entropy) -> `[dephase in the eigenbasis]` -> classical distributions
(simplex, Fisher-Rao metric, Shannon entropy).

**Arrow below VN: `pure_to_vn.py`, verdict `EMERGES_ONE_WAY`.** Von Neumann
entropy is zero on every pure state (sampled sphere max `|S|` = `3.08e-15`)
and is born at the cut: `S(rho_A) = ln 2` for the Schmidt state
`cos(t)|00> + sin(t)|11>` at `t = pi/4`. Load-bearing witness: `psi` and
`(I tensor diag(1,i))psi` are distinct states with identical
`rho_A = I/2` — partial trace is non-injective, no inverse. Geometry
couples: the pure-state boundary sphere is exactly the zero-entropy set.

**Arrow VN -> Shannon: `vn_to_shannon.py`, verdict `RATCHETED_ONE_WAY`.**
Dephasing `D(rho) = diag(rho)` is idempotent, its image (the simplex) sits
inside the Bloch ball, and it is entropy-monotone (minimum off-diagonal gap
`0.0316 > 0`). Geometry couples exactly: the BKM metric restricts to the
Fisher-Rao metric with zero numeric difference. Load-bearing witness:
`rho != rho'` with equal off-diagonal magnitude but different phase share
the same `D(rho) = D(rho')` — non-injective, no inverse.

**Engines.** sympy + numpy (load-bearing, both arrows), z3 + cvc5
(supportive_nonvacuity_only), qutip (second-engine cross-check, commit
`0c2de7076` — reproduces both witnesses; on `vn_to_shannon` qutip used a
physically distinct mechanism, ancilla-CNOT-entangle-then-partial-trace,
still matched to machine precision, the strongest cross-engine confirmation
in the set). Julia leg: `julia_leg` field present, honestly
`DEFERRED_BLOCKED_ON_MEMORY` (psutil headroom below the 0.40 gate).

**Status.** EARNED (both arrows), ordering PROPOSED not canon.

**Held-open negatives (qwen3):**
- On `pure_to_vn`: for a known bipartite structure (fixed `H_A tensor H_B`),
  the Schmidt decomposition means `rho_A`'s spectrum plus known local bases
  reconstructs `|psi>` up to local unitary — the "cannot recover" claim
  holds only if the Schmidt-basis choice is thrown away as unspecified
  metadata. Same pattern as the magma and anticommutation negatives.
- On `vn_to_shannon`: if dephasing is performed exactly in `rho`'s own
  eigenbasis (the only physically meaningful choice), `S(rho) = H(diag(rho))`
  identically — an equality, not a one-way drop. The arrow's one-way-ness
  would then rest on dephasing in a different basis, arguably a mislabeled
  operation. Direct, checkable: compute both sides on an explicit `rho` and
  compare. Not yet run against the committed sim code.

**PROPOSED rung below (not yet run).**
`system_v8/candidates/cards/CARD_hopf_fiber_phase_forget_arrow.md`: the Hopf
projection `pi: S^3 -> S^2` sends the full normalized spinor (with its
`U(1)` fiber phase) to its Bloch point. Expected `EMERGES_ONE_WAY` /
`RATCHETED_ONE_WAY` — the fiber collapses to a point, and the lost datum is
the fiber phase plus its holonomy under the Hopf connection
`A = dphi + cos(2 eta) dchi` (standard solid-angle Berry-phase argument).
Status **PROPOSED**.

---

## Layer 6 — Renyi alpha-axis

**Formal object.** The Renyi family `S_alpha(rho) = (1-alpha)^-1 ln Tr(rho^alpha)`,
with `S_0 = ln rank(rho)` (quantum Hartley / min-entropy) at one end and
`S_1 = S_VN` (von Neumann) at the interior point `alpha = 1`.

`renyi_alpha_axis.py`, verdict `S0_ONEWAY_FORGET_OF_VN`. `S_0` is a one-way
forget of the VN spectrum (keeps support/rank, drops weights) — witness:
distinct density matrices sharing the same rank but different `S_1`.
Family is monotone, `S_0 >= S_1 >= S_infinity`, with equality exactly at
`rho = I/d`. The quantum Hartley sits WITH von Neumann on the same carrier,
not below it — held distinct from two other "Hartley" readouts: the Axis-0
counting drive (`dC = D log V` across ticks) and the foundation count
`ln|Y|` (pre-carrier admissible-class count). All three coincide only at
`rho = I/d`.

**Engines.** sympy + numpy (load-bearing), z3 + cvc5 (supportive), qutip
(cross-check via `eigenenergies()`, exact match). Julia: deferred on memory.

**Status.** EARNED, ordering PROPOSED not canon.

**Held-open negative (qwen3, technical):** `S_alpha` is analytic in `alpha`
for `alpha > 0`; its Taylor expansion near `alpha = 0` encodes moments of
the full eigenvalue distribution, so the family in a neighbourhood of
`alpha = 0` reconstructs the full spectrum by analytic continuation. This
does not refute "`S_0` alone is one-way" but sharpens its honest scope: the
one-way claim is about the single limit point, not the axis near it. Worth
checking the receipt's language does not overclaim past that point (it
currently does not — `verdict` names `S_0` specifically).

---

## Layer 7 — Bures / Fubini-Study / Berry geometry

**Formal object.** The Bures metric on mixed states, restricted to the
pure-state boundary, versus the Fubini-Study metric; the antisymmetric
(Berry curvature) half of the quantum geometric tensor.

`bures_to_fubini_study.py`, verdict `BERRY_IRREDUCIBLE` (commit `5aaffc3ca`).
**Positive:** Bures restricted to the pure boundary equals Fubini-Study
exactly, proportionality constant `1.0` (not the commonly assumed `1/4`,
which holds only under the bare-round-sphere convention — flagged in the
receipt's `convention_note`, not silently overridden). Cross-checked three
ways: exact sympy at 5 `theta`, numeric finite-difference sweep at 25
`theta`, and the `F_Q = 4 g_FS` metrology identity. **Load-bearing:** Berry
curvature `F` (the antisymmetric half of the QGT) is not recoverable from
Bures, a real symmetric tensor with zero antisymmetric part. Witness:
conjugate pair `psi` vs `psi*` share identical real Bures/Fubini-Study
components (`g_tt = g_pp = 0.25`, `g_tp = 0`) but opposite curvature
(`+/- 0.5`). z3 and cvc5 both UNSAT on shared-recovery, erased control flips
to SAT. Berry curvature at `theta = pi/2` equals `0.5` (monopole).

**Engines.** sympy + numpy + z3 (load-bearing), cvc5 (supportive), qutip
(cross-check, deviation `~2.8e-8`). Julia: deferred on memory.

**Status.** EARNED, ordering PROPOSED not canon. This is the geometric twin
of "VN born at the cut": complex phase structure is genuinely new at the
pure/complex layer, not inherited from the mixed metric.

**PROPOSED rung above (not yet run).**
`system_v8/candidates/cards/CARD_schmidt_tori_foliation_arrow.md`: the
Hopf/Schmidt torus foliation of `S^3`, with entanglement entropy
`S(eta) = h(cos^2 eta)` as an exact level-set function on each torus leaf
`T_eta`. Two arrows expected: (1) the chi-orbit average is one-way (forgets
the fiber coordinates `phi, chi`); (2) `S(eta)` is symmetric under
`eta <-> pi/2 - eta`, so `eta` is a 2-to-1 fold of `S` alone — the
hemisphere sign `b_0 = sign(cos 2 eta)` is the independent coordinate that
resolves the fold, distinct from the phase-forget in (1). Status
**PROPOSED**.

---

## Layer 8 — finite to continuum

**Formal object.** A discretization map from a continuum interval to a
finite dyadic tower of cells, and the completeness axiom that would be
needed to reconstruct the continuum from finite data.

`finite_to_continuum_rung.py`, verdict `CONTINUUM_ABOVE_FINITE_ONEWAY`.
Discretization is many-to-one (witness: exact `Fraction` arithmetic shows
`x1 != x2` sharing the same cell index at every tested level `1..K_MAX`).
Continuum sits above finite, gated by a completeness axiom that finite data
cannot itself earn. Honest ceiling stated in the receipt: finite proxy only,
the reals are not constructed here.

**Engines.** sympy (load-bearing, exact Hartley-growth formula and
per-level interval-width identities), z3 + cvc5 (supportive). numpy, jax,
julia: not run (exact `Fraction` arithmetic used instead of numpy).

**Status.** EARNED, ordering PROPOSED not canon.

---

## Layer 9 — real to complex

**Formal object.** Local tomography: does the state-space dimension of a
composite system factor as `d(A x B) = d(A) * d(B)` under real versus
complex Hilbert-space amplitudes.

`real_vs_complex_tomography.py`, verdict `COMPLEX_EARNED_BY_TOMOGRAPHY`
(commit `c9fed6057`). Complex: `d2 = d1^2` holds. Real: `d2 = 10 > d1^2 = 9`
— fails by the standard one-dimensional two-rebit deficit. Among `{R, C}`
the reconstruction axiom selects complex; `C -> R` (forget the imaginary
part) is one-way. The build honestly deviated from the owner's informal
Bloch-figure convention to the correct unconstrained (Hardy) convention —
flagged in the receipt, not silent.

**Engines.** sympy + numpy (load-bearing), z3 + cvc5 (supportive). jax,
julia: not run.

**Status.** EARNED, ordering PROPOSED not canon.

---

## Held-open negatives with no strong carrier (recorded, not built against)

Two arrows in the panel run got only single-model, weak coverage — recorded
so they are not silently dropped, but neither is a genuine refutation as
delivered:

- **finite_to_continuum** (llama only): claims a finite dataset can
  sometimes be exactly represented by a continuum model, with no concrete
  carrier given. Unverified as stated.
- **bures_to_fubini_study** (llama only): asserts the QGT (hence Berry
  curvature) can be computed from the Bures metric alone. This is
  confused on its face — the QGT's antisymmetric part is by definition not
  in the symmetric Bures/Fubini-Study metric — and restates the arrow's own
  claim rather than refuting it. Recorded as a failed refutation attempt:
  the arrow survives this particular probe.

Cross-cutting pattern the panel surfaced across the magma, `pure_to_vn`, and
anticommutation negatives: the strongest recurring objection is never that
an arrow is factually wrong, but that several one-way claims implicitly
assume a specific choice of what data survives the quotient (discard
associator triples / discard basis choice / discard generator relations)
without arguing that discard as a separate, contestable step. This is a
methodological gap worth checking against the actual sim code for
`magma_to_semigroup` and `pure_to_vn` specifically — those are the two
arrows where the panel's proposed reconstruction is concrete enough to
actually test. Not yet done.

---

## Layer 10 (top) — speculative physics: SPECULATIVE / NUMEROLOGY fence

Everything below this line is standard finite/quantum math with a gated
witness. Everything from here up is synthesis pasted from an external
Gemini thread, run through a six-model NVIDIA panel
(deepseek-v4-flash, qwen3-next-80b, llama-3.3-70b-instruct,
nemotron-super-49b-v1.5, glm-5.2, gpt-oss-120b) on 2026-07-21 for
classification only. No claim here is admitted; no arrow above this line is
confirmed or denied by the panel. Three roster models named originally
(deepseek-v3.1, qwen3-235b, kimi-k2-instruct) were dead endpoints and were
substituted — recorded, not silently dropped. Splits are held open per
standing anti-collapse rule; do not read a single tag as consensus where the
vote was divided.

| # | Claim | Panel vote (of 6) | Status |
|---|---|---|---|
| 1 | E8 -> F4 -> G2 cascade + Clifford Weyl bundles -> Standard Model gauge group | 5 SPECULATIVE-SYNTHESIS, 1 EARNED (llama, uncorroborated outlier) | SPECULATIVE |
| 2 | 3 generations = 3 real eigenvalues of the Freudenthal cubic over `J_3(O)` | 4 SPECULATIVE-SYNTHESIS, 1 STANDARD-BUT-UNBUILT (glm-5.2: the eigenvalue fact is real algebra, just not derived here), 1 LIKELY-WRONG/NUMEROLOGY (nemotron) | SPECULATIVE (3-way split, held open) |
| 3 | Gravity = entropic push, `1/R^2` convergence of Feynman amplitudes on "Bekenstein-Hopf shells" | 4 LIKELY-WRONG/NUMEROLOGY, 2 SPECULATIVE-SYNTHESIS | NUMEROLOGY — weakest-link plurality pick (3 of 6 models named this claim weakest); "Bekenstein-Hopf shell" is not a recognized object in any model |
| 4 | Lambda = global trace defect / Hodge core, solves the `10^120` problem | exact 3/3 split, SPECULATIVE-SYNTHESIS vs LIKELY-WRONG/NUMEROLOGY | NUMEROLOGY (held as a genuine, exact split — not averaged) |
| 5 | Dark energy = future-inbound / dark matter = past-outbound flux, same shell | exact 3/3 split, SPECULATIVE-SYNTHESIS vs LIKELY-WRONG/NUMEROLOGY | NUMEROLOGY (glm-5.2 called it "word-salad coincidence-matching" and separately named it weakest link) |
| 6 | QHNN as native hardware, 16 basins = quantum associative-memory attractors | 4 SPECULATIVE-SYNTHESIS, 2 STANDARD-BUT-UNBUILT (qwen, nemotron: quantum Hopfield networks and attractor dynamics are real objects; the "16 basins as native hardware" framing is not) | SPECULATIVE |
| 7 | Bures-metric / Hopf-fiber spinor databases replacing vector databases | 6/6 SPECULATIVE-SYNTHESIS, unanimous | SPECULATIVE — the cleanest tag in the set: every model affirms the math objects are real, none derives the database-replacement proposal |
| 8 | Xi gravity-bridge = Petz recovery map | 4 SPECULATIVE-SYNTHESIS, 2 LIKELY-WRONG/NUMEROLOGY (deepseek, llama: "forced"/"misidentified") | NUMEROLOGY-leaning (deepseek separately named this its own weakest-link pick) |

No model called any claim EARNED except the single llama-3.3-70b vote on
claim 1 — uncorroborated by any other model, treated as an outlier, not
consensus. Weakest-link plurality: claim 3 (Bekenstein-Hopf `1/R^2`
gravity), named by half the panel; second place claims 5 and 8 (one vote
each); nemotron's weakest-link answer was truncated by the token cap but
pointed at claim 2.

Panel deliverables: `nvidia_fuel_audit.py`, `nvidia_fuel_audit_results.json`
(scratchpad, session `4e94deaf-efb4-4f21-8416-8c730d026545`).

---

## Presumption ordering, summarised

Two axes are settled by gated arrows (with the caveat that ordering itself
stays `PROPOSED not canon` per every receipt):

- **{associativity, commutativity}** — `law_order_branch.py`: the two
  imposition orders RE-MERGE at the same 2-element semilattice (genuine
  isomorphism), but the path cost is order-dependent (N01: different
  structural-entropy drops per step). A genuine non-re-merging branch exists
  on the same machinery (`S`/`H` operators) as a contrast pole — the
  detector was pinned at both re-merge and non-re-merge before this verdict
  was read off, not hard-wired.
- **{associativity, sign-symmetrization}** — same three-pole question,
  PROPOSED not yet run (`CARD_assoc_sign_order_branch.md`).

Everything else in the presumption stack (G2/octonions/E8 placement,
finitude vs non-commutation vs non-associativity vs anticommutation vs
sedenion order) remains explicitly OPEN per
`ROOT/META_AXIOMS_LLM_FAILURE_GUARD.md` — not hard-coded, not to be treated
as settled by any single arrow above.

---

## Section headers (for quick scan)

1. Root: identity is probe-relative — presumption floor
2. Bare magma frontier — EARNED (`magma_to_semigroup`, `magma_smt_genuine`)
3. Algebra ladder (identity/inverse/associativity/commutativity) — EARNED (2 of 4 sub-arrows)
4. Presumption order on {associativity, commutativity} — EARNED (`law_order_branch`); PROPOSED extension to {associativity, sign}
5. Anticommutation rung (Clifford/Grassmann/commutative) — EARNED (`anticommutation_rung`)
6. Quantum entropy axis (pure/VN/Shannon) — EARNED (`pure_to_vn`, `vn_to_shannon`); PROPOSED rung below (Hopf fiber phase-forget)
7. Renyi alpha-axis — EARNED (`renyi_alpha_axis`)
8. Bures/Fubini-Study/Berry geometry — EARNED (`bures_to_fubini_study`); PROPOSED rung above (Schmidt torus foliation)
9. Finite to continuum — EARNED (`finite_to_continuum_rung`)
10. Real to complex — EARNED (`real_vs_complex_tomography`)
11. Speculative physics top (SM emergence, entropic gravity, Lambda, QHNN, spinor databases, Petz bridge) — SPECULATIVE / NUMEROLOGY, fenced, no repo arrow confirmed or denied

## Status tally

- EARNED: 10 rungs (11 receipts counting the supporting genuine-mechanism SMT sim)
- PROPOSED: 3 (`CARD_schmidt_tori_foliation_arrow`, `CARD_assoc_sign_order_branch`, `CARD_hopf_fiber_phase_forget_arrow`)
- SPECULATIVE: 4 claims (1, 2, 6, 7 — plurality or majority SPECULATIVE-SYNTHESIS; claim 2 is a genuine 3-way split held open)
- NUMEROLOGY: 4 claims (3, 4, 5, 8 — plurality or exact-split LIKELY-WRONG/NUMEROLOGY; claims 4 and 5 are exact 3/3 splits held open, not averaged)
