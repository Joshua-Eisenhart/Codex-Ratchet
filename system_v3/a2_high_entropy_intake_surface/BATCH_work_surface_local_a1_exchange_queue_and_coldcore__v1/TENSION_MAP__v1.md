# TENSION MAP

Batch id: `BATCH_work_surface_local_a1_exchange_queue_and_coldcore__v1`

## Tension 1: high-volume request stream vs near-absent responses

Evidence
- `requests/` contains `2655` files.
- `responses/` contains only `2` files.
- Prefix `000001` repeats `2650` times with no captured response.

Meaning
- The bridge preserves intent to externalize A1 memo generation, but the captured archive shows queue accumulation rather than a balanced handshake.

## Tension 2: timestamp churn vs logical content stability

Evidence
- Raw request files are all unique at the byte level.
- Normalized comparison collapses them to `2` logical signatures.

Meaning
- Most of the observed traffic is filename/timestamp/path churn, not new semantic request variety.

## Tension 3: shared A1 brain excerpt vs divergent run scopes

Evidence
- Both request families reuse the same `a1_brain_context.excerpt_sha256`.
- the prepack request signature carries `30` terms and `0` graveyard targets.
- the graveyard-aware request signature carries `98` terms and `24` graveyard targets.

Meaning
- The contextual overlay is stable, but the operational target set swings substantially. The bridge does not capture a correspondingly clearer context split.

## Tension 4: multi-role response design vs duplicate response capture

Evidence
- Both captured responses normalize to the same `12`-memo packet for sequence `6`.

Meaning
- The prototype knows how to generate a rich role-split response, but the recorded return surface shows duplication rather than iterative development.

## Tension 5: cold-core distillation narrows aggressively

Evidence
- A `24`-memo graveyard-validity run collapses to one admissible term: `entropy_production_rate`.
- A `10`-memo substrate-family run collapses to seven admissible terms.

Meaning
- The reduction stage is effective at narrowing, but it may overcompress high-entropy exploration into very small survivor sets.

## Tension 6: distilled proposal packets omit state binding

Evidence
- Both cold-core proposal files leave `state_hash` empty.

Meaning
- The outputs are shaped like executable handoff packets but do not preserve a concrete state binding.

## Tension 7: test residue exists without surrounding run context

Evidence
- `cache_backup` preserves pytest node ids for A1 bridge parsing and max-sims enforcement.
- It does not preserve the run reports or assertions beyond the cache index.

Meaning
- The residue hints that validation happened, but the archive is too thin to treat it as substantive evidence by itself.
