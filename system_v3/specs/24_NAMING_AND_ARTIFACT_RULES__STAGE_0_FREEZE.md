# Stage-0 Naming and Artifact Rules Freeze
Status: DRAFT / NONCANON
Date: 2026-03-03
Owner: naming and transport hygiene

## Purpose
Freeze one naming grammar for Stage-0 so ZIP jobs, run artifacts, and brain updates are explicit, batch-first, OS-usable, and deterministic.

## Scope
In scope:
- ZIP job input/output filenames.
- Batch folder names.
- Brain/bootpack artifact names.
- A1 lane request/return names.

Out of scope:
- Changing ZIP payload contracts in `ZIP_PROTOCOL_v2`.
- Changing A0/B/SIM admission behavior.

## Core Rules
1. Batch-first ordering is required for any batch artifact.
2. Names must be explicit but length-bounded.
3. One separator style only: double underscore `__` between fields.
4. One token style only: uppercase snake tokens (`A-Z0-9_`).
5. Version field is always terminal before extension (`__vN` or `__vN_M`).
6. Extensions are lowercase (`.zip`, `.md`, `.json`, `.txt`).

## Character and Length Contract
- Allowed filename charset: `A-Z`, `a-z`, `0-9`, `_`, `.`
- No spaces.
- No hyphens.
- No parentheses.
- No repeated separators beyond `__`.
- Filename max length:
  - preferred: `<= 120` chars
  - hard max: `<= 160` chars
- Directory max length:
  - preferred: `<= 80` chars
  - hard max: `<= 120` chars

If a generated name exceeds preferred length, shorten only the subject field, never the prefix fields.

## Canonical Field Order
Use this field order for all new Stage-0 artifacts:

1. `BATCH_OR_SEQ_PREFIX`
2. `PIPELINE_SCOPE`
3. `ARTIFACT_ROLE`
4. `SUBJECT`
5. `VERSION`

### Field Definitions
- `BATCH_OR_SEQ_PREFIX`:
  - batch form: `BATCH_01_OF_10`
  - sequence form: `000001`
  - run form (non-batch): `RUN_<TOKEN>`
- `PIPELINE_SCOPE` examples:
  - `A2_LAYER1`
  - `A2_LAYER1_5`
  - `A1_WIGGLE`
  - `RATCHET_PREP`
- `ARTIFACT_ROLE` enum (Stage-0):
  - `INPUT_JOB`
  - `OUTPUT_JOB`
  - `BRAIN_UPDATE_PACKET`
  - `BOOTPACK`
  - `AUDIT`
  - `MANIFEST`
  - `REQUEST`
  - `RETURN`
- `SUBJECT`:
  - concise explicit slug, uppercase snake, no filler words.
  - target length: `<= 48` chars.
- `VERSION`:
  - `v1`, `v2`, `v7_2_4`, etc.

## Canonical Filename Patterns

### 1) Batch input ZIP
`BATCH_01_OF_10__A2_LAYER1__INPUT_JOB__FEP_MARKOV_BLANKET_SURFACE__v1.zip`

### 2) Batch output ZIP
`BATCH_01_OF_10__A2_LAYER1__OUTPUT_JOB__FEP_MARKOV_BLANKET_SURFACE__v1.zip`

### 3) Stage audit report
`BATCH_01_OF_10__A2_LAYER1__AUDIT__FEP_MARKOV_BLANKET_SURFACE__v1.md`

### 4) Brain update packet
`BATCH_01_OF_10__A2_LAYER1_5__BRAIN_UPDATE_PACKET__A2_BRAIN_DELTA__v1.md`

### 5) Batch manifest
`BATCH_SET__A2_LAYER1__MANIFEST__CORE_DOCS_10_THREAD_RUN__v1.json`

### 6) A1 request/return ZIP
- Request: `000068__A1_WIGGLE__REQUEST__LAWYER_PACK__v1.zip`
- Return: `000068__A1_WIGGLE__RETURN__ROLE_OUTPUTS__v1.zip`

## Directory Naming Patterns

### Batch root
`A2_LAYER1_BATCH_RUNS__v1`

### Batch-specific folder
`BATCH_01_OF_10__A2_LAYER1__FEP_MARKOV_BLANKET`

### Brain folders
- `a2_brain_persistent__v1`
- `a1_brain_persistent__v1`

## Subject Compression Rules (for Overlong Names)
If subject is too long:
1. Remove stop words: `AND`, `THE`, `WITH`, `FOR`, `DEFAULT`, `ANY`.
2. Compress repeated concepts to one token (`MULTI_TOPIC_FULL_EXTRACTION` -> `TOPIC_EXTRACTION`).
3. Keep domain-critical anchors (`A2`, `A1`, `RATCHET`, `IGT`, `FEP`, `SZILARD`, `CARNOT`).

Do not remove:
- batch prefix
- pipeline scope
- artifact role
- version

## Backward Compatibility Rule
Existing files are not renamed retroactively in Stage-0.
All new artifacts created from this point must use this grammar.

## Stage-0 Acceptance Checklist
- Every new batch ZIP starts with `BATCH_XX_OF_YY`.
- Every new filename contains a valid `ARTIFACT_ROLE`.
- No new filename exceeds hard max length.
- No spaces or parentheses in new names.
- Output and input pairs share the same first four fields and differ only by role/version.
- A1 sequence artifacts keep six-digit numeric prefix.

## Immediate Adoption Targets
Apply this naming freeze to:
- `work/zip_dropins/` outputs
- `work/zip_job_templates/` generated zips
- desktop-exported batch zips
- `work/a1_llm_lane_requests/` and `work/a1_llm_lane_returns/` next generated names

