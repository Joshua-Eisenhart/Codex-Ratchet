---
name: paperclip-scope-guard
description: Refuse a keep that maximises one number by exploding scope. Use when a loop touches too many files, mints an untested wave, or flips promotion_allowed.
---

# Paperclip scope guard

A paperclip keep maximises the score and eats the object.

Refuse when:

- more than 8 files were touched in one mutation
- a new wave has no tests
- `promotion_allowed` became true
- the claim ceiling was cut below 20 characters

```text
python3 ~/.codex/skills/paperclip-scope-guard/scripts/check_paperclip.py \
  --mutation /path/mutation.json
```

Terminals: `SCOPE_CLEAN`, `REFUSE_PAPERCLIP`.
