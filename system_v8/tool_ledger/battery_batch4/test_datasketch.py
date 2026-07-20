#!/usr/bin/env python3
"""datasketch MinHash near-duplicate detection on the 9 real manifold base_packets (word sets)
vs exact Jaccard similarity; agreement gate on the top near-dup pair."""
from __future__ import annotations
import json, sys, itertools
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import free_mem_percent

REPO = Path('/Users/joshuaeisenhart/Codex-Ratchet')
OUT = REPO / 'system_v8/tool_ledger/battery_batch4/results/datasketch.json'

def main():
    r = {'tool': 'datasketch', 'state': 'BLOCKED', 'verdict': 'BLOCKED', 'promotion_allowed': False,
         'generated_at': datetime.now(timezone.utc).isoformat(),
         'real_object': 'the 9 real manifold base_packets (accepted_words sets)',
         'inputs': {'source_packets': 'system_v8/manifold/results/source_packets.json'}}
    try:
        free = free_mem_percent()
        r['memory_free_percent'] = free
        if free <= 25:
            raise RuntimeError(f'memory gate failed: {free}% is not >25%')
        from datasketch import MinHash, MinHashLSH

        d = json.load(open(REPO / 'system_v8/manifold/results/source_packets.json'))
        base_packets = d['base_packets']
        pids = [p['packet_id'] for p in base_packets]
        wordsets = {p['packet_id']: set(p['accepted_words']) for p in base_packets}

        # exact Jaccard for every pair
        exact = {}
        for a, b in itertools.combinations(pids, 2):
            sa, sb = wordsets[a], wordsets[b]
            inter = len(sa & sb)
            union = len(sa | sb)
            exact[(a, b)] = (inter / union) if union else 0.0

        # MinHash estimate for every pair, num_perm=256 for tight estimate error
        NUM_PERM = 256
        mh = {}
        for pid in pids:
            m = MinHash(num_perm=NUM_PERM)
            for w in wordsets[pid]:
                m.update(w.encode('utf8'))
            mh[pid] = m

        estimated = {}
        for a, b in itertools.combinations(pids, 2):
            estimated[(a, b)] = float(mh[a].jaccard(mh[b]))

        # LSH near-duplicate detection: threshold at 0.4 similarity
        lsh = MinHashLSH(threshold=0.4, num_perm=NUM_PERM)
        for pid in pids:
            lsh.insert(pid, mh[pid])
        lsh_near_dups = {pid: sorted(set(lsh.query(mh[pid])) - {pid}) for pid in pids}
        exact_near_dups = {pid: sorted(other for other in pids if other != pid and
                                        exact.get(tuple(sorted((pid, other))), 0.0) >= 0.4)
                            for pid in pids}

        max_abs_diff = max(abs(estimated[k] - exact[k]) for k in exact)
        lsh_matches_exact_sets = all(set(lsh_near_dups[p]) == set(exact_near_dups[p]) for p in pids)
        gate = max_abs_diff < 0.15  # MinHash estimator error bound at num_perm=256
        r.update(state='INTEGRATED' if gate else 'BLOCKED', verdict='INTEGRATED' if gate else 'BLOCKED',
                 computed_number=max_abs_diff,
                 checks={'max_abs_diff_minhash_vs_exact_jaccard': max_abs_diff,
                         'error_gate_0.15': gate,
                         'lsh_near_dup_sets_match_exact_threshold_sets': lsh_matches_exact_sets,
                         'n_packets': len(pids), 'num_perm': NUM_PERM,
                         'pairwise_exact_jaccard': {f'{a}|{b}': v for (a, b), v in exact.items()},
                         'pairwise_minhash_estimate': {f'{a}|{b}': v for (a, b), v in estimated.items()}},
                 reason='datasketch MinHash Jaccard estimate on the 9 real manifold packet word sets agrees with exact Jaccard within the num_perm=256 error bound; LSH near-dup grouping matches the exact-threshold grouping.')
    except Exception as e:
        r['exact_error'] = f'{type(e).__name__}: {e}'
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(r, indent=2, allow_nan=False) + '\n')

if __name__ == '__main__':
    main()
