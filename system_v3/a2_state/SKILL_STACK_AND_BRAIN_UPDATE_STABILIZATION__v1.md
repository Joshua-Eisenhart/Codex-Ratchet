# SKILL_STACK_AND_BRAIN_UPDATE_STABILIZATION__v1

Status: DRAFT / NONCANON / A2 WORKING NOTE
Date: 2026-03-09
Role: identify the minimum skill stack needed to make A2/A1 brain updates consistent and less thread-dependent

## 1) Current read

The system has real process law for:
- A2-brain-first operation
- A2 -> A1 derivation
- ZIP-mediated upper-loop work
- append-driven brain updates

But those rules are still mostly distributed across:
- `system_v3/a2_state/`
- `system_v3/specs/`
- tool contracts
- thread-carried controller habits

Only two actual Codex skills are currently live:
- `playwright`
- `ratchet-a2-a1`

That means the system still lacks callable low-freedom skills for the repeatable upper-loop processes that most directly affect:
- A2 freshness
- A1 derivation consistency
- memory admission hygiene
- external-research refinery loops

## 2) Main problem

The current failure mode is not lack of ideas.

It is:
- process knowledge exists
- but it is not packaged into stable callable skills
- so brain updates still depend too much on:
  - which thread is running
  - what the operator remembers
  - whether the current assistant chooses the right sequence

That creates inconsistent A2/A1 refresh behavior.

## 3) Skill design rule

These should be skills, not new doctrine surfaces.

Each skill should:
- own one bounded repeatable process
- stay lean
- point to active owner docs/scripts
- avoid broad freeform interpretation when the process is fragile

For brain-update work, the desired freedom level is mostly low-to-medium.

## 4) Minimum priority skill stack

### S0) Thread closeout auditor skill

Purpose:
- stop overlong worker threads cleanly and emit a reusable controller packet

Must do:
1. force the thread into closeout-audit mode
2. classify the lane:
   - healthy/stop
   - healthy/one-more-step
   - stalled
   - duplicate
   - drifted
   - metadata-polish-only
   - waiting-on-external
3. collect strongest reusable outputs
4. emit stop/continue/correct decision
5. emit a small handoff packet

Why first:
- if worker lanes do not stop cleanly, every other skill gets buried under long-thread churn
- this is now a direct control problem, not just a convenience improvement

### S1) A2 brain refresh skill

Purpose:
- run the A2-brain-first refresh loop in the correct order

Must do:
1. load active A2 control surfaces
2. classify touched surfaces
3. detect stale-A2 vs active-repo drift
4. emit bounded A2 update notes
5. append safely into active A2 surfaces
6. emit off-process flags when the loop was bypassed

Why first:
- without this, every later skill is built on stale or inconsistent A2

### S2) A1-from-A2 distillation skill

Purpose:
- derive proposal-only A1 outputs from refreshed A2

Must do:
1. require explicit A2 input surfaces
2. forbid direct source -> A1 shortcuts
3. emit proposal-only A1 outputs
4. preserve traceability back to refreshed A2
5. flag when requested work is actually A2 work, not A1 work

Why second:
- current A1 quality depends on whether the operator manually re-imposes the A2-first discipline

### S3) A2/A1 memory admission guard skill

Purpose:
- audit or gate append/update candidates before they are allowed into A2/A1 active memory surfaces

Must check:
- surface class
- schema/provenance
- source refs
- proposal vs earned-state hygiene
- source-vs-derived precedence
- active-owner targeting

Why third:
- best intentions do not stop semantic elevation drift
- brain updates need structure, not only awareness

### S4) External research refinery launcher skill

Purpose:
- build and launch bounded external-research ZIP jobs with narrow boots

Must do:
- instantiate the correct ZIP_JOB template/dropin
- fill the topic brief
- build the narrow Pro boot
- keep active-vs-derived scope explicit
- emit the exact send text / controller boot plan

Why fourth:
- this new refinery lane will create a lot of thread churn if it is not callable and repeatable

### S5) Pro-return instant audit skill

Purpose:
- audit returned Pro/deep-research material before A2 ingestion

Must check:
- citation quality
- overclaim / smoothing
- ontology smuggling
- process-vs-math confusion
- missing adjacent lines
- `usable now / after retool / reject` discipline

Why fifth:
- external research is useful only if the audit pass is systematic

### S6) Brain delta consolidation skill

Purpose:
- turn many bounded outputs into a small number of append-safe A2/A1 deltas

Must do:
- merge without contradiction smoothing
- keep source anchors
- separate:
  - A2 updates
  - A1 impacts
  - unresolved tensions
  - hold/revisit items

Why sixth:
- otherwise the system keeps generating raw packets without reliably strengthening the persistent brains

## 5) Strong recommendation

Do not try to build every possible skill first.

Build the first four as the control spine:
- `thread closeout auditor`
- `A2 brain refresh`
- `A1 from A2 distillation`
- `A2/A1 memory admission guard`

Then build the two external-refinery skills:
- `external research refinery launcher`
- `Pro-return instant audit`

Then build consolidation.

## 6) Scripts vs text

These skills should not be pure prose if a deterministic scriptable step already exists.

Prefer:
- SKILL.md = routing, sequence, guardrails
- repo docs = authority surfaces
- scripts = deterministic execution steps

That means the skills should call or point at:
- active A2 owner surfaces
- active ZIP-job tooling
- validators/builders
- bounded audit scripts where they exist

## 7) Bottom line

The skill layer is now a real bottleneck.

The problem is not that the system lacks A2/A1 theory.
The problem is that the repeatable upper-loop brain-update processes are not yet packaged into stable callable skills.

The minimum fix is not "more agent architecture."

It is:
- one small skill stack that makes:
  - A2 refresh
  - A1 derivation
  - memory admission
  - external research launch
  - external research audit
  - delta consolidation

callable, bounded, and consistent.
