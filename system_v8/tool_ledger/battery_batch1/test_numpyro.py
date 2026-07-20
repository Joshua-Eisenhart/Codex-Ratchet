#!/usr/bin/env python3
"""NumPyro posterior recomputation on one real senses_v2 likelihood update."""
from __future__ import annotations
import json, sys, subprocess, re
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

REPO=Path('/Users/joshuaeisenhart/Codex-Ratchet'); OUT=REPO/'system_v8/tool_ledger/battery_batch1/results/numpyro.json'
sys.path.insert(0,str(REPO/'system_v8/loop3_senses'))
def main():
    result={'tool':'numpyro','state':'BLOCKED','verdict':'BLOCKED','promotion_allowed':False,'generated_at':datetime.now(timezone.utc).isoformat(),'inputs':{'events':'system_v8/loop2_world/results/world_source/events_dynamics_on.jsonl','senses_source':'system_v8/loop3_senses/senses_v2_slow_memory.py'}}
    try:
        free=int(re.search(r'(\d+)%',subprocess.run(['memory_pressure'],capture_output=True,text=True,check=True).stdout.split('System-wide memory free percentage:')[1]).group(1)); result['memory_free_percent']=free
        if free<=25: raise RuntimeError(f'memory gate failed: {free}% is not >25%')
        import numpyro.distributions as dist
        import senses_v2_slow_memory as s
        import visibility_sanity_gate as visibility
        receipt=json.load(open(s.WORLD_RECEIPT)); rules={int(k):tuple(v) for k,v in receipt['parameters']['rule_family'].items()}
        log,_=visibility.parse_event_log(s.EVENTS); channels,_=visibility.load_stage_channels(json.load(open(s.STAGE64)),encoder_channel_fix=False)
        words,rs,h=s.build_hypotheses(rules); engine=s.QuantumReadoutBayes(channels,visibility,words,rs,h)
        masks={v:{tuple(log[o][v][p]!='withheld' for p in range(s.N_BITS)) for o in log} for v in range(s.N_VIEWS)}
        engine.calibrate_sigma(masks); oid='obj-000'; view=2; mask=tuple(log[oid][view][p]!='withheld' for p in range(s.N_BITS))
        actual=engine.readout(engine.actual_density(visibility.RHO0,lambda vv,p: None if log[oid][vv][p]=='withheld' else log[oid][vv][p],view,frozen=False))
        candidates=engine.reset_candidate_readouts(view,mask); ll=-.5*np.sum((candidates-actual[None,:])**2,axis=1)/(engine.sigma**2)
        # NumPyro's Categorical log_prob supplies the hidden-hypothesis prior term;
        # the real readout likelihood above is the only evidence term.
        prior=np.full(len(h),1/len(h)); lp=np.asarray(dist.Categorical(probs=prior).log_prob(np.arange(len(h))))+ll
        post=np.exp(lp-lp.max()); post/=post.sum(); source=engine.update_posterior(prior,actual,candidates)
        target=0; bit=np.asarray([((int(word)>>target)&1) for word in words]); npy_bit=float(post[bit==1].sum()); source_bit=float(source[bit==1].sum()); delta=float(np.max(np.abs(post-source)))
        ok=delta<1e-12
        result.update(state='INTEGRATED' if ok else 'BLOCKED',verdict='INTEGRATED' if ok else 'BLOCKED',real_object=f'{oid} view-{view} senses_v2 quantum-readout likelihood',computed_number=delta,checks={'object':oid,'view':view,'hypotheses':len(h),'sigma':float(engine.sigma),'numpyro_hidden_bit_p1':npy_bit,'m_slow_hidden_bit_p1':source_bit,'max_hypothesis_posterior_abs_delta':delta,'agreement_gate':ok},reason='numpyro.distributions.Categorical prior plus the real quantum-readout likelihood recomputed the 1024-hypothesis m_slow posterior; hidden-bit marginal is derived from that posterior.')
    except Exception as e: result['exact_error']=f'{type(e).__name__}: {e}'
    OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
if __name__=='__main__': main()
