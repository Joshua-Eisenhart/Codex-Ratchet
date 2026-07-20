# Spinor-Otto Ladder — preregistered build card v0

Status: card only. No sim code has been written against this card.
`promotion_allowed: false` for every rung, at every stage, permanently —
this card does not define a path to canonical status by itself; it
defines the pass/fail gates a future sim result would have to clear to
even be considered evidence.

Literature grounding for this card: `~/wiki/projects/codex-ratchet/weyl-chamber-otto-attachment-hypotheses-2026-07-19.md`,
"round 2: spinor-Otto ladder" section (2026-07-19). Read that section
before building any rung — it states which parts of this card rest on
real published results (Rungs 1 and 2's core mechanism, and the
geometric-phase framing) and which parts are honestly this project's own
unclaimed territory (Rung 3's G2 framing, Rung 4 entirely).

## Binding process rules for this ladder

1. **One rung at a time.** Rung `N+1` is blocked until Rung `N` has a
   receipt (a result JSON under `system_v8/otto_weld/results/`, not a
   claim in this card or in chat).
2. **`promotion_allowed: false`** on every rung's receipt, unconditionally.
   This ladder produces `tool_lego_fit_probe`-class evidence at best,
   never canonical, never bridge, never axis-level, per this repo's
   stage-gate and sim-requirements rules.
3. **A negative is a result.** Every rung below states, explicitly, what
   a negative outcome would look like and that a negative outcome is not
   a failure of the card — it is the card doing its job. Do not soften a
   negative into an "inconclusive" or quietly drop the rung.
4. **Controls are load-bearing, not decorative.** Every rung's control
   must actually run and actually be capable of failing the sim's own
   headline claim. A control that cannot fail is not a control.
5. **Builds go through the three-engine sim contract** (Julia canon / JAX
   workhorse / PyTorch when scoped) per this repo's standing rules —
   this card does not waive that; it is silent on engine assignment per
   rung because that is a build-time decision, not a preregistration
   decision.
6. **Cross-references, not dependencies.** This ladder is expected to
   interact with two lanes that are running independently right now:
   `system_v8/otto_weld/otto_stroke_map_v0.py` (results at
   `system_v8/otto_weld/results/otto_stroke_map_v0/receipt.json`, current
   classification `tool_lego_fit_probe`) and
   `system_v8/entanglement_pawl/pawl_v0.py`. Rungs 1-2 should reuse or
   extend that machinery rather than re-deriving GKSL stroke plumbing
   from scratch, but this card does not require it — a rung that
   diverges from those files should say why in its own build, not
   silently duplicate them.

---

## Rung 1 — single-qubit Otto on the project's GKSL stack

**Object.** A single-qubit Zeeman Hamiltonian `H(t) = -(B(t)/2) sigma_z`
run through a four-stroke Otto cycle on the project's existing GKSL
engine: isentropic compression (`B: Bc -> Bh`, isolated), isochoric hot
bath coupling (fixed `B = Bh`, thermalize toward the hot bath), isentropic
expansion (`B: Bh -> Bc`, isolated), isochoric cold bath coupling (fixed
`B = Bc`, thermalize toward the cold bath). The Zeeman gap is the piston.

**Preregistered pass criterion.** In the slow (quasi-static) limit, the
cycle's efficiency `eta = W_net / Q_hot` must land at `1 - Bc/Bh` within
a preregistered numerical tolerance (proposed: relative error `< 1e-3` at
the slowest tested ramp rate, tightening as ramp rate decreases — state
the actual tolerance curve in the build, do not silently pick one after
seeing the number). This is the standard textbook Otto bound for a
two-level system; it is not itself a novel claim, it is a sanity floor
this rung must clear before anything downstream is trusted.

**Quantum-friction control (load-bearing, not decorative).** Run the same
cycle at a fast (non-adiabatic) ramp rate. Per the friction literature
cited in the round-2 wiki section (arXiv:1605.02522, arXiv:1906.07473),
a fast ramp through a time-dependent, non-commuting-at-intermediate-times
Hamiltonian must generate off-diagonal coherence in the instantaneous
energy eigenbasis, and that coherence carries a measurable extra-work
penalty relative to the slow-ramp trajectory at matched `Bc`, `Bh`, and
bath temperatures. **Preregistered check:** `W_fast > W_slow` (more work
input, or equivalently lower measured efficiency than the slow-ramp
value) at matched cycle boundary conditions, and the excess must
correlate with the off-diagonal coherence magnitude in the instantaneous
eigenbasis at the end of each isentropic stroke (report both quantities,
do not report only the pass/fail on work). **What a negative looks
like:** if `W_fast` is statistically indistinguishable from `W_slow`
across a swept range of ramp rates, or if it varies but does not
co-vary with the measured coherence, that is a genuine negative — it
would mean this project's GKSL stroke implementation is not exhibiting
quantum friction in the textbook sense, which is itself worth knowing
before Rung 2 is trusted to carry a friction-sensitive claim.

**Honest constructibility note.** This is the least risky rung — a
single-qubit driven-and-dissipative GKSL cycle is squarely inside
existing repo machinery (`otto_stroke_map_v0.py` already runs
purity-parameterized channels through Otto-shaped strokes). The risk is
entirely in getting the tolerance and the friction-correlation check
preregistered honestly, not in the underlying computation.

---

## Rung 2 — coupled two-qubit Otto through the Weyl-chamber perfect-entangler region

**Blocked until Rung 1 has a receipt.**

**Object.** Two coupled qubits (A, B), each running its own Otto piston
stroke, plus an interaction stroke where a two-qubit coupling term is
turned on and off according to a schedule parameterized by the
two-qubit-gate Weyl-chamber coordinates `(c1, c2, c3)` (Zhang-Vala-
Sastry-Whaley convention). The interaction-stroke schedule is chosen to
sweep through, near, and outside the perfect-entangler polyhedron (the
sub-region of the chamber where the instantaneous gate can generate
maximal entanglement from a product state).

**Preregistered metric.** Work output of the coupled two-qubit cycle
versus an uncoupled-pair control (two independent Rung-1 cycles run in
parallel with the interaction term held at zero) at matched thermal
budgets (same bath temperatures, same cycle duration, same total drive
energy available). Report `W_coupled - W_uncoupled` as a function of
where the interaction-stroke schedule sits relative to the
perfect-entangler region boundary.

**Entanglement-work sign tracking (ties to the entanglement-pawl lane).**
For every schedule point, compute `S(A|B)` (the conditional entropy of
qubit A given qubit B, state-only, following the existing
`entanglement_pawl` convention of never letting drive enter the entropy
functional directly — see `system_v8/entanglement_pawl/pawl_v0_v43_card.json`,
"required invariants": "all entropy and coherent-information functions
take a density state and no drive argument"). Track the sign of `S(A|B)`
across the interaction stroke alongside the work-output delta. The
preregistered question, stated as a question rather than a predicted
answer per this card's anti-collapse discipline: does a schedule that
drives `S(A|B)` negative (an entanglement-fuel-bearing trajectory in the
pawl lane's vocabulary) co-vary with `W_coupled > W_uncoupled`, or is
work output independent of the `S(A|B)` sign?

**Honesty note on the literature framing.** Per the round-2 wiki
section, the real literature (arXiv:2102.11657, arXiv:2503.21590)
supports an entanglement/work-extraction covariation stated in terms of
level populations, not in terms of the Weyl-chamber gate-geometry
framing used here. The chamber-coordinate framing of the interaction
stroke is this project's own addition, not a replication of a published
protocol — say so in the build's own header, do not imply a paper does
this exact construction.

**What a negative looks like.** If `W_coupled - W_uncoupled` shows no
consistent relationship to either the chamber-region location or the
`S(A|B)` sign across a swept set of schedules, that is a real negative:
it would mean either (a) this project's specific coupled-GKSL
implementation does not exhibit the entanglement-work link the
literature reports in other coupled-spin models, or (b) the literature's
effect is real but the Weyl-chamber-gate framing is the wrong lens for
locating it. Distinguish (a) from (b) before concluding either — (a) is
checkable by comparing against a population-based metric matching
arXiv:2503.21590's framing directly, on the same run.

**Honest constructibility note.** Moderate risk. Two-qubit GKSL with a
tunable coupling term and Weyl-chamber-coordinate scheduling is a real
build (not exotic), but the "locate the interaction stroke inside chamber
coordinates" step requires decomposing the instantaneous coupling
propagator into its local-invariant `(c1,c2,c3)` and has not been done
anywhere in this repo yet — budget real build time for that
decomposition step alone, separate from the GKSL evolution itself.

---

## Rung 3 — seven-level G2 engine

**Blocked until Rung 2 has a receipt.**

**Object.** A seven-level quantum system whose structure is built from
the 7-dimensional fundamental representation of G2, realized as the
imaginary octonions (structure constants already implemented in this
repo's exceptional-algebra solvers — see `system_v7/constraint_core/julia_canon/src/ExceptionalAlgebraCanon.jl`
for the checked-in `Octonion`/`Albert` Julia canon, and the Pack-186
native G2/F4 derivation at
`.../owner_packs/pack186/RATCHET_186_REAL_NESTED_ENTROPIC_GEOMETRIC_MANIFOLD_2026-07-19_v1/active/exceptional_stack_geometry.py`
which executed `G2 = Der(O)`, dimension 14, natively — flagged honestly:
that Pack-186 file currently lives in a session scratchpad path, not
under version control in this repo; before Rung 3 build time, it must be
pulled into the repo proper, re-derived from
`ExceptionalAlgebraCanon.jl`, or cited only as prior-session provenance —
not silently treated as an existing repo artifact). Run Otto-shaped
strokes (an analogous compression/bath/expansion/bath four-stroke
structure, generalized to seven energy levels) on this spectrum, with a
G2-structured Hamiltonian family (built from the 14 G2 generators acting
on the 7-dim rep) as the piston.

**This would be the first load-bearing use of G2 in the model.** Every
prior G2 appearance in this repo (`system_v4/probes/sim_*g2*`,
`system_v6/sims/*g2*`, Pack-186's own native execution) is either a
scratch tool-lego-fit probe or explicitly "computed natively... but not
selected" (Pack-186's own verdict, per the wiki pack-lineage record). No
G2 object anywhere in this repo has ever been load-bearing for a
measurable outcome. State that plainly rather than implying precedent.

**Preregistered pass criterion — a generic-symmetry control, mandatory.**
Build a control: a seven-level system with the *same* spectrum (same
energy gaps) and the *same* number of independent Hamiltonian-family
generators (14), but with those 14 generators chosen generically (a
random `su(7)`-adjacent-dimension-matched Hermitian basis, not
G2-structured) rather than as the actual G2 generator set. Run the
identical Otto-stroke protocol on both. **The preregistered question:**
does the G2-structured engine show any measurable difference from the
generic-symmetry control — in efficiency, in friction cost, in any
quantity this rung defines — at matched spectrum and matched generator
count?

**Honest statement of the negative, stated in advance per the task's own
framing:** if the G2 symmetry does nothing measurable versus the generic
7-level control, that negative *is* the result. It would mean G2's
exceptional structure is not, by itself, thermodynamically load-bearing
for an Otto-type cycle on its fundamental representation — a genuine and
useful finding, not a failed build. Do not retry with a different metric
until one shows a difference; that is exactly the p-hacking pattern this
project's fabrication-audit discipline exists to catch. If a difference
does appear, it must be checked against the generic-control seed
(rerun with multiple independent random generic bases) before being
called a G2-specific effect, since a single generic draw is not a
control, it is one sample.

**Honest constructibility note.** High constructibility risk in one
specific place: decomposing the G2 Weyl chamber's 12 walls into a
concrete Hamiltonian-schedule parameterization for the strokes is not a
solved problem anywhere in this repo (the existing G2 sims compute
structure constants, root systems, and chamber geometry as static
objects — none of them drive a dynamical process through the chamber).
Budget this as the highest-uncertainty rung in the ladder. It should not
be started until Rungs 1-2's stroke-and-control machinery is solid,
since Rung 3 reuses that machinery on a higher-dimensional spectrum.

---

## Rung 4 — Albert-algebra spectral strokes

**Blocked until Rung 3 has a receipt.**

**Object.** A 27-dimensional spectral simplex from the eigenvalue
structure of the Albert algebra `H3(O)` (3x3 octonionic Hermitian
matrices, Jordan product only — `X ∘ Y = 1/2(XY+YX)`, never associative
matrix multiplication as a stand-in). Otto-shaped strokes are defined
directly on the Jordan-algebraic eigenvalue simplex (the natural
generalization of the density-matrix spectral simplex used in ordinary
quantum thermodynamics), with an `F4`-invariant entropy functional
(`F4 = Der(H3(O))` acting as the symmetry preserving the Jordan
structure) standing in for von Neumann entropy.

**Honesty note, stated up front per the task's framing:** the round-2
literature pass found no real literature putting a Gibbs state or a
thermal entropy functional on the Albert algebra. This rung is the
model's own territory. It should be written up as such — not as an
implementation of an existing (obscure) protocol.

**Non-associative friction — the load-bearing novel metric.** Ordinary
quantum friction (Rung 1) is a cost from non-commutativity under
finite-time driving. On a non-associative algebra, there is a second,
structurally distinct cost available: the failure of the Jordan
identity / Jordan-BCH-type composition law under fast strokes, measured
via the Jordan associator `(x,y,z) = (x∘y)∘z - x∘(y∘z)` accumulated along
a fast-stroke path versus a slow-stroke path. **Preregistered check:**
run the stroke schedule at slow and fast rates; measure the maximum and
median Jordan-identity residual (the same quantity already computed in
this repo's existing `H3(O)` receipt — see gate below) along each
trajectory; the preregistered claim under test is that the fast-stroke
trajectory accumulates a larger non-associative-friction residual than
the slow-stroke trajectory, analogous to Rung 1's ordinary quantum
friction but with no literature precedent to check it against.

**Gating receipt — must be checked before this rung is built, not
after.** `system_v8/otto_weld/results/albert_field_atlas_188.json`-class
evidence already exists in this project's history (Pack 188,
`ratchet.four_engine_albert_atlas_comparison.v1` schema; the file itself
currently lives at
`.../owner_packs/sweep/RATCHET_188/.../results_188/albert_field_atlas_188.json`
in a session scratchpad, not yet in this repo's version control — pull
or re-derive before relying on it as a repo artifact). That receipt found:
four independent three-engine `H3(O)` Albert charts (dimension 27 each)
pass the Jordan identity exactly (`max_jordan_identity_residual` on the
order of `1e-16`, machine precision) and glue exactly at shared node/edge
coordinates (`overlap_coordinate_defects`: all `0.0`), while a single
global four-engine `H4(O)` Jordan carrier (dimension 52) **fails**
strongly on both a generic random-sample control
(`pass_fraction_under_tol: 0.0`, median residual `~0.72`) and on the
specific executed field (`max_jordan_identity_residual: ~1.2e-7`,
`jordan_pass: false`). The receipt's own stated placement result: "The
four-engine field can be covered by four mutually consistent `H3(O)`
charts. It cannot be one `H4(O)` Jordan state space."

**Binding constructibility gate from that receipt.** Rung 4 must be
built on the `H3(O)` chart structure (27-dimensional, three-node local
charts, glued at shared coordinates where multiple charts overlap) —
**not** on a naive extension to a single global higher-dimensional
`H4(O)`-style object, which the existing receipt shows fails. If Rung
4's build wants more than three coupled subsystems, it must use the
overlapping-chart structure (multiple `H3(O)` local charts glued at
shared coordinates), not a single larger Jordan algebra, unless a fresh
sim first re-derives that the `H4(O)` failure does not apply to the
specific construction being proposed. Treat the existing receipt as a
standing negative control this rung is not allowed to silently route
around.

**What a negative looks like.** If the non-associative-friction residual
does not distinguish fast from slow strokes (i.e. the Jordan-BCH failure
term is dominated by numerical noise rather than stroke-rate-dependent
structure), that is a clean negative: it would mean this rung's proposed
novel friction mechanism does not exist as a measurable effect at
achievable simulation precision, and the rung should be closed with that
finding rather than re-tuned until a signal appears.

**Honest constructibility note.** Highest risk in the ladder, on two
independent axes: (1) no literature exists to sanity-check the
construction against, unlike Rungs 1-3; (2) the binding gate above
means this rung cannot use the most naive global construction and must
instead build and maintain the overlapping-chart machinery, which adds
real implementation complexity before any physics question can even be
asked.

---

## Summary table

| Rung | Object | Pass criterion | Mandatory control | Literature anchor | Constructibility risk |
|---|---|---|---|---|---|
| 1 | single-qubit Otto, GKSL | `eta` to `1-Bc/Bh` within tolerance (slow limit) | fast-ramp friction penalty vs slow | real, direct (NMR + friction papers) | low |
| 2 | coupled two-qubit Otto, Weyl-chamber interaction stroke | `W_coupled` vs `W_uncoupled`, matched budget | uncoupled-pair control; `S(A|B)` sign tracking | real mechanism, thin chamber-framing | moderate |
| 3 | seven-level G2 engine | measurable difference vs generic-symmetry control | matched-spectrum, matched-generator-count random control | none (first load-bearing G2 use) | high |
| 4 | Albert-algebra spectral strokes | non-associative friction residual, fast vs slow | slow-stroke baseline; `H3(O)`-chart gate from existing receipt | none (model's own territory) | highest |

`promotion_allowed: false` applies to every row, unconditionally, at
every stage of build or result.
