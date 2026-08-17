---
name: cb-context-projector
description: Build bounded context packets. Every packet gets a tiny shared kernel (object hash, hard constraints, claim ceiling) plus deliberately different role-specific source roots. Use before dispatching wave members.
---

# CB context projector

Object continuity lives in the kernel. Input diversity lives in the lane packets.

Selection rule: relevance × authority × unresolved obligation. Not recency.

```text
python3 ~/.codex/skills/cb-context-projector/scripts/project.py \
  --kernel /path/kernel.json --lanes /path/lanes.json --out /path/packets.json
```

Refuse if two lanes share the same source-root digest.
