# Wizard v4.3 full-run verdict — RPF "retrocausal inward compression" is NOT EARNED (2026-06-13)

```yaml
receipt_kind: wizard_full_verdict
pipeline: gate-v42 ok:True (preflight) -> 3 councils (all voices + premortem + grok-4.3 + gemini-3.1-pro) -> collapse-audit -> decisive falsifier executed
status: PARTIAL exit — genuine on two axes, NOT earned on the defining (retrocausal) axis
```

## The decisive falsifier (council question C), executed by the controller

A naive **forward sequential selector** (walk inward shells outer->inner by radius desc, same cross-shell argmax, with NO "inward/retrocausal" semantics) was run against `compression_map` on rpf_v1's actual inputs:

| scenario | compression_map | forward_seq | result |
|---|---|---|---|
| canonical | b3 | b3 | IDENTICAL |
| shell-reassignment | b0 | b0 | IDENTICAL |
| state-mutation | b3 | b3 | IDENTICAL |
| radius-reorder | b0 | b0 | IDENTICAL |

**IDENTICAL on all four.** `compression_map` IS outer->inner forward sequential selection. No active probe distinguishes "retrocausal inward compression" from forward sequential selection → the object NAME is not earned on this carrier.

## Honest three-axis verdict (surviving divergence preserved, per anti-collapse)

- **Field instantiation axis — GENUINE.** rpf_v0/v1 carry the 10 first-class fields as real shaped data (shell-keyed `future_continuations` LISTs, pairwise `compatibility_weights`, derived `present_survivor`, provenance `outward_record`). This genuinely exits the GROSS-proxy basin (carve-counts etc.). Confirmed by independent re-derivation.
- **Shell-ordering axis — GENUINE.** rpf_v1's survivor is order-sensitive: shell-reassignment moves it; the flat-union negative control stays inert and the baselines disagree (b3 vs b2) → not a relabeled flat-union. Confirmed.
- **Retrocausal/inward-semantics axis — NOT EARNED.** The INWARD/OUTWARD orientation, the shell radii, and the `1/(1+L1)` compatibility weight are builder-STIPULATED, not derived from any constraint C. The computation runs forward and is indistinguishable from forward sequential selection (above). "Retrocausal" is narrative, not a derived/constrained property.

## Council findings folded in

- **Collapse-audit:** moderate DECORATIVE SPLIT (8 voices made the same "orientation is a hardcoded label" move) — the observation is correct but over-counted; Pushback/Orwell recommended re-spawn with distinct constraints.
- **Popper found a real BUG (untracked, pre-commit):** rpf_v1's `state_mutation_trap` shallow-copies (`saved={k:dict(v)...}`) then mutates `b3.a += 5` in place, so the `finally` does NOT restore — `b3.a=6` PERSISTS in the written results JSON. rpf_v1 must NOT be committed until fixed.
- grok-4.3's extensional-equivalence falsifier was KILLED on the canonical instance (traversal b3 != flat b2); but the broader forward-selection falsifier (above) SURVIVES.

## Compiled next move (B) — what actually earns "retrocausal"

NOT more rpf machinery. To make the defining axis real:
1. Fix the rpf_v1 `b3.a=6` state-mutation contamination (deep-copy restore) before any commit.
2. Derive the `compatibility_weights` from the actual constraint families C (admissibility), not an arbitrary L1 proximity metric.
3. Adopt the rpf_v2_`irreversibility` orientation (derived from MEASURED fiber cardinality: many-to-one=INWARD, injective=OUTWARD) — this is a DERIVED directional asymmetry a forward selector does not compute, and is the candidate that could make the forward-selector control DIFFER.
4. PERMANENT acceptance gate: install the forward_sequential_selector as a standing control — the object is "retrocausal" only if some probe makes it DIFFER from forward selection. Until then, ceiling stays scratch_diagnostic and the name is held as target, not claim.

## Ceiling
scratch_diagnostic; promotion_allowed=false. rpf_v0 committed (32eafee26) honestly. rpf_v1/v2 UNTRACKED and must stay so until (1) the contamination bug is fixed and (2) "retrocausal" is either earned (probe differs from forward selection) or the name is dropped to "shell-ordered sequential selection field". No proxy promotion.
