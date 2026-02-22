import argparse
import hashlib
import json
import os
import subprocess
import time
from pathlib import Path

try:
    from a0_generator_v2 import generate_export_block
except ImportError:
    from a0_generator import generate_export_block
from b_kernel import BKernel
from state import KernelState
from a1_protocol import load_strategy, expand_strategy, compile_batch
from zip_protocol import create_zip
from feedback import run_feedback
from fuel_cursor import load_fuel_cursor, save_fuel_cursor
from a1_seed_strategy import fuel_to_strategy
DEFAULT_RUN_DIR = os.path.join("runs", "ratchet_v2")
LOG_SHARD_BYTES = 2_000_000
OUTBOX_SHARD_BYTES = 2_000_000
MANIFEST_SHARD_BYTES = 2_000_000
def _sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()
def _load_context(repo_root, log_fn):
    if log_fn:
        log_fn({"event": "context_loaded", "files": {}})
    return {}
def _ensure_run_dir(run_dir):
    Path(run_dir).mkdir(parents=True, exist_ok=True)
def _state_path(run_dir):
    return os.path.join(run_dir, "state.json")
def _log_writer(run_dir):
    _ensure_run_dir(run_dir)
    seq = {"n": 0}
    shard = {"n": 0}

    def _current_path():
        return os.path.join(run_dir, f"events.{shard['n']:03d}.jsonl")

    def _rotate_if_needed():
        path = _current_path()
        if os.path.exists(path) and os.path.getsize(path) >= LOG_SHARD_BYTES:
            shard["n"] += 1

    def _log(event):
        seq["n"] += 1
        _rotate_if_needed()
        payload = {"seq": seq["n"], **event}
        with open(_current_path(), "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n")

    return _log


def _write_outbox(run_dir, block_text):
    outbox = Path(run_dir) / "outbox"
    outbox.mkdir(parents=True, exist_ok=True)
    meta_path = outbox / "manifest.json"
    if meta_path.exists():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    else:
        meta = {"next_index": 1, "shard": 0}

    record_index = int(meta.get("next_index", 1))
    shard = int(meta.get("shard", 0))
    payload = (
        f"BEGIN EXPORT_RECORD {record_index:08d}\n"
        f"{block_text.rstrip()}\n"
        f"END EXPORT_RECORD {record_index:08d}\n\n"
    )

    shard_path = outbox / f"export_blocks.{shard:03d}.txt"
    if shard_path.exists() and shard_path.stat().st_size + len(payload.encode("utf-8")) > OUTBOX_SHARD_BYTES:
        shard += 1
        shard_path = outbox / f"export_blocks.{shard:03d}.txt"
    with shard_path.open("a", encoding="utf-8") as f:
        f.write(payload)

    meta["next_index"] = record_index + 1
    meta["shard"] = shard
    meta_path.write_text(json.dumps(meta, sort_keys=True, separators=(",", ":")), encoding="utf-8")
    return shard_path, record_index
def init_state(run_dir, repo_root):
    log_fn = _log_writer(run_dir)
    _load_context(repo_root, log_fn)
    state = KernelState()
    state.add_axiom("F01_FINITUDE", "AXIOM_HYP", ["AXIOM_HYP F01_FINITUDE"])
    state.add_axiom("N01_NONCOMMUTATION", "AXIOM_HYP", ["AXIOM_HYP N01_NONCOMMUTATION"])
    fuel_path = Path(repo_root) / "work" / "a2_state" / "fuel_queue.json"
    pool_count = state.seed_pool_from_fuel(fuel_path) if fuel_path.exists() else 0
    with open(_state_path(run_dir), "w", encoding="utf-8") as f:
        f.write(state.to_json())
    log_fn({"event": "init", "state_hash": state.hash(), "pool_seeded": pool_count})


def run_once(run_dir, repo_root, max_specs=6):
    log_fn = _log_writer(run_dir)
    _load_context(repo_root, log_fn)
    state_file = _state_path(run_dir)
    if os.path.exists(state_file):
        with open(state_file, "r", encoding="utf-8") as f:
            state = KernelState.from_json(f.read())
    else:
        state = KernelState()
    bootpack_path = os.path.join(repo_root, "core_docs", "BOOTPACK_THREAD_B_v3.9.13.md")
    kernel = BKernel(bootpack_path)
    kernel.manifest_dir = str(Path(run_dir) / "sim_manifests")
    kernel.manifest_ledger_dir = str(Path(run_dir) / "sim")
    block = generate_export_block(state, max_specs=max_specs, run_dir=run_dir)
    out_path, record_index = _write_outbox(run_dir, block)
    log_fn({"event": "outbox_write", "path": str(out_path), "record_index": record_index})
    log_fn({"event": "a0_batch", "bytes": len(block)})
    kernel.evaluate_export_block(block, state, log_fn=log_fn)
    with open(state_file, "w", encoding="utf-8") as f:
        f.write(state.to_json())
    log_fn({"event": "run_once", "state_hash": state.hash()})
    summary = {
        "state_hash": state.hash(),
        "survivor_count": len(state.survivor_order),
        "term_count": len(state.terms),
        "probe_count": state.probe_count,
        "parked_count": len(state.parked),
        "pending_count": len(state.evidence_pending),
    }
    print(json.dumps(summary, sort_keys=True, separators=(",", ":")))


def run_sim_test(run_dir, repo_root):
    log_fn = _log_writer(run_dir)
    _load_context(repo_root, log_fn)
    state_file = _state_path(run_dir)
    if os.path.exists(state_file):
        with open(state_file, "r", encoding="utf-8") as f:
            state = KernelState.from_json(f.read())
    else:
        state = KernelState()
    bootpack_path = os.path.join(repo_root, "core_docs", "BOOTPACK_THREAD_B_v3.9.13.md")
    kernel = BKernel(bootpack_path)
    kernel.manifest_dir = str(Path(run_dir) / "sim_manifests")
    kernel.manifest_ledger_dir = str(Path(run_dir) / "sim")
    target_spec = None
    target_token = None
    if state.evidence_pending:
        target_spec = sorted(state.evidence_pending.keys())[0]
        pending = state.evidence_pending.get(target_spec, set())
        if pending:
            target_token = sorted(list(pending))[0]
    sim_id = target_spec or "S_NULL"
    code_hash = "0" * 64
    output_hash = _sha256_bytes(b"sim_output")
    input_hash = _sha256_bytes(b"sim_input")
    manifest_hash = _write_manifest(Path(run_dir), {
        "sim_id": sim_id,
        "code_hash_sha256": code_hash,
        "output_hash_sha256": output_hash,
        "input_hash_sha256": input_hash,
    })
    sim_text = "\n".join([
        "BEGIN SIM_EVIDENCE v1",
        f"SIM_ID: {sim_id}",
        f"CODE_HASH_SHA256: {code_hash}",
        f"OUTPUT_HASH_SHA256: {output_hash}",
        f"INPUT_HASH_SHA256: {input_hash}",
        f"RUN_MANIFEST_SHA256: {manifest_hash}",
        f"EVIDENCE_SIGNAL {target_spec or 'S_NULL'} CORR {target_token or 'EV_NULL'}",
        "END SIM_EVIDENCE v1",
        "",
    ])
    kernel.ingest_sim_evidence(sim_text, state, log_fn=log_fn)
    with open(state_file, "w", encoding="utf-8") as f:
        f.write(state.to_json())
    evidence_map = {}
    for spec_id in sorted(state.specs.keys()):
        ev = state.specs[spec_id].get("evidence_tokens", set())
        evidence_map[spec_id] = sorted(list(ev))
    output = {
        "state_hash": state.hash(),
        "evidence_tokens": evidence_map,
        "pending_count": len(state.evidence_pending),
    }
    print(json.dumps(output, sort_keys=True, separators=(",", ":")))


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_sim_binding():
    binding_path = Path(__file__).resolve().parent / "constraint_sim_binding.json"
    if not binding_path.exists():
        return {}
    try:
        return json.loads(binding_path.read_text())
    except Exception:
        return {}


def _write_manifest(run_dir: Path, payload: dict) -> str:
    sim_dir = run_dir / "sim"
    sim_dir.mkdir(parents=True, exist_ok=True)
    payload_data = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    digest = _sha256_bytes(payload_data)

    meta_path = sim_dir / "manifest_ledger_meta.json"
    if meta_path.exists():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    else:
        meta = {"next_index": 1, "shard": 0}

    record_index = int(meta.get("next_index", 1))
    shard = int(meta.get("shard", 0))
    row = {"manifest_sha256": digest, "record_index": record_index, **payload}
    row_text = json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n"

    shard_path = sim_dir / f"manifests.{shard:03d}.jsonl"
    if shard_path.exists() and shard_path.stat().st_size + len(row_text.encode("utf-8")) > MANIFEST_SHARD_BYTES:
        shard += 1
        shard_path = sim_dir / f"manifests.{shard:03d}.jsonl"
    with shard_path.open("a", encoding="utf-8") as fh:
        fh.write(row_text)

    meta["next_index"] = record_index + 1
    meta["shard"] = shard
    meta_path.write_text(json.dumps(meta, sort_keys=True, separators=(",", ":")), encoding="utf-8")
    return digest


def _execute_sim(script_file: Path, sim_id: str, target_spec: str, target_token: str, run_dir: Path, repo_root: Path):
    code_hash = _sha256_file(script_file)
    cmd = ["python3", str(script_file)]
    env = os.environ.copy()
    env["TARGET_SPEC"] = target_spec
    env["TARGET_TOKEN"] = target_token
    env["RUN_DIR"] = str(run_dir)
    proc = subprocess.run(cmd, cwd=str(repo_root), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=False, env=env)
    stdout_bytes = proc.stdout or b""
    stderr_bytes = proc.stderr or b""
    output_hash = _sha256_bytes(stdout_bytes + stderr_bytes)
    input_payload = {
        "target_spec": target_spec,
        "target_token": target_token,
        "script_path": str(script_file.relative_to(repo_root)),
        "args": [],
    }
    input_hash = _sha256_bytes(json.dumps(input_payload, sort_keys=True).encode("utf-8"))
    manifest_hash = _write_manifest(run_dir, {
        "sim_id": sim_id,
        "script_path": str(script_file.relative_to(repo_root)),
        "command_line": cmd,
        "target_spec": target_spec,
        "target_token": target_token,
        "code_hash_sha256": code_hash,
        "output_hash_sha256": output_hash,
        "input_hash_sha256": input_hash,
        "stdout_sha256": _sha256_bytes(stdout_bytes),
        "stderr_sha256": _sha256_bytes(stderr_bytes),
        "exit_code": proc.returncode,
    })
    return {
        "exit_code": proc.returncode,
        "code_hash": code_hash,
        "output_hash": output_hash,
        "input_hash": input_hash,
        "manifest_hash": manifest_hash,
    }


def _pick_sim_for_spec(spec_id: str, spec_kind: str, repo_root: Path, binding: dict):
    entry = binding.get(spec_id)
    if entry and entry.get("sim_path"):
        candidate = Path(repo_root) / entry["sim_path"]
        if candidate.exists():
            return candidate, entry.get("sim_id")
    # Generic fallbacks for terms without dedicated sim implementations.
    sims_dir = Path(repo_root) / "work" / "ratchet_core" / "sims"
    if spec_id.startswith("SIM_TERM_"):
        generic = sims_dir / "sim_term_generic.py"
        if generic.exists():
            return generic, "SIM_TERM_GENERIC"
    if spec_id.startswith("SIM_MATH_"):
        generic_math = sims_dir / "sim_math_generic.py"
        if generic_math.exists():
            return generic_math, "SIM_MATH_GENERIC"
    if spec_id.startswith("SIM_NEG_MATH_"):
        generic_math_neg = sims_dir / "sim_math_generic_negative.py"
        if generic_math_neg.exists():
            return generic_math_neg, "SIM_MATH_GENERIC_NEGATIVE"
    if spec_id.startswith("SIM_NEG_"):
        generic_neg = sims_dir / "sim_term_generic_negative.py"
        if generic_neg.exists():
            return generic_neg, "SIM_TERM_GENERIC_NEGATIVE"
    if not sims_dir.exists():
        return None, None
    normalized = spec_id.lower().replace("sim_term_", "").replace("sim_", "")
    for sim_file in sorted(sims_dir.glob("sim_*.py")):
        sim_name = sim_file.stem.replace("sim_", "")
        if sim_name == normalized or sim_name in normalized:
            return sim_file, sim_file.stem
    return None, None


def _run_pending_sims(state, kernel, binding, repo_root_path, run_dir_path, sim_cap, log_fn):
    """Run sims for specs with pending evidence. Shared by run_cycle and run_full_cycle."""
    pending = sorted(state.evidence_pending.keys())
    if not pending:
        log_fn({"event": "sim_skip", "reason": "NO_PENDING"})
        return 0
    sims_run = 0
    for spec_id in pending:
        if sims_run >= sim_cap:
            break
        pending_tokens = sorted(list(state.evidence_pending.get(spec_id, set())))
        if not pending_tokens:
            continue
        token = pending_tokens[0]
        spec = state.specs.get(spec_id, {})
        script_file, sim_id = _pick_sim_for_spec(
            spec_id, spec.get("kind"), repo_root_path, binding)
        if not script_file or not script_file.exists():
            log_fn({"event": "sim_skip", "spec": spec_id, "reason": "NO_SIM"})
            continue
        sim_id_final = sim_id or script_file.stem
        result = _execute_sim(
            script_file, sim_id_final, spec_id, token, run_dir_path, repo_root_path)
        log_fn({"event": "sim_run", "spec": spec_id, "sim_id": sim_id_final, **result})
        if result["exit_code"] != 0:
            state.graveyard.append({
                "id": spec_id, "reason": "SIM_FAIL",
                "exit_code": result["exit_code"]})
            state.evidence_pending.pop(spec_id, None)
            if spec_id in state.specs:
                state.specs[spec_id]["status"] = "FAILED_SIM"
        else:
            sim_text = "\n".join([
                "BEGIN SIM_EVIDENCE v1",
                f"SIM_ID: {sim_id_final}",
                f"CODE_HASH_SHA256: {result['code_hash']}",
                f"OUTPUT_HASH_SHA256: {result['output_hash']}",
                f"INPUT_HASH_SHA256: {result['input_hash']}",
                f"RUN_MANIFEST_SHA256: {result['manifest_hash']}",
                f"EVIDENCE_SIGNAL {spec_id} CORR {token}",
                "END SIM_EVIDENCE v1",
                "",
            ])
            ok = kernel.ingest_sim_evidence(sim_text, state, log_fn=log_fn)
            if ok:
                state.sim_run_count += 1
                if spec_id.startswith("SIM_NEG_"):
                    kill_id = f"ALT_{spec_id}"
                    if not any(
                        g.get("id") == kill_id and g.get("reason") == "SIM_NEGATIVE_BASELINE"
                        for g in state.graveyard
                    ):
                        state.graveyard.append({
                            "id": kill_id,
                            "reason": "SIM_NEGATIVE_BASELINE",
                            "raw_lines": [
                                f"SIM_SOURCE {spec_id}",
                                f"EVIDENCE_TOKEN {token}",
                            ],
                        })
                    log_fn({"event": "sim_kill", "id": kill_id, "source": spec_id})
        sims_run += 1
    return sims_run


def run_cycle(run_dir, repo_root, sim_cap=3, max_specs=6):
    log_fn = _log_writer(run_dir)
    _load_context(repo_root, log_fn)
    state_file = _state_path(run_dir)
    if os.path.exists(state_file):
        with open(state_file, "r", encoding="utf-8") as f:
            state = KernelState.from_json(f.read())
    else:
        state = KernelState()
    bootpack_path = os.path.join(repo_root, "core_docs", "BOOTPACK_THREAD_B_v3.9.13.md")
    kernel = BKernel(bootpack_path)
    kernel.manifest_dir = str(Path(run_dir) / "sim_manifests")
    kernel.manifest_ledger_dir = str(Path(run_dir) / "sim")

    block = generate_export_block(state, max_specs=max_specs, run_dir=run_dir)
    out_path, record_index = _write_outbox(run_dir, block)
    log_fn({"event": "outbox_write", "path": str(out_path), "record_index": record_index})
    log_fn({"event": "a0_batch", "bytes": len(block)})
    kernel.evaluate_export_block(block, state, log_fn=log_fn)
    with open(state_file, "w", encoding="utf-8") as f:
        f.write(state.to_json())

    if not state.evidence_pending:
        log_fn({"event": "sim_skip", "reason": "NO_PENDING"})
        print(json.dumps({"status": "NO_PENDING", "state_hash": state.hash()},
                         sort_keys=True, separators=(",", ":")))
        return

    binding = _load_sim_binding()
    _run_pending_sims(state, kernel, binding,
                      Path(repo_root), Path(run_dir), sim_cap, log_fn)

    with open(state_file, "w", encoding="utf-8") as f:
        f.write(state.to_json())

    summary = {
        "state_hash": state.hash(),
        "survivor_count": len(state.survivor_order),
        "term_count": len(state.terms),
        "probe_count": state.probe_count,
        "parked_count": len(state.parked),
        "pending_count": len(state.evidence_pending),
    }
    print(json.dumps(summary, sort_keys=True, separators=(",", ":")))


def run_full_cycle(run_dir, repo_root, strategy_path=None, fuel_path=None,
                   sim_cap=3, max_entries=20, max_items=1000):
    """Full pipeline: A2 fuel -> A1 strategy -> expand -> B -> SIM -> feedback."""
    log_fn = _log_writer(run_dir)
    run_dir_path = Path(run_dir)
    repo_root_path = Path(repo_root)
    state_file = _state_path(run_dir)

    if os.path.exists(state_file):
        with open(state_file, "r", encoding="utf-8") as f:
            state = KernelState.from_json(f.read())
    else:
        state = KernelState()

    if strategy_path:
        strategy = load_strategy(Path(strategy_path))
        log_fn({"event": "strategy_loaded", "path": strategy_path})
    else:
        fp = fuel_path or os.path.join(repo_root, "work", "a2_state", "fuel_queue.json")
        cursor = load_fuel_cursor(run_dir)
        strategy, next_cursor, total_entries = fuel_to_strategy(
            fp, state, max_entries=max_entries, start=cursor, repo_root=repo_root)
        save_fuel_cursor(run_dir, next_cursor)
        meta = strategy.get("_meta", {}) if isinstance(strategy, dict) else {}
        log_fn({"event": "strategy_generated", "fuel_path": fp,
                "fuel_cursor": cursor, "fuel_cursor_next": next_cursor,
                "fuel_total_entries": total_entries,
                "terms": len(strategy["terms_to_admit"]),
                "math_defs": len(strategy["math_defs"]),
                "hard_reject_ratio": meta.get("hard_reject_ratio", 0.0),
                "suppress_new_math_defs": bool(meta.get("suppress_new_math_defs", False))})

    create_zip("A1_STRATEGY", "A1_LLM", "A1_EXPANDER", strategy,
               out_dir=run_dir_path / "zips")

    items = expand_strategy(strategy, state, max_items=max_items)
    if not items:
        log_fn({"event": "expand_empty"})
        print(json.dumps({"status": "EXPAND_EMPTY", "state_hash": state.hash()},
                         sort_keys=True, separators=(",", ":")))
        return

    block = compile_batch(items, state)
    create_zip("A1_BATCH", "A1_EXPANDER", "A0",
               {"item_count": len(items), "block_bytes": len(block)},
               out_dir=run_dir_path / "zips")
    out_path, record_index = _write_outbox(run_dir, block)
    log_fn({"event": "outbox_write", "path": str(out_path), "record_index": record_index})
    log_fn({"event": "a1_batch", "items": len(items), "bytes": len(block)})

    bootpack_path = os.path.join(
        repo_root, "core_docs", "BOOTPACK_THREAD_B_v3.9.13.md")
    kernel = BKernel(bootpack_path)
    kernel.manifest_dir = str(run_dir_path / "sim_manifests")
    kernel.manifest_ledger_dir = str(run_dir_path / "sim")
    kernel.evaluate_export_block(block, state, log_fn=log_fn)

    with open(state_file, "w", encoding="utf-8") as f:
        f.write(state.to_json())

    binding = _load_sim_binding()
    sims_run = _run_pending_sims(
        state, kernel, binding, repo_root_path, run_dir_path, sim_cap, log_fn)

    with open(state_file, "w", encoding="utf-8") as f:
        f.write(state.to_json())

    fb_result = run_feedback(state, a2_state_dir=run_dir_path / "a2_feedback_state")
    create_zip("FEEDBACK", "A1", "A2", fb_result,
               out_dir=run_dir_path / "zips")
    log_fn({"event": "feedback", **fb_result})

    summary = {
        "state_hash": state.hash(),
        "items_expanded": len(items),
        "survivor_count": len(state.survivor_order),
        "term_count": len(state.terms),
        "graveyard_count": len(state.graveyard),
        "graveyard_ratio": fb_result["graveyard_ratio"],
        "sims_run": sims_run,
        "rosetta_added": fb_result["rosetta_terms_added"],
        "pending_count": len(state.evidence_pending),
    }
    print(json.dumps(summary, sort_keys=True, separators=(",", ":")))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--init", action="store_true")
    parser.add_argument("--run-once", action="store_true")
    parser.add_argument("--run-sim-test", action="store_true")
    parser.add_argument("--cycle", action="store_true")
    parser.add_argument("--full-cycle", action="store_true")
    parser.add_argument("--loops", type=int, default=1)
    parser.add_argument("--sim-cap", type=int, default=3)
    parser.add_argument("--max-specs", type=int, default=6)
    parser.add_argument("--max-entries", type=int, default=20)
    parser.add_argument("--max-items", type=int, default=1000)
    parser.add_argument("--strategy", type=str, default=None)
    parser.add_argument("--fuel", type=str, default=None)
    parser.add_argument("--run-dir", default=DEFAULT_RUN_DIR)
    args = parser.parse_args()
    base_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.abspath(os.path.join(base_dir, "..", ".."))
    run_dir = args.run_dir

    if args.init:
        init_state(run_dir, repo_root)
    if args.run_once:
        run_once(run_dir, repo_root, max_specs=args.max_specs)
    if args.run_sim_test:
        run_sim_test(run_dir, repo_root)
    if args.cycle:
        for _ in range(max(1, args.loops)):
            run_cycle(run_dir, repo_root, sim_cap=args.sim_cap, max_specs=args.max_specs)
    if args.full_cycle:
        for _ in range(max(1, args.loops)):
            run_full_cycle(run_dir, repo_root, strategy_path=args.strategy,
                           fuel_path=args.fuel, sim_cap=args.sim_cap,
                           max_entries=args.max_entries, max_items=args.max_items)


if __name__ == "__main__":
    main()
