#!/usr/bin/env python3
"""Record the exact jax-verify import boundary before tournament-GRU bounds."""
from __future__ import annotations
import json, subprocess, re
from datetime import datetime, timezone
from pathlib import Path
REPO=Path('/Users/joshuaeisenhart/Codex-Ratchet'); OUT=REPO/'system_v8/tool_ledger/battery_batch1/results/jax_verify.json'
def main():
 r={'tool':'jax-verify','state':'BLOCKED','verdict':'BLOCKED','promotion_allowed':False,'generated_at':datetime.now(timezone.utc).isoformat(),'real_object':'carrier_tournament_v1 16-to-11 GRU family','inputs':{'gru_lane':'system_v8/loop3_senses/carrier_tournament_v1.py'},'attempted_computation':'interval/bound propagation for a tiny trained tournament-GRU family net'}
 try:
  free=int(re.search(r'(\d+)%',subprocess.run(['memory_pressure'],capture_output=True,text=True,check=True).stdout.split('System-wide memory free percentage:')[1]).group(1)); r['memory_free_percent']=free
  if free<=25: raise RuntimeError(f'memory gate failed: {free}% is not >25%')
  import jax_verify # noqa: F401
  r['exact_error']='unexpectedly imported; no bound computation was executed'
 except Exception as e: r['exact_error']=f'{type(e).__name__}: {e}'; r['retry_condition']='Install a jax-verify release compatible with installed jax 0.10.1 (current package references removed jax.lax.standard_naryop).'
 OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(r,indent=2)+'\n')
if __name__=='__main__': main()
