#!/usr/bin/env bun

import { createHash } from 'node:crypto';
import { spawnSync } from 'node:child_process';
import { createRequire } from 'node:module';
import { mkdir, readFile, realpath, rename, stat, unlink, writeFile } from 'node:fs/promises';
import { dirname, isAbsolute, join, relative, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

const LANE = 'system_v5/ops/tooling/deep_stack_stress_20260714';
const CONTRACT_PATH = `${LANE}/lev/qit_bridge_seam_contract.json`;
const LEV_RUNTIME_PATH = `${LANE}/lev/current_lev_runtime.json`;
const PRODUCER_PATH = 'system_v7/constraint_core/sims_and_scripts/lev_bridge_sim.py';
const ADAPTER_PATH = 'system_v7/constraint_core/sims_and_scripts/lev_qit_bridge_stream_host_adapter.py';
const LEV_INGEST_PATH = 'plugins/sim-witness/src/qit-bridge-stream.ts';
const LEV_SENSOR_PATH = 'plugins/sim-witness/evals/cr_qit_bridge_stream_v0/companions/sensor.mjs';
const LEV_GATE_POLICY_PATH = 'plugins/sim-witness/evals/cr_qit_bridge_stream_v0/policies/gate-policy.yaml';
const LEV_ROUTING_POLICY_PATH = 'plugins/sim-witness/evals/cr_qit_bridge_stream_v0/policies/routing-policy.yaml';

function parseArgs(argv) {
  const required = ['--repo-root', '--lev-root', '--python', '--out', '--requested-at'];
  const known = new Set(required);
  const values = new Map();
  for (let index = 0; index < argv.length; index += 1) {
    const flag = argv[index];
    if (!flag.startsWith('--')) throw new Error(`Unexpected positional argument: ${flag}`);
    if (!known.has(flag)) throw new Error(`Unknown argument: ${flag}`);
    if (values.has(flag)) throw new Error(`Duplicate argument: ${flag}`);
    const value = argv[index + 1];
    if (!value || value.startsWith('--')) throw new Error(`Missing value for ${flag}`);
    values.set(flag, value);
    index += 1;
  }
  for (const flag of required) {
    if (!values.has(flag)) throw new Error(`Missing required argument ${flag}`);
  }
  const requestedAt = values.get('--requested-at');
  if (!Number.isFinite(Date.parse(requestedAt)) || new Date(requestedAt).toISOString() !== requestedAt) {
    throw new Error('--requested-at must be a canonical ISO-8601 timestamp');
  }
  return {
    repoRoot: resolve(values.get('--repo-root')),
    levRoot: resolve(values.get('--lev-root')),
    python: resolve(values.get('--python')),
    out: resolve(values.get('--out')),
    requestedAt,
  };
}

function isInside(root, candidate) {
  const rel = relative(root, candidate);
  return rel === '' || (!rel.startsWith('..') && !isAbsolute(rel));
}

async function sha256File(path) {
  const digest = createHash('sha256');
  digest.update(await readFile(path));
  return digest.digest('hex');
}

async function readJson(path) {
  return JSON.parse(await readFile(path, 'utf8'));
}

async function writeJsonAtomic(path, value) {
  await mkdir(dirname(path), { recursive: true });
  const temporary = `${path}.tmp-${process.pid}`;
  await writeFile(temporary, `${JSON.stringify(value, null, 2)}\n`, 'utf8');
  await rename(temporary, path);
}

async function clearOwnedFile(path) {
  try {
    const value = await stat(path);
    if (!value.isFile()) throw new Error(`Refusing to replace non-file output: ${path}`);
    await unlink(path);
    return true;
  } catch (error) {
    if (error?.code === 'ENOENT') return false;
    throw error;
  }
}

function execute(command, argv, cwd, timeoutMs = 120_000) {
  const completed = spawnSync(command, argv, {
    cwd,
    encoding: 'utf8',
    env: {
      ...process.env,
      PYTHONDONTWRITEBYTECODE: '1',
      PYTHONNOUSERSITE: '1',
    },
    shell: false,
    timeout: timeoutMs,
  });
  return {
    command: [command, ...argv],
    cwd,
    exit_code: completed.status ?? 1,
    signal: completed.signal,
    timed_out: completed.error?.code === 'ETIMEDOUT',
    stdout: completed.stdout ?? '',
    stderr: completed.stderr ?? '',
    executed: true,
  };
}

function requireSuccess(record, label) {
  if (record.exit_code !== 0) {
    throw new Error(`${label} failed with exit ${record.exit_code}: ${record.stderr || record.stdout}`);
  }
  return record;
}

function gitValue(root, argv) {
  const record = requireSuccess(execute('/usr/bin/git', ['-C', root, ...argv], root), `git ${argv.join(' ')}`);
  return record.stdout.trim();
}

function gitIdentity(root) {
  return {
    root,
    commit: gitValue(root, ['rev-parse', 'HEAD']),
    tree: gitValue(root, ['rev-parse', 'HEAD^{tree}']),
    branch: gitValue(root, ['rev-parse', '--abbrev-ref', 'HEAD']),
    tracked_bytes_clean: execute('/usr/bin/git', ['-C', root, 'diff', '--quiet', 'HEAD', '--'], root).exit_code === 0,
  };
}

function thresholdPolicyMatches(contract, gatePolicy) {
  const thresholds = gatePolicy?.thresholds ?? {};
  return [
    'baseline_mean_lt',
    'spike_max_gt',
    'tail_mean_lt',
    'tail_max_lt',
  ].every((key) => thresholds[key] === contract.shape_contract[key])
    && thresholds.min_provider_ticks === contract.expected.tick_count;
}

async function sourceRecord(role, root, path) {
  const absolute = resolve(root, path);
  return {
    role,
    path: absolute,
    sha256: await sha256File(absolute),
  };
}

async function runSeam(args) {
  const repoRoot = await realpath(args.repoRoot);
  const levRoot = await realpath(args.levRoot);
  const out = resolve(args.out);
  if (!isInside(repoRoot, out)) throw new Error(`Receipt output must remain inside the Codex-Ratchet root: ${out}`);

  const contract = await readJson(join(repoRoot, CONTRACT_PATH));
  const runtime = await readJson(join(repoRoot, LEV_RUNTIME_PATH));
  const codexIdentity = gitIdentity(repoRoot);
  const levIdentity = gitIdentity(levRoot);
  const rawPath = join(dirname(out), 'codex_qit_bridge_raw.json');
  const adaptedPath = join(dirname(out), 'codex_qit_bridge_lev_v1.json');
  const preexistingOutputsRemoved = {
    raw: await clearOwnedFile(rawPath),
    adapted: await clearOwnedFile(adaptedPath),
    receipt: await clearOwnedFile(out),
  };

  const producer = requireSuccess(execute(args.python, ['-B', PRODUCER_PATH, '--out', rawPath], repoRoot), 'Codex QIT producer');
  const adapter = requireSuccess(execute(args.python, ['-B', ADAPTER_PATH, '--source', rawPath, '--out', adaptedPath], repoRoot), 'Codex-to-Lev stream adapter');

  const requireFromLev = createRequire(join(levRoot, 'package.json'));
  const { parse: parseYaml } = requireFromLev('yaml');
  const gatePolicy = parseYaml(await readFile(join(levRoot, LEV_GATE_POLICY_PATH), 'utf8'));
  const routingPolicy = parseYaml(await readFile(join(levRoot, LEV_ROUTING_POLICY_PATH), 'utf8'));
  const moduleBinding = encodeURIComponent(levIdentity.commit);
  const ingestModule = await import(`${pathToFileURL(join(levRoot, LEV_INGEST_PATH)).href}?lev=${moduleBinding}`);
  const sensorModule = await import(`${pathToFileURL(join(levRoot, LEV_SENSOR_PATH)).href}?lev=${moduleBinding}`);

  const rawDocument = await readJson(rawPath);
  const adaptedDocument = await readJson(adaptedPath);
  const ingestion = await ingestModule.ingestQitBridgeStreamFile(adaptedPath, {
    subjectRef: contract.subject_ref,
    generation: contract.generation,
    requestedAt: args.requestedAt,
  });
  const negativeControl = ingestModule.ingestQitBridgeStreamDocument(
    { ...adaptedDocument, schema_version: 'constraint_core.invalid.v0' },
    {
      subjectRef: contract.subject_ref,
      generation: contract.generation,
      requestedAt: args.requestedAt,
      sourcePath: `${adaptedPath}#invalid-schema-control`,
    },
  );
  const sensorResult = ingestion.ok
    ? sensorModule.score({ provider_evidence: ingestion.providerEvidence, shape_contract: contract.shape_contract })
    : { passed: false, decision: 'block', action: 'block', reason: ingestion.reason };

  const levExecutableSha256 = await sha256File(runtime.executable);
  const levLauncherTarget = await realpath(runtime.launcher);
  const levExecutableTarget = await realpath(runtime.executable);
  const providerAddresses = ingestion.ok ? ingestion.providerEvidence.map((row) => row.content_address) : [];
  const gates = {
    seam_contract_schema_exact: contract.schema === 'codex_ratchet.qit_bridge_seam_contract.v1',
    lev_runtime_schema_exact: runtime.schema === 'codex_ratchet.lev_runtime_binding.v1',
    codex_tracked_bytes_clean: codexIdentity.tracked_bytes_clean,
    lev_tracked_bytes_clean: levIdentity.tracked_bytes_clean,
    lev_runtime_root_match: runtime.root === levRoot,
    lev_runtime_branch_match: runtime.branch === levIdentity.branch,
    lev_runtime_commit_match: runtime.commit === levIdentity.commit,
    lev_runtime_tree_match: runtime.tree === levIdentity.tree,
    lev_global_launcher_match: levLauncherTarget === levExecutableTarget,
    lev_executable_hash_match: runtime.executable_sha256 === levExecutableSha256,
    producer_exit_zero: producer.exit_code === 0,
    adapter_exit_zero: adapter.exit_code === 0,
    raw_to_adapted_ticks_exact: JSON.stringify(rawDocument.stream) === JSON.stringify(adaptedDocument.stream),
    source_classification_exact: adaptedDocument.classification === contract.expected.classification,
    source_promotion_blocked: adaptedDocument.promotion_allowed === contract.expected.promotion_allowed,
    source_claim_ceiling_exact: adaptedDocument.claim_ceiling === contract.source_claim_ceiling,
    lev_ingest_pass: ingestion.ok === true,
    provider_tick_count_exact: ingestion.ok && ingestion.providerEvidence.length === contract.expected.tick_count,
    provider_addresses_unique: providerAddresses.length === new Set(providerAddresses).size,
    provider_addresses_typed: providerAddresses.every((value) => value.startsWith('sim-witness:fnv1a32:')),
    gate_threshold_policy_exact: thresholdPolicyMatches(contract, gatePolicy),
    routing_policy_exact: routingPolicy?.routes?.pass?.action === contract.expected.sensor_action,
    sensor_decision_pass: sensorResult.decision === contract.expected.sensor_decision && sensorResult.passed === true,
    sensor_action_exact: sensorResult.action === contract.expected.sensor_action,
    schema_negative_control_blocks: negativeControl.ok === false && negativeControl.reason === contract.expected.negative_control_reason,
  };
  const allPass = Object.values(gates).every((value) => value === true);

  const sources = await Promise.all([
    sourceRecord('codex_qit_producer', repoRoot, PRODUCER_PATH),
    sourceRecord('codex_host_adapter', repoRoot, ADAPTER_PATH),
    sourceRecord('seam_contract', repoRoot, CONTRACT_PATH),
    sourceRecord('lev_runtime_binding', repoRoot, LEV_RUNTIME_PATH),
    sourceRecord('lev_ingester', levRoot, LEV_INGEST_PATH),
    sourceRecord('lev_sensor', levRoot, LEV_SENSOR_PATH),
    sourceRecord('lev_gate_policy', levRoot, LEV_GATE_POLICY_PATH),
    sourceRecord('lev_routing_policy', levRoot, LEV_ROUTING_POLICY_PATH),
  ]);
  const receipt = {
    schema: 'codex_ratchet.lev_qit_bridge_seam_receipt.v1',
    status: allPass ? 'pass' : 'blocked',
    all_pass: allPass,
    command: [process.execPath, ...process.argv.slice(1)],
    requested_at: args.requestedAt,
    runner: {
      script: resolve(process.argv[1]),
      script_sha256: await sha256File(resolve(process.argv[1])),
      bun_executable: process.execPath,
      bun_version: Bun.version,
      python_executable: args.python,
      python_version: requireSuccess(execute(args.python, ['--version'], repoRoot), 'Python version').stdout.trim(),
      codex_repo: codexIdentity,
      lev_repo: levIdentity,
      lev_executable: runtime.executable,
      lev_executable_sha256: levExecutableSha256,
      global_launcher: runtime.launcher,
      global_launcher_target: levLauncherTarget,
    },
    source_material: sources,
    outputs: {
      preexisting_outputs_removed: preexistingOutputsRemoved,
      raw_stream: { path: rawPath, sha256: await sha256File(rawPath) },
      adapted_stream: { path: adaptedPath, sha256: await sha256File(adaptedPath) },
      receipt: { path: out },
    },
    hops: [
      { id: 'codex_qit_producer', ...producer },
      { id: 'codex_stream_adapter', ...adapter },
      { id: 'lev_sim_witness_ingest', ok: ingestion.ok, provider_evidence_count: ingestion.ok ? ingestion.providerEvidence.length : 0, reason: ingestion.ok ? null : ingestion.reason },
      { id: 'lev_deterministic_sensor', result: sensorResult },
      { id: 'schema_negative_control', result: negativeControl },
    ],
    gates,
    classification: contract.expected.classification,
    promotion_allowed: false,
    release_eligible: false,
    projection_only: true,
    llm_used: false,
    model_adapter_used: false,
    provider_call_used: false,
    install_attempted: false,
    scientific_claim_proven: false,
    claim_ceiling: contract.receipt_claim_ceiling,
  };
  await writeJsonAtomic(out, receipt);
  console.log(JSON.stringify({
    schema: receipt.schema,
    status: receipt.status,
    all_pass: receipt.all_pass,
    receipt: out,
    codex_commit: codexIdentity.commit,
    lev_commit: levIdentity.commit,
    provider_tick_count: ingestion.ok ? ingestion.providerEvidence.length : 0,
    sensor_decision: sensorResult.decision,
    negative_control: negativeControl.ok ? 'unexpected_pass' : negativeControl.reason,
    promotion_allowed: false,
    release_eligible: false,
    scientific_claim_proven: false,
  }, null, 2));
  return allPass ? 0 : 1;
}

const args = parseArgs(process.argv.slice(2));
try {
  process.exitCode = await runSeam(args);
} catch (error) {
  const blocked = {
    schema: 'codex_ratchet.lev_qit_bridge_seam_receipt.v1',
    status: 'blocked',
    all_pass: false,
    command: [process.execPath, ...process.argv.slice(1)],
    requested_at: args.requestedAt,
    error: error instanceof Error ? error.message : String(error),
    promotion_allowed: false,
    release_eligible: false,
    llm_used: false,
    model_adapter_used: false,
    provider_call_used: false,
    install_attempted: false,
    projection_only: true,
    scientific_claim_proven: false,
    claim_ceiling: 'Operational seam execution failed; no integration or scientific claim is authorized.',
  };
  if (isInside(args.repoRoot, args.out)) await writeJsonAtomic(args.out, blocked);
  console.error(JSON.stringify(blocked, null, 2));
  process.exitCode = 1;
}
