#!/usr/bin/env python3
"""UMAP embedding of the 384 real senses_v2 trajectory states against PCA."""
import json, re, subprocess
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[3]; OUT=ROOT/"system_v8/tool_ledger/battery_batch1/results/umap_learn.json"; TRAJ=ROOT/"system_v8/loop3_senses/results/senses_v2_slow_memory/state_trajectories.json"
def gate():
 t=subprocess.run(["memory_pressure"],capture_output=True,text=True,check=True).stdout;m=re.search(r"System-wide memory free percentage:\s*(\d+)%",t)
 if not m or int(m.group(1))<=25: raise RuntimeError("memory gate failed: "+(m.group(1) if m else "unparsed"))
 return int(m.group(1))
def main():
 r={"tool":"umap-learn","promotion_allowed":False,"real_object":str(TRAJ),"generated_at":datetime.now(timezone.utc).isoformat(),"verdict":"BLOCKED"}
 try:
  free=gate(); import umap
  from sklearn.decomposition import PCA
  from sklearn.manifold import trustworthiness
  d=json.loads(TRAJ.read_text()); rows=[]
  for obj in d["object_order"]:
   for state in d["candidate_reset_fast"][obj]: rows.append(state["quantum_readout"]+state["m_slow_summary"])
  X=np.asarray(rows,float); X=(X-X.mean(0))/np.maximum(X.std(0),1e-12)
  embedding=umap.UMAP(n_neighbors=15,min_dist=0.1,n_components=2,metric="euclidean",random_state=20260719).fit_transform(X)
  pca=PCA(n_components=2,random_state=20260719).fit_transform(X); tu=float(trustworthiness(X,embedding,n_neighbors=10)); tp=float(trustworthiness(X,pca,n_neighbors=10))
  r.update({"verdict":"INTEGRATED","memory_free_percent":free,"computed_number":{"real_states":int(X.shape[0]),"feature_width":int(X.shape[1]),"umap_trustworthiness_k10":tu,"pca_trustworthiness_k10":tp,"umap_minus_pca":tu-tp},"agreement_gate":tu>tp,"reason":"UMAP fit is load-bearing on all saved real rho_fast Pauli and m_slow trajectory features; the local-neighborhood trustworthiness gate is compared directly to a same-data PCA control."})
 except Exception as e:r["exact_error"]=f"{type(e).__name__}: {e}"
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(r,indent=2,allow_nan=False)+"\n");print(json.dumps(r,sort_keys=True))
if __name__=="__main__":main()
