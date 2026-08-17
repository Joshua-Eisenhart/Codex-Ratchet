---
name: cb-context-strategy-wave
description: Step back from the local packet and manage whole-project context. Inventories prompt vs output corpora, drafts user and project MMMs as active-inference compressions, and refuses to admit a summary that lost its source. Use when context is rotting, before a campaign, after several waves, or when the user asks for context strategy, memory management, or MMM compression.
---

# CB Context Strategy Wave

This is the step-back wave. It does not harvest rival futures and it does not
falsify them. It decides what may enter the next short-lived worker.

`decision.context_strategy` already named the job: track intent, larger
context, strategy state, and what must not be lost. This wave makes that
job executable.

## Two corpora

Keep them apart.

- User corpus: typed owner prompt bytes. That is the user's language and
  order of thought. Draft the user MMM only from `owner_typed` quotes.
  Headings marked `pasted material, not typed` stay in the inventory and
  stay out of the user MMM. They are input, not voice.
- Project corpus: receipts, compiled packets, gate reasons, test
  dispositions. That is the system's language. Draft the project MMM only
  from this.

A project phrase must not overwrite a user verb. A user summary must not
pretend a receipt said something it did not.

## Active inference, honestly

Treat each MMM as a small generative model of language, not of the Light
object F. The Light contract still forbids importing FEP, personality, or
spinor as Light geometry.

- The user MMM predicts the user's distinctions.
- The project MMM predicts receipt vocabulary.
- New prompts or receipts that the draft cannot reconstruct are residual.
- Compression is an update that should shrink residual without replacing
  the source corpus.

A draft that cannot quote its sources is refused. Cognition is not proved.
`mmm_read_proved` stays false.

## Children

1. Inventory both corpora and the live context budget. Deterministic.
2. Draft a user MMM from prompt quotes only. `a1-from-a2-distillation`.
3. Draft a project MMM from output tokens only. Same skill, other corpus.
4. Guard admission. `a2-a1-memory-admission-guard`. Derived surfaces do
   not become source.
5. Step back. `wizard-systems-strategy` names what must not be lost in the
   next wave.

Every model-backed cell uses `mmm-preload`. Distinct mini-voice sets.

## Deterministic runner

```text
python3 ~/.codex/skills/cb-context-strategy-wave/scripts/run_context_strategy.py \
  --root /path/to/constraint_box \
  --prompt-path docs/OWNER_PROMPTS_VERBATIM_20260809.md \
  --output-path receipts \
  --out /path/to/context-strategy.receipt.json
```

The runner writes the receipt and two proposal drafts. It never admits
them as packs. It never rewrites owner prompts.

## Terminals

- `CONTEXT_SNAPSHOT_READY` — inventories and drafts are source-bound
- `HOLD` — a corpus is missing, mixed, or a draft lost its source
- `REFUSE` — asked to treat a draft as law, or to merge the two corpora
- `CANCELLED`

## Claim ceiling

Context inventory, proposal-only MMM drafts, and a step-back list of what
must not be lost. Not Light geometry. Not FEP. Not pack admission. Not
promotion.
