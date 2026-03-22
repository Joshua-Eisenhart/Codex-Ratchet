"""
Skill Registry — Model-Agnostic Skill Identity & Relevance System

Skills are first-class graphed objects. Each skill gets:
- one canonical identity in the registry
- relevance edges to layers/graphs/task patterns
- model-agnostic spec (separate from adapters)
- maintenance tracking via health_pass()

This module is LLM-agnostic: Codex, Gemini, subagents, or shell runners
can all query and invoke skills through the same registry.
"""

from __future__ import annotations

import json
import os
import tempfile
import time
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, Field, ValidationError


# ── Skill Record ──────────────────────────────────────────────────────

class SkillRecord(BaseModel):
    """Canonical identity for one skill in the system."""

    skill_id: str                           # unique, stable
    name: str                               # human-readable
    description: str                        # one-liner
    skill_type: str                         # extraction, enrichment, refinement,
                                            # verification, maintenance, audit,
                                            # orchestration, bridge, runner,
                                            # agent, lane, supervisor
    source_type: str                        # repo_skill | operator_module | runner
    source_path: str                        # canonical spec location in repo
    applicable_trust_zones: list[str] = Field(default_factory=list)
    applicable_graphs: list[str] = Field(default_factory=list)
    inputs: list[str] = Field(default_factory=list)
    outputs: list[str] = Field(default_factory=list)
    related_skills: list[str] = Field(default_factory=list)
    adapters: dict[str, str] = Field(default_factory=dict)  # model → path
    capabilities: dict[str, bool] = Field(default_factory=dict)
    # Supported capability keys:
    #   can_spawn_subagents    - skill can launch parallel worker lanes
    #   can_run_parallel       - skill supports concurrent execution
    #   can_write_repo         - skill writes to repo surfaces
    #   can_only_propose       - skill proposes but cannot commit
    #   can_call_external      - skill can launch external research
    #   requires_human_gate    - skill needs human approval before commit
    #   requires_tool          - skill needs a tool backend (z3, etc.)
    #   is_phase_runner        - skill may be selected by phase orchestration
    #   is_generic_phase_handler - skill is a generic phase handler for PHASE_* zones,
    #                              not a queue-driven correction side lane
    #   is_owner_graph_builder - skill materializes an owner graph surface rather than
    #                            acting as a thin operator/module wrapper
    tool_dependencies: list[str] = Field(default_factory=list)  # e.g. ["z3", "playwright"]
    provenance: str = ""                    # where the pattern came from (repo, doc, etc.)
    status: str = "active"                  # active | stale | retired | draft
    last_verified_utc: str = ""
    tags: list[str] = Field(default_factory=list)


# ── Skill Registry ───────────────────────────────────────────────────

class SkillRegistry:
    """
    Canonical inventory of all skills in the system.

    Persists to JSON. Provides relevance queries and health auditing.
    """

    def __init__(self, workspace_root: str):
        self.workspace_root = Path(workspace_root).resolve()
        self.store_path = (
            self.workspace_root
            / "system_v4"
            / "a1_state"
            / "skill_registry_v1.json"
        )
        self.skills: dict[str, SkillRecord] = {}
        self.load_issues: list[dict[str, Any]] = []
        self.load_stats: dict[str, int] = {"loaded": 0, "repaired": 0, "skipped": 0}
        self._load()

    @staticmethod
    def _infer_source_type(record: dict[str, Any]) -> str:
        source_path = str(record.get("source_path", ""))
        adapters = record.get("adapters")
        adapter_values: list[str] = []
        if isinstance(adapters, dict):
            adapter_values = [str(value) for value in adapters.values()]
        if source_path.endswith(".md") or "/skill_specs/" in source_path:
            return "repo_skill"
        if source_path.endswith(".py") or any(value.endswith(".py") for value in adapter_values):
            return "operator_module"
        return "repo_skill"

    @staticmethod
    def _repair_description(skill_id: str, record: dict[str, Any]) -> str:
        skill_type = str(record.get("skill_type", "skill")).replace("_", " ")
        source_path = str(record.get("source_path", "")).strip()
        if source_path:
            return f"Repaired {skill_type} registry row for {skill_id} from {source_path}"
        return f"Repaired {skill_type} registry row for {skill_id}"

    # ── Persistence ──────────────────────────────────────────────────

    def _load(self) -> None:
        self.skills = {}
        self.load_issues = []
        self.load_stats = {"loaded": 0, "repaired": 0, "skipped": 0}
        if not self.store_path.exists():
            return
        try:
            data = json.loads(self.store_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            self.load_issues.append(
                {
                    "scope": "registry",
                    "skill_id": None,
                    "action": "read_failed",
                    "error": str(exc),
                }
            )
            return

        if not isinstance(data, dict):
            self.load_issues.append(
                {
                    "scope": "registry",
                    "skill_id": None,
                    "action": "invalid_root_type",
                    "error": f"expected object, got {type(data).__name__}",
                }
            )
            return

        for sid, rec in data.items():
            if not isinstance(rec, dict):
                self.load_stats["skipped"] += 1
                self.load_issues.append(
                    {
                        "scope": "row",
                        "skill_id": sid,
                        "action": "skipped",
                        "error": f"expected object, got {type(rec).__name__}",
                    }
                )
                continue

            row = dict(rec)
            repaired_fields: list[str] = []

            if not row.get("skill_id"):
                row["skill_id"] = sid
                repaired_fields.append("skill_id")
            if not row.get("name"):
                row["name"] = sid
                repaired_fields.append("name")
            if not row.get("description"):
                row["description"] = self._repair_description(sid, row)
                repaired_fields.append("description")
            if not row.get("source_type"):
                row["source_type"] = self._infer_source_type(row)
                repaired_fields.append("source_type")

            try:
                record = SkillRecord(**row)
            except (ValidationError, KeyError, TypeError, ValueError) as exc:
                self.load_stats["skipped"] += 1
                self.load_issues.append(
                    {
                        "scope": "row",
                        "skill_id": sid,
                        "action": "skipped",
                        "error": str(exc),
                    }
                )
                continue

            self.skills[record.skill_id] = record
            self.load_stats["loaded"] += 1
            if repaired_fields:
                self.load_stats["repaired"] += 1
                self.load_issues.append(
                    {
                        "scope": "row",
                        "skill_id": record.skill_id,
                        "action": "repaired",
                        "repaired_fields": repaired_fields,
                    }
                )

    def save(self) -> None:
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        data = {sid: rec.model_dump() for sid, rec in self.skills.items()}
        content = json.dumps(data, indent=2, sort_keys=True) + "\n"
        tmp_fd, tmp_path = tempfile.mkstemp(
            dir=str(self.store_path.parent), suffix=".tmp"
        )
        try:
            with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
                f.write(content)
            os.replace(tmp_path, str(self.store_path))
        except Exception:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise

    # ── Registration ─────────────────────────────────────────────────

    def register(self, record: SkillRecord) -> None:
        """Register or update a skill."""
        self.skills[record.skill_id] = record

    def retire(self, skill_id: str) -> bool:
        """Mark a skill as retired (don't delete, keep history)."""
        if skill_id in self.skills:
            self.skills[skill_id].status = "retired"
            return True
        return False

    def get(self, skill_id: str) -> Optional[SkillRecord]:
        return self.skills.get(skill_id)

    # ── Relevance Queries ────────────────────────────────────────────

    def find_relevant(
        self,
        layer_id: Optional[str] = None,
        trust_zone: Optional[str] = None,
        graph_family: Optional[str] = None,
        skill_type: Optional[str] = None,
        tags_any: Optional[list[str]] = None,
        capabilities_all: Optional[list[str]] = None,
    ) -> list[SkillRecord]:
        """
        Find skills relevant to a given context.

        This is the main query the autonomous loop should call before each phase
        to discover which skills apply.
        """
        if layer_id and not trust_zone:
            trust_zone = layer_id
        results = []
        for rec in self.skills.values():
            if rec.status != "active":
                continue
            if trust_zone and trust_zone not in rec.applicable_trust_zones:
                continue
            if graph_family and graph_family not in rec.applicable_graphs:
                continue
            if skill_type and rec.skill_type != skill_type:
                continue
            if tags_any and not any(t in rec.tags for t in tags_any):
                continue
            if capabilities_all and not all(rec.capabilities.get(cap, False) for cap in capabilities_all):
                continue
            results.append(rec)
        return results

    def find_by_type(self, skill_type: str) -> list[SkillRecord]:
        """All active skills of a given type."""
        return [s for s in self.skills.values()
                if s.skill_type == skill_type and s.status == "active"]

    def find_related(self, skill_id: str) -> list[SkillRecord]:
        """Skills related to the given skill."""
        rec = self.get(skill_id)
        if not rec:
            return []
        return [self.skills[sid] for sid in rec.related_skills
                if sid in self.skills]

    # ── Export for Model ─────────────────────────────────────────────

    @staticmethod
    def detect_runtime() -> str:
        """Auto-detect the current runtime model."""
        for env_name in ("SKILL_RUNTIME_MODEL", "RATCHET_RUNTIME_MODEL"):
            val = os.environ.get(env_name, "").strip()
            if val:
                return val
        codex_skills = Path.home() / ".codex" / "skills"
        if codex_skills.exists():
            return "codex"
        gemini_dir = Path.home() / ".gemini"
        if gemini_dir.exists():
            return "gemini"
        return "shell"

    def resolve_adapter(
        self,
        skill_id: str,
        model: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Resolve the best adapter for a skill given the current model.

        Fallback chain:
        1. Explicit adapter for the detected/specified model
        2. Canonical source_path (always works)

        Returns dict with skill spec + resolved adapter + capability warnings.
        """
        if model is None:
            model = self.detect_runtime()

        rec = self.get(skill_id)
        if not rec:
            return {"error": f"skill {skill_id} not found", "model": model}

        # Resolve adapter path: model-specific > canonical
        adapter_path = rec.adapters.get(model, rec.source_path)
        execution_path = adapter_path
        execution_runtime = model

        # Canonical SKILL.md specs are documentation surfaces, not executable
        # bindings. If a shell adapter exists, prefer that for in-loop execution
        # while preserving the model-facing adapter_path for visibility/export.
        if adapter_path.endswith(".md") and rec.adapters.get("shell"):
            execution_path = rec.adapters["shell"]
            execution_runtime = "shell"

        # Check capability compatibility
        unsupported: list[str] = []
        if model == "gemini" and rec.capabilities.get("can_spawn_subagents"):
            unsupported.append("can_spawn_subagents (gemini: use sequential)")
        if rec.capabilities.get("requires_tool") and rec.tool_dependencies:
            unsupported.append(f"requires_tool: {rec.tool_dependencies}")

        return {
            "skill_id": rec.skill_id,
            "name": rec.name,
            "description": rec.description,
            "skill_type": rec.skill_type,
            "inputs": rec.inputs,
            "outputs": rec.outputs,
            "adapter_path": adapter_path,
            "execution_path": execution_path,
            "execution_runtime": execution_runtime,
            "source_path": rec.source_path,
            "model": model,
            "capabilities": rec.capabilities,
            "tool_dependencies": rec.tool_dependencies,
            "provenance": rec.provenance,
            "unsupported_for_model": unsupported,
        }

    def export_for_model(self, skill_id: str, model: str) -> Optional[dict]:
        """
        Return skill spec + adapter path for a given model.
        Works for codex, gemini, shell, subagent, etc.
        """
        result = self.resolve_adapter(skill_id, model)
        if "error" in result:
            return None
        return result

    # ── Health Pass ──────────────────────────────────────────────────

    def health_pass(self) -> dict[str, Any]:
        """
        Audit all registered skills for problems:
        - orphaned: source_path doesn't exist on disk
        - stale: last_verified > 7 days ago or never verified
        - duplicate: overlapping name
        - missing_adapter: no adapter for any model
        - retired: count of retired skills
        """
        orphaned = []
        stale = []
        missing_adapter = []
        retired = []
        active = []
        names_seen: dict[str, list[str]] = {}
        phase_zone_non_runner = []
        phase_runner_missing_exec = []
        phase_handler_missing_generic_flag = []
        generic_phase_handler_missing_zone = []
        owner_graph_builder_missing_output = []
        owner_graph_builder_non_writer = []
        phase_graph_builder_missing_builder_flag = []

        now = time.time()
        seven_days_ago = now - (7 * 86400)

        for sid, rec in self.skills.items():
            # Check retired
            if rec.status == "retired":
                retired.append(sid)
                continue

            active.append(sid)

            # Check source_path exists
            source = Path(rec.source_path)
            if not source.is_absolute():
                source = self.workspace_root / source
            if not source.exists():
                orphaned.append(sid)
                rec.status = "stale"

            # Check last_verified
            if not rec.last_verified_utc:
                stale.append(sid)
            else:
                try:
                    verified_ts = time.mktime(
                        time.strptime(rec.last_verified_utc, "%Y-%m-%dT%H:%M:%SZ")
                    )
                    if verified_ts < seven_days_ago:
                        stale.append(sid)
                except ValueError:
                    stale.append(sid)

            # Track duplicates by name
            norm_name = rec.name.lower().replace("-", "_").replace(" ", "_")
            names_seen.setdefault(norm_name, []).append(sid)

            # Check adapters.
            # Python-backed operator modules are valid via source_path fallback
            # even when they do not declare an explicit model adapter.
            if not rec.adapters:
                source_suffix = source.suffix.lower()
                if source_suffix != ".py":
                    missing_adapter.append(sid)

            phase_zones = [
                zone for zone in rec.applicable_trust_zones
                if zone.startswith("PHASE_")
            ]
            is_phase_runner = rec.capabilities.get("is_phase_runner", False)
            is_generic_phase_handler = rec.capabilities.get(
                "is_generic_phase_handler", False
            )
            is_owner_graph_builder = rec.capabilities.get(
                "is_owner_graph_builder", False
            )
            shell_adapter = rec.adapters.get("shell")
            shell_source = None
            if shell_adapter:
                shell_source = Path(shell_adapter)
                if not shell_source.is_absolute():
                    shell_source = self.workspace_root / shell_source
            has_python_exec = (
                source.exists() and source.suffix.lower() == ".py"
            ) or (
                shell_source is not None
                and shell_source.exists()
                and shell_source.suffix.lower() == ".py"
            )

            if phase_zones and not is_phase_runner:
                phase_zone_non_runner.append(sid)
            if is_phase_runner and not has_python_exec:
                phase_runner_missing_exec.append(sid)
                if sid not in missing_adapter:
                    missing_adapter.append(sid)
            if phase_zones and is_phase_runner and not is_generic_phase_handler:
                phase_handler_missing_generic_flag.append(sid)
            if is_generic_phase_handler and not phase_zones:
                generic_phase_handler_missing_zone.append(sid)
            graph_outputs = [
                output
                for output in rec.outputs
                if output.endswith("_graph_v1") or output == "identity_registry_v1"
            ]
            if is_owner_graph_builder and not graph_outputs:
                owner_graph_builder_missing_output.append(sid)
            if is_owner_graph_builder and not rec.capabilities.get("can_write_repo", False):
                owner_graph_builder_non_writer.append(sid)
            if phase_zones and sid.endswith("-graph-builder") and not is_owner_graph_builder:
                phase_graph_builder_missing_builder_flag.append(sid)

        duplicates = {
            name: sids for name, sids in names_seen.items() if len(sids) > 1
        }

        return {
            "total": len(self.skills),
            "active": len(active),
            "retired": len(retired),
            "orphaned": orphaned,
            "stale": stale,
            "duplicates": duplicates,
            "missing_adapter": missing_adapter,
            "phase_zone_non_runner": phase_zone_non_runner,
            "phase_runner_missing_exec": phase_runner_missing_exec,
            "phase_handler_missing_generic_flag": phase_handler_missing_generic_flag,
            "generic_phase_handler_missing_zone": generic_phase_handler_missing_zone,
            "owner_graph_builder_missing_output": owner_graph_builder_missing_output,
            "owner_graph_builder_non_writer": owner_graph_builder_non_writer,
            "phase_graph_builder_missing_builder_flag": phase_graph_builder_missing_builder_flag,
            "registry_load_loaded": self.load_stats["loaded"],
            "registry_load_repaired": self.load_stats["repaired"],
            "registry_load_skipped": self.load_stats["skipped"],
            "registry_load_issues": self.load_issues,
        }

    # ── Summary ──────────────────────────────────────────────────────

    def summary(self) -> dict[str, Any]:
        """Quick summary of registry state."""
        by_type: dict[str, int] = {}
        by_source: dict[str, int] = {}
        by_status: dict[str, int] = {}
        for rec in self.skills.values():
            by_type[rec.skill_type] = by_type.get(rec.skill_type, 0) + 1
            by_source[rec.source_type] = by_source.get(rec.source_type, 0) + 1
            by_status[rec.status] = by_status.get(rec.status, 0) + 1
        return {
            "total": len(self.skills),
            "by_type": by_type,
            "by_source": by_source,
            "by_status": by_status,
        }
