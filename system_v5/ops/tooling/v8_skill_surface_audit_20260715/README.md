# V8 skill surface audit

This is a deterministic, read-only inventory of ten Codex Ratchet sim/control
skills across the repo-held source, `/Users/joshuaeisenhart/.codex/skills`, and
`/Users/joshuaeisenhart/.agents/skills`.

The auditor itself does not install or edit active skills. The current receipt
records two bounded repairs made before its final rerun and preserves the
remaining blocking facts:

- `codex-ratchet-sim-audit-spine` now has an exact repo/active Codex source,
  with active-checkout resolution replacing the hardcoded owner checkout;
- `codex-ratchet-deep-stack-stress` repo/active Codex wording and checkout
  runner path are now exact;
- the tested repo `claude-bridge` candidate is not installed;
- repo/Codex operational-body drift is not normalized except for one exact,
  enumerated source-family preamble used by five engine/stewardship skills;
- no skill or provider output receives gate, promotion, launch, or science
  authority.

Run from the repository root:

```bash
BASE=system_v5/ops/tooling/v8_skill_surface_audit_20260715
python3 "$BASE/audit_skill_surface.py" \
  --repo-root "$PWD" \
  --json-out "$BASE/results/skill_surface_audit.json" \
  --markdown-out "$BASE/results/SKILL_SURFACE_AUDIT.md"
python3 "$BASE/validate_skill_surface.py" \
  "$BASE/results/skill_surface_audit.json" \
  --out "$BASE/results/validation.json"
python3 "$BASE/run_mutation_tests.py" \
  "$BASE/results/skill_surface_audit.json" \
  --out "$BASE/results/mutation_tests.json"
python3 -m unittest discover -s "$BASE/tests" -p 'test_*.py' -v
```

Implementation levels are deliberately narrow:

- `guidance_only`: no local deterministic validator is present;
- `validator_backed`: validator present, no local runner;
- `runner_and_validator`: both present, no focused tests in that skill;
- `tested_candidate`: runner, validator, and focused tests are all present.

Runner-only installed surfaces remain `guidance_only` with an explicit
`runner_without_local_validator` gap; a runner does not certify itself.
