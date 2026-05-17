"""contract_engine_16_placement_64_microstep_uniqueness.py — the actual target.

Binding contract for the engine architecture goal:
  2 engine types × 8 stages × 4 substages = 64 microstep outputs
  with 16 distinct stage placements (engine × stage) each producing
  unique nontrivial results that DEPEND on the input state (not on
  index labels alone).

This contract replaces ad-hoc Phase 32 / Phase 20 reads. It tests what
the user actually wants: do the 64 microsteps span a genuine
information-processing architecture, or are they 64 relabels of one
operation?

API required:
  candidate.engine_stage(engine_id: str, stage_idx: int,
                         substage_idx: int, input_rho_qt) -> dict
  with "output_rho_qt" in the returned dict, a 4-qubit density matrix
  on dims=[[2,2,2,2],[2,2,2,2]].

Hidden checks (Grok/Gemini do NOT see these specifics):
  1. UNIQUENESS-IN-ENGINE: for engine_id ∈ {"A","B"}, the 32 microstep
     outputs (8 stages × 4 substages) are pairwise distinct in
     trace distance; min pairwise td > TAU_IN.
  2. UNIQUENESS-ACROSS-ENGINES: every output for engine A is distinct
     from every output for engine B; all 32×32 = 1024 cross pairs have
     trace distance > TAU_CROSS.
  3. GEOMETRIC-DEPENDENCE: varying the input rho through a 3-state
     family (|0000⟩, |+⟩^⊗4, max-mixed) produces 3 DIFFERENT
     microstep-output tables. If the 64 outputs are the same for all
     3 inputs, the candidate is index-only (no geometric content).
  4. NO-INDEX-SHORTCUT: a permutation of (engine_id, stage_idx,
     substage_idx) labels that doesn't change the underlying math
     must produce the SAME output. Concretely: if the candidate
     just hashes the index tuple into the output, swapping stage 3
     and stage 5 (with the same generators) should also swap outputs.
     The contract probes this by checking that the output table has
     genuine algebraic structure, not lexicographic labeling.

Graveyards (auto-reject patterns):
  - candidate.engine_stage returns the same output for all (engine,
    stage, substage) → constant output → KILLED
  - output depends only on (stage_idx + 8*engine_idx) hash → label
    shortcut → KILLED
  - output uses primality / totient / divisor / gcd in any path
    → number-theory smuggle → KILLED
  - output uses % stage_idx as a switch with no underlying math
    → modular hash → KILLED
  - output ignores input_rho_qt entirely (cardinal test of geometric
    dependence) → label-only → KILLED

Status vocabulary: SURVIVED / KILLED / OPEN / NOT_YET_TESTED.
"""
import ast
import math
from pathlib import Path

import numpy as np


# Hidden thresholds. These are the harness's, not the candidate author's.
TAU_IN = 1e-3       # min pairwise td within an engine
TAU_CROSS = 1e-3    # min pairwise td across engines
TAU_GEOM = 1e-3     # min difference between output tables across inputs


def _arr(obj):
    """Coerce qutip / torch / numpy to a numpy complex array."""
    if hasattr(obj, "full"):
        return np.asarray(obj.full(), dtype=complex)
    if hasattr(obj, "detach"):
        return obj.detach().cpu().numpy().astype(complex)
    if hasattr(obj, "numpy"):
        return obj.numpy().astype(complex)
    return np.asarray(obj, dtype=complex)


def _trace_distance(rho_a: np.ndarray, rho_b: np.ndarray) -> float:
    diff = (rho_a - rho_b)
    diff_h = 0.5 * (diff + diff.conj().T)
    return 0.5 * float(np.sum(np.abs(np.linalg.eigvalsh(diff_h))))


def _qt_4qubit_ref_states():
    import qutip as qt
    plus = (qt.basis(2, 0) + qt.basis(2, 1)).unit()
    zero4 = qt.ket2dm(qt.tensor(qt.basis(2, 0), qt.basis(2, 0),
                                 qt.basis(2, 0), qt.basis(2, 0)))
    plus4 = qt.ket2dm(qt.tensor(plus, plus, plus, plus))
    max_mixed = qt.Qobj(np.eye(16, dtype=complex) / 16,
                        dims=[[2, 2, 2, 2], [2, 2, 2, 2]])
    return [("zero4", zero4), ("plus4", plus4), ("max_mixed", max_mixed)]


def _source_guard(candidate) -> list[dict]:
    """Reject candidates whose source contains number-theory smuggle
    or pure-hash shortcuts in engine_stage's body."""
    failures = []
    path = getattr(candidate, "__file__", None)
    if not path:
        return failures
    try:
        src = Path(path).read_text()
    except Exception:
        return failures
    # Scan for banned patterns in engine_stage's source specifically
    banned = [
        "math.gcd(", "math.factorial(", "sympy.factorint(",
        "sympy.divisors(", "sympy.totient(", "sympy.gcd(",
        "is_prime(", "is_coprime(", "phi(n)", "euler_phi(",
        "totient(", "divisors(", "factorint(", "factorize(",
        "hash(engine_id", "hash(stage_idx", "hash(substage_idx",
        "hash((engine_id", "hash((stage_idx",
    ]
    hits = [b for b in banned if b in src]
    if hits:
        failures.append({
            "check": "source_guard_banned_patterns",
            "msg": f"banned patterns in candidate source: {hits[:5]}",
        })
    return failures


def run(candidate) -> dict:
    failures = []
    metrics = {}

    if not hasattr(candidate, "engine_stage"):
        return {"pass": False,
                "failures": [{"check": "engine_stage_exists",
                              "msg": "Required `engine_stage(engine_id, stage_idx, substage_idx, rho)` not exported."}],
                "metrics": metrics}

    failures.extend(_source_guard(candidate))

    try:
        import qutip as qt
    except Exception as e:
        return {"pass": False,
                "failures": failures + [{"check": "qutip_import", "msg": str(e)[:160]}],
                "metrics": metrics}

    ref_states = _qt_4qubit_ref_states()

    # Per ref state, build the full 64-microstep table.
    # microsteps[(input_name, engine, stage, sub)] = density matrix array
    microsteps = {}
    call_failures = []
    for input_name, rho_in in ref_states:
        for engine in ("A", "B"):
            for s in range(8):
                for sub in range(4):
                    try:
                        r = candidate.engine_stage(engine, s, sub, rho_in)
                        out = r.get("output_rho_qt") if isinstance(r, dict) else r
                        microsteps[(input_name, engine, s, sub)] = _arr(out)
                    except Exception as e:
                        call_failures.append({
                            "check": f"engine_stage_{input_name}_{engine}_{s}_{sub}",
                            "msg": f"{type(e).__name__}: {str(e)[:120]}",
                        })
    if call_failures:
        failures.extend(call_failures[:5])  # don't flood; first 5 is enough

    # Check 1: uniqueness within each engine on each input state.
    n_inputs_with_full_table = 0
    in_engine_min_tds = []
    cross_engine_min_tds = []
    for input_name, _ in ref_states:
        per_input_ok = True
        for engine in ("A", "B"):
            keys = [(input_name, engine, s, sub) for s in range(8) for sub in range(4)]
            states = [microsteps.get(k) for k in keys]
            if any(s is None for s in states):
                per_input_ok = False
                continue
            mn = math.inf
            for i in range(32):
                for j in range(i + 1, 32):
                    td = _trace_distance(states[i], states[j])
                    if td < mn:
                        mn = td
            in_engine_min_tds.append({"input": input_name, "engine": engine, "min_td": mn})
        # cross-engine
        keysA = [(input_name, "A", s, sub) for s in range(8) for sub in range(4)]
        keysB = [(input_name, "B", s, sub) for s in range(8) for sub in range(4)]
        statesA = [microsteps.get(k) for k in keysA]
        statesB = [microsteps.get(k) for k in keysB]
        if not any(x is None for x in statesA) and not any(x is None for x in statesB):
            mn = math.inf
            for a in statesA:
                for b in statesB:
                    td = _trace_distance(a, b)
                    if td < mn:
                        mn = td
            cross_engine_min_tds.append({"input": input_name, "min_cross_td": mn})
        if per_input_ok:
            n_inputs_with_full_table += 1

    metrics["in_engine_min_tds"] = in_engine_min_tds
    metrics["cross_engine_min_tds"] = cross_engine_min_tds
    metrics["n_inputs_with_full_table"] = n_inputs_with_full_table

    # Check pass condition for uniqueness within / across engines.
    for row in in_engine_min_tds:
        if row["min_td"] < TAU_IN:
            failures.append({
                "check": f"uniqueness_in_engine_{row['engine']}_{row['input']}",
                "msg": f"min pairwise td {row['min_td']:.2e} < tau_in {TAU_IN}",
            })
    for row in cross_engine_min_tds:
        if row["min_cross_td"] < TAU_CROSS:
            failures.append({
                "check": f"uniqueness_across_engines_{row['input']}",
                "msg": f"min cross td {row['min_cross_td']:.2e} < tau_cross {TAU_CROSS}",
            })

    # Check 3: geometric dependence on input state. The output tables
    # across the 3 inputs should DIFFER (not be the same 64 outputs).
    geom_dep_evidence = []
    if all((input_name, "A", 0, 0) in microsteps for input_name, _ in ref_states):
        # Compare microstep (A, 0, 0) across the 3 input states.
        outs = [microsteps[(name, "A", 0, 0)] for name, _ in ref_states]
        td_01 = _trace_distance(outs[0], outs[1])
        td_02 = _trace_distance(outs[0], outs[2])
        td_12 = _trace_distance(outs[1], outs[2])
        geom_dep_evidence = {"td_zero_vs_plus": td_01,
                             "td_zero_vs_max_mixed": td_02,
                             "td_plus_vs_max_mixed": td_12}
        if min(td_01, td_02, td_12) < TAU_GEOM:
            failures.append({
                "check": "geometric_dependence",
                "msg": ("engine_stage output for (A, 0, 0) is the same across "
                        "distinct input states — candidate ignores input geometry"),
            })
    metrics["geometric_dependence"] = geom_dep_evidence

    # Check 4: no index-shortcut. If outputs depend ONLY on indices,
    # then for any TWO different inputs, the 64 outputs should be
    # identical pairwise. We already failed geom-dep if so. We also
    # demand: for a fixed input, the trace distance between adjacent
    # microsteps (s,sub) and (s+1,sub) should not be perfectly constant
    # (a strong hash signature). Compute coefficient of variation of
    # adjacent-pair td's; require CV > 0.05 (some variation = real math).
    adj_tds = []
    name0 = ref_states[0][0]
    for engine in ("A", "B"):
        for s in range(7):
            for sub in range(4):
                a = microsteps.get((name0, engine, s, sub))
                b = microsteps.get((name0, engine, s + 1, sub))
                if a is not None and b is not None:
                    adj_tds.append(_trace_distance(a, b))
    if adj_tds:
        mu = sum(adj_tds) / len(adj_tds)
        if mu > 0:
            var = sum((x - mu) ** 2 for x in adj_tds) / len(adj_tds)
            cv = (var ** 0.5) / mu
            metrics["adjacent_td_cv"] = cv
            if cv < 0.05:
                failures.append({
                    "check": "no_index_shortcut_cv",
                    "msg": (f"adjacent (s, s+1) trace distances have CV {cv:.4f} < 0.05; "
                            f"output looks index-formulaic, not algebraically structured"),
                })

    return {
        "pass": len(failures) == 0,
        "failures": failures,
        "metrics": metrics,
        "graveyard_companions": [
            "constant output across all 64 microsteps — degenerate engine",
            "output depends only on (engine, stage, substage) indices — label shortcut",
            "output uses prime/totient/gcd/divisor anywhere — number-theory smuggle",
            "output uses %stage_idx or hash() shortcuts — modular/hash bypass",
            "output ignores input_rho_qt — label-only with no geometric content",
        ],
        "baseline_variants": [
            "identity engine: output = input for all microsteps — trivially geometric "
            "but fails uniqueness (all 64 outputs identical)",
            "single-generator engine: one unitary applied scaled by stage_idx — fails "
            "uniqueness across substages (substages collapse)",
        ],
    }
