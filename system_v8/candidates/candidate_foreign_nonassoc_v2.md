# Candidate: Nonassociative (Octonionic) Carrier with Grouping-Order as Load-Bearing Structure, v2

**Supersession note:** this is a v2 restatement/improvement of
`candidate_foreign_nonassoc.md`, produced in a 2026-07-21 fuel-regeneration
task. Per the immutability rule, this is a NEW fuel-pool entry admitted
through the same gates as the original, never an overwrite. The original
document remains on disk unchanged, as its own honest history. §9 below names
exactly what changed and why; nothing here silently substitutes a claim.

**Status:** CONDITIONAL PROPOSAL — not asserted as correct.
`promotion_allowed: false`, `formal_admission_allowed: false`. This candidate
exists to test whether nonzero associators and nonassociative grouping earn
distinctions the classical/quantum/QCA frontiers do not. Explicitly
speculative, and one candidate among rivals in `system_v8/candidates/` — it
is not canon and does not admit anything. Role: `structural_rival`.

---

## 0. Stance and role

The carrier is genuinely foreign to the pool's other members: associativity
is not assumed at the base (contrast: standard quantum mechanics assumes
associative matrix algebra). Grouping-order is load-bearing — how `x·y·z` is
parenthesized determines what the system distinguishes, not just parameter
values. No state space is prior; states emerge as quotient classes under
associator-preserving probes. Neither Hilbert space nor classical probability
is installed initially.

## 1. Ordered layer list (conditional structure)

Hypothesized, not canonical — one plausible sequence under the constraint
that distinguishability (via probes) drives layer stratification.

| Layer | Name | Role | Presumed by |
|---|---|---|---|
| L0 | Constraint surface (distinguishability) | Root: finite probe quotient on a demanded edge set; identity is probe-relative only | Nothing; L0 is primitive |
| L1 | Associator floor (octonionic grouping) | Eight octonion units {1,i,j,k,l,il,jl,kl}; multiplication table with nonzero associator as primary invariant | L0's demand that distinctions remain under nested probes |
| L2 | Density matrices on octonion base | 2x2 density matrices with octonion-valued entries; GKSL generators preserve octonion structure | L1's grouping constraints must persist in linear algebra |
| L3 | Nested Hopf tori (octonion fibers) | Hopf fibration S^7 -> S^4 with octonion line bundles | L2 tensorial structure requires geometric grounding |
| L4 | S^2 layer (intermediate geometry) | Quotient of Hopf structure; octonion-preserving projection | L3 torus nesting demands intermediate reduction |
| L5 | S^3 / Weyl spinor layer | Spinors realize some octonion operations exactly, others only projectively | L4 geometry requires spinorial witness |
| L6 | Entropy-geometry coface (octonion quotient surface) | Octonion grouping failures read as unresolved entropy AND geometric misalignment | L5 spinor layer must admit finitary observation surface |
| L7 | Attractor basin dynamics (grouping-aware) | Heat/exploration gradient drives basin trajectories; associator-nonzero failures cause branching | L6 coface must support directed evolution |

## 2. The carrier

The carrier is the sedenion-reduction octonion algebra O with standard
multiplication `x*y` where `(x*y)*z != x*(y*z)` for generic triples, a
nonzero, measurable associator `alpha(x,y,z) = (x*y)*z - x*(y*z)`, and the
7-dimensional associator surface (not the 8-dimensional algebra) as the
primary structure. Probe family M: for each triple `(x,y,z)` in a finite
grammar, `alpha(x,y,z)` is a grouping-order distinguishability test.
Admissibility constraint C: two representations are indistinguishable under
M iff their associators agree on all tested triples.

## 3. What each layer presumes

L0 -> L1: if identity is probe-relative (a=a iff a~b), the basic operation
relating two elements must itself be order-sensitive; associativity would
collapse order distinctions prematurely.

L1 -> L2: a finite algebra with nonzero associators must extend to a
representation *within* linear algebra, not *as* linear algebra.

L2 -> L3: density matrices on a non-associative base cannot be supported on
a commutative point set; they require a non-commutative geometric carrier.

L3 -> L4: octonion Hopf geometry at S^7 -> S^4 is too rich for observation;
S^2 is the first intermediate reduction that tests whether grouping-order
survives geometric quotienting.

L4 -> L5: S^2 alone is insufficient to generate probe-relative identity
under all probes; S^3's spinorial structure allows finer probe resolution.

L5 -> L6: L5's spinorial quotient must be finite and probe-interrogable;
L_D(pi) is the unresolved-distinction count when a spinor representation
fails to preserve the associator demands D.

L6 -> L7: a static coface is insufficient; the ratchet demands an
evolutionary direction — configurations with smaller associator defects are
more stable.

## 4. Persistence and evolution (conditional mechanism)

Octonion grouping-order is stable under restriction to quaternionic
subalgebras (where associativity is automatic), octonion basis changes
preserving the multiplication table, and associator-invariant gauge
transformations. It fails under forced commutativity, enforced global
associativity, or probeless observation.

Evolution (attractor basin dynamics): an initial population of octonion-based
density-matrix configurations, each with an associator-defect score
`d(pi) = |{(x,y,z) in D : alpha_pi(x,y,z) != 0}|`; a gradient
`g_D(pi -> rho) = d(pi) - d(rho)`; heat allows uphill moves, admission
temperature kills unstable basin edges; the system ratchets toward minima of
associator defect. A basin-isolated minimum `d(pi*)` "locks" — the
minimal-defect representation is the provisional MSS for that basin,
conditional on the tested demand set D and probe family M. Nesting: a
lower-defect basin may contain sub-basins if D is refined.

## 5. Probe / distinguishability test, and load-bearing associator witness

Probe family M (finite grammar): for a tested grammar
`G = {(a_i, b_j, c_k)}`, `P_G(pi) = {alpha_pi(a_i,b_j,c_k) : (a_i,b_j,c_k) in G}`.
Two representations are M-indistinguishable iff `P_G(pi) = P_G(rho)` exactly.

Per-layer distinguishability test: L1 (two multiplication tables distinct
iff associator surfaces disagree); L2 (two density-matrix realizations
distinct iff octonion-entry associators differ under a chosen probe
grammar); L3 (two Hopf fiber structures distinct iff curvature/Chern class
depends on associator structure); L4-L5 (distinctiveness tested by whether
the quotient preserves or kills the associator witness); L6 (coface loss
`L_D(pi)` is the direct count of unresolved distinctions); L7 (two basins
distinct iff minimal-defect attractors differ, or the gradient trajectory
branches before a common minimum).

**Load-bearing associator witness (the key test):** choose a tested triple
`(x,y,z)` from the demand set D; compute `alpha(x,y,z)` for each candidate.
This candidate WINS IF a competing associative candidate requires artificial
structure (extra scalars, enlarged symmetry groups, hidden canonical choices)
to distinguish the same triple, while this candidate resolves it purely from
octonion grouping-order. The associative candidate WINS IF the same
distinguishability is achievable with equal or fewer degrees of freedom, or
an external, non-load-bearing control drives the outcome more parsimoniously.

## 6. Honest weaknesses (structural)

1. Finite grammar capture: a static tested grammar G may miss a new
   `(x,y,z)` that exposes a nonzero associator. Provisional until a complete
   grammar is fixed by the owner's demands.
2. Octonion non-calibration: no proof that O is the minimal nonassociative
   algebra admitting the required nesting structure; smaller nonassociative
   algebras (Lie-Malcev, Jordan triple systems) are unexplored.
3. GKSL compatibility unclear: whether GKSL superoperators can be defined
   canonically on octonion-valued density matrices is unknown; the standard
   Lindblad form assumes associativity in the commutator and anticommutator.
4. Metric and measure absent: `L_D(pi)` is a count, not a probabilistic or
   geometric integral; connection to classical entropy (von Neumann,
   Shannon) is entirely open.
5. Attractor basin formalism speculative: no Lyapunov function or rigorous
   stability proof; basin dynamics may be unstable or need undiscovered
   constraints.

## 7. Omitted layers (genuine gaps)

Sub-L0 structure (nothing below constrained distinguishability is modeled);
sedenion (16-dimensional) extension, kept as a separate candidate; the
quantum-geometric (C*-algebra, spectral triple) version of the Hopf/octonion
geometry; Chern-Simons and other topological invariants; any physical
interpretation beyond QIT (no thermodynamics, classical mechanics, field
theory, cosmology layer).

## 8. Order uncertainty (where layers may be misplaced)

L1<->L0 (could octonion grouping-order itself be the root constraint rather
than emerging from it — owner decision required); L2<->L3 order (density
matrices on octonion base vs. geometric constraint forcing octonion-valued
entries, direction not ruled out); L4 vs L5 independence (S^2 and S^3 related
by a covering map — genuine intermediate rung, or compressible); L6
placement (could the coface emerge at L2 or L3 instead); L7 closure
(attractor-basin dynamics as a layer, or a transverse description applying
L0-L6 simultaneously).

## 9. What changed from v1 (named explicitly, per the supersession note)

- Restated the role explicitly as `structural_rival`, matching this pool's
  `variation_slots` vocabulary (`fuel_gate/fuel_adequacy_gate.py`
  `SLOT_DESCRIPTIONS`) — v1 did not name the slot term explicitly in its own
  text.
- Consolidated the load-bearing associator witness into one explicit
  win/lose test in §5 (v1 stated the same content across two subsections;
  this v2 keeps the content identical but states the win/lose branches
  together, once, to reduce restatement drift).
- No change to the carrier definition, the layer list, the persistence
  mechanism, the honest weaknesses, the omitted layers, or the order
  uncertainty beyond the reorganization named above — this is a restatement,
  not a redesign. In particular this v2 does NOT resolve any of v1's named
  open questions (minimal nonassociative algebra, GKSL compatibility,
  Lyapunov stability) — those remain open exactly as v1 left them.

## 10. Admission ceiling, defeat conditions, and next steps

This candidate is proposed only as a test of whether nonzero associators can
be load-bearing witnesses that distinguishing power derives from
grouping-order, and a check on whether octonion algebra admits a finitary
realization weaker than full quantum mechanics and genuinely distinct from
classical mechanics. It makes no claim to being the true carrier of the
ratchet system, to outperforming associative quantum mechanics without new
empirical data, to grounding physical law, or to having a unique minimal
representative.

**Witness / defeat condition, falsifiable and stated as a can-fail check:**
this candidate loses its "genuinely foreign" status the moment an associative
rival distinguishes the same demanded triple with equal or fewer degrees of
freedom (§5); it loses its "minimal nonassociative carrier" status the moment
a smaller nonassociative algebra (Lie-Malcev, Jordan triple system) is shown
to carry the same associator-witness distinctions at lower cost (§6.2); and
the whole candidate would flip from "provisional structural rival" to
"eliminated" if a finite associator-measurement oracle (§5, not yet
implemented — named honestly as absent in both v1 and this v2) is built and
run, and it shows the associative rival wins on every tested triple in the
fixed demand set D.

**Next steps to test this candidate**, unchanged from v1: fix a finite
demand set D; implement the finite-grammar associator-measurement oracle;
compare parsimony against associative and QCA rivals on the same demands; if
it survives, run coupling and coexistence tests at higher rung nesting.

---

## 11. Notation and definitions (reference)

`alpha(x,y,z) = (x*y)*z - x*(y*z)` (associator; zero iff associative); `O`
(octonion division algebra); `M(pi, pi')` (probe family M distinguishes pi
from pi' iff `P_G(pi) != P_G(pi')`); `d(pi)` (associator-defect score);
`L_D(pi)` (coface loss); `Surv(D)` (candidates with `L_D(pi) = 0`); `M(D)`
(minimal elements of `Surv(D)` under partition refinement); `pi <= rho` (pi
coarser than rho if every block of rho lies within a block of pi).

**End of candidate proposal, v2**
