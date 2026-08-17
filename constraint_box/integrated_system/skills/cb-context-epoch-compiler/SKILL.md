---
name: cb-context-epoch-compiler
description: After a wave, create an immutable epoch referring to the prior epoch plus admitted deltas. Preserve genealogy while allowing bounded projections.
---

# CB context epoch compiler

Epochs are append-only. An epoch without a parent is only legal as genesis.
