# ConstraintBox Complete Standalone Pack

**Version:** proposed `0.2.0`, 2026-07-25
**Promotion:** `promotion_allowed: false`
**Scope:** complete standalone handoff, not a patch or delta

ConstraintBox is a proposed branch-preserving finite constraint-path runtime.
It can run without LevOS, Codex-Ratchet, a simulation engine, or an LLM.  Those
systems attach through bounded adapters.

The persistent unit is not an LLM conversation.  It is a finite constrained
ensemble of candidate histories, projections, branches, evidence, and
unresolved obligations.  Agents may propose modifications to that ensemble.
Only the controller may execute capabilities, record evidence, prune or merge
branches, or emit an operational disposition.

## What is in this pack

| Surface | Included |
|---|---|
| Formal shared object | finite history ensemble, projections and fibres |
| Nominalist constraint rules | identity/equality/probability/metric are not implicit |
| Branch operations | preserve, park, earned prune and earned merge |
| Finite constraint solver | zero-dependency enumeration backend |
| SMT adapter | optional bounded Z3 profile; absence returns `UNKNOWN` |
| Numeric adapter | optional NumPy aggregate recomputation |
| Relative Ratchet | frozen probes, nonempty demand, verified nests, plural rivals |
| Agent boundary | proposals cannot contain commands, profiles, tolerances or verdicts |
| Worker controller | fixed source digest, argv, timeout and output binding |
| Evidence ledger | local hash-chain consistency with explicit trust ceiling |
| LevOS extraction map | what is reused, excluded or still aspirational |
| CR and Sim adapters | boundaries and acceptance contracts, not full engines |
| TLA+ model | proposed controller transition and invariants |
| Schemas | closed proposed contracts for objects, proposals, profiles and decisions |
| Tests | 40 executable unit/hostile tests plus estate acceptance |
| Simulation capability estate | four proposed, separately installable layers |
| Boot maintenance | version, source, witness and negative-control checks |

## Quick run

```bash
cd runtime
PYTHONPATH=src python3 -m unittest discover -s tests -v
PYTHONPATH=src python3 -m constraintbox demo
PYTHONPATH=src python3 -m constraintbox doctor
```

No installation is required for the core or enumerated finite solver.

## Load order

1. `STATUS_AND_AUTHORITY.md`
2. `../01_FOUNDATION/SHARED_FINITE_CONSTRAINT_PATH_OBJECT.md`
3. `../01_FOUNDATION/NOMINALIST_CR_ALIGNMENT.md`
4. `../02_ARCHITECTURE/SYSTEM_BOUNDARIES.md`
5. `../02_ARCHITECTURE/AGENT_CONTAINMENT_AND_OBJECT_ORCHESTRATION.md`
6. `../02_ARCHITECTURE/LEVOS_EXTRACTION.md`
7. `../03_EXECUTION/TOOLS_PROFILES_AND_RESOURCE_POLICY.md`
8. `../03_EXECUTION/TEST_AND_MAINTENANCE_PROGRAM.md`
9. `../03_EXECUTION/SIM_CAPABILITY_ESTATE.md`
10. `../03_EXECUTION/ESTATE_INSTALL_AND_BOOT.md`
11. `../06_MANIFEST/ESTATE_VERIFICATION.md`
12. `../05_AUDIT/KNOWN_LIMITS_AND_OPEN_WORK.md`

## One-sentence contract

> ConstraintBox preserves finite rival histories and allows execution,
> pruning, merging, and settlement only through controller-owned constraints
> and independently recorded evidence.
