# BUILD CARD — assoc_sign_order_branch

Proposal-sim card (cr-ratchet, stage-5). Standard finite math only. No coined terms.
Ceiling: `classification = "tool_lego_fit_probe"`, `promotion_allowed = false`,
`ordering_status = "PROPOSED not canon"`.

## Goal

Extend the `{associativity, commutativity}` re-merge/path-dependence result
(`law_order_branch`, committed c9fed6057) to the owner-open algebra set. Two
one-way arrows are already committed but NOT chained:
`magma ->[+associativity] semigroup` (`magma_to_semigroup`) and
`anticommutative ->[symmetrize, forget sign] commutative` (`anticommutation_rung`).
The memory names their ordering OPEN ("order of finitude/noncomm/nonassoc/
anticomm/sedenion is OPEN, DON'T hard-code"; Axis B: "the metric/sign and
associativity sub-branches NOT yet chained"). This card chains them and asks the
same three-pole question the `{A,C}` card answered: is the order of imposing
`+associativity` versus `+sign-symmetrization` a CHAIN, a RE-MERGING BRANCH with
path-dependent cost, or a GENUINE non-re-merging branch?

## Per-rung formal objects

| Rung | Formal object | Equation | Doc citation |
|---|---|---|---|
| carrier | small signed magma / 2-generator Grassmann basis | `V = span{1, e1, e2, e1e2}` with a fixed nonassociative signed product table | PROPOSED-not-documented (standard exterior-algebra basis; atlas does not order these) |
| law A | associativity congruence | `(xy)z ~ x(yz)`, quotient `S_assoc` | committed `magma_to_semigroup.py`; atlas §3.1 gives no algebra-law order |
| law Sym | sign-symmetrization | `x·y ~ +(y·x)` (forget the anticommuting sign) | committed `anticommutation_rung.py` (Grassmann = `g->0` degenerate Clifford) |
| path P1 | assoc-first | `free ->[+A] S_assoc ->[+Sym] end_1` | PROPOSED-not-documented |
| path P2 | sym-first | `free ->[+Sym] S_sym ->[+A] end_2` | PROPOSED-not-documented |
| endpoint test | table isomorphism | brute-force label-bijection preserving the Cayley table, `end_1 ≅ end_2`? | method from `law_order_branch.py` |
| path cost | structural-entropy trajectory | `ln|free| -> ln|mid| -> ln|end|` per path (N01 order-sensitivity) | method from `law_order_branch.py` |

Every algebra-law-ORDER row is PROPOSED-not-documented: the atlas ladder (§3.1)
orders geometry rungs, not the equational-law presumption order. The individual
law arrows are committed; their composition order is the open question.

## The arrow(s) to gate

Run both orders explicitly on ONE fixed carrier. Answer two strictly separated
questions (never conflated), exactly as `law_order_branch` did:

1. ENDPOINTS. Is `end_1` genuinely isomorphic to `end_2` (label-bijection on the
   Cayley table, not just equal cardinality)? If yes -> the branches RE-MERGE
   (the associativity/sign sub-branches join at a common destination = the
   congruence-lattice join over `{A, Sym}`).
2. PATH. Are the per-step structural-entropy drops order-dependent? If yes ->
   N01 holds: same destination, order-dependent cost.

Expected verdict: one of `CHAIN` / `REMERGE_PATH_DEPENDENT` / `GENUINE_BRANCH`,
computed, primary verdict NOT hardwired.

HONEST SUBTLETY TO FLAG IN THE BUILD (do not smooth): anticommutativity
`x·y = -y·x` needs additive/sign structure a bare magma lacks, so `Sym` is only
imposable on a SIGNED carrier (an algebra with a `-1`), whereas `A` is a pure
magma congruence. The two laws live on slightly different substrates; the card
must state whether the chosen carrier genuinely supports both, or whether the
composition is only defined on the signed sub-structure. If it is only partial,
report `GENUINE_BRANCH by substrate mismatch` honestly rather than forcing a
re-merge.

## Rivals / controls

- Three-pole detector pinned at all poles (as in `law_order_branch`): a known
  CHAIN pair, a known RE-MERGE pair (`{A,C}` result), and a known
  GENUINE-BRANCH pair (`S`/`H` subalgebra/homomorphic-image operators) run on
  the same machinery so the verdict is not an artifact.
- GENUINE control: a law pair that provably commutes (imposing them in either
  order gives byte-identical intermediates) — verifies the detector can register
  order-INsensitivity, so a `REMERGE_PATH_DEPENDENT` finding is discriminating.
- Anti-tautology: the isomorphism is brute-forced over all permutations; the
  path cost is the recomputed `ln|quotient|` trajectory. SMT (if used at all) is
  supportive non-vacuity only, NOT the carrier — per the 2026-07-21 systemic
  finding.

## Three-engine scoping

- `sympy` — LOAD-BEARING. Exact congruence quotients (`FiniteGroup`/permutation
  or union-find over the table), symbolic entropy trajectory.
- `numpy` / pure-Python — LOAD-BEARING. Cayley-table construction, brute-force
  isomorphism search, `ln|quotient|` per step.
- `z3` / `cvc5` — SUPPORTIVE only (`smt_role = supportive_nonvacuity_only`),
  out of `core_ok`. A genuine mechanism-encoded SMT is OPTIONAL here and, if
  built, must pin the actual table as constraints (pattern from committed
  `magma_smt_genuine.py`) so perturbing the table flips UNSAT — only then may
  its z3 be labeled load-bearing.
- `jax` — memory-gated; batched permutation search for the isomorphism brute
  force if `>= 0.40`, else queued honestly.
- `julia` — memory-gated; reference recompute of the quotients (Julia is Canon
  for algebra; if it runs its verdict is the reference).
- `qutip` — not applicable (no quantum state here); mark `tried=False`.

## Acceptance

- Starts from `SIM_TEMPLATE.py`; full manifest + positive/negative/boundary.
- Result JSON in `ratchet_contract/ratchetings/results/`; passes local rerun.
- ClaimGate hook tier0 PASS, exit 3 acceptable; receipt declares
  `classification` + `promotion_allowed=false`.
- Lev record: schema-valid projection; wiring may stay BLOCKED (honest residual).

## Ceiling

`tool_lego_fit_probe`, `promotion_allowed=false`. Does not settle a canonical
algebra-law order or support promotion. Poset effect if it holds: chains the two
committed Axis-B sub-branches (associativity, sign) and classifies their
composition order, PROPOSED. Feeds the owner-open `{finitude, noncomm, nonassoc,
anticomm, sedenion}` ordering question WITHOUT hard-coding it.
