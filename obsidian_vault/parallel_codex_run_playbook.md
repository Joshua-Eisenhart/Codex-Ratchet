---
id: "A2_3::SOURCE_MAP_PASS::parallel_codex_run_playbook::1c24b62e8178db7e"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "DRAFT"
---

# parallel_codex_run_playbook
**Node ID:** `A2_3::SOURCE_MAP_PASS::parallel_codex_run_playbook::1c24b62e8178db7e`

## Description
Concrete operator playbook: C0=controller, W1=highest-value A2 pass (refinedfuel RUN_NOW set), W2=empty unless clearly separate, A1=empty until a1? returns ready. Continuation handling via auto-go-on applicator: SEND_ONE_GO_ON, STOP_NOW, ROUTE_TO_CLOSEOUT, MANUAL_REVIEW_REQUIRED. A1 does not free-run; runs only when controller emits dispatch packet. Default bias: prefer C0+W1, add W2 only if separate, add A1 last.

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[value]]
- **DEPENDS_ON** → [[packet]]
- **EXCLUDES** → [[v3_spec_66_parallel_codex_run_playbook__v1]]

## Inward Relations
- [[66_PARALLEL_CODEX_RUN_PLAYBOOK__v1.md]] → **SOURCE_MAP_PASS**
- [[first_parallel_wave_operator_handoff_68_to_70]] → **RELATED_TO**
- [[v3_spec_66_parallel_codex_run_playbook__v1]] → **DEPENDS_ON**
- [[B_SURVIVOR_F156_LABEL_DEF]] → **ACCEPTED_FROM**
- [[GRAVEYARD_F154]] → **GRAVEYARD_OF**
- [[B_PARKED_F153]] → **PARKED_FROM**
- [[B_PARKED_F155]] → **PARKED_FROM**
