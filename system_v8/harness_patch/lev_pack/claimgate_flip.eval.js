// Codex-Ratchet side eval pack. Lives OUTSIDE ~/lev-main (read-only), and is
// run zero-touch via:  lev eval run <abs-path>/claimgate_flip.eval.js --json
export default {
  id: 'claimgate-flip-battery-eval',
  target: './companions/flip_sensor.mjs',
  flowmind: './flows/score.flow.yaml',
  fixtures: {
    evidence: './fixtures/flip_evidence.trace.json',
  },
  greenChecks: [
    'real z3 + JAX flip-battery measurements are present for a candidate and a negative control',
    'the mechanism-dependency question is decided by the scorer, not by the receipt',
  ],
  redChecks: [
    'provider evidence cannot carry its own verdict or an evaluated status',
    'a battery whose negative control also passes is refused as non-discriminating',
    'a decorative/tautological encoding (flip_rate at or below threshold) cannot be admitted',
  ],
  traceCases: [{
    id: 'flip-battery-real-vs-control',
    claim: 'Stage order is load-bearing in the Type-1 deductive engine loop, and the commuting control is not.',
    subjectFixture: 'evidence',
    expectations: {
      schema: 'lev.claimgate_flip_battery.trace.v1',
      subject_ref: 'codex-ratchet:system_v8/harness_patch/flip_harness.py',
      observable_name: 'flip_rate',
      tolerance: 0,
    },
  }],
};
