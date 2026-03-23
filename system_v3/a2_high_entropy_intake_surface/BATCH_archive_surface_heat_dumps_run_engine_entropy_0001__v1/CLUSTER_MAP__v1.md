# CLUSTER_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_heat_dumps_run_engine_entropy_0001__v1`
Date: 2026-03-09

## Cluster 1: Run-Named Sandbox Shell
- archive meaning:
  - `RUN_ENGINE_ENTROPY_0001` is named like a run but preserves only three sandbox child families at this boundary
- bound evidence:
  - no root-level summary/state/events surfaces were read because none exist in this folder
  - only `a1_sandbox__prompt_queue`, `a1_sandbox__lawyer_memos`, and `a1_sandbox__incoming_consumed` are retained
- retained interpretation:
  - useful example of heat-dump naming drift where a run id wraps a prompt/memo workbench instead of an earned runtime snapshot

## Cluster 2: Seven-Role Prompt Carousel
- archive meaning:
  - the prompt family is a strict seven-role orchestration lattice
- bound evidence:
  - `938` prompt files
  - `134` prefixes
  - every prefix contains exactly `7` prompts
  - roles are the six lens/rescuer lanes plus `PACK_SELECTOR`
- retained interpretation:
  - useful historical scaffold for multi-lens sandbox prompting with one explicit strategy-selection lane added on top

## Cluster 3: Six-Role Output Funnel
- archive meaning:
  - downstream stored outputs collapse the seven prompt lanes back to six memo roles
- bound evidence:
  - `810` lawyer memo JSONs and `810` consumed JSONs
  - neither downstream family retains any `PACK_SELECTOR` role file
  - prompt prefixes `000001` and `000002` never produce downstream memo/consumed files
- retained interpretation:
  - useful evidence that the selector lane remained instruction-side pressure rather than a retained output channel

## Cluster 4: Shadow-Mirror Consumption Layer
- archive meaning:
  - the consumed family mirrors lawyer memos instead of adding new semantic content
- bound evidence:
  - `66` early bare consumed files match lawyer memo JSON exactly by sequence and role
  - `744` later memo-named consumed files all match lawyer memo JSON exactly once timestamp skew is ignored
  - `684` later consumed files add `__AUTOFILL`
- retained interpretation:
  - useful historical pattern for transport/consumption shadow copies, timestamp rewrites, and autofill labeling without semantic change

## Cluster 5: Duplicate Retry Waves
- archive meaning:
  - some sequences preserve more than one output wave under the same prefix
- bound evidence:
  - prefixes `000039`, `000106`, and `000111` each retain two six-role lawyer-memo waves
  - the consumed mirror preserves both waves as `__AUTOFILL` copies
  - prompt family keeps only one seven-role wave for each of those prefixes
- retained interpretation:
  - useful retry lineage signature showing repeated output emission under stable sequence ids

## Cluster 6: Heavy Prompt Payload Embedding
- archive meaning:
  - prompts are not minimal asks; they embed rosetta and A1-brain context blocks
- bound evidence:
  - late prompt samples include `BEGIN_ROSETTA_INDEX`
  - the same samples include `BEGIN_A1_BRAIN_TAIL`
  - the `PACK_SELECTOR` and lens prompts share this heavy embedded tail
- retained interpretation:
  - useful example of sandbox prompting that inlines context packs directly into each role file instead of referencing lighter external state
