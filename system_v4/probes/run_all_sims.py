#!/usr/bin/env python3
"""
Unified SIM Runner — Codex Ratchet Evidence Engine
====================================================
Runs ALL SIM files, collects evidence tokens, builds
the consolidated evidence graph, and produces the
system status report.

This IS the autopoietic heartbeat loop: 
  Run SIMs → Collect tokens → Build graph → Report status
"""

import subprocess
import json
import os
import sys
from datetime import datetime, UTC
from pathlib import Path

PROBES_DIR = Path(__file__).parent
RESULTS_DIR = PROBES_DIR / "a2_state" / "sim_results"

SIM_FILES = [
    "foundations_sim.py",
    "math_foundations_sim.py",
    "deep_math_foundations_sim.py",
    "arithmetic_gravity_sim.py",
    "proof_cost_sim.py",
    "navier_stokes_complexity_sim.py",
    "complexity_gap_sim.py",
    "topology_operator_sim.py",
    "igt_game_theory_sim.py",
    "engine_terrain_sim.py",
    "igt_advanced_sim.py",
    "godel_stall_sim.py",
    "dual_weyl_spinor_engine_sim.py",
    "full_8stage_engine_sim.py",
    "rock_falsifier_sim.py",
    "constraint_gap_sim.py",
    "szilard_64stage_sim.py",
    "nlm_batch2_sim.py",
    # Pro Thread Dispatch SIMs
    "gain_calibration_sim.py",
    "demon_fixed_sim.py",
    "type2_engine_sim.py",
    "riemann_zeta_sim.py",
    "p_vs_np_sim.py",
    "navier_stokes_qit_sim.py",
    "consciousness_sim.py",
    "alignment_sim.py",
    "abiogenesis_sim.py",
    "quantum_gravity_sim.py",
    "yang_mills_sim.py",
    "scale_testing_sim.py",
    "chemistry_sim.py",
    "world_model_sim.py",
    "scientific_method_sim.py",
    "navier_stokes_formal_sim.py",
    "rock_falsifier_enhanced_sim.py",
]


def run_sim(filename: str) -> dict:
    """Run a single SIM file and capture its output."""
    filepath = PROBES_DIR / filename
    if not filepath.exists():
        return {"file": filename, "status": "MISSING", "tokens": []}
    
    try:
        result = subprocess.run(
            [sys.executable, str(filepath)],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=str(PROBES_DIR)
        )
        
        # Try to find the results JSON
        result_files = {
            "foundations_sim.py": "foundations_results.json",
            "math_foundations_sim.py": "math_foundations_results.json",
            "deep_math_foundations_sim.py": "deep_math_results.json",
            "arithmetic_gravity_sim.py": "arithmetic_gravity_results.json",
            "proof_cost_sim.py": "proof_cost_results.json",
            "navier_stokes_complexity_sim.py": "navier_stokes_results.json",
            "complexity_gap_sim.py": "complexity_gap_results.json",
            "topology_operator_sim.py": "topology_operator_results.json",
            "igt_game_theory_sim.py": "igt_results.json",
            "engine_terrain_sim.py": "engine_terrain_results.json",
            "igt_advanced_sim.py": "igt_advanced_results.json",
            "godel_stall_sim.py": "godel_stall_results.json",
            "dual_weyl_spinor_engine_sim.py": "dual_weyl_results.json",
            "full_8stage_engine_sim.py": "full_8stage_results.json",
            "rock_falsifier_sim.py": "rock_falsifier_results.json",
            "constraint_gap_sim.py": "constraint_gap_results.json",
            "szilard_64stage_sim.py": "szilard_64stage_results.json",
            "nlm_batch2_sim.py": "nlm_batch2_results.json",
            # Pro Thread Dispatch SIMs
            "gain_calibration_sim.py": "gain_calibration_results.json",
            "demon_fixed_sim.py": "demon_fixed_results.json",
            "type2_engine_sim.py": "type2_engine_results.json",
            "riemann_zeta_sim.py": "riemann_zeta_results.json",
            "p_vs_np_sim.py": "p_vs_np_results.json",
            "navier_stokes_qit_sim.py": "navier_stokes_qit_results.json",
            "consciousness_sim.py": "consciousness_results.json",
            "alignment_sim.py": "alignment_results.json",
            "abiogenesis_sim.py": "abiogenesis_results.json",
            "quantum_gravity_sim.py": "quantum_gravity_results.json",
            "yang_mills_sim.py": "yang_mills_results.json",
            "scale_testing_sim.py": "scale_testing_results.json",
            "chemistry_sim.py": "chemistry_results.json",
            "world_model_sim.py": "world_model_results.json",
            "scientific_method_sim.py": "scientific_method_results.json",
            "navier_stokes_formal_sim.py": "navier_stokes_formal_results.json",
            "rock_falsifier_enhanced_sim.py": "rock_falsifier_enhanced_results.json",
        }
        
        tokens = []
        rfile = result_files.get(filename)
        if rfile:
            rpath = RESULTS_DIR / rfile
            if rpath.exists():
                with open(rpath) as f:
                    data = json.load(f)
                    tokens = data.get("evidence_ledger", [])
        
        status = "PASS" if result.returncode == 0 else "FAIL"
        
        # Evidence-level health: does the SIM have any KILL tokens?
        # This is distinct from process status (exit code).
        # A SIM can exit 0 (ran successfully) but emit KILL tokens.
        n_kills = sum(1 for t in tokens if t.get("status") == "KILL")
        n_pass = sum(1 for t in tokens if t.get("status") == "PASS")
        evidence_status = "ALL_PASS" if n_kills == 0 and n_pass > 0 else (
            "KILL_PRESENT" if n_kills > 0 else "NO_TOKENS"
        )
        
        return {
            "file": filename,
            "status": status,           # process-level (exit code)
            "evidence_status": evidence_status,  # token-level health
            "tokens": tokens,
            "pass_count": n_pass,
            "kill_count": n_kills,
            "returncode": result.returncode,
            "stderr": result.stderr[-200:] if result.stderr else "",
        }
    
    except subprocess.TimeoutExpired:
        return {"file": filename, "status": "TIMEOUT", "evidence_status": "NO_TOKENS",
                "tokens": [], "pass_count": 0, "kill_count": 0}
    except Exception as e:
        return {"file": filename, "status": f"ERROR: {e}", "evidence_status": "NO_TOKENS",
                "tokens": [], "pass_count": 0, "kill_count": 0}


def build_evidence_graph(all_tokens: list) -> dict:
    """Build the dependency graph from all evidence tokens."""
    # Organize by layer
    layers = {
        0: [],  # Axioms
        1: [],  # Derived constraints
        2: [],  # Arithmetic
        3: [],  # Physics
        4: [],  # Complexity
        5: [],  # Topology/Operators
        6: [],  # IGT
        7: [],  # Engine Terrains
        8: [],  # Theory (advanced IGT)
    }
    
    layer_map = {
        "E_SIM_F01_": 0, "E_SIM_N01_": 0,
        "E_SIM_LANDAUER_": 1, "E_SIM_CPTP_": 1, "E_SIM_NO_CLONE_": 1,
        "E_SIM_COUNTING_": 2, "E_SIM_ADDITION_": 2, "E_SIM_MULTIPLICATION_": 2,
        "E_SIM_PRIMES_": 2, "E_SIM_ZERO_": 2, "E_SIM_NEGATION_": 2,
        "E_SIM_SUBTRACTION_": 2, "E_SIM_DIVISION_": 2, "E_SIM_FRACTIONS_": 2,
        "E_SIM_GROUP_": 2, "E_SIM_NONABELIAN_": 2,
        "E_SIM_GRAVITY_": 3, "E_SIM_ARROW_": 3, "E_SIM_VISCOSITY_": 3,
        "E_SIM_SMOOTHNESS_": 3,
        "E_SIM_P_WITHIN_": 4, "E_SIM_NP_BETWEEN_": 4, "E_SIM_GAP_": 4,
        "E_SIM_CONTINUUM_": 4, "E_SIM_BASIN_": 4, "E_SIM_TURBULENCE_": 4,
        "E_SIM_PROOF_": 4, "E_SIM_GODEL_": 4,
        "E_SIM_TOROIDAL_": 5, "E_SIM_DIVERGENT_": 5, "E_SIM_SINGULAR_": 5,
        "E_SIM_STABLE_": 5, "E_SIM_PROJECTION_": 5, "E_SIM_EXPANSION_": 5,
        "E_SIM_FILTERING_": 5, "E_SIM_DISSIPATION_": 5,
        "E_SIM_IGT_": 6, "E_SIM_CHIRAL_": 7,
        "E_SIM_TYPE1_": 7, "E_SIM_TYPE2_": 7,
        "E_SIM_WIN_": 8, "E_SIM_720_": 8, "E_SIM_MINIMIN_": 8,
        "E_SIM_DUAL_": 8, "E_SIM_IRRATIONAL_": 8,
    }
    
    for token in all_tokens:
        tid = token.get("token_id", "")
        placed = False
        for prefix, layer in layer_map.items():
            if tid.startswith(prefix):
                layers[layer].append(token)
                placed = True
                break
        if not placed and tid:
            layers[8].append(token)
    
    return {
        "layers": {str(k): v for k, v in layers.items()},
        "total_tokens": len(all_tokens),
        "pass_count": sum(1 for t in all_tokens if t.get("status") == "PASS"),
        "kill_count": sum(1 for t in all_tokens if t.get("status") == "KILL"),
    }


def main():
    print(f"{'#'*60}")
    print(f"  CODEX RATCHET — UNIFIED SIM RUNNER")
    print(f"  {datetime.now(UTC).isoformat()}")
    print(f"{'#'*60}")
    
    os.makedirs(RESULTS_DIR, exist_ok=True)
    
    all_results = []
    all_tokens = []
    
    for sim_file in SIM_FILES:
        print(f"\n{'─'*40}")
        print(f"  Running: {sim_file}")
        print(f"{'─'*40}")
        
        result = run_sim(sim_file)
        all_results.append(result)
        # Stamp source_file on each token so downstream consumers
        # (materializer, heartbeat) can link tokens back to their producer
        for t in result["tokens"]:
            t["source_file"] = sim_file
        all_tokens.extend(result["tokens"])
        
        n_pass = sum(1 for t in result["tokens"] if t.get("status") == "PASS")
        n_kill = sum(1 for t in result["tokens"] if t.get("status") == "KILL")
        print(f"  → {result['status']} | {n_pass} PASS | {n_kill} KILL")
    
    # Build evidence graph
    graph = build_evidence_graph(all_tokens)
    
    # Report
    print(f"\n{'#'*60}")
    print(f"  UNIFIED EVIDENCE REPORT")
    print(f"{'#'*60}")
    print(f"  Total tokens: {graph['total_tokens']}")
    print(f"  PASS: {graph['pass_count']}")
    print(f"  KILL: {graph['kill_count']}")
    print(f"\n  By layer:")
    layer_names = {
        "0": "Axioms (F01, N01)",
        "1": "Derived Constraints",
        "2": "Arithmetic",
        "3": "Physics",
        "4": "Complexity",
        "5": "Topology/Operators",
        "6": "IGT",
        "7": "Engine Terrains",
        "8": "Advanced Theory",
    }
    for layer_id, tokens in graph["layers"].items():
        name = layer_names.get(layer_id, f"Layer {layer_id}")
        n_pass = sum(1 for t in tokens if t.get("status") == "PASS")
        n_kill = sum(1 for t in tokens if t.get("status") == "KILL")
        if tokens:
            print(f"    Layer {layer_id} ({name}): {n_pass} PASS, {n_kill} KILL")
    
    # File-level summary
    print(f"\n  By SIM file:")
    sims_with_kills = []
    sims_clean = []
    for r in all_results:
        n = len(r["tokens"])
        p = r.get("pass_count", 0)
        k = r.get("kill_count", 0)
        ev = r.get("evidence_status", "UNKNOWN")
        
        if r["status"] != "PASS":
            icon = "✗"
        elif k > 0:
            icon = "⚠"  # process ran but has kills
            sims_with_kills.append(r)
        elif p > 0:
            icon = "✓"  # fully clean
            sims_clean.append(r)
        else:
            icon = "?"
        
        print(f"    {icon} {r['file']:40s} proc={r['status']:4s}  evidence={ev:12s} ({p}P/{k}K)")
    
    if sims_with_kills:
        print(f"\n  ⚠ WARNING: {len(sims_with_kills)} SIMs ran successfully but contain KILL tokens:")
        for r in sims_with_kills:
            kill_reasons = [t.get('kill_reason', '?') for t in r['tokens'] if t.get('status') == 'KILL']
            print(f"    - {r['file']}: {', '.join(kill_reasons)}")
    
    # Save consolidated report
    report = {
        "timestamp": datetime.now(UTC).isoformat(),
        "total_tokens": graph["total_tokens"],
        "pass_count": graph["pass_count"],
        "kill_count": graph["kill_count"],
        "layers": graph["layers"],
        "sim_results": [{
            "file": r["file"],
            "process_status": r["status"],
            "evidence_status": r.get("evidence_status", "UNKNOWN"),
            "token_count": len(r["tokens"]),
            "pass_count": r.get("pass_count", 0),
            "kill_count": r.get("kill_count", 0),
        } for r in all_results],
        "all_tokens": all_tokens,
    }
    
    outpath = RESULTS_DIR / "unified_evidence_report.json"
    with open(outpath, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\n  Report saved to: {outpath}")


if __name__ == "__main__":
    main()
