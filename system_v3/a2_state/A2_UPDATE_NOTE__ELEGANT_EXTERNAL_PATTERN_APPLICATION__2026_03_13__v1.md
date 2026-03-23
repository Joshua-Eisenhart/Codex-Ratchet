# A2_UPDATE_NOTE__ELEGANT_EXTERNAL_PATTERN_APPLICATION__2026_03_13__v1

Status: DRAFT / NONCANON / A2 CONTROL NOTE
Date: 2026-03-13
Role: bounded A2 refresh for practical elegant application of current external pattern references
Surface class: DERIVED_A2

## Scope

This pass does one bounded A2 task:
- deepen the current external-pattern understanding
- extract only the parts that practically improve the ratchet
- translate those parts into lean local design guidance

This pass does not:
- adopt any outside framework wholesale
- literalize geometric metaphor
- promote any new A1 work

## Source anchors

Local reference notes:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/external_refs/PI_MONO__REFERENCE_NOTE__2026_03_13__v1.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/external_refs/KARPATHY__REFERENCE_NOTE__2026_03_13__v1.md`

Primary external sources:
- `pi-mono` coding-agent README:
  - `https://github.com/badlogic/pi-mono/tree/main/packages/coding-agent`
- `karpathy/nanochat` README:
  - `https://github.com/karpathy/nanochat`
- `karpathy/autoresearch` README:
  - `https://github.com/karpathy/autoresearch`
- `karpathy/llm-council` README:
  - `https://github.com/karpathy/llm-council`

## External findings that matter

### 1. `pi-mono`: minimal harness, extensibility pushed outward

Useful current read:
- keep the core minimal
- adapt the tool to the workflow, not the workflow to the tool
- put special behavior in skills/extensions/packages, not in the core
- keep a small default tool surface
- allow session branching and compaction without inflating the base harness

Practical ratchet translation:
- keep one lean controller core
- put workflow specialization into:
  - skills
  - automation prompts
  - packet standards
- do not bake every useful idea into the core A2/A1 doctrine

### 2. `nanochat`: one cohesive baseline, one main complexity dial

Useful current read:
- one cohesive end-to-end baseline
- small hackable codebase
- one main knob (`depth`) that determines the rest
- avoid giant configuration forests

Practical ratchet translation:
- prefer one dominant control dial for upper-loop work instead of many weak knobs
- likely candidates:
  - packet scope class
  - audit depth
  - lane budget
- the system should prefer a small number of legible operating modes over many overlapping policy switches

### 3. `autoresearch`: fixed-budget mutation/eval loop

Useful current read:
- single file to mutate
- fixed 5-minute budget
- one metric
- keep/discard loop
- `program.md` as the lightweight human-edited org/skill surface

Practical ratchet translation:
- when experimenting with upgrade-support loops, mutate one bounded surface at a time
- prefer fixed-budget experiments
- use one explicit success test per loop
- keep the human-edit surface small and textual

Safe local targets for this pattern:
- automation prompts
- packet standards
- audit templates
- controller decision rules

Unsafe targets for this pattern:
- active A2/A1 owner surfaces
- lower-loop mutation path
- anything destructive

### 4. `llm-council`: staged multi-view audit

Useful current read:
- stage 1: independent first opinions
- stage 2: anonymized review/ranking
- stage 3: chairman synthesis

Practical ratchet translation:
- use this as an audit pattern, not as core ontology
- good fit for:
  - `Pro` return review
  - cross-lane disagreement surfacing
  - contradiction-preserving audit summaries

Minimal ratchet form:
- first pass: raw return extraction
- second pass: blinded critique/comparison
- third pass: controller summary with keep/retool/reject classification

## Elegant-application rule set

The cleanest current import rule is:

1. borrow process shape, not framework sprawl
2. prefer one small owner surface over many helper layers
3. prefer one dominant knob over many configuration axes
4. mutate one bounded thing at a time
5. evaluate on one explicit criterion per loop
6. keep review multi-view when truth is uncertain
7. keep metaphor as guidance unless and until lower-loop support exists

## Direct practical upgrades for this repo

Most promising near-term applications:

### A. One dominant upper-loop budget dial

Define one small explicit dial for bounded work, for example:
- `LIGHT`
- `STANDARD`
- `DEEP`

Use it consistently across:
- packet prep
- return audit
- controller summaries
- external pattern mining

This is the strongest current path toward elegance because it reduces policy sprawl.

### B. Council-style return audit

Turn the current return-audit concept into a formal three-stage review:
- extraction
- critique
- controller synthesis

This improves rigor without adding much machinery.

### C. `program.md`-like controller surfaces

Keep human-edited control text small.
Prefer a few compact controller notes and packet manifests over large diffuse instructions.

### D. One-mutable-surface experiments in quarantine

When improving the support program, change one thing at a time:
- one automation prompt
- one packet contract
- one audit rubric

Then compare against one explicit criterion:
- fewer blocked cases
- less drift
- smaller packet
- fewer ambiguous outputs

### E. Hopf/tori as runtime overlay only

Use the geometry as:
- phase labeling
- nested-loop intuition
- recurrence structure

Do not use it as:
- literal substrate closure
- required architecture inflation

This preserves the useful intuition while keeping the machine lean.

## Bottom line

The deeper read does support the user's claim:
- these external ideas can make the system more practical
- they can also make it leaner and more elegant

But only if the import posture stays:
- minimal-core
- nonliteral
- nonclassical-permitted
- anti-bloat
- audit-first
