# TENSION_MAP__v1
Status: PROPOSED / NONCANONICAL / CONTRADICTION-PRESERVING
Batch: `BATCH_upgrade_docs_bootpack_thread_b_kernel_engine_pattern__v1`
Extraction mode: `ENGINE_PATTERN_PASS`

## T1) Sole-source-of-truth claim vs duplicated in-file packaging residue
- source markers:
  - source 1: `3`
  - source 1: `975-981`
  - source 1: `1956`
- tension:
  - the source claims Thread B is the sole source of truth
  - the file itself contains duplicate kernel copies and a foreign `END BOOTPACK_THREAD_S v1.64` marker
- preserved read:
  - preserve both the authority claim and the packaging contamination

## T2) Tag fence vs in-text use of tags outside that fence
- source markers:
  - source 1: `118-135`
  - source 1: `374`
  - source 1: `575`
  - source 1: `1098-1115`
  - source 1: `1355`
  - source 1: `1556`
- tension:
  - `TAG_FENCE` restricts admissible rejection tags
  - the same source later uses or references:
    - `UNDEFINED_LEXEME`
    - `TERM_DRIFT`
  - neither appears in the allowed tag list
- preserved read:
  - do not silently normalize those tags into the fence

## T3) Namespace rule vs initial-state identifier example
- source markers:
  - source 1: `144-148`
  - source 1: `776-779`
  - source 1: `1124-1128`
  - source 1: `1757-1760`
- tension:
  - the namespace rule reserves AXIOM, PROBE, and SPEC id prefixes tightly
  - initial state includes `N01_NONCOMMUTATION`
- preserved read:
  - the source gives an example that appears inconsistent with its own declared id namespace

## T4) Equals-sign admission rule vs first-copy glyph-map omission
- source markers:
  - source 1: `219-223`
  - source 1: `239-262`
  - source 1: `1199-1203`
  - source 1: `1219-1243`
- tension:
  - the source requires `equals_sign` admission for `=`
  - the first copy omits `"=" -> "equals_sign"` from `FORMULA_GLYPH_REQUIREMENTS`
  - the second copy adds it explicitly
- preserved read:
  - the in-file duplicate is not redundant noise; it carries a real correction

## T5) Allowed command verbs vs missing visible handler rules
- source markers:
  - source 1: `615-627`
  - source 1: `810-904`
  - source 1: `1596-1608`
  - source 1: `1791-1884`
- tension:
  - the command surface lists:
    - `REPORT_STATE`
    - `CHECK_CLOSURE`
    - `SAVE_NOW`
    - `MANUAL_UNPARK`
    - `HELP`
  - no explicit handler rules for those verbs are visible in this source extract
- preserved read:
  - keep the difference between interface listing and visible implementation

## T6) Stable rulebook aspiration vs undefined rule reference
- source markers:
  - source 1: `791-799`
  - source 1: `1772-1780`
- tension:
  - `HEADER_GATE_ECHO` refers to the megaboot gate as `MBH-021`
  - the visible megaboot rules are `MBH-001` and `MBH-002`
- preserved read:
  - preserve this as source-local rule-reference drift

## T7) Container schema vs later gate-required header surface
- source markers:
  - source 1: `504-512`
  - source 1: `645-652`
  - source 1: `1485-1493`
  - source 1: `1626-1633`
- tension:
  - the `EXPORT_BLOCK` container definition explicitly mentions optional `RULESET_SHA256`
  - later megaboot hardening may require `MEGABOOT_SHA256`
  - the container header sketch does not advertise that second header
- preserved read:
  - container grammar summary and later gate behavior are not perfectly aligned in the source

## T8) No-drift, hard-kernel posture vs large non-enforceable advisory tail
- source markers:
  - source 1: `137-142`
  - source 1: `906-974`
  - source 1: `1887-1953`
- tension:
  - the source frames itself as a hard, no-drift enforcement kernel
  - it also includes sizable non-enforceable advisory zones:
    - usability command card
    - cosmological-parameter note
    - formula grammar ladder
- preserved read:
  - the source combines strict law with documentary/operator guidance inside one file
