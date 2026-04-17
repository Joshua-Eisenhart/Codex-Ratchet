#!/usr/bin/env python3
"""Generate default queue: never-run probes + canonical-missing-depth.
Sorted smallest-first for fast feedback."""
import glob, os, json, sys

repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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

result_dirs = [
    'system_v4/probes/a2_state/sim_results',
    'system_v4/probes/sim_results',
    'system_v4/a2_state/sim_results',
]
results = set()
for d in result_dirs:
    for p in glob.glob(f'{d}/*.json'):
        results.add(os.path.basename(p).replace('_results.json', ''))

never_run = [(os.path.basename(p)[:-3], os.path.getsize(p)) for p in probes if os.path.basename(p)[:-3] not in results]
never_run.sort(key=lambda x: x[1])

canonical_missing = []
for d in result_dirs:
    for p in glob.glob(f'{d}/*.json'):
        try: j = json.load(open(p))
        except Exception: continue
        if not isinstance(j, dict): continue
        if j.get('classification') == 'canonical' and 'tool_integration_depth' not in j:
            base = os.path.basename(p).replace('_results.json', '')
            if os.path.exists(f'system_v4/probes/{base}.py'):
                canonical_missing.append(base)

lines = [
    "# Default queue — never-run probes + canonical-missing-depth.",
    "# Sorted smallest-file-first for fast feedback signal.",
    "# Runner rewrites DONE/FAIL/SKIPPED lines in place.",
    f"# generated: {len(never_run)} never-run + {len(canonical_missing)} missing-depth",
    "",
    "# ---- canonical missing depth (priority) ----",
]
lines.extend(canonical_missing)
lines.append("# ---- never-run probes, smallest-first ----")
lines.extend(b for b, _ in never_run)

sys.stdout.write('\n'.join(lines) + '\n')
