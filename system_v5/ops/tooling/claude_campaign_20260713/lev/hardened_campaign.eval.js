import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const suiteDir = dirname(fileURLToPath(import.meta.url));
const ratchetRoot = resolve(suiteDir, '../../../../..');
const hardened = `${ratchetRoot}/system_v5/ops/tooling/claude_campaign_20260713/hardened`;
const python = '/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3';
const archive = process.env.CODEX_RATCHET_PACKET_166
  ?? '/Users/joshuaeisenhart/Desktop/166_reconciled_ratchet_v0_11_7_cold_verified (1).zip';
const envelope = `${hardened}/results/hardened_campaign_v2_envelope.json`;

export default {
  id: 'codex-ratchet-hardened-claude-campaign-v2',
  target: './hardened_campaign_target.md',
  flowmind: './hardened_campaign_flow.yaml',
  fixtures: {},
  greenChecks: [
    'all five bounded producers execute and rewrite source-hashed receipts',
    'the dedicated campaign envelope validates fail-closed',
    'fabricated promotion, green, completion, and hash claims are rejected',
  ],
  redChecks: [
    'campaign all_pass remains false',
    'H remains a cycle observation with unresolved ancestry semantics, not an admitted integrity defect',
    'no Lev graph mutation or scientific promotion is emitted',
  ],
  commandCases: [
    {
      id: 'run-hardened-campaign',
      command: python,
      argv: [
        `${hardened}/run_hardened_campaign_v2.py`,
        '--archive',
        archive,
        '--output',
        envelope,
      ],
      cwd: ratchetRoot,
      expectedExitCode: 0,
      stdoutContains: ['"runner_all_completed": true', '"all_pass": false'],
    },
    {
      id: 'validate-hardened-envelope',
      command: python,
      argv: [`${hardened}/validate_hardened_campaign_v2.py`, envelope],
      cwd: ratchetRoot,
      expectedExitCode: 0,
      stdoutContains: '"ok": true',
    },
    {
      id: 'reject-fabricated-campaign-claims',
      command: python,
      argv: ['-B', `${hardened}/test_validate_hardened_campaign_v2.py`],
      cwd: ratchetRoot,
      expectedExitCode: 0,
      stdoutContains: ['"all_pass": true', '"forged_promotion_eligibility"'],
    },
  ],
};
