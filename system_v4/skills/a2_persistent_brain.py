import json
import time
import hashlib
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from collections import Counter


class A2PersistentBrain:
    """
    A2 Persistent Brain for System V4.

    Implements the v3-defined 19_A2_PERSISTENT_BRAIN_AND_CONTEXT_SEAL_CONTRACT.md,
    adapted for v4 paths.  The brain gives any thread — hot or cold — a
    deterministic, file-backed understanding of the system state without
    depending on LLM context.

    Core surfaces (all under system_v4/a2_state/):
        memory.jsonl              – append-only event log
        thread_seals.000.jsonl    – context seal records
        doc_index_v4.json         – deterministic file index
        system_state_report.json  – boot-time system snapshot
        graphs/system_architecture_v1.json – the real system graph
    """

    # ── sharding limits (from spec 19) ──────────────────────────────────────
    MAX_BYTES_PER_SHARD = 65536
    MAX_LINES_PER_SHARD = 2000

    def __init__(self, workspace_root: str):
        self.workspace_root = Path(workspace_root).resolve()
        self.a2_state_dir = self.workspace_root / "system_v4" / "a2_state"
        self.memory_log_path = self.a2_state_dir / "memory.jsonl"
        self.seal_log_path = self.a2_state_dir / "thread_seals.000.jsonl"
        self.doc_index_path = self.a2_state_dir / "doc_index_v4.json"
        self.system_state_path = self.a2_state_dir / "system_state_report.json"
        self.system_graph_path = (
            self.a2_state_dir / "graphs" / "system_architecture_v1.json"
        )

        self.a2_state_dir.mkdir(parents=True, exist_ok=True)

        # Loaded lazily
        self._system_graph: Optional[Dict[str, Any]] = None

    # ── time / hash helpers ─────────────────────────────────────────────────
    @staticmethod
    def _utc_iso() -> str:
        return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    @staticmethod
    def _sha256_dict(data: Dict[str, Any]) -> str:
        raw = json.dumps(data, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(raw.encode()).hexdigest()

    @staticmethod
    def _sha256_file(path: Path) -> str:
        h = hashlib.sha256()
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()

    # ── low-level I/O ───────────────────────────────────────────────────────
    def _append_jsonl(self, file_path: Path, entry: Dict[str, Any]) -> None:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(entry, sort_keys=True, separators=(",", ":")) + "\n"
        with file_path.open("a", encoding="utf-8") as f:
            f.write(line)

    def _get_next_entry_id(self, file_path: Path) -> int:
        if not file_path.exists():
            return 1
        count = 0
        with file_path.open("r", encoding="utf-8") as f:
            for _ in f:
                count += 1
        return count + 1

    # ── 1. SYSTEM GRAPH AWARENESS ───────────────────────────────────────────
    def load_system_graph(self) -> Dict[str, Any]:
        """Load the real system architecture graph."""
        if self._system_graph is not None:
            return self._system_graph

        if not self.system_graph_path.exists():
            self._system_graph = {"nodes": {}, "edges": [], "stats": {}}
            return self._system_graph

        with self.system_graph_path.open() as f:
            self._system_graph = json.load(f)
        return self._system_graph

    def get_system_topology_summary(self) -> Dict[str, Any]:
        """Return a compact summary of the system's topology."""
        g = self.load_system_graph()
        stats = g.get("stats", {})

        # Identify hub nodes (degree > 10)
        degree: Counter = Counter()
        for e in g.get("edges", []):
            degree[e["source"]] += 1
            degree[e["target"]] += 1

        hubs = []
        nodes = g.get("nodes", {})
        for nid, deg in degree.most_common(10):
            nd = nodes.get(nid, {})
            hubs.append({
                "id": nid,
                "name": nd.get("name", nid),
                "type": nd.get("node_type", "?"),
                "degree": deg,
            })

        return {
            "total_nodes": stats.get("total_nodes", len(nodes)),
            "total_edges": stats.get("total_edges", len(g.get("edges", []))),
            "connected_nodes": stats.get("connected_nodes", 0),
            "isolated_nodes": stats.get("isolated_nodes", 0),
            "nodes_by_type": stats.get("nodes_by_type", {}),
            "edges_by_type": stats.get("edges_by_type", {}),
            "hubs": hubs,
        }

    # ── 2. DOC INDEX (spec 19: A2_DOC_INDEX_v1) ────────────────────────────
    def refresh_doc_index(self) -> Dict[str, Any]:
        """
        Deterministic full scan of v4 artefacts.
        Path-lexicographic ordering, stable SHA-256 hashes.
        """
        scan_dirs = [
            self.workspace_root / "system_v4" / "skills",
            self.workspace_root / "system_v4" / "tests",
            self.workspace_root / "system_v4" / "runners",
            self.workspace_root / "system_v4" / "probes",
            self.workspace_root / "system_v4" / "specs",
            self.workspace_root / "system_v4" / "docs",
        ]

        documents: List[Dict[str, Any]] = []
        for scan_dir in scan_dirs:
            if not scan_dir.exists():
                continue
            for root, _dirs, files in os.walk(scan_dir):
                _dirs.sort()
                for fname in sorted(files):
                    if fname.startswith(".") or fname.endswith(".pyc"):
                        continue
                    fpath = Path(root) / fname
                    rel = str(fpath.relative_to(self.workspace_root))
                    documents.append({
                        "path": rel,
                        "sha256": self._sha256_file(fpath),
                        "size_bytes": fpath.stat().st_size,
                        "layer": scan_dir.name,
                    })

        # Strict path-lexicographic sort (spec 19)
        documents.sort(key=lambda d: d["path"])

        index = {
            "schema": "A2_DOC_INDEX_v1",
            "schema_version": 1,
            "generated_utc": self._utc_iso(),
            "document_count": len(documents),
            "documents": documents,
        }

        with self.doc_index_path.open("w", encoding="utf-8") as f:
            json.dump(index, f, indent=2)

        return index

    # ── 3. MEMORY LOG (spec 19: A2_MEMORY_ENTRY_v1) ────────────────────────
    def append_memory_event(
        self,
        entry_type: str,
        content: Any,
        source_refs: Optional[List[Dict[str, str]]] = None,
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        entry_id = self._get_next_entry_id(self.memory_log_path)
        event = {
            "schema": "A2_MEMORY_ENTRY_v1",
            "entry_id": f"{entry_id:08d}",
            "ts_utc": self._utc_iso(),
            "entry_type": entry_type,
            "content": content,
            "source_refs": source_refs or [],
            "tags": tags or [],
        }
        self._append_jsonl(self.memory_log_path, event)
        return event

    # ── 4. CONTEXT SEAL (spec 19: A2_SEAL_RECORD_v1) ───────────────────────
    def seal_context(
        self,
        source_thread_id: str,
        pending_actions: List[str],
        next_read_set: List[str],
        state_digest_hash: str,
    ) -> Dict[str, Any]:
        seal_id = self._get_next_entry_id(self.seal_log_path)

        head_entry_id = "00000000"
        head_hash = "none"
        if self.memory_log_path.exists():
            with self.memory_log_path.open("r", encoding="utf-8") as f:
                lines = f.readlines()
                if lines:
                    last = lines[-1].strip()
                    try:
                        obj = json.loads(last)
                        head_entry_id = obj.get("entry_id", "00000000")
                        head_hash = hashlib.sha256(last.encode()).hexdigest()
                    except json.JSONDecodeError:
                        pass

        seal = {
            "schema": "A2_SEAL_RECORD_v1",
            "seal_id": f"SEAL_V4_{seal_id:08d}",
            "ts_utc": self._utc_iso(),
            "source_thread_id": source_thread_id,
            "source_memory_head_entry_id": head_entry_id,
            "source_memory_head_hash": head_hash,
            "pending_actions": pending_actions,
            "next_read_set": next_read_set,
            "state_digest_hash": state_digest_hash,
        }
        self._append_jsonl(self.seal_log_path, seal)

        self.append_memory_event(
            entry_type="CONTEXT_SEALED",
            content={"seal_id": seal["seal_id"], "reason": "Thread context rotation."},
            tags=["CONTEXT_ROTATION", "SEAL"],
        )
        return seal

    # ── 5. BOOT STATE REPORT ────────────────────────────────────────────────
    def generate_boot_state_report(self) -> Dict[str, Any]:
        """
        Generate a complete system state report.
        This is what a new thread reads to know where the system is
        without depending on LLM context.
        """
        topo = self.get_system_topology_summary()

        # Skill registry state
        skill_count = topo.get("nodes_by_type", {}).get("V4_SKILL", 0)
        test_count = topo.get("nodes_by_type", {}).get("V4_TEST", 0)
        spec_count = topo.get("nodes_by_type", {}).get("V4_SKILL_SPEC", 0)

        # Latest seal
        latest_seal = None
        if self.seal_log_path.exists():
            with self.seal_log_path.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            latest_seal = json.loads(line)
                        except json.JSONDecodeError:
                            pass

        # Memory log stats
        memory_entries = 0
        if self.memory_log_path.exists():
            with self.memory_log_path.open("r", encoding="utf-8") as f:
                for _ in f:
                    memory_entries += 1

        # State file health
        state_files_health: Dict[str, Any] = {}
        check_files = {
            "memory.jsonl": self.memory_log_path,
            "thread_seals": self.seal_log_path,
            "doc_index_v4.json": self.doc_index_path,
            "system_architecture_graph": self.system_graph_path,
            "intent_control": self.a2_state_dir / "A2_INTENT_CONTROL__CURRENT__v1.json",
            "daemon_state": self.a2_state_dir / "daemon_state.json",
        }
        for name, fpath in check_files.items():
            state_files_health[name] = {
                "exists": fpath.exists(),
                "size_bytes": fpath.stat().st_size if fpath.exists() else 0,
            }

        report = {
            "schema": "A2_SYSTEM_STATE_REPORT_v1",
            "generated_utc": self._utc_iso(),
            "system_topology": topo,
            "skill_count": skill_count,
            "test_count": test_count,
            "spec_count": spec_count,
            "memory_entries": memory_entries,
            "latest_seal": latest_seal,
            "state_files_health": state_files_health,
            "pending_actions": (
                latest_seal.get("pending_actions", []) if latest_seal else []
            ),
            "next_read_set": (
                latest_seal.get("next_read_set", []) if latest_seal else []
            ),
        }

        with self.system_state_path.open("w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        # Log the boot event
        self.append_memory_event(
            entry_type="BOOT_STATE_GENERATED",
            content={
                "skill_count": skill_count,
                "graph_nodes": topo["total_nodes"],
                "graph_edges": topo["total_edges"],
                "memory_entries": memory_entries,
            },
            tags=["BOOT", "STATE_REPORT"],
        )

        return report

    # ── 6. DETERMINISTIC TICK (spec 19 §Deterministic Refresh Sequence) ────
    def tick(self) -> Dict[str, Any]:
        """
        Execute one deterministic A2 tick.

        Ordered sequence (no reorder allowed):
        1. refresh doc_index
        2. append mining/decision entries to memory.jsonl (caller's job)
        3. generate boot state report
        4. seal if trigger hit
        """
        results: Dict[str, Any] = {"ts_utc": self._utc_iso(), "steps": []}

        # Step 1: refresh doc index
        idx = self.refresh_doc_index()
        results["steps"].append({
            "step": "refresh_doc_index",
            "document_count": idx["document_count"],
        })

        # Step 2: entries — handled by caller between ticks

        # Step 3: boot state report
        report = self.generate_boot_state_report()
        results["steps"].append({
            "step": "generate_boot_state_report",
            "skill_count": report["skill_count"],
            "graph_nodes": report["system_topology"]["total_nodes"],
            "graph_edges": report["system_topology"]["total_edges"],
        })

        return results

    # ── 7. SKILL UNDERSTANDING ──────────────────────────────────────────────
    def load_skill_understanding(self) -> Dict[str, Any]:
        """Load the skill understanding index."""
        path = self.a2_state_dir / "skill_understanding_index_v1.json"
        if not path.exists():
            return {"skills": {}}
        with path.open() as f:
            return json.load(f)

    def lookup_skill(self, skill_name: str) -> Optional[Dict[str, Any]]:
        """
        Look up everything the brain knows about a skill:
        what it does, who it talks to, where it's explained.
        """
        idx = self.load_skill_understanding()
        skill = idx.get("skills", {}).get(skill_name)
        if not skill:
            for name, info in idx.get("skills", {}).items():
                if skill_name.replace("-", "_") == name or skill_name in name:
                    skill = info
                    skill["matched_name"] = name
                    break
        return skill

    def find_explanations(self, skill_name: str) -> List[str]:
        """Find all docs/files that explain a given skill."""
        info = self.lookup_skill(skill_name)
        if not info:
            return []
        return info.get("mentioned_in_docs", [])

    # ── 8. NESTED GRAPH ACCESS ──────────────────────────────────────────────
    def load_nested_graph(self) -> Dict[str, Any]:
        """Load the nested system graph (L0-L3 layers)."""
        path = self.a2_state_dir / "graphs" / "nested_system_graph_v1.json"
        if not path.exists():
            return {"layers": {}}
        with path.open() as f:
            return json.load(f)

    def get_system_core(self) -> Dict[str, Any]:
        """Return L0: the lowest-entropy system spine."""
        nested = self.load_nested_graph()
        return nested.get("layers", {}).get("L0_SYSTEM_CORE", {})

    def get_skill_clusters(self) -> Dict[str, Any]:
        """Return L1: skill clusters with cross-cluster dependencies."""
        nested = self.load_nested_graph()
        return nested.get("layers", {}).get("L1_SKILL_CLUSTERS", {})

    def get_cluster_for_skill(self, skill_name: str) -> Optional[str]:
        """Find which cluster a skill belongs to."""
        clusters = self.get_skill_clusters()
        for _nid, cdata in clusters.get("nodes", {}).items():
            if skill_name in cdata.get("skills", []):
                return cdata.get("name")
            if skill_name.replace("-", "_") in cdata.get("skills", []):
                return cdata.get("name")
        return None

    # ── 9. V3 BOOT-READ-ORDER PROTOCOL (spec 07 §Boot Order) ───────────────
    # The v3 boot order defines 3 steps: owner law → brain surfaces → persistent state
    V3_BOOT_READ_ORDER = {
        "step1_owner_law": [
            "system_v3/specs/01_REQUIREMENTS_LEDGER.md",
            "system_v3/specs/02_OWNERSHIP_MAP.md",
            "system_v3/specs/07_A2_OPERATIONS_SPEC.md",
            "system_v3/specs/19_A2_PERSISTENT_BRAIN_AND_CONTEXT_SEAL_CONTRACT.md",
        ],
        "step2_brain_surfaces": [
            "system_v3/a2_state/INTENT_SUMMARY.md",
            "system_v3/a2_state/A2_BRAIN_SLICE__v1.md",
            "system_v3/a2_state/A2_SYSTEM_UNDERSTANDING_UPDATE__SOURCE_BOUND_v2.md",
            "system_v3/a2_state/A2_TERM_CONFLICT_MAP__v1.md",
            "system_v3/a2_state/A2_TO_A1_DISTILLATION_INPUTS__v1.md",
            "system_v3/a2_state/OPEN_UNRESOLVED__v1.md",
            "system_v3/a2_state/A2_CONTROLLER_STATE_RECORD__CURRENT__v1.md",
            "system_v3/a2_state/SURFACE_CLASS_AND_MEMORY_ADMISSION_RULES__v1.md",
            "system_v3/a2_state/A2_KEY_CONTEXT_APPEND_LOG__v1.md",
            "system_v3/a2_state/A2_SKILL_SOURCE_INTAKE_PROCEDURE__CURRENT__v1.md",
        ],
        "step3_persistent_state": [
            "system_v3/a2_state/memory.jsonl",
            "system_v3/a2_state/doc_index.json",
            "system_v3/a2_state/fuel_queue.json",
            "system_v3/a2_state/rosetta.json",
            "system_v3/a2_state/constraint_surface.json",
        ],
    }

    # 3x2 layer graph paths
    LAYER_3x2 = {
        "A2_HIGH_INTAKE": "system_v4/a2_state/graphs/a2_high_intake_graph_v1.json",
        "A2_MID_REFINEMENT": "system_v4/a2_state/graphs/a2_mid_refinement_graph_v1.json",
        "A2_LOW_CONTROL": "system_v4/a2_state/graphs/a2_low_control_graph_v1.json",
        "A1_JARGONED": "system_v4/a1_state/a1_jargoned_graph_v1.json",
        "A1_STRIPPED": "system_v4/a1_state/a1_stripped_graph_v1.json",
        "A1_CARTRIDGE": "system_v4/a1_state/a1_cartridge_graph_v1.json",
    }

    def audit_v3_boot_surfaces(self) -> Dict[str, Any]:
        """Check which v3 boot-read-order surfaces exist and their sizes."""
        result: Dict[str, Any] = {}
        for step, paths in self.V3_BOOT_READ_ORDER.items():
            step_result = []
            for p in paths:
                fpath = self.workspace_root / p
                step_result.append({
                    "path": p,
                    "exists": fpath.exists(),
                    "size_bytes": fpath.stat().st_size if fpath.exists() else 0,
                })
            result[step] = step_result
        return result

    def assess_a2_a1_bridge(self) -> Dict[str, Any]:
        """Assess the health of the A2→A1 Rosetta bridge."""
        def _count_nodes(path: str) -> int:
            fpath = self.workspace_root / path
            if not fpath.exists():
                return 0
            try:
                data = json.loads(fpath.read_text())
                nodes = data.get("nodes", {})
                return len(nodes) if isinstance(nodes, dict) else 0
            except (json.JSONDecodeError, OSError):
                return 0

        layer_counts = {}
        for layer, path in self.LAYER_3x2.items():
            layer_counts[layer] = _count_nodes(path)

        rosetta_path = self.workspace_root / "system_v4" / "a1_state" / "rosetta_v2.json"

        a2_low = layer_counts.get("A2_LOW_CONTROL", 0)
        a1_jar = layer_counts.get("A1_JARGONED", 0)

        if a1_jar <= 2:
            status = "BROKEN"
        elif a1_jar < a2_low // 2:
            status = "PARTIAL"
        else:
            status = "HEALTHY"

        return {
            "bridge_status": status,
            "layer_node_counts": layer_counts,
            "rosetta_v2_exists": rosetta_path.exists(),
            "rosetta_v2_size_bytes": (
                rosetta_path.stat().st_size if rosetta_path.exists() else 0
            ),
            "bottleneck": (
                "A1 jargoned graph builder needs to run with real A2_LOW_CONTROL data"
                if status == "BROKEN"
                else "A1 stripped/cartridge builders need data"
                if layer_counts.get("A1_STRIPPED", 0) == 0
                else "Bridge is healthy"
            ),
        }

    def generate_comprehensive_boot_state(self) -> Dict[str, Any]:
        """
        Full system boot state for any new thread.
        Follows the v3 spec 07 boot-read-order protocol.
        """
        topo = self.get_system_topology_summary()
        bridge = self.assess_a2_a1_bridge()
        v3_surfaces = self.audit_v3_boot_surfaces()

        # Latest seal
        latest_seal = None
        if self.seal_log_path.exists():
            with self.seal_log_path.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            latest_seal = json.loads(line)
                        except json.JSONDecodeError:
                            pass

        # Memory log count
        memory_entries = 0
        if self.memory_log_path.exists():
            with self.memory_log_path.open("r", encoding="utf-8") as f:
                for _ in f:
                    memory_entries += 1

        report = {
            "schema": "A2_COMPREHENSIVE_BOOT_STATE_v1",
            "generated_utc": self._utc_iso(),
            "system_architecture": topo,
            "layer_3x2": bridge["layer_node_counts"],
            "a2_to_a1_bridge": {
                "status": bridge["bridge_status"],
                "bottleneck": bridge["bottleneck"],
                "rosetta_v2_size": bridge["rosetta_v2_size_bytes"],
            },
            "v3_boot_surfaces": {
                step: {
                    "present": sum(1 for s in surfaces if s["exists"]),
                    "total": len(surfaces),
                }
                for step, surfaces in v3_surfaces.items()
            },
            "memory_entries": memory_entries,
            "latest_seal": latest_seal,
            "pending_actions": (
                latest_seal.get("pending_actions", []) if latest_seal else []
            ),
        }

        with self.system_state_path.open("w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        self.append_memory_event(
            entry_type="COMPREHENSIVE_BOOT_STATE",
            content={
                "graph_nodes": topo["total_nodes"],
                "bridge_status": bridge["bridge_status"],
                "layer_counts": bridge["layer_node_counts"],
            },
            tags=["BOOT", "3x2", "BRIDGE_ASSESSMENT"],
        )

        return report
