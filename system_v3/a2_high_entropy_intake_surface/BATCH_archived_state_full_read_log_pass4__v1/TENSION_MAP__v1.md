# TENSION_MAP__v1
Status: PROPOSED / NONCANONICAL / CONTRADICTION-PRESERVING
Batch: `BATCH_archived_state_full_read_log_pass4__v1`
Extraction mode: `READ_LOG_AUDIT_PASS`

## T1) Read-log breadth vs source-class purity
- source markers:
  - source 1: throughout
  - source 1: tail `results_*` entries
- tension:
  - the file tries to inventory a very broad upload corpus in one pass
  - that same breadth mixes Thread-S dumps, ladder docs, notes, rosettas, runner scripts, and SIM results inside one audit surface
- preserved read:
  - useful for inventory, weak for clean source-class separation

## T2) Undeclared canon labels vs strong constraint/candidate language
- source markers:
  - source 1: repeated `CANON: undeclared`
  - source 1: repeated explicit constraint lists and assumption statements
- tension:
  - many logged docs carry detailed constraint IDs and strong declarative assumptions
  - the log still marks their canon status as undeclared
- preserved read:
  - the file preserves a real authority gap between document richness and canon grounding

## T3) Append-only audit posture vs rewrite/compression warnings
- source markers:
  - source 1: repeated `A2_CONFLICTS: REWRITE_LANGUAGE_PRESENT(conflicts_with_append_only)`
  - source 1: repeated `A2_CONFLICTS: COMPRESSION_LANGUAGE_PRESENT(review)`
- tension:
  - the pass is trying to review sources under append-only / anti-compression discipline
  - several source docs still trigger rewrite-language and compression-language warnings
- preserved read:
  - the archive captures active tension between desired process discipline and incoming document style

## T4) Root-constraint correction vs surviving `AXIOM_HYP` labels
- source markers:
  - source 1: `18-20`
  - source 1: `66-68`
- tension:
  - the audit flags the `AXIOM_HYP` vs root-constraint mismatch explicitly
  - it still leaves the underlying artifacts in that older labeling regime
- preserved read:
  - this is a recorded naming debt, not a repaired state

## T5) Megaboot packaging rules vs inherited artifact reality
- source markers:
  - source 1: `18-19`
  - source 1: `66-67`
  - source 1: repeated `ASCII_ONLY_VIOLATION(non_ascii_content)` and `PATH_NONASCII`
- tension:
  - the pass audits against packaging/hygiene rules such as text size caps and ASCII/path constraints
  - the underlying archive corpus repeatedly violates those constraints
- preserved read:
  - the file is valuable precisely because it records those failures instead of hiding them

## T6) SIM evidence presence vs low interpretive content
- source markers:
  - source 1: later `SIM results artifact (json)` entries
- tension:
  - the pass includes many SIM result artifacts
  - it mostly treats them as logged files rather than interpreted evidence or system consequences
- preserved read:
  - this is an inventory/audit log, not an evidence-analysis surface
