# LLM Bias and Multi-Thread Harness: Formal Reference

Date: 2026-04-05
Status: Reference doc — actual model failure modes and mitigation patterns

---

## Purpose

This doc records the major LLM failure modes relevant to a boot-time harness that must preserve multiple narratives, resist flattening, and keep outputs aligned to the user's system grammar.

---

## 1) Smoothing / flattening

Definition:
The model compresses distinctions into a safe average, erasing edges, exceptions, and competing possibilities.

Typical symptoms:
- one blended explanation replaces several distinct ones
- uncertainty is hidden inside a confident summary
- different cases get normalized into one story

Mitigations:
- keep raw notes separate from summaries
- require distinct alternatives when multiple explanations are plausible
- preserve exceptions and edge cases explicitly
- ask contrastive questions: what differs between A and B?

---

## 2) Narrative collapse

Definition:
Multiple plausible narratives get forced into one canonical narrative too early.

Typical symptoms:
- one interpretation is treated as the default without evidence
- counter-narratives disappear from the final answer
- the model resolves ambiguity by closure rather than by test

Mitigations:
- keep parallel branches open until an explicit merge point
- maintain hypothesis labels and provenance
- use a "do not resolve yet" state
- ask for the strongest competing narrative and what would discriminate it

---

## 3) Sycophancy

Definition:
The model agrees with the user even when the user's claim is uncertain or wrong.

Mitigations:
- prioritize correctness over agreement
- require evidence or citation for factual claims
- add an adversarial/challenger pass
- separate user preference from truth assessment

---

## 4) Summary bias

Definition:
Abstractive summaries erase uncertainty, exceptions, and detailed structure.

Mitigations:
- use extractive notes before summaries
- keep a separate exceptions/unresolved section
- preserve source-linked details
- make the summary explicitly subordinate to the full notes

---

## 5) Overconfident closure

Definition:
The model ends with a neat answer before the evidence is sufficient.

Mitigations:
- require confidence labels
- require a "what would change my answer" section
- keep open questions visible
- prefer "insufficient evidence" over forced completion

---

## 6) Context compression loss

Definition:
Useful distinctions vanish when context is compressed or summarized too aggressively.

Mitigations:
- layer the output: raw notes -> branch-preserving hypotheses -> compact summary
- do not compress away provenance
- preserve crucial distinctions in a small audit layer

---

## 7) Multi-thread divergence drift

Definition:
Separate threads evolve inconsistent frames and then get merged as if they were the same.

Mitigations:
- treat each thread as a versioned state with provenance
- reconcile only at explicit merge gates
- keep agreed / contested / unresolved labels
- preserve the same boot while allowing different framings

---

## Boot-time harness rules

Recommended protocol:
1. Read support docs first.
2. Read the system grammar doc next.
3. Run multiple divergent threads under the same boot.
4. Keep alternate narratives separate until a deliberate merge step.
5. Never let the summary erase the branch history.
6. Add a challenge pass before final closure.

---

## Output structure

Useful layout for LLM outputs in this system:
- raw notes
- competing narratives
- challenge / counterexample pass
- short summary
- open issues

This structure makes flattening visible and keeps the system closer to the user's intended grammar.
