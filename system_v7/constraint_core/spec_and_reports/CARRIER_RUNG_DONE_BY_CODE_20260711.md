
## Rung C — dynamics_su2_forced_quaternion_not_carrier_sim.py (the rung above the carrier)
Given C^2, what reversible dynamics is forced? DEMAND: the dynamics group must act **transitively** on
the pure-state (Bloch) sphere — identity `a=a iff a~b` requires no distinguishable pair be permanently
unreachable. Measured Lie-closure dimension per generating set (engines agree numpy==JAX==Torch==Julia):

| generating set      | lie_dim | transitive |
|---------------------|---------|------------|
| {σz} (1 axis)       | 1       | no (latitude circle) |
| {σz,σx} (2 noncomm) | **3**   | **yes** (bracket generates σy) |
| {σz,σx,σy}          | 3       | yes (overshoots) |

z3 **and** cvc5 both return **UNSAT** to "a transitive set with Lie-closure < 3 exists" → transitivity
**forces the full su(2)** = SU(2) = Sp(1) = **unit quaternions**. su(2)=Im(ℍ) verified (Hamilton relations
i²=j²=k²=ijk=−1 exact). Erase-N01 control (abelian-only sets): **UNSAT** on both solvers (never transitive)
→ noncommutation is what reaches the sphere. Failability: if su(2) were only 2-dim the verdict would flip
to SAT (checked).

**VERDICT: the forced reversible dynamics is the unit quaternions Sp(1)=SU(2).**

**THE NEGATIVE THAT MATTERS (kept):** ℍ is forced as the **dynamics group**, NOT as the **carrier scalar
field**. ℍ scalars do not commute (measured commutator defect 0.87 ≠ 0), and a composite of two systems
needs commuting scalars to form a tensor product — so the carrier stays ℂ while the dynamics group is
unit-ℍ. "ℍ is forced" is TRUE for dynamics, FALSE for the carrier — exactly parallel to the octonion
result (Malcev dynamics nameable, 𝕆 carrier not forced). The fork is recorded, not hidden.

## Rung ladder so far (each a single gate, real tools, hypothesis-not-canon)
1. carrier bakeoff → ℂ **installed, not forced** (rebit passes weaker gate)
2. phase-closure → ℂ **forced** over rebit by the continuous no-distinguishability fiber
3. dynamics → **Sp(1)=SU(2)=unit ℍ forced as the dynamics group**, ℍ **not** forced as carrier scalar (negative)

Next open rung: does anything force ℍ (or 𝕆) as the *carrier field*, or is the carrier permanently ℂ
with only the dynamics climbing? (The octonion cluster already answers 𝕆-carrier = not forced; the ℍ-carrier
question is the immediate one.)

## Rung D — carrier_field_stays_complex_two_negatives_sim.py (is H/R/O forced as the carrier FIELD?)
The dynamics rung forced unit-ℍ as the *dynamics group* but not as the *carrier field*. Which field is
forced for the carrier? Two demands from earlier rungs decide it (engines agree numpy==JAX==Torch==Julia):

| field | su2_generator_dim | scalars_commute | hosts su(2)? | composable? |
|-------|-------------------|-----------------|--------------|-------------|
| ℝ     | 1 (so(2))         | yes             | **no**       | yes         |
| ℂ     | 3 (su(2))         | yes             | yes          | yes         |
| ℍ     | 3 (Sp(1))         | **no**          | yes          | **no**      |

z3 **and** cvc5 both **UNSAT** that any non-ℂ field satisfies BOTH demands → **the carrier field is forced
to ℂ**. Two flipped controls, each isolating a negative: drop su(2)-hosting → **ℝ re-qualifies** (witness R
on both solvers) → Demand 1 kills ℝ; drop composability → **ℍ re-qualifies** (witness H on both) → Demand 2
kills ℍ.

**VERDICT: the carrier scalar field is forced to ℂ** — uniquely hosts the forced su(2) dynamics AND has
composable scalars for bipartite tensor products.
**TWO NEGATIVES kept:** (1) ℝ cannot host su(2) (only so(2), dim 1). (2) ℍ scalars noncommute → no
composite tensor product. 𝕆 is killed even harder (nonassociative → not a division-algebra carrier for
linear QM; the octonion cluster's standing result).

## Rung ladder (updated)
1. carrier bakeoff → ℂ **installed, not forced** (rebit passes weaker gate)
2. phase-closure → ℂ **forced** over rebit (continuous no-distinguishability fiber)
3. dynamics → **Sp(1)=SU(2)=unit ℍ forced as the dynamics group**; ℍ **not** the carrier (negative)
4. carrier field → **ℂ forced as the carrier field** (unique: hosts su(2) ∧ composable); ℝ and ℍ each
   killed by a distinct demand (two negatives)

The carrier question is now closed on both faces: the field is ℂ (rung 4), the dynamics group is unit-ℍ
(rung 3). Next open rung: composite/multipartite structure — does the tensor-product rung force a minimum
number of systems (the 3-qubit floor from a *forcing* demand rather than the tomography count)?
