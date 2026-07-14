const lane = 'system_v5/ops/tooling/claude_campaign_20260713/skill_provenance';
const validator =
  'system_v5/codex_skills/codex-ratchet-tool-status-auditor/scripts/validate_skills_used.py';
const python = '/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3';

export const skillProvenanceEval = {
  id: 'codex-ratchet-skill-validator-provenance',
  target: './target.md',
  flowmind: './flow.yaml',
  fixtures: {},
  greenChecks: [
    'the exact Lev executor commit is recorded before evidence execution',
    'the committed lane bytes are clean and present at the recorded Ratchet HEAD',
    'the sidecar-declared validator command executes under the same command case ID',
    'the authentic executable-validator sidecar is l3-eligible but remains capped at L2',
    'all 12 focused adversarial validator tests execute and pass',
    'a stale executable-validator hash is rejected with a blocked verdict',
  ],
  redChecks: [
    'the self-reported sidecar alone cannot earn L3',
    'the external scorecard cannot promote guidance declarations above L2',
    'validator execution cannot prove an engine skill or tool API was load-bearing',
    'validator execution cannot discharge or promote a scientific claim',
    'the scorecard is projection-only and release-ineligible',
  ],
  commandCases: [
    {
      id: 'verify-bound-lev-executor-head',
      commandLine:
        'git -C /Users/joshuaeisenhart/lev-main/.worktrees/eval-projection-contract rev-parse HEAD',
      expectedExit: 'zero',
      stdoutContains: '856acb1a5de42528a9a54272435d98a9fe226186',
    },
    {
      id: 'verify-committed-lane-source-bytes',
      commandLine:
        `git diff --quiet HEAD -- ${lane} && git ls-files --error-unmatch ` +
        `${lane}/README.md ` +
        `${lane}/fixtures/authentic_l3_eligible_sidecar.json ` +
        `${lane}/fixtures/guidance_subject_sidecar.json ` +
        `${lane}/fixtures/guidance_subject_verdict.json ` +
        `${lane}/fixtures/tampered_stale_hash_sidecar.json ` +
        `${lane}/lev/flow.yaml ` +
        `${lane}/lev/skill_provenance.eval.js ` +
        `${lane}/lev/target.md >/dev/null && git rev-parse HEAD`,
      expectedExit: 'zero',
    },
    {
      id: 'validate-guidance-subject',
      commandLine:
        `${python} -B ${validator} ` +
        `${lane}/fixtures/guidance_subject_sidecar.json ` +
        `--repo-root . --out ${lane}/fixtures/guidance_subject_verdict.json`,
      expectedExit: 'zero',
      stdoutContains: [
        '"all_pass": true',
        '"l3_eligible": false',
        '"max_skill_provenance_level": "L2"',
        'no executable or scientific evidence',
      ],
    },
    {
      id: 'confirm-authentic-sidecar-ceiling',
      commandLine:
        `${python} -B ${validator} ` +
        `${lane}/fixtures/authentic_l3_eligible_sidecar.json ` +
        `--repo-root . --out ${lane}/results/authentic_l3_eligible_verdict.json`,
      expectedExit: 'zero',
      stdoutContains: [
        '"all_pass": true',
        '"external_runner_receipt_required": true',
        '"l3_eligible": true',
        '"max_skill_provenance_level": "L2"',
        'requires an independent hash-bound runner receipt for actual L3',
      ],
    },
    {
      id: 'run-12-focused-adversarial-tests',
      commandLine:
        `${python} -B -m pytest system_v5/tests/test_tool_status_skill_provenance.py -q`,
      expectedExit: 'zero',
      stdoutContains: '12 passed',
    },
    {
      id: 'reject-stale-executable-validator-hash',
      commandLine:
        `${python} -B ${validator} ` +
        `${lane}/fixtures/tampered_stale_hash_sidecar.json --repo-root .`,
      expectedExit: 'nonzero',
      stdoutContains: [
        '"all_pass": false',
        '"l3_eligible": false',
        '"max_skill_provenance_level": "BLOCKED"',
        'does not match current bytes',
      ],
    },
  ],
};

export default skillProvenanceEval;
