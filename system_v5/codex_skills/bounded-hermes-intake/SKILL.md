---
name: bounded-hermes-intake
description: Use when converting Hermes wiki work, Hermes skills, wiki receipts, or wiki maintenance requests into a bounded Codex-readable intake pack without treating Hermes or the wiki as Codex authority.
---

# Bounded Hermes Intake

Use this when Hermes wiki work or Hermes skills should inform Codex. The wiki is the long-form frame and memory surface; skills are procedures. Do not read the whole wiki and do not copy Hermes behavior law into Codex.

## Step 1: Inventory The Source

Run the Codex inventory:

```bash
python3 scripts/codex_skill_agent_inventory.py --out /tmp/codex_skill_agent_inventory.json
```

Validation: the JSON includes `hermes_installed` and `wiki_surfaces`.

On failure: fix inventory paths before accepting any Hermes/wiki source claim.

## Step 2: Read The Hermes Spine

For substantive wiki/Hermes work, read:

1. `/Users/joshuaeisenhart/wiki/hermes-current/read-first.md`
2. `/Users/joshuaeisenhart/wiki/hermes-current/skills-and-agent-rules.md`
3. `/Users/joshuaeisenhart/wiki/hermes-current/current-vs-legacy.md`
4. `/Users/joshuaeisenhart/wiki/hermes-current/active-intentions.md` when priorities matter.

Validation: every accepted pattern names which spine note controlled it.

On failure: mark the source `reference_only`.

## Step 3: Build A Bounded Pack

Every Hermes/wiki intake pack must include:

```yaml
purpose:
role:
frame:
read_order:
do_not_read:
questions:
required_output:
promotion_rule:
target_codex_surface:
minimal_test:
```

Valid roles include `audit_reader`, `bounded_synthesizer`, `skills_planner`, `wiki_router`, `skill_patch_scout`, and `reference_repo_classifier`.

Validation: all fields are non-empty and the read order is finite.

On failure: do not proceed with broad reading.

## Step 4: Preserve Authority Boundaries

Treat these as source/reference unless a current Codex repo rule says otherwise:

- `/Users/joshuaeisenhart/wiki/hermes-current/*`
- `/Users/joshuaeisenhart/wiki/wizard/hermes-version-current/*`
- `/Users/joshuaeisenhart/.hermes/skills/*`
- Hermes worker receipts and wiki run receipts.

Hermes may reveal useful mechanics: bounded intake, wiki probe checks, maintenance governance, subagent ledgers, memory-preserve-before-compress, and skill patch after real failure. Port mechanics, not authority.

Validation: each accepted mechanic has `authority_reason` and `promotion_boundary`.

On failure: reject the mechanic for active Codex skill changes.

## Step 5: Verify Wiki Claims

When a claim is about wiki structure, run or cite a current probe. Prefer:

```bash
python3 /Users/joshuaeisenhart/wiki/tools/wiki_probe.py --wiki-root /Users/joshuaeisenhart/wiki --output /tmp/wiki_probe.json
```

If that tool is unavailable, use direct file reads and say the check is file-read only.

Validation: a claim like `CLEAN`, missing pages, or broken links names the current probe output or readback evidence.

On failure: keep the wiki claim at `exists` or `observed in note`, not verified-current.

## Step 6: Port The Smallest Useful Artifact

Allowed Codex targets:

- repo-held skill source under `system_v5/codex_skills/`;
- installed active skill under `$CODEX_HOME/skills/` after validation;
- role cards or source matrices under `references/`;
- deterministic inventory or probe scripts under `scripts/`;
- tests under `system_v5/tests/`.

Do not edit `/Users/joshuaeisenhart/wiki` from this skill unless the user explicitly asks for wiki edits and the path is writable/approved.

Validation: target path and minimal test are named before writing.

On failure: return a bounded pack only.

## Step 7: Report

Return:

- source paths read;
- bounded pack fields;
- accepted mechanics;
- rejected mechanics;
- Codex edits made;
- validation commands and results;
- remaining wiki/Hermes questions.

Do not report a Hermes skill, worker, or Wizard run as executed unless a current receipt or local validation proves it.
