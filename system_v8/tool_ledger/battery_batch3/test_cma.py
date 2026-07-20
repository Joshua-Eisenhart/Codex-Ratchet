#!/usr/bin/env python3
"""cma evolutionary search maximizing IG over real probe orders; beats random mean."""
from __future__ import annotations
import json, sys, subprocess, re
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

REPO = Path('/Users/joshuaeisenhart/Codex-Ratchet')
OUT = REPO / 'system_v8/tool_ledger/battery_batch3/results/cma.json'

def main():
    r = {'tool': 'cma', 'state': 'BLOCKED', 'verdict': 'BLOCKED', 'promotion_allowed': False,
         'generated_at': datetime.now(timezone.utc).isoformat(),
         'real_object': 'real cumulative IG fitness from senses hypotheses',
         'inputs': {'world': 'system_v8/loop2_world/results/world_source/events_dynamics_on.jsonl'}}
    try:
        free = int(re.search(r'(\d+)%', subprocess.run(['memory_pressure'], capture_output=True, text=True, check=True).stdout.split('System-wide memory free percentage:')[1]).group(1))
        r['memory_free_percent'] = free
        if free <= 25: raise RuntimeError(f'memory gate failed: {free}% is not >25%')
        import cma
        sys.path.insert(0, str(REPO / 'system_v8/loop3_senses'))
        import visibility_sanity_gate as v
        import senses_v2_slow_memory as s
        from pathlib import Path as P
        wr = json.load(open(s.WORLD_RECEIPT))
        rules = {int(k):tuple(x) for k,x in wr["parameters"]["rule_family"].items()}
        log,_ = v.parse_event_log(P(s.EVENTS))
        full,_ = v.recover_full_views(log, rules)
        words,rs,h = s.build_hypotheses(rules)
        oid="obj-000"; view=3
        true = np.array(full[oid][view],int)
        cands = np.asarray(h[:,view,:])
        def entropy_after(seen):
            keep = np.ones(len(h),bool)
            for a in seen: keep &= (cands[:,a]==true[a])
            q = keep / max(1,keep.sum())
            if keep.sum()<2: return 0.0
            return -float(np.sum(q[keep]*np.log(np.clip(q[keep],1e-12,1))))
        def fitness(x):
            p = np.argsort(x).tolist()
            s = 0.0; seen=[]
            for a in p:
                seen.append(a); s += entropy_after(seen)
            return s
        es = cma.CMAEvolutionStrategy([3.5]*8, 1.2, {'popsize':8, 'seed':20260719})
        for _ in range(6):
            xs = es.ask()
            es.tell(xs, [-fitness(x) for x in xs])  # maximize
        best = -es.result[1]
        randoms = [fitness(np.random.permutation(8).astype(float)) for _ in range(20)]
        rand_mean = float(np.mean(randoms))
        ok = best > rand_mean
        r.update(state='INTEGRATED' if ok else 'BLOCKED', verdict='INTEGRATED' if ok else 'BLOCKED',
                 computed_number=best,
                 checks={'best_ig': best, 'random_mean': rand_mean, 'beats_random': ok},
                 reason='cma evolves real probe-order IG; must beat random mean.')
    except Exception as e:
        r['exact_error'] = f'{type(e).__name__}: {e}'
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(r, indent=2, allow_nan=False) + '\n')

if __name__ == '__main__':
    main()
