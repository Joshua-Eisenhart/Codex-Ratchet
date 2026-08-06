import { spawnSync } from 'node:child_process';
import { readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const EVALUATOR_ID = 'claimgate';
const RECEIPT_SCHEMA = 'codex_ratchet.engine_leg_result.v1';
const FORBIDDEN_PROVIDER_FIELDS = new Set([
  'all_pass',
  'promotion_allowed',
  'verdict',
  'gate_proof',
]);
const HERE = dirname(fileURLToPath(import.meta.url));
const CLAIM_VERIFY = resolve(HERE, '../../../claim_verify.py');

export function score(input) {
  const receiptPath = receiptPathFrom(input);
  if (!receiptPath) {
    return result('evaluation_error', 2, 'receipt_path is required', false);
  }

  let receipt;
  try {
    receipt = JSON.parse(readFileSync(receiptPath, 'utf8'));
  } catch (error) {
    return result('evaluation_error', 2, `receipt could not be read as JSON: ${error.message}`, false);
  }

  if (!isRecord(receipt) || receipt.schema !== RECEIPT_SCHEMA) {
    return result('evaluation_error', 2, `receipt schema must equal ${RECEIPT_SCHEMA}`, false);
  }

  const forbidden = forbiddenFields(receipt);
  if (forbidden.length > 0) {
    return result(
      'rejected',
      1,
      `provider evidence contains forbidden verdict field(s): ${forbidden.join(', ')}`,
      true,
    );
  }

  const invocation = invokeClaimVerify(receiptPath);
  if (invocation.error) {
    return result('evaluation_error', 2, invocation.error, false);
  }

  const report = parseReport(invocation.stdout);
  if (!report.ok) {
    return result('evaluation_error', 2, report.reason, false);
  }

  if (invocation.exitCode === 0 && report.value.verdict === 'VERIFIED') {
    return result('verified', 0, 'claim_verify returned exit 0 and exact verdict VERIFIED', false, report.value);
  }
  if (invocation.exitCode === 1 && report.value.verdict === 'REJECTED') {
    return result('rejected', 1, 'claim_verify returned REJECTED', false, report.value);
  }
  if (invocation.exitCode === 3 && report.value.verdict === 'INSUFFICIENT_DEPTH') {
    return result('insufficient_depth', 3, 'claim_verify returned INSUFFICIENT_DEPTH', false, report.value);
  }
  if (invocation.exitCode === 2) {
    return result('evaluation_error', 2, 'claim_verify returned an error', false, report.value);
  }

  return result(
    'evaluation_error',
    2,
    `claim_verify exit/verdict mismatch: exit=${invocation.exitCode}, verdict=${String(report.value.verdict)}`,
    false,
    report.value,
  );
}

function invokeClaimVerify(receiptPath) {
  const child = spawnSync(
    'python3',
    [CLAIM_VERIFY, receiptPath, '--json'],
    {
      cwd: resolve(HERE, '../../../..'),
      timeout: 900_000,
      maxBuffer: 8 * 1024 * 1024,
      encoding: 'utf8',
    },
  );
  if (child.error) return { error: `claim_verify could not be executed: ${child.error.message}` };
  return {
    exitCode: child.status,
    stdout: child.stdout ?? '',
    stderr: child.stderr ?? '',
  };
}

function parseReport(stdout) {
  try {
    const value = JSON.parse(stdout);
    return isRecord(value) && typeof value.verdict === 'string'
      ? { ok: true, value }
      : { ok: false, reason: 'claim_verify JSON omitted a string verdict' };
  } catch (error) {
    return { ok: false, reason: `claim_verify output was not JSON: ${error.message}` };
  }
}

function result(disposition, exitCode, reason, providerVerdictBitsPresent, report = undefined) {
  const passed = disposition === 'verified';
  return {
    schema: 'lev.evaluator.result.v1',
    evaluator_id: EVALUATOR_ID,
    passed,
    decision: passed ? 'pass' : 'block',
    action: passed ? 'keep' : 'block',
    reason,
    measurements: {
      schema: 'lev.measurement.v1',
      variables: {
        claim_verify_exit_code: triple(exitCode),
        claim_verified: triple(passed),
        provider_verdict_bits_present: triple(providerVerdictBitsPresent),
        disposition: triple(disposition),
      },
    },
    evidence_refs: report && typeof report.receipt === 'string'
      ? [{ kind: 'claimgate_receipt', ref: report.receipt, exists: true }]
      : [],
    required_repairs: passed ? [] : [repairFor(disposition)],
  };
}

function receiptPathFrom(input) {
  if (typeof input === 'string' && input.trim()) return resolve(input);
  if (isRecord(input) && typeof input.receipt_path === 'string' && input.receipt_path.trim()) {
    return resolve(input.receipt_path);
  }
  return undefined;
}

function forbiddenFields(value, path = '$', found = []) {
  if (Array.isArray(value)) {
    value.forEach((entry, index) => forbiddenFields(entry, `${path}[${index}]`, found));
    return found;
  }
  if (!isRecord(value)) return found;
  for (const [key, entry] of Object.entries(value)) {
    if (FORBIDDEN_PROVIDER_FIELDS.has(key)) found.push(`${path}.${key}`);
    if (key === 'name' && typeof entry === 'string' && FORBIDDEN_PROVIDER_FIELDS.has(entry)) {
      found.push(`${path}.name=${entry}`);
    }
    forbiddenFields(entry, `${path}.${key}`, found);
  }
  return found;
}

function repairFor(disposition) {
  if (disposition === 'rejected') return 'repair rejected evidence; provider-authored verdict bits must be stripped';
  if (disposition === 'insufficient_depth') return 'classify the claim and supply every evaluator-required evidence tier';
  return 'repair the evaluator invocation or malformed receipt before admission';
}

function triple(value) {
  return { value, confidence: 1, evidence_count: 1 };
}

function isRecord(value) {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}
