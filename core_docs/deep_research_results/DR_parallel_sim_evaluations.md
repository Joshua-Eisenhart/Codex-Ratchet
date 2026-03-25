# Parallelizing SIM Evaluations in Codex-Ratchet with asyncio and subprocess.Popen

## Executive summary

Codex-Ratchet’s current unified SIM harness (`system_v4/probes/run_all_sims.py`) executes SIMs **sequentially** by looping over `TIERED_SIMS` and calling `run_sim()` one file at a time. Each call uses `subprocess.run(..., capture_output=True, timeout=...)`, then reads the SIM’s results JSON from `system_v4/probes/a2_state/sim_results/` to collect evidence tokens. Tier gating halts the pipeline if “gating tiers” emit unexpected `KILL` tokens, and negative SIMs (`neg_*.py`) are treated as “expected to KILL.” fileciteturn31file0L1-L1

This report proposes a refactor that preserves existing scoring behavior (including the axis orthogonality suite’s QIT scoring and evidence emission) by **only** changing the harness’s process orchestration. The refactor runs SIMs **in parallel within each tier** using an `asyncio` event loop plus a bounded worker pool implemented via `asyncio.Semaphore`, and spawns each SIM using `subprocess.Popen` (per your requirements). Logs are streamed in a non-blocking way by redirecting each subprocess’s `stdout` (and `stderr`) to separate files under `a2_state/logs/`, with Python invoked using `-u` to ensure unbuffered writes. The event loop remains responsive because blocking process waiting is delegated via `asyncio.to_thread()`. citeturn0search5turn3search0turn0search4turn4search3

A rigorous validation plan is included: (1) “compat mode” runs with `--max-workers 1` to reproduce sequential semantics, (2) golden-file comparisons of consolidated evidence output and per-SIM results JSONs (especially `axis_orthogonality_v3_results.json`), and (3) focused pytest tests using fast dummy SIM scripts.

Important limitation: the requested file name `autoresearch_sim_harness.py` was **not found** in the accessible Codex-Ratchet repository via connector search and direct fetch attempts. The closest canonical SIM harness in `system_v4/probes` is `run_all_sims.py`, which is what this research inspected and what the proposed patch targets. fileciteturn31file0L1-L1

## Baseline implementation and constraints discovered in the repos

### The current execution model is sequential and uses subprocess.run

`run_all_sims.py` defines `TIERED_SIMS` (tiers `T0_AXIOMS` through `T6_ADVANCED`) and a `GATING_TIERS` set (`T0_AXIOMS`, `T1_CONSTRAINTS`). The main loop iterates tier-by-tier and SIM-by-SIM; each SIM is executed by `run_sim(sim_file)` and then tokens are aggregated into `all_tokens` and summarized into a consolidated `unified_evidence_report.json`. fileciteturn31file0L1-L1

`run_sim()` uses:

- `subprocess.run([sys.executable, str(filepath)], capture_output=True, text=True, timeout=sim_timeout, cwd=str(PROBES_DIR))` (blocking) fileciteturn31file0L1-L1  
- A per-SIM timeout override mapping (e.g., `axis_orthogonality_suite.py: 600`) with a default of 120s fileciteturn31file0L1-L1  
- A large filename-to-results-JSON mapping used to locate the evidence token ledger fileciteturn31file0L1-L1  
- Tier gating semantics:
  - For non-negative SIMs in gating tiers, `KILL` tokens halt the entire pipeline
  - For negative SIMs (filenames starting with `neg_`), `KILL` is expected and lack of `KILL` is an “unexpected pass” warning fileciteturn31file0L1-L1

### Axis orthogonality scoring is self-contained and should not be modified

The axis orthogonality suite (`axis_orthogonality_suite.py`) deterministically computes pairwise and axis-0-moderated overlaps and writes `axis_orthogonality_v3_results.json` under `a2_state/sim_results/`. Evidence emission is delivered via an `evidence_ledger` containing a `PASS` token (`E_SIM_ORTHOGONAL_15PAIR_V3`). The harness should treat this output as an opaque artifact and merely run it and collect tokens. fileciteturn36file0L1-L1

### Other repos show an internal reference pattern for asyncio subprocesses

In `lev-os/leviathan`, a `Runner` class uses `asyncio.create_subprocess_exec(...)` and `asyncio.wait_for(proc.communicate(), timeout=...)`, killing the process on timeout. This demonstrates that your ecosystem already accepts asyncio-managed subprocess execution patterns, even though your explicit requirement here is `subprocess.Popen`. fileciteturn41file0L1-L1

## Concurrency design for parallel SIM evaluation

### Where asyncio belongs in the current harness

The clean insertion points in `run_all_sims.py` are:

- Replace the inner tier loop `for sim_file in tier_sims: result = run_sim(sim_file)` with scheduling + awaiting tasks for that tier. fileciteturn31file0L1-L1
- Preserve tier ordering and tier gating by:
  - Running **within-tier** SIMs concurrently (bounded)
  - Awaiting a tier’s completion before starting the next tier
  - Evaluating gating conditions based on the tier’s aggregated evidence before launching later tiers

This yields meaningful speedups because the largest work is the `T6_ADVANCED` tier (many SIMs) and the heaviest SIMs have explicit timeouts (e.g., 600 seconds for the axis orthogonality suite). fileciteturn31file0L1-L1

### Options for subprocess concurrency and logging

| Option | How processes are launched | How stdout is streamed to files | Event loop blocking risk | Platform notes | Fit for your constraints |
|---|---|---|---|---|---|
| Use asyncio subprocess APIs | `asyncio.create_subprocess_exec` citeturn1search0 | Read from `Process.stdout`/`stderr` and write | Low; fully async (but must avoid deadlocks; docs recommend `communicate()`) citeturn1search0 | Windows support tied to `ProactorEventLoop` citeturn1search5 | Great, but doesn’t satisfy “use Popen explicitly” |
| Popen + redirect to files | `subprocess.Popen(..., stdout=file, stderr=file)` citeturn0search4 | OS-level streaming to files; no Python pipe reading | Low; waiting is the blocking part, handled via `asyncio.to_thread` citeturn3search0 | Cross-platform; simplest | **Best match** for “Popen + streaming logs without blocking loop” |
| Popen + pipe + add_reader | `subprocess.Popen(..., stdout=PIPE)` | `loop.add_reader(fd, ...)` | Low, but file writes still sync unless offloaded | Unix event loops only; not portable | Complexity high; optional future enhancement |

The recommended implementation is **Popen + direct file redirection** for stdout/stderr, combined with `asyncio.Semaphore` for concurrency and `asyncio.to_thread(proc.wait)` for non-blocking waits. This directly leverages the subprocess API contract that `stdout`/`stderr` may be an existing file object, not just `PIPE`. citeturn0search4turn0search5turn3search0

### Ensuring “streaming” behavior in log files

When Python stdout is redirected to a file, buffering can delay writes significantly. To ensure logs update as the SIM runs, invoke each SIM with `python -u` (“unbuffered”). Python’s command-line docs specify `-u` forces `stdout` and `stderr` to be unbuffered and points to `PYTHONUNBUFFERED`. citeturn4search3

### Proposed flow chart

```mermaid
flowchart TD
  A[Start run_all_sims.py] --> B[Parse args: --max-workers, optional --run-id]
  B --> C[Create run_id + ensure a2_state/sim_results + a2_state/logs/run_id]
  C --> D{For each tier in TIERED_SIMS}
  D --> E[Schedule SIMs as asyncio Tasks]
  E --> F[Bound concurrency with asyncio.Semaphore]
  F --> G[subprocess.Popen each SIM with -u; redirect stdout/stderr to per-SIM log files]
  G --> H[Await completion via asyncio.to_thread(proc.wait) + timeout handling]
  H --> I[Read per-SIM results JSON from a2_state/sim_results; extract evidence_ledger/tokens]
  I --> J{Tier gating?}
  J -->|Gating tier has unexpected KILLs| K[Stop launching further tiers]
  J -->|No gating halt| D
  K --> L[Build evidence graph + write unified_evidence_report.json]
  D --> L
```

## Concrete refactor proposal and patch

### Design goals locked-in to preserve scoring behavior

The patch is explicitly designed to keep these behavioral invariants:

- The harness still runs the same SIM filenames per tier and maintains the same tier gating semantics. fileciteturn31file0L1-L1
- Evidence token parsing remains identical (accept either `evidence_ledger` or `tokens` schema variants). fileciteturn31file0L1-L1
- The axis orthogonality suite logic and file outputs remain untouched; it continues to emit evidence via `axis_orthogonality_v3_results.json`. fileciteturn36file0L1-L1
- Log streaming is added without changing SIM internals: stdout/stderr are redirected by the parent process, and Python’s `-u` makes writes immediate. citeturn0search4turn4search3

### Patch overview

Key changes to `system_v4/probes/run_all_sims.py`:

- Add `argparse` flag `--max-workers` (bounded concurrency)
- Add an `asyncio` entrypoint (`asyncio.run(...)`)
- Replace `subprocess.run` with `subprocess.Popen`
- Add per-SIM log files under `a2_state/logs/<run_id>/`
- Use `asyncio.Semaphore` to bound concurrent SIM processes citeturn0search5
- Use `asyncio.to_thread` to avoid blocking the event loop during `proc.wait()` citeturn3search0
- Maintain stable aggregation order (tier order, then SIM list order) to minimize diffs in emitted consolidated JSON

### Proposed diff-style patch

```diff
diff --git a/system_v4/probes/run_all_sims.py b/system_v4/probes/run_all_sims.py
index ce11d5e..parallel 100755
--- a/system_v4/probes/run_all_sims.py
+++ b/system_v4/probes/run_all_sims.py
@@ -1,19 +1,27 @@
 #!/usr/bin/env python3
 """
 Unified SIM Runner — Codex Ratchet Evidence Engine
 ====================================================
 Runs ALL SIM files, collects evidence tokens, builds
 the consolidated evidence graph, and produces the
 system status report.
@@
 """
 
+import argparse
+import asyncio
 import subprocess
 import json
 import os
 import sys
+import time
+import threading
 from datetime import datetime, UTC
 from pathlib import Path
 
 PROBES_DIR = Path(__file__).parent
 RESULTS_DIR = PROBES_DIR / "a2_state" / "sim_results"
+LOGS_DIR = PROBES_DIR / "a2_state" / "logs"
+
+_ACTIVE_PROCS: set[subprocess.Popen] = set()
+_ACTIVE_PROCS_LOCK = threading.Lock()
 
 # ── TIERED SIM EXECUTION ORDER ──
@@
 GATING_TIERS = {"T0_AXIOMS", "T1_CONSTRAINTS"}
 
+def _register_proc(p: subprocess.Popen) -> None:
+    with _ACTIVE_PROCS_LOCK:
+        _ACTIVE_PROCS.add(p)
+
+def _unregister_proc(p: subprocess.Popen) -> None:
+    with _ACTIVE_PROCS_LOCK:
+        _ACTIVE_PROCS.discard(p)
+
+def _terminate_all_procs(grace_seconds: float = 2.0) -> None:
+    with _ACTIVE_PROCS_LOCK:
+        procs = list(_ACTIVE_PROCS)
+    for p in procs:
+        try:
+            p.terminate()
+        except Exception:
+            pass
+    deadline = time.monotonic() + grace_seconds
+    for p in procs:
+        remaining = max(0.0, deadline - time.monotonic())
+        try:
+            p.wait(timeout=remaining)
+        except Exception:
+            pass
+    for p in procs:
+        try:
+            if p.poll() is None:
+                p.kill()
+        except Exception:
+            pass
+
+def _safe_log_stem(filename: str) -> str:
+    # Keep filenames stable across OSes / shells.
+    # Example: "axis_orthogonality_suite.py" -> "axis_orthogonality_suite"
+    base = filename.replace("\\", "/").split("/")[-1]
+    if base.endswith(".py"):
+        base = base[:-3]
+    return "".join(ch if (ch.isalnum() or ch in ("-", "_", ".")) else "_" for ch in base)
+
+def _tail_text(path: Path, max_chars: int = 200) -> str:
+    try:
+        data = path.read_bytes()
+        if not data:
+            return ""
+        txt = data.decode("utf-8", errors="replace")
+        return txt[-max_chars:]
+    except Exception:
+        return ""
+
+# Hoist mappings so they are not rebuilt per SIM.
+_TIMEOUT_OVERRIDES = {
+    "axis_orthogonality_suite.py": 600,
+    "tier_3_mega_sim.py": 300,
+}
+
+_RESULT_FILES = {
+    "foundations_sim.py": "foundations_results.json",
+    "math_foundations_sim.py": "math_foundations_results.json",
+    "deep_math_foundations_sim.py": "deep_math_results.json",
+    "arithmetic_gravity_sim.py": "arithmetic_gravity_results.json",
+    "proof_cost_sim.py": "proof_cost_results.json",
+    "navier_stokes_complexity_sim.py": "navier_stokes_results.json",
+    "complexity_gap_v2_sim.py": "complexity_gap_v2_results.json",
+    "topology_operator_sim.py": "topology_operator_results.json",
+    "igt_game_theory_sim.py": "igt_results.json",
+    "engine_terrain_sim.py": "process_cycle_terrain_results.json",
+    "igt_advanced_sim.py": "igt_advanced_results.json",
+    "godel_stall_sim.py": "godel_stall_results.json",
+    "dual_weyl_spinor_engine_sim.py": "dual_weyl_results.json",
+    "full_8stage_engine_sim.py": "full_8stage_results.json",
+    "rock_falsifier_sim.py": "rock_falsifier_results.json",
+    "constraint_gap_sim.py": "operator_bound_gap_results.json",
+    "szilard_64stage_v2_sim.py": "szilard_64stage_v2_results.json",
+    "nlm_batch2_sim.py": "nlm_batch2_results.json",
+    "gain_calibration_v2_sim.py": "gain_calibration_v2_results.json",
+    "demon_fixed_sim.py": "demon_fixed_results.json",
+    "type2_engine_sim.py": "type2_process_cycle_results.json",
+    "riemann_zeta_sim.py": "riemann_zeta_results.json",
+    "p_vs_np_sim.py": "p_vs_np_results.json",
+    "navier_stokes_qit_sim.py": "navier_stokes_qit_results.json",
+    "consciousness_sim.py": "recursive_state_results.json",
+    "alignment_sim.py": "alignment_results.json",
+    "abiogenesis_v2_sim.py": "abiogenesis_v2_results.json",
+    "quantum_gravity_sim.py": "quantum_gravity_results.json",
+    "yang_mills_sim.py": "yang_mills_results.json",
+    "scale_testing_sim.py": "scale_testing_results.json",
+    "chemistry_sim.py": "chemistry_results.json",
+    "world_model_sim.py": "world_model_results.json",
+    "scientific_method_sim.py": "scientific_method_results.json",
+    "navier_stokes_formal_sim.py": "navier_stokes_formal_results.json",
+    "rock_falsifier_enhanced_sim.py": "rock_falsifier_enhanced_results.json",
+    "tier_3_mega_sim.py": "tier_3_mega_results.json",
+    "sim_moloch_trap_field.py": "moloch_trap_field_results.json",
+    "axis_6_precedence_sim.py": "axis_6_precedence_results.json",
+    "i_scalar_filtration_sim.py": "iscalar_filtration_results.json",
+    "axis3_orthogonality_sim.py": "axis3_orthogonality_results.json",
+    "axis_triplet_orthogonality_sim.py": "axis_triplet_orthogonality_results.json",
+    "axis0_correlation_sim.py": "axis0_correlation_results.json",
+    "axis0_path_integral_sim.py": "axis0_path_integral_results.json",
+    "axis_relations_sim.py": "axis_relations_results.json",
+    "orthogonality_axis0_axis1_sim.py": "ort_0_1_results.json",
+    "orthogonality_axis0_axis2_sim.py": "ort_0_2_results.json",
+    "orthogonality_axis0_axis4_sim.py": "ort_0_4_results.json",
+    "orthogonality_axis0_axis5_sim.py": "ort_0_5_results.json",
+    "orthogonality_axis0_axis6_sim.py": "ort_0_6_results.json",
+    "qit_topology_parity_sim.py": "qit_topology_parity_results.json",
+    "deep_graveyard_battery.py": "deep_graveyard_results.json",
+    "extended_graveyard_battery.py": "extended_graveyard_results.json",
+    "thermodynamic_graveyard_battery.py": "thermo_graveyard_results.json",
+    "information_graveyard_battery.py": "info_graveyard_results.json",
+    "axis_orthogonality_suite.py": "axis_orthogonality_v3_results.json",
+    "egglog_graph_rewrite_probe.py": "egglog_rewrite_results.json",
+    "neg_scrambled_sequence_sim.py": "neg_scrambled_sequence_results.json",
+    "neg_inverted_major_loop_sim.py": "neg_inverted_major_loop_results.json",
+    "neg_commutative_engine_sim.py": "neg_commutative_process_cycle_results.json",
+    "neg_infinite_d_sim.py": "neg_infinite_d_results.json",
+    "neg_single_loop_sim.py": "neg_single_loop_results.json",
+    "neg_classical_probability_sim.py": "neg_classical_results.json",
+    "neg_no_dissipation_sim.py": "neg_no_dissipation_results.json",
+}
 
-
-def run_sim(filename: str) -> dict:
-    """Run a single SIM file and capture its output."""
+def _run_sim_blocking(filename: str, *, run_id: str, logs_root: Path) -> dict:
+    """Run a single SIM file via subprocess.Popen and write stdout/stderr to log files."""
     filepath = PROBES_DIR / filename
     if not filepath.exists():
         return {"file": filename, "status": "MISSING", "tokens": []}
 
-    # Per-SIM timeout overrides (default 120s)
-    timeout_overrides = {
-        "axis_orthogonality_suite.py": 600,  # Full 15-pair × 4-dim suite
-        "tier_3_mega_sim.py": 300,
-    }
-    sim_timeout = timeout_overrides.get(filename, 120)
+    sim_timeout = _TIMEOUT_OVERRIDES.get(filename, 120)
+
+    log_dir = logs_root / run_id
+    os.makedirs(log_dir, exist_ok=True)
+    stem = _safe_log_stem(filename)
+    stdout_path = log_dir / f"{stem}.stdout.log"
+    stderr_path = log_dir / f"{stem}.stderr.log"
 
     try:
-        result = subprocess.run(
-            [sys.executable, str(filepath)],
-            capture_output=True,
-            text=True,
-            timeout=sim_timeout,
-            cwd=str(PROBES_DIR)
-        )
+        start = time.monotonic()
+        # Use "-u" to make logs stream in near-real-time when redirected.
+        cmd = [sys.executable, "-u", str(filepath)]
+
+        # Redirect to files (non-blocking for the asyncio loop).
+        with open(stdout_path, "wb") as out_f, open(stderr_path, "wb") as err_f:
+            p = subprocess.Popen(
+                cmd,
+                cwd=str(PROBES_DIR),
+                stdout=out_f,
+                stderr=err_f,
+            )
+            _register_proc(p)
+            try:
+                p.wait(timeout=sim_timeout)
+            except subprocess.TimeoutExpired:
+                try:
+                    p.terminate()
+                except Exception:
+                    pass
+                try:
+                    p.wait(timeout=2)
+                except Exception:
+                    try:
+                        p.kill()
+                    except Exception:
+                        pass
+                return {
+                    "file": filename,
+                    "status": "TIMEOUT",
+                    "evidence_status": "NO_TOKENS",
+                    "tokens": [],
+                    "pass_count": 0,
+                    "kill_count": 0,
+                    "returncode": None,
+                    "stdout_log": str(stdout_path),
+                    "stderr_log": str(stderr_path),
+                    "stderr": _tail_text(stderr_path, 200),
+                    "duration_s": time.monotonic() - start,
+                }
+            finally:
+                _unregister_proc(p)
 
-        # Try to find the results JSON
-        result_files = {
-            ...
-        }
-
         tokens = []
-        rfile = result_files.get(filename)
+        rfile = _RESULT_FILES.get(filename)
         if rfile:
             rpath = RESULTS_DIR / rfile
             if rpath.exists():
                 with open(rpath) as f:
                     data = json.load(f)
                     # Accept both schema variants
                     tokens = data.get("evidence_ledger", data.get("tokens", []))
 
-        status = "PASS" if result.returncode == 0 else "FAIL"
+        status = "PASS" if p.returncode == 0 else "FAIL"
 
         # Evidence-level health: does the SIM have any KILL tokens?
@@
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
-            "returncode": result.returncode,
-            "stderr": result.stderr[-200:] if result.stderr else "",
+            "returncode": p.returncode,
+            "stdout_log": str(stdout_path),
+            "stderr_log": str(stderr_path),
+            "stderr": _tail_text(stderr_path, 200),
+            "duration_s": time.monotonic() - start,
         }
 
-    except subprocess.TimeoutExpired:
-        return {"file": filename, "status": "TIMEOUT", "evidence_status": "NO_TOKENS",
-                "tokens": [], "pass_count": 0, "kill_count": 0}
     except Exception as e:
-        return {"file": filename, "status": f"ERROR: {e}", "evidence_status": "NO_TOKENS",
-                "tokens": [], "pass_count": 0, "kill_count": 0}
+        return {
+            "file": filename,
+            "status": f"ERROR: {e}",
+            "evidence_status": "NO_TOKENS",
+            "tokens": [],
+            "pass_count": 0,
+            "kill_count": 0,
+            "stdout_log": "",
+            "stderr_log": "",
+            "stderr": "",
+        }
+
+async def run_sim_async(filename: str, *, sem: asyncio.Semaphore, run_id: str) -> dict:
+    async with sem:
+        # Run blocking Popen logic in a thread to avoid blocking event loop.
+        return await asyncio.to_thread(_run_sim_blocking, filename, run_id=run_id, logs_root=LOGS_DIR)
 
@@
-def main():
+def _parse_args(argv: list[str] | None = None):
+    p = argparse.ArgumentParser(description="Codex Ratchet — Unified SIM Runner (parallel-capable)")
+    p.add_argument("--max-workers", type=int, default=1, help="Max concurrent SIM subprocesses to run per tier (default: 1)")
+    p.add_argument("--run-id", type=str, default="", help="Optional run id for log folder naming; default is timestamp-based")
+    return p.parse_args(argv)
+
+async def _run_all_sims(max_workers: int, run_id: str):
     print(f"{'#'*60}")
     print(f"  CODEX RATCHET — UNIFIED SIM RUNNER")
     print(f"  {datetime.now(UTC).isoformat()}")
     print(f"{'#'*60}")
 
     os.makedirs(RESULTS_DIR, exist_ok=True)
+    os.makedirs(LOGS_DIR / run_id, exist_ok=True)
 
     all_results = []
     all_tokens = []
 
+    sem = asyncio.Semaphore(max_workers)
+
     for tier_name, tier_sims in TIERED_SIMS.items():
         print(f"\n{'═'*60}")
         print(f"  TIER: {tier_name}")
         print(f"{'═'*60}")
 
+        # Schedule tier sims concurrently (bounded).
+        tasks = {s: asyncio.create_task(run_sim_async(s, sem=sem, run_id=run_id), name=f"sim:{s}") for s in tier_sims}
+        tier_done = []
+        for fut in asyncio.as_completed(tasks.values()):
+            r = await fut
+            tier_done.append(r)
+
+        results_by_file = {r["file"]: r for r in tier_done}
+
         tier_kills = 0
         tier_unexpected_passes = 0
-        is_neg_tier = (tier_name == "T1_CONSTRAINTS")
-
-        for sim_file in tier_sims:
+        for sim_file in tier_sims:
             print(f"\n{'─'*40}")
             print(f"  Running: {sim_file}")
             print(f"{'─'*40}")
-
-            result = run_sim(sim_file)
+            result = results_by_file.get(sim_file, {"file": sim_file, "status": "ERROR: missing result", "tokens": []})
             all_results.append(result)
             for t in result["tokens"]:
                 t["source_file"] = sim_file
             all_tokens.extend(result["tokens"])
 
@@
         if tier_name in GATING_TIERS:
             if tier_kills > 0:
                 print(f"\n  ⛔ TIER GATE HALT: {tier_name} has {tier_kills} KILL tokens")
                 print(f"     Pipeline cannot proceed past {tier_name}.")
                 print(f"     Fix root axiom failures before running higher tiers.")
                 break  # Stop execution
             if tier_unexpected_passes > 0:
                 print(f"\n  ⚠ TIER WARNING: {tier_name} has {tier_unexpected_passes} negative SIMs that passed unexpectedly")
 
@@
     outpath = RESULTS_DIR / "unified_evidence_report.json"
     with open(outpath, "w") as f:
         json.dump(report, f, indent=2)
     print(f"\n  Report saved to: {outpath}")
 
+def main(argv: list[str] | None = None):
+    args = _parse_args(argv)
+    if args.max_workers < 1:
+        raise SystemExit("--max-workers must be >= 1")
+    run_id = args.run_id.strip() or datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
+    try:
+        asyncio.run(_run_all_sims(max_workers=args.max_workers, run_id=run_id))
+    except KeyboardInterrupt:
+        print("\nKeyboardInterrupt: terminating running SIM subprocesses...")
+        _terminate_all_procs()
+        raise
+
 if __name__ == "__main__":
     main()
```

### Notes on the patch’s concurrency, cleanup, and logging

The patch uses three core asyncio mechanisms:

- `asyncio.run(...)` to create and own the event loop (recommended in the asyncio event-loop docs). citeturn3search4  
- `asyncio.Semaphore` to bound concurrent tasks to `--max-workers`. citeturn0search5  
- `asyncio.to_thread` to run blocking `Popen.wait()` calls without blocking the event loop. citeturn3search0  

For logging, it relies on the subprocess API contract that `stdout` and `stderr` may be file objects; the child process streams directly to them. citeturn0search4 The `-u` flag is used to ensure that Python SIM processes flush to these files without buffering delays. citeturn4search3

Process cleanup is handled via a global registry of active `Popen` objects. On `KeyboardInterrupt`, the runner terminates all tracked processes and then escalates to `kill()` for any that refuse to stop promptly.

## Validation and tests to ensure correctness and unchanged scoring

### Validation steps for unchanged evidence and scoring

Because the harness is only an orchestrator and scoring happens inside SIM scripts (e.g., the axis orthogonality suite emits its own evidence JSON), the key correctness property is: **the same SIM scripts, run with the same inputs, produce the same results JSONs and token ledgers**. fileciteturn36file0L1-L1

A practical validation protocol:

- Run **baseline sequential** harness (current `main` branch version) and archive:
  - `system_v4/probes/a2_state/sim_results/unified_evidence_report.json`
  - `system_v4/probes/a2_state/sim_results/axis_orthogonality_v3_results.json`
- Run the refactored harness with `--max-workers 1` (compat mode), compare:
  - JSON equivalence for `all_tokens` multiset (order-insensitive comparison recommended)
  - Equality (or stable equivalence) of `pass_count`, `kill_count`, and layer summaries
- Run the refactored harness with `--max-workers N` where `N>1`, compare:
  - Per-SIM results JSONs should match (the SIM scripts write these files; harness shouldn’t mutate their contents)
  - Consolidated report should match except for any optional new metadata fields you might add (e.g., `stdout_log`, `stderr_log`, `duration_s`)

Special attention for the axis orthogonality suite:
- It is deterministic due to fixed RNG seeds and deterministic computation paths. fileciteturn36file0L1-L1  
- The harness should verify the existence of `axis_orthogonality_v3_results.json` and that the `evidence_ledger` token (`E_SIM_ORTHOGONAL_15PAIR_V3`) remains identical between runs. fileciteturn36file0L1-L1  

### Proposed pytest tests

Codex-Ratchet already uses pytest + hypothesis in `system_v4/probes/test_nested_graph_builder.py`. fileciteturn45file0L1-L1

Add a small test module that does **not** run the full SIM suite (too slow for CI), but verifies the new parallel runner behavior with dummy SIM scripts created in a temp directory:

- A dummy SIM that:
  - prints a few lines to stdout/stderr (to test log streaming and `-u`)
  - writes a results JSON with an `evidence_ledger` token into a temp `sim_results` folder
  - exits 0  
- A dummy SIM that sleeps longer than timeout to ensure TIMEOUT behavior and cleanup works

To make this test practical, the runner should accept injected `probes_dir` and `results_dir` parameters (or the test should monkeypatch module globals). If you prefer minimal surface changes, use pytest `monkeypatch` to point `PROBES_DIR`, `RESULTS_DIR`, and `LOGS_DIR` to `tmp_path`.

## Pull request plan and operational guidance

### Branching and commit strategy

Recommended branch name:
- `feature/parallel-sim-runner-asyncio-popen`

Suggested commits (split for reviewability):
- `Autopoietic Hub: parallel SIM runner scaffolding (asyncio + argparse)`
- `Autopoietic Hub: Popen execution + per-SIM logs + timeout cleanup`
- `Autopoietic Hub: pytest harness tests for parallel runner`

PR description template (high-signal, reviewer-friendly):
- **Problem:** current SIM runner executes sequentially; slow wall-clock time for `T5/T6` tiers; no per-SIM logs
- **Solution:** asyncio bounded parallel execution per tier; `--max-workers`; `Popen` with `-u`; per-SIM stdout/stderr logs under `a2_state/logs/<run_id>/`
- **Behavior preserved:** evidence token collection semantics unchanged; axis orthogonality suite unchanged; tier gating semantics unchanged
- **How to test:** `python system_v4/probes/run_all_sims.py --max-workers 1` then `--max-workers 8`; compare results JSONs; run `pytest -q`

### Important limitation about the “commit directly via connector” instruction

You requested that I commit/push files directly to your GitHub repo via the connector and not print patches here. However, the available GitHub connector actions in this session are **read-only** (e.g., fetch/search/compare) and do not include write operations like commit/push or PR creation. As a result, I cannot perform the direct commit step from within this chat, and I’ve provided the patch inline instead.

If you want automated PR creation from the assistant in a future session, the environment would need a GitHub tool with write scopes (create branch, commit, push, open PR).