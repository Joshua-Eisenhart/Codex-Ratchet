# VOICES AND MMMs — the divergence mechanism (owner canon, 2026-08-06)

**Provenance: owner-minted.** Stated directly. This is the mechanism
behind the wave model; the wave model is the skeleton, this is what
makes the skeleton produce real spread instead of costume spread.

## The statement

> I created voices, to drive an llm to think in a formal different way.
> And have mmms load those voices. **Not as rules. But as pre language
> to bias the saliency.** Create more real divergence in llms. While
> then forcing convergence in llm councils. And sequencing the waves.
> And looping the waves.

## Why "pre-language, not rules" is the whole thing

A rule acts on output: it tells a model what it may not say. The model
still thinks the same way and then edits itself. Every member so ruled
remains the same model wearing a label — costume divergence.

Pre-language acts on what the model reaches for first. Loading a voice
before the task shifts which terms, questions, and framings are
salient, so the model generates from a different region to begin with.
That is **formal difference in the thinking**, not difference in the
phrasing of a shared thought.

This is why the mini-MMM fields are what they are:

| Field | What it biases |
|---|---|
| `phraselets` | the terms the model tends to use — vocabulary priming |
| `question_stems` | the questions it naturally asks — attention priming |
| `job` | what this member makes more salient |
| `return_shape` | what a receipt from this member contains |
| `avoid` | the failure modes of this role |
| `compile_relevance` | how this member contributes to bounded work |

Note what is absent: prohibitions on content, scoring rubrics, output
filters. The packet says it outright — a mini-MMM "is a role-local
salience profile. **It is not a rule list.**"

## The four-beat cycle

1. **Diverge** — voices loaded as pre-language via per-node MMMs, with
   constrained and deliberately dissimilar root inputs.
2. **Converge** — the LLM council forces unification of the spread it
   just produced. Convergence is a stage, not an emergent hope.
3. **Sequence** — waves are barriers; a later wave consumes the
   accepted output of the earlier ones.
4. **Loop** — waves re-enter, within themselves and across each other,
   so divergence and convergence alternate rather than run once.

Divergence without forced convergence is noise. Convergence without
driven divergence is the v3 collapse. The cycle needs both, in order,
repeatedly.

## The failure this prevents, stated precisely

The v3 systems had deterministic gates and no exploration at them: the
models absorbed the gate's ontology and went hyper-conservative. That
happens when every node shares root inputs and one vocabulary. Under
this mechanism it cannot: nodes are primed with *different*
pre-language and *constrained, dissimilar* inputs, so they do not
occupy the same basin to begin with.

## Hard consequence for ConstraintBox

**CB must never turn voices into rules.** If CB checks outputs for
conformity to voice vocabulary, it converts saliency bias into
compliance — and compliance is exactly the v3 collapse, rebuilt with
better receipts. The boundary:

| Layer | Uses voices as | May check |
|---|---|---|
| Exploration lane | pre-language, loaded before the task | nothing — it is generating |
| Council | convergence stage over diverse output | that members diverged, not that they conformed |
| CB | none — CB never loads voices into explorers | structure of the returned packet: fields present, receipts real, count law satisfied |

What CB *can* measure without breaking the mechanism:

- **root-input dissimilarity** across nodes in a wave (shared root-input
  hash = one opinion in many hats);
- **MMM/slice preload recorded per node** — the packet already requires
  `positive_mini_mmm_loaded_before_task` in the subsubagent receipt;
- **distinct deltas** — the topology correction already requires child
  variants to produce different kinds of delta, not copies;
- **collapse detection** — `agents/auditors/council-collapse-auditor.md`
  exists for exactly this.

CB checks that divergence *happened*. It never checks that output
*sounds right*.

## Open gap between model and packet

`voice.zhuangzi` — live readings, alternate interpretations, exclusion
condition — carries an agent spec but appears in none of the nine v4.3
routes' required-children lists. Under this mechanism that is the voice
whose pre-language most directly produces alternate framings, i.e. the
one most responsible for real divergence. Worth a ruling: whether it is
optional by design, or an omission.
