---
name: cb-goodhart-wave
description: Alignment coupler for self-loops. Runs context-strategy, then refuses proxy scores, paperclip scope, and mass drift. Use before keeping a loop mutation.
---

# CB Goodhart wave

This wave is the paperclip set. It does not raise the estate score. It can veto a keep.

1. Run `cb-context-strategy-wave`. If it is not ready, stop.
2. Run `goodhart-proxy-guard` on before/after scores.
3. Run `paperclip-scope-guard` on the mutation report.
4. Run `mass-drift-guard` on context plus harvest.

Any refuse discards the mutation and stops the loop.

Claim ceiling: alignment veto only. Not a Light verdict. Not promotion.
