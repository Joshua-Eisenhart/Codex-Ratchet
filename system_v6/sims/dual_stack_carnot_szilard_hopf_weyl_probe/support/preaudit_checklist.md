# Dual-Stack Carnot/Szilard Pre-Audit

Scope: adversarial pre-audit for `dual_stack_carnot_szilard_hopf_weyl_probe`, based on `/tmp/found/ds_build.txt` and `system_v6/foundations/working_math_scaffold_20260609.md` section 14.

Current repo fact checked during pre-audit: `system_v6/sims/` is absent in this checkout. Treat every check below as fail-closed until the builder creates:

```bash
find system_v6/sims/dual_stack_carnot_szilard_hopf_weyl_probe -maxdepth 3 -type f -print
```

Expected target:

```bash
SIM=system_v6/sims/dual_stack_carnot_szilard_hopf_weyl_probe
RESULT=$SIM/results/dual_stack_carnot_szilard_hopf_weyl_probe_envelope_results.json
```

## 0. Artifact Existence And Ceiling

Failure mode: the builder reports a successful sim without creating the exact target files or with a promoted claim ceiling.

Grep/jq/python checks:

```bash
SIM=system_v6/sims/dual_stack_carnot_szilard_hopf_weyl_probe; test -d "$SIM" && find "$SIM" -maxdepth 2 -type f | sort
```

```bash
RESULT=system_v6/sims/dual_stack_carnot_szilard_hopf_weyl_probe/results/dual_stack_carnot_szilard_hopf_weyl_probe_envelope_results.json; jq -e '.schema_version=="three_engine_sim_result_v1" and .classification=="scratch_diagnostic" and .promotion_allowed==false and .formal_admission_allowed==false and .engine_contract.mode=="all_three_full_sims"' "$RESULT"
```

```bash
/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch system_v6/sims/dual_stack_carnot_szilard_hopf_weyl_probe/results/dual_stack_carnot_szilard_hopf_weyl_probe_envelope_results.json
```

Genuine condition: all four source runners exist, each engine ran, envelope validates with `--require-pytorch`, and ceiling remains `scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`.

## A. Landauer Ledger Fakery

Most probable subtle failure: `information_gained`, `work_extracted`, and `landauer_reset_cost` are defined from each other or from hardcoded `ln2`, so the bound passes by construction. The ledger must be recomputable from actual density states:

- `I_gained = S(rho_S) + S(rho_M) - S(rho_SM)` after `M`.
- `p_excited = Tr[(I_S tensor |1><1|_M) rho_SM_before_reset]`.
- `reset_cost >= ln(2) * p_excited` in the requested natural units.
- `work_extracted` must come from the feedback energy/free-energy change, not from `ln2 * I_gained`.

Grep check:

```bash
rg -n "information_gained|I_gained|mutual_information|work_extracted|Landauer|landauer|reset_cost|p_excited|ln\\(2\\)|log\\(2\\)" system_v6/sims/dual_stack_carnot_szilard_hopf_weyl_probe
```

Red flags in source:

```bash
rg -n "work_extracted\\s*=\\s*.*information|information_gained\\s*=\\s*.*work|landauer.*=\\s*.*information|net.*=\\s*0\\.0|W_extracted\\s*=\\s*log\\(2\\)|I_gained\\s*=\\s*1\\.0|asserted_precomputed|by[-_ ]construction" system_v6/sims/dual_stack_carnot_szilard_hopf_weyl_probe
```

jq check:

```bash
RESULT=system_v6/sims/dual_stack_carnot_szilard_hopf_weyl_probe/results/dual_stack_carnot_szilard_hopf_weyl_probe_envelope_results.json; jq -e '.legality_ledgers.szilard | has("information_gained") and has("work_extracted") and has("landauer_reset_cost") and has("p_excited_before_reset") and has("bound_margin") and (.bound_margin <= 1e-9)' "$RESULT"
```

Python recomputation check:

```bash
python3 - <<'PY'
import json, math, numpy as np
from pathlib import Path
R=Path("system_v6/sims/dual_stack_carnot_szilard_hopf_weyl_probe/results/dual_stack_carnot_szilard_hopf_weyl_probe_envelope_results.json")
d=json.loads(R.read_text())
tol=1e-8

def arr(x):
    a=np.array(x, dtype=complex)
    return a
def vn(r):
    w=np.linalg.eigvalsh((r+r.conj().T)/2)
    return float(-sum(v*math.log(v) for v in w if v>1e-14))
def ptrace_system(r):
    x=r.reshape(2,2,2,2)  # S,M,S',M'
    return np.einsum("smtm->st", x)
def ptrace_memory(r):
    x=r.reshape(2,2,2,2)
    return np.einsum("smsn->mn", x)

st=d["states"]
rhoM=arr(st["after_M_joint"])
rho_preR=arr(st.get("before_R_joint", st["after_F_joint"]))
I=vn(ptrace_system(rhoM))+vn(ptrace_memory(rhoM))-vn(rhoM)
P1=np.diag([0,1])
p_exc=float(np.trace(np.kron(np.eye(2),P1)@rho_preR).real)
ledger=d["legality_ledgers"]["szilard"]
assert abs(I-ledger["information_gained"]) < tol, (I, ledger["information_gained"])
assert abs(p_exc-ledger["p_excited_before_reset"]) < tol, (p_exc, ledger["p_excited_before_reset"])
assert ledger["landauer_reset_cost"] + tol >= math.log(2)*p_exc
assert ledger["work_extracted"] - math.log(2)*ledger["information_gained"] <= tol
print("LANDAUER_LEDGER_RECOMPUTES")
PY
```

GENUINE positive condition: the recomputed numbers match the ledger and the bound margin is `<= 1e-8`. Honest-divergence condition: if the bound is violated, the result may still be an honest negative result only if `all_pass=false` and the envelope explicitly says the encoding is broken; it is not a successful witness.

## B. Measurement Channel Honesty

Most probable subtle failure: `M` is implemented as branch bookkeeping over a classical outcome instead of a real CPTP channel on `system tensor memory`.

Required object: `M` is a 4-dimensional input/output channel, represented by 4x4 Kraus operators or a 16x16 Choi matrix, with TP defect near zero, Choi minimum eigenvalue nonnegative, and a measured joint output that correlates system and memory.

Grep check:

```bash
rg -n "measurement|measure|CNOT|controlled|kraus|K0|K1|choi|CPTP|tensor|kron|system.*memory|memory.*system" system_v6/sims/dual_stack_carnot_szilard_hopf_weyl_probe
```

Red flags:

```bash
rg -n "if .*outcome|for .*outcome|branch|measured_branch|classical_outcome|prob0.*rho0|prob1.*rho1|M\\s*=\\s*\\{|measurement_map.*dict" system_v6/sims/dual_stack_carnot_szilard_hopf_weyl_probe
```

jq check:

```bash
RESULT=system_v6/sims/dual_stack_carnot_szilard_hopf_weyl_probe/results/dual_stack_carnot_szilard_hopf_weyl_probe_envelope_results.json; jq -e '.channels.M.kind=="cptp_joint_measurement" and .channels.M.input_dim==4 and .channels.M.output_dim==4 and (.channels.M.tp_defect < 1e-8) and (.channels.M.choi_min_eig > -1e-8) and (.legality_ledgers.szilard.information_gained > 1e-8)' "$RESULT"
```

Python Choi/Kraus check:

```bash
python3 - <<'PY'
import json, numpy as np
from pathlib import Path
d=json.loads(Path("system_v6/sims/dual_stack_carnot_szilard_hopf_weyl_probe/results/dual_stack_carnot_szilard_hopf_weyl_probe_envelope_results.json").read_text())
M=d["channels"]["M"]
tol=1e-8
if "kraus" in M:
    Ks=[np.array(k, dtype=complex) for k in M["kraus"]]
    assert all(K.shape==(4,4) for K in Ks)
    tp=sum(K.conj().T@K for K in Ks)
    assert np.linalg.norm(tp-np.eye(4)) < tol
    choi=sum(np.outer(K.reshape(-1, order="F"), K.reshape(-1, order="F").conj()) for K in Ks)
else:
    choi=np.array(M["choi"], dtype=complex)
assert choi.shape==(16,16)
assert np.linalg.eigvalsh((choi+choi.conj().T)/2).min() > -tol
rho=np.array(d["states"]["after_M_joint"], dtype=complex)
assert rho.shape==(4,4)
assert abs(np.trace(rho)-1) < tol
print("MEASUREMENT_CHANNEL_CPTP_JOINT")
PY
```

GENUINE positive condition: `M` is Choi-checkable as a joint CPTP channel and the post-measurement joint state carries nonzero system-memory mutual information. If only per-outcome branch densities exist, the measurement legality claim is decorative.

## C. Feedback Conditioning

Most probable subtle failure: `F` is selected by a hidden Python/Julia branch variable (`if outcome == 1`) instead of being a conditional operation on the memory state inside the density formalism.

Required object: a joint 4x4 feedback unitary/channel conditioned on memory projectors, such as `F = U0 tensor |0><0|_M + U1 tensor |1><1|_M` depending on the chosen tensor order, applied to `rho_SM_after_M`.

Grep check:

```bash
rg -n "feedback|conditional|controlled|memory_projector|P0|P1|pi.flip|sigmax|kron|tensor|after_M|after_F" system_v6/sims/dual_stack_carnot_szilard_hopf_weyl_probe
```

Red flags:

```bash
rg -n "if .*memory|if .*outcome|if .*branch|measured_branch|feedback.*branch|F.*outcome|selected.*unitary|hidden.*classical" system_v6/sims/dual_stack_carnot_szilard_hopf_weyl_probe
```

jq check:

```bash
RESULT=system_v6/sims/dual_stack_carnot_szilard_hopf_weyl_probe/results/dual_stack_carnot_szilard_hopf_weyl_probe_envelope_results.json; jq -e '.channels.F.kind=="memory_conditioned_joint_unitary" and .channels.F.input_dim==4 and .channels.F.output_dim==4 and (.channels.F.unitary_defect < 1e-8) and (.states.after_M_joint|type=="array") and (.states.after_F_joint|type=="array")' "$RESULT"
```

Python density-formalism check:

```bash
python3 - <<'PY'
import json, numpy as np
from pathlib import Path
d=json.loads(Path("system_v6/sims/dual_stack_carnot_szilard_hopf_weyl_probe/results/dual_stack_carnot_szilard_hopf_weyl_probe_envelope_results.json").read_text())
tol=1e-8
F=np.array(d["channels"]["F"]["matrix"], dtype=complex)
rhoM=np.array(d["states"]["after_M_joint"], dtype=complex)
rhoF=np.array(d["states"]["after_F_joint"], dtype=complex)
assert F.shape==(4,4)
assert np.linalg.norm(F.conj().T@F-np.eye(4)) < tol
assert np.linalg.norm(F@rhoM@F.conj().T-rhoF) < tol
print("FEEDBACK_CONDITIONED_ON_MEMORY_STATE")
PY
```

GENUINE positive condition: the recorded `after_F_joint` is obtained from a single joint operator/channel acting on `after_M_joint`. Hidden branch control kills the feedback legality claim even if scalar ledgers look right.

## D. Classical Control Must Run The Same Pipeline

Most probable subtle failure: the diagonal/decohered carrier control is short-circuited, with `W_qit_coherence = 0` asserted by label rather than computed by the same pipeline.

Required object: diagonal-only `rho` runs through the same `D`, `M`, `F`, `R`, Type1, Type2, ledger, and readout functions. `W_qit_coherence` vanishes because the computed off-diagonal/coherence measure vanishes; classical work may remain nonzero.

Grep check:

```bash
rg -n "classical|diagonal|decoher|W_qit_coherence|coherence|offdiag|same_pipeline|control" system_v6/sims/dual_stack_carnot_szilard_hopf_weyl_probe
```

Red flags:

```bash
rg -n "W_qit_coherence\\s*=\\s*0\\.0|classical.*skip|if .*classical|decohered.*return|same_pipeline\\s*=\\s*false" system_v6/sims/dual_stack_carnot_szilard_hopf_weyl_probe
```

jq check:

```bash
RESULT=system_v6/sims/dual_stack_carnot_szilard_hopf_weyl_probe/results/dual_stack_carnot_szilard_hopf_weyl_probe_envelope_results.json; jq -e '.controls.classical_decohered.same_pipeline==true and (((.controls.classical_decohered.W_qit_coherence|tonumber) as $x | if $x < 0 then -$x else $x end) < 1e-8) and (((.controls.classical_decohered.W_classical|tonumber) as $x | if $x < 0 then -$x else $x end) > 1e-8)' "$RESULT"
```

If this `jq` lacks `fabs`, use:

```bash
RESULT=system_v6/sims/dual_stack_carnot_szilard_hopf_weyl_probe/results/dual_stack_carnot_szilard_hopf_weyl_probe_envelope_results.json; python3 - <<'PY'
import json, pathlib
d=json.loads(pathlib.Path("system_v6/sims/dual_stack_carnot_szilard_hopf_weyl_probe/results/dual_stack_carnot_szilard_hopf_weyl_probe_envelope_results.json").read_text())
c=d["controls"]["classical_decohered"]
assert c["same_pipeline"] is True
assert abs(c["W_qit_coherence"]) < 1e-8
assert abs(c["W_classical"]) > 1e-8
print("CLASSICAL_CONTROL_SAME_PIPELINE")
PY
```

Python recomputation check:

```bash
python3 - <<'PY'
import json, numpy as np
from pathlib import Path
d=json.loads(Path("system_v6/sims/dual_stack_carnot_szilard_hopf_weyl_probe/results/dual_stack_carnot_szilard_hopf_weyl_probe_envelope_results.json").read_text())
tol=1e-8
c=d["controls"]["classical_decohered"]
rho=np.array(c["input_rho"], dtype=complex)
coh=float(np.sum(np.abs(rho-np.diag(np.diag(rho)))))
assert coh < tol
assert abs(c["computed_input_coherence"]-coh) < tol
assert abs(c["W_qit_coherence"]) < tol
print("CLASSICAL_COHERENCE_COMPUTED_ZERO")
PY
```

GENUINE positive condition: the classical control is a same-codepath control, not a special-case assertion. If QIT coherence is zero by assignment, the "without QIT structure" witness is fake.

## E. Order Witness Inflated By Trivial Noncommutation

Most probable subtle failure: the headline witness is just `U` vs damping noncommutation. That is easy and not the requested structure. The interesting claim is loop-level `D/I` divergence and Type1-vs-Type2 placement divergence.

Required objects:

- `Delta_loop = ||Phi_D(Phi_I(rho_L)) - Phi_I(Phi_D(rho_L))||_1 > tol`.
- Type1 final state differs from Type2 final state on the specified sheets.
- `ax6_order_gap` or stroke-pair gap may be reported only as a sub-readout.
- commuting control pair collapses at loop level.

Grep check:

```bash
rg -n "Phi_D|Phi_I|Type1|Type2|Delta|trace_norm|norm.*1|ax6_order_gap|commuting_control|stroke_pair|D\\(I|I\\(D" system_v6/sims/dual_stack_carnot_szilard_hopf_weyl_probe
```

Red flags:

```bash
rg -n "headline.*U.*E|Delta\\s*=\\s*.*U.*E|order_witness\\s*=\\s*.*commutator|\\[U,E\\]|U_E_gap|stroke_pair_gap.*headline" system_v6/sims/dual_stack_carnot_szilard_hopf_weyl_probe
```

jq check:

```bash
RESULT=system_v6/sims/dual_stack_carnot_szilard_hopf_weyl_probe/results/dual_stack_carnot_szilard_hopf_weyl_probe_envelope_results.json; jq -e '(.readouts.headline_order_witness.kind=="loop_level_D_I") and (.readouts.headline_order_witness.Delta > 1e-8) and (.readouts.type1_type2_trace_distance > 1e-8) and (.controls.commuting_pair.Delta_loop < 1e-8) and (.readouts.stroke_pair_gap != .readouts.headline_order_witness.Delta)' "$RESULT"
```

Python recomputation check:

```bash
python3 - <<'PY'
import json, numpy as np
from pathlib import Path
d=json.loads(Path("system_v6/sims/dual_stack_carnot_szilard_hopf_weyl_probe/results/dual_stack_carnot_szilard_hopf_weyl_probe_envelope_results.json").read_text())
tol=1e-8
def A(name): return np.array(d["states"][name], dtype=complex)
def trnorm(x): return float(np.sum(np.linalg.svd(x, compute_uv=False)))
delta=trnorm(A("D_after_I_rho_L")-A("I_after_D_rho_L"))
placement=trnorm(A("type1_final")-A("type2_final"))
comm=trnorm(A("commuting_D_after_I")-A("commuting_I_after_D"))
assert abs(delta-d["readouts"]["headline_order_witness"]["Delta"]) < tol
assert delta > tol
assert placement > tol
assert comm < tol
print("LOOP_LEVEL_ORDER_WITNESS_NOT_STROKE_ONLY")
PY
```

GENUINE positive condition: headline is loop-level and placement-level. Honest-divergence condition: if `U/E` noncommute but `D/I` loop gap or Type1-vs-Type2 placement gap vanishes, the result is a useful negative/control result, not engine-structure evidence.

## F. Memory Reset Partial-Trace Leak

Most probable subtle failure: `I_c(S>M)` is computed on the correct post-measurement joint state but reported under a post-reset stage, or computed after reset while claiming measurement-created cut.

Required stage labels:

- `after_M_joint`: natural `rho_AB` for Axis-0 cut.
- `before_R_joint` or `after_F_joint`: reset input for Landauer.
- `after_R_joint`: reset output, expected to reduce/remove memory excitation and often reduce the cut.

Grep check:

```bash
rg -n "I_c|coherent_information|conditional_entropy|after_M|before_R|after_R|partial_trace|ptrace|rho_AB|Axis-0|axis0|Phi0" system_v6/sims/dual_stack_carnot_szilard_hopf_weyl_probe
```

Red flags:

```bash
rg -n "I_c.*after_R|Phi0.*after_R|rho_AB.*after_R|axis0.*reset|coherent_information.*reset" system_v6/sims/dual_stack_carnot_szilard_hopf_weyl_probe
```

jq check:

```bash
RESULT=system_v6/sims/dual_stack_carnot_szilard_hopf_weyl_probe/results/dual_stack_carnot_szilard_hopf_weyl_probe_envelope_results.json; jq -e '.axis0_cut.by_stage.after_M.I_c_S_to_M != null and .axis0_cut.by_stage.after_R.I_c_S_to_M != null and .axis0_cut.reported_phi0_stage=="after_M"' "$RESULT"
```

Python recomputation check:

```bash
python3 - <<'PY'
import json, math, numpy as np
from pathlib import Path
d=json.loads(Path("system_v6/sims/dual_stack_carnot_szilard_hopf_weyl_probe/results/dual_stack_carnot_szilard_hopf_weyl_probe_envelope_results.json").read_text())
tol=1e-8
def vn(r):
    w=np.linalg.eigvalsh((r+r.conj().T)/2)
    return float(-sum(v*math.log(v) for v in w if v>1e-14))
def ptrace_memory(r):
    x=r.reshape(2,2,2,2)
    return np.einsum("smsn->mn", x)
def Ic(r):
    return vn(ptrace_memory(r))-vn(r)  # -S(S|M)
for stage in ["after_M","after_R"]:
    rho=np.array(d["states"][f"{stage}_joint"], dtype=complex)
    got=d["axis0_cut"]["by_stage"][stage]["I_c_S_to_M"]
    assert abs(Ic(rho)-got) < tol, (stage, Ic(rho), got)
assert d["axis0_cut"]["reported_phi0_stage"]=="after_M"
print("AXIS0_STAGE_LABELS_HONEST")
PY
```

GENUINE positive condition: the natural cut is reported at `after_M`, reset effects are separately reported, and both values recompute from their labeled joint density matrices. If stage labels are blurred, the Axis-0 readout is not trustworthy.

## G. SMT Binding Actual 4x4 Objects

Most probable subtle failure: z3/cvc5 bind 2x2 toy matrices, precomputed booleans, or precomputed scalar gaps and relabel them as `system tensor memory`.

Required SMT:

- For full `D/I` claim: solver variables bind actual 4x4 joint density/channel entries or explicit honest reduced objects with a written reason.
- Solver derives entries of `D(I(rho)) - I(D(rho))` in-solver from bound matrices.
- Equality assertion for noncommuting pair is `UNSAT`; commuting control equality is `SAT`.
- No free Boolean `P and not P`, no asserted `delta != 0` from a precomputed scalar.

Grep check:

```bash
rg -n "z3|cvc5|Solver|Real\\(|RealVal|mkReal|mkConst|4x4|16|rho_.*_.*|matrix_entries|bound.*entries|derived.*solver|precomputed|delta|commuting.*SAT|UNSAT" system_v6/sims/dual_stack_carnot_szilard_hopf_weyl_probe
```

Red flags:

```bash
rg -n "Bool\\(|P_and_not_P|precomputed.*delta|assert.*delta|RealVal\\(.*Delta|mkReal\\(.*Delta|2x2.*SMT|toy|scalar_gap|solver\\.add\\(.*!=\\s*0\\)" system_v6/sims/dual_stack_carnot_szilard_hopf_weyl_probe
```

jq check:

```bash
RESULT=system_v6/sims/dual_stack_carnot_szilard_hopf_weyl_probe/results/dual_stack_carnot_szilard_hopf_weyl_probe_envelope_results.json; jq -e '.smt.z3.binds_object_dim==4 and .smt.cvc5.binds_object_dim==4 and .smt.z3.derived_entries_in_solver==true and .smt.cvc5.derived_entries_in_solver==true and .smt.z3.equality_verdict=="unsat" and .smt.cvc5.equality_verdict=="unsat" and .smt.z3.commuting_control_equality_verdict=="sat" and .smt.cvc5.commuting_control_equality_verdict=="sat" and (.smt.z3.asserted_precomputed_scalar_literal==false) and (.smt.cvc5.asserted_precomputed_scalar_literal==false)' "$RESULT"
```

Python source anti-fakery scan:

```bash
python3 - <<'PY'
from pathlib import Path
import re
root=Path("system_v6/sims/dual_stack_carnot_szilard_hopf_weyl_probe")
src="\n".join(p.read_text(errors="ignore") for p in root.glob("*_jax.py"))
bad=[
    r"Bool\(",
    r"P_and_not_P",
    r"precomputed.*delta",
    r"RealVal\([^)]*Delta",
    r"mkReal\([^)]*Delta",
    r"solver\.add\([^)]*delta[^)]*!=\s*0",
]
for pat in bad:
    assert not re.search(pat, src, re.I|re.S), pat
assert re.search(r"for .* in range\(4\)", src) or re.search(r"binds_object_dim.?[:=].?4", src)
assert re.search(r"derived_entries_in_solver|derived_products|matrix_entries", src, re.I)
print("SMT_SOURCE_NOT_OBVIOUSLY_DECORATIVE")
PY
```

GENUINE positive condition: both solvers derive the equality failure from bound matrix/channel entries over the correct 4x4 object, with a commuting control SAT flip. If the solver only re-checks a scalar gap computed outside the solver, the SMT layer is decorative even if numerics are correct.

## Required Numbers For GENUINE

Use `tol = 1e-8` unless the runner records a stricter tolerance.

Positive dual-stack witness requires all of these:

- Artifact/ceiling: `schema_version=three_engine_sim_result_v1`, `engine_contract.mode=all_three_full_sims`, Julia/JAX/PyTorch all `ran=true`, `reads_peer_result=false`, `classification=scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`, validator `--require-pytorch` exits 0.
- CPTP legality: every stroke/channel including `U`, `E`, `D`, `M`, `F`, `R`, Type1, Type2 has `tp_defect < tol` and `choi_min_eig > -tol`; `F` may use unitary defect `< tol`.
- Measurement honesty: `M.input_dim=M.output_dim=4`, Choi shape `16x16` or Kraus list of 4x4 matrices; `I_gained_after_M > tol` and recomputes from `rho_SM_after_M`.
- Landauer ledger: reported `information_gained`, `p_excited_before_reset`, `landauer_reset_cost`, `work_extracted`, and `bound_margin` recompute from recorded states; `landauer_reset_cost + tol >= ln(2)*p_excited_before_reset`; `work_extracted - ln(2)*information_gained <= tol`.
- Feedback: `after_F_joint == F(after_M_joint)` within `tol` for one joint memory-conditioned operator/channel; no hidden branch variable controls the density update.
- Order: headline `Delta_loop = ||D(I(rho_L))-I(D(rho_L))||_1 > tol`; `type1_type2_trace_distance > tol`; commuting loop control `< tol`; stroke-level `U/E` gap is separate and not the headline.
- Classical control: `same_pipeline=true`; computed input/output coherence readouts are present; `abs(W_qit_coherence) < tol`; `abs(W_classical) > tol` if the classical Szilard ledger is meant to persist.
- Reset staging: `I_c(S>M)` recomputes at `after_M` and `after_R`; reported `Phi0`/natural Axis-0 cut stage is `after_M`, not silently post-reset.
- SMT: z3 and cvc5 both bind actual 4x4 joint objects or explicitly justified reduced objects; noncommuting equality verdicts are `unsat`; commuting control equality verdicts are `sat`; no precomputed scalar/boolean literal gates the proof.
- Controls: sign/chirality control reports mirror/gamma5-odd flip; label shuffle reports ledger equality within `tol` while map-derived structure remains tied to actual maps, not labels.

Honest-divergence outcomes that are still useful but not a positive GENUINE witness:

- Landauer bound violation with `all_pass=false`: honest broken encoding, useful failure.
- `U/E` stroke noncommutation nonzero but `D/I` loop gap zero: trivial stroke result only, no dual-stack engine structure.
- Type1-vs-Type2 final states equal while loop gap nonzero: order exists, placement claim failed.
- Classical control has nonzero `W_qit_coherence`: decohered-carrier control failed or coherence computation is wrong.
- Measurement/feedback implemented by branch bookkeeping: useful classical branch sim, not a QIT density-formalism Szilard loop.
- SMT decorative while numeric gap is real: numeric diagnostic only, proof layer not load-bearing.
