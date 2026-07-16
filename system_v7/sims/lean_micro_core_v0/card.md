# LEAN MICRO-CORE v0 — Frozen Card

Status: `frozen-before-implementation`

## Identity and scope

- Lane: `system_v7/sims/lean_micro_core_v0/`
- Program priority: owner cross-view program, priority 4
- Execution kind: bounded formal proof/control lane
- Public status ceiling: `passes local rerun`
- Internal classification: `formal_scout`
- Promotion allowed: `false`
- Physics admission allowed: `false`
- Axis/bridge/manifold admission allowed: `false`
- Primary object: four small, exact Lean statements selected from the owner's ten foundational targets
- Lean carrier role: proof adapter for those exact statements only; it is not the larger foundational object and does not establish physical interpretation

## Toolchain contract

- Use `~/.elan/bin/lean` and `~/.elan/bin/lake`.
- Pin the lane to the Lean toolchain required by the read-only working reference `/Users/joshuaeisenhart/GitHub/physlib` (`leanprover/lean4:v4.31.0`).
- Prefer a lane-local Lake project with a path dependency on the existing physlib checkout so its already-fetched mathlib dependency can be reused.
- The physlib checkout is read-only for this task: copy nothing into it and make no edits there.
- If a compatible lane-local Lake project cannot use the existing dependency estate without modifying physlib or fetching unavailable infrastructure, prove targets 1–2 with core Lean and record targets 3–4 as blocked with the exact reason.

## Exact targets

### T1 — Probe indistinguishability equivalence

For finite state and probe-index types and a declared observation function, define two states to be probe-indistinguishable when every declared probe returns the same observation on them. Prove reflexivity, symmetry, and transitivity, and package the result as an `Equivalence` theorem. This theorem must use only Lean core; finiteness is a declared scope condition, not an extra mathematical premise used by the proof.

Pass rule: Lean accepts the theorem with no `sorry`, and `#print axioms` reports its exact axiom footprint.

Kill/block rule: any undeclared observational assumption, quotient claim, or physics interpretation exceeds scope.

### T2 — Probe-family refinement preorder

Define `fine` to refine `coarse` when indistinguishability under `fine` implies indistinguishability under `coarse`. Prove reflexivity and transitivity of this refinement relation (a preorder; antisymmetry is not claimed because differently presented probe families may induce the same indistinguishability relation).

Pass rule: Lean accepts the reflexivity/transitivity/preorder theorem(s) with no `sorry`, and `#print axioms` reports exact footprints.

Kill/block rule: claiming a partial order on syntactic probe-family presentations, or claiming that every refinement is strict, exceeds scope.

### T3 — Concrete 2x2 complex matrix associator control

Using mathlib `Matrix` over `Complex`, define explicit concrete `2 x 2` matrices and prove their associator vanishes:

`(A * B) * C - A * (B * C) = 0`.

The proof may use the general associativity instance, but the theorem statement must be about concrete matrices. This is the associative control required by the nonassociativity program; it does not prove or disprove any nonassociative target.

Pass rule: Lean accepts the concrete theorem with no `sorry`, and `#print axioms` reports its exact footprint.

Kill/block rule: unavailable compatible mathlib/Complex/Matrix infrastructure is recorded as blocked; do not replace the theorem with an unchecked computation or prose.

### T4 — Concrete Pauli commutator closure

Using concrete `2 x 2` complex matrices `sigmaX`, `sigmaY`, and `sigmaZ`, prove the three cyclic commutator relations under the convention `[A,B] = A*B - B*A`:

- `[sigmaX, sigmaY] = (2 * I) • sigmaZ`
- `[sigmaY, sigmaZ] = (2 * I) • sigmaX`
- `[sigmaZ, sigmaX] = (2 * I) • sigmaY`

where `I` is the complex imaginary unit and scalar multiplication is the matrix module action.

Pass rule: Lean accepts all three concrete equalities with no `sorry`, and `#print axioms` reports exact footprints.

Kill/block rule: unavailable compatible mathlib/Complex/Matrix infrastructure, an unresolved convention mismatch, or reliance on an unproved custom axiom is recorded as blocked with reason.

## Required artifacts

- `card.md` (this file, frozen before implementation)
- lane-local Lake project files
- one Lean source file per target
- `build_log.txt` containing verbatim fresh `lake env lean` and/or `lake build` output, including `#print axioms` output
- `results_v1.json` listing proved theorems, their reported axiom footprints, blocked items and reasons, commands, toolchain, and exact claim ceiling

## Acceptance and stop condition

Accept only theorem declarations checked by the pinned Lean toolchain in a fresh lane-local command. Record failures rather than weakening a target silently. After the card, sources, build log, and `results_v1.json` are frozen and audited for exact scope, stop the lane. No queue promotion, physics admission, coupling claim, file movement, deletion, commit, or push is authorized.
