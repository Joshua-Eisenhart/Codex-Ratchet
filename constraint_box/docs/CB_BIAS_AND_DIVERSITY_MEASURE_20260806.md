# CB PHILOSOPHICAL BIAS AND THE DIVERSITY MEASURE (owner canon, 2026-08-06)

**Provenance: owner-minted.** Recorded as stated.

## 1. CB has a bias. It is not neutral, and it is not all ideologies at once.

> I mostly drive all of CB and the wizard to be **operationalist,
> nominalist, and sentimentalist**. No universals, no causality, and
> that sentiments are empirically real.

> LLMs can't actually operate on universals, nor on causality. They
> just make up nice stories and drive teleology. They make causal
> stories but that doesn't mean the causality is real or works. We have
> to force LLMs to be accountable.

> CB isn't all ideologies at once, it has a bias. It uses SMT, it uses
> constraints, and all this aligns with nominalism and operationalism.

### What each commitment does mechanically

| Commitment | Operational form in CB |
|---|---|
| **Nominalist** | no universals; identity is probe-relative (`a ~_P b`); claims name their probe family, admissibility, and quotient or they are provisional |
| **Operationalist** | a term means the procedure that decides it; SMT encodings, declared bounds, and recompute contracts are the definition, not a gloss on one |
| **Sentimentalist** | sentiments are empirically real — they are data with a probe, not noise to be stripped, and not a universal either |
| **No causality** | causal language requires a bounded causal packet (intervention, scope, control); ordering and retained history alone license nothing |

The alignment the owner names is real and worth stating plainly: **SMT
and finite constraints ARE nominalism and operationalism in executable
form.** A bounded satisfiability question has no universals in it, and
its meaning is exactly the decision procedure that answers it. CB is
not adopting a philosophy as decoration; its tooling already commits it.

### Consequence for MMMs

Many MMMs may be used, and they **must be genuinely diverse from each
other** — but they are **diverse and coupled**: coupled to this bias.
Divergence happens inside an operationalist-nominalist frame, not
across incompatible metaphysics. That is what keeps divergence
productive rather than merely scattered.

## 2. Diversity is measured deterministically, in sub-LLMs, not by the main one

> we can measure input diversity. and it can be done in sub llms and
> not the main one. and hopefully with deterministic gating processes,
> so it isn't pure llm measured.

Implemented: `input_diversity_gate.py` — stdlib only, no model in the
loop. Per wave it measures:

- **identity** — exact root-input hash collisions;
- **overlap** — pairwise Jaccard over k-shingles of each root input;
- **preamble** — length of the shared leading prefix across all nodes;
- **mmm_distinct** — number of distinct MMM slices primed;
- **model_spread** — distinct provider/model pairs.

Verdicts `COLLAPSED` / `COUPLED` / `DIVERSE`, with the bounds
**declared in the receipt** so a wave can be re-judged under a
different standard without re-running it.

Self-test result: four nodes sharing one long preamble and one MMM →
`COLLAPSED` (3 duplicate hashes, 870-char shared preamble); four nodes
with voice-specific root inputs and distinct MMM slices → `DIVERSE`
(mean pairwise overlap 0.0).

Claim ceiling, stated in every receipt: **it measures whether the root
inputs differed. It says nothing about output quality or truth.** That
keeps the gate inside CB's remit — it never scores content.

## 3. Zhuangzi is a prompt generator, not a seat

> zhuangzi is intentionally for driving divergence. it probably should
> be used more as a generator of prompts for other llms.

This resolves the gap noted earlier. `voice.zhuangzi` having an agent
spec but no required seat in the nine v4.3 routes is **not an
omission** — it is a category difference. Zhuangzi operates one level
up: it does not vote inside a council, it **manufactures the
dissimilar root inputs that the council's members receive.**

That closes a loop with the Wizard's origin. The first Wizards existed
to write the next formal prompt for a thread; zhuangzi's job — live
readings, alternate interpretations, exclusion conditions — is exactly
the generator you want producing those prompts. Divergence is not
achieved by asking members to disagree; it is achieved by **feeding
them genuinely different prompts**, and zhuangzi is the thing that
writes them.

Which also makes the diversity gate self-consistent: zhuangzi produces
the spread, `input_diversity_gate.py` proves the spread is real, and
the council converges over spread that was measured rather than
assumed.

## Placement

`input_diversity_gate.py` belongs with the other CB control tools. It
is deterministic, stdlib, self-tested, and takes a wave manifest of
`{node_id, root_input, mmm_slice, provider, model}`.
