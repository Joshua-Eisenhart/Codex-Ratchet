#!/usr/bin/env python3
"""
Layer 6 — Master Engine SIM
=============================
Everything composed. The whole engine on the whole manifold.

Runs all layers in dependency order, gates each on the previous,
and emits a master verdict.

Token: E_MASTER_ENGINE_VALID
"""

import numpy as np
import os
import sys
import json
import time
from datetime import datetime, UTC

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from proto_ratchet_sim_runner import EvidenceToken


def run_L6_master():
    print("=" * 72)
    print("LAYER 6: MASTER ENGINE SIM")
    print("  'Everything composed — bottom-up validation'")
    print("=" * 72)

    all_tokens = []
    layer_results = {}
    all_pass = True

    # ── Layer 0: S³ Hopf Manifold ────────────────────────────────
    print("\n" + "─" * 72)
    print("  Running Layer 0: S³ Hopf Manifold...")
    print("─" * 72)
    t0 = time.time()
    from sim_L0_s3_valid import run_L0_validation
    l0_tokens = run_L0_validation()
    dt0 = time.time() - t0
    l0_pass = all(t.status == "PASS" for t in l0_tokens)
    layer_results["L0_S3_Manifold"] = {"pass": l0_pass, "time_s": dt0}
    all_tokens.extend(l0_tokens)
    if not l0_pass:
        print("\n  ✗ Layer 0 KILL — halting pipeline")
        all_pass = False

    # ── Layer 1: Two Loop Families ───────────────────────────────
    if all_pass:
        print("\n" + "─" * 72)
        print("  Running Layer 1: Two Loop Families...")
        print("─" * 72)
        t1 = time.time()
        from sim_L1_loop_families import run_L1_validation
        l1_tokens = run_L1_validation()
        dt1 = time.time() - t1
        l1_pass = all(t.status == "PASS" for t in l1_tokens)
        layer_results["L1_Loop_Families"] = {"pass": l1_pass, "time_s": dt1}
        all_tokens.extend(l1_tokens)
        if not l1_pass:
            print("\n  ✗ Layer 1 KILL — halting pipeline")
            all_pass = False

    # ── Layer 2: Eight Topological Stages ────────────────────────
    if all_pass:
        print("\n" + "─" * 72)
        print("  Running Layer 2: Eight Topological Stages...")
        print("─" * 72)
        t2 = time.time()
        from sim_L2_eight_stages import run_L2_validation
        l2_tokens = run_L2_validation()
        dt2 = time.time() - t2
        l2_pass = all(t.status == "PASS" for t in l2_tokens)
        layer_results["L2_Eight_Stages"] = {"pass": l2_pass, "time_s": dt2}
        all_tokens.extend(l2_tokens)
        if not l2_pass:
            print("\n  ✗ Layer 2 KILL — halting pipeline")
            all_pass = False

    # ── Layer 3: Operators on Stages ─────────────────────────────
    if all_pass:
        print("\n" + "─" * 72)
        print("  Running Layer 3: Operators on Stages...")
        print("─" * 72)
        t3 = time.time()
        from sim_L3_operators_on_stages import run_L3_validation
        l3_tokens = run_L3_validation()
        dt3 = time.time() - t3
        l3_pass = all(t.status == "PASS" for t in l3_tokens)
        layer_results["L3_Operators"] = {"pass": l3_pass, "time_s": dt3}
        all_tokens.extend(l3_tokens)
        if not l3_pass:
            print("\n  ✗ Layer 3 KILL — halting pipeline")
            all_pass = False

    # ── Layer 4: Engine Chirality ────────────────────────────────
    if all_pass:
        print("\n" + "─" * 72)
        print("  Running Layer 4: Engine Chirality...")
        print("─" * 72)
        t4 = time.time()
        from sim_L4_engine_chirality import run_L4_validation
        l4_tokens = run_L4_validation()
        dt4 = time.time() - t4
        l4_pass = all(t.status == "PASS" for t in l4_tokens)
        layer_results["L4_Chirality"] = {"pass": l4_pass, "time_s": dt4}
        all_tokens.extend(l4_tokens)
        if not l4_pass:
            print("\n  ✗ Layer 4 KILL — halting pipeline")
            all_pass = False

    # ── Layer 5: Axis Orthogonality ──────────────────────────────
    if all_pass:
        print("\n" + "─" * 72)
        print("  Running Layer 5: Axis Orthogonality...")
        print("─" * 72)
        t5 = time.time()
        from sim_L5_axis_orthogonality import run_L5_validation
        l5_tokens = run_L5_validation()
        dt5 = time.time() - t5
        l5_pass = all(t.status == "PASS" for t in l5_tokens)
        layer_results["L5_Axes"] = {"pass": l5_pass, "time_s": dt5}
        all_tokens.extend(l5_tokens)
        if not l5_pass:
            print("\n  ✗ Layer 5 KILL — halting pipeline")
            all_pass = False

    # ── Master Verdict ───────────────────────────────────────────
    print(f"\n{'=' * 72}")
    print(f"  MASTER ENGINE RESULTS")
    print(f"{'=' * 72}")
    total_time = sum(v["time_s"] for v in layer_results.values())
    for name, info in layer_results.items():
        icon = "✓" if info["pass"] else "✗"
        print(f"  {icon} {name}: {'PASS' if info['pass'] else 'KILL'} ({info['time_s']:.2f}s)")
    print(f"\n  Total time: {total_time:.2f}s")
    print(f"  Total tokens: {len(all_tokens)}")
    print(f"  PASS: {sum(1 for t in all_tokens if t.status == 'PASS')}")
    print(f"  KILL: {sum(1 for t in all_tokens if t.status == 'KILL')}")
    print(f"\n{'=' * 72}")
    print(f"  MASTER VERDICT: {'PASS ✓' if all_pass else 'KILL ✗'}")
    print(f"{'=' * 72}")

    if all_pass:
        all_tokens.append(EvidenceToken(
            "E_MASTER_ENGINE_VALID", "S_L6_MASTER",
            "PASS", float(len(layer_results))
        ))
    else:
        failed = [k for k, v in layer_results.items() if not v["pass"]]
        all_tokens.append(EvidenceToken(
            "", "S_L6_MASTER", "KILL", 0.0,
            f"BLOCKED_AT: {', '.join(failed)}"
        ))

    # Save
    base_dir = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(base_dir, "a2_state", "sim_results")
    os.makedirs(results_dir, exist_ok=True)
    outpath = os.path.join(results_dir, "L6_master_engine_results.json")
    with open(outpath, "w") as f:
        json.dump({
            "timestamp": datetime.now(UTC).isoformat(),
            "layer": 6,
            "name": "Master_Engine_Validation",
            "layer_results": {k: {"pass": bool(v["pass"]), "time_s": v["time_s"]}
                              for k, v in layer_results.items()},
            "total_tokens": len(all_tokens),
            "pass_count": sum(1 for t in all_tokens if t.status == "PASS"),
            "kill_count": sum(1 for t in all_tokens if t.status == "KILL"),
            "evidence_ledger": [t.__dict__ for t in all_tokens],
        }, f, indent=2, default=str)
    print(f"  Results saved: {outpath}")
    return all_tokens


if __name__ == "__main__":
    run_L6_master()
