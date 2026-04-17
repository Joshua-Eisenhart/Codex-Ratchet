---
title: Current Formal Methods Core
created: 2026-04-07
updated: 2026-04-16
type: summary
framing: current
tags: [reference, research, system, validation, formal]
sources:
  - raw/articles/new-docs/references/FORMAL_METHODS_AND_WITNESS_DISCIPLINE_REFERENCE.md
  - raw/articles/new-docs/references/DISTINGUISHABILITY_FORMAL_REFERENCE.md
  - raw/articles/new-docs/references/CONSTRAINT_ON_DISTINGUISHABILITY_FULL_MATH.md
  - raw/articles/new-docs/SYSTEM_ARCHITECTURE_REFERENCE.md
  - raw/articles/new-docs/references/FORMAL_METHODS_AND_WITNESS_DISCIPLINE_REFERENCE.md
---

# Current Formal Methods Core

## Overview
This page summarizes the current formal-methods policy lane: constraint-first reasoning, witness discipline, fail-closed admission, and the distinction between admissible and inadmissible states. These pages collectively describe what the active formal-methods surfaces count as evidence, what they admit, and what they reject.

## The witness discipline
The formal-methods lane requires checkable witnesses for every claim. This comes from formal methods: model checking produces counterexamples, SAT/SMT produces satisfying assignments, proof-carrying code carries explicit certificates. In this wiki's current policy framing, every simulation result, invariant claim, and admitted state should carry a traceable witness that can be independently verified.

Core requirements:
1. **Claim tables:** assertions should enter as structured claims with evidence, bounded criteria, and source trace
2. **Fail-closed admission:** nothing should pass unless explicitly witnessed. Absence of evidence is evidence of absence in this regime
3. **Batch worker separation:** LLMs that produce claims are separated from LLMs that verify claims. The controller contract ([[llm-controller-contract]]) describes this separation
4. **Public status discipline:** broad summaries should route through the controller docs' four public labels `exists`, `runs`, `passes local rerun`, and `canonical by process`, with that last term treated as the strongest controller-admission label rather than a blanket whole-wiki canon claim

## Constraint-first reasoning
This lane reasons from constraints upward, not from models downward. The constraint surface M(C) is defined by distinguishability conditions ([[constraint-on-distinguishability]]), not by any particular coordinate system or model. This matches the formal methods tradition: safety properties constrain what behaviors are admissible, then implementations are constructed to satisfy those constraints.

## 2026-04-14 bounded sim-tranche note
Recent artifact-side additions make the formal-methods lane less abstract than it was earlier in the week. A bounded tranche routed at [[sim-tranche-2026-04-14-axioms-tools-gerbes-motives]] is relevant here because:
- F01 is represented there by explicit micro-sim artifacts for finite state set, finite measurement set, finite Hilbert dimension, and quotient well-definedness
- N01 is represented there by explicit micro-sim artifacts for generic noncommutation, composition-order distinction, identity via indistinguishability, indiscernibility-implies-identity, and Pauli algebra closure
- deeper tool-native claim packets are also present there for z3, sympy, rustworkx, PyG, GUDHI, and torch rather than only shallow capability language

In this maintenance pass those artifacts should still be read as `exists` unless a fresh rerun is cited. The value of the tranche is that the root constraints and tool-pressure claims are now more executable and more enumerable in the published wiki.

Key formal structures:
- **Bisimulation:** captures interaction-level indistinguishability -- two states are bisimilar if no observation distinguishes them. The system's distinguishability constraint is the quantum-information analog
- **Refinement:** safety-preserving narrowing of the state space. Each layer of the system refines the admissible set
- **Invariants:** properties preserved across all transitions. The system's fence system ([[ladders-fences-admission-reference]]) is an invariant-checking layer
- **Trace equivalence and dependency:** when order-sensitive actions cannot be swapped, the distinction should remain explicit. [[concurrency-and-trace-theory-reference]] supplies the CS-native language for this boundary.

## Fail-closed design
This page treats the architecture as deny-by-default:
- No claim should enter the public record without explicit witness
- No tool result should be treated as verified without independent confirmation
- No LLM output should be trusted without cross-check from a separate narrative thread
- Status labels enforce explicit accountability: a claim should remain explicitly open, narrower-status, or unwitnessed unless the stronger label is directly earned

Important correction:
- fail-closed does not mean binary overclaim
- it does not collapse `open`, `exists`, `runs`, `passes local rerun`, `survived`, and `canonical by process` into one confirmation bucket
- it means no upward inference from a weaker status to a stronger one
- it also means killed/negative evidence and unresolved branches should remain visible instead of being smoothed away by summary prose

This matches the formal-methods tradition of proof-carrying code (Necula & Lee, 1998): the code carries its own proof of safety, and the verifier checks the proof, not the code. The system's claim tables are the current proof-carrying analog.

## External grounding
- Model checking (Clarke, Emerson, Sistla; 1980s): systematic exploration of state space against temporal logic specifications
- SAT/SMT solving: Davis-Putnam (1960), DPLL, modern SMT (Z3, CVC5) -- constraint satisfaction with theory reasoning
- CEGAR (Clarke et al., 2000): Counterexample-Guided Abstraction Refinement -- iteratively refine abstractions using spurious counterexamples
- Proof-carrying code (Necula & Lee, 1998): code producer supplies safety proof, consumer verifies it
- Bisimulation (Milner, Park, 1980s): observational equivalence in concurrent systems
- Trace theory and refinement (Hoare, Lamport): specification via pre/post conditions and invariants

## Core pages
- [[formal-methods-and-witness-discipline]] -- detailed reference on each formal method
- [[tool-capability-sim-program]] -- bounded tool-lego probes for discovering real capability envelopes
- [[networkx-graph-structure-reference]] -- canonical graph object layer
- [[pydantic-typed-schema-reference]] -- typed contract/schema layer
- [[jsonschema-artifact-validation-reference]] -- artifact structure validation layer
- [[pytest-tiered-gate-reference]] -- executable tiered gates
- [[hypothesis-property-based-testing-reference]] -- property-based invariant pressure
- [[witness-recorder-and-trace-reference]] -- append-only evidence trace layer
- [[lean4-proof-assistant-reference]] -- planned theorem-prover layer
- [[tlaps-temporal-proof-reference]] -- planned temporal proof layer
- [[z3-smt-solver-reference]] -- primary UNSAT/SAT admissibility proof surface
- [[cvc5-smt-and-sygus-reference]] -- second solver and synthesis pressure
- [[sympy-symbolic-math-reference]] -- symbolic derivation layer between numerics and SMT
- [[sim-tranche-2026-04-14-axioms-tools-gerbes-motives]] -- bounded artifact summary for F01/N01 micro-sims, deep tool-native packets, gerbe/G-tower families, and motives packet routing
- [[constraint-on-distinguishability]] -- the distinguishability constraint definition
- [[constraint-on-distinguishability-full-math]] -- full mathematical treatment
- [[distinguishability-formal-reference]] -- trace distance, fidelity, data processing, Blackwell order
- [[codex-audit-controller-contract]] -- controller-level enforcement
- [[system-architecture-reference]] -- architecture rules and fail-closed admission
- [[llm-controller-contract]] -- claim tables and status labels

## Related pages
- [[current-research-overlays]]
- [[docs-alignment-catalog]]
- [[docs-framing-map]]
- [[ladders-fences-admission-reference]]
- [[llm-bias-and-failure-modes-reference]]
