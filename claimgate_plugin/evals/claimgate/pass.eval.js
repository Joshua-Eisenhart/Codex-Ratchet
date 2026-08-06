import { readFileSync, unlinkSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { score } from './companions/sensor.mjs';

const here = dirname(fileURLToPath(import.meta.url));
const fixturePath = join(here, 'fixtures/engine-leg-field-only.receipt.json');
const fixture = JSON.parse(readFileSync(fixturePath, 'utf8'));

const verified = score({ receipt_path: fixturePath });
assertResult(verified, {
  passed: true,
  disposition: 'verified',
  exitCode: 0,
});

const forbiddenCases = ['all_pass', 'promotion_allowed', 'verdict', 'gate_proof'];
for (const field of forbiddenCases) {
  const hostilePath = join(here, 'fixtures', `.claimgate-hostile-${field}.json`);
  const hostile = { ...fixture, evidence: { ...fixture.evidence, [field]: false } };
  writeFileSync(hostilePath, `${JSON.stringify(hostile, null, 2)}\n`, 'utf8');
  try {
    const rejected = score({ receipt_path: hostilePath });
    assertResult(rejected, {
      passed: false,
      disposition: 'rejected',
      exitCode: 1,
      providerVerdictBitsPresent: true,
    });
  } finally {
    try { unlinkSync(hostilePath); } catch {}
  }
}

const unclassifiedPath = join(here, 'fixtures', '.claimgate-unclassified.json');
writeFileSync(
  unclassifiedPath,
  `${JSON.stringify({ ...fixture, claim_kind: 'unclassified_fixture_claim' }, null, 2)}\n`,
  'utf8',
);
try {
  const insufficient = score({ receipt_path: unclassifiedPath });
  assertResult(insufficient, {
    passed: false,
    disposition: 'insufficient_depth',
    exitCode: 3,
  });
} finally {
  try { unlinkSync(unclassifiedPath); } catch {}
}

export default {
  id: 'claimgate-pass-trace-eval',
  target: './companions/sensor.mjs',
  flowmind: './flows/measure.flow.yaml',
  fixtures: {
    trace: './fixtures/engine-leg-field-only.receipt.json',
  },
  greenChecks: [
    'claim_verify exit 0 is accepted only with exact verdict VERIFIED',
    'a classified verdict-free engine-leg receipt is evaluated by ClaimGate',
  ],
  redChecks: [
    'provider evidence carrying all_pass, promotion_allowed, verdict, or gate_proof is rejected',
    'exit 3 and unclassified receipts are INSUFFICIENT_DEPTH, never green',
  ],
  traceCases: [{
    id: 'verified-field-only-fixture',
    claim: 'A verdict-free classified receipt maps claim_verify exit 0 and exact VERIFIED to a passing evaluator result.',
    subject: verified,
    expectations: {
      schema: 'lev.evaluator.result.v1',
      evaluator_id: 'claimgate',
      passed: true,
      decision: 'pass',
      'measurements.variables.claim_verify_exit_code.value': 0,
      'measurements.variables.disposition.value': 'verified',
    },
  }],
};

function assertResult(result, expected) {
  const variables = result?.measurements?.variables ?? {};
  const actual = {
    passed: result?.passed,
    disposition: variables.disposition?.value,
    exitCode: variables.claim_verify_exit_code?.value,
    providerVerdictBitsPresent: variables.provider_verdict_bits_present?.value,
  };
  for (const [key, value] of Object.entries(expected)) {
    if (!Object.is(actual[key], value)) {
      throw new Error(`ClaimGate suite self-check failed: ${key}=${JSON.stringify(actual[key])}, expected ${JSON.stringify(value)}`);
    }
  }
}
