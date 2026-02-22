import sys
from pathlib import Path

RUNTIME_ROOT = Path(__file__).resolve().parents[1]
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))
from runtime_surface_guard import enforce_canonical_runtime

enforce_canonical_runtime(__file__)

import re
from typing import List, Tuple

from containers import parse_export_block, split_items
from state import KernelState


_PROBE_KIND_RE = re.compile(r"^PROBE_KIND\s+(\S+)\s+CORR\s+(\S+)$")
_ASSERT_PROBE_RE = re.compile(r"^ASSERT\s+(\S+)\s+CORR\s+EXISTS\s+PROBE_TOKEN\s+(\S+)$")
_SPEC_KIND_RE = re.compile(r"^SPEC_KIND\s+(\S+)\s+CORR\s+(\S+)$")
_REQUIRES_RE = re.compile(r"^REQUIRES\s+(\S+)\s+CORR\s+(\S+)$")
_DEF_REQ_EVIDENCE_RE = re.compile(r"^DEF_FIELD\s+(\S+)\s+CORR\s+REQUIRES_EVIDENCE\s+(\S+)$")
_ASSERT_EVIDENCE_RE = re.compile(r"^ASSERT\s+(\S+)\s+CORR\s+EXISTS\s+EVIDENCE_TOKEN\s+(\S+)$")

_SIM_EVIDENCE_BEGIN_RE = re.compile(r"^BEGIN SIM_EVIDENCE v1$")
_SIM_EVIDENCE_END_RE = re.compile(r"^END SIM_EVIDENCE v1$")
_SIM_EVIDENCE_SIM_ID_RE = re.compile(r"^SIM_ID:\s*(\S+)$")
_SIM_EVIDENCE_CODE_HASH_RE = re.compile(r"^CODE_HASH_SHA256:\s*([0-9a-fA-F]{64})$")
_SIM_EVIDENCE_OUTPUT_HASH_RE = re.compile(r"^OUTPUT_HASH_SHA256:\s*([0-9a-fA-F]{64})$")
_SIM_EVIDENCE_SIGNAL_RE = re.compile(r"^EVIDENCE_SIGNAL\s+(\S+)\s+CORR\s+(\S+)$")


class BKernel:
    def __init__(self):
        self.allowed_spec_kinds = {"SIM_SPEC"}

    def evaluate_export_block(self, text: str, state: KernelState, log_fn=None) -> dict:
        result = {"accepted": [], "rejected": []}
        try:
            block = parse_export_block(text)
        except Exception as exc:
            reason = f"PARSE_FAIL:{exc}"
            if log_fn:
                log_fn({"event": "reject", "reason": reason})
            result["rejected"].append({"id": "EXPORT_BLOCK", "reason": reason})
            return result

        items = split_items(block.content_lines)
        block_probes = {}

        # First pass: validate probes
        for item in items:
            if item["header"] != "PROBE_HYP":
                continue
            pid = item["id"]
            lines = item["lines"]
            kind = None
            token = None
            for ln in lines:
                m = _PROBE_KIND_RE.match(ln)
                if m:
                    kind = m.group(2)
                m = _ASSERT_PROBE_RE.match(ln)
                if m:
                    token = m.group(2)
            if not kind or not token:
                result["rejected"].append({"id": pid, "reason": "PROBE_SCHEMA_FAIL"})
                if log_fn:
                    log_fn({"event": "reject", "id": pid, "reason": "PROBE_SCHEMA_FAIL"})
                continue
            block_probes[pid] = {"kind": kind, "token": token}
            state.probes[pid] = {"kind": kind, "token": token}
            state.survivor_order.append(pid)
            result["accepted"].append(pid)
            if log_fn:
                log_fn({"event": "accept", "id": pid, "header": "PROBE_HYP"})

        # Second pass: validate specs
        available_probes = set(state.probes.keys()) | set(block_probes.keys())
        for item in items:
            if item["header"] != "SPEC_HYP":
                continue
            sid = item["id"]
            lines = item["lines"]
            kind = None
            requires = None
            req_token = None
            assert_token = None
            for ln in lines:
                m = _SPEC_KIND_RE.match(ln)
                if m:
                    kind = m.group(2)
                m = _REQUIRES_RE.match(ln)
                if m:
                    requires = m.group(2)
                m = _DEF_REQ_EVIDENCE_RE.match(ln)
                if m:
                    req_token = m.group(2)
                m = _ASSERT_EVIDENCE_RE.match(ln)
                if m:
                    assert_token = m.group(2)
            if kind not in self.allowed_spec_kinds:
                result["rejected"].append({"id": sid, "reason": "SPEC_KIND_UNSUPPORTED"})
                if log_fn:
                    log_fn({"event": "reject", "id": sid, "reason": "SPEC_KIND_UNSUPPORTED"})
                continue
            if requires is None or requires not in available_probes:
                result["rejected"].append({"id": sid, "reason": "MISSING_REQUIRED_PROBE"})
                if log_fn:
                    log_fn({"event": "reject", "id": sid, "reason": "MISSING_REQUIRED_PROBE"})
                continue
            if not req_token or not assert_token or req_token != assert_token:
                result["rejected"].append({"id": sid, "reason": "EVIDENCE_TOKEN_MISMATCH"})
                if log_fn:
                    log_fn({"event": "reject", "id": sid, "reason": "EVIDENCE_TOKEN_MISMATCH"})
                continue

            state.specs[sid] = {
                "kind": kind,
                "requires_probe": requires,
                "requires_evidence": req_token,
                "evidence_tokens": [],
            }
            state.evidence_pending[sid] = {req_token}
            state.survivor_order.append(sid)
            result["accepted"].append(sid)
            if log_fn:
                log_fn({"event": "accept", "id": sid, "header": "SPEC_HYP", "kind": kind})

        return result

    def ingest_sim_evidence(self, text: str, state: KernelState, log_fn=None) -> dict:
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        if not lines or not _SIM_EVIDENCE_BEGIN_RE.match(lines[0]) or not _SIM_EVIDENCE_END_RE.match(lines[-1]):
            return {"status": "REJECT", "reason": "BAD_SIM_EVIDENCE_CONTAINER"}

        sim_id = None
        code_hash = None
        output_hash = None
        signals: List[Tuple[str, str]] = []
        for ln in lines[1:-1]:
            m = _SIM_EVIDENCE_SIM_ID_RE.match(ln)
            if m:
                sim_id = m.group(1)
                continue
            m = _SIM_EVIDENCE_CODE_HASH_RE.match(ln)
            if m:
                code_hash = m.group(1)
                continue
            m = _SIM_EVIDENCE_OUTPUT_HASH_RE.match(ln)
            if m:
                output_hash = m.group(1)
                continue
            m = _SIM_EVIDENCE_SIGNAL_RE.match(ln)
            if m:
                signals.append((m.group(1), m.group(2)))

        if not sim_id or not code_hash or not output_hash:
            return {"status": "REJECT", "reason": "MISSING_SIM_FIELDS"}

        satisfied = []
        for target, token in signals:
            if target not in state.evidence_pending:
                continue
            pending = state.evidence_pending.get(target, set())
            if token in pending:
                pending.remove(token)
                spec = state.specs.get(target)
                if spec is not None:
                    spec.setdefault("evidence_tokens", []).append(token)
                if not pending:
                    state.evidence_pending.pop(target, None)
                else:
                    state.evidence_pending[target] = pending
                satisfied.append(target)
                if log_fn:
                    log_fn({"event": "evidence_accept", "spec": target, "token": token})
        return {"status": "OK", "satisfied": satisfied}
