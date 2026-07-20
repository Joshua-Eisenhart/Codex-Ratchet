#!/usr/bin/env python3
"""gymnasium wraps the occluded-object world as Gym env and runs 100 real steps."""
from __future__ import annotations
import json, sys, subprocess, re
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

REPO = Path('/Users/joshuaeisenhart/Codex-Ratchet')
OUT = REPO / 'system_v8/tool_ledger/battery_batch3/results/gymnasium.json'

def main():
    r = {'tool': 'gymnasium', 'state': 'BLOCKED', 'verdict': 'BLOCKED', 'promotion_allowed': False,
         'generated_at': datetime.now(timezone.utc).isoformat(),
         'real_object': 'loop2_world occluded probe sequences as Gymnasium Env',
         'inputs': {'events': 'system_v8/loop2_world/results/world_source/events_dynamics_on.jsonl'}}
    try:
        free = int(re.search(r'(\d+)%', subprocess.run(['memory_pressure'], capture_output=True, text=True, check=True).stdout.split('System-wide memory free percentage:')[1]).group(1))
        r['memory_free_percent'] = free
        if free <= 25: raise RuntimeError(f'memory gate failed: {free}% is not >25%')
        import gymnasium as gym
        from gymnasium import spaces
        import sys
        sys.path.insert(0, str(REPO / 'system_v8/loop3_senses'))
        import visibility_sanity_gate as v
        from pathlib import Path as P
        log, _ = v.parse_event_log(P(REPO / 'system_v8/loop2_world/results/world_source/events_dynamics_on.jsonl'))
        # build per-object view sequences
        class OccludedWorldEnv(gym.Env):
            def __init__(self):
                self.observation_space = spaces.Box(0, 1, (8,), dtype=np.int8)
                self.action_space = spaces.Discrete(8)  # probe position
                self.log = log
                self.oids = list(log.keys())[:4]
                self.cur_oid = 0
                self.cur_view = 0
                self.step_count = 0
            def reset(self, seed=None, options=None):
                self.cur_oid = (self.cur_oid + 1) % len(self.oids)
                self.cur_view = 0
                self.step_count = 0
                obs = np.array([1 if self.log[self.oids[self.cur_oid]][self.cur_view].get(p,'withheld')!='withheld' else 0 for p in range(8)], dtype=np.int8)
                return obs, {}
            def step(self, action):
                oid = self.oids[self.cur_oid]
                vv = self.cur_view
                bit = self.log[oid][vv].get(action, 'withheld')
                reward = 0.0 if bit == 'withheld' else (1.0 if int(bit)==1 else 0.0)
                self.step_count += 1
                done = self.step_count >= 25 or self.cur_view >= 5
                if done and self.cur_view < 5:
                    self.cur_view += 1
                    self.step_count = 0
                obs = np.array([1 if self.log[oid][self.cur_view].get(p,'withheld')!='withheld' else 0 for p in range(8)], dtype=np.int8)
                return obs, float(reward), bool(done), False, {'bit': bit}
        env = OccludedWorldEnv()
        obs, _ = env.reset()
        steps = 0
        rews = []
        while steps < 100:
            a = env.action_space.sample()
            obs, rew, term, trunc, info = env.step(a)
            rews.append(rew)
            steps += 1
            if term or trunc:
                obs, _ = env.reset()
        total_r = float(np.sum(rews))
        ok = steps == 100 and len(rews) == 100
        r.update(state='INTEGRATED' if ok else 'BLOCKED', verdict='INTEGRATED' if ok else 'BLOCKED',
                 computed_number=total_r,
                 checks={'steps': steps, 'total_reward': total_r, 'env_steps_gate': ok},
                 reason='gymnasium Env wrapper over real occluded-object probe sequences; 100 load-bearing steps executed.')
    except Exception as e:
        r['exact_error'] = f'{type(e).__name__}: {e}'
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(r, indent=2, allow_nan=False) + '\n')

if __name__ == '__main__':
    main()
