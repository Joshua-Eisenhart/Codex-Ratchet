# A1_REPAIR_OPERATOR_MAPPING v1

This specification defines the bounded operator space A1 may use for structured repair and anti-fake wiggle discipline.

This is a **non-kernel** artifact. B never sees it.
A0 may enforce operator usage requirements deterministically via admission checks and/or audit.

## 1) Operator enum (canonical)

`operator_id` values are defined exclusively in `specs/ENUM_REGISTRY_v1.md` under `operator_id (A1 repair / generation)`.
This document MUST NOT redefine the set.

## 2) Failure classes (inputs to repair)

A1 repair decisions may be triggered by deterministic evidence from:
- A0 admission failures (compiler-level)
- B reject/park outcomes (kernel-level; taxonomy is bootpack-defined)
- SIM outcomes (`SIM_EVIDENCE v1`, including `KILL_SIGNAL`)

Transport-level ZIP_PROTOCOL_v2 reject tags MUST NOT trigger A1 repair. Transport failures are handled at the sender/validator boundary.

## 3) Mapping: failure class → allowed operator set (bounded)

The mappings below are *allowlists* of operator_ids A1 may use when responding to a given failure class.

### SIM-driven failures
- Presence of `KILL_SIGNAL` in SIM_EVIDENCE → { `OP_NEG_SIM_EXPAND`, `OP_REORDER_DEPENDENCIES`, `OP_INJECT_PROBE` }
- Negative SIM failure without kill (implementation-defined) → { `OP_NEG_SIM_EXPAND`, `OP_INJECT_PROBE` }

### Kernel/compiler-style failures (generic)
NOTE: concrete B reject tag taxonomy is bootpack-defined. The mapping below is generic and must be refined to actual tags without inventing new kernel primitives.

- Dependency / ordering failure → { `OP_REORDER_DEPENDENCIES`, `OP_INJECT_PROBE` }
- Unknown token / lexeme failure → { `OP_MUTATE_LEXEME`, `OP_INJECT_PROBE` }
- Unsupported spec_kind failure → { `OP_A1_GENERATED` }  (forces regeneration under bounded schema)
- Duplicate id failure → { `OP_MUTATE_LEXEME` }
- Evidence binding failure → { `OP_BIND_SIM`, `OP_NEG_SIM_EXPAND` }

## 4) Deterministic exhaustion rule

For a given failure class in a given cycle:

1) A1 MUST choose one operator_id from the allowed set and record it in the affected proposal(s).
2) If the chosen operator_id fails to yield an admissible candidate under A0 checks, A1 may try another operator_id from the same allowed set.
3) Escalation to A2 is permitted only after all operators in the allowed set have been attempted (operator exhaustion).
   Escalation is advisory only: it must be represented as a request/notice, and A2 is manual-triggered.
   No automatic A2 invocation is permitted.
4) Operator selection may be nondeterministic internally, but exported artifacts MUST be deterministic and fully audited (A1_STRATEGY self_audit).

## 5) Anti-fake operator constraint (deterministic)

If a repair is triggered and `operator_id == OP_MUTATE_LEXEME`, the proposal MUST also change at least one of:
- `spec_kind`
- `requires`
- a `fields` entry
- an `asserts` entry

Otherwise the repair is considered fake wiggle and MUST fail A0 admission deterministically.
