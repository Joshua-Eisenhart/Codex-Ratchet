export const zeroExecutionEval = {
  id: 'codex-ratchet-deep-stack-zero-execution-control',
  target: './target.md',
  flowmind: './flow.yaml',
  fixtures: {},
  greenChecks: [
    'projection without an executed command case is explicitly blocked',
  ],
  redChecks: [
    'zero executed command cases cannot validate tool integration or earn a green projection',
  ],
};

export default zeroExecutionEval;
