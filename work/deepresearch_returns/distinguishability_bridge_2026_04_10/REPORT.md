# Distinguishability Bridge Audit

Repo anchor commit: `c480a4a6154a181d3ff9ec1e8dbf679fcc7b3631`

Scope: repo-anchored bridge built from:
- `new docs/references/DISTINGUISHABILITY_FORMAL_REFERENCE.md`
- `new docs/CONSTRAINT_ON_DISTINGUISHABILITY_FULL_MATH.md`
- `new docs/references/INFORMATION_GEOMETRY_REFERENCE.md`
- `new docs/references/PROCESS_PHILOSOPHY_AND_RELATIONAL_PHYSICS_REFERENCE.md`

This audit separates technical support from philosophical support, and it does not treat operational equivalence as ontology.

## 1. What the repo already states well

- The repo already has a strong operational spine: distinguishability is defined by admissible probes, and operational equivalence is stated as equality of outcome statistics across a measurement family.
- The quotient construction `S/~_M` is a good formal device for an **effective state space at probe resolution `M`**.
- The information-geometry doc correctly centers local distinguishability rather than parameter distance, and it already flags the classical/quantum split: classical Fisher-Rao uniqueness versus quantum monotone-metric non-uniqueness.
- The full-math doc makes two important constraints explicit and usable: finitude of admissible carriers/probes and load-bearing noncommutation of composition order.
- The repo is already close to a good bridge between distinguishability and context dependence because it uses probe families, quotienting, and ordered composition instead of vague substance language.
- The process/relational reference is useful as interpretation background, provided it stays in the interpretation lane and is not used as theorem support.

## 2. What concepts need better sourcing

- The operational meaning of trace distance, fidelity bounds, and one-shot discrimination should be attached to theorem-level sources wherever those claims are used.
- The statement that a density matrix stands for many ensemble decompositions needs the exact HJW source so the repo does not slide from operational equivalence into ontology.
- The move from operational equivalence to contextuality needs the exact Spekkens bridge: operational equivalences constrain ontological representations in noncontextual models.
- The move from local contexts to failure of a global description needs explicit sheaf/topos sourcing, not just high-level relational language.
- The information-geometry claims about Čencov and Petz need exact theorem-level citations at the point of use.
- The use of Blackwell order, data-processing monotonicity, and coarse-graining should be sourced where they are treated as load-bearing bridge components.
- Entropy-increase language needs qualification. Coarse-graining can increase entropy, but not every physical channel does so in the unrestricted sense.
- The claim that there are exactly four structurally distinct one-parameter CPTP semigroups or that such a classification is forced by `su(2)` needs either a proof path or a status downgrade to repo-specific derivation-in-progress.

## 3. Best technical sources

- Carl W. Helstrom, *Quantum Detection and Estimation Theory* (1976): core source for binary quantum discrimination and the operational meaning of trace distance / Helstrom bound.
- Christopher A. Fuchs and Jeroen van de Graaf, "Cryptographic Distinguishability Measures for Quantum-Mechanical States" (1999): exact fidelity / trace-distance inequalities.
- Lane P. Hughston, Richard Jozsa, and William K. Wootters, "A Complete Classification of Quantum Ensembles Having a Given Density Matrix" (1993): exact ensemble non-uniqueness result for fixed density matrix.
- Robert W. Spekkens, "Contextuality for Preparations, Transformations, and Unsharp Measurements" (2005): canonical operational-equivalence to generalized-contextuality bridge.
- Nikolai N. Čencov, *Statistical Decision Rules and Optimal Inference* (1982): theorem source for classical Fisher-Rao uniqueness under sufficient statistics / Markov morphisms.
- Dénes Petz, "Monotone metrics on matrix spaces" (1996): theorem source for the quantum family of monotone metrics.
- Samson Abramsky and Adam Brandenburger, "The Sheaf-Theoretic Structure of Non-Locality and Contextuality" (2011): canonical source for contextuality as obstruction to a global section.
- Chris Heunen, N. P. Landsman, and Bas Spitters, "A topos for algebraic quantum theory" (2009): clean source for context-posets of commutative subalgebras and topos-style dependence on context.
- Jeremy Butterfield and Chris Isham, the "Topos Perspective on the Kochen-Specker Theorem" papers: useful when the repo wants to speak in terms of context-indexed valuations and lack of global valuation.
- David Mermin, "Simple Unified Form for the Major No-Hidden-Variables Theorems" (1990), and A. A. Klyachko et al., "Simple Test for Hidden Variables in Spin-1 Systems" (2008): exact witness sources if contextuality examples are moved from code into docs.
- Vittorio Gorini, Andrzej Kossakowski, E. C. G. Sudarshan (1976), and Göran Lindblad (1976): theorem sources if the semigroup classification remains central.

## 4. Best interpretation/support sources

These are support sources for interpretation and framing, not theorem sources.

- Carlo Rovelli, "Relational Quantum Mechanics" (1996), plus the Stanford Encyclopedia entry on Relational Quantum Mechanics: useful if the repo wants a disciplined relational reading of state-as-relative-description.
- Stanford Encyclopedia entry on Structural Realism: useful for structure-first language, especially when the repo wants support for relation- or structure-heavy wording without overclaiming.
- Stanford Encyclopedia entry on Process Philosophy: useful only as cautious philosophical background when discussing process-first or anti-substance framing.
- David Deutsch and Chiara Marletto on constructor theory of information: useful support when the repo wants operation/task language rather than static-substance language.
- Wojciech Zurek on decoherence / Quantum Darwinism: useful support when the repo wants a physically grounded emergence story for effective objectivity under restricted access.
- Andreas Döring / C. J. Isham reviews, and Janotta-style overview material on topos approaches: useful as interpretation support when the repo wants to explain what context-dependent valuation language is doing.

## 5. Best critique sources

- Michela Massimi-style and Stanford Encyclopedia discussions of structural realism objections: useful for guarding against "relations all the way down" overreach.
- Davide Romano Oldofredi and Cristian López on the Harrigan-Spekkens taxonomy and Einstein: useful for preventing sloppy inferences from operational indistinguishability to psi-epistemic ontology.
- Critical literature on Relational Quantum Mechanics and the measurement problem: useful for preventing the repo from treating relationality as a settled technical consequence rather than one interpretation among several.
- Review literature on the topos approach that highlights the cost of intuitionistic / multivalued truth conditions and the non-uniqueness of context choices: useful for preventing "topos proves ontology" talk.
- Review literature on contextuality as a resource: useful for preventing the repo from claiming that contextuality by itself explains all quantum advantage.
- Standard QIT cautions on entropy monotonicity: useful for preventing the repo from writing unrestricted "physical evolution always increases entropy" claims.

## 6. Clean vocabulary to use in repo docs

- operational equivalence
- probe-relative indistinguishability
- admissible probe family
- effective state space at probe resolution `M`
- operational state specification
- compatible measurement context
- commutative context
- context-indexed local valuation
- global section obstruction
- monotone under admissible channels
- theorem-supported
- interpretive support
- repo-specific derivation

## 7. Vocabulary to avoid

- "the quotient is the ontology"
- "the density matrix is reality"
- "operational equivalence proves ontology"
- "contextuality means observer-created reality"
- "topos proves relation-first ontology"
- "Fisher geometry is categorically forced" without the classical qualifier
- "entropy always increases under physical evolution" without conditions
- "exactly four semigroups are forced by su(2)" unless the repo supplies the proof and hypotheses
- "relations all the way down" in technical docs
- "observer-dependent reality" unless the passage is explicitly marked as interpretive

## 8. Top 5 exact doc-strengthening opportunities

1. In `new docs/CONSTRAINT_ON_DISTINGUISHABILITY_FULL_MATH.md`, replace:
   - `The quotient Q = S/~_M is the ontology at resolution M.`
   with:
   - `The quotient Q = S/~_M is the operational state space at probe resolution M. Any ontological reading requires additional assumptions beyond operational equivalence.`

2. In `new docs/references/DISTINGUISHABILITY_FORMAL_REFERENCE.md`, replace the strongest density-matrix identity language with HJW-grounded wording:
   - current posture: density matrix as ontology / quotient in a strong sense
   - stronger doc posture: a density matrix specifies the operational state common to all ensembles that generate the same measurement statistics; HJW is the exact theorem for ensemble non-uniqueness.

3. Add a new reference doc such as `new docs/references/CONTEXTUALITY_TOPOS_BRIDGE_REFERENCE.md` that explicitly links:
   - operational equivalence of procedures (Spekkens)
   - compatible measurement contexts
   - contextuality as failure of a global assignment (Abramsky-Brandenburger)
   - topos contexts as commutative subalgebras / context-posets (Butterfield-Isham; Heunen-Landsman-Spitters)
   This is the cleanest way to bridge contextuality and topos-style context dependence without metaphysical drift.

4. In `new docs/references/INFORMATION_GEOMETRY_REFERENCE.md`, tighten the theorem language:
   - keep the strong classical claim for Čencov,
   - keep the quantum non-uniqueness claim for Petz,
   - but explicitly state that the uniqueness claim is classical and that the quantum case admits a family of monotone metrics.

5. In `new docs/references/PROCESS_PHILOSOPHY_AND_RELATIONAL_PHYSICS_REFERENCE.md`, add a hard interpretive fence near the top:
   - `This document provides philosophical and interpretive support only. It does not substitute for theorem-level sources on operational equivalence, distinguishability, contextuality, or topos/sheaf formalisms.`
   This one paragraph would prevent future drift from technical bridge to metaphysical manifesto.
