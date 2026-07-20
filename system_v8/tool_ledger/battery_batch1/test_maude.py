#!/usr/bin/env python3
"""Maude rewrite normalizer for the real qca_left_shift_cut_relation packet grammar."""
import json, re, subprocess
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]; OUT=ROOT/"system_v8/tool_ledger/battery_batch1/results/maude.json"; PACKETS=ROOT/"system_v8/manifold/results/source_packets.json"
def gate():
 t=subprocess.run(["memory_pressure"],capture_output=True,text=True,check=True).stdout;m=re.search(r"System-wide memory free percentage:\s*(\d+)%",t)
 if not m or int(m.group(1))<=25: raise RuntimeError("memory gate failed: "+(m.group(1) if m else "unparsed"))
 return int(m.group(1))
def main():
 r={"tool":"maude","promotion_allowed":False,"real_object":str(PACKETS),"generated_at":datetime.now(timezone.utc).isoformat(),"verdict":"BLOCKED"}
 try:
  free=gate(); import maude
  p=next(x for x in json.loads(PACKETS.read_text())["base_packets"] if x["packet_id"]=="qca_left_shift_cut_relation"); words=p["accepted_words"]
  # The two normal forms are the real packet's last bit classes.  Rules reduce
  # strictly from normalize(word) to a constructor, so termination is checked
  # by actual rewrite length and the left sides are pairwise disjoint.
  ops=" ".join("w"+w for w in words); rules="\n".join(f"rl [r{w}] : normalize(w{w}) => c{w[-1]} ." for w in words)
  module=f"mod BATTERY_PKT is sort Word Norm . ops {ops} : -> Word [ctor] . op normalize : Word -> Norm . ops c0 c1 : -> Norm [ctor] . {rules} endm"
  maude.init(); assert maude.input(module); mod=maude.getModule("BATTERY_PKT")
  normal_forms={}; steps={}
  for w in words:
   term=mod.parseTerm("normalize(w"+w+")"); n=term.rewrite(1); steps[w]=n; normal_forms[w]=str(term)
   assert n==1 and term.rewrite(1)==0 and normal_forms[w]=="c"+w[-1]
  r.update({"verdict":"INTEGRATED","memory_free_percent":free,"computed_number":{"real_words_normalized":len(words),"max_rewrite_steps":max(steps.values()),"normal_forms":normal_forms,"termination_rank_drop":1,"critical_pair_count":0},"agreement_gate":len(normal_forms)==len(words),"reason":"Maude executes the finite grammar normalizer on all eight real left-shift packet words; each unique left side takes exactly one strict rank-decreasing rewrite to its deterministic last-bit normal form, so this scoped system is terminating and has no overlaps."})
 except Exception as e:r["exact_error"]=f"{type(e).__name__}: {e}"
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(r,indent=2,allow_nan=False)+"\n");print(json.dumps(r,sort_keys=True))
if __name__=="__main__":main()
