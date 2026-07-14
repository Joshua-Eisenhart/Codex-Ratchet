export const fullSurfaceCampaignEval = {
  id: 'codex-ratchet-full-surface-campaign',
  target: './target.md',
  flowmind: './flow.yaml',
  fixtures: {},
  greenChecks: [
    'source-backed producers execute in disposable staging directories',
    'commands, logs, source bytes, archive members, and artifacts are hash-bound',
    'validator accepts the authentic receipt and an honest scientific demotion',
    'Lev zero-execution mode blocks instead of projecting a false green',
  ],
  redChecks: [
    'execution completion cannot become scientific admission',
    'provider advice cannot become evidence',
    'partial-promotion, projection-only, replay, and fabrication aliases reject',
    'known H, ALCO, physlib, hardcoded-write, and consumer gaps remain visible',
  ],
  commandCases: [
    {
      id: 'execute-full-source-backed-surface',
      commandLine: '/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -B system_v5/ops/tooling/claude_campaign_20260713/full_surface/run_full_surface.py --archive "/Users/joshuaeisenhart/Desktop/166_reconciled_ratchet_v0_11_7_cold_verified (1).zip" --output system_v5/ops/tooling/claude_campaign_20260713/full_surface/results/full_surface_lev_envelope.json --artifact-dir system_v5/ops/tooling/claude_campaign_20260713/full_surface/results/artifacts/full-surface-ab211e8c-run1',
      expectedExit: 'zero',
      stdoutContains: [
        '"runner_all_completed": true',
        '"all_pass": false',
      ],
    },
    {
      id: 'validate-authentic-envelope',
      commandLine: '/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -B system_v5/ops/tooling/claude_campaign_20260713/full_surface/validate_full_surface.py system_v5/ops/tooling/claude_campaign_20260713/full_surface/results/full_surface_lev_envelope.json',
      expectedExit: 'zero',
      stdoutContains: '"ok": true',
    },
    {
      id: 'run-fabrication-and-demotion-controls',
      commandLine: '/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -B system_v5/ops/tooling/claude_campaign_20260713/full_surface/test_validate_full_surface.py system_v5/ops/tooling/claude_campaign_20260713/full_surface/results/full_surface_lev_envelope.json',
      expectedExit: 'zero',
      stdoutContains: [
        '"baseline_accepts": true',
        '"accepted": true',
        '"all_pass": true',
      ],
    },
    {
      id: 'lev-zero-execution-blocks',
      commandLine: 'bun /Users/joshuaeisenhart/lev-main/.worktrees/eval-projection-contract/core/poly/bin/lev eval run system_v5/ops/tooling/claude_campaign_20260713/full_surface/lev/zero_execution.eval.js --execute --json --project-root /Users/joshuaeisenhart/.config/superpowers/worktrees/Codex-Ratchet/claude-integration-hardening-20260713 --output-root system_v5/ops/tooling/claude_campaign_20260713/full_surface/results/lev_zero_runs --run-id full-surface-zero-ab211e8c-run1',
      expectedExit: 'nonzero',
      stdoutContains: [
        'suite.execution.none',
        '"status": "blocked"',
        '"projection_only": true',
        '"release_eligible": false',
      ],
    },
  ],
};

export default fullSurfaceCampaignEval;
