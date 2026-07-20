#!/usr/bin/env python3
"""miniKanren (kanren) + logical-unification: relational query over the real
qca_left_shift_cut_relation packet grammar's 8 accepted words — find every
word unifying with the pattern (starts with '1', ends with '0'), via
kanren.run + membero, checked against brute-force enumeration over the same
real word list."""
from __future__ import annotations
import json, sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import free_mem_percent

REPO = Path('/Users/joshuaeisenhart/Codex-Ratchet')
OUT = REPO / 'system_v8/tool_ledger/battery_batch5/results/minikanren.json'
PACKETS = REPO / 'system_v8/manifold/results/source_packets.json'


def main():
    r = {'tool': 'miniKanren+logical-unification', 'state': 'BLOCKED', 'verdict': 'BLOCKED',
         'promotion_allowed': False,
         'generated_at': datetime.now(timezone.utc).isoformat(),
         'real_object': str(PACKETS)}
    try:
        free = free_mem_percent()
        r['memory_free_percent'] = free
        if free <= 25:
            raise RuntimeError(f'memory gate failed: {free}% is not >25%')
        from kanren import run, eq, var, membero
        from unification import unify, var as uvar  # logical-unification, exercised directly below

        pkt = next(x for x in json.loads(PACKETS.read_text())['base_packets']
                   if x['packet_id'] == 'qca_left_shift_cut_relation')
        words = pkt['accepted_words']
        word_tuples = [tuple(w) for w in words]

        c0, c1, c2, c3 = var(), var(), var(), var()
        results = run(0, (c0, c1, c2, c3),
                      membero((c0, c1, c2, c3), word_tuples),
                      eq(c0, '1'), eq(c3, '0'))
        kanren_matches = sorted(''.join(t) for t in results)

        brute_force = sorted(w for w in words if w[0] == '1' and w[-1] == '0')

        # exercise logical-unification's own unify() directly on one real word,
        # against a pattern with a free logic variable in position 1
        x = uvar('x')
        one_word = word_tuples[4]  # '1000'
        pattern = ('1', x, one_word[2], one_word[3])  # free var only at position 1
        unify_result = unify(pattern, one_word, {})
        unify_ok = unify_result is not False and unify_result.get(x) == one_word[1]

        agree = kanren_matches == brute_force
        ok = agree and unify_ok
        r.update(state='INTEGRATED' if ok else 'BLOCKED', verdict='INTEGRATED' if ok else 'BLOCKED',
                 computed_number=float(len(kanren_matches)),
                 checks={'n_real_words': len(words), 'kanren_matches': kanren_matches,
                         'brute_force_matches': brute_force, 'agreement_gate': agree,
                         'unify_direct_check_word': one_word[0] + ''.join(one_word[1:]),
                         'unify_bound_var_matches_word': unify_ok},
                 reason=f'kanren.run relational query (membero + eq unification goals) over the real 8-word '
                        f'qca_left_shift_cut_relation grammar finds words matching pattern (starts \'1\', ends '
                        f'\'0\'): {kanren_matches}, exactly matching brute-force enumeration over the same real '
                        f'words. unification.unify is exercised directly, binding a free logic variable to the '
                        f'real word\'s second character.')
    except Exception as e:
        r['exact_error'] = f'{type(e).__name__}: {e}'
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(r, indent=2, allow_nan=False) + '\n')


if __name__ == '__main__':
    main()
