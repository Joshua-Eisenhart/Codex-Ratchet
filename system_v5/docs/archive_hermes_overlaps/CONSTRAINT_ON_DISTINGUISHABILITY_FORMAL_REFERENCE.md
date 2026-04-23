# Constraint on Distinguishability: Formal Reference

Date: 2026-04-05
Status: Reference doc — actual formal concepts, not the system's interpretation

---

## Core idea

This doc collects existing formal concepts that express a limit on what can be told apart under a restricted family of observations, measurements, or processes.

The user phrase "constraint on distinguishability" is not a standard single canonical term, but the underlying structure is already formalized in several literatures.

---

## 1) Indistinguishability relation / observational equivalence

Definition:
Two states, objects, or configurations are indistinguishable if every admissible observation gives the same outcome on them.

Typical forms:
- x ~ y iff all allowed observables agree on x and y
- quotienting by the relation gives equivalence classes of observationally identical items

Best use:
- generic support for probe-relative identity
- exact fit when your system cares about what survives all allowed tests

Mismatch:
- does not quantify degrees of difference
- does not by itself describe dynamics

---

## 2) Operational equivalence

Definition:
Two preparations, processes, or states are operationally equivalent if no allowed experiment distinguishes them.

Best use:
- physics and information-processing settings
- ideal when the system is framed in terms of admissible probes

Mismatch:
- depends on a chosen experimental/measurement family

---

## 3) Coarse-graining

Definition:
A map or partition that collapses fine-grained distinctions into fewer observed classes.

Best use:
- formalization of lost resolution
- explains how constraints reduce distinguishability

Mismatch:
- coarse-graining is not itself a metric or equivalence relation

---

## 4) Pseudometric

Definition:
A distance-like function d(x,y) satisfying symmetry, triangle inequality, and d(x,x)=0, but possibly d(x,y)=0 for x != y.

Best use:
- quantitative but constraint-friendly distinguishability
- useful when different states can still be collapsed by the observer family

Mismatch:
- not the same as strict identity

---

## 5) Trace distance

Definition:
For quantum states ρ and σ,
D(ρ,σ) = 1/2 ||ρ - σ||_1.

Operational meaning:
- gives the optimal distinguishability advantage in binary state discrimination

Best use:
- primary quantitative notion in quantum information
- exact operational support for distinguishability under measurement

Mismatch:
- only directly applies to quantum states

---

## 6) Helstrom bound

Definition:
The optimal minimum-error probability for distinguishing two quantum states.

Best use:
- direct operational discrimination limit
- useful if the system needs a hard discrimination bound

Mismatch:
- binary discrimination only in the standard form

---

## 7) Data processing inequality

Definition:
Applying an allowed channel/process cannot increase distinguishability or information divergence.

Examples:
- total variation cannot increase under a channel
- relative entropy cannot increase under a channel
- trace distance is monotone under CPTP maps

Best use:
- strongest general formal statement for a constraint on distinguishability
- explains why admissible processing can only lose or preserve distinctions

Mismatch:
- theorem about monotonicity, not a state-space relation by itself

---

## 8) Blackwell order

Definition:
One experiment is more informative than another if the second can be obtained from the first by garbling; equivalently, the first is better for every decision problem.

Best use:
- comparing probe families by how much distinguishability they preserve

Mismatch:
- about experiments/information structures, not object identity directly

---

## 9) Superselection rules

Definition:
Restrictions on the observable algebra that forbid certain coherent superpositions or transitions between sectors.

Best use:
- physics-specific constraint on what distinctions are physically meaningful

Mismatch:
- narrow and theory-specific

---

## Best-fit mapping for the user's system

Most useful formal support terms:
- operational equivalence
- indistinguishability relation
- coarse-graining
- data processing inequality
- trace distance
- Helstrom bound
- Blackwell order

If the system is quantum-adjacent:
- trace distance + Helstrom bound + data processing inequality are the best core trio

If the system is probe-family / rule-family based:
- operational equivalence + indistinguishability relation + coarse-graining are the best core trio

If the system is comparing what different probe sets can preserve:
- Blackwell order is highly relevant

---

## Translation rule

Use existing formal terms directly.
Do not invent compound labels when the literature already has a clean term.
If a new compound is needed, mark it as provisional and separate it from the reference vocabulary.
