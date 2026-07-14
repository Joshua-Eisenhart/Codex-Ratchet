# Codex-native skill-validator provenance lane

This lane tests one narrow proposition: whether the repo-held
`codex-ratchet-tool-status-auditor` validator is both hash-bound and actually
executed by an independent Lev evaluator.

## Evidence split

- `fixtures/guidance_subject_sidecar.json` is a valid guidance-only subject.
  Its deterministic verdict is L2 and not L3-eligible.
- `fixtures/authentic_l3_eligible_sidecar.json` records the exact
  `validate-guidance-subject` command, the current repo skill and validator
  hashes, and the deterministic output artifact hash. The repo validator
  accepts it as `l3_eligible: true` but caps the sidecar itself at L2.
- `fixtures/tampered_stale_hash_sidecar.json` changes only the declared
  executable-validator hash to zeroes. It must fail closed as `BLOCKED`.
- A fresh Lev scorecard at executor commit
  `856acb1a5de42528a9a54272435d98a9fe226186` independently executes the exact
  `validate-guidance-subject` case and hashes stdout and stderr. That scorecard
  is the only L3 evidence in this lane, and only for execution of
  `validate_skills_used.py`.

The scorecard does not raise the guidance declaration above L2. It does not
prove that an engine skill ran, that any downstream tool API was load-bearing,
or that a scientific claim passed. Lev reports it as projection-only and
release-ineligible.

## Pre-run local checks

Run these before committing the stable suite bytes:

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -B \
  system_v5/codex_skills/codex-ratchet-tool-status-auditor/scripts/validate_skills_used.py \
  system_v5/ops/tooling/claude_campaign_20260713/skill_provenance/fixtures/authentic_l3_eligible_sidecar.json \
  --repo-root .

/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -B -m pytest \
  system_v5/tests/test_tool_status_skill_provenance.py -q
```

The stale-hash control is expected to exit nonzero:

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -B \
  system_v5/codex_skills/codex-ratchet-tool-status-auditor/scripts/validate_skills_used.py \
  system_v5/ops/tooling/claude_campaign_20260713/skill_provenance/fixtures/tampered_stale_hash_sidecar.json \
  --repo-root .
```

## Post-commit Lev run

Do not run this command until every source and fixture named by the suite is
committed and clean. The run ID is unique to this lane:

```bash
bun /Users/joshuaeisenhart/lev-main/.worktrees/eval-projection-contract/core/poly/bin/lev eval run \
  system_v5/ops/tooling/claude_campaign_20260713/skill_provenance/lev/skill_provenance.eval.js \
  --execute --json \
  --project-root /Users/joshuaeisenhart/.config/superpowers/worktrees/Codex-Ratchet/claude-integration-hardening-20260713 \
  --output-root system_v5/ops/tooling/claude_campaign_20260713/skill_provenance/results/lev_eval_runs \
  --run-id skill-provenance-validator-856acb1a5-run1
```

Accept the result only if `run.json` reports `status: projected`,
`suite_status: passed`, `projection_only: true`, and
`release_eligible: false`, and the scorecard reports six executed cases, zero
failures, twelve hash-bound stdout/stderr artifact references, and the exact
case ID `validate-guidance-subject`.
