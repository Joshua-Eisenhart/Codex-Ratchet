# spinor_network_hopf_weyl_testbed pre-audit

Scope: read `/tmp/found/sn_build.txt` and `system_v6/foundations/working_math_scaffold_20260609.md`, especially scaffold sections 10.5, 11, and 13. At pre-audit time, `system_v6/sims/spinor_network_hopf_weyl_testbed/` does not exist in this checkout, so these are fail-closed post-build checks against the expected implementation.

Expected paths used below:

```bash
SIM=system_v6/sims/spinor_network_hopf_weyl_testbed; ID=spinor_network_hopf_weyl_testbed; ENV=$SIM/results/${ID}_envelope_results.json
```

## 1. Spinor lift leaks through dissipative channels

Most likely subtle failure: the implementation evolves `psi` through the same Lindblad/GKSL terrain channel used for `rho`, then calls that a spinor lift. The 720 readout is only honest if the lifted spinor transport is fenced to loop geometry/unitary transport (`gamma_f`/`gamma_b`), while dissipative terrain laws act only on `rho`.

Executable source check:

```bash
python3 - <<'PY'
from pathlib import Path
import re, sys
SIM=Path("system_v6/sims/spinor_network_hopf_weyl_testbed")
src="\n".join(p.read_text(errors="ignore") for p in SIM.glob("*") if p.suffix in {".py",".jl"})
bad=[]
for m in re.finditer(r"(?is)(def |function )[^\\n]*(spinor|psi|lift|transport)[\\s\\S]{0,1600}", src):
    block=m.group(0)
    if re.search(r"Lindblad|GKSL|dissip|D\\s*\\[|sigma[_+-]|sigma_minus|sigma_plus|expm\\(0\\.4\\s*\\*\\s*X|terrain", block):
        bad.append(block.splitlines()[0][:160])
if bad:
    print({"ok": False, "spinor_transport_mentions_density_channel_terms": bad[:8]}); sys.exit(1)
need=("gamma_f" in src or "fiber" in src) and ("gamma_b" in src or "base" in src) and re.search(r"psi.*transport|transport.*psi|lifted", src, re.I)
print({"ok": bool(need), "has_loop_geometry_spinor_transport": bool(need)})
sys.exit(0 if need else 1)
PY
```

Result check:

```bash
jq -e '.dual_stack_flow.scope=="loop_geometry_only" and (.dual_stack_flow.no_lindblad_spinor_lift==true) and (.terrain_evolution.carrier=="rho_only")' "$ENV"
```

## 2. Pin block adjusted to manufacture the -1/+1 headline

Most likely subtle failure: one leg silently changes `eta`, loop length, `q1/q2`, `theta/phi`, schedule, or edge couplings until the dual-stack readout looks clean. The build card says the pin block is fixed and identical in all legs; the headline must be computed from that pin, not tuned into existence.

Executable pin check:

```bash
python3 - <<'PY'
from pathlib import Path
import re, sys, json
SIM=Path("system_v6/sims/spinor_network_hopf_weyl_testbed")
files=[SIM/"spinor_network_hopf_weyl_testbed_julia.jl",SIM/"spinor_network_hopf_weyl_testbed_jax.py",SIM/"spinor_network_hopf_weyl_testbed_pytorch.py"]
required=[r"N\\s*=\\s*6", r"pi\\s*/\\s*8", r"pi\\s*/\\s*20", r"0\\.3\\s*\\*?\\s*i", r"0\\.2\\s*\\*?\\s*i", r"q1\\s*=\\s*0\\.3", r"q2\\s*=\\s*0\\.3", r"theta\\s*=\\s*pi\\s*/\\s*2", r"phi\\s*=\\s*pi\\s*/\\s*2", r"0\\.4\\s*\\*\\s*X"]
bad={}
for f in files:
    text=f.read_text(errors="ignore")
    miss=[pat for pat in required if not re.search(pat,text)]
    tune=re.findall(r"optimi[sz]e|minimi[sz]e|grid_search|target_phase|force_720|tune|fit", text, flags=re.I)
    if miss or tune: bad[str(f)]={"missing":miss,"tuning_terms":sorted(set(tune))}
print(json.dumps({"ok": not bad, "violations": bad}, indent=2))
sys.exit(0 if not bad else 1)
PY
```

Envelope pin equality check:

```bash
jq -e '.pin_block.identical_literal_across_legs==true and (.engines|to_entries|all(.value.pin_sha256 == $.pin_block.sha256))' "$ENV"
```

## 3. Density-only control is asserted instead of computed through the same transport

Most likely subtle failure: the density control is hardcoded to zero because `rho=psi psi^dagger` is phase-blind, without actually transporting `rho` by the corresponding `U rho U^dagger` pipeline at each step. That makes the control unable to catch implementation errors.

Executable source check:

```bash
python3 - <<'PY'
from pathlib import Path
import re, sys, json
SIM=Path("system_v6/sims/spinor_network_hopf_weyl_testbed")
src="\n".join(p.read_text(errors="ignore") for p in SIM.glob("*") if p.suffix in {".py",".jl"})
has_density_transport=bool(re.search(r"rho[^\\n]{0,80}(U|transport)|U\\s*@\\s*rho\\s*@|U\\s*\\*\\s*rho\\s*\\*", src, re.I))
hardcoded_zero=bool(re.search(r"density[^\\n]{0,80}(defect|residual)[^\\n]{0,80}=\\s*(0|0\\.0|zeros)", src, re.I))
same_transport=bool(re.search(r"density[^\\n]{0,120}same[^\\n]{0,80}transport|same_transport[^\\n]{0,80}rho", src, re.I))
ok=has_density_transport and same_transport and not hardcoded_zero
print(json.dumps({"ok":ok,"has_density_transport":has_density_transport,"same_transport_named":same_transport,"hardcoded_zero_suspected":hardcoded_zero}, indent=2))
sys.exit(0 if ok else 1)
PY
```

Result check:

```bash
jq -e '[.engines[].readouts.dual_stack_flow.density_only_control.per_node_step_defects[]] | length==12 and all(abs < 1e-10)' "$ENV"
```

## 4. Tensor-network readout is a synthetic proxy, not carrier-backed

Most likely subtle failure from scaffold 10.5: ITensors/quimb constructs a generic six-site chain or Bell/random state and computes a cut value, but the state is not built from the node spinors/densities and edge couplings, especially the chord `(0,3)`.

Executable source check:

```bash
python3 - <<'PY'
from pathlib import Path
import re, sys, json
SIM=Path("system_v6/sims/spinor_network_hopf_weyl_testbed")
texts={str(p):p.read_text(errors="ignore") for p in SIM.glob("*") if p.suffix in {".py",".jl"}}
tn="\n".join(t for t in texts.values() if re.search(r"ITensors|quimb|qtn|MPS|MatrixProduct", t))
carrier_refs=len(re.findall(r"psi_|rho_|node_states|coupling|edge|chord|0\\s*,\\s*3|eta|phi|chi", tn))
synthetic=bool(re.search(r"random|randn|bell|ghz|zeros\\(|ones\\(|product_state|computational_state", tn, re.I))
ok=carrier_refs>=6 and not synthetic
print(json.dumps({"ok":ok,"carrier_ref_count":carrier_refs,"synthetic_state_terms":synthetic}, indent=2))
sys.exit(0 if ok else 1)
PY
```

Tool-map result check:

```bash
jq -e '.tool_exercise_map[] | select(.tool=="ITensors" or .tool=="quimb" or .tool=="quimb.tensor") | (.genuinely_on_carrier==true and (.computed_what|test("chord|0,3|node|coupling|spinor|rho";"i")) and (.capability_receipt_path|length>0))' "$ENV"
```

## 5. PyG MessagePassing does not carry order-sensitive quaternion edge updates

Most likely subtle failure: PyG is present and `MessagePassing.propagate()` runs, but the message is a linear/additive feature pass or edge attribute concat. The build requires the message function to multiply quaternion edge updates in an order-sensitive way and show a noncommutative gap against a commuting control.

Executable source check:

```bash
python3 - <<'PY'
from pathlib import Path
import re, sys, json
pt=Path("system_v6/sims/spinor_network_hopf_weyl_testbed/spinor_network_hopf_weyl_testbed_pytorch.py")
text=pt.read_text(errors="ignore")
msg=re.search(r"class\\s+\\w+\\(\\s*MessagePassing\\s*\\)[\\s\\S]+?(?=\\nclass\\s|\\nif __name__|\\Z)", text)
block=msg.group(0) if msg else ""
has_message="def message" in block and "edge_attr" in block
has_qmul=bool(re.search(r"quat|quaternion|hamilton", block, re.I)) and bool(re.search(r"\\*|matmul|einsum|cross", block))
has_order=bool(re.search(r"q_edge.*q_node|edge.*source|source.*edge|left.*right|order", block, re.I))
linear_only=bool(re.search(r"Linear\\(|torch\\.cat|x_j\\s*\\+", block)) and not has_qmul
ok=has_message and has_qmul and has_order and not linear_only
print(json.dumps({"ok":ok,"has_message":has_message,"has_quaternion_multiply":has_qmul,"order_sensitive_terms":has_order,"linear_only_suspected":linear_only}, indent=2))
sys.exit(0 if ok else 1)
PY
```

Result check:

```bash
jq -e '.engines.pytorch.readouts.pyg_quaternion_message.noncommutative_message_gap > 1e-9 and .engines.pytorch.readouts.pyg_quaternion_message.commuting_edge_control_gap < 1e-10' "$ENV"
```

## 6. Stage-token placement is mislabeled

Most likely subtle failure: the report uses the scheduled labels (`TiSe UP`, etc.) but the code executes the wrong order, wrong terrain, or wrong operator. `UP` must mean operator-first `Phi_T(O(rho))`; `DOWN` must mean terrain-first `O(Phi_T(rho))`.

Executable schedule check:

```bash
python3 - <<'PY'
import json, sys
from pathlib import Path
ENV=Path("system_v6/sims/spinor_network_hopf_weyl_testbed/results/spinor_network_hopf_weyl_testbed_envelope_results.json")
data=json.loads(ENV.read_text())
expected=[
  ("TiSe","UP","operator_first","Ti","Se"),
  ("NeTi","DOWN","terrain_first","Ti","Ne"),
  ("NiFe","DOWN","terrain_first","Fe","Ni"),
  ("FeSi","UP","operator_first","Fe","Si"),
  ("FiSe","UP","operator_first","Fi","Se"),
  ("TeSi","UP","operator_first","Te","Si"),
  ("NiTe","DOWN","terrain_first","Te","Ni"),
  ("NeFi","DOWN","terrain_first","Fi","Ne"),
]
stages=data.get("schedule",{}).get("stages") or data.get("readouts",{}).get("order_gaps",{}).get("stages") or []
got=[(s.get("token"),s.get("direction"),s.get("placement"),s.get("operator"),s.get("terrain")) for s in stages]
ok=got==expected
print(json.dumps({"ok":ok,"expected":expected,"got":got}, indent=2))
sys.exit(0 if ok else 1)
PY
```

Source order check:

```bash
rg -n 'operator_first|terrain_first|Phi_T\\(O\\(rho\\)\\)|O\\(Phi_T\\(rho\\)\\)|TiSe|NeTi|NiFe|FeSi|FiSe|TeSi|NiTe|NeFi' "$SIM"
```

## 7. Deprecated `torch_ga` remains on the claim path instead of `kingdon`

Most likely subtle failure: the PyTorch leg reuses older `torch_ga` patterns because the generic validator still recognizes it as aligned. v6 current convention says `torch_ga/clifford -> kingdon`; this build card explicitly says kingdon, not `torch_ga`.

Executable source check:

```bash
rg -n 'torch_ga|GeometricAlgebra|from clifford|import clifford' "$SIM" && exit 1 || true
```

Result check:

```bash
jq -e '(.engines.pytorch.packages_used|index("kingdon")) and ((.engines.pytorch.packages_used + .engines.pytorch.aligned_packages_load_bearing + .claim_path_tools)|index("torch_ga")|not)' "$ENV"
```

Capability gate:

```bash
python3 scripts/verify_load_bearing_has_capability_probe.py --sim "$SIM/${ID}_pytorch.py"
```

## 8. Topology label-shuffle control cannot fail

Most likely subtle failure: the topology control shuffles labels after features are computed, or compares sorted invariants that are label-invariant by construction. The control must actually change carrier features/weights before GUDHI/TopoNetX/XGI recompute; otherwise it is decorative.

Executable source check:

```bash
python3 - <<'PY'
from pathlib import Path
import re, sys, json
src="\n".join(p.read_text(errors="ignore") for p in Path("system_v6/sims/spinor_network_hopf_weyl_testbed").glob("*") if p.suffix in {".py",".jl"})
shuffle_blocks=re.findall(r"(?is)(label[^\\n]{0,40}shuffle|shuffle[^\\n]{0,40}label)[\\s\\S]{0,1000}", src)
joined="\n".join(shuffle_blocks)
changes_features=bool(re.search(r"feature|weight|filtration|edge_attr|node_state|coupling|rho|psi", joined, re.I))
recomputes=bool(re.search(r"gudhi|SimplexTree|toponetx|xgi|persistence|boundary", joined, re.I))
ok=bool(shuffle_blocks) and changes_features and recomputes
print(json.dumps({"ok":ok,"shuffle_blocks":len(shuffle_blocks),"changes_features_before_recompute":changes_features,"recomputes_topology":recomputes}, indent=2))
sys.exit(0 if ok else 1)
PY
```

Result check:

```bash
jq -e '.topology_controls.label_shuffle.feature_delta > 1e-9 and .topology_controls.label_shuffle.changed_features==true and .topology_controls.label_shuffle.changed_topology==true' "$ENV"
```

## 9. Terrain laws or Ni Pit/Source signs drift under scheduled tokens

Most likely subtle failure: the code implements generic amplitude damping/dephasing but swaps `sigma_-`/`sigma_+`, L/R Hamiltonian signs, or Type-1/Type-2 signs. This can make the schedule look right while executing the wrong terrain law.

Executable source check:

```bash
python3 - <<'PY'
from pathlib import Path
import re, sys, json
src="\n".join(p.read_text(errors="ignore") for p in Path("system_v6/sims/spinor_network_hopf_weyl_testbed").glob("*") if p.suffix in {".py",".jl"})
checks={
  "sigma_minus_defined": bool(re.search(r"sigma(_minus|-)|sigma_m", src)),
  "sigma_plus_defined": bool(re.search(r"sigma(_plus|\\+)|sigma_p", src)),
  "Ni_Pit_uses_minus": bool(re.search(r"Ni[^\\n]{0,40}Pit[\\s\\S]{0,300}(sigma(_minus|-)|sigma_m)", src, re.I)),
  "Ni_Source_uses_plus": bool(re.search(r"Ni[^\\n]{0,40}Source[\\s\\S]{0,300}(sigma(_plus|\\+)|sigma_p)", src, re.I)),
  "H_L_positive_H0": bool(re.search(r"H_L\\s*=\\s*\\+?\\s*H_0|HL\\s*=\\s*\\+?\\s*H0", src)),
  "H_R_negative_H0": bool(re.search(r"H_R\\s*=\\s*-\\s*H_0|HR\\s*=\\s*-\\s*H0", src)),
}
ok=all(checks.values())
print(json.dumps({"ok":ok, **checks}, indent=2))
sys.exit(0 if ok else 1)
PY
```

Result check:

```bash
jq -e '.terrain_laws.Ni_Pit.jump=="sigma_minus" and .terrain_laws.Ni_Source.jump=="sigma_plus" and .chirality_control.sign_erasure_kills_gap==true' "$ENV"
```

## 10. Envelope hides an unclean 720 pattern behind rounded signs or aggregate divergence

Most likely subtle failure: the code reports a boolean `dual_stack_720=true`, rounded `-1/+1`, or a single averaged scalar while per-node phases disagree. The build card's honesty rule requires verbatim per-node phases and an honest-divergence case when the pinned geometry does not give a clean pattern.

Executable result check:

```bash
python3 - <<'PY'
import json, math, sys
from pathlib import Path
ENV=Path("system_v6/sims/spinor_network_hopf_weyl_testbed/results/spinor_network_hopf_weyl_testbed_envelope_results.json")
d=json.loads(ENV.read_text())
flow=d.get("dual_stack_flow") or d.get("readouts",{}).get("dual_stack_flow") or {}
nodes=flow.get("per_node") or []
tol=float(flow.get("phase_tolerance", 1e-6))
def near_mod(x,target,tol):
    return abs(((x-target+math.pi)%(2*math.pi))-math.pi) <= tol
bad=[]
clean=[]
for row in nodes:
    sid=row.get("node")
    phases1=row.get("single_loop_component_phase_shifts", [])
    phases2=row.get("dual_stack_component_phase_shifts", [])
    sd=float(row.get("single_loop_spinor_return_defect", 999))
    dd=float(row.get("dual_stack_spinor_return_defect", 999))
    c=(len(phases1)==2 and len(phases2)==2 and all(near_mod(float(p), math.pi, tol) for p in phases1)
       and all(near_mod(float(p), 0.0, tol) for p in phases2) and abs(sd-2.0)<=1e-6 and dd<=1e-6)
    clean.append(c)
    if not {"node","single_loop_component_phase_shifts","dual_stack_component_phase_shifts","single_loop_spinor_return_defect","dual_stack_spinor_return_defect"} <= set(row):
        bad.append({"node":sid,"missing_fields":True})
declared=flow.get("clean_minus_plus_pattern")
honest_divergence=flow.get("honest_geometry_divergence") is True and flow.get("headline_claim") in {"pattern_not_clean","raw_phases_reported_no_clean_720_claim"}
ok=(len(nodes)==6 and not bad and ((all(clean) and declared is True) or ((not all(clean)) and declared is False and honest_divergence)))
print(json.dumps({"ok":ok,"per_node_count":len(nodes),"clean_by_node":clean,"declared_clean":declared,"honest_divergence":honest_divergence,"bad":bad}, indent=2))
sys.exit(0 if ok else 1)
PY
```

Generic validator still required, but it is not sufficient:

```bash
/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --require-source-backed "$ENV"
```

## Required numbers for the headline

The headline may say a clean dual-stack 720 spinor flow only if all of these numeric conditions hold on the pinned geometry, without parameter tuning:

- Per engine, `reads_peer_result=false`; all three legs expose the same six `per_node` rows for the dual-stack readout.
- For every node, single-loop spinor component phase shifts are both `pi mod 2pi` within the declared tolerance, and `single_loop_spinor_return_defect` is approximately `2.0` for normalized `psi`.
- For every node, dual-stack component phase shifts are both `0 mod 2pi` within tolerance, and `dual_stack_spinor_return_defect <= 1e-6` or a stricter declared tolerance.
- Density-only control reports the same transport pipeline on `rho`, with every per-node/per-step density defect `<= 1e-10`; source must show the computation, not assignment to zero.
- Classical SO(3) vector transport does not show the spinor sign structure: its single-loop vector defect should be near zero for a `2pi` rotation, not near `2.0`, and the result should mark `classical_no_sign_structure=true`.
- The envelope compares like-named scalars only; no aggregate can replace the per-node phase and defect arrays.

Honest-divergence case: if any pinned node is not clean `-1/+1`, the sim can still pass as a scratch diagnostic only when it reports the raw phases and defects verbatim, sets `clean_minus_plus_pattern=false`, sets an explicit `honest_geometry_divergence=true` or equivalent field, and avoids any headline stronger than `pattern_not_clean_from_pinned_geometry`. That is a finding, not a build failure; hiding it behind rounding, retuning, or averaged divergence is a failure.
