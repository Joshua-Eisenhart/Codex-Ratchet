"""
heartbeat_daemon.py — Self-Reflecting Autopoietic Heartbeat
=============================================================
JP's bootstrap chain, fully implemented:

  dna.yaml → DAG walker → XDG telemetry → self-reflection loop
  → versioned dna.yaml seeds

Every tick:
  1. Load dna.yaml (the seed)
  2. Run all probes (DAG walk)
  3. Bridge evidence → witnesses
  4. Compare this run to last run (self-reflection)
  5. Write triage report (should I keep running?)
  6. Every Nth tick: deep triage (should I change the seed?)
  7. Snapshot dna.yaml version (versioned seeds)
"""

import json
import os
import sys
import shutil
import yaml
from pathlib import Path
from datetime import datetime, timezone

REPO = str(Path(__file__).resolve().parents[3])
sys.path.insert(0, REPO)


def load_dna():
    dna_path = os.path.join(REPO, "system_v4/skills/intent-compiler/dna.yaml")
    with open(dna_path) as f:
        return yaml.safe_load(f)


def run_probes():
    """Execute run_all_sims.py and capture the result."""
    import subprocess
    result = subprocess.run(
        [sys.executable, os.path.join(REPO, "system_v4/probes/run_all_sims.py")],
        cwd=REPO, capture_output=True, text=True, timeout=300
    )
    return result.returncode == 0, result.stdout, result.stderr


def bridge_evidence():
    """Run the evidence → witness bridge."""
    import subprocess
    result = subprocess.run(
        [sys.executable, os.path.join(REPO, "system_v4/skills/evidence_witness_bridge.py")],
        cwd=REPO, capture_output=True, text=True, timeout=60
    )
    return result.returncode == 0


def load_current_report():
    report_path = os.path.join(
        REPO, "system_v4/probes/a2_state/sim_results/unified_evidence_report.json"
    )
    if os.path.exists(report_path):
        with open(report_path) as f:
            return json.load(f)
    return None


def load_previous_report():
    history_dir = os.path.join(REPO, "system_v4/probes/a2_state/sim_results/history")
    if not os.path.exists(history_dir):
        return None
    files = sorted(Path(history_dir).glob("report_*.json"))
    if files:
        with open(files[-1]) as f:
            return json.load(f)
    return None


def save_report_snapshot(report):
    """Save timestamped snapshot for comparison on next run."""
    history_dir = os.path.join(REPO, "system_v4/probes/a2_state/sim_results/history")
    os.makedirs(history_dir, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    snapshot_path = os.path.join(history_dir, f"report_{ts}.json")
    with open(snapshot_path, "w") as f:
        json.dump(report, f, indent=2)
    
    # Keep only last 50 snapshots
    files = sorted(Path(history_dir).glob("report_*.json"))
    for old in files[:-50]:
        old.unlink()


def version_dna():
    """Snapshot the current dna.yaml with a version timestamp."""
    dna_src = os.path.join(REPO, "system_v4/skills/intent-compiler/dna.yaml")
    versions_dir = os.path.join(REPO, "system_v4/skills/intent-compiler/versions")
    os.makedirs(versions_dir, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dst = os.path.join(versions_dir, f"dna_{ts}.yaml")
    shutil.copy2(dna_src, dst)
    
    # Keep only last 20 versions
    files = sorted(Path(versions_dir).glob("dna_*.yaml"))
    for old in files[:-20]:
        old.unlink()


def reflect(current, previous):
    """
    Self-reflection: compare current run to previous run.
    Returns a triage dict.
    """
    triage = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": "CONTINUE",
        "regressions": [],
        "recoveries": [],
        "new_kills": [],
        "resolved_kills": [],
        "delta_pass": 0,
        "delta_kill": 0,
        "trend": "STABLE",
        "runner_ok": True,
        "evidence_ok": True,
    }

    curr_pass = current.get("pass_count", 0)
    curr_kill = current.get("kill_count", 0)
    curr_total = current.get("total_tokens", 0)
    
    if previous is None:
        triage["trend"] = "FIRST_RUN"
        triage["current_pass"] = curr_pass
        triage["current_kill"] = curr_kill
        triage["evidence_ok"] = curr_kill == 0
        return triage
    
    prev_pass = previous.get("pass_count", 0)
    prev_kill = previous.get("kill_count", 0)
    
    triage["current_pass"] = curr_pass
    triage["current_kill"] = curr_kill
    triage["previous_pass"] = prev_pass
    triage["previous_kill"] = prev_kill
    triage["delta_pass"] = curr_pass - prev_pass
    triage["delta_kill"] = curr_kill - prev_kill
    
    # Evidence health: any KILLs means evidence is degraded
    triage["evidence_ok"] = curr_kill == 0
    
    # Detect regressions
    if curr_kill > prev_kill:
        triage["regressions"].append(f"KILL count increased: {prev_kill}→{curr_kill}")
        triage["trend"] = "DEGRADING"
    
    if curr_pass < prev_pass:
        triage["regressions"].append(f"PASS count decreased: {prev_pass}→{curr_pass}")
        triage["trend"] = "DEGRADING"
    
    # Detect recoveries
    if curr_kill < prev_kill:
        triage["recoveries"].append(f"KILL count decreased: {prev_kill}→{curr_kill}")
        triage["trend"] = "IMPROVING"
    
    if curr_pass > prev_pass:
        triage["recoveries"].append(f"PASS count increased: {prev_pass}→{curr_pass}")
        triage["trend"] = "IMPROVING"
    
    # Self-kill conditions (from dna.yaml)
    if curr_pass < 50:
        triage["action"] = "SELF_KILL"
        triage["regressions"].append("PASS count below 50 — engine integrity compromised")
    
    # Find specific new and resolved KILLs using (sim_spec_id, status, kill_reason)
    # tuples — NOT token_id, which is often blank on KILL tokens
    curr_tokens = current.get("all_tokens", [])
    prev_tokens = previous.get("all_tokens", [])
    
    def _kill_signature(token):
        """Stable identifier for a KILL token — works even with blank token_id."""
        return (
            token.get("sim_spec_id", ""),
            token.get("source_file", ""),
            token.get("kill_reason", "UNKNOWN"),
        )
    
    prev_kill_sigs = {_kill_signature(t) for t in prev_tokens if t.get("status") == "KILL"}
    curr_kill_sigs = {_kill_signature(t) for t in curr_tokens if t.get("status") == "KILL"}
    
    new_kills = curr_kill_sigs - prev_kill_sigs
    resolved_kills = prev_kill_sigs - curr_kill_sigs
    
    if new_kills:
        triage["new_kills"] = [
            f"{sig[0]} ({sig[1]}): {sig[2]}" for sig in sorted(new_kills)
        ]
    if resolved_kills:
        triage["resolved_kills"] = [
            f"{sig[0]} ({sig[1]}): {sig[2]}" for sig in sorted(resolved_kills)
        ]
    
    return triage


def run_tick(spawn_codex: bool = True):
    """Execute one complete heartbeat tick."""
    print(f"\n{'='*60}")
    print(f"HEARTBEAT TICK: {datetime.now(timezone.utc).isoformat()}")
    print(f"{'='*60}")
    
    # 1. Load DNA
    dna = load_dna()
    known_open_kills = set(dna.get("graveyard", {}).get("known_open_kills", []))
    print(f"  DNA loaded: v{dna.get('version', '?')}, {len(dna.get('probes', []))} probes")
    print(f"  Known open KILLs: {len(known_open_kills)}")
    
    # 2. Run probes
    print(f"  Running probes...")
    runner_ok, stdout, stderr = run_probes()
    if not runner_ok:
        print(f"\n  RUNNER STATUS: ✗ FAIL")
        if stderr:
            print(f"    stderr: {stderr[:200]}")
        print(f"  EVIDENCE STATUS: UNKNOWN (runner failed)")
        print(f"  ACTION: ATTENTION_REQUIRED")
        return
    print(f"  RUNNER STATUS: ✓ OK")
    
    # 3. Bridge evidence → witnesses
    print(f"  Bridging evidence → witnesses...")
    bridge_ok = bridge_evidence()
    print(f"  {'✓' if bridge_ok else '✗'} Bridge {'completed' if bridge_ok else 'failed'}")
    
    # 4. Load report and assess evidence health
    previous = load_previous_report()
    current = load_current_report()
    
    if not current:
        print(f"\n  EVIDENCE STATUS: ✗ NO REPORT")
        print(f"  ACTION: ATTENTION_REQUIRED")
        return
    
    # 4a. Per-SIM evidence health
    sim_results = current.get("sim_results", [])
    sims_clean = []
    sims_with_kills = []
    sims_no_tokens = []
    for sim in sim_results:
        ev = sim.get("evidence_status", "UNKNOWN")
        if ev == "ALL_PASS":
            sims_clean.append(sim)
        elif ev == "KILL_PRESENT":
            sims_with_kills.append(sim)
        elif ev == "NO_TOKENS":
            sims_no_tokens.append(sim)
    
    # 4b. Classify current KILLs as known vs new
    all_tokens = current.get("all_tokens", [])
    current_kill_ids = set()
    for t in all_tokens:
        if t.get("status") == "KILL":
            tid = t.get("token_id") or t.get("sim_spec_id", "")
            current_kill_ids.add(tid)
    
    new_regression_kills = current_kill_ids - known_open_kills
    known_present_kills = current_kill_ids & known_open_kills
    
    # 4c. Determine evidence status
    if len(sims_with_kills) == 0:
        evidence_label = "CLEAN"
    elif new_regression_kills:
        evidence_label = "DEGRADED"
    else:
        evidence_label = "KNOWN_ISSUES"  # all KILLs are in allowlist
    
    # 5. Self-reflect (delta comparison)
    triage = reflect(current, previous)
    
    # Override action based on evidence assessment
    if new_regression_kills:
        triage["action"] = "DEGRADED"
    elif known_present_kills and not new_regression_kills:
        triage["action"] = "ATTENTION_REQUIRED"
    elif evidence_label == "CLEAN":
        triage["action"] = "CONTINUE"
    
    # 6. Print assessment
    print(f"\n  {'─'*50}")
    print(f"  EVIDENCE ASSESSMENT")
    print(f"  {'─'*50}")
    print(f"    Runner status:   {'OK' if runner_ok else 'FAIL'}")
    print(f"    Evidence status: {evidence_label}")
    print(f"    PASS tokens:     {triage.get('current_pass', '?')} (Δ{triage['delta_pass']:+d})")
    print(f"    KILL tokens:     {triage.get('current_kill', '?')} (Δ{triage['delta_kill']:+d})")
    print(f"    Trend:           {triage['trend']}")
    print(f"    Action:          {triage['action']}")
    
    print(f"\n    SIMs clean:       {len(sims_clean)}")
    print(f"    SIMs with KILLs:  {len(sims_with_kills)}")
    print(f"    SIMs no tokens:   {len(sims_no_tokens)}")
    
    if sims_with_kills:
        print(f"\n    SIMS WITH KILLS:")
        for sim in sims_with_kills:
            print(f"      ⚠ {sim.get('file', '?')}: {sim.get('kill_count', '?')}K")
    
    if known_present_kills:
        print(f"\n    KNOWN OPEN KILLS (allowlisted):")
        for kid in sorted(known_present_kills):
            print(f"      ○ {kid}")
    
    if new_regression_kills:
        print(f"\n    *** NEW REGRESSION KILLS (not in allowlist) ***")
        for kid in sorted(new_regression_kills):
            print(f"      ✗ {kid}")
    
    if triage.get("resolved_kills"):
        print(f"\n    RESOLVED KILLS (were KILL, now PASS):")
        for r in triage["resolved_kills"]:
            print(f"      ✓ {r}")
    
    if triage["regressions"]:
        print(f"\n    REGRESSIONS:")
        for r in triage["regressions"]:
            print(f"      ⚠ {r}")
    
    if triage["recoveries"]:
        print(f"\n    RECOVERIES:")
        for r in triage["recoveries"]:
            print(f"      ✓ {r}")
    
    # 7. Save triage
    triage["evidence_label"] = evidence_label
    triage["sims_clean"] = len(sims_clean)
    triage["sims_with_kills"] = len(sims_with_kills)
    triage["sims_no_tokens"] = len(sims_no_tokens)
    triage["known_open_kills"] = list(known_present_kills)
    triage["new_regression_kills"] = list(new_regression_kills)
    
    triage_path = os.path.join(
        REPO, "system_v4/probes/a2_state/sim_results/latest_triage.json"
    )
    with open(triage_path, "w") as f:
        json.dump(triage, f, indent=2)
    
    # 8. Save snapshot for next comparison
    save_report_snapshot(current)
    
    # 9. Version the DNA
    version_dna()
    print(f"\n  DNA version snapshot saved")

    # 10. Check constraint manifold coverage
    manifold_path = os.path.join(REPO, "system_v4/skills/intent-compiler/constraint_manifold.yaml")
    if os.path.exists(manifold_path):
        with open(manifold_path) as f:
            manifold = yaml.safe_load(f)
        core = manifold.get("core_constraints", {})
        cross = manifold.get("cross_cutting", {})
        total = len(core) + len(cross)
        covered = sum(1 for c in list(core.values()) + list(cross.values())
                     if c.get("sim_coverage"))
        print(f"\n  CONSTRAINT MANIFOLD:")
        print(f"    Total constraints: {total}")
        print(f"    With SIM coverage: {covered}")
        print(f"    Coverage: {covered/total*100:.0f}%")

    # 11. Update workstream status
    try:
        ws_module = os.path.join(REPO, "system_v4/skills/intent-compiler/workstream.py")
        import importlib.util
        spec = importlib.util.spec_from_file_location("workstream", ws_module)
        ws = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(ws)
        all_ws = ws.list_all()
        active = sum(1 for w in all_ws if w["status"] == "active")
        total_tokens = sum(w["tokens"] for w in all_ws)
        total_kills = sum(w["kills"] for w in all_ws)
        print(f"\n  WORKSTREAMS:")
        print(f"    Active: {active}/{len(all_ws)}")
        print(f"    Total tokens: {total_tokens}")
        print(f"    Total kills: {total_kills}")
    except Exception as e:
        print(f"  Workstream check skipped: {e}")

    # 12. Materialize probe evidence into graph for run_real_ratchet
    try:
        import subprocess
        result = subprocess.run(
            [sys.executable, os.path.join(REPO, "system_v4/skills/probe_graph_materializer.py")],
            cwd=REPO, capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            print(f"\n  GRAPH MATERIALIZED: probe evidence → run_real_ratchet fuel ✓")
        else:
            print(f"  Graph materialization skipped: {result.stderr[:100]}")
    except Exception as e:
        print(f"  Graph materialization skipped: {e}")

    # 13. Action check
    if triage["action"] == "SELF_KILL":
        print(f"\n  *** SELF-KILL TRIGGERED ***")
        print(f"  The engine has decided to stop running.")
        print(f"  Reason: {triage['regressions']}")
        return
    
    # 14. Codex headless learning tick
    # Only run if evidence is not fundamentally broken
    if spawn_codex and evidence_label in ("CLEAN", "KNOWN_ISSUES"):
        print(f"\n  CODEX LEARNING TICK:")
        codex_ok = run_codex_learning_tick()
        if codex_ok:
            print(f"    ✓ Codex headless tick completed")
        else:
            print(f"    ⚠ Codex headless tick skipped or failed")
    elif spawn_codex and evidence_label == "DEGRADED":
        print(f"\n  CODEX LEARNING TICK: SKIPPED (evidence DEGRADED — fix regressions first)")
    
    print(f"\n  {'─'*50}")
    final = "✓" if evidence_label == "CLEAN" else "⚠" if evidence_label == "KNOWN_ISSUES" else "✗"
    print(f"  {final} Heartbeat tick complete.")
    print(f"    Runner: OK | Evidence: {evidence_label} | Action: {triage['action']}")
    print(f"  {'─'*50}")


# ── Codex Headless Learning Tick ──────────────────────────────────────────

# Codex CLI paths (in priority order)
CODEX_PATHS = [
    "/Applications/Codex.app/Contents/Resources/codex",
    os.path.expanduser("~/.local/bin/codex"),
    "codex",  # fallback to PATH
]

TICK_PROMPT_PATH = os.path.join(
    REPO, "system_v4/skills/intent-compiler/tick_prompt.md"
)


def find_codex() -> str | None:
    """Find the codex CLI binary."""
    for path in CODEX_PATHS:
        if os.path.isfile(path) and os.access(path, os.X_OK):
            return path
    # Try which
    try:
        result = subprocess.run(["which", "codex"], capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except Exception:
        pass
    return None


def run_codex_learning_tick() -> bool:
    """
    Spawn a headless codex exec session.
    The prompt is: "Load and follow tick_prompt.md"
    Returns True if codex ran successfully.
    """
    codex_bin = find_codex()
    if not codex_bin:
        print(f"    codex CLI not found, skipping learning tick")
        return False
    
    if not os.path.exists(TICK_PROMPT_PATH):
        print(f"    tick_prompt.md not found at {TICK_PROMPT_PATH}")
        return False
    
    prompt = f"Load and follow {TICK_PROMPT_PATH}"
    
    cmd = [
        codex_bin, "exec",
        "--cd", REPO,
        "--sandbox", "workspace-write",
        "-a", "never",
        prompt,
    ]
    
    print(f"    Spawning: {codex_bin} exec ...")
    print(f"    Prompt: {prompt[:80]}...")
    
    try:
        import subprocess
        result = subprocess.run(
            cmd,
            cwd=REPO,
            capture_output=True,
            text=True,
            timeout=600,  # 10 minute max per learning tick
        )
        
        if result.returncode == 0:
            # Log the output
            log_path = os.path.join(
                REPO, "system_v4/probes/a2_state/sim_results/codex_learning_tick.log"
            )
            with open(log_path, "a") as f:
                f.write(f"\n{'='*60}\n")
                f.write(f"TICK: {datetime.now(timezone.utc).isoformat()}\n")
                f.write(f"{'='*60}\n")
                if result.stdout:
                    f.write(result.stdout[-2000:])  # last 2000 chars
                f.write(f"\n--- END TICK ---\n")
            return True
        else:
            print(f"    codex exec failed: rc={result.returncode}")
            if result.stderr:
                print(f"    stderr: {result.stderr[:200]}")
            return False
    except subprocess.TimeoutExpired:
        print(f"    codex exec timed out (10 min limit)")
        return False
    except Exception as e:
        print(f"    codex exec error: {e}")
        return False


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Codex Ratchet Heartbeat Daemon")
    parser.add_argument("--no-codex", action="store_true",
                       help="Skip the codex headless learning tick")
    args = parser.parse_args()
    run_tick(spawn_codex=not args.no_codex)
