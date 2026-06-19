---
name: codex-skill-agent-upgrader
description: Use when improving Codex skills, agents, role prompts, or workflow skills from the current Codex skill homes, repo skill specs, Claude agents/skills, Hermes rules, or Wizard packet-local skills without treating external runtime material as authority.
---

# Codex Skill Agent Upgrader

Use this skill to make the Codex skill and agent layer better from observed sources. Do not start by inventing a new skill. Inventory first, classify sources, then port the smallest useful mechanic. Treat `$codex-autoresearch` as the primary Karpathy-inspired Codex loop surface, and treat `tribunal`, `cdo`, and Wizard councils as existing council surfaces unless the inventory proves a concrete adapter gap.

## Step 1: Inventory

Run:

```bash
python3 scripts/codex_skill_agent_inventory.py --out /tmp/codex_skill_agent_inventory.json
```

Validation: the JSON has `sections.codex_installed`, `sections.agents_installed`, `sections.repo_codex_skills`, `sections.claude_skills`, `sections.system_v4_skill_specs`, `hermes_installed`, `wiki_surfaces`, `claude_agents`, and `upgrade_gaps`.

On failure: fix the inventory script or path issue before editing any skill.

## Step 2: Read Authority

For Codex Ratchet, read in this order:

1. `AGENTS.md`
2. `CODEX.md`
3. `system_v5/docs/ENFORCEMENT_AND_PROCESS_RULES.md`
4. `system_v5/docs/LLM_CONTROLLER_CONTRACT.md`
5. `system_v5/docs/LEGO_SIM_CONTRACT.md`

Validation: every accepted upgrade cites which authority surface controls it.

On failure: keep the source as `reference_only`; do not install or patch active skills.

## Step 3: Classify Source Family

Use `references/source_family_matrix.md`.

Allowed source families:

- installed Codex skill;
- installed `.agents` skill;
- repo-held Codex skill source;
- Wizard packet-local skill;
- Claude skill;
- Claude agent;
- Hermes rule or bounded-intake doc;
- Hermes installed skill;
- Hermes wiki spine or wiki receipt;
- `system_v4/skill_specs` skill spec;
- `system_v4/skills` executable operator;
- Karpathy-family reference, `$codex-autoresearch`, or bounded-improve support operator;
- user correction.

Validation: every source path has `family`, `authority_status`, `accepted_pattern`, `target_surface`, and `minimal_test`.

On failure: reject the source for this pass.

## Step 4: Extract Pattern Cards

For every candidate mechanic, write a compact card:

```yaml
source_path:
family:
pattern_name:
problem_solved:
mechanism:
port_as: skill | workflow | role_card | script | test | reject
target_path:
authority_reason:
risk:
minimal_test:
status:
```

Favor patterns that improve repeated execution: inventory, bounded intake, role separation, gate running, artifact status labels, source locks, independent audits, and receipt truth.

Reject patterns that import Claude/Hermes as authority, claim fake subagents, merge builder and auditor roles, hide stale gates, or promote sim/proof status without repo evidence.

Validation: each accepted card has a concrete target path and a command or file-read test.

On failure: demote to `reference_only`.

## Step 5: Pick Target Surface

Use the smallest target that can run:

- `system_v5/codex_skills/<name>/`: repo-held Codex skill source.
- `$CODEX_HOME/skills/<name>/`: active installed Codex skill, only after repo source validates.
- `references/*.md`: role cards, source matrices, or prompt templates.
- `scripts/*.py`: deterministic inventory, validation, or packaging.
- `system_v5/tests/*.py`: focused tests for scripts or validators.

Do not patch broad authority docs unless the user explicitly asks for doctrine changes.

Validation: target path matches the port type and is not a bulk rewrite.

On failure: stop before writing.

## Step 6: Validate

For every skill created or patched:

```bash
python3 /Users/joshuaeisenhart/.codex-second/skills/.system/skill-creator/scripts/quick_validate.py <skill-dir>
```

For inventory/script changes:

```bash
python3 -m pytest system_v5/tests/test_codex_skill_agent_inventory.py
```

For Wizard v4.3 changes:

```bash
python3 scripts/wizard_v4_3_object_preservation.py selftest --out /tmp/v43_selftest.json
```

Validation: each command exits 0, or the final report names the failing command and blocker.

On failure: do not report the upgrade as installed or usable.

## Step 7: Report

Return:

- accepted patterns;
- rejected patterns;
- files changed;
- installed skills, if any;
- validation commands and results;
- remaining gaps from the inventory.

Use status labels honestly: `exists`, `runs`, `passes local rerun`, or `canonical by process` where applicable. A skill validator pass means the skill file is structurally valid, not that the behavior is proven.
