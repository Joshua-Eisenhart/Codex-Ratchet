# Formal Methods / Witness Discipline Reference

Date: 2026-04-05
Status: Reference — exact-term support for admissibility, witnesses, and fail-closed checking

---

## Core idea

This reference supports the system’s admissibility grammar with standard formal-methods terms.

The system’s closest exact external support is not one field alone, but a cluster:
- model checking
- theorem proving
- proof-carrying code
- invariant checking
- Hoare logic
- separation logic
- CEGAR
- certificate / witness language

These traditions do not supply the system’s ontology. They supply disciplined acceptance/rejection machinery.

---

## Exact fit terms

### Model checking
- Checks whether a transition system satisfies a property.
- Produces counterexamples when a property fails.
- Good fit for fail-closed admission: if the property is violated, reject.
- Good fit for finite witness discipline: counterexamples are finite artifacts.

### Theorem proving
- Proves statements from axioms and inference rules.
- Good fit for admissibility when a claim must be justified before acceptance.
- Best when the proof object is machine-checkable.

### Proof-carrying code
- Code is accepted only when accompanied by a valid proof/certificate.
- Best exact fit for fail-closed checking.
- Best fit for the system’s acceptance gate: no certificate, no admission.

### Invariant checking
- Verifies that an invariant holds over a system or execution.
- Good fit for surface-style constraints: if a state leaves the admissible surface, reject it.

### Hoare logic
- Pairs preconditions and postconditions with proofs about programs.
- Good fit for admissibility as a proof obligation.

### Separation logic
- Strong fit for resource, ownership, and heap-structured invariants.
- Good fit if the system’s admissibility rules concern resource accounting or structural ownership.

### CEGAR
- Abstract, check, then refine if a counterexample is spurious.
- Good fit for iterative witness validation.
- Important caveat: a candidate counterexample is not automatically a true witness.

---

## How to map into system language

Use these exact translations where possible:
- admissibility gate -> proof obligation / acceptance condition
- witness -> proof object or counterexample trace, depending on context
- graveyard -> rejected counterexamples / invalid certificates archive
- fail-closed -> reject on missing or invalid proof/certificate
- finite witness discipline -> finite counterexample, finite proof object, finite trace
- admissible surface -> property set / invariant-preserving state space

---

## Mismatch notes

- “KILLED / SURVIVED” is not standard formal-methods terminology.
  - Use accepted / rejected, verified / refuted, certified / uncertified instead.
- “graveyard” is not standard formal-methods terminology.
  - Use rejected witness archive or counterexample log if precision matters.
- Formal methods usually separate proof objects from counterexamples.
  - If the system uses both, define them explicitly.

---

## Best exact fit summary

If you need one support cluster for admissibility and witness discipline, use:
1. proof-carrying code
2. model checking
3. invariant checking
4. theorem proving
5. CEGAR as the workflow around them

This is the cleanest external support for the system’s fail-closed grammar.
