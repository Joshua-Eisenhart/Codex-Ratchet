import json
import time
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional

class A2PersistentBrain:
    """
    Manages the A2 Persistent Brain and Context Seal mechanics for System V4.
    Adheres strictly to the V3-defined `19_A2_PERSISTENT_BRAIN_AND_CONTEXT_SEAL_CONTRACT.md`,
    adapted for the V4 `system_v4/a2_state/` paths.
    
    This skill ensures that 'hot' A2 LLM threads can dump their active context
    into an append-only memory log and 'Seal' their progress, allowing a fresh
    thread to boot up with a cold, distilled representation of the system state
    wihout losing the historical constraint graph or drifting into classical mechanics.
    """

    def __init__(self, workspace_root: str):
        self.workspace_root = Path(workspace_root).resolve()
        self.a2_state_dir = self.workspace_root / "system_v4" / "a2_state"
        self.memory_log_path = self.a2_state_dir / "memory.jsonl"
        self.seal_log_path = self.a2_state_dir / "thread_seals.000.jsonl"
        
        # Ensure directories exist
        self.a2_state_dir.mkdir(parents=True, exist_ok=True)

    def _utc_iso(self) -> str:
        """Returns current time in strict ISO-8601 UTC format."""
        return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    def _sha256_dict(self, data: Dict[str, Any]) -> str:
        """Returns a deterministic SHA256 of a dictionary."""
        # Ensure stable sort
        json_str = json.dumps(data, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(json_str.encode("utf-8")).hexdigest()

    def _append_jsonl(self, file_path: Path, entry: Dict[str, Any]) -> None:
        """Deterministically formats and appends a single JSON object to a JSONL file."""
        file_path.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(entry, sort_keys=True, separators=(",", ":")) + "\n"
        with file_path.open("a", encoding="utf-8") as f:
            f.write(line)

    def _get_next_entry_id(self, file_path: Path) -> int:
        """Retrieves the monotonic lexical ID for the next append entry."""
        if not file_path.exists():
            return 1
            
        count = 0
        with file_path.open("r", encoding="utf-8") as f:
            for _ in f:
                count += 1
        return count + 1

    def append_memory_event(self, 
                            entry_type: str, 
                            content: Any, 
                            source_refs: Optional[list[Dict[str, str]]] = None,
                            tags: Optional[list[str]] = None) -> Dict[str, Any]:
        """
        Appends a general memory event to memory.jsonl.
        Conforms to A2_MEMORY_ENTRY_v1 schema.
        """
        entry_id = self._get_next_entry_id(self.memory_log_path)
        
        event = {
            "schema": "A2_MEMORY_ENTRY_v1",
            "entry_id": f"{entry_id:08d}",
            "ts_utc": self._utc_iso(),
            "entry_type": entry_type,
            "content": content,
            "source_refs": source_refs or [],
            "tags": tags or []
        }
        
        self._append_jsonl(self.memory_log_path, event)
        return event

    def seal_context(self, 
                     source_thread_id: str,
                     pending_actions: list[str], 
                     next_read_set: list[str],
                     state_digest_hash: str) -> Dict[str, Any]:
        """
        Issues a formal A2 Context Seal.
        Records the exact termination point of an A2 thread, appending a record
        to thread_seals.000.jsonl to allow the next thread to pick up exactly
        where the last one left off without narrative drift.
        Conforms to A2_SEAL_RECORD_v1.
        """
        seal_id = self._get_next_entry_id(self.seal_log_path)
        
        # Read the head of the memory log to bind the seal
        head_entry_id = "00000000"
        head_hash = "none"
        
        if self.memory_log_path.exists():
            with self.memory_log_path.open("r", encoding="utf-8") as f:
                lines = f.readlines()
                if lines:
                    last_line = lines[-1].strip()
                    try:
                        last_obj = json.loads(last_line)
                        head_entry_id = last_obj.get("entry_id", "00000000")
                        head_hash = hashlib.sha256(last_line.encode("utf-8")).hexdigest()
                    except json.JSONDecodeError:
                        pass
        
        seal_record = {
            "schema": "A2_SEAL_RECORD_v1",
            "seal_id": f"SEAL_V4_{seal_id:08d}",
            "ts_utc": self._utc_iso(),
            "source_thread_id": source_thread_id,
            "source_memory_head_entry_id": head_entry_id,
            "source_memory_head_hash": head_hash,
            "pending_actions": pending_actions,
            "next_read_set": next_read_set,
            "state_digest_hash": state_digest_hash
        }
        
        self._append_jsonl(self.seal_log_path, seal_record)
        
        # Also log the seal event in the main memory log
        self.append_memory_event(
            entry_type="CONTEXT_SEALED",
            content={"seal_id": seal_record["seal_id"], "reason": "Thread context rotation initiated."},
            tags=["CONTEXT_ROTATION", "SEAL"]
        )
        
        return seal_record
