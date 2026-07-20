#!/usr/bin/env python3
"""ribs (pyribs): quality-diversity CMA-ME search over the same real
probe-order cumulative-IG objective as batch3 cma/deap/pymoo (real
obj-000/view-3 hypothesis space), with a real 2D behavior descriptor
(rank position of probe 0, rank position of probe 1 in the decoded order).
Archive best objective must beat the random-order mean, same gate as
cma/deap/pymoo (33.7-scale)."""
from __future__ import annotations
import json, sys
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from _common import free_mem_percent

REPO = Path('/Users/joshuaeisenhart/Codex-Ratchet')
OUT = REPO / 'system_v8/tool_ledger/battery_batch5/results/ribs.json'


def main():
    r = {'tool': 'ribs', 'state': 'BLOCKED', 'verdict': 'BLOCKED', 'promotion_allowed': False,
         'generated_at': datetime.now(timezone.utc).isoformat(),
         'real_object': 'real obj-000/view-3 probe-order cumulative-IG objective (senses_v2_slow_memory)'}
    try:
        free = free_mem_percent()
        r['memory_free_percent'] = free
        if free <= 25:
            raise RuntimeError(f'memory gate failed: {free}% is not >25%')
        from ribs.archives import GridArchive
        from ribs.emitters import EvolutionStrategyEmitter
        from ribs.schedulers import Scheduler

        sys.path.insert(0, str(REPO / 'system_v8/loop3_senses'))
        import visibility_sanity_gate as v
        import senses_v2_slow_memory as s

        wr = json.load(open(s.WORLD_RECEIPT))
        rules = {int(k): tuple(x) for k, x in wr['parameters']['rule_family'].items()}
        log, _ = v.parse_event_log(Path(s.EVENTS))
        full, _ = v.recover_full_views(log, rules)
        words, rs, h = s.build_hypotheses(rules)
        oid, view = 'obj-000', 3
        true = np.array(full[oid][view], int)
        cands = np.asarray(h[:, view, :])

        def entropy_after(seen):
            keep = np.ones(len(h), bool)
            for a in seen:
                keep &= (cands[:, a] == true[a])
            n = keep.sum()
            if n < 2:
                return 0.0
            q = keep / n
            return -float(np.sum(q[keep] * np.log(np.clip(q[keep], 1e-12, 1))))

        def cum_ig(order):
            s_ = 0.0
            seen = []
            for a in order:
                seen.append(a)
                s_ += entropy_after(seen)
            return s_

        def decode(x):
            return np.argsort(x)

        archive = GridArchive(solution_dim=8, dims=[8, 8], ranges=[(0, 7), (0, 7)], seed=20260720)
        emitters = [EvolutionStrategyEmitter(archive, x0=np.full(8, 3.5), sigma0=1.2,
                                              batch_size=8, seed=20260720)]
        scheduler = Scheduler(archive, emitters)

        for _ in range(15):
            sols = scheduler.ask()
            objs, measures = [], []
            for x in sols:
                order = decode(x)
                objs.append(cum_ig(order))
                measures.append([float(np.where(order == 0)[0][0]), float(np.where(order == 1)[0][0])])
            scheduler.tell(np.asarray(objs), np.asarray(measures))

        best_qd = float(archive.stats.obj_max)
        rng = np.random.default_rng(20260720)
        randoms = [cum_ig(rng.permutation(8)) for _ in range(20)]
        rand_mean = float(np.mean(randoms))

        ok = best_qd > rand_mean and int(archive.stats.num_elites) > 1
        r.update(state='INTEGRATED' if ok else 'BLOCKED', verdict='INTEGRATED' if ok else 'BLOCKED',
                 computed_number=best_qd,
                 checks={'best_qd_objective': best_qd, 'random_mean': rand_mean,
                         'beats_random_mean': best_qd > rand_mean,
                         'num_archive_elites': int(archive.stats.num_elites)},
                 reason=f'ribs GridArchive + EvolutionStrategyEmitter (CMA-ES-driven QD) searches the same real '
                        f'probe-order cumulative-IG objective as batch3 cma/deap/pymoo, with a real 2D behavior '
                        f'descriptor (rank positions of probes 0 and 1); best archived objective {best_qd:.5f} '
                        f'beats the random-order mean {rand_mean:.5f}, populating {int(archive.stats.num_elites)} '
                        f'distinct archive cells.')
    except Exception as e:
        r['exact_error'] = f'{type(e).__name__}: {e}'
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(r, indent=2, allow_nan=False) + '\n')


if __name__ == '__main__':
    main()
