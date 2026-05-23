#!/usr/bin/env python3
from __future__ import annotations

import ast
import json
import os
import subprocess
import time
from collections import Counter, defaultdict
from pathlib import Path

import adaptive_controller
import lint_sim_contract
import sim_program_audit


REPO = Path(__file__).resolve().parents[1]
PROBES = adaptive_controller.PROBES
RESULTS_DIR = PROBES / "a2_state" / "sim_results"
RESULT_ROOTS = [
    REPO / "system_v4/probes/a2_state/sim_results",
    REPO / "system_v4/probes/sim_results",
    REPO / "system_v4/a2_state/sim_results",
]
PIDFILES = {
    "perpetual_runner": Path("/tmp/codex_ratchet_perpetual_runner.pid"),
    "adaptive_controller": Path("/tmp/codex_ratchet_adaptive_controller.pid"),
    "autonomous_reseed": Path("/tmp/codex_ratchet_autonomous_reseed.pid"),
    "overnight_lock": Path("/tmp/codex_ratchet_overnight.lock"),
}
IMPORT_TOOL_ALIASES = {
    "numpy": "numpy",
    "scipy": "scipy",
    "torch": "pytorch",
    "torch_ga": "torch_ga",
    "torch_geometric": "pyg",
    "qutip": "qutip",
    "cirq": "cirq",
    "pennylane": "pennylane",
    "z3": "z3",
    "cvc5": "cvc5",
    "sympy": "sympy",
    "clifford": "clifford",
    "geomstats": "geomstats",
    "e3nn": "e3nn",
    "rustworkx": "rustworkx",
    "xgi": "xgi",
    "toponetx": "toponetx",
    "gudhi": "gudhi",
    "networkx": "networkx",
    "igraph": "igraph",
    "hypothesis": "hypothesis",
    "optuna": "optuna",
    "evotorch": "evotorch",
    "datasketch": "datasketch",
    "pynndescent": "pynndescent",
    "sklearn": "sklearn",
    "hdbscan": "hdbscan",
    "umap": "umap",
    "pymoo": "pymoo",
    "ribs": "ribs",
    "deap": "deap",
    "cma": "cma",
}


def _exists_safe(path: Path) -> bool:
    try:
        return path.exists()
    except OSError:
        return False


TOOL_BUNDLES = {
    "quantum_ga_bridge_stack": {
        "goal": "classical numeric + Clifford/GA + quantum state bridge lane",
        "tools": ["numpy", "scipy", "pytorch", "clifford", "torch_ga", "qutip", "cirq", "pennylane"],
    },
    "quantum_open_entangle_correlator_mega_stack": {
        "goal": "entangled 2-qubit state + open-system decay + correlator geometry bridge lane",
        "tools": ["numpy", "scipy", "qutip", "cirq", "pennylane", "pytorch", "clifford", "torch_ga"],
    },
    "qutip_open_system_stack": {
        "goal": "classical open-system + qutip Lindblad bridge lane",
        "tools": ["numpy", "scipy", "qutip"],
    },
    "quantum_open_entanglement_stack": {
        "goal": "classical Bell entanglement + bounded open-system bridge lane",
        "tools": ["numpy", "scipy", "qutip", "cirq", "pennylane"],
    },
    "classical_nonclassical_entropy_stack": {
        "goal": "classical-vs-quantum entropy gap bridge lane",
        "tools": ["numpy", "scipy", "torch", "clifford", "qutip", "pennylane", "torch_ga"],
    },
    "cirq_pennylane_entanglement_stack": {
        "goal": "classical 2-qubit entanglement bridge lane for cirq and pennylane",
        "tools": ["numpy", "scipy", "cirq", "pennylane"],
    },
    "quantum_ga_correlator_stack": {
        "goal": "quantum + GA correlator bridge lane",
        "tools": ["numpy", "scipy", "pytorch", "clifford", "torch_ga", "qutip", "cirq", "pennylane"],
    },
    "thermo_open_system_bridge_stack": {
        "goal": "thermal relaxation + open-system bridge lane",
        "tools": ["numpy", "scipy", "qutip", "cirq", "pennylane"],
    },
    "torch_clifford_ga_rotor_stack": {
        "goal": "rotor geometry bridge lane for pytorch + clifford + torch_ga",
        "tools": ["numpy", "scipy", "pytorch", "clifford", "torch_ga"],
    },
    "quantum_open_entangle_correlator_mega_stack": {
        "goal": "entanglement + open-system + reduced correlator mega bridge lane",
        "tools": ["numpy", "scipy", "qutip", "cirq", "pennylane", "pytorch", "clifford", "torch_ga"],
        "sim_name_contains": ["quantum_open_entangle_correlator_mega_stack"],
    },
    "classical_nonclassical_entropy_stack": {
        "goal": "classical/nonclassical entropy comparison bridge lane",
        "tools": ["numpy", "scipy", "pytorch", "clifford", "qutip", "pennylane", "torch_ga"],
        "sim_name_contains": ["classical_nonclassical_entropy_stack"],
    },
    "thermo_open_system_bridge_stack": {
        "goal": "thermodynamics + open-system + mixed-state circuit bridge lane",
        "tools": ["numpy", "scipy", "qutip", "cirq", "pennylane"],
        "sim_name_contains": ["thermo_open_system_bridge_stack"],
    },
    "axis0_dynamic_shell_stack": {
        "goal": "Axis 0 dynamic-shell open-system correlator bridge lane",
        "tools": [
            "numpy",
            "scipy",
            "qutip",
            "cirq",
            "pennylane",
            "pytorch",
            "clifford",
            "torch_ga",
            "rustworkx",
            "xgi",
            "toponetx",
            "gudhi",
            "sympy",
            "z3",
        ],
        "sim_name_contains": ["quantum_open_entangle_correlator_mega_stack"],
    },
    "axis0_lambda_expansion_stack": {
        "goal": "Axis 0 lambda-shell expansion and cosmology proxy lane",
        "tools": [
            "numpy",
            "scipy",
            "qutip",
            "cirq",
            "pennylane",
            "pytorch",
            "pyg",
            "cvc5",
            "clifford",
            "torch_ga",
            "e3nn",
            "rustworkx",
            "xgi",
            "toponetx",
            "gudhi",
            "sympy",
            "z3",
            "geomstats",
        ],
        "sim_name_contains": ["axis0_lambda_expansion_cosmology_stack"],
    },
    "axis0_lambda_crosslane_semantic_bridge_stack": {
        "goal": "Axis 0 lambda-shell cross-lane semantic bridge across cosmology, seam, shell, and PyG witnesses",
        "tools": [
            "numpy",
            "scipy",
            "qutip",
            "cirq",
            "pennylane",
            "pytorch",
            "pyg",
            "cvc5",
            "clifford",
            "torch_ga",
            "e3nn",
            "rustworkx",
            "xgi",
            "toponetx",
            "gudhi",
            "sympy",
            "z3",
            "geomstats",
        ],
        "sim_name_contains": ["axis0_lambda_crosslane_semantic_bridge"],
    },
    "axis0_lambda_crosslane_result_audit_stack": {
        "goal": "Axis 0 persisted-result semantic consistency audit across cosmology, seam, shell, and PyG witnesses",
        "tools": [
            "numpy",
            "scipy",
            "qutip",
            "cirq",
            "pennylane",
            "pytorch",
            "pyg",
            "cvc5",
            "clifford",
            "torch_ga",
            "e3nn",
            "rustworkx",
            "xgi",
            "toponetx",
            "gudhi",
            "sympy",
            "z3",
            "geomstats",
        ],
        "sim_name_contains": ["axis0_lambda_crosslane_result_audit"],
    },
    "axis0_history_dynamic_shell_stack": {
        "goal": "Axis 0 history-driven dynamic shell topology and expansion lane",
        "tools": [
            "numpy",
            "scipy",
            "pytorch",
            "clifford",
            "torch_ga",
            "rustworkx",
            "xgi",
            "toponetx",
            "gudhi",
            "sympy",
            "z3",
            "geomstats",
        ],
        "sim_name_contains": ["axis0_dynamic_shell"],
    },
    "axis0_iscalar_deep_stack": {
        "goal": "Axis 0 i-scalar ranking grounded in the deep shell contract",
        "tools": [
            "numpy",
            "scipy",
            "pytorch",
            "clifford",
            "torch_ga",
            "rustworkx",
            "xgi",
            "toponetx",
            "gudhi",
            "sympy",
            "z3",
            "geomstats",
        ],
        "sim_name_contains": ["axis0_iscalar_sweep"],
    },
    "axis0_fep_framing_deep_stack": {
        "goal": "Axis 0 FEP framing grounded in the deep shell contract",
        "tools": [
            "numpy",
            "scipy",
            "pytorch",
            "clifford",
            "torch_ga",
            "rustworkx",
            "xgi",
            "toponetx",
            "gudhi",
            "sympy",
            "z3",
            "geomstats",
        ],
        "sim_name_contains": ["axis0_fep_compression_framing"],
    },
    "axis0_fe_indexed_xi_hist_deep_stack": {
        "goal": "Axis 0 Fe-indexed Xi-history ranking grounded in the deep shell contract",
        "tools": [
            "numpy",
            "scipy",
            "pytorch",
            "clifford",
            "torch_ga",
            "rustworkx",
            "xgi",
            "toponetx",
            "gudhi",
            "sympy",
            "z3",
            "geomstats",
        ],
        "sim_name_contains": ["axis0_fe_indexed_xi_hist"],
    },
    "axis0_coarising_stress_deep_stack": {
        "goal": "Axis 0 co-arising stress ranking grounded in the deep shell contract",
        "tools": [
            "numpy",
            "scipy",
            "pytorch",
            "clifford",
            "torch_ga",
            "rustworkx",
            "xgi",
            "toponetx",
            "gudhi",
            "sympy",
            "z3",
            "geomstats",
        ],
        "sim_name_contains": ["axis0_coarising_stress_test"],
    },
    "axis0_bridge_search_deep_stack": {
        "goal": "Axis 0 bridge-search ranking grounded in the deep shell contract",
        "tools": [
            "numpy",
            "scipy",
            "pytorch",
            "clifford",
            "torch_ga",
            "rustworkx",
            "xgi",
            "toponetx",
            "gudhi",
            "sympy",
            "z3",
            "geomstats",
        ],
        "sim_name_contains": ["axis0_bridge_search"],
    },
    "axis0_phase3_composite_deep_stack": {
        "goal": "Axis 0 Phase-3 composite ranking grounded in the deep shell contract",
        "tools": [
            "numpy",
            "scipy",
            "pytorch",
            "clifford",
            "torch_ga",
            "rustworkx",
            "xgi",
            "toponetx",
            "gudhi",
            "sympy",
            "z3",
            "geomstats",
        ],
        "sim_name_contains": ["axis0_phase3_composite"],
    },
    "axis0_phase4_final_bridge_deep_stack": {
        "goal": "Axis 0 Phase-4 final-bridge ranking grounded in the deep shell contract",
        "tools": [
            "numpy",
            "scipy",
            "pytorch",
            "clifford",
            "torch_ga",
            "rustworkx",
            "xgi",
            "toponetx",
            "gudhi",
            "sympy",
            "z3",
            "geomstats",
        ],
        "sim_name_contains": ["axis0_phase4_final_bridge"],
    },
    "axis0_phase5a_marginal_preserving_deep_stack": {
        "goal": "Axis 0 Phase-5A marginal-preserving honesty surface grounded in the deep shell contract",
        "tools": [
            "numpy",
            "scipy",
            "pytorch",
            "clifford",
            "torch_ga",
            "rustworkx",
            "xgi",
            "toponetx",
            "gudhi",
            "sympy",
            "z3",
            "geomstats",
        ],
        "sim_name_contains": ["axis0_phase5a_marginal_preserving"],
    },
    "axis0_phase5b_stability_deep_stack": {
        "goal": "Axis 0 Phase-5B stability surface grounded in the deep shell contract",
        "tools": [
            "numpy",
            "scipy",
            "pytorch",
            "clifford",
            "torch_ga",
            "rustworkx",
            "xgi",
            "toponetx",
            "gudhi",
            "sympy",
            "z3",
            "geomstats",
        ],
        "sim_name_contains": ["axis0_phase5b_stability"],
    },
    "axis0_phase5c_honesty_deep_stack": {
        "goal": "Axis 0 Phase-5C earned-vs-smuggled honesty surface grounded in the deep shell contract",
        "tools": [
            "numpy",
            "scipy",
            "pytorch",
            "clifford",
            "torch_ga",
            "rustworkx",
            "xgi",
            "toponetx",
            "gudhi",
            "sympy",
            "z3",
            "geomstats",
        ],
        "sim_name_contains": ["axis0_phase5c_earned_vs_smuggled"],
    },
    "axis0_phase6_clifford_anomaly_deep_stack": {
        "goal": "Axis 0 Phase-6 Clifford anomaly surface grounded in the deep shell contract",
        "tools": [
            "numpy",
            "scipy",
            "pytorch",
            "clifford",
            "torch_ga",
            "rustworkx",
            "xgi",
            "toponetx",
            "gudhi",
            "sympy",
            "z3",
            "geomstats",
        ],
        "sim_name_contains": ["axis0_phase6_clifford_anomaly"],
    },
    "axis0_phase6_point_reference_deep_stack": {
        "goal": "Axis 0 Phase-6 point-reference surface grounded in the deep shell contract",
        "tools": [
            "numpy",
            "scipy",
            "pytorch",
            "clifford",
            "torch_ga",
            "rustworkx",
            "xgi",
            "toponetx",
            "gudhi",
            "sympy",
            "z3",
            "geomstats",
        ],
        "sim_name_contains": ["axis0_phase6_point_reference"],
    },
    "axis0_chiral_deep_search_deep_stack": {
        "goal": "Axis 0 chiral deep-search surface grounded in the deep shell contract",
        "tools": [
            "numpy",
            "scipy",
            "pytorch",
            "clifford",
            "torch_ga",
            "rustworkx",
            "xgi",
            "toponetx",
            "gudhi",
            "sympy",
            "z3",
            "geomstats",
        ],
        "sim_name_contains": ["axis0_chiral_deep_search"],
    },
    "axis0_axis6_coupling_seam_deep_stack": {
        "goal": "Axis 0 x Axis 6 coupling seam grounded in the deep shell contract",
        "tools": [
            "numpy",
            "scipy",
            "pytorch",
            "pyg",
            "cvc5",
            "clifford",
            "torch_ga",
            "e3nn",
            "rustworkx",
            "xgi",
            "toponetx",
            "gudhi",
            "sympy",
            "z3",
            "geomstats",
        ],
        "sim_name_contains": ["axis0_axis6_coupling_seam"],
    },
    "axis0_through_shells_deep_stack": {
        "goal": "Axis 0 gradient-through-shells mechanics grounded in the deep shell contract",
        "tools": [
            "numpy",
            "scipy",
            "pytorch",
            "pyg",
            "cvc5",
            "clifford",
            "torch_ga",
            "e3nn",
            "rustworkx",
            "xgi",
            "toponetx",
            "gudhi",
            "sympy",
            "z3",
            "geomstats",
        ],
        "sim_name_contains": ["axis0_through_shells"],
    },
    "axis0_attractor_basin_boundary_deep_stack": {
        "goal": "Axis 0 attractor-basin boundary grounded in the deep shell contract",
        "tools": [
            "numpy",
            "scipy",
            "pytorch",
            "clifford",
            "torch_ga",
            "rustworkx",
            "xgi",
            "toponetx",
            "gudhi",
            "sympy",
            "z3",
            "geomstats",
        ],
        "sim_name_contains": ["axis0_attractor_basin_boundary"],
    },
    "phi0_signed_kernel_bounded_point_family_deep_stack": {
        "goal": "Phi0 signed-kernel bounded point-family lane grounded in the deep shell contract",
        "tools": [
            "numpy",
            "scipy",
            "pytorch",
            "clifford",
            "torch_ga",
            "rustworkx",
            "xgi",
            "toponetx",
            "gudhi",
            "sympy",
            "z3",
            "geomstats",
        ],
        "sim_name_contains": ["phi0_signed_kernel_bounded_point_family"],
    },
    "axis0_cut_kernel_sweep_deep_stack": {
        "goal": "Axis 0 cut-kernel sweep grounded in the deep shell contract",
        "tools": [
            "numpy",
            "scipy",
            "pytorch",
            "clifford",
            "torch_ga",
            "rustworkx",
            "xgi",
            "toponetx",
            "gudhi",
            "sympy",
            "z3",
            "geomstats",
        ],
        "sim_name_contains": ["axis0_cut_kernel_sweep"],
    },
    "axis0_entropy_gradient_constraint_deep_stack": {
        "goal": "Axis 0 entropy-gradient constraint grounded in the deep shell contract",
        "tools": [
            "numpy",
            "scipy",
            "pytorch",
            "clifford",
            "torch_ga",
            "rustworkx",
            "xgi",
            "toponetx",
            "gudhi",
            "sympy",
            "z3",
            "geomstats",
        ],
        "sim_name_contains": ["axis0_entropy_gradient_constraint_canonical"],
    },
    "axis0_orbit_phase_alignment_deep_stack": {
        "goal": "Axis 0 orbit-phase alignment grounded in the deep shell contract",
        "tools": [
            "numpy",
            "scipy",
            "pytorch",
            "clifford",
            "torch_ga",
            "rustworkx",
            "xgi",
            "toponetx",
            "gudhi",
            "sympy",
            "z3",
            "geomstats",
        ],
        "sim_name_contains": ["axis0_orbit_phase_alignment"],
    },
    "axis0_gtower_gradient_cascade_deep_stack": {
        "goal": "Axis 0 G-tower gradient cascade grounded in the deep shell contract",
        "tools": [
            "numpy",
            "scipy",
            "pytorch",
            "clifford",
            "torch_ga",
            "rustworkx",
            "xgi",
            "toponetx",
            "gudhi",
            "sympy",
            "z3",
            "geomstats",
        ],
        "sim_name_contains": ["axis0_gtower_gradient_cascade"],
    },
    "axis0_pyg_proxy_deep_stack": {
        "goal": "Axis 0 PyG proxy gradient lane grounded in the deep shell contract",
        "tools": [
            "numpy",
            "scipy",
            "pytorch",
            "pyg",
            "clifford",
            "torch_ga",
            "rustworkx",
            "xgi",
            "toponetx",
            "gudhi",
            "sympy",
            "z3",
            "geomstats",
        ],
        "sim_name_contains": ["axis0_pyg_proxy"],
    },
    "symbolic_solver_stack": {
        "goal": "solver + symbolic + rotor reference lane",
        "tools": ["pytorch", "z3", "cvc5", "sympy", "clifford"],
    },
    "equivariant_geometry_stack": {
        "goal": "equivariant geometry reference lane",
        "tools": ["pytorch", "clifford", "e3nn", "geomstats", "sympy"],
    },
    "graph_topology_stack": {
        "goal": "graph/hypergraph/topology reference lane",
        "tools": ["pytorch", "pyg", "rustworkx", "xgi", "toponetx", "gudhi"],
    },
    "symbolic_graph_topology_stack": {
        "goal": "solver + rotor + graph topology mega reference lane",
        "tools": ["pytorch", "z3", "cvc5", "sympy", "clifford", "pyg", "rustworkx", "xgi", "toponetx", "gudhi"],
    },
    "symbolic_graph_manifold_stack": {
        "goal": "solver + graph topology + manifold clustering bridge lane",
        "tools": [
            "pytorch",
            "z3",
            "cvc5",
            "sympy",
            "clifford",
            "pyg",
            "rustworkx",
            "xgi",
            "toponetx",
            "gudhi",
            "datasketch",
            "pynndescent",
            "umap",
            "hdbscan",
            "sklearn",
        ],
    },
    "symbolic_graph_manifold_search_stack": {
        "goal": "solver + graph topology + manifold + searched archive mega lane",
        "tools": [
            "pytorch",
            "z3",
            "cvc5",
            "sympy",
            "clifford",
            "pyg",
            "rustworkx",
            "xgi",
            "toponetx",
            "gudhi",
            "datasketch",
            "pynndescent",
            "umap",
            "hdbscan",
            "sklearn",
            "optuna",
            "pymoo",
            "ribs",
            "deap",
            "evotorch",
        ],
    },
    "equivariant_symbolic_graph_manifold_search_stack": {
        "goal": "equivariant + solver + graph topology + manifold + searched archive mega lane",
        "tools": [
            "pytorch",
            "z3",
            "cvc5",
            "sympy",
            "clifford",
            "e3nn",
            "geomstats",
            "pyg",
            "rustworkx",
            "xgi",
            "toponetx",
            "gudhi",
            "datasketch",
            "pynndescent",
            "umap",
            "hdbscan",
            "sklearn",
            "optuna",
            "pymoo",
            "ribs",
            "deap",
            "evotorch",
        ],
    },
    "manifold_cluster_stack": {
        "goal": "manifold + ANN + embedding + density clustering reference lane",
        "tools": ["pytorch", "datasketch", "pynndescent", "umap", "hdbscan", "sklearn"],
    },
    "manifold_search_archive_stack": {
        "goal": "search-tuned manifold + archive reference lane",
        "tools": ["pytorch", "datasketch", "pynndescent", "umap", "hdbscan", "sklearn", "optuna", "ribs"],
    },
    "search_archive_stack": {
        "goal": "optimizer/archive/search reference lane",
        "tools": ["pytorch", "optuna", "pymoo", "ribs", "deap", "evotorch"],
    },
}


def _canonical_tool(name: str) -> str:
    return IMPORT_TOOL_ALIASES.get(name.strip().lower().replace("-", "_"), name.strip().lower().replace("-", "_"))


def _results_dir() -> Path:
    return PROBES / "a2_state" / "sim_results"


def _rel_or_abs(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def _run(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str] | None:
    try:
        return subprocess.run(args, cwd=cwd or REPO, capture_output=True, text=True)
    except (FileNotFoundError, PermissionError, OSError):
        return None


def _process_command(pid: int) -> str | None:
    proc = _run(["ps", "-p", str(pid), "-o", "command="])
    if proc is None or proc.returncode != 0:
        return None
    text = proc.stdout.strip()
    return text or None


def _pidfile_status(name: str, pidfile: Path) -> dict:
    status = {
        "name": name,
        "pidfile": str(pidfile),
        "pid": None,
        "alive": None,
        "alive_state": "missing_pidfile",
        "command": None,
    }
    if not pidfile.exists():
        return status
    try:
        pid = int(pidfile.read_text(encoding="utf-8").strip())
    except Exception:
        status["alive_state"] = "invalid_pidfile"
        return status
    status["pid"] = pid
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        status["alive"] = False
        status["alive_state"] = "stale_pid"
        return status
    except PermissionError:
        status["command"] = _process_command(pid)
        if status["command"]:
            status["alive"] = True
            status["alive_state"] = "ps_visible_permission_limited"
            return status
        status["alive"] = None
        status["alive_state"] = "permission_limited"
        return status
    except OSError:
        status["command"] = _process_command(pid)
        if status["command"]:
            status["alive"] = True
            status["alive_state"] = "ps_visible_os_error_limited"
            return status
        status["alive"] = None
        status["alive_state"] = "os_error_limited"
        return status
    status["alive"] = True
    status["alive_state"] = "alive"
    status["command"] = _process_command(pid)
    return status


def _wrapper_processes() -> list[dict]:
    rows = []
    for args in (["ps", "aux"], ["ps", "-Ao", "pid=,command="]):
        proc = _run(args)
        if proc is None or proc.returncode != 0:
            continue
        for line in proc.stdout.splitlines():
            line = line.strip()
            if not line or "scripts/perpetual_runner.sh" not in line:
                continue
            if args == ["ps", "aux"]:
                parts = line.split(None, 10)
                if len(parts) < 11:
                    continue
                pid_text = parts[1]
                cmd = parts[10]
            else:
                pid_text, _, cmd = line.partition(" ")
            try:
                pid = int(pid_text.strip())
            except ValueError:
                continue
            rows.append({"pid": pid, "command": cmd.strip()})
        if rows:
            break
    return rows


def _queue_claim_summary(limit: int = 8) -> dict:
    claimed_dir = adaptive_controller.QUEUE / "claimed"
    samples = []
    if claimed_dir.exists():
        for path in sorted(claimed_dir.glob("*.json.*"))[:limit]:
            data = adaptive_controller.load_result(path)
            samples.append({
                "file": path.name,
                "sim": Path(str(data.get("sim_path", ""))).name,
                "lane": data.get("lane"),
                "claimed_at": data.get("claimed_at"),
            })
    return {"count": adaptive_controller.queue_counts().get("claimed", 0), "samples": samples}


def _blocked_surface(limit: int = 8) -> dict:
    blocked_dir = adaptive_controller.QUEUE / "blocked"
    reasons: Counter[str] = Counter()
    sim_counts: Counter[str] = Counter()
    samples = []
    if blocked_dir.exists():
        for path in sorted(blocked_dir.iterdir()):
            if not path.is_file():
                continue
            data = adaptive_controller.load_result(path)
            reason = str(data.get("blocked_reason") or data.get("reason") or "unknown")
            sim = Path(str(data.get("sim_path", ""))).name
            reasons[reason] += 1
            if sim:
                sim_counts[sim] += 1
            if len(samples) < limit:
                samples.append({
                    "file": path.name,
                    "reason": reason,
                    "sim": sim,
                    "lane": data.get("lane"),
                })
    duplicate_sims = {sim: count for sim, count in sim_counts.items() if count > 1}
    return {
        "active_count": sum(reasons.values()),
        "resolved_count": adaptive_controller.resolved_blocked_count(),
        "reasons": dict(reasons),
        "unique_sims": len(sim_counts),
        "duplicate_entries": sum(count - 1 for count in duplicate_sims.values()),
        "duplicate_sims": duplicate_sims,
        "samples": samples,
    }


def _queue_dir_freshness(path: Path) -> dict:
    newest_name = None
    newest_mtime = None
    if path.exists():
        for entry in path.iterdir():
            if not entry.is_file():
                continue
            try:
                mtime = entry.stat().st_mtime
            except OSError:
                continue
            if newest_mtime is None or mtime > newest_mtime:
                newest_mtime = mtime
                newest_name = entry.name
    age = None if newest_mtime is None else max(0.0, time.time() - newest_mtime)
    return {
        "newest_file": newest_name,
        "newest_age_sec": age,
        "active_within_60s": age is not None and age < 60,
        "active_within_300s": age is not None and age < 300,
    }


def _claimed_age_surface(claimed_dir: Path, limit: int = 5) -> dict:
    now = time.time()
    ages: list[dict[str, object]] = []
    if claimed_dir.exists():
        for path in claimed_dir.glob("*.json.*"):
            try:
                data = adaptive_controller.load_result(path)
            except Exception:
                data = {}
            try:
                fallback_ts = path.stat().st_mtime
            except OSError:
                fallback_ts = now
            claimed_at = data.get("claimed_at") if isinstance(data, dict) else None
            ts = claimed_at if isinstance(claimed_at, (int, float)) else fallback_ts
            age = max(0.0, now - float(ts))
            ages.append({
                "file": path.name,
                "sim": Path(str(data.get("sim_path", ""))).name if isinstance(data, dict) else "",
                "age_sec": age,
            })
    ages.sort(key=lambda row: float(row["age_sec"]), reverse=True)
    return {
        "count": len(ages),
        "oldest_age_sec": ages[0]["age_sec"] if ages else None,
        "over_300s": sum(1 for row in ages if float(row["age_sec"]) >= 300),
        "over_900s": sum(1 for row in ages if float(row["age_sec"]) >= 900),
        "samples": ages[:limit],
    }


def _git_layer(path: str) -> str:
    if path.startswith("READ ONLY Legacy "):
        return "legacy_copies"
    if path.startswith("obsidian_vault/"):
        return "owner_vault"
    if path.startswith("system_v5/docs/") or path.endswith(".md"):
        return "owner_docs"
    if (
        path.startswith("system_v4/probes/")
        and path.endswith("_results.json")
        and not path.startswith("system_v4/probes/a2_state/sim_results/")
        and not path.startswith("system_v4/probes/sim_results/")
    ):
        return "misplaced_probe_results"
    if path.startswith("system_v4/probes/sim_") and path.endswith(".py"):
        return "probe_sources"
    if path.startswith("system_v4/probes/a2_state/sim_results/") or path.startswith("system_v4/probes/sim_results/"):
        return "probe_results"
    if path.startswith("system_v4/a2_state/sim_results/") or path.startswith("system_v4/a2_state/audit_logs/"):
        return "system_results"
    if path.startswith("overnight_logs/"):
        return "runner_logs"
    if path.startswith("scripts/") or path.startswith("system_v5/tests/"):
        return "code_and_tests"
    return "other"


def _git_status_entries() -> list[dict[str, str]]:
    proc = _run(["git", "status", "--short", "--untracked-files=all"])
    if proc is None:
        return []
    entries: list[dict[str, str]] = []
    for line in proc.stdout.splitlines():
        if not line:
            continue
        status = line[:2]
        path = line[3:].strip()
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        entries.append({"status": status, "path": path.strip('"')})
    return entries


def git_surface() -> dict:
    entries = _git_status_entries()
    if not entries:
        return {"total_entries": 0, "layers": {}, "samples": {}, "error": "git_status_unavailable"}
    counts: Counter[str] = Counter()
    samples: defaultdict[str, list[dict]] = defaultdict(list)
    total = 0
    for entry in entries:
        total += 1
        status = entry["status"]
        path = entry["path"]
        layer = _git_layer(path)
        counts[layer] += 1
        if len(samples[layer]) < 8:
            samples[layer].append({"status": status, "path": path})
    return {
        "total_entries": total,
        "layers": dict(counts),
        "samples": dict(samples),
        "cleanup_posture": {
            "code_and_tests": "KEEP_ACTIVE",
            "runner_logs": "KEEP_ACTIVE",
            "probe_sources": "BLOCKED_REQUIRES_PREP",
            "misplaced_probe_results": "REPAIR_TO_CANONICAL_ROOT",
            "probe_results": "KEEP_ACTIVE",
            "system_results": "KEEP_ACTIVE",
            "owner_vault": "BLOCKED_REQUIRES_PREP",
            "owner_docs": "BLOCKED_REQUIRES_PREP",
            "legacy_copies": "MOVE_TO_QUARANTINE",
            "other": "BLOCKED_REQUIRES_PREP",
        },
    }


def _string_key(node: ast.AST | None) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _depth_value(node: ast.AST | None):
    if isinstance(node, ast.Constant) and (node.value is None or isinstance(node.value, str)):
        return node.value
    return None


def _module_literal(tree: ast.AST, name: str):
    for node in ast.iter_child_nodes(tree):
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == name:
                try:
                    return ast.literal_eval(node.value)
                except Exception:
                    return None
    return None


def _module_dict_keys(tree: ast.AST, name: str) -> set[str]:
    for node in ast.iter_child_nodes(tree):
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if not isinstance(target, ast.Name) or target.id != name:
                continue
            if isinstance(node.value, ast.Dict):
                return {
                    str(raw)
                    for raw in (
                        _string_key(key)
                        for key in node.value.keys
                    )
                    if raw is not None
                }
            literal = _module_literal(tree, name)
            if isinstance(literal, dict):
                return {str(raw) for raw in literal}
            return set()
    return set()


def _module_classification(path: Path) -> str | None:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    for node in ast.iter_child_nodes(tree):
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if not isinstance(target, ast.Name) or target.id != "classification":
                continue
            try:
                value = ast.literal_eval(node.value)
            except Exception:
                return None
            return value if isinstance(value, str) else None
    return None


def _module_depth_map(tree: ast.AST, name: str, manifest_keys: set[str] | None = None) -> dict[str, object] | None:
    base: dict[str, object] | None = None
    for node in ast.iter_child_nodes(tree):
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == name:
                if isinstance(node.value, ast.Dict):
                    parsed: dict[str, object] = {}
                    for key_node, value_node in zip(node.value.keys, node.value.values):
                        key = _string_key(key_node)
                        if key is None:
                            continue
                        value = _depth_value(value_node)
                        if value is None and not (
                            isinstance(value_node, ast.Constant) and value_node.value is None
                        ):
                            continue
                        parsed[key] = value
                    base = parsed
                elif (
                    isinstance(node.value, ast.DictComp)
                    and isinstance(node.value.key, ast.Name)
                    and node.value.key.id
                    and isinstance(node.value.value, ast.Constant)
                    and node.value.value.value is None
                    and len(node.value.generators) == 1
                    and isinstance(node.value.generators[0].iter, ast.Name)
                    and node.value.generators[0].iter.id == "TOOL_MANIFEST"
                    and manifest_keys
                ):
                    base = {key: None for key in manifest_keys}
                else:
                    literal = _module_literal(tree, name)
                    base = literal if isinstance(literal, dict) else None
            elif (
                isinstance(target, ast.Subscript)
                and isinstance(target.value, ast.Name)
                and target.value.id == name
                and base is not None
            ):
                key = _string_key(target.slice)
                value = _depth_value(node.value)
                if key is not None and value is not None:
                    base[key] = value
    return base


def _imported_tools(path: Path) -> tuple[set[str], bool]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except Exception:
        return set(), False
    tools: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                head = alias.name.split(".", 1)[0]
                tool = IMPORT_TOOL_ALIASES.get(head)
                if tool:
                    tools.add(tool)
        elif isinstance(node, ast.ImportFrom):
            if not node.module:
                continue
            head = node.module.split(".", 1)[0]
            tool = IMPORT_TOOL_ALIASES.get(head)
            if tool:
                tools.add(tool)
    return tools, True


def _capability_probe_status(tool: str) -> dict[str, object]:
    results_dir = _results_dir()
    candidates = [
        (
            PROBES / f"sim_{tool}_capability.py",
            results_dir / f"{tool}_capability_results.json",
        ),
        (
            PROBES / f"sim_capability_{tool}_isolated.py",
            results_dir / f"sim_capability_{tool}_isolated_results.json",
        ),
    ]
    probe_files = [_rel_or_abs(probe) for probe, _ in candidates if _exists_safe(probe)]
    result_files = [_rel_or_abs(result) for _, result in candidates if _exists_safe(result)]
    status = "missing"
    if probe_files:
        status = "probe_stale"
    for _probe, result in candidates:
        if not _exists_safe(result):
            continue
        try:
            data = json.loads(result.read_text(encoding="utf-8"))
        except Exception:
            status = "probe_failing"
            continue
        summary = data.get("summary") if isinstance(data, dict) else {}
        passing = (
            data.get("overall_pass") is True
            or data.get("all_pass") is True
            or (isinstance(summary, dict) and summary.get("all_pass") is True)
            or (isinstance(summary, dict) and summary.get("all_passed") is True)
            or (
                isinstance(summary, dict)
                and isinstance(summary.get("passed"), int)
                and isinstance(summary.get("total"), int)
                and summary.get("total", 0) > 0
                and summary.get("passed") == summary.get("total")
            )
        )
        status = "passing" if passing else "probe_failing"
        if passing:
            break
    return {
        "status": status,
        "probe_files": probe_files,
        "result_files": result_files,
    }


def _result_paths_for_probe(path: Path) -> list[Path]:
    probe_stem = path.stem
    result_names = [f"{probe_stem}_results.json"]
    if probe_stem.startswith("sim_"):
        result_names.append(f"{probe_stem[4:]}_results.json")
    candidates: list[Path] = []
    seen: set[str] = set()
    for root in RESULT_ROOTS:
        for name in result_names:
            candidate = root / name
            key = str(candidate)
            if key in seen:
                continue
            seen.add(key)
            candidates.append(candidate)
    return candidates


def _first_result_for_probe(path: Path) -> Path | None:
    return next((candidate for candidate in _result_paths_for_probe(path) if _exists_safe(candidate)), None)


def _integration_relationship_surface(
    sim_rows: list[dict[str, object]],
    all_tools: list[str],
    limit: int = 12,
) -> dict[str, object]:
    max_stack_sims = []
    for row in sim_rows:
        imported_tools = sorted(set(row["imported_tools"]))
        declared_tools = sorted(set(row["declared_tools"]))
        load_bearing_tools = sorted(set(row["load_bearing_tools"]))
        max_stack_sims.append({
            "sim": row["sim"],
            "imported_tool_count": len(imported_tools),
            "header_declared_tool_count": len(declared_tools),
            "load_bearing_tool_count": len(load_bearing_tools),
            "imported_tools": imported_tools,
            "header_declared_tools": declared_tools,
            "load_bearing_tools": load_bearing_tools,
        })
    max_stack_sims.sort(
        key=lambda row: (
            -int(row["load_bearing_tool_count"]),
            -int(row["header_declared_tool_count"]),
            -int(row["imported_tool_count"]),
            str(row["sim"]),
        )
    )

    declared_target_tools = sorted(
        {
            tool
            for row in sim_rows
            for tool in set(row["declared_tools"])
        }
    )
    remaining_declared_tools = set(declared_target_tools)
    greedy_cover_rows = []
    cover_candidates = list(sim_rows)
    while remaining_declared_tools:
        best = None
        best_new_tools: set[str] = set()
        for row in cover_candidates:
            row_declared_tools = set(row["declared_tools"])
            new_tools = row_declared_tools & remaining_declared_tools
            if not new_tools:
                continue
            if best is None:
                best = row
                best_new_tools = new_tools
                continue
            best_key = (
                len(best_new_tools),
                len(set(best["load_bearing_tools"]) & remaining_declared_tools),
                len(set(best["declared_tools"])),
                len(set(best["imported_tools"])),
                -len(str(best["sim"])),
            )
            row_key = (
                len(new_tools),
                len(set(row["load_bearing_tools"]) & remaining_declared_tools),
                len(set(row["declared_tools"])),
                len(set(row["imported_tools"])),
                -len(str(row["sim"])),
            )
            if row_key > best_key or (row_key == best_key and str(row["sim"]) < str(best["sim"])):
                best = row
                best_new_tools = new_tools
        if best is None:
            break
        greedy_cover_rows.append({
            "sim": best["sim"],
            "new_header_declared_tools": sorted(best_new_tools),
            "new_load_bearing_tools": sorted(set(best["load_bearing_tools"]) & remaining_declared_tools),
            "header_declared_tool_count": len(set(best["declared_tools"])),
            "load_bearing_tool_count": len(set(best["load_bearing_tools"])),
            "imported_tool_count": len(set(best["imported_tools"])),
        })
        remaining_declared_tools -= best_new_tools
        cover_candidates = [row for row in cover_candidates if row["sim"] != best["sim"]]

    companion_stats: defaultdict[str, defaultdict[str, dict[str, object]]] = defaultdict(
        lambda: defaultdict(
            lambda: {
                "co_import_sims": 0,
                "co_declared_sims": 0,
                "co_load_bearing_sims": 0,
                "sample_sims": [],
            }
        )
    )
    tool_anchor_rows: defaultdict[str, list[dict[str, object]]] = defaultdict(list)
    for row in sim_rows:
        imported_tools = sorted(set(row["imported_tools"]))
        declared_tools = sorted(set(row["declared_tools"]))
        load_bearing_tools = sorted(set(row["load_bearing_tools"]))
        imported_set = set(imported_tools)
        declared_set = set(declared_tools)
        load_bearing_set = set(load_bearing_tools)
        for tool in imported_tools:
            tool_anchor_rows[tool].append({
                "sim": row["sim"],
                "imported_tool_count": len(imported_set),
                "header_declared_tool_count": len(declared_set),
                "load_bearing_tool_count": len(load_bearing_set),
            })
        for tool in imported_tools:
            for companion in imported_set - {tool}:
                companion_row = companion_stats[tool][companion]
                companion_row["co_import_sims"] = int(companion_row["co_import_sims"]) + 1
                if companion in declared_set and tool in declared_set:
                    companion_row["co_declared_sims"] = int(companion_row["co_declared_sims"]) + 1
                if companion in load_bearing_set and tool in load_bearing_set:
                    companion_row["co_load_bearing_sims"] = int(companion_row["co_load_bearing_sims"]) + 1
                if len(companion_row["sample_sims"]) < 5:
                    companion_row["sample_sims"].append(str(row["sim"]))

    per_tool_best_companions: dict[str, dict[str, object]] = {}
    for tool in all_tools:
        anchor_rows = tool_anchor_rows.get(tool, [])
        anchor_rows.sort(
            key=lambda row: (
                -int(row["load_bearing_tool_count"]),
                -int(row["header_declared_tool_count"]),
                -int(row["imported_tool_count"]),
                str(row["sim"]),
            )
        )
        companion_rows = []
        for companion, stats in companion_stats.get(tool, {}).items():
            companion_rows.append({
                "tool": companion,
                "co_import_sims": int(stats["co_import_sims"]),
                "co_declared_sims": int(stats["co_declared_sims"]),
                "co_load_bearing_sims": int(stats["co_load_bearing_sims"]),
                "sample_sims": list(stats["sample_sims"])[:5],
            })
        companion_rows.sort(
            key=lambda row: (
                -int(row["co_load_bearing_sims"]),
                -int(row["co_declared_sims"]),
                -int(row["co_import_sims"]),
                str(row["tool"]),
            )
        )
        per_tool_best_companions[tool] = {
            "best_companions": companion_rows[:limit],
            "best_anchor_sims": anchor_rows[:limit],
        }

    return {
        "max_stack_sims": max_stack_sims[:limit],
        "greedy_declared_cover": {
            "target_tool_count": len(declared_target_tools),
            "covered_tool_count": len(declared_target_tools) - len(remaining_declared_tools),
            "uncovered_tools": sorted(remaining_declared_tools),
            "selected_sims": greedy_cover_rows[:limit],
        },
        "per_tool_best_companions": per_tool_best_companions,
    }


def tool_integration_surface(limit: int = 12) -> dict:
    missing_depth: Counter[str] = Counter()
    missing_manifest: Counter[str] = Counter()
    samples: list[dict[str, object]] = []
    sim_rows: list[dict[str, object]] = []
    per_tool: defaultdict[str, dict[str, object]] = defaultdict(
        lambda: {
            "imported_in_sims": 0,
            "missing_manifest": 0,
            "missing_depth": 0,
            "load_bearing_witnesses": 0,
            "supportive_witnesses": 0,
            "decorative_witnesses": 0,
            "header_declared_without_depth": 0,
            "sample_witnesses": [],
        }
    )
    parse_failures = 0
    audited = 0

    for path in sorted(PROBES.glob("sim_*.py")):
        if " 2" in path.name:
            continue
        imported_tools, parsed = _imported_tools(path)
        if not parsed:
            parse_failures += 1
            continue
        if not imported_tools:
            continue
        audited += 1
        for tool in imported_tools:
            per_tool[tool]["imported_in_sims"] = int(per_tool[tool]["imported_in_sims"]) + 1
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except Exception:
            parse_failures += 1
            continue
        manifest_tools = _module_dict_keys(tree, "TOOL_MANIFEST")
        depth = _module_depth_map(tree, "TOOL_INTEGRATION_DEPTH", manifest_tools)
        manifest = {tool: True for tool in manifest_tools} if manifest_tools else None
        depth_tools = set(depth) if isinstance(depth, dict) else set()
        load_bearing_tools = (
            {
                _canonical_tool(str(raw_tool))
                for raw_tool, level in depth.items()
                if level == "load_bearing"
            }
            if isinstance(depth, dict)
            else set()
        )
        declared_tools = (
            set(imported_tools)
            & {_canonical_tool(str(tool)) for tool in manifest_tools}
            & {_canonical_tool(str(tool)) for tool in depth_tools}
        )
        sim_rows.append({
            "sim": path.name,
            "imported_tools": set(imported_tools),
            "manifest_tools": {_canonical_tool(str(tool)) for tool in manifest_tools},
            "depth_tools": {_canonical_tool(str(tool)) for tool in depth_tools},
            "declared_tools": declared_tools,
            "load_bearing_tools": load_bearing_tools,
        })
        if isinstance(depth, dict):
            for raw_tool, level in depth.items():
                tool = _canonical_tool(str(raw_tool))
                row = per_tool[tool]
                if level == "load_bearing":
                    row["load_bearing_witnesses"] = int(row["load_bearing_witnesses"]) + 1
                elif level == "supportive":
                    row["supportive_witnesses"] = int(row["supportive_witnesses"]) + 1
                elif level == "decorative":
                    row["decorative_witnesses"] = int(row["decorative_witnesses"]) + 1
                elif tool in imported_tools:
                    row["header_declared_without_depth"] = int(row["header_declared_without_depth"]) + 1
                if (
                    level in {"load_bearing", "supportive", "decorative"}
                    and len(row["sample_witnesses"]) < 5
                ):
                    row["sample_witnesses"].append(path.name)
        missing_manifest_tools = sorted(
            tool for tool in imported_tools
            if not isinstance(manifest, dict) or tool not in manifest
        )
        missing_depth_tools = sorted(
            tool for tool in imported_tools
            if not isinstance(depth, dict) or tool not in depth
        )
        for tool in missing_manifest_tools:
            missing_manifest[tool] += 1
            per_tool[tool]["missing_manifest"] = int(per_tool[tool]["missing_manifest"]) + 1
        for tool in missing_depth_tools:
            missing_depth[tool] += 1
            per_tool[tool]["missing_depth"] = int(per_tool[tool]["missing_depth"]) + 1
        if (missing_manifest_tools or missing_depth_tools) and len(samples) < limit:
            samples.append({
                "sim": path.name,
                "imported_tools": sorted(imported_tools),
                "missing_manifest_tools": missing_manifest_tools,
                "missing_depth_tools": missing_depth_tools,
            })

    all_tools = sorted(
        set(per_tool)
        | {_canonical_tool(path.stem.removeprefix("sim_").removesuffix("_capability")) for path in PROBES.glob("sim_*_capability.py")}
        | {_canonical_tool(path.stem.removeprefix("sim_capability_").removesuffix("_isolated")) for path in PROBES.glob("sim_capability_*_isolated.py")}
    )
    per_tool_report: dict[str, dict[str, object]] = {}
    for tool in all_tools:
        row = dict(per_tool[tool])
        row.update(_capability_probe_status(tool))
        per_tool_report[tool] = row

    relationship_surface = _integration_relationship_surface(sim_rows, all_tools, limit)

    bundle_report: dict[str, dict[str, object]] = {}
    for bundle_name, spec in TOOL_BUNDLES.items():
        tools = [_canonical_tool(tool) for tool in spec["tools"]]
        tool_set = set(tools)
        name_filters = spec.get("sim_name_contains") or []
        if isinstance(name_filters, str):
            name_filters = [name_filters]
        deep_threshold = max(3, (2 * len(tools) + 2) // 3)
        witnesses: list[dict[str, object]] = []
        full_bundle_witness_count = 0
        deep_bundle_witness_count = 0

        for row in sim_rows:
            sim_name = str(row["sim"])
            if name_filters and not any(token in sim_name for token in name_filters):
                continue
            imported_overlap = sorted(tool_set & set(row["imported_tools"]))
            if not imported_overlap:
                continue
            manifest_overlap = sorted(tool_set & set(row["manifest_tools"]))
            depth_overlap = sorted(tool_set & set(row["depth_tools"]))
            load_bearing_overlap = sorted(tool_set & set(row["load_bearing_tools"]))
            missing_tools = sorted(tool_set - set(row["imported_tools"]))
            header_complete = tool_set.issubset(set(row["imported_tools"])) and tool_set.issubset(set(row["manifest_tools"])) and tool_set.issubset(set(row["depth_tools"]))
            deep_witness = (
                len(imported_overlap) >= deep_threshold
                and len(manifest_overlap) >= deep_threshold
                and len(depth_overlap) >= deep_threshold
            )
            if header_complete:
                full_bundle_witness_count += 1
            if deep_witness:
                deep_bundle_witness_count += 1
            witnesses.append({
                "sim": row["sim"],
                "imported_overlap_count": len(imported_overlap),
                "header_declared_overlap_count": min(len(manifest_overlap), len(depth_overlap)),
                "load_bearing_overlap_count": len(load_bearing_overlap),
                "missing_tools": missing_tools,
                "header_complete": header_complete,
                "deep_witness": deep_witness,
            })

        witnesses.sort(
            key=lambda row: (
                -int(row["imported_overlap_count"]),
                -int(row["header_declared_overlap_count"]),
                -int(row["load_bearing_overlap_count"]),
                len(row["missing_tools"]),
                str(row["sim"]),
            )
        )

        capability_gap_tools = [
            tool for tool in tools
            if per_tool_report.get(tool, {}).get("status") != "passing"
        ]
        weak_tools = [
            tool for tool in tools
            if int(per_tool_report.get(tool, {}).get("imported_in_sims", 0)) == 0
        ]
        load_bearing_gap_tools = [
            tool for tool in tools
            if int(per_tool_report.get(tool, {}).get("load_bearing_witnesses", 0)) == 0
        ]
        recommendation = (
            "repair_capability_first"
            if capability_gap_tools
            else "add_reference_sim"
            if full_bundle_witness_count == 0
            else "expand_existing_bundle"
        )
        bundle_report[bundle_name] = {
            "goal": spec["goal"],
            "tools": tools,
            "capability_gap_tools": capability_gap_tools,
            "weak_tools": weak_tools,
            "load_bearing_gap_tools": load_bearing_gap_tools,
            "deep_threshold": deep_threshold,
            "full_bundle_witness_count": full_bundle_witness_count,
            "deep_bundle_witness_count": deep_bundle_witness_count,
            "needs_reference_sim": full_bundle_witness_count == 0,
            "recommendation": recommendation,
            "best_existing_witnesses": witnesses[:limit],
        }

    return {
        "audited_sims_with_tool_imports": audited,
        "parse_failures": parse_failures,
        "missing_manifest_by_tool": dict(missing_manifest),
        "missing_depth_by_tool": dict(missing_depth),
        "per_tool": per_tool_report,
        "max_stack_sims": relationship_surface["max_stack_sims"],
        "greedy_declared_cover": relationship_surface["greedy_declared_cover"],
        "per_tool_best_companions": relationship_surface["per_tool_best_companions"],
        "bundles": bundle_report,
        "samples": samples,
    }


def classical_surface(limit: int = 12) -> dict:
    classical_paths = [
        path for path in sorted(PROBES.glob("sim_*.py"))
        if " 2" not in path.name and _module_classification(path) == "classical_baseline"
    ]
    state_counts: Counter[str] = Counter()
    fail_families: Counter[str] = Counter()
    unknown_families: Counter[str] = Counter()
    no_result_families: Counter[str] = Counter()
    stale_families: Counter[str] = Counter()
    missing_manifest: Counter[str] = Counter()
    missing_depth: Counter[str] = Counter()
    lint_counts: Counter[str] = Counter()
    lint_samples: defaultdict[str, list[str]] = defaultdict(list)
    lint_rule_sets: dict[str, set[str]] = {}
    result_samples: defaultdict[str, list[str]] = defaultdict(list)
    tool_samples: list[dict[str, object]] = []
    sim_rows: list[dict[str, object]] = []
    result_repair_queue: defaultdict[str, list[dict[str, object]]] = defaultdict(list)
    per_tool: defaultdict[str, dict[str, object]] = defaultdict(
        lambda: {
            "imported_in_sims": 0,
            "missing_manifest": 0,
            "missing_depth": 0,
            "load_bearing_witnesses": 0,
            "supportive_witnesses": 0,
            "decorative_witnesses": 0,
            "header_declared_without_depth": 0,
            "sample_witnesses": [],
        }
    )

    old_lint_repo = lint_sim_contract.REPO
    old_lint_probes = lint_sim_contract.PROBES_DIR
    old_lint_results = lint_sim_contract.RESULTS_DIR
    lint_sim_contract.REPO = REPO
    lint_sim_contract.PROBES_DIR = PROBES
    lint_sim_contract.RESULTS_DIR = _results_dir()
    try:
        for path in classical_paths:
            result_path = _first_result_for_probe(path)
            if result_path is None:
                state_counts["no_result"] += 1
                no_result_families[_result_family(path)] += 1
                if len(result_samples["no_result"]) < limit:
                    result_samples["no_result"].append(path.name)
                if len(result_repair_queue["no_result"]) < limit:
                    result_repair_queue["no_result"].append({
                        "sim": path.name,
                        "family": _result_family(path),
                    })
            else:
                try:
                    data = json.loads(result_path.read_text(encoding="utf-8"))
                except Exception:
                    data = None
                state = _pass_state(data)
                state_counts[state] += 1
                if state == "fail":
                    fail_families[_result_family(path)] += 1
                    if len(result_samples["fail"]) < limit:
                        result_samples["fail"].append(path.name)
                elif state == "unknown":
                    unknown_families[_result_family(path)] += 1
                    if len(result_samples["unknown"]) < limit:
                        result_samples["unknown"].append(path.name)
                    if len(result_repair_queue["unknown"]) < limit:
                        result_repair_queue["unknown"].append({
                            "sim": path.name,
                            "result": _rel_or_abs(result_path),
                            "family": _result_family(path),
                        })
                try:
                    if path.stat().st_mtime > result_path.stat().st_mtime:
                        state_counts["stale_source_newer"] += 1
                        stale_families[_result_family(path)] += 1
                        if len(result_samples["stale_source_newer"]) < limit:
                            result_samples["stale_source_newer"].append(path.name)
                        if len(result_repair_queue["stale_source_newer"]) < limit:
                            result_repair_queue["stale_source_newer"].append({
                                "sim": path.name,
                                "result": _rel_or_abs(result_path),
                                "family": _result_family(path),
                            })
                except OSError:
                    pass

            violations = lint_sim_contract.lint_sim(path)
            if not violations:
                lint_counts["clean"] += 1
            else:
                lint_counts["violating_sims"] += 1
                seen_rules: set[str] = set()
                for violation in violations:
                    rule = str(violation.get("rule"))
                    lint_counts[rule] += 1
                    if rule not in seen_rules and len(lint_samples[rule]) < limit:
                        lint_samples[rule].append(path.name)
                    seen_rules.add(rule)
                lint_rule_sets[path.name] = seen_rules

            imported_tools, parsed = _imported_tools(path)
            if not parsed or not imported_tools:
                continue
            for tool in imported_tools:
                per_tool[tool]["imported_in_sims"] = int(per_tool[tool]["imported_in_sims"]) + 1
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            manifest_tools = _module_dict_keys(tree, "TOOL_MANIFEST")
            depth = _module_depth_map(tree, "TOOL_INTEGRATION_DEPTH", manifest_tools)
            manifest = {tool: True for tool in manifest_tools} if manifest_tools else None
            depth_tools = set(depth) if isinstance(depth, dict) else set()
            load_bearing_tools = (
                {
                    _canonical_tool(str(raw_tool))
                    for raw_tool, level in depth.items()
                    if level == "load_bearing"
                }
                if isinstance(depth, dict)
                else set()
            )
            declared_tools = (
                set(imported_tools)
                & {_canonical_tool(str(tool)) for tool in manifest_tools}
                & {_canonical_tool(str(tool)) for tool in depth_tools}
            )
            sim_rows.append({
                "sim": path.name,
                "imported_tools": set(imported_tools),
                "manifest_tools": {_canonical_tool(str(tool)) for tool in manifest_tools},
                "depth_tools": {_canonical_tool(str(tool)) for tool in depth_tools},
                "declared_tools": declared_tools,
                "load_bearing_tools": load_bearing_tools,
            })
            if isinstance(depth, dict):
                for raw_tool, level in depth.items():
                    tool = _canonical_tool(str(raw_tool))
                    row = per_tool[tool]
                    if level == "load_bearing":
                        row["load_bearing_witnesses"] = int(row["load_bearing_witnesses"]) + 1
                    elif level == "supportive":
                        row["supportive_witnesses"] = int(row["supportive_witnesses"]) + 1
                    elif level == "decorative":
                        row["decorative_witnesses"] = int(row["decorative_witnesses"]) + 1
                    elif tool in imported_tools:
                        row["header_declared_without_depth"] = int(row["header_declared_without_depth"]) + 1
                    if (
                        level in {"load_bearing", "supportive", "decorative"}
                        and len(row["sample_witnesses"]) < 5
                    ):
                        row["sample_witnesses"].append(path.name)
            missing_manifest_tools = sorted(
                tool for tool in imported_tools
                if not isinstance(manifest, dict) or tool not in manifest
            )
            missing_depth_tools = sorted(
                tool for tool in imported_tools
                if not isinstance(depth, dict) or tool not in depth
            )
            for tool in missing_manifest_tools:
                missing_manifest[tool] += 1
                per_tool[tool]["missing_manifest"] = int(per_tool[tool]["missing_manifest"]) + 1
            for tool in missing_depth_tools:
                missing_depth[tool] += 1
                per_tool[tool]["missing_depth"] = int(per_tool[tool]["missing_depth"]) + 1
            if (missing_manifest_tools or missing_depth_tools) and len(tool_samples) < limit:
                tool_samples.append({
                    "sim": path.name,
                    "imported_tools": sorted(imported_tools),
                    "missing_manifest_tools": missing_manifest_tools,
                    "missing_depth_tools": missing_depth_tools,
                })
    finally:
        lint_sim_contract.REPO = old_lint_repo
        lint_sim_contract.PROBES_DIR = old_lint_probes
        lint_sim_contract.RESULTS_DIR = old_lint_results

    all_tools = sorted(set(per_tool))
    per_tool_report: dict[str, dict[str, object]] = {}
    for tool in all_tools:
        row = dict(per_tool[tool])
        row.update(_capability_probe_status(tool))
        per_tool_report[tool] = row
    relationship_surface = _integration_relationship_surface(sim_rows, all_tools, limit)
    manifest_rules = {"C2_manifest_missing", "C2_manifest_malformed"}
    depth_rules = {"C3_depth_missing", "C3_depth_malformed", "C3_depth_invalid_value"}
    divergence_rules = {"C4_divergence_log_missing", "C4_divergence_log_empty"}
    contract_priority_buckets: defaultdict[str, list[str]] = defaultdict(list)
    for sim, rules in lint_rule_sets.items():
        if rules & manifest_rules and rules & depth_rules and rules & divergence_rules:
            bucket = "three_rule_header_backfill"
        elif "C6_classical_has_load_bearing" in rules:
            bucket = "classical_load_bearing_leakage"
        elif rules & manifest_rules or rules & depth_rules:
            bucket = "manifest_depth_normalization"
        elif rules & divergence_rules:
            bucket = "divergence_log_backfill"
        else:
            bucket = "other_contract_debt"
        contract_priority_buckets[bucket].append(sim)
    return {
        "count": len(classical_paths),
        "result_states": dict(state_counts),
        "fail_families": dict(fail_families.most_common(10)),
        "unknown_families": dict(unknown_families.most_common(10)),
        "no_result_families": dict(no_result_families.most_common(10)),
        "stale_families": dict(stale_families.most_common(10)),
        "lint": {
            "counts": dict(lint_counts),
            "samples": dict(lint_samples),
        },
        "tool_integration": {
            "missing_manifest_by_tool": dict(missing_manifest),
            "missing_depth_by_tool": dict(missing_depth),
            "per_tool": per_tool_report,
            "max_stack_sims": relationship_surface["max_stack_sims"],
            "greedy_declared_cover": relationship_surface["greedy_declared_cover"],
            "per_tool_best_companions": relationship_surface["per_tool_best_companions"],
            "samples": tool_samples,
        },
        "repair_queues": {
            "results": {
                key: {
                    "count": len(entries),
                    "samples": entries,
                }
                for key, entries in result_repair_queue.items()
            },
            "contract": {
                key: {
                    "count": len(entries),
                    "samples": entries[:limit],
                }
                for key, entries in contract_priority_buckets.items()
            },
        },
        "samples": dict(result_samples),
    }


def _pass_state(data: object) -> str:
    if not isinstance(data, dict):
        return "non_dict_json"
    value = adaptive_controller.is_passing(data)
    if value is True:
        return "pass"
    if value is False:
        return "fail"
    if _looks_like_legacy_pass(data):
        return "pass_inferred"
    return "unknown"


def _boolish(value: object) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered == "true":
            return True
        if lowered == "false":
            return False
    return None


def _all_check_flags_pass(section: object) -> bool | None:
    saw_flag = False
    failed = False
    if isinstance(section, dict):
        for key, value in section.items():
            if key in {"pass", "passed", "ok"}:
                flag = _boolish(value)
                if flag is None:
                    continue
                saw_flag = True
                if not flag:
                    failed = True
            else:
                nested = _all_check_flags_pass(value)
                if nested is True:
                    saw_flag = True
                elif nested is False:
                    saw_flag = True
                    failed = True
    elif isinstance(section, list):
        for value in section:
            nested = _all_check_flags_pass(value)
            if nested is True:
                saw_flag = True
            elif nested is False:
                saw_flag = True
                failed = True
    if not saw_flag:
        return None
    return not failed


def _summary_counts_all_pass(summary: dict) -> bool:
    passed = summary.get("passed")
    total = summary.get("total")
    if isinstance(passed, int) and isinstance(total, int) and total > 0:
        return passed == total
    for value in summary.values():
        if isinstance(value, str) and "/" in value:
            left, _, right = value.partition("/")
            try:
                if int(left) != int(right):
                    return False
            except ValueError:
                continue
    return any(isinstance(value, str) and "/" in value for value in summary.values())


def _looks_like_legacy_pass(data: dict) -> bool:
    if isinstance(data.get("evidence_ledger"), list) and data["evidence_ledger"]:
        statuses = [str(item.get("status", "")).upper() for item in data["evidence_ledger"] if isinstance(item, dict)]
        if statuses and all(status == "PASS" for status in statuses):
            return True
    if data.get("ALL_PASS") is True:
        return True
    if isinstance(data.get("summary"), dict) and _summary_counts_all_pass(data["summary"]):
        return True
    if isinstance(data.get("summary"), dict) and adaptive_controller._summary_bools_all_true(data["summary"]):
        return True
    if adaptive_controller._nested_statuses_all_ok(data):
        return True
    section_votes = []
    for key in ("positive", "negative", "boundary", "results"):
        if key in data:
            vote = _all_check_flags_pass(data[key])
            if vote is not None:
                section_votes.append(vote)
    return bool(section_votes) and all(section_votes)


def _section_flag_counts(section: object) -> tuple[int, int]:
    total = 0
    failed = 0

    def walk(value: object) -> None:
        nonlocal total, failed
        if isinstance(value, dict):
            for key, nested in value.items():
                if key in {"pass", "passed", "ok"}:
                    flag = _boolish(nested)
                    if flag is None:
                        continue
                    total += 1
                    if not flag:
                        failed += 1
                else:
                    walk(nested)
            return
        if isinstance(value, list):
            for nested in value:
                walk(nested)

    walk(section)
    return total, failed


def _result_fail_mode(data: object) -> str | None:
    if not isinstance(data, dict):
        return None
    if _pass_state(data) != "fail":
        return None
    if data.get("error") or data.get("failure_reason"):
        return "explicit_error"
    if isinstance(data.get("summary"), dict):
        summary = data["summary"]
        tests_failed = summary.get("tests_failed")
        if isinstance(tests_failed, int) and tests_failed > 0:
            return "tests_failed"
        passed = summary.get("passed")
        total = summary.get("total")
        if isinstance(passed, int) and isinstance(total, int) and passed < total:
            return "partial_pass"
        for key in ("all_pass", "all_passed"):
            verdict = _boolish(summary.get(key))
            if verdict is False:
                return "summary_gate_false"
    top_all_pass = _boolish(data.get("all_pass"))
    if top_all_pass is False:
        return "top_level_gate_false"
    total_flags = 0
    failed_flags = 0
    for key in ("positive", "negative", "boundary", "results"):
        section_total, section_failed = _section_flag_counts(data.get(key))
        total_flags += section_total
        failed_flags += section_failed
    if total_flags and failed_flags:
        return "section_check_failed"
    return "unclassified_fail"


def _result_family(path: Path) -> str:
    stem = path.name
    if stem.endswith("_results.json"):
        stem = stem[:-13]
    elif stem.endswith(".json"):
        stem = stem[:-5]
    if stem.startswith("sim_"):
        stem = stem[4:]
    return stem.split("_", 1)[0] if "_" in stem else stem


def _dirty_probe_source_paths() -> tuple[set[str], set[str]]:
    dirty: set[str] = set()
    untracked: set[str] = set()
    for entry in _git_status_entries():
        path = entry["path"]
        if _git_layer(path) != "probe_sources":
            continue
        dirty.add(path)
        if entry["status"] == "??":
            untracked.add(path)
    return dirty, untracked


def _source_state_for_result(
    root: Path,
    result_path: Path,
    dirty_probe_sources: set[str],
    untracked_probe_sources: set[str],
) -> dict[str, object] | None:
    if root == REPO / "system_v4/a2_state/sim_results":
        return None
    if not result_path.name.endswith("_results.json"):
        return None
    stem = result_path.name[:-13]
    candidates = [PROBES / f"{stem}.py"]
    if not stem.startswith("sim_"):
        candidates.append(PROBES / f"sim_{stem}.py")
    source = next((candidate for candidate in candidates if _exists_safe(candidate)), candidates[0])
    rel_source = str(source.relative_to(REPO))
    state = {
        "source_path": rel_source,
        "source_exists": _exists_safe(source),
        "source_canonical_name": source.name.startswith("sim_"),
        "source_dirty": rel_source in dirty_probe_sources,
        "source_untracked": rel_source in untracked_probe_sources,
        "source_newer_than_result": False,
        "result_newer_than_source": False,
    }
    if _exists_safe(source):
        try:
            source_mtime = source.stat().st_mtime
            result_mtime = result_path.stat().st_mtime
            if source_mtime > result_mtime:
                state["source_newer_than_result"] = True
            elif result_mtime > source_mtime:
                state["result_newer_than_source"] = True
        except OSError:
            pass
    return state


def _source_state_label(state: dict[str, object] | None) -> str | None:
    if state is None:
        return None
    if state["source_untracked"]:
        prefix = "source_untracked"
    elif state["source_dirty"]:
        prefix = "source_dirty"
    elif not state["source_exists"]:
        prefix = "source_missing"
    else:
        prefix = "source_clean"
    if state["source_exists"]:
        if state["source_newer_than_result"]:
            return f"{prefix}_source_newer"
        if state["result_newer_than_source"]:
            return f"{prefix}_result_newer"
    return prefix


def _fail_action_bucket(
    fail_mode: str | None,
    source_state: dict[str, object] | None,
) -> str | None:
    if source_state is None:
        return None
    if not source_state["source_exists"]:
        return "missing_source_repair"
    if not source_state["source_canonical_name"]:
        return "noncanonical_source_repair"
    if source_state["source_untracked"] or source_state["source_dirty"]:
        return "source_drift_review"
    if source_state["source_newer_than_result"]:
        return "rerun_candidate"
    if source_state["result_newer_than_source"]:
        if fail_mode == "summary_gate_false":
            return "current_fail_review"
        return "current_fail_review"
    return "fail_review"


def result_surface() -> dict:
    dirty_probe_sources, untracked_probe_sources = _dirty_probe_source_paths()
    roots = {}
    for root in RESULT_ROOTS:
        files = list(root.glob("*.json")) if root.exists() else []
        status_counts: Counter[str] = Counter()
        schema_counts: Counter[str] = Counter()
        fail_families: Counter[str] = Counter()
        fail_modes: Counter[str] = Counter()
        fail_source_states: Counter[str] = Counter()
        fail_actions: Counter[str] = Counter()
        unknown_families: Counter[str] = Counter()
        dirty_source_results = 0
        untracked_source_results = 0
        orphan_like = 0
        samples: defaultdict[str, list[str]] = defaultdict(list)
        fail_details: list[dict[str, object]] = []
        for path in files:
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                data = None
            pass_state = _pass_state(data)
            source_state = _source_state_for_result(root, path, dirty_probe_sources, untracked_probe_sources)
            status_counts[pass_state] += 1
            if pass_state == "fail" and len(samples["fail"]) < 8:
                samples["fail"].append(path.name)
                fail_families[_result_family(path)] += 1
            elif pass_state == "fail":
                fail_families[_result_family(path)] += 1
            elif pass_state == "unknown":
                unknown_families[_result_family(path)] += 1
            fail_mode = _result_fail_mode(data)
            if fail_mode:
                fail_modes[fail_mode] += 1
            source_label = _source_state_label(source_state)
            if pass_state == "fail" and source_label:
                fail_source_states[source_label] += 1
                action = _fail_action_bucket(fail_mode, source_state)
                if action:
                    fail_actions[action] += 1
                if len(fail_details) < 8:
                    fail_details.append({
                        "result": path.name,
                        "source": source_state["source_path"],
                        "fail_mode": fail_mode,
                        "source_state": source_label,
                        "action": action,
                    })
            if isinstance(data, dict):
                if "overall_pass" in data:
                    schema_counts["overall_pass"] += 1
                elif "passed" in data:
                    schema_counts["passed_only"] += 1
                elif "all_pass" in data:
                    schema_counts["all_pass"] += 1
                elif "ALL_PASS" in data:
                    schema_counts["ALL_PASS"] += 1
                elif isinstance(data.get("summary"), dict) and "all_pass" in data["summary"]:
                    schema_counts["summary_all_pass"] += 1
                elif isinstance(data.get("summary"), dict) and "all_passed" in data["summary"]:
                    schema_counts["summary_all_passed"] += 1
                elif isinstance(data.get("summary"), dict) and adaptive_controller._summary_bools_all_true(data["summary"]):
                    schema_counts["summary_bool_inferred"] += 1
                elif adaptive_controller._nested_statuses_all_ok(data):
                    schema_counts["nested_status_inferred"] += 1
                elif _looks_like_legacy_pass(data):
                    schema_counts["legacy_pass_inferred"] += 1
                else:
                    schema_counts["no_pass_key"] += 1
                    if len(samples["no_pass_key"]) < 8:
                        samples["no_pass_key"].append(path.name)
            else:
                schema_counts["non_dict_json"] += 1
                if len(samples["non_dict_json"]) < 8:
                    samples["non_dict_json"].append(path.name)
            if source_state is not None:
                rel_source = str(source_state["source_path"])
                if rel_source in dirty_probe_sources:
                    dirty_source_results += 1
                    if len(samples["dirty_source_results"]) < 8:
                        samples["dirty_source_results"].append(path.name)
                if rel_source in untracked_probe_sources:
                    untracked_source_results += 1
                    if len(samples["untracked_source_results"]) < 8:
                        samples["untracked_source_results"].append(path.name)
                if not source_state["source_exists"]:
                    orphan_like += 1
                    if len(samples["orphan_like"]) < 8:
                        samples["orphan_like"].append(path.name)
        roots[str(root.relative_to(REPO))] = {
            "count": len(files),
            "status": dict(status_counts),
            "schema": dict(schema_counts),
            "fail_families": dict(fail_families.most_common(10)),
            "fail_modes": dict(fail_modes.most_common(10)),
            "fail_source_states": dict(fail_source_states.most_common(10)),
            "fail_actions": dict(fail_actions.most_common(10)),
            "unknown_families": dict(unknown_families.most_common(10)),
            "dirty_source_results": dirty_source_results,
            "untracked_source_results": untracked_source_results,
            "orphan_like": orphan_like,
            "fail_details": fail_details,
            "samples": dict(samples),
        }
    return roots


def _runner_health(queue_counts: dict, freshness: dict, claimed_age: dict | None = None) -> dict:
    claimed = int(queue_counts.get("claimed", 0) or 0)
    done_fresh = freshness.get("done", {}).get("active_within_60s") is True
    claimed_fresh = freshness.get("claimed", {}).get("active_within_60s") is True
    lane_b_fresh = freshness.get("lane_B", {}).get("active_within_60s") is True
    backlog = int(queue_counts.get("lane_A", 0) or 0) + int(queue_counts.get("lane_B", 0) or 0)
    long_claims = int((claimed_age or {}).get("over_900s", 0) or 0)
    if claimed > 0 and done_fresh and long_claims > 0:
        return {"status": "draining_with_long_claims", "reason": "done surface is fresh but some claims exceed 15 minutes"}
    if claimed > 0 and not done_fresh and long_claims > 0:
        return {"status": "possibly_stuck", "reason": "claims exceed 15 minutes and done surface is stale"}
    if claimed > 0 and done_fresh:
        return {"status": "draining", "reason": "claimed and done surfaces are both fresh"}
    if claimed > 0 and not done_fresh:
        return {"status": "possibly_stuck", "reason": "claims exist but done surface is stale"}
    if claimed == 0 and backlog > 0 and lane_b_fresh:
        return {"status": "feeding", "reason": "queue is active but workers are between claims"}
    if claimed == 0 and backlog > 0:
        return {"status": "idle_with_backlog", "reason": "backlog exists without fresh claim/done movement"}
    return {"status": "idle", "reason": "no active claims and no material backlog"}


def _runner_warnings(
    queue_counts: dict,
    freshness: dict,
    claimed_age: dict | None = None,
    blocked: dict | None = None,
) -> list[str]:
    warnings: list[str] = []
    claimed = int(queue_counts.get("claimed", 0) or 0)
    blocked_state = blocked or {}
    duplicate_entries = int(blocked_state.get("duplicate_entries", 0) or 0)
    if duplicate_entries > 0:
        active_count = int(blocked_state.get("active_count", 0) or 0)
        unique_sims = int(blocked_state.get("unique_sims", 0) or 0)
        warnings.append(
            f"{active_count} blocked entry(s) across {unique_sims} unique sim(s)"
        )
    if claimed <= 0:
        return warnings
    ages = claimed_age or {}
    over_900 = int(ages.get("over_900s", 0) or 0)
    over_300 = int(ages.get("over_300s", 0) or 0)
    if over_900:
        warnings.append(f"{over_900} claim(s) over 900s")
    elif over_300:
        warnings.append(f"{over_300} claim(s) over 300s")
    if freshness.get("done", {}).get("active_within_60s") is not True:
        warnings.append("done surface not fresh within 60s")
    return warnings


def runner_surface() -> dict:
    queue_counts = adaptive_controller.queue_counts()
    freshness = {
        lane: _queue_dir_freshness(adaptive_controller.QUEUE / lane)
        for lane in ("lane_A", "lane_B", "claimed", "done")
    }
    claimed_age = _claimed_age_surface(adaptive_controller.QUEUE / "claimed")
    blocked = _blocked_surface()
    return {
        "pidfiles": {name: _pidfile_status(name, pidfile) for name, pidfile in PIDFILES.items()},
        "wrappers": _wrapper_processes(),
        "queue": queue_counts,
        "freshness": freshness,
        "claimed_age": claimed_age,
        "blocked": blocked,
        "health": _runner_health(queue_counts, freshness, claimed_age),
        "warnings": _runner_warnings(queue_counts, freshness, claimed_age, blocked),
        "claimed": _queue_claim_summary(),
    }


def program_surface() -> dict:
    state = adaptive_controller.triage_cycle(dry=True)
    integration = adaptive_controller.build_integration_summary(state)
    snapshot = adaptive_controller.build_plane_snapshot(state, integration)
    return {
        "triage": snapshot["state_plane"]["triage"],
        "queue_duplicates": sim_program_audit.queue_duplicate_summary(),
        "queue_noncanonical_names": sim_program_audit.queue_noncanonical_summary(),
        "queue_claimed_overlaps": sim_program_audit.queue_claimed_overlap_summary(),
        "next_queue_candidates": {
            "lane_A": sim_program_audit.next_queue_candidates("lane_A", limit=6),
            "lane_B": sim_program_audit.next_queue_candidates("lane_B", limit=6),
        },
        "never_run_families": snapshot["state_plane"]["program"]["never_run_families"],
        "never_run_buckets": snapshot["state_plane"]["program"]["never_run_buckets"],
        "never_run_stages": snapshot["state_plane"]["program"]["never_run_stages"],
    }


def _git_maintenance_queue(git: dict) -> dict:
    cleanup_posture = git.get("cleanup_posture", {})
    layers = git.get("layers", {})
    blocked_layers = {
        key: value
        for key, value in layers.items()
        if cleanup_posture.get(key) == "BLOCKED_REQUIRES_PREP"
    }
    active_layers = {
        key: value
        for key, value in layers.items()
        if cleanup_posture.get(key) == "KEEP_ACTIVE"
    }
    repair_layers = {
        key: value
        for key, value in layers.items()
        if cleanup_posture.get(key) == "REPAIR_TO_CANONICAL_ROOT"
    }
    return {
        "blocked_entries": sum(blocked_layers.values()),
        "blocked_layers": blocked_layers,
        "repair_entries": sum(repair_layers.values()),
        "repair_layers": repair_layers,
        "active_churn_entries": sum(active_layers.values()),
        "active_churn_layers": active_layers,
    }


def _results_maintenance_queue(results: dict) -> dict:
    main = results.get("system_v4/probes/a2_state/sim_results", {})
    grouped: defaultdict[str, list[dict]] = defaultdict(list)
    for row in main.get("fail_details", []):
        action = str(row.get("action", "unclassified"))
        if len(grouped[action]) < 5:
            grouped[action].append(row)
    return {
        "fail_actions": dict(main.get("fail_actions", {})),
        "fail_action_samples": dict(grouped),
        "dirty_source_results": int(main.get("dirty_source_results", 0) or 0),
        "untracked_source_results": int(main.get("untracked_source_results", 0) or 0),
    }


def _classical_maintenance_queue(classical: dict) -> dict:
    lint = classical.get("lint", {})
    tool_integration = classical.get("tool_integration", {})
    samples = classical.get("samples", {})
    result_states = classical.get("result_states", {})
    return {
        "count": int(classical.get("count", 0) or 0),
        "result_states": dict(result_states),
        "freshness_queue": {
            "count": int(result_states.get("stale_source_newer", 0) or 0),
            "families": dict(classical.get("stale_families", {})),
            "samples": list(samples.get("stale_source_newer", []))[:5],
        },
        "no_result_queue": {
            "count": int(result_states.get("no_result", 0) or 0),
            "families": dict(classical.get("no_result_families", {})),
            "samples": list(samples.get("no_result", []))[:5],
        },
        "unknown_queue": {
            "count": int(result_states.get("unknown", 0) or 0),
            "families": dict(classical.get("unknown_families", {})),
            "samples": list(samples.get("unknown", []))[:5],
        },
        "lint_counts": dict(lint.get("counts", {})),
        "contract_queue": {
            "violating_sims": int(lint.get("counts", {}).get("violating_sims", 0) or 0),
            "top_rules": {
                key: int(value)
                for key, value in lint.get("counts", {}).items()
                if key not in {"clean", "violating_sims"}
            },
            "samples": dict(lint.get("samples", {})),
        },
        "top_tool_manifest_gaps": dict(Counter(tool_integration.get("missing_manifest_by_tool", {})).most_common(10)),
        "top_tool_depth_gaps": dict(Counter(tool_integration.get("missing_depth_by_tool", {})).most_common(10)),
        "tool_queue": {
            "top_anchor_sims": list(tool_integration.get("max_stack_sims", []))[:5],
            "cover": dict(tool_integration.get("greedy_declared_cover", {})),
        },
    }


def maintenance_queue_surface(git: dict, runner: dict, results: dict, classical: dict | None = None) -> dict:
    return {
        "git": _git_maintenance_queue(git),
        "runner": {
            "status": runner.get("health", {}).get("status"),
            "warnings": list(runner.get("warnings", [])),
            "claimed_age": dict(runner.get("claimed_age", {})),
            "blocked": {
                "active_count": int(runner.get("blocked", {}).get("active_count", 0) or 0),
                "reasons": dict(runner.get("blocked", {}).get("reasons", {})),
                "unique_sims": int(runner.get("blocked", {}).get("unique_sims", 0) or 0),
                "duplicate_entries": int(runner.get("blocked", {}).get("duplicate_entries", 0) or 0),
                "samples": list(runner.get("blocked", {}).get("samples", [])),
            },
        },
        "results": _results_maintenance_queue(results),
        "classical": _classical_maintenance_queue(classical or {}),
    }


def main() -> int:
    git = git_surface()
    runner = runner_surface()
    results = result_surface()
    classical = classical_surface()
    report = {
        "git": git,
        "runner": runner,
        "program": program_surface(),
        "tool_integration": tool_integration_surface(),
        "results": results,
        "classical": classical,
        "maintenance_queue": maintenance_queue_surface(git, runner, results, classical),
    }
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
