---
name: karpathy-bounded-improve
description: Use only as a small support loop when improving one Codex skill, prompt, script, or artifact is too narrow for `$codex-autoresearch`; primary Karpathy-inspired Codex execution remains `$codex-autoresearch`, with councils handled by existing council skills.
---

# Karpathy Bounded Improve

Use this for one small improvement target when `$codex-autoresearch` would be too much machinery. The pattern is: mutate, evaluate, keep or discard, repeat under a finite cap. It is not permissionless self-mutation, not a replacement for `$codex-autoresearch`, and not an LLM council surface.

Local source pattern:

```text
/Users/joshuaeisenhart/.agents/skills/codex-autoresearch/SKILL.md
/Users/joshuaeisenhart/.agents/skills/tribunal/SKILL.md
system_v4/skills/bounded_improve_operator.py
system_v4/skill_specs/skill-improver-operator/SKILL.md
```

Use the existing surfaces first:

- `$codex-autoresearch` for autonomous long-running improve-verify loops.
- `tribunal`, `cdo`, or Wizard councils for independent LLM council/adjudication work.
- this support skill only for a finite local mutate-evaluate-keep pass on one declared target.

## Step 1: Pick One Target

Define:

```yaml
target_path:
artifact_type: skill | script | prompt | reference | test
allowed_write: true | false
round_cap:
score_function:
acceptance_test:
stop_condition:
```

Validation: `target_path`, `round_cap`, `score_function`, and `acceptance_test` are non-empty before any edit.

On failure: stop and ask only if the missing value is preference-bound.

## Step 2: Establish Baseline

Read the current target and run the acceptance test before mutation.

For a skill:

```bash
python3 /Users/joshuaeisenhart/.codex-second/skills/.system/skill-creator/scripts/quick_validate.py <skill-dir>
```

For the local bounded loop source:

```bash
python3 -m system_v4.skills.bounded_improve_operator
```

Validation: baseline result is recorded as `baseline_score` and `baseline_test`.

On failure: decide whether the job is repair or improvement; do not hide the red baseline.

## Step 3: Mutate One Thing

A mutation changes one bounded aspect:

- trigger description;
- read order;
- validation command;
- authority boundary;
- role card;
- test fixture;
- deterministic script behavior.

Do not mutate broad doctrine, git state, registries, or shared queues in this loop.

Validation: mutation diff touches only the declared target and one aspect.

On failure: discard the mutation.

## Step 4: Evaluate

Evaluate against the declared score and acceptance test. Keep a mutation only if it improves the score and does not fail hard gates.

Score examples:

- fewer missing inventory gaps;
- skill validator passes after failing before;
- test count passes;
- source family matrix now covers a real source;
- role card now blocks a known failure mode.

Validation: every kept change has `score_before`, `score_after`, and test result.

On failure: revert or discard the candidate; do not rationalize it as progress.

## Step 5: Stop

Stop when:

- `round_cap` is reached;
- no mutation improves the score;
- the next mutation requires owner preference;
- the next mutation widens target scope;
- a write needs approval or would touch non-writable surfaces.

Validation: final report names kept and discarded mutations.

On failure: mark the loop incomplete, not done.

## Step 6: Report

Return:

```yaml
target_path:
rounds:
kept_mutations:
discarded_mutations:
baseline_test:
final_test:
final_score:
status: improved | unchanged | blocked
promotion_boundary:
```

A successful bounded improve loop means the target improved under its local score. It does not mean the skill is canonical, globally correct, or proven by user behavior unless a separate usage test proves that.
