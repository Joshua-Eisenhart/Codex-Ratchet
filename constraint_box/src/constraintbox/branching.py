from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .intake import canonical_json


class BranchStatus(str, Enum):
    LIVE = "LIVE"
    PARKED = "PARKED"
    PRUNED = "PRUNED"
    MERGED = "MERGED"


@dataclass(frozen=True)
class Branch:
    branch_id: str
    payload_sha256: str
    parents: tuple[str, ...] = ()
    status: BranchStatus = BranchStatus.LIVE


@dataclass(frozen=True)
class PruneEvidence:
    contract_sha256: str
    extension_count: int | None
    solver_status: str
    evidence_ref: str


@dataclass(frozen=True)
class MergeEvidence:
    active_probes: tuple[str, ...]
    allowed_continuations: tuple[str, ...]
    observations_left: tuple[tuple[str, tuple[Any, ...]], ...]
    observations_right: tuple[tuple[str, tuple[Any, ...]], ...]
    contract_sha256: str


@dataclass
class BranchLedger:
    """Preserves all branches; pruning and merging change status, not history."""

    branches: dict[str, Branch] = field(default_factory=dict)
    events: list[dict[str, Any]] = field(default_factory=list)

    def add(
        self, branch_id: str, payload: Any, parents: tuple[str, ...] = ()
    ) -> Branch:
        if branch_id in self.branches:
            raise ValueError("branch id already exists")
        if any(parent not in self.branches for parent in parents):
            raise ValueError("unknown parent branch")
        branch = Branch(
            branch_id,
            hashlib.sha256(canonical_json(payload)).hexdigest(),
            parents,
        )
        self.branches[branch_id] = branch
        self.events.append({"event": "BRANCH_ADDED", "branch_id": branch_id})
        return branch

    def park(self, branch_id: str, reason: str) -> None:
        branch = self._live(branch_id)
        self.branches[branch_id] = Branch(
            branch.branch_id, branch.payload_sha256, branch.parents, BranchStatus.PARKED
        )
        self.events.append(
            {"event": "BRANCH_PARKED", "branch_id": branch_id, "reason": reason}
        )

    def prune(self, branch_id: str, evidence: PruneEvidence) -> None:
        branch = self._live(branch_id)
        earned = (
            evidence.extension_count == 0
            and evidence.solver_status == "BOUNDED_UNSAT"
            and bool(evidence.contract_sha256)
            and bool(evidence.evidence_ref)
        )
        if not earned:
            raise ValueError("pruning_not_earned")
        self.branches[branch_id] = Branch(
            branch.branch_id, branch.payload_sha256, branch.parents, BranchStatus.PRUNED
        )
        self.events.append(
            {
                "event": "BRANCH_PRUNED",
                "branch_id": branch_id,
                "evidence": evidence.__dict__,
            }
        )

    def merge(
        self,
        left_id: str,
        right_id: str,
        merged_id: str,
        payload: Any,
        evidence: MergeEvidence,
    ) -> Branch:
        left = self._live(left_id)
        right = self._live(right_id)
        if not evidence.active_probes:
            raise ValueError("merge_requires_active_probes")
        if not evidence.allowed_continuations:
            raise ValueError("merge_requires_continuation_contract")
        left_obs = dict(evidence.observations_left)
        right_obs = dict(evidence.observations_right)
        expected = set(evidence.allowed_continuations)
        if set(left_obs) != expected or set(right_obs) != expected:
            raise ValueError("merge_evidence_incomplete")
        if left_obs != right_obs:
            raise ValueError("branches_remain_distinguishable")
        if not evidence.contract_sha256:
            raise ValueError("merge_contract_missing")
        merged = self.add(merged_id, payload, parents=(left_id, right_id))
        self.branches[left_id] = Branch(
            left.branch_id, left.payload_sha256, left.parents, BranchStatus.MERGED
        )
        self.branches[right_id] = Branch(
            right.branch_id, right.payload_sha256, right.parents, BranchStatus.MERGED
        )
        self.events.append(
            {
                "event": "BRANCHES_MERGED",
                "left": left_id,
                "right": right_id,
                "merged": merged_id,
                "contract_sha256": evidence.contract_sha256,
            }
        )
        return merged

    def _live(self, branch_id: str) -> Branch:
        branch = self.branches.get(branch_id)
        if branch is None:
            raise ValueError("unknown branch")
        if branch.status is not BranchStatus.LIVE:
            raise ValueError("branch_not_live")
        return branch
