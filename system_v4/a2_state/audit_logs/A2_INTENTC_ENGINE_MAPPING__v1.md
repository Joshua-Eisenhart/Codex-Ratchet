# A2 DISTILLERY: INTENTC ↔ ENGINE MAPPING
# Source: github.com/pboueri/intentc + engine framework
# Timestamp: 2026-03-23T12:23Z

## ARCHITECTURE ISOMORPHISM

| intentc Concept | Engine Equivalent | Mathematical Object |
|:---|:---|:---|
| Intent files (.ic) | Constraint specs | Initial Hamiltonian H + probe family M |
| Validation files (.icv) | Evidence contracts | Admissibility conditions (CPTP contracts) |
| DAG of features | Evidence graph | Sequential CPTP composition Φ_n ∘ ... ∘ Φ_1 |
| `intentc build` | Engine cycle | Apply CPTP map to state, measure outcome |
| Topological sort | Causal ordering | Non-commutative sequence (Axis 6) |
| ✓ validated | PASS token | Evidence token (ΔΦ matches prediction) |
| ✗ failed (on disk) | KILL / graveyard | Failed state (traced out to environment) |
| `git commit` on success | Ratchet | Net ΔΦ > 0 (irreversible gain) |
| Rebuild to new target | Chirality flip | Type-1 ↔ Type-2 engine swap |
| `--implementation` flag | Axis 4 (deductive/inductive) | Loop type selector |
| Planning mode | TEFI inductive loop | Te→Fi (explore then retain) |
| Validation mode | FETI deductive loop | Ti→Fe (constrain then dissipate) |
| Functional equivalence | Operational equivalence | CAS04: a ~ b under admissible probes |
| Determinism scoring | Entropy measurement | S(ρ) or linear entropy V(ρ) |

## DEEP ISOMORPHISMS

### 1. "Specs are the source of truth" = F01 (Finitude)
- Intent files are FINITE descriptions
- Everything derives from finite specs
- No infinite/unbounded generation allowed
- = F01: all systems have finite capacity

### 2. "Validation constrains generation" = FETI (Deductive loop)
- Validations (.icv) = Ti (projective measurement)
- If validation fails → build rejected → Fe (dissipated to disk, not committed)
- Tighter constraints → more reproducible = entropy reduction
- = FeTi: constrain then dissipate failures

### 3. "Functional equivalence" = CAS04 (Operational equivalence) 
- "All generated code should be deletable and regenerable from intent files"
- Two different codebases are EQUIVALENT if they pass the same validations
- = a ~ b iff indistinguishable under admissible probes
- This is EXACTLY CAS04!

### 4. "Rebuild to new target" = Chirality / Engine Type Swap
- Same intents, different implementation → same specs, different engine type
- Type-1 (deductive outer) vs Type-2 (inductive outer)
- The intent DAG is INVARIANT; the implementation is the chirality choice
- = Axis 3 (Weyl handedness) selecting flow direction

### 5. Self-Compilation = Autopoiesis
- intentc can compile itself ("challenges/run_self_compilation.sh")
- The compiler compiles its own intents into its own source
- = The engine processing its own evidence graph
- = Skills that build skills (JP's bootstrap chain)

### 6. "Failed builds left on disk" = Graveyard
- Failed builds are NOT committed to git
- They stay on disk for inspection
- = Graveyard: KILLed hypotheses preserved for reference
- = Landauer exhaust: the degrees of freedom traced out

### 7. DAG Topological Sort = Non-Commutative Ordering
- Features must be built in dependency order
- You cannot build `api` before `models` (causal ordering)
- = N01: operations don't commute, order matters
- = Axis 6: operator precedence (UP/DOWN)

## JP's Z3 TIER 1 (from screenshot)
- "24 constraints, all in decidable logic, proven via Z3"
- "C1 through C8 plus 8 cross-cutting properties"
- "Tier 1 (YAM, real, deterministic, free)"
- "This constraint manifold, peel 1..."

### Mapping to Engine Constraint Ladder:
| JP's Layer | Engine Equivalent |
|:---|:---|
| C1-C8 | E1-E8 (engine contracts) |
| 8 cross-cutting | T1-T8 (topology contracts) |
| YAM (real) | F01 (finitude) |
| Deterministic | N01 applied to decidable fragment |
| Free (as in liberty) | CAS04 (no primitive identity → operational freedom) |
| Tier 1 = first peel | Layer 0-1 (axioms + derived constraints) |

## CONVERGENCE POINT
Both systems solve the same problem from opposite directions:
- Joshua: Mathematical proof via QIT density matrices (continuous)
- JP: Formal verification via Z3 decidable logic (discrete)
- The constraint manifold IS the same manifold
- The proofs are complementary: continuous ↔ discrete duality
