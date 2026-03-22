"""
Refinery Daemon Runner — Background Process Architecture

A long-running background process that watches for new files and
automatically ingests them through the A2 graph refinery.

Architecture:
  ┌──────────────────────────────────────────────────────┐
  │                  DAEMON PROCESS                      │
  │                                                      │
  │  ┌─────────┐   ┌──────────┐   ┌──────────────────┐  │
  │  │ WATCHER │──▶│  QUEUE   │──▶│  INGESTION LOOP  │  │
  │  │ (fsevt) │   │ (FIFO)   │   │  (deterministic) │  │
  │  └─────────┘   └──────────┘   └──────────────────┘  │
  │       │                              │               │
  │       │ new files                    │ concepts      │
  │       ▼                              ▼               │
  │  ┌─────────┐                  ┌──────────────────┐  │
  │  │ FILTER  │                  │   A2 REFINERY    │  │
  │  │ (.py,   │                  │   (graph ingest) │  │
  │  │  .md,   │                  └──────────────────┘  │
  │  │  .json) │                         │               │
  │  └─────────┘                         ▼               │
  │                               ┌──────────────────┐  │
  │                               │  CHECKPOINT      │  │
  │                               │  (save graph)    │  │
  │                               └──────────────────┘  │
  └──────────────────────────────────────────────────────┘

Key design principles (following JP's determinism-first rule):
  1. The daemon is deterministic — same inputs always produce same graph
  2. LLM extraction is OPTIONAL — daemon can register source docs without LLM
  3. Deep extraction (concept identification) can be deferred to a human pass
  4. File watching uses OS-level events (fsevents on macOS) not polling
  5. Queue is FIFO with dedup by content hash
  6. Contradictions at A2/A1 layers are WANTED — they create heat for refinement
  7. Only B+SIM ratchet resolves contradictions

Run modes:
  --watch     : Watch directories and auto-ingest new files
  --batch DIR : One-shot batch ingestion of a directory
  --status    : Print current daemon state
"""

import argparse
import hashlib
import json
import os
import signal
import sys
import time
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))


# ── File Filter ───────────────────────────────────────────────────────

WATCH_EXTENSIONS = {".py", ".md", ".json", ".txt", ".yaml", ".yml", ".toml"}
IGNORE_PATTERNS = {
    "__pycache__", ".git", "node_modules", ".DS_Store",
    ".pyc", ".pyo", ".egg-info",
}


def should_process(path: Path) -> bool:
    """Determine if a file should be processed by the daemon."""
    if not path.is_file():
        return False
    if path.suffix not in WATCH_EXTENSIONS:
        return False
    for part in path.parts:
        if part in IGNORE_PATTERNS or part.startswith("."):
            return False
    return True


def content_hash(path: Path) -> str:
    """SHA256 of file content for dedup."""
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()[:16]
    except (OSError, PermissionError):
        return ""


# ── Queue ─────────────────────────────────────────────────────────────

@dataclass
class QueueItem:
    path: str
    hash: str
    queued_utc: str
    status: str = "PENDING"  # PENDING, PROCESSING, DONE, ERROR


@dataclass
class DaemonState:
    queue: deque = field(default_factory=deque)
    processed_hashes: set = field(default_factory=set)
    stats: dict = field(default_factory=lambda: {
        "files_queued": 0,
        "files_processed": 0,
        "files_skipped_dedup": 0,
        "concepts_ingested": 0,
        "errors": 0,
        "last_checkpoint_utc": "",
    })
    state_file: str = ""

    def enqueue(self, path: Path) -> bool:
        """Add a file to the queue. Returns False if already processed."""
        h = content_hash(path)
        if not h or h in self.processed_hashes:
            self.stats["files_skipped_dedup"] += 1
            return False
        item = QueueItem(
            path=str(path),
            hash=h,
            queued_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        )
        self.queue.append(item)
        self.stats["files_queued"] += 1
        return True

    def save_state(self):
        if not self.state_file:
            return
        data = {
            "queue": [
                {"path": item.path, "hash": item.hash,
                 "queued_utc": item.queued_utc, "status": item.status}
                for item in self.queue
            ],
            "processed_hashes": sorted(self.processed_hashes),
            "stats": self.stats,
        }
        Path(self.state_file).write_text(
            json.dumps(data, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    @classmethod
    def load_state(cls, state_file: str) -> "DaemonState":
        state = cls(state_file=state_file)
        p = Path(state_file)
        if not p.exists():
            return state
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            for item_data in data.get("queue", []):
                state.queue.append(QueueItem(**item_data))
            state.processed_hashes = set(data.get("processed_hashes", []))
            state.stats.update(data.get("stats", {}))
        except (json.JSONDecodeError, KeyError):
            pass
        return state


# ── Ingestion Loop ────────────────────────────────────────────────────

def process_single_file(state: DaemonState, refinery, item: QueueItem) -> bool:
    """
    Process a single file through the refinery.
    
    This is the DETERMINISTIC part — it registers the file as a source
    document. Deep concept extraction (which may involve LLM) is separate
    and can be run later by a human or scheduled task.
    
    Contradictions at A2/A1 are WANTED — they drive refinement.
    """
    from system_v4.skills.a2_graph_refinery import ExtractionMode

    fpath = Path(item.path)
    if not fpath.exists():
        item.status = "ERROR"
        state.stats["errors"] += 1
        return False

    try:
        batch_id = f"BATCH_DAEMON_{fpath.stem.upper()[:20]}_{item.hash}"
        refinery.ingest_document(
            doc_path=str(fpath),
            extraction_mode=ExtractionMode.SOURCE_MAP,
            batch_id=batch_id,
            concepts=[],  # Source doc registration only — no LLM extraction
        )
        # Mark as SOURCE_REGISTERED, not DONE — deep extraction hasn't happened yet
        item.status = "SOURCE_REGISTERED"
        state.processed_hashes.add(item.hash)
        state.stats["files_processed"] += 1
        return True
    except Exception as exc:
        item.status = "ERROR"
        state.stats["errors"] += 1
        print(f"  ERROR processing {fpath.name}: {exc}", file=sys.stderr)
        return False


def run_batch(directory: str, state: DaemonState):
    """One-shot batch ingestion of all eligible files in a directory."""
    from system_v4.skills.a2_graph_refinery import A2GraphRefinery

    target = Path(directory).resolve()
    if not target.is_dir():
        print(f"Not a directory: {target}", file=sys.stderr)
        return

    # Scan and enqueue
    count = 0
    for fpath in sorted(target.rglob("*")):
        if should_process(fpath):
            if state.enqueue(fpath):
                count += 1
    print(f"Queued {count} new files from {target}")

    if not state.queue:
        print("Nothing to process.")
        return

    # Process queue
    refinery = A2GraphRefinery(str(REPO_ROOT))
    sid = refinery.start_session(f"DAEMON_BATCH_{time.strftime('%Y%m%d_%H%M%S')}")
    print(f"Session: {sid}")

    processed = 0
    while state.queue:
        item = state.queue.popleft()
        if item.status != "PENDING":
            continue
        item.status = "PROCESSING"
        success = process_single_file(state, refinery, item)
        if success:
            processed += 1
        if processed % 50 == 0 and processed > 0:
            refinery.checkpoint()
            state.save_state()
            print(f"  Checkpoint at {processed} files")

    log_path = refinery.end_session()
    state.stats["last_checkpoint_utc"] = time.strftime(
        "%Y-%m-%dT%H:%M:%SZ", time.gmtime()
    )
    state.save_state()

    print(f"\nBatch complete: {processed} files processed")
    print(f"Graph: {len(refinery.builder.pydantic_model.nodes)} nodes, "
          f"{len(refinery.builder.pydantic_model.edges)} edges")
    if log_path:
        print(f"Session log: {log_path}")


def run_watch(directories: list[str], state: DaemonState):
    """
    Watch directories for changes using polling (cross-platform).
    
    For production, this should be replaced with:
    - macOS: fsevents via watchdog
    - Linux: inotify via watchdog  
    - Both: `pip install watchdog` then use Observer + FileSystemEventHandler
    
    The polling fallback here works without dependencies.
    """
    from system_v4.skills.a2_graph_refinery import A2GraphRefinery

    targets = [Path(d).resolve() for d in directories]
    poll_interval = 30  # seconds

    print(f"Daemon watching {len(targets)} directories (poll every {poll_interval}s)")
    print("Press Ctrl+C to stop.\n")

    refinery = A2GraphRefinery(str(REPO_ROOT))
    sid = refinery.start_session(f"DAEMON_WATCH_{time.strftime('%Y%m%d_%H%M%S')}")

    # Track file mtimes for change detection
    known_mtimes: dict[str, float] = {}

    running = True

    def handle_signal(signum, frame):
        nonlocal running
        running = False
        print("\nShutting down daemon...")

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    cycle = 0
    while running:
        cycle += 1
        new_files = []

        for target in targets:
            for fpath in target.rglob("*"):
                if not should_process(fpath):
                    continue
                key = str(fpath)
                try:
                    mtime = fpath.stat().st_mtime
                except OSError:
                    continue
                if key not in known_mtimes or known_mtimes[key] < mtime:
                    known_mtimes[key] = mtime
                    if state.enqueue(fpath):
                        new_files.append(fpath.name)

        if new_files:
            print(f"[cycle {cycle}] {len(new_files)} new/changed files detected")
            while state.queue:
                item = state.queue.popleft()
                if item.status != "PENDING":
                    continue
                item.status = "PROCESSING"
                success = process_single_file(state, refinery, item)
                if success:
                    print(f"  Ingested: {Path(item.path).name}")

            refinery.checkpoint()
            state.save_state()

        # Sleep in small increments so signal handling is responsive
        for _ in range(poll_interval):
            if not running:
                break
            time.sleep(1)

    # Clean shutdown
    state.stats["last_checkpoint_utc"] = time.strftime(
        "%Y-%m-%dT%H:%M:%SZ", time.gmtime()
    )
    state.save_state()
    log_path = refinery.end_session()
    print(f"Daemon stopped. Session log: {log_path}")
    print(f"Graph: {len(refinery.builder.pydantic_model.nodes)} nodes, "
          f"{len(refinery.builder.pydantic_model.edges)} edges")


def print_status(state: DaemonState):
    """Print current daemon state."""
    print("Refinery Daemon Status:")
    print(f"  Files queued:       {state.stats['files_queued']}")
    print(f"  Files processed:    {state.stats['files_processed']}")
    print(f"  Files skipped:      {state.stats['files_skipped_dedup']}")
    print(f"  Concepts ingested:  {state.stats['concepts_ingested']}")
    print(f"  Errors:             {state.stats['errors']}")
    print(f"  Last checkpoint:    {state.stats['last_checkpoint_utc'] or 'never'}")
    print(f"  Pending in queue:   {sum(1 for i in state.queue if i.status == 'PENDING')}")
    print(f"  Processed hashes:   {len(state.processed_hashes)}")


# ── CLI ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Refinery Daemon — background file ingestion into A2 graph"
    )
    parser.add_argument(
        "--watch", nargs="+", metavar="DIR",
        help="Watch directories for new files and auto-ingest"
    )
    parser.add_argument(
        "--batch", metavar="DIR",
        help="One-shot batch ingestion of a directory"
    )
    parser.add_argument(
        "--status", action="store_true",
        help="Print current daemon state"
    )
    parser.add_argument(
        "--state-file", default=str(
            REPO_ROOT / "system_v4" / "a2_state" / "daemon_state.json"
        ),
        help="Path to daemon state file"
    )

    args = parser.parse_args()
    state = DaemonState.load_state(args.state_file)

    if args.status:
        print_status(state)
    elif args.batch:
        run_batch(args.batch, state)
    elif args.watch:
        run_watch(args.watch, state)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
