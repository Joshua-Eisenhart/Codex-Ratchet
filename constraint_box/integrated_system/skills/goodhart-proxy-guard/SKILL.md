---
name: goodhart-proxy-guard
description: Refuse a rising score that bought a fallen protected measure. Use when a self-loop, metric, or keep/discard step might be Goodharting.
---

# Goodhart proxy guard

When a measure becomes the target, it stops being a measure.

Protected measures may not fall just because a composite score rose:

- `seed_admit`
- `light_decides_control`
- `valid_v1`
- `zip_valid`
- `tests_passed`
- `promotion_allowed` must stay false
- `test_failures` must stay empty

```text
python3 $CB_SKILLS_ROOT/goodhart-proxy-guard/scripts/check_proxy.py \
  --before /path/before.json --after /path/after.json
```

Terminals: `PROXY_CLEAN`, `REFUSE_PROXY`.
Authority: none. Not a Light verdict.
