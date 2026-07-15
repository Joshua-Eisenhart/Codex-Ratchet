#!/usr/bin/env python3
"""Generate the exhaustive V8 sim-stack/tool/repo inventory from frozen registries."""

from __future__ import annotations

import collections
import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any


SIM_DIR = Path(__file__).resolve().parent
ROOT = SIM_DIR.parents[2]
ROSTER_PATH = ROOT / "system_v5/ops/tooling/deep_stack_stress_20260714/registry/tool_roster_v1.json"
EDGES_PATH = ROOT / "system_v5/ops/tooling/deep_stack_stress_20260714/registry/integration_edges_v1.json"
ESTATE_PATH = ROOT / "system_v5/ops/tooling/deep_stack_stress_20260714/results/deep_stack_estate_lev.json"
FINAL_PATH = SIM_DIR / "results/final_report.json"
SOURCES_PATH = SIM_DIR / "inventory_sources.json"
JSON_OUT = SIM_DIR / "results/sim_stack_inventory.json"
MD_OUT = SIM_DIR / "SIM_STACK_INVENTORY.md"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def git_state(path: Path) -> dict[str, Any]:
    if not (path / ".git").exists() and not (path / ".git").is_file():
        return {"is_git": False, "exists": path.exists()}

    def git(*args: str) -> tuple[int, str]:
        proc = subprocess.run(["git", *args], cwd=path, text=True, capture_output=True, check=False)
        return proc.returncode, proc.stdout.strip()

    _, head = git("rev-parse", "HEAD")
    _, tree = git("rev-parse", "HEAD^{tree}")
    _, branch = git("branch", "--show-current")
    _, status = git("status", "--porcelain")
    rows = status.splitlines() if status else []
    untracked = sum(row.startswith("??") for row in rows)
    return {
        "is_git": True,
        "exists": True,
        "head": head,
        "tree": tree,
        "branch": branch or "DETACHED",
        "clean": not rows,
        "tracked_dirty_count": len(rows) - untracked,
        "untracked_count": untracked,
    }


def first_rung_role(tool_id: str) -> dict[str, str] | None:
    roles = {
        "py_jax": {"state": "fresh_bounded_claim_load_bearing", "role": "batched census and fixed-point closure"},
        "py_torch": {"state": "fresh_bounded_claim_load_bearing", "role": "tensor census and graph closure support"},
        "py_torch_geometric": {"state": "fresh_bounded_claim_load_bearing", "role": "MessagePassing reachability closure"},
        "py_z3": {"state": "fresh_bounded_proof_discharge", "role": "free-variable equivalence SAT/UNSAT encoding"},
        "py_cvc5": {"state": "fresh_bounded_proof_discharge", "role": "independent free-variable equivalence SAT/UNSAT encoding"},
        "jl_graphs": {"state": "fresh_bounded_claim_load_bearing", "role": "connected-component equivalence closure"},
        "jl_json3": {"state": "fresh_support", "role": "structured engine receipt serialization"},
        "jl_sha": {"state": "fresh_support", "role": "source hash binding"},
        "jl_dates": {"state": "fresh_support", "role": "receipt timestamp"}
    }
    return roles.get(tool_id)


def main() -> int:
    roster = load(ROSTER_PATH)
    edges = load(EDGES_PATH)
    estate = load(ESTATE_PATH)
    sources = load(SOURCES_PATH)
    final = load(FINAL_PATH)
    current_head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=True).stdout.strip()
    current_tree = subprocess.run(["git", "rev-parse", "HEAD^{tree}"], cwd=ROOT, text=True, capture_output=True, check=True).stdout.strip()
    receipts = {row["tool_id"]: row for row in estate["tool_receipts"]}
    tools = []
    for row in roster["tools"]:
        receipt = receipts.get(row["tool_id"])
        verdict = receipt.get("verdict", {}) if receipt else {}
        stale = bool(receipt and receipt.get("source_binding", {}).get("ratchet_tree") != current_tree)
        tool = {
            **row,
            "historical_receipt_present": receipt is not None,
            "historical_operational_status": verdict.get("operational_status"),
            "historical_receipt_valid": verdict.get("receipt_valid"),
            "historical_operational_pass": verdict.get("operational_pass"),
            "historical_source_commit": receipt.get("source_binding", {}).get("ratchet_commit") if receipt else None,
            "historical_source_tree": receipt.get("source_binding", {}).get("ratchet_tree") if receipt else None,
            "stale_to_v8_tree": stale,
            "first_rung": first_rung_role(row["tool_id"]),
            "claim_ceiling": "L2 historical integration diagnostic; fresh v0 roles support finite mechanics only, not a Ratchet tooth"
        }
        tools.append(tool)
    bucket_counts = dict(sorted(collections.Counter(row["bucket"] for row in roster["tools"]).items()))
    operational_count = sum(bool(row.get("historical_operational_pass")) for row in tools)
    edge_ids = [row["id"] for row in edges["edges"]]
    repositories = []
    for declared in sources["repositories"]:
        path = Path(declared["path"])
        repositories.append({**declared, "live_state": git_state(path)})
    worktree_status = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, text=True, capture_output=True, check=True).stdout.splitlines()
    inventory = {
        "schema": "codex_ratchet.v8_sim_stack_inventory.v1",
        "generated_at": dt.datetime.now(dt.UTC).isoformat(),
        "current_v8_source": {
            "root": str(ROOT),
            "base_commit": current_head,
            "base_tree": current_tree,
            "worktree_clean": not worktree_status,
            "worktree_status_row_count": len(worktree_status),
            "new_packet_is_source_hash_bound_not_yet_commit_bound": True
        },
        "authority": {
            "roster": {"path": str(ROSTER_PATH.relative_to(ROOT)), "sha256": sha256(ROSTER_PATH), "tool_count": len(tools)},
            "edges": {"path": str(EDGES_PATH.relative_to(ROOT)), "sha256": sha256(EDGES_PATH), "edge_count": len(edge_ids)},
            "historical_estate": {"path": str(ESTATE_PATH.relative_to(ROOT)), "sha256": sha256(ESTATE_PATH), "source_commit": estate["source_state"]["ratchet_commit"], "source_tree": estate["source_state"]["ratchet_tree"], "projection_only": True, "release_eligible": estate.get("release_eligible"), "scientific_claim_proven": estate.get("scientific_claim_proven"), "stale_to_v8_tree": estate["source_state"]["ratchet_tree"] != current_tree},
            "first_rung_v0": {"path": str(FINAL_PATH.relative_to(ROOT)), "sha256": sha256(FINAL_PATH), "mechanical_code_gates_pass": final["mechanical_code_gates_pass"], "semantic_forcing_pass": final["semantic_forcing_pass"], "all_code_gates_pass": final["all_code_gates_pass"], "decision": final["decision"], "official_launch_allowed": final["official_launch_allowed"]}
        },
        "summary": {"tool_count": len(tools), "bucket_counts": bucket_counts, "historical_operational_pass_count": operational_count, "integration_edge_count": len(edge_ids), "fresh_first_rung_tool_count": sum(row["first_rung"] is not None for row in tools)},
        "integration_edges": {"ids": edge_ids, "compatibility_or_cohealth_count": 25, "independent_cross_runtime_recomputation_ids": ["cross_tensor", "cross_dynamics", "cross_proof"], "direct_value_handoff_ids": ["cross_jax_torch"], "claim_boundary": "29 green edge receipts do not mean 29 shared-value pipelines"},
        "tools": tools,
        "repositories": repositories,
        "extra_tools_outside_139": sources["extra_tools_outside_139"],
        "code_surfaces": sources["code_surfaces"],
        "launch_boundary": {"first_bounded_scratch_tooth": "not_earned", "v0_mechanical_pass": final["mechanical_code_gates_pass"], "v0_semantic_forcing_pass": final["semantic_forcing_pass"], "official_launch": "blocked", "lev_proof_backed_execution": final["lev_boundary"]["proof_backed_execution"], "proof_bundle_written": final["lev_boundary"]["proof_bundle_written"]}
    }
    JSON_OUT.write_text(json.dumps(inventory, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# V8 Sim Engine, Library, Tool, Repo, and Code State",
        "",
        f"Generated in an isolated worktree based on commit `{current_head}`. The new packet is bound by per-source hashes and is not yet commit-bound. This is an inventory and scratch-tooth report, not launch authority.",
        "",
        "## Outcome",
        "",
        f"- Finite roster: **{len(tools)}** rows across **{len(bucket_counts)}** buckets.",
        f"- Historical estate: **{operational_count}** operational passes and **{len(edge_ids)}** integration edges, but bound to `{estate['source_state']['ratchet_commit'][:12]}` / tree `{estate['source_state']['ratchet_tree'][:12]}` and stale to V8.",
        f"- Fresh v0 mechanics: **{final['decision']}**; mechanical gates green, semantic forcing red.",
        "- Ratchet tooth: **NOT EARNED**. G10 or a ProofBundle cannot override the semantic red.",
        "- Official launch: **BLOCKED**.",
        "",
        "## Bucket Counts",
        "",
        "| Bucket | Count |",
        "|---|---:|",
    ]
    lines.extend(f"| `{bucket}` | {count} |" for bucket, count in bucket_counts.items())
    lines.extend(["", "## Complete 139-Row Roster", ""])
    for bucket in bucket_counts:
        lines.extend([f"### `{bucket}` ({bucket_counts[bucket]})", "", "| ID | Package | Family | Runtime | Expected role | Current honest state | First-tooth role |", "|---|---|---|---|---|---|---|"])
        for row in [item for item in tools if item["bucket"] == bucket]:
            if row["first_rung"]:
                current = row["first_rung"]["state"]
                fresh = row["first_rung"]["role"]
            elif row["bucket"] in {"candidate_missing", "blocked_or_avoid", "quarantined"}:
                current = row["bucket"]
                fresh = "none"
            elif row["historical_receipt_present"]:
                current = "historical receipt; stale to V8 tree" if row["stale_to_v8_tree"] else "historical receipt"
                fresh = "none"
            else:
                current = "policy row only"
                fresh = "none"
            lines.append(f"| `{row['tool_id']}` | `{row['package']}` | `{row['family']}` | `{row['runtime_id']}` | `{row['expected_operational_role']}` | {current} | {fresh} |")
        lines.append("")
    lines.extend(["## The 29 Registered Connections", "", "- Compatibility/co-health witnesses (25): all non-cross IDs plus legacy reconciliation.", "- Independent recomputations (3): `cross_tensor`, `cross_dynamics`, `cross_proof`.", "- Direct value handoff (1): `cross_jax_torch` through DLPack.", "", "Exact IDs: " + ", ".join(f"`{edge}`" for edge in edge_ids) + ".", "", "## Connected Repositories", "", "| Path | Role | Live state | Connection / boundary |", "|---|---|---|---|"])
    for repo in repositories:
        state = repo["live_state"]
        if state.get("is_git"):
            live = f"`{state['branch']}` `{state['head'][:12]}`; " + ("clean" if state["clean"] else f"dirty {state['tracked_dirty_count']} tracked + {state['untracked_count']} untracked")
        else:
            live = "non-Git" if state.get("exists") else "missing"
        lines.append(f"| `{repo['path']}` | {repo['role']} | {live} | {repo['connection']} ({repo['authority']}) |")
    lines.extend(["", "## Code Surfaces", "", "| Surface | State | Evidence | Boundary |", "|---|---|---|---|"])
    for row in sources["code_surfaces"]:
        lines.append(f"| {row['surface']} | {row['state']} | `{row['evidence']}` | {row['boundary']} |")
    lines.extend(["", "## Tools Outside the Frozen 139", "", "| Tool | State | Evidence | Blocker |", "|---|---|---|---|"])
    for row in sources["extra_tools_outside_139"]:
        lines.append(f"| {row['tool']} | {row['state']} | {row['evidence']} | {row['blocker']} |")
    lines.extend(["", "## Launch Boundary", "", "V0 has not earned a Ratchet tooth. Its finite mechanics are useful, but semantic forcing, held-out generalization, and a persistent pawl are red. Build the sealed v1 semantic-forcing preregistration before any G10, QIT, Axis, terrain/operator, or launch claim.", ""])
    MD_OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"V8_INVENTORY_DONE tools={len(tools)} edges={len(edge_ids)} repos={len(repositories)} json={JSON_OUT} md={MD_OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
