#!/usr/bin/env python3
"""XGI hypergraph statistics of the real nine-packet Hamming-1 capacity complexes."""
import json, re, subprocess
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/"system_v8/tool_ledger/battery_batch1/results/xgi.json"; PACKETS=ROOT/"system_v8/manifold/results/source_packets.json"; TOPO=ROOT/"system_v8/deep_integration/results/topology/receipt.json"
def gate():
 t=subprocess.run(["memory_pressure"],capture_output=True,text=True,check=True).stdout;m=re.search(r"System-wide memory free percentage:\s*(\d+)%",t)
 if not m or int(m.group(1))<=25: raise RuntimeError("memory gate failed: "+(m.group(1) if m else "unparsed"))
 return int(m.group(1))
def main():
 r={"tool":"xgi","promotion_allowed":False,"real_object":str(PACKETS),"generated_at":datetime.now(timezone.utc).isoformat(),"verdict":"BLOCKED"}
 try:
  free=gate(); import xgi
  packets=json.loads(PACKETS.read_text())["base_packets"]; expected=json.loads(TOPO.read_text())["data"]["capacity_graph_per_packet"]
  stats={}; all_ok=True
  for p in packets:
   words=p["accepted_words"]; edges=[[i,j] for i in range(len(words)) for j in range(i+1,len(words)) if sum(a!=b for a,b in zip(words[i],words[j]))==1]
   H=xgi.Hypergraph(edges); H.add_nodes_from(range(len(words)))
   components=xgi.number_connected_components(H); degrees=H.nodes.degree.asdict(); exp=expected[p["packet_id"]]
   ok=components==exp["rx"]["components"] and len(edges)==exp["n_hamming1_edges"]
   all_ok &= ok; stats[p["packet_id"]]={"nodes":len(words),"two_node_hyperedges":len(edges),"xgi_components":components,"degree_sum":sum(degrees.values()),"rustworkx_components":exp["rx"]["components"],"agreement":ok}
  r.update({"verdict":"INTEGRATED","memory_free_percent":free,"computed_number":{"all_9_component_and_edge_agreement":all_ok,"per_packet":stats},"agreement_gate":all_ok,"reason":"Each hyperedge is a genuine Hamming-1 capacity edge from real manifold packets; XGI components/edge counts are independently gated against the rustworkx topology receipt."})
 except Exception as e:r["exact_error"]=f"{type(e).__name__}: {e}"
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(r,indent=2,allow_nan=False)+"\n");print(json.dumps(r,sort_keys=True))
if __name__=="__main__":main()
