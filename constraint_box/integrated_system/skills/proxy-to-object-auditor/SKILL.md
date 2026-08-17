---
name: proxy-to-object-auditor
description: Goodhart auditor. Names the real object, the proxy being scored, and interventions where the proxy can rise while the object gets worse. Use before keeping a self-loop mutation.
---

# Proxy-to-object auditor

Couples to `goodhart-proxy-guard` for the numeric veto. This skill names the split.

Required answers:

1. What is the real object?
2. What proxy are we scoring?
3. Under what intervention can the proxy rise while the object gets worse?

If those three are missing, HOLD. If a named intervention is observed in the score delta, REFUSE.

```text
python3 ~/.codex/skills/proxy-to-object-auditor/scripts/audit_proxy.py \
  --card /path/object_proxy.json --before score.json --after score.json
```

Default CB object: finite Light seed F plus honest operation names.
Default proxy: wave-estate composite score.
Known bad intervention: add empty tests, mint untested waves, treat solver-chosen obs as quotients.
