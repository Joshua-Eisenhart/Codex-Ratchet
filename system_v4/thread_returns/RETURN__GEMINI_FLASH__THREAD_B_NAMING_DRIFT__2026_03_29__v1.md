# Thread B Naming Drift Report

**Date:** 2026-03-29
**Scope:** Strict identification of naming drift, token drift, capitalization drift, and duplicated literal families across Thread B lexeme documents.
**Policy:** No doctrine changes made. Identification only.

## 1. Naming Drift & Token Drift

Identified instances where the mathematical object/lexeme name drifts from the branch/term classification name:

- **CPTP Family Drift:** 
  - Lexeme: `CPTP_channel` (QIT-basin object)
  - Term: `proper_cptp_branch` (TERM_PERMITTED classification)
  *(Drift between naming the object and naming the branch)*

- **Unitary Family Drift:** 
  - Lexeme: `Unitary_commutator` (QIT-basin object generator)
  - Term: `unitary_branch` (TERM_PERMITTED classification)
  *(Drift between naming the generator and naming the branch)*

- **Loop Family Drift:** 
  - Lexeme: `horizontal_lift_loop` (REALIZATION_ADMITTED favored geometry)
  - Terms: `fiber_loop`, `base_loop` (TERM_PERMITTED)
  *(Drift between specific geometric realization and the broader admitted term)*

- **Cut/Bridge vs Signed Functional Drift:**
  - Lexeme: `signed_cut_functional` (Tier 4)
  - Terms/Labels: `shell_interior_boundary_cut`, `xi_ref` (QUARANTINED cut families)
  *(Drift between functional class and the targeted cut doctrine instances)*

## 2. Capitalization Drift

Identified instances of capitalization inconsistencies among literals:

- **Non-commutativity:**
  - `Non_commutativity` (capital N)
  - `noncommutative_composition` (lowercase n)
  - `non_commutativity` (lowercase n)
  *(The capitalization is inconsistent across admissions lists and checking maps)*

## 3. Duplicated Literal Families

Families where the naming stems have duplicated extensions competing in the same conceptual space:

- **Coherent Information Family:**
  - `coherent_information` (TERM_PERMITTED) — unsigned/base term token
  - `coherent_information_relation` (LEXEME_ADMITTED_WITH_FENCE) — specific math relation/identity lexeme
  - `coherent_information_axis0` (QUARANTINED) — locked namespace attempt
  *(Family duplication creates "soft shadow" escalation risks)*

- **Geometry Overlay Labels vs Specific Lexemes:**
  - `Hopf_fiber` vs `Hopf`
  - `Weyl_sheet` vs `Weyl`
  *(The root labels are LABEL_PERMITTED, while the compound forms are actual geometry lexemes. Duplicated base literals invite cross-contamination.)*
