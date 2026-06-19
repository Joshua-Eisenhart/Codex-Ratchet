# Nested Hopf/Weyl Signed-Cut Ratchet Pre-Audit

Repo: `/Users/joshuaeisenhart/Codex-Ratchet`  
Object under audit: `foundation_nested_hopf_weyl_signed_cut_ratchet`  
Scope: adversarial post-build checks for the parallel builder output. These checks are read-only and assume the builder created the four requested source files plus result JSONs.

## Result Discovery

Use this first so the later checks agree on the concrete files:

```bash
cd /Users/joshuaeisenhart/Codex-Ratchet
find system_v5 -type f \( -name 'foundation_nested_hopf_weyl_signed_cut_ratchet*' -o -name '*nested_hopf_weyl_signed_cut_ratchet*' \) | sort
```

Expected source files:

- `system_v5/julia_carrier/foundation_nested_hopf_weyl_signed_cut_ratchet_julia.jl`
- `system_v5/ops/formal_scouts/foundation_nested_hopf_weyl_signed_cut_ratchet_jax.py`
- `system_v5/ops/formal_scouts/foundation_nested_hopf_weyl_signed_cut_ratchet_pytorch.py`
- `system_v5/ops/formal_scouts/foundation_nested_hopf_weyl_signed_cut_ratchet_envelope.py`

Expected result files should include `julia`, `jax`, `pytorch`, and `envelope` result JSONs for the same object id.

## 1. Pin-Spec Drift Across Legs

Most likely subtle failure: the three legs each compute a plausible `rho_r` from slightly different rung parameters, coupling constants, cut convention, log base, or state formula, then the envelope reports agreement anyway.

The result must expose an identical literal pin spec from all three engine results and the envelope must compare the specs before `all_pass`.

```bash
cd /Users/joshuaeisenhart/Codex-Ratchet
python3 - <<'PY'
import json, pathlib, sys
root = pathlib.Path.cwd()
paths = sorted(root.glob("system_v5/**/*nested_hopf_weyl_signed_cut_ratchet*results.json"))
paths += sorted(root.glob("system_v5/**/*nested_hopf_weyl_signed_cut_ratchet*_results.json"))
paths = sorted(set(paths))
legs = {k: [p for p in paths if k in p.name.lower()] for k in ("julia", "jax", "pytorch", "envelope")}
missing = [k for k, v in legs.items() if not v]
if missing:
    raise SystemExit(f"FAIL missing result legs: {missing}; found={[str(p) for p in paths]}")

def load(p): return json.loads(p.read_text())
def find_key(obj, names):
    if isinstance(obj, dict):
        for n in names:
            if n in obj:
                return obj[n]
        for v in obj.values():
            got = find_key(v, names)
            if got is not None:
                return got
    elif isinstance(obj, list):
        for v in obj:
            got = find_key(v, names)
            if got is not None:
                return got
    return None

specs = {}
for leg in ("julia", "jax", "pytorch"):
    payload = load(legs[leg][0])
    if payload.get("reads_peer_result") is not False:
        raise SystemExit(f"FAIL {leg} reads_peer_result is not false: {payload.get('reads_peer_result')}")
    spec = find_key(payload, {"PIN_SPEC", "pin_spec", "pinned_spec", "rho_spec"})
    if not isinstance(spec, dict):
        raise SystemExit(f"FAIL {leg} missing object pin spec")
    specs[leg] = spec

canon = json.dumps(specs["julia"], sort_keys=True, separators=(",", ":"))
for leg, spec in specs.items():
    s = json.dumps(spec, sort_keys=True, separators=(",", ":"))
    if s != canon:
        raise SystemExit(f"FAIL pin spec mismatch: {leg} != julia\n{specs['julia']}\n{spec}")

required_terms = ["eta", "rung", "coupling", "rho", "Weyl", "L", "R", "natural"]
flat = json.dumps(specs["julia"], sort_keys=True)
missing_terms = [t for t in required_terms if t.lower() not in flat.lower()]
if missing_terms:
    raise SystemExit(f"FAIL pin spec too weak, missing terms: {missing_terms}")
print("PASS pin specs identical, peer reads disabled, required pin terms present")
PY
```

Source-side check that each leg has a literal pin block rather than only envelope prose:

```bash
cd /Users/joshuaeisenhart/Codex-Ratchet
rg -n "PIN_SPEC|pin_spec|pinned_spec|rho_spec|eta_1|eta_2|eta_3|natural_log|Weyl.*L|Weyl.*R" \
  system_v5/julia_carrier/foundation_nested_hopf_weyl_signed_cut_ratchet_julia.jl \
  system_v5/ops/formal_scouts/foundation_nested_hopf_weyl_signed_cut_ratchet_jax.py \
  system_v5/ops/formal_scouts/foundation_nested_hopf_weyl_signed_cut_ratchet_pytorch.py
```

Fail if any leg lacks a top-level literal spec, or if the envelope only compares an opaque hash without surfacing the fields.

## 2. Incommensurable `max_divergence`

Most likely subtle failure: `max_divergence=0.0` is computed across engine values that are not the same observable, for example Julia reports `S(A|B)`, JAX reports `order_gap`, and PyTorch reports a gradient.

The envelope must compare like-for-like named scalar arrays. The key sets for each engine must match for the claim-bearing observables.

```bash
cd /Users/joshuaeisenhart/Codex-Ratchet
python3 - <<'PY'
import json, pathlib
root = pathlib.Path.cwd()
envs = sorted(root.glob("system_v5/**/*nested_hopf_weyl_signed_cut_ratchet*envelope*results.json"))
if not envs:
    raise SystemExit("FAIL no envelope result found")
env = json.loads(envs[-1].read_text())
div = env.get("divergence", {})
vals = div.get("engine_values")
if not isinstance(vals, dict):
    raise SystemExit("FAIL divergence.engine_values missing or not object")
for leg in ("julia", "jax", "pytorch"):
    if leg not in vals:
        raise SystemExit(f"FAIL divergence missing {leg}")
    if not isinstance(vals[leg], dict):
        raise SystemExit(f"FAIL {leg} engine_values is not a named observable object")

required = {
    "conditional_entropy_A_given_B_by_rung",
    "signed_cut_S_A_given_B_by_rung",
    "order_gap_by_adjacent_pair",
    "separable_conditional_entropy_A_given_B_by_rung",
    "commuting_order_gap_by_adjacent_pair",
}
keysets = {leg: set(vals[leg]) for leg in ("julia", "jax", "pytorch")}
if len(set(map(tuple, (sorted(v) for v in keysets.values())))) != 1:
    raise SystemExit(f"FAIL incommensurable engine value keys: {keysets}")
missing = required - keysets["julia"]
if missing:
    raise SystemExit(f"FAIL missing named observables from divergence comparison: {sorted(missing)}")
if div.get("max_divergence") == 0 and not div.get("observablewise_max_divergence"):
    raise SystemExit("FAIL aggregate max_divergence=0 without observablewise_max_divergence table")
print("PASS divergence compares matching named observables")
PY
```

Fail if the envelope has only one scalar per engine, or if keys differ and the code still reports `all_pass`.

## 3. Wrong Marginal Or Wrong Sign For `S(A|B)`

Most likely subtle failure: `S(A|B)` is accidentally computed as `S_AB - S_A`, `S_B - S_AB`, `S_A - S_AB`, or with the Weyl-L/R cut swapped without saying so.

The claim uses `A = Weyl-L`, `B = Weyl-R`, natural logs, and:

```text
S(A|B) = S(rho_AB) - S(rho_B)
I_c(A->B) = -S(A|B) = S(rho_B) - S(rho_AB)
```

```bash
cd /Users/joshuaeisenhart/Codex-Ratchet
python3 - <<'PY'
import json, math, pathlib
root = pathlib.Path.cwd()
paths = sorted(root.glob("system_v5/**/*nested_hopf_weyl_signed_cut_ratchet*results.json"))
if not paths:
    raise SystemExit("FAIL no result JSONs found")

def walk(obj):
    if isinstance(obj, dict):
        yield obj
        for v in obj.values():
            yield from walk(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from walk(v)

rows = []
for p in paths:
    payload = json.loads(p.read_text())
    for d in walk(payload):
        keys = set(d)
        if {"S_AB", "S_B"} <= keys and ("S_A_given_B" in keys or "conditional_entropy_A_given_B" in keys):
            val = d.get("S_A_given_B", d.get("conditional_entropy_A_given_B"))
            rows.append((p, d, float(d["S_AB"]), float(d["S_B"]), float(val)))
if not rows:
    raise SystemExit("FAIL no rows expose S_AB, S_B, and S(A|B)")
for p, d, s_ab, s_b, got in rows:
    if not math.isfinite(got):
        raise SystemExit(f"FAIL non-finite conditional entropy in {p}: {d}")
    if abs((s_ab - s_b) - got) > 1e-8:
        raise SystemExit(f"FAIL wrong S(A|B) formula in {p}: got {got}, expected S_AB-S_B={s_ab-s_b}, row={d}")
print(f"PASS {len(rows)} exposed conditional entropy rows recompute as S_AB-S_B")
PY
```

Source grep to catch the common wrong marginal:

```bash
cd /Users/joshuaeisenhart/Codex-Ratchet
rg -n "S_AB.*-.*S_A|S_A.*-.*S_AB|conditional.*S_A|coherent.*=|partial_trace|rho_B|Weyl.*R|Weyl.*L" \
  system_v5/julia_carrier/foundation_nested_hopf_weyl_signed_cut_ratchet_julia.jl \
  system_v5/ops/formal_scouts/foundation_nested_hopf_weyl_signed_cut_ratchet_jax.py \
  system_v5/ops/formal_scouts/foundation_nested_hopf_weyl_signed_cut_ratchet_pytorch.py
```

Fail if `rho_B` is not explicitly the Weyl-R marginal, or if the source only stores coherent information and reconstructs `S(A|B)` by sign convention later.

## 4. Entropy Readout Is Plumbing, Not Carrier-Dependent

Most likely subtle failure: the entropy values are independent of the actual `psi` or `rho_r`; entangled and separable inputs produce the same readout, so the code measures the trace/shape/plumbing rather than the Weyl L/R carrier.

The carrier lane must differ from the separable control, and only the carrier lane may cross negative.

```bash
cd /Users/joshuaeisenhart/Codex-Ratchet
python3 - <<'PY'
import json, pathlib, math
root = pathlib.Path.cwd()
envs = sorted(root.glob("system_v5/**/*nested_hopf_weyl_signed_cut_ratchet*envelope*results.json"))
if not envs:
    raise SystemExit("FAIL no envelope result found")
env = json.loads(envs[-1].read_text())

def find(obj, names):
    if isinstance(obj, dict):
        for n in names:
            if n in obj:
                return obj[n]
        for v in obj.values():
            got = find(v, names)
            if got is not None:
                return got
    elif isinstance(obj, list):
        for v in obj:
            got = find(v, names)
            if got is not None:
                return got
    return None

carrier = find(env, {"conditional_entropy_A_given_B_by_rung", "carrier_conditional_entropy_by_rung", "S_A_given_B_by_rung"})
sep = find(env, {"separable_conditional_entropy_A_given_B_by_rung", "separable_S_A_given_B_by_rung"})
if not isinstance(carrier, list) or not isinstance(sep, list):
    raise SystemExit("FAIL missing carrier and separable per-rung S(A|B) arrays")
carrier = [float(x) for x in carrier]
sep = [float(x) for x in sep]
if len(carrier) < 2 or len(carrier) != len(sep):
    raise SystemExit(f"FAIL bad rung lengths: carrier={carrier}, separable={sep}")
if max(abs(a-b) for a, b in zip(carrier, sep)) <= 1e-8:
    raise SystemExit(f"FAIL psi-independent entropy readout: carrier == separable {carrier}")
if not any(x < -1e-8 for x in carrier):
    raise SystemExit(f"FAIL carrier never crosses negative: {carrier}")
if any(x < -1e-8 for x in sep):
    raise SystemExit(f"FAIL separable control has negative S(A|B): {sep}")
if len(set(round(x, 12) for x in carrier)) == 1:
    raise SystemExit(f"FAIL carrier S(A|B) flat across rungs: {carrier}")

grad = find(env, {"dS_dcoupling_at_crossing", "dS_A_given_B_dcoupling_at_crossing", "pytorch_jacrev_dS_dcoupling"})
if grad is None or not math.isfinite(float(grad)) or abs(float(grad)) <= 1e-10:
    raise SystemExit(f"FAIL missing/nonzero PyTorch coupling gradient at crossing: {grad}")
print("PASS entropy depends on carrier, separable control does not cross, PyTorch gradient nonzero")
PY
```

Fail if the only evidence is `trace == 1`, `PSD`, or a fixed spectrum reused across all rungs.

## 5. Probe Families Declared But Not Used

Most likely subtle failure: `M_1 ⊂ M_2 ⊂ M_3` is described in the receipt but no computed quantity depends on those operator lists, so the quotient/readout is not a probe-family result.

The result must expose each probe operator list, strict inclusion by rung, and a non-flat quotient/class readout. The source must compute quotient/classes from `M_r`, not from `rung_id` alone.

```bash
cd /Users/joshuaeisenhart/Codex-Ratchet
python3 - <<'PY'
import json, pathlib
root = pathlib.Path.cwd()
envs = sorted(root.glob("system_v5/**/*nested_hopf_weyl_signed_cut_ratchet*envelope*results.json"))
if not envs:
    raise SystemExit("FAIL no envelope result found")
env = json.loads(envs[-1].read_text())

def find(obj, names):
    if isinstance(obj, dict):
        for n in names:
            if n in obj:
                return obj[n]
        for v in obj.values():
            got = find(v, names)
            if got is not None:
                return got
    elif isinstance(obj, list):
        for v in obj:
            got = find(v, names)
            if got is not None:
                return got
    return None

families = find(env, {"probe_families_by_rung", "M_by_rung", "probe_operator_lists"})
quot = find(env, {"quotient_dimension_by_rung", "distinguishable_classes_by_rung", "density_quotient_by_rung"})
if not isinstance(families, list) or len(families) < 2:
    raise SystemExit("FAIL missing per-rung probe families")
sets = [set(map(str, f)) for f in families]
for i in range(len(sets)-1):
    if not sets[i] < sets[i+1]:
        raise SystemExit(f"FAIL probe family not strict nested at {i}->{i+1}: {families}")
if not isinstance(quot, list) or len(quot) != len(families):
    raise SystemExit(f"FAIL missing quotient/classes per rung: {quot}")
q = [float(x["value"] if isinstance(x, dict) and "value" in x else x) for x in quot]
if len(set(q)) == 1:
    raise SystemExit(f"FAIL quotient/classes flat despite strict M nesting: {q}")

direction = find(env, {"quotient_monotone_direction", "probe_metric_direction"})
if direction not in {"nondecreasing", "nonincreasing"}:
    raise SystemExit(f"FAIL missing declared monotone direction for quotient metric: {direction}")
if direction == "nondecreasing" and any(q[i+1] < q[i] for i in range(len(q)-1)):
    raise SystemExit(f"FAIL quotient not nondecreasing: {q}")
if direction == "nonincreasing" and any(q[i+1] > q[i] for i in range(len(q)-1)):
    raise SystemExit(f"FAIL quotient not nonincreasing: {q}")
print("PASS probe families are strict nested and quotient/classes are non-flat monotone")
PY
```

Source grep for fake quotient wiring:

```bash
cd /Users/joshuaeisenhart/Codex-Ratchet
rg -n "M_r|probe_family|probe_famil|quotient|distinguishable|classes|operator list|expect|trace" \
  system_v5/julia_carrier/foundation_nested_hopf_weyl_signed_cut_ratchet_julia.jl \
  system_v5/ops/formal_scouts/foundation_nested_hopf_weyl_signed_cut_ratchet_jax.py \
  system_v5/ops/formal_scouts/foundation_nested_hopf_weyl_signed_cut_ratchet_pytorch.py
```

Fail if the quotient is a hard-coded function of rung index or probe-list length only.

## 6. Order Gap On Bare Unitaries Instead Of Full Stacking Channels

Most likely subtle failure: the build computes `||Phi_r Phi_{r+1} - Phi_{r+1} Phi_r||` as a matrix/unitary commutator, not the requested full channel action on the pinned `rho`, or the commuting control uses a different state family and becomes vacuous.

The ratchet gap must be:

```text
|| (Phi_r o Phi_{r+1})(rho_r or pinned adjacent probe rho) - (Phi_{r+1} o Phi_r)(same rho) ||_1
```

and the commuting control must use the same pin spec/state family.

```bash
cd /Users/joshuaeisenhart/Codex-Ratchet
python3 - <<'PY'
import json, pathlib
root = pathlib.Path.cwd()
envs = sorted(root.glob("system_v5/**/*nested_hopf_weyl_signed_cut_ratchet*envelope*results.json"))
if not envs:
    raise SystemExit("FAIL no envelope result found")
env = json.loads(envs[-1].read_text())

def find(obj, names):
    if isinstance(obj, dict):
        for n in names:
            if n in obj:
                return obj[n]
        for v in obj.values():
            got = find(v, names)
            if got is not None:
                return got
    elif isinstance(obj, list):
        for v in obj:
            got = find(v, names)
            if got is not None:
                return got
    return None

gaps = find(env, {"order_gap_by_adjacent_pair", "ratchet_order_gap_by_pair", "order_gaps"})
ctrl = find(env, {"commuting_order_gap_by_adjacent_pair", "commuting_control_order_gaps"})
if not isinstance(gaps, list) or not gaps:
    raise SystemExit("FAIL missing ratchet order gaps")
if not isinstance(ctrl, list) or len(ctrl) != len(gaps):
    raise SystemExit(f"FAIL missing commuting control gaps: gaps={gaps}, ctrl={ctrl}")
g = [float(x["value"] if isinstance(x, dict) and "value" in x else x) for x in gaps]
c = [float(x["value"] if isinstance(x, dict) and "value" in x else x) for x in ctrl]
if any(x <= 1e-8 for x in g):
    raise SystemExit(f"FAIL nonzero ratchet order gap not shown: {g}")
if any(abs(x) > 1e-8 for x in c):
    raise SystemExit(f"FAIL commuting control order gap not zero: {c}")
same = find(env, {"commuting_control_same_pin_spec", "control_same_state_family", "commuting_control_same_rho_family"})
if same is not True:
    raise SystemExit(f"FAIL commuting control does not assert same pin/state family: {same}")
boundary = find(env, {"boundary_rung_count_1", "rung_count_1_boundary"})
if not isinstance(boundary, dict) or boundary.get("signed_cut_crossing") not in {False, "false"}:
    raise SystemExit(f"FAIL rung-count-1 boundary does not block crossing: {boundary}")
print("PASS order gap and commuting/boundary controls have the required flip")
PY
```

Source grep for the unitary-only anti-pattern:

```bash
cd /Users/joshuaeisenhart/Codex-Ratchet
rg -n "commutator|Phi|order_gap|trace_norm|norm|rho|channel|compose|stack" \
  system_v5/julia_carrier/foundation_nested_hopf_weyl_signed_cut_ratchet_julia.jl \
  system_v5/ops/formal_scouts/foundation_nested_hopf_weyl_signed_cut_ratchet_jax.py \
  system_v5/ops/formal_scouts/foundation_nested_hopf_weyl_signed_cut_ratchet_pytorch.py
```

Fail if the source computes only `norm(A @ B - B @ A)` with no same-`rho` channel application in the gap path.

## 7. Decorative SMT

Most likely subtle failure: z3/cvc5 bind a precomputed scalar or Python boolean, so the solver proves the report's arithmetic plumbing rather than deriving noncommutation from the bound rung-2 matrices.

The solver must bind the rung-2 stacking matrices entry-wise and derive:

- main: `UNSAT` that the bound matrices commute;
- commuting control: `SAT` for the commuting control family.

```bash
cd /Users/joshuaeisenhart/Codex-Ratchet
python3 - <<'PY'
import json, pathlib
root = pathlib.Path.cwd()
jax_results = sorted(root.glob("system_v5/**/*nested_hopf_weyl_signed_cut_ratchet*jax*results.json"))
if not jax_results:
    raise SystemExit("FAIL no JAX result found")
jax = json.loads(jax_results[-1].read_text())

def find(obj, names):
    if isinstance(obj, dict):
        for n in names:
            if n in obj:
                return obj[n]
        for v in obj.values():
            got = find(v, names)
            if got is not None:
                return got
    elif isinstance(obj, list):
        for v in obj:
            got = find(v, names)
            if got is not None:
                return got
    return None

smt = find(jax, {"smt", "crossover_proofs", "solver_proofs"})
if not isinstance(smt, dict):
    raise SystemExit("FAIL missing SMT proof block")
for solver in ("z3", "cvc5"):
    rec = smt.get(solver)
    if not isinstance(rec, dict):
        raise SystemExit(f"FAIL missing {solver} record")
    main = rec.get("main_status", rec.get("verdict"))
    ctrl = rec.get("commuting_control_status", rec.get("control_verdict", rec.get("negative_control_verdict")))
    bound = rec.get("bound_entries_count", rec.get("matrix_entries_bound"))
    if str(main).lower() != "unsat":
        raise SystemExit(f"FAIL {solver} main must be UNSAT for commutation denial, got {main}")
    if str(ctrl).lower() != "sat":
        raise SystemExit(f"FAIL {solver} commuting control must be SAT, got {ctrl}")
    if not isinstance(bound, int) or bound < 16:
        raise SystemExit(f"FAIL {solver} does not expose enough entry-wise bound matrix entries: {bound}")
    text = json.dumps(rec).lower()
    bad = ["precomputed", "boolval", "order_gap_scalar", "python_bool"]
    if any(b in text for b in bad):
        raise SystemExit(f"FAIL {solver} proof smells scalar/decorative: {rec}")
print("PASS SMT records expose entry-wise derived noncommutation and control flip")
PY
```

Source grep for decorative SMT anti-patterns:

```bash
cd /Users/joshuaeisenhart/Codex-Ratchet
rg -n "BoolVal|boolval|precomputed|order_gap_scalar|python_bool|RealVal\\(|solver\\.add|assertFormula|mkReal|mkConst|bound_entries|matrix_entries" \
  system_v5/ops/formal_scouts/foundation_nested_hopf_weyl_signed_cut_ratchet_jax.py \
  system_v5/julia_carrier/foundation_nested_hopf_weyl_signed_cut_ratchet_julia.jl
```

Fail if the solver path never binds matrix entries or if it binds only a scalar gap.

## 8. Load-Bearing Labels Without Capability Probes

Most likely subtle failure: rich tools are marked `load_bearing` because they were imported, but the repo's capability-probe gate does not support that label.

Run the repo gate over each created sim source:

```bash
cd /Users/joshuaeisenhart/Codex-Ratchet
python3 scripts/verify_load_bearing_has_capability_probe.py --sim system_v5/ops/formal_scouts/foundation_nested_hopf_weyl_signed_cut_ratchet_jax.py
python3 scripts/verify_load_bearing_has_capability_probe.py --sim system_v5/ops/formal_scouts/foundation_nested_hopf_weyl_signed_cut_ratchet_pytorch.py
python3 scripts/verify_load_bearing_has_capability_probe.py --sim system_v5/ops/formal_scouts/foundation_nested_hopf_weyl_signed_cut_ratchet_envelope.py
```

Then inspect the declared depths:

```bash
cd /Users/joshuaeisenhart/Codex-Ratchet
jq '.TOOL_INTEGRATION_DEPTH // .tool_integration_depth // empty' \
  $(find system_v5 -type f -name '*nested_hopf_weyl_signed_cut_ratchet*results.json' | sort)
```

Fail if `numpy`, `scipy`, or `mpmath` appears in `claim_path_tools`; fail if a claimed `load_bearing` package does not pass the capability-probe gate. Julia `QuantumOptics`, JAX `z3/cvc5`, and PyTorch `torch.func` may be load-bearing only if the source/result records the actual function-level call and gate it controls.

## 9. Contract And Source-Backed Envelope Gate

The normal validator is necessary but not sufficient. Run it anyway, with source-backed audit if available:

```bash
cd /Users/joshuaeisenhart/Codex-Ratchet
PY=/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3
ENV=$(find system_v5 -type f -name '*nested_hopf_weyl_signed_cut_ratchet*envelope*results.json' | sort | tail -1)
$PY scripts/validate_three_engine_sim_result.py --require-pytorch "$ENV"
$PY scripts/validate_three_engine_sim_result.py --require-pytorch --require-source-backed "$ENV"
```

Also compile the Python sources:

```bash
cd /Users/joshuaeisenhart/Codex-Ratchet
PY=/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3
$PY -m py_compile \
  system_v5/ops/formal_scouts/foundation_nested_hopf_weyl_signed_cut_ratchet_jax.py \
  system_v5/ops/formal_scouts/foundation_nested_hopf_weyl_signed_cut_ratchet_pytorch.py \
  system_v5/ops/formal_scouts/foundation_nested_hopf_weyl_signed_cut_ratchet_envelope.py
```

Fail if the result is not `classification="scratch_diagnostic"`, `promotion_allowed=false`, and `formal_admission_allowed=false`.

## Per-Rung Numbers Required For Real Support

The headline claim is supported only if the per-rung table shows all of this, not just consistency with it:

1. Same object: all engines use the identical pin spec: `eta_1 > eta_2 > eta_3`, same stacking channel definition, same closed-form `rho_r`, same Weyl-L/Weyl-R cut, same coupling constant, same natural-log entropy.
2. Carrier signed cut: `S(A|B)_1 > S(A|B)_2 > S(A|B)_3` within stated tolerance, with at least one rung crossing below `0`. If the crossing is claimed at rung 2, rung 1 must be nonnegative and rung 2 or 3 must be negative.
3. Separable control: `S(A|B)_r >= 0` for every rung, under the same rungs and same cut. If it goes negative, the encoding is broken.
4. Carrier dependence: carrier and separable `S(A|B)` arrays must differ by more than numerical tolerance, and the PyTorch `dS(A|B)/d coupling` at the crossing rung must be finite and nonzero.
5. Probe nesting: `M_1 ⊂ M_2 ⊂ M_3` as actual operator-list inclusion. The quotient/class readout must be monotone in the declared direction and non-flat; the commuting control must lose that ratchet pattern or be explicitly marked `not_a_ratchet`.
6. Order sensitivity: every adjacent ratchet pair has positive full-channel trace-norm gap on the same pinned state family. The commuting control has gap `0` within tolerance.
7. Boundary rung count 1: no nesting, no adjacent order gap, and no signed-cut crossing.
8. Cross-engine agreement: Julia/JAX/PyTorch agree per named observable, per rung or pair. An aggregate `max_divergence` without an observable-wise table is not evidence.
9. SMT: JAX z3 and cvc5 derive noncommutation from bound rung-2 matrix entries, with `UNSAT` for forced commutation and `SAT` for the commuting control. Julia Z3 either runs the same shape or is explicitly `not_scoped` with a reason.

If any one of these fails, the honest ceiling is: source exists and may be a useful `scratch_diagnostic`, but the nested Hopf/Weyl signed-cut ratchet claim is not supported.
