---
name: cb-object-proxy-mapper
description: Map a primary object to its proxy, measurement, consumer, and allowed inference without deciding truth or promotion.
---

# Object-proxy mapper

`scripts/map_proxy.py` is a deterministic, model-free proposal cell. Its exact
input is a JSON object with canonical `operation_id` equal to
`cb-object-proxy-mapper.v1`, one consistent nonempty `target`/`target_id`, and
the five chain fields. It emits a content-addressed receipt with promotion,
provider, and writes disabled. `cancel_requested: true` returns passive
`CANCELLED` without sealing a receipt; missing chain fields remain
`HOLD_CHAIN_INCOMPLETE`.
