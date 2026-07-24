// Deterministic scorer for ClaimGate flip-battery evidence.
// Lives in Codex-Ratchet (CR proposes); Lev runs it and decides.
//
// One-brain contract, enforced HERE and not merely documented: if the provider
// evidence carries its own verdict or an evaluated status, this BLOCKS. Evidence
// may measure; only the scorer may conclude.

const PROVIDER_SCHEMA = 'lev.sim_witness.provider_evidence.v1';

const FORBIDDEN_PROVIDER_FIELDS = Object.freeze([
  'verdict', 'EvalVerdict', 'gate_proof', 'GateProof',
  'proof_bundle', 'ProofBundle', 'effect_receipt', 'EffectReceipt',
  'run_seal', 'RunSeal',
]);
const FORBIDDEN_PROVIDER_STATUSES = Object.freeze([
  'evaluated', 'pass', 'fail', 'not_evaluated',
]);

const THRESHOLDS = Object.freeze({
  min_flip_rate: 0.5,      // below this the pinned mechanism did not bear weight
  max_control_flip_rate: 0.0,
});

function result(status, reason, measurements = {}) {
  return { status, reason, measurements, evaluator_id: 'claimgate_flip_battery' };
}

function scanForbidden(node, path = '') {
  const hits = [];
  if (node && typeof node === 'object' && !Array.isArray(node)) {
    for (const [k, v] of Object.entries(node)) {
      if (FORBIDDEN_PROVIDER_FIELDS.includes(k)) hits.push(`${path}.${k}`);
      if (k === 'status' && FORBIDDEN_PROVIDER_STATUSES.includes(String(v))) {
        hits.push(`${path}.status=${v}`);
      }
      hits.push(...scanForbidden(v, `${path}.${k}`));
    }
  } else if (Array.isArray(node)) {
    node.forEach((v, i) => hits.push(...scanForbidden(v, `${path}[${i}]`)));
  }
  return hits;
}

function loadBearing(entry) {
  const erase = entry?.test_1_erase?.erase_flips === true;
  const rate = Number(entry?.test_2_perturb?.flip_rate ?? 0);
  const core = entry?.test_3_core?.core_is_subset === true;
  return erase && rate > THRESHOLDS.min_flip_rate && core;
}

export function score(input) {
  const ev = input?.provider_evidence ?? input?.evidence ?? input;

  if (!ev || typeof ev !== 'object') {
    return result('block', 'no provider evidence supplied');
  }
  if (ev.schema && !String(ev.schema).includes('trace') && ev.schema !== PROVIDER_SCHEMA) {
    return result('block', `unexpected provider schema ${ev.schema}`);
  }

  // ONE-BRAIN: evidence that grades itself is refused outright.
  const selfGraded = scanForbidden(ev);
  if (selfGraded.length) {
    return result('block',
      `provider evidence carries its own verdict at ${selfGraded.join(', ')} — ` +
      `evidence may measure, only the scorer concludes`);
  }

  // Lanes carry name/value facts; rebuild the two candidates from them.
  const lanes = Array.isArray(ev.provider_evidence) ? ev.provider_evidence : [];
  if (lanes.length < 2) {
    return result('block', 'battery needs a real candidate AND a negative control');
  }
  const asEntry = (l) => {
    const f = Object.fromEntries((l.facts ?? []).map((x) => [x.name, x.value]));
    return {
      label: f.label,
      test_1_erase: { erase_flips: f.erase_flips, real: f.smt_real, erased: f.smt_erased },
      test_2_perturb: { flip_rate: f.flip_rate, n_perturbations: f.n_perturbations },
      test_3_core: { core_is_subset: f.core_is_subset, unsat_core_size: f.unsat_core_size },
    };
  };
  const results = lanes.map(asEntry).filter((e) => e.label);
  const real = results.find((r) => !String(r.label).startsWith('NEGATIVE'));
  const ctrl = results.find((r) => String(r.label).startsWith('NEGATIVE'));
  if (!real || !ctrl) {
    return result('block', 'missing real candidate or negative control');
  }

  const realLB = loadBearing(real);
  const ctrlLB = loadBearing(ctrl);
  const measurements = {
    real_label: real.label,
    real_flip_rate: real.test_2_perturb?.flip_rate ?? null,
    real_erase_flips: real.test_1_erase?.erase_flips ?? null,
    real_core_subset: real.test_3_core?.core_is_subset ?? null,
    control_label: ctrl.label,
    control_flip_rate: ctrl.test_2_perturb?.flip_rate ?? null,
    llm_tokens_spent: ev.llm_tokens_spent ?? null,
  };

  // The control MUST fail. A battery where everything passes discriminates nothing.
  if (ctrlLB) {
    return result('block',
      'negative control also scored load-bearing — the battery does not discriminate',
      measurements);
  }
  if (!realLB) {
    return result('block',
      'candidate mechanism did not bear weight (erase did not flip, or flip_rate below threshold, ' +
      'or unsat core not a subset) — consistent with a decorative/tautological encoding',
      measurements);
  }

  return result('admit',
    `mechanism bore weight: erase flipped unsat->sat, flip_rate ${measurements.real_flip_rate} ` +
    `> ${THRESHOLDS.min_flip_rate}, unsat core a proper subset; negative control correctly failed`,
    measurements);
}

export default { score };
