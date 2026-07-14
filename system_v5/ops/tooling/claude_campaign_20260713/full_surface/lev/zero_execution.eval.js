export const zeroExecutionEval = {
  id: 'codex-ratchet-zero-execution-control',
  target: './target.md',
  flowmind: './flow.yaml',
  fixtures: {},
  greenChecks: ['projection without execution is explicitly blocked'],
  redChecks: ['zero executed command cases cannot pass'],
};

export default zeroExecutionEval;
