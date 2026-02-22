# Evidence + Sims + Negative Sims (System Spec Pack v2)
Status: DRAFT / NONCANON
Date: 2026-02-20

## Why Sims Are Mandatory (structural)
- B eliminates/adjudicates by staged fences, but cannot validate behavior.
- SIM provides dynamic execution evidence for admitted structures.

## Evidence Objects
- `SIM_SPEC` (SPEC_HYP kind)
  - declares a required evidence token
  - is admitted/parked/rejected by B like other specs
  - causes `EVIDENCE_PENDING[SIM_SPEC_ID] = {TOKEN}` until satisfied

- `SIM_EVIDENCE v1` (artifact container)
  - includes one or more `EVIDENCE_SIGNAL <SIM_SPEC_ID> CORR <TOKEN>` lines
  - when ingested, satisfies pending evidence and attaches tokens to the target spec

## Term Canonicality (evidence gate)
- `CANON_PERMIT` (SPEC_HYP kind)
  - links a term literal to a REQUIRED_EVIDENCE token in TERM_REGISTRY
- When SIM evidence arrives matching REQUIRED_EVIDENCE:
  - TERM_REGISTRY[term].STATE transitions to `CANONICAL_ALLOWED`

## Positive vs Negative Sims
- Positive sim: validates intended behavior for a candidate.
- Negative sim: an adversarial falsification test tied to a specific target and failure mode.

Negative sim requirements (normative):
- must name a target survivor/spec id
- must name a failure mode id (what is being attacked/falsified)
- must emit deterministic evidence token(s) for the attempted falsification
- must state expected outcome class:
  - `NEG_EXPECT_FAIL_TARGET` (target should fail under invalid/adversarial condition), or
  - `NEG_EXPECT_REJECT_ALTERNATIVE` (alternative should fail while target survives required invariants)

Negative sim is NOT:
- a random failed idea
- a generic crash
- a graveyard entry by itself

Relationship to graveyard:
- negative sims provide dynamic falsification evidence
- graveyard stores explicit rejected alternatives and rejection reasons
- both are required for "meaningful survivor" status

Minimum intended audit bar for any "meaningful survivor":
- at least 1 positive sim that runs and produces evidence
- at least 1 negative sim that runs and produces evidence
- at least 1 plausible alternative that failed and is recorded in graveyard

Tiering note:
- tier structure + promotion gates are defined in:
  - `system_v2/specs/system_spec_pack_v2/19_SIM_TIER_ARCHITECTURE.md`
  - `system_v2/specs/system_spec_pack_v2/20_SIM_PROMOTION_AND_MASTER_SIM.md`
