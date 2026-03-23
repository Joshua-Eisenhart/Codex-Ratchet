# TENSION_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_heat_dumps_run_engine_entropy_0001__v1`
Date: 2026-03-09

## Tension 1: Run Label Versus Missing Run Spine
- source anchors:
  - `RUN_ENGINE_ENTROPY_0001` root inventory
- bounded contradiction:
  - the object is run-named, but at this retained boundary it has no summary/state/events spine and preserves only sandbox prompt/memo families
- intake handling:
  - preserve the run-named/sandbox-shaped split without inventing missing runtime state

## Tension 2: Seven Prompt Roles Versus Six Stored Output Roles
- source anchors:
  - `a1_sandbox__prompt_queue`
  - `a1_sandbox__lawyer_memos`
  - `a1_sandbox__incoming_consumed`
- bounded contradiction:
  - every prompt round includes `PACK_SELECTOR`, but no retained lawyer or consumed output exists for that role
- intake handling:
  - preserve `PACK_SELECTOR` as an unclosed selector lane rather than treat it as silently successful

## Tension 3: PACK_SELECTOR Prompt Contract Self-Conflict
- source anchors:
  - `000001_20260225T060434Z_ROLE_7_PACK_SELECTOR__A1_PROMPT.txt`
  - late `000106` and `000134` `PACK_SELECTOR` prompt samples
- bounded contradiction:
  - the prompt schema section still demands `A1_LAWYER_MEMO_v1`, while the role objective instructs the model to emit one `A1_STRATEGY_v1` object
- intake handling:
  - preserve the memo-schema versus strategy-object conflict as a historical contract flaw

## Tension 4: Queue Depth Versus Admitted Progress
- source anchors:
  - prompt samples for prefixes `000001`, `000002`, `000003`, `000133`, `000134`
- bounded contradiction:
  - prompt sequence rises to `134`, but the final retained prompt still reports `requested_step=112` and `next_inbox_sequence=131`
- intake handling:
  - preserve the queue/progress skew as evidence of orchestration lag rather than as straightforward step advancement

## Tension 5: Prompt Start Versus Output Start
- source anchors:
  - prompt prefix inventory
  - lawyer/consumed prefix inventories
- bounded contradiction:
  - prompt rounds begin at `000001`, but stored memo/consumed outputs begin only at `000003`
- intake handling:
  - preserve the first two rounds as prompt-only warm-up or dropped-output residue, not as completed response cycles

## Tension 6: Independent Output Appearance Versus Shadow-Mirror Reality
- source anchors:
  - lawyer memo samples
  - consumed samples
  - lawyer/consumed JSON equality checks
- bounded contradiction:
  - the archive appears to preserve two output families, but the consumed layer adds no semantic divergence and mostly rewrites names, timestamps, and autofill suffixes only
- intake handling:
  - treat the consumed family as a shadow transport mirror, not as a second independent evidence corpus

## Tension 7: Stable Sequence IDs Versus Repeated Output Waves
- source anchors:
  - duplicate prefixes `000039`, `000106`, `000111`
- bounded contradiction:
  - one prompt wave is retained for those sequences, but two lawyer-memo and two consumed waves survive under the same prefix
- intake handling:
  - preserve repeated-wave residue as retry lineage under stable ids instead of flattening it into one clean sequence pass
