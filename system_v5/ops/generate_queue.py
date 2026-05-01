#!/usr/bin/env python3
"""Generate the stage-gated default queue.

This queue is a fallback for tool sims, tool-integration sims, and unfinished
local lego work only. It must not auto-queue pairwise/coexistence/bridge/axis
style probes before the lego stage is complete.
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
    'pairwise', 'coupling', 'coexistence', 'triple', 'bridge', 'axis',
    'phi0', 'rho_ab', 'cut_', '_cut', 'kernel', 'emergence', 'stacking',
    'carnot', 'szilard', 'jarzynski', 'landauer', 'engine', 'ladder',
    'bakeoff',
)

def allowed_in_default_queue(base: str) -> bool:
    lower = base.lower()
    return not any(token in lower for token in LATE_STAGE_TOKENS)

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
    "# Contains tool sims, tool-integration sims, and local lego-stage work.",
    "# Excludes pairwise/coexistence/bridge/axis/engine-style probes.",
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
