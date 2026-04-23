# Proto-Ratchet Branch Space

**Date:** 2026-03-29  
**Purpose:** Preserve the current branch space opened by the root constraints without silently collapsing the current favored finite-QIT/Hopf basin into the only admissible endpoint.  
**Scope discipline:** This is a proto-ratchet control packet, not canon and not an owner-math packet. It tracks live branches, weak branches, open branches, and anti-smoothing rules.

---

## 1. Scope And Status

This packet is about branch space:

- what the root constraints seem to admit
- what the current corpus favors strongly
- what remains open rather than killed
- what must not be back-projected into canon

It is not:

- the allowed-math owner
- the geometry owner
- the `Ax0` bridge owner
- the `Ax0` cut owner

Related owner/index surfaces:

- [PROTO_RATCHET_ALLOWED_MATH_CHART.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/PROTO_RATCHET_ALLOWED_MATH_CHART.md)
- [PROTO_RATCHET_ADMISSIBLE_BRANCH_SPACE.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/PROTO_RATCHET_ADMISSIBLE_BRANCH_SPACE.md)
- [PROTO_RATCHET_CONSTRAINT_GEOMETRY_BASIN.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/PROTO_RATCHET_CONSTRAINT_GEOMETRY_BASIN.md)
- [CONSTRAINT_GEOMETRY_AXIS0_SEPARATION.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/CONSTRAINT_GEOMETRY_AXIS0_SEPARATION.md)
- [AXIS0_MANIFOLD_BRIDGE_OPTIONS.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/AXIS0_MANIFOLD_BRIDGE_OPTIONS.md)
- [AXIS0_CUT_TAXONOMY.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/AXIS0_CUT_TAXONOMY.md)

---

## 2. What Counts As A Branch

For this packet, a branch is a candidate family that the roots do not yet kill.

| Branch type | Meaning |
|---|---|
| admissible-math branch | a family of mathematical objects or formalisms allowed by the roots |
| geometry branch | a candidate compatible manifold or carrier realization |
| bridge/cut branch | a candidate way of turning geometry/history into a cut-state for `Ax0` |
| overlay branch | a downstream naming or symbolic family that must not be mistaken for kernel math |

---

## 3. Root Constraint Pressure

The root side currently says two things at once:

1. the roots strongly favor finite, witness-disciplined, noncommutative structure
2. the roots do **not** justify uniqueness by fiat

That is why branch space exists at all.

Key root-side open rules:

| Open item | Meaning |
|---|---|
| emergence order open | geometry-first vs axis-first is still open |
| uniqueness of manifold open | Hopf/S3 may be a stable attractor, not the only endpoint |
| allowable mathematics boundary open | admissible math may not be closed under completions |
| uniqueness assumptions broadly forbidden | paths, transports, cycles, dimensions, scalar functionals, and completions are not unique by default |

Key refs:

- [Constraints.md#L990](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/core_docs/a1_refined_Ratchet%20Fuel/constraint%20ladder/Constraints.md#L990)
- [Constraints.md#L1020](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/core_docs/a1_refined_Ratchet%20Fuel/constraint%20ladder/Constraints.md#L1020)
- [Constraints.md#L1124](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/core_docs/a1_refined_Ratchet%20Fuel/constraint%20ladder/Constraints.md#L1124)

---

## 4. Admissible-Math Branches

| Branch family | Current status | Why still live |
|---|---|---|
| finite-QIT state/operator/channel basin | strongest favored branch | executable, finite, noncommutative, probe-compatible |
| noncommutative algebra more broadly | live | follows directly from `N01_NONCOMMUTATION` without forcing one QIT package |
| order/refinement/lattice-like structures | live | distinguishability/refinement language is root-compatible |
| finite path algebra without primitive time | live | admitted before metric/time semantics |
| restricted category-like structures | live but later | transformation-first objects are proto-foundationally compatible |
| information geometry | late-live | explicitly admitted as late-emergent, not primitive |

Weak / not-yet-promoted:

| Branch family | Status | Why not stronger yet |
|---|---|---|
| completions / asymptotic tools | open but weak | allowable mathematics boundary is still open |
| probability-heavy descriptions | open but descriptive only | allowed as bookkeeping, not ontology |

Killed as primitive:

| Branch family | Why killed early |
|---|---|
| unrestricted reals / completed infinities | violate finitude |
| free metrics / global coordinates | smuggle geometry too early |
| free equality / free substitution | violate emergent identity discipline |

---

## 5. Geometry Branches

| Geometry branch | Current status | Why |
|---|---|---|
| finite-QIT carrier -> `S^3` / Hopf / `S^2` / nested tori / Weyl working layer | strongest favored branch | source-backed, executable, geometrically rich, fits the current basin |
| Hopf/S3 as unique minimal manifold | open, not locked | roots do not yet justify uniqueness |
| Hopf/S3 as one stable attractor among several | strongest open meta-read | explicitly supported by the constraint-ladder uncertainty register |
| non-Hopf compatible manifolds at higher cost | open, weak | allowed by the uniqueness-open rule, but not currently supported by executable evidence |

Key refs:

- [Constraints.md#L180](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/core_docs/a1_refined_Ratchet%20Fuel/constraint%20ladder/Constraints.md#L180)
- [Constraints.md#L805](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/core_docs/a1_refined_Ratchet%20Fuel/constraint%20ladder/Constraints.md#L805)
- [Constraints.md#L1020](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/core_docs/a1_refined_Ratchet%20Fuel/constraint%20ladder/Constraints.md#L1020)
- [PROTO_RATCHET_ALLOWED_MATH_CHART.md#L90](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/PROTO_RATCHET_ALLOWED_MATH_CHART.md#L90)

### 5.1 Strict geometry-branch comparison

| Geometry read | Status | What currently supports it | What would strengthen it | What would kill or weaken it |
|---|---|---|---|---|
| finite-QIT -> `S^3` / Hopf / `T_eta` / fiber-base / Weyl working layer | favored live basin | source-backed equations, executable probes, compatibility with finite-QIT state language | direct comparison wins against rival manifolds under the same witness/probe discipline | a rival geometry with equal or better executable fit and less auxiliary structure |
| Hopf/S3 as a stable attractor but not unique | strongest open meta-read | fits both the executable success and the uniqueness-open constraint register | explicit branch-comparison packet showing why it dominates while alternatives remain admissible | a proof of uniqueness, or strong rival geometry evidence |
| Hopf/S3 as uniquely forced from the roots | not earned | none at the root layer; only later working realization support exists | a derivation from root constraints through allowed math with no equivalent rival branch | current branch-space and handoff docs already weaken this as an overclaim |
| non-Hopf compatible manifolds | open but weak | uniqueness-open rule and nonclosure of branch-space | one worked alternative with real probes and clear handoff from allowed math | repeated failure to realize comparable loop/transport/probe structure |
| algebra-first with no committed manifold yet | open control position | protects the handoff order `roots -> allowed math -> later geometry` | clearer delayed-geometry realization that still reproduces the current executable strengths | proof that geometry commitment is needed earlier to preserve witness discipline |

Shortest safe read:

\[
\text{roots} \nRightarrow S^3/\mathrm{Hopf}\ \text{uniquely}
\]

\[
\text{finite admissible core} \to \text{finite-QIT packet} \to \text{Hopf/Weyl basin is currently favored}
\]

not yet:

\[
\text{finite admissible core} \Rightarrow \text{Hopf/Weyl as the only surviving geometry}
\]

---

## 6. Why The Current Basin Is Favored

The current favored branch is not arbitrary.

| Evidence type | What it favors |
|---|---|
| root constraints | finite admissible carriers and noncommutative operator language |
| working math packet | finite QIT objects, density matrices, CPTP maps, probes, Pauli basis |
| executable geometry probes | `S^3`, Hopf, `T_eta`, fiber/base, Weyl working layer |
| `Ax0` work | cut-state entropy/correlation functionals on top of that same basin |

So the strongest current favored branch is:

\[
\text{finite admissible core} \to \text{finite QIT realization} \to S^3/\text{Hopf}/T_\eta/\text{Weyl working layer}
\]

But the corpus still does **not** say:

\[
\text{roots} \Rightarrow \text{that branch uniquely}
\]

---

## 7. Branch Table

| Branch | Type | Status | Owner or anchor | What would strengthen it | What would kill it |
|---|---|---|---|---|---|
| finite-QIT state/operator/channel basin | admissible-math | favored live | [PROTO_RATCHET_ALLOWED_MATH_CHART.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/PROTO_RATCHET_ALLOWED_MATH_CHART.md) | more explicit root-to-QIT derivation | evidence of a better finite admissible basin |
| Hopf/S3/nested-tori/Weyl basin | geometry | favored live | [PROTO_RATCHET_CONSTRAINT_GEOMETRY_BASIN.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/PROTO_RATCHET_CONSTRAINT_GEOMETRY_BASIN.md) | direct comparison against alternative manifolds | stronger alternative geometry with equal or better fit |
| order/refinement/lattice branch | admissible-math | live | [PROTO_RATCHET_ALLOWED_MATH_CHART.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/PROTO_RATCHET_ALLOWED_MATH_CHART.md) | clearer executable realization | proof that it collapses into or is dominated by the favored QIT packet |
| restricted category-like branch | admissible-math | live but late | [Constraints.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/core_docs/a1_refined_Ratchet%20Fuel/constraint%20ladder/Constraints.md) | explicit finite admissible implementation | incompatibility with witness discipline |
| non-Hopf compatible manifolds | geometry | open but weak | [Constraints.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/core_docs/a1_refined_Ratchet%20Fuel/constraint%20ladder/Constraints.md) | a worked alternative candidate with live probes | proof that no rival manifold survives the same constraints |
| completions/asymptotic tools | admissible-math | open but weak | [Constraints.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/core_docs/a1_refined_Ratchet%20Fuel/constraint%20ladder/Constraints.md) | explicit justification under finitude | completion smuggling into primitive structure |

---

## 8. Promotion Rules

| Move | Needed before promotion |
|---|---|
| branch-space -> allowed-math chart | admissibility is clear and upstream-safe |
| branch-space -> geometry basin | branch has a real geometry packet and not just metaphor |
| branch-space -> owner bridge/cut docs | branch has already survived geometry and `Ax0` interface tests |
| branch-space -> canon | uniqueness or necessity is actually derived, not just favored |

---

## 9. Residue And Graveyard Rules

- rejected branches should stay visible as residue or graveyard entries
- open branches should not be silently dropped because the favored basin is currently stronger
- executable success for one branch does not by itself kill all alternatives
- overlay branches must never be allowed to masquerade as admissible-math or geometry branches

---

## 10. Do Not Smooth

- Do not equate the strongest current favored branch with the only admissible endpoint.
- Do not back-project `S^3` / Hopf / Weyl into the root constraints.
- Do not let executable success imply uniqueness.
- Do not let probe success for Hopf/Weyl silently kill non-Hopf branches that have not been fairly compared.
- Do not confuse “stable attractor basin” with “deduced theorem.”
- Do not let branch-space become owner doctrine.
- Do not quietly delete weaker but still-open branches from the basin.
