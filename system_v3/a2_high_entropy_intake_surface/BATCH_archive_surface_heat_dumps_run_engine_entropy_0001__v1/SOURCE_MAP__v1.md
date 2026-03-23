# SOURCE_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_heat_dumps_run_engine_entropy_0001__v1`
Extraction mode: `ARCHIVE_HEAT_DUMPS_RUN_ENGINE_ENTROPY_0001_PASS`
Batch scope: archive-only intake of `HEAT_DUMPS/20260225T070252Z/RUN_ENGINE_ENTROPY_0001`, bounded to its three retained sandbox child families and representative prompt/memo/consumed signatures only
Date: 2026-03-09

## 1) Batch Selection
- selected sources:
  - direct archive object:
    - `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/HEAT_DUMPS/20260225T070252Z/RUN_ENGINE_ENTROPY_0001`
  - retained child families:
    - `a1_sandbox__prompt_queue`
    - `a1_sandbox__lawyer_memos`
    - `a1_sandbox__incoming_consumed`
  - representative source anchors:
    - `000001_20260225T060434Z_ROLE_1_LENS_VN__A1_PROMPT.txt`
    - `000001_20260225T060434Z_ROLE_7_PACK_SELECTOR__A1_PROMPT.txt`
    - `000003_MEMO_LENS_VN__20260225T060711Z.json`
    - `000024_MEMO_LENS_VN__20260225T063305Z.json`
    - `000106_MEMO_LENS_VN__20260225T064837Z.json`
    - `000003_LENS_VN.json`
    - `000024_MEMO_LENS_VN__20260225T063305Z__AUTOFILL.json`
- reason for bounded family batch:
  - this pass resolves the sandbox-like branch that the earlier root-split batch deferred
  - the archive value is structural rather than authoritative: it preserves a prompt-orchestration workbench with repeated role lanes, shadow output mirrors, and retry/autofill residue
  - the branch is useful for historical lineage because it shows how a run-named object could act as a lawyer-pack entropy conveyor without preserving ordinary runtime state surfaces
- deferred next bounded batch in folder order:
  - `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/HEAT_DUMPS/20260225T070252Z/repo_archive__moved_out_of_git`

## 2) Source Membership
### Source 1
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/HEAT_DUMPS/20260225T070252Z/RUN_ENGINE_ENTROPY_0001`
- source class: run-named sandbox residue root
- retained family markers:
  - file count: `2558`
  - directory count: `3`
  - only child families:
    - `a1_sandbox__incoming_consumed`
    - `a1_sandbox__lawyer_memos`
    - `a1_sandbox__prompt_queue`
- archive meaning:
  - this object is shaped like a sandbox export shell, not a normal run root with summary/state/events surfaces at this boundary

### Source 2
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/HEAT_DUMPS/20260225T070252Z/RUN_ENGINE_ENTROPY_0001/a1_sandbox__prompt_queue`
- source class: sandbox prompt conveyor
- retained markers:
  - file count: `938`
  - round prefixes: `134`
  - exact round width: `7` prompt files per prefix
  - role set:
    - `LENS_VN`
    - `LENS_MUTUAL_INFO`
    - `LENS_CONDITIONAL`
    - `LENS_THERMO_ANALOGY`
    - `DEVIL_CLASSICAL_SMUGGLER`
    - `RESCUER`
    - `PACK_SELECTOR`
  - prompt-only prefixes with no downstream memo/consumed counterparts:
    - `000001`
    - `000002`
  - role-1 prompt evolution:
    - `134` prompts
    - `35` unique `state_hash` values
    - `35` unique `requested_step` values
    - requested-step range: `1` through `112`
  - late queue signature:
    - final retained prompt prefix is `000134`
    - final prompt still reports `requested_step=112`
    - final prompt reports `next_inbox_sequence=131`
- archive meaning:
  - the prompt queue preserves an overproduced role carousel whose sequence count runs ahead of admitted step progress

### Source 3
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/HEAT_DUMPS/20260225T070252Z/RUN_ENGINE_ENTROPY_0001/a1_sandbox__lawyer_memos`
- source class: lawyer memo output mirror
- retained markers:
  - file count: `810`
  - unique prefixes: `132`
  - effective six-role memo sets: `135`
  - role set:
    - `LENS_VN`
    - `LENS_MUTUAL_INFO`
    - `LENS_CONDITIONAL`
    - `LENS_THERMO_ANALOGY`
    - `DEVIL_CLASSICAL_SMUGGLER`
    - `RESCUER`
  - duplicate memo prefixes with two retained timestamp waves each:
    - `000039`
    - `000106`
    - `000111`
  - prompt-side `PACK_SELECTOR` has no retained lawyer-memo output family
- archive meaning:
  - the memo layer preserves six role responses only, so the seventh prompt lane is retained as instruction pressure rather than as stored output

### Source 4
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/HEAT_DUMPS/20260225T070252Z/RUN_ENGINE_ENTROPY_0001/a1_sandbox__incoming_consumed`
- source class: consumed sandbox mirror
- retained markers:
  - file count: `810`
  - unique prefixes: `132`
  - role set matches the six lawyer-memo roles only
  - naming split:
    - `66` bare early files such as `000003_LENS_VN.json`
    - `744` memo-named later files
    - `684` memo-named files carry `__AUTOFILL`
  - content relation to lawyer memos:
    - all `66` bare early files match lawyer-memo JSON exactly by `sequence` plus `role`
    - `620` later memo-named files match lawyer memo JSON exactly with identical timestamp signatures
    - the remaining `124` later files still match lawyer memo JSON exactly when timestamp skew is ignored
    - no true JSON-content divergence was found between lawyer and consumed mirrors
- archive meaning:
  - this is a transport-style shadow surface over the lawyer memos, not an independent evidence family

## 3) Representative Evidence Anchors
- prompt contract anchor:
  - `000001_20260225T060434Z_ROLE_1_LENS_VN__A1_PROMPT.txt` uses `A1_SANDBOX_MODE: LAWYER_PACK_v1`, sets `RUN_ID: RUN_ENGINE_ENTROPY_0001`, and constrains output to a sandbox-only JSON object
- prompt contradiction anchor:
  - `000001_20260225T060434Z_ROLE_7_PACK_SELECTOR__A1_PROMPT.txt` keeps the memo-schema requirement but changes the role objective to "output one schema-valid A1_STRATEGY_v1 JSON object only"
- memo/output mirror anchor:
  - `000003_MEMO_LENS_VN__20260225T060711Z.json` and `000003_LENS_VN.json` carry the same JSON payload under different naming shells
- autofill onset anchor:
  - `000024_MEMO_LENS_VN__20260225T063305Z.json` has a matching consumed shadow `000024_MEMO_LENS_VN__20260225T063305Z__AUTOFILL.json`
- duplicate-wave anchor:
  - prefix `000106` keeps one prompt wave at `20260225T064714Z`, one lawyer memo wave at `20260225T064715Z`, and a second lawyer/consumed wave at `20260225T064837Z`

## 4) Archive Handling Decision
- treat this branch as:
  - retention/history/heat-dump prompt-orchestration residue
  - useful for older sandbox patterns, role-lane experiments, and duplication/retry lineage
  - not active runtime input or current authority
- do not infer:
  - a complete run spine
  - earned lower-loop validation
  - successful strategy selection outputs from the `PACK_SELECTOR` lane
