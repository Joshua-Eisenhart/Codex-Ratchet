#!/usr/bin/env python3
"""Generate the stage-gated default queue.

This queue is a fail-closed fallback for controller-approved tool sims and
unfinished local lego work only. Stage-heavier tool-integration rows belong in
Tier A or explicit review; the default generator must not auto-queue broad
integration, pairwise, coexistence, bridge, or axis probes before the lego stage
is complete.
"""
import glob, os, sys

repo = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(repo)

probes = sorted(glob.glob('system_v4/probes/*.py'))
# Skip private helpers and non-sim utility scripts. Only include actual probe-runnable files.
SKIP_PREFIXES = ('test_', 'run_', 'validate_', 'strata_', 'gen_', 'audit_', 'check_')
probes = [
    p for p in probes
    if not os.path.basename(p).startswith('_')
    and os.path.basename(p) != '__init__.py'
    and not any(os.path.basename(p).startswith(pre) for pre in SKIP_PREFIXES)
]

LATE_STAGE_TOKENS = (
    'pairwise', 'couple', 'coupling', 'crosscouple', 'coexistence', 'triple', 'bridge', 'axis',
    'phi0', 'rho_ab', 'cut_', '_cut', 'kernel', 'emergence', 'stacking',
    'carnot', 'szilard', 'jarzynski', 'landauer', 'engine', 'ladder',
    'bakeoff',
)

BROAD_SCOPE_TOKENS = (
    'cascade', 'pipeline', 'integrated', 'integration', 'compound',
    'composition', 'global', 'companion', 'overlay', 'alignment',
    'meta_', 'deep_quantum', 'full_', 'mega_', 'substrate_',
    'topology_entropy', 'topology_boundary', 'topology_compatibility',
    'topology_pauli', 'carrier_array', 'cross_layer', 'crosscheck',
    'geom_layer_', 'layered_', 'minimal_surviving_set',
    'g_structure_tower', 'gtower_chain', 'tower_chain',
)

MULTI_LAYER_TOKENS = (
    'layer4_5_6', 'layer7_12', 'layer13_19', 'layer0_1',
    'l4_l6', 'l6_l7', 'l5_l6', 'l0_l1',
)

ALLOWED_SINGLE_LAYER_PREFIXES = (
    'sim_constrain_legos_l',
    'sim_l6_binding_radius_sweep',
    'sim_geometry_families_l0',
)

def allowed_in_default_queue(base: str) -> bool:
    lower = base.lower()
    if any(lower.startswith(prefix) for prefix in ALLOWED_SINGLE_LAYER_PREFIXES):
        return not any(token in lower for token in LATE_STAGE_TOKENS)
    tokens = LATE_STAGE_TOKENS + BROAD_SCOPE_TOKENS + MULTI_LAYER_TOKENS
    return not any(token in lower for token in tokens)

result_dirs = [
    'system_v4/probes/a2_state/sim_results',
    'system_v4/probes/sim_results',
    'system_v4/a2_state/sim_results',
]
results = set()
for d in result_dirs:
    for p in glob.glob(f'{d}/*.json'):
        results.add(os.path.basename(p).replace('_results.json', ''))

never_run = [
    (os.path.basename(p)[:-3], os.path.getsize(p))
    for p in probes
    if os.path.basename(p)[:-3] not in results
    and allowed_in_default_queue(os.path.basename(p)[:-3])
]
never_run.sort(key=lambda x: x[1])

# Missing-depth repair is intentionally not inferred from the whole historical
# result estate here. That scan is expensive and mixes contract repair with the
# safe default queue. Use explicit repair queues for missing-depth work.
canonical_missing = []

lines = [
    "# Default queue — stage-gated fallback only.",
    "# Contains controller-approved tool sims and local lego-stage work.",
    "# Stage-heavier tool-integration rows belong in Tier A or explicit review.",
    "# Excludes pairwise/coexistence/bridge/axis/engine and broad cascade/pipeline/integration probes.",
    "# Sorted smallest-file-first inside the allowed stage only.",
    "# Runner rewrites DONE/FAIL/SKIPPED lines in place.",
    f"# generated: {len(never_run)} never-run + {len(canonical_missing)} missing-depth",
    "",
    "# ---- canonical missing depth (priority) ----",
]
lines.extend(canonical_missing)
lines.append("# ---- never-run probes, smallest-first ----")
lines.extend(b for b, _ in never_run)

sys.stdout.write('\n'.join(lines) + '\n')
