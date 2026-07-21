# Candidate manifold: ablation control, nesting/composition flattened (conditional, non-canonical)

Status: `exists` — an authored proposal, not executed code. This document is
one candidate among rivals in `system_v8/candidates/`. It is not canon and
does not admit anything. `promotion_allowed: false`,
`formal_admission_allowed: false`. Role: `ablation_control` — a deletion/
flatten control against `candidate_classical_bottomup.md`, per the
fuel-adequacy gate's slot definition
(`fuel_gate/fuel_adequacy_gate.py`, `SLOT_DESCRIPTIONS["ablation_control"]`).

**Honesty header (added by the human-facing wrapper, not by the generating
model):** the body below (from the `#` heading onward) is the verbatim
output of `deepseek-ai/deepseek-v4-pro`, called through the NVIDIA
`integrate.api.nvidia.com` chat-completions endpoint, given the digest of
`candidate_classical_bottomup.md` (first 6000 characters) plus an ablation
brief instructing it to flatten that candidate's Layer 1/Layer 2
nesting-and-composition structure, name what capability is lost, state a
testable prediction, and include probe/witness sections satisfying the
fuel-adequacy gate's executable-enough grep check. The full prompt is
recorded verbatim as this candidate's `prompt_lineage` in the provenance
manifest. The response was cut off mid-sentence by the requested
`max_tokens: 2000` cap (`finish_reason: "length"`) at the very end of its
closing discussion section (§7) — the substantive content (deletions
named, capability-loss analysis, witness/defeat condition, testable
prediction, probe) is complete; only the last closing sentence is missing
its final clause. This truncation is recorded honestly rather than
silently completed or re-run to look cleaner.

---

# ablation_control: flat probe-response relation (no composition, no nesting)

**Role:** `ablation_control`
**Project:** Codex-Ratchet, fuel-adequacy pool
**Status:** `exists` — control candidate, not a contender
**Target:** `candidate_classical_bottomup.md`
**Ablation performed:** Remove all index-nesting structure (Layer 1) and all path-closure structure (Layer 2); retain only the flat probe-response relation (Layer 0).

---

## 0. What this control is and why it exists

This is an **ablation control**, not a rival. It is deliberately, provably weaker than the candidate it ablates. Its sole purpose is to isolate what the nesting and composition machinery in `candidate_classical_bottomup.md` actually does, by building a carrier that has none of it and then naming exactly what is lost.

The base candidate's core claim is a three-layer structure:

- **Layer 0** — a flat probe-response incidence relation over a finite atom set.
- **Layer 1** — an indexed, ordered, branching family of Layer-0 relations connected by a step relation between indices (the nesting/composition apparatus).
- **Layer 2** — a persistent-distinction closure formed by intersecting over all admissible Layer-1 paths (composition as intersection-over-paths).

This ablation **deletes Layers 1 and 2 entirely**, leaving only Layer 0 standing alone. The result is a flat relation carrier with no index set, no step relation, no admissible-path structure, and no persistence claim whatsoever.

---

## 1. The carrier (post-ablation)

One carrier only: a **finite relation over a finite atom set**, read as a probe-context to response incidence map.

- **Atoms:** finite set (finitude preserved).
- **Probe contexts:** finite set, not ordered.
- **Response relation:** a set of tuples `(probe_context, response)` — no reflexivity, symmetry, transitivity, or single-valuedness assumed.
- **No index set.**
- **No step relation between indices.**
- **No notion of an admissible path through a branching family of relations.**
- **No closure operation over such paths.**

In the base candidate, this was Layer 0 only. Here it is everything. The carrier is identical to the base candidate's Layer 0 reading — `b0_unrestricted_relation` / `probe_response_incidence` — and nothing else.

---

## 2. What was deleted (explicit deletions)

### 2.1 Deletion of Layer 1: the index set and step relation

The base candidate attaches to every Layer-0 relation a **finite index set** and a **finite step relation** between indices, forming an ordered, branching family of Layer-0 snapshots.

**Deleted:**

- The index set itself.
- The step relation that connects indices.
- All admissible-path structure — there are no longer any paths to walk through the relational family, because there is no family.
- All branching (multiple admissible next-indices) and all ordering constraints (whether installed, forced, or idle).

**What this removes:** The carrier can no longer represent evolving relational structure under local rewrites — it has one static relation, no history of states, and no nondeterministic branching across possible relational configurations. The response to the base campaign's negative result against single-valued transition functions (cf. base candidate §6a) is entirely lost, because there is no transition function to make multi-valued.

### 2.2 Deletion of Layer 2: the persistent-distinction closure

The base candidate defines Layer 2 as a closure: the sub-relation of distinctions that survive **every admissible Layer-1 path**, computed by intersection over paths.

**Deleted:**

- The closure operation itself.
- Any notion of a distinction surviving a family of evolutions.
- Any notion of a bounded set of admissible paths over which to intersect.
- Any claim of permanence or persistence at all — replaced with nothing.

**What this removes:** The entire concept of a persistent distinction — a probe-response pair that holds invariant under all admissible transformations in the indexed family. Without an index family there are no paths; without paths there is nothing to intersect over. The flat relation has atomic distinctions, but no way to claim any of them persist beyond the single instantaneous snapshot.

---

## 3. Capability lost by this flattening

All the structural verbs of the base candidate are gone.

1. **No re-use over sequential structures:** The flat carrier cannot express that the relation changes under an admissible step, because there is no step and no "next" index. It is a single static snapshot.

2. **No branching families or nondeterminism:** There is no index family, so there is no branching of admissible configurations — the flattened carrier cannot support the base candidate's Layer-1 claim that the step relation between pages is multi-valued.

3. **No persistent distinctions:** Without paths, there is no admissible set of transformations across which to check invariance. Distinctions are instantaneous only. The flattened carrier has no way to claim that anything survives change, because it has no change to survive.

4. **No notion of seeded, controlled, dynamical composition over time-like indexing:** The base candidate's most important structural claim — that persistent distinctions are a compositional discipline of intersection over embedding — is entirely absent. The ablation cannot express grouping, layering, modular structure, or long-range invariance under rewriting.

5. **Loss of structured compositional recombination:** The ablation is a tuple set; the base candidate can compose by rewriting indices and intersecting families. The ablation cannot do that at all.

The **single biggest loss**: the flattening abolishes the concept that two distinctions can be **differently persistent** — that one may survive all paths and another may only survive some paths. Without paths, all distinctions are equally provisional; there is no gradient or hierarchy of permanence.

---

## 4. Witness / defeat condition: what the nested candidate can do that this one provably cannot

The nested candidate can, in principle, construct a finite carrier where:

1. A particular probe-response pair `(p, r)` is present in some but not all Layer-1 indices in the family.
2. A different pair `(p', r')` is present in **all** admissible indices connected by the step relation.
3. By Layer 2 closure, `(p', r')` is labelled *persistent* and `(p, r)` is not.

The flattened ablation has no index family and no closure operation. It can represent `(p, r)` and `(p', r')` as atomic distinctions within a single relation, but it **cannot distinguish them** on any durability criterion. It has precisely one relation state, so the difference between PRESENT_IN_ALL_STATES and PRESENT_IN_SOME_STATES is not expressible.

This is a **witness for the flattening**: any environment that can count steps, count configurations, or check invariance across state space can **see** which distinctions are persistent in the original candidate, but cannot see that in the ablation. The ablation must remain silent on anything that would require surfacing a distinction between *transient* and *enduring* structure.

---

## 5. Testable prediction

**Prediction:** Any test that operationalizes "distinguish between transient and persistent probe-response pairs under a family of admissible temporal configurations" will succeed (even in manual constraint check) for `candidate_classical_bottomup.md` and will **fail** for this ablation — because the ablated carrier lacks the vocabulary to express the family or the closure.

---

## 6. Probe / distinguishability test

A minimal executable probe for the difference:

1. **Fix** a finite atom set and a probe-response relation `R`.
2. **Create** an index family `I` over relations, measuring a step relation, using the minted Layer-1 rules in the base candidate.
3. **Identify** a pair `d` present in every index, and a pair `e` present in only some.
4. **Compute** Layer 2 closure of the base candidate — it flags `d` as persistent, `e` not.
5. **Feed** the same data (relation only) to the ablation — it contains `d` and `e` as equally present atoms. Ask: "which of `d`, `e` is persistent?" — the answer must be no path-family available, query unintelligible, cannot categorize.

The ablation **cannot pass** the probe; the base candidate **can**. If both could pass, the ablation that removed parenting and composition is irrelevant — and the hypothesized refusal to pass is the evidence that the original structure carried real, testable weight.

---

## 7. What this implies and does not assert

This control does not claim the base candidate is correct, nor that the base candidate's particular closure is the right one. It does not claim that being able to pass the probe means the carrier has acquired "consciousness" or "normative binding." It exists only to show that the thing the base candidate added — indexing over a step relation + intersection-closure over paths — has a measurable, local functional consequence detectable without importing any category beyond finite relations.

If the base candidate were exactly the same as this flat control, then its Layers 1 and 2 would be *invisible* — performative rather than structural. That would refute the reason for building them.

The ablation exists to guarantee that **isolation** is testable: to make visible the destructive fingerprint where removing

**[response truncated here by the requested max_tokens: 2000 cap; finish_reason: "length" — recorded honestly, not completed or re-run]**
