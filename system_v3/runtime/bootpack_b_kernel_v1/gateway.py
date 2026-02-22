from datetime import datetime, timezone

from containers import parse_export_block, parse_sim_evidence_pack
from kernel import BootpackBKernel
from snapshot import build_snapshot_v2
from state import KernelState


BOOT_ID = "BOOTPACK_THREAD_B_v3.9.13"


def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _trim_outer_blank_lines(text: str) -> str:
    lines = [line.rstrip("\n") for line in text.splitlines()]
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    if not lines:
        return ""
    return "\n".join(lines) + "\n"


def _escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


class BootpackBGateway:
    def __init__(self, kernel: BootpackBKernel | None = None, boot_id: str = BOOT_ID, now_utc_fn=None):
        self.kernel = kernel if kernel is not None else BootpackBKernel()
        self.boot_id = boot_id
        self.now_utc_fn = now_utc_fn if now_utc_fn is not None else _now_utc_iso

    def handle_message(self, text: str, state: KernelState, batch_id: str = "") -> dict:
        normalized = _trim_outer_blank_lines(text)
        timestamp_utc = self.now_utc_fn()
        if self._is_command_message(normalized):
            requests = [line.strip() for line in normalized.splitlines() if line.strip()]
            outputs = [self._run_command(request, state, timestamp_utc) for request in requests]
            return {"status": "PASS", "tag": "", "outputs": outputs, "output_text": "\n\n".join(outputs)}

        if self._is_export_message(normalized):
            return self._handle_export_message(normalized, state, batch_id=batch_id, timestamp_utc=timestamp_utc)
        if self._is_snapshot_message(normalized):
            return self._handle_snapshot_message(normalized, state, batch_id=batch_id, timestamp_utc=timestamp_utc)
        if self._is_sim_evidence_pack_message(normalized):
            return self._handle_sim_message(normalized, state, batch_id=batch_id, timestamp_utc=timestamp_utc)

        report = self._build_report(
            report_kind="MESSAGE_REJECT",
            timestamp_utc=timestamp_utc,
            result="REJECT",
            export_id="UNKNOWN",
            ruleset_header_match="UNKNOWN",
            megaboot_header_match="UNKNOWN",
            entries=[{"id": "MESSAGE", "tag": "MULTI_ARTIFACT_OR_PROSE", "detail": "MSG-001"}],
        )
        return {"status": "REJECT", "tag": "MULTI_ARTIFACT_OR_PROSE", "output_text": report}

    def _run_command(self, request: str, state: KernelState, timestamp_utc: str) -> str:
        if request in {"REQUEST DUMP_LEDGER", "REQUEST DUMP_LEDGER_BODIES"}:
            return self._dump_ledger_bodies(state, timestamp_utc)
        if request == "REQUEST DUMP_TERMS":
            return self._dump_terms(state, timestamp_utc)
        if request == "REQUEST DUMP_INDEX":
            return self._dump_index(state, timestamp_utc)
        if request == "REQUEST DUMP_EVIDENCE_PENDING":
            return self._dump_evidence_pending(state, timestamp_utc)
        if request == "REQUEST REPORT_POLICY_STATE":
            return self._report_policy_state(state, timestamp_utc)
        if request == "REQUEST SAVE_SNAPSHOT":
            return build_snapshot_v2(state, boot_id=self.boot_id, timestamp_utc=timestamp_utc, lexicographic=True)
        if request == "REQUEST REPORT_STATE":
            return self._report_state(state, timestamp_utc)
        return self._build_report(
            report_kind="COMMAND_REJECT",
            timestamp_utc=timestamp_utc,
            result="REJECT",
            export_id="UNKNOWN",
            ruleset_header_match="UNKNOWN",
            megaboot_header_match="UNKNOWN",
            entries=[{"id": "COMMAND", "tag": "SCHEMA_FAIL", "detail": f"UNKNOWN_REQUEST:{request}"}],
        )

    def _handle_export_message(self, normalized: str, state: KernelState, batch_id: str, timestamp_utc: str) -> dict:
        try:
            block = parse_export_block(normalized)
        except Exception as exc:
            report = self._build_report(
                report_kind="EXPORT_EVAL",
                timestamp_utc=timestamp_utc,
                result="FAIL",
                export_id="UNKNOWN",
                ruleset_header_match="UNKNOWN",
                megaboot_header_match="UNKNOWN",
                entries=[{"id": "EXPORT_BLOCK", "tag": "SCHEMA_FAIL", "detail": f"PARSE_EXPORT:{exc}"}],
            )
            return {"status": "REJECT", "tag": "SCHEMA_FAIL", "output_text": report}

        ruleset_header_match = self._header_match(state.active_ruleset_sha256, block.ruleset_sha256)
        megaboot_header_match = self._header_match(state.active_megaboot_sha256, block.megaboot_sha256)

        result = self.kernel.evaluate_export_block(normalized, state, batch_id=batch_id)
        entries = []
        for parked in result["parked"]:
            entries.append({"id": parked.get("id", ""), "tag": parked.get("reason", ""), "detail": parked.get("detail", "")})
        for rejected in result["rejected"]:
            row = {
                "id": rejected.get("id", ""),
                "tag": rejected.get("reason", ""),
                "detail": rejected.get("detail", ""),
            }
            if rejected.get("offender_rule"):
                row["offender_rule"] = rejected.get("offender_rule", "")
            if rejected.get("offender_line"):
                row["offender_line"] = rejected.get("offender_line", "")
            if rejected.get("offender_literal"):
                row["offender_literal"] = rejected.get("offender_literal", "")
            entries.append(row)
        report = self._build_report(
            report_kind="EXPORT_EVAL",
            timestamp_utc=timestamp_utc,
            result="PASS" if not result["rejected"] else "FAIL",
            export_id=block.export_id,
            ruleset_header_match=ruleset_header_match,
            megaboot_header_match=megaboot_header_match,
            entries=entries,
            accepted_count=len(result["accepted"]),
            parked_count=len(result["parked"]),
            rejected_count=len(result["rejected"]),
        )
        return {"status": "PASS" if not result["rejected"] else "FAIL", "result": result, "output_text": report}

    def _handle_snapshot_message(self, normalized: str, state: KernelState, batch_id: str, timestamp_utc: str) -> dict:
        if self._has_comment_lines(normalized):
            report = self._build_report(
                report_kind="SNAPSHOT_ADMIT",
                timestamp_utc=timestamp_utc,
                result="FAIL",
                export_id="UNKNOWN",
                ruleset_header_match="UNKNOWN",
                megaboot_header_match="UNKNOWN",
                entries=[{"id": "SNAPSHOT", "tag": "COMMENT_BAN", "detail": "MSG-002"}],
            )
            return {"status": "REJECT", "tag": "COMMENT_BAN", "output_text": report}

        if not self._snapshot_has_item_header(normalized):
            report = self._build_report(
                report_kind="SNAPSHOT_ADMIT",
                timestamp_utc=timestamp_utc,
                result="FAIL",
                export_id="UNKNOWN",
                ruleset_header_match="UNKNOWN",
                megaboot_header_match="UNKNOWN",
                entries=[{"id": "SNAPSHOT", "tag": "SNAPSHOT_NONVERBATIM", "detail": "MSG-003"}],
            )
            return {"status": "REJECT", "tag": "SNAPSHOT_NONVERBATIM", "output_text": report}

        report = self._build_report(
            report_kind="SNAPSHOT_ADMIT",
            timestamp_utc=timestamp_utc,
            result="PASS",
            export_id="UNKNOWN",
            ruleset_header_match="UNKNOWN",
            megaboot_header_match="UNKNOWN",
            entries=[],
        )
        return {"status": "PASS", "tag": "", "output_text": report}

    def _handle_sim_message(self, normalized: str, state: KernelState, batch_id: str, timestamp_utc: str) -> dict:
        if self._has_comment_lines(normalized):
            report = self._build_report(
                report_kind="SIM_EVIDENCE_INGEST",
                timestamp_utc=timestamp_utc,
                result="FAIL",
                export_id="UNKNOWN",
                ruleset_header_match="UNKNOWN",
                megaboot_header_match="UNKNOWN",
                entries=[{"id": "SIM_EVIDENCE", "tag": "COMMENT_BAN", "detail": "MSG-002"}],
            )
            return {"status": "REJECT", "tag": "COMMENT_BAN", "output_text": report}

        ingest = self.kernel.ingest_sim_evidence_pack(normalized, state, batch_id=batch_id)
        if ingest.get("status") != "OK":
            report = self._build_report(
                report_kind="SIM_EVIDENCE_INGEST",
                timestamp_utc=timestamp_utc,
                result="FAIL",
                export_id="UNKNOWN",
                ruleset_header_match="UNKNOWN",
                megaboot_header_match="UNKNOWN",
                entries=[{"id": "SIM_EVIDENCE", "tag": ingest.get("reason", "SCHEMA_FAIL"), "detail": "SIM_INGEST_FAIL"}],
            )
            return {"status": "FAIL", "tag": ingest.get("reason", "SCHEMA_FAIL"), "output_text": report}

        entries = [{"id": spec_id, "tag": "EVIDENCE_SATISFIED", "detail": "EV-002"} for spec_id in ingest.get("satisfied", [])]
        report = self._build_report(
            report_kind="SIM_EVIDENCE_INGEST",
            timestamp_utc=timestamp_utc,
            result="PASS",
            export_id="UNKNOWN",
            ruleset_header_match="UNKNOWN",
            megaboot_header_match="UNKNOWN",
            entries=entries,
        )
        return {"status": "PASS", "tag": "", "output_text": report}

    def _build_report(
        self,
        report_kind: str,
        timestamp_utc: str,
        result: str,
        export_id: str,
        ruleset_header_match: str,
        megaboot_header_match: str,
        entries: list[dict],
        accepted_count: int = 0,
        parked_count: int = 0,
        rejected_count: int = 0,
    ) -> str:
        lines = [
            "BEGIN REPORT v1",
            f"BOOT_ID: {self.boot_id}",
            f"TIMESTAMP_UTC: {timestamp_utc}",
            f"REPORT_KIND: {report_kind}",
            f"RESULT: {result}",
            f"EXPORT_ID: {export_id or 'UNKNOWN'}",
            f"RULESET_HEADER_MATCH {ruleset_header_match}",
            f"MEGABOOT_HEADER_MATCH {megaboot_header_match}",
            f"ACCEPTED_COUNT: {accepted_count}",
            f"PARKED_COUNT: {parked_count}",
            f"REJECTED_COUNT: {rejected_count}",
            "DETAIL:",
        ]
        if not entries:
            lines.append("  EMPTY")
        else:
            for row in entries:
                lines.append(f"  ITEM {row.get('id', '')} TAG {row.get('tag', '')} DETAIL {row.get('detail', '')}")
                if row.get("offender_rule"):
                    lines.append(f'  OFFENDER_RULE "{_escape(str(row.get("offender_rule", "")))}"')
                if row.get("offender_line"):
                    lines.append(f'  OFFENDER_LINE "{_escape(str(row.get("offender_line", "")))}"')
                if row.get("offender_literal"):
                    lines.append(f'  OFFENDER_LITERAL "{_escape(str(row.get("offender_literal", "")))}"')
        lines.append("END REPORT v1")
        return "\n".join(lines) + "\n"

    def _dump_ledger_bodies(self, state: KernelState, timestamp_utc: str) -> str:
        lines = [
            "BEGIN DUMP_LEDGER_BODIES v1",
            f"BOOT_ID: {self.boot_id}",
            f"TIMESTAMP_UTC: {timestamp_utc}",
            "SURVIVOR_LEDGER_BODIES:",
        ]
        for item_id in sorted(state.survivor_ledger.keys()):
            item_text = str(state.survivor_ledger[item_id].get("item_text", "")).strip("\n")
            if not item_text:
                continue
            for line in item_text.splitlines():
                lines.append(f"  {line}")
        lines.append("PARK_SET_BODIES:")
        for item_id in sorted(state.park_set.keys()):
            item_text = str(state.park_set[item_id].get("item_text", "")).strip("\n")
            if not item_text:
                continue
            for line in item_text.splitlines():
                lines.append(f"  {line}")
        lines.append("END DUMP_LEDGER_BODIES v1")
        return "\n".join(lines) + "\n"

    def _dump_terms(self, state: KernelState, timestamp_utc: str) -> str:
        lines = [
            "BEGIN DUMP_TERMS v1",
            f"BOOT_ID: {self.boot_id}",
            f"TIMESTAMP_UTC: {timestamp_utc}",
            "TERM_REGISTRY:",
        ]
        for term in sorted(state.term_registry.keys()):
            entry = state.term_registry[term]
            state_value = entry.get("state", "")
            bound_math = entry.get("bound_math_def", "") or "NONE"
            required = entry.get("required_evidence", "") or "EMPTY"
            lines.append(f"  TERM {term} STATE {state_value} BINDS {bound_math} REQUIRED_EVIDENCE {required}")
        lines.append("END DUMP_TERMS v1")
        return "\n".join(lines) + "\n"

    def _dump_index(self, state: KernelState, timestamp_utc: str) -> str:
        by_class_status: dict[tuple[str, str], list[str]] = {}
        for item_id in sorted(state.survivor_ledger.keys()):
            row = state.survivor_ledger[item_id]
            key = (str(row.get("class", "")), str(row.get("status", "")))
            by_class_status.setdefault(key, []).append(item_id)

        lines = [
            "BEGIN REPORT v1",
            f"BOOT_ID: {self.boot_id}",
            f"TIMESTAMP_UTC: {timestamp_utc}",
            "REPORT_KIND: DUMP_INDEX",
            "RESULT: PASS",
            "DETAIL:",
        ]
        for key in sorted(by_class_status.keys()):
            cls, status = key
            ids = ",".join(by_class_status[key])
            lines.append(f"  CLASS {cls} STATUS {status} COUNT {len(by_class_status[key])} IDS {ids}")
        lines.append("END REPORT v1")
        return "\n".join(lines) + "\n"

    def _dump_evidence_pending(self, state: KernelState, timestamp_utc: str) -> str:
        lines = [
            "BEGIN REPORT v1",
            f"BOOT_ID: {self.boot_id}",
            f"TIMESTAMP_UTC: {timestamp_utc}",
            "REPORT_KIND: DUMP_EVIDENCE_PENDING",
            "RESULT: PASS",
            "DETAIL:",
        ]
        if not state.evidence_pending:
            lines.append("  EMPTY")
        for spec_id in sorted(state.evidence_pending.keys()):
            for token in sorted(state.evidence_pending[spec_id]):
                lines.append(f"  PENDING {spec_id} REQUIRES_EVIDENCE {token}")
        lines.append("END REPORT v1")
        return "\n".join(lines) + "\n"

    def _report_policy_state(self, state: KernelState, timestamp_utc: str) -> str:
        equals_allowed = self._term_canonical_allowed(state, "equals_sign")
        digit_allowed = self._term_canonical_allowed(state, "digit_sign")
        lines = [
            "BEGIN REPORT v1",
            f"BOOT_ID: {self.boot_id}",
            f"TIMESTAMP_UTC: {timestamp_utc}",
            "REPORT_KIND: REPORT_POLICY_STATE",
            "RESULT: PASS",
            "POLICY_FLAGS:",
            f"  ACTIVE_RULESET_SHA256_EMPTY {'TRUE' if not state.active_ruleset_sha256 else 'FALSE'}",
            f"  RULESET_SHA256_HEADER_REQUIRED {'TRUE' if state.active_ruleset_sha256 else 'FALSE'}",
            f"  ACTIVE_MEGABOOT_SHA256_EMPTY {'TRUE' if not state.active_megaboot_sha256 else 'FALSE'}",
            f"  MEGABOOT_SHA256_HEADER_REQUIRED {'TRUE' if state.active_megaboot_sha256 else 'FALSE'}",
            f"  EQUALS_SIGN_CANONICAL_ALLOWED {'TRUE' if equals_allowed else 'FALSE'}",
            f"  DIGIT_SIGN_CANONICAL_ALLOWED {'TRUE' if digit_allowed else 'FALSE'}",
            "END REPORT v1",
        ]
        return "\n".join(lines) + "\n"

    def _report_state(self, state: KernelState, timestamp_utc: str) -> str:
        lines = [
            "BEGIN REPORT v1",
            f"BOOT_ID: {self.boot_id}",
            f"TIMESTAMP_UTC: {timestamp_utc}",
            "REPORT_KIND: REPORT_STATE",
            "RESULT: PASS",
            "DETAIL:",
            f"  SURVIVOR_COUNT {len(state.survivor_ledger)}",
            f"  PARK_COUNT {len(state.park_set)}",
            f"  EVIDENCE_PENDING_COUNT {len(state.evidence_pending)}",
            f"  ACCEPTED_BATCH_COUNT {state.accepted_batch_count}",
            f"  UNCHANGED_LEDGER_STREAK {state.unchanged_ledger_streak}",
            "END REPORT v1",
        ]
        return "\n".join(lines) + "\n"

    def _term_canonical_allowed(self, state: KernelState, term: str) -> bool:
        entry = state.term_registry.get(term.lower())
        return bool(entry and entry.get("state") == "CANONICAL_ALLOWED")

    def _header_match(self, active_sha256: str, candidate: str) -> str:
        if not active_sha256:
            return "UNKNOWN"
        if candidate and candidate.lower() == active_sha256.lower():
            return "TRUE"
        return "FALSE"

    def _has_comment_lines(self, normalized: str) -> bool:
        for line in normalized.splitlines():
            stripped = line.strip()
            if stripped.startswith("#") or stripped.startswith("//"):
                return True
        return False

    def _snapshot_has_item_header(self, normalized: str) -> bool:
        lines = normalized.splitlines()
        in_survivor = False
        for line in lines:
            stripped = line.strip()
            if stripped == "SURVIVOR_LEDGER:":
                in_survivor = True
                continue
            if in_survivor and stripped.endswith(":") and stripped not in {"SURVIVOR_LEDGER:"}:
                break
            if in_survivor:
                if stripped.startswith(("AXIOM_HYP ", "PROBE_HYP ", "SPEC_HYP ")):
                    return True
        return False

    def _is_command_message(self, normalized: str) -> bool:
        if not normalized:
            return False
        lines = normalized.splitlines()
        if not lines:
            return False
        for line in lines:
            stripped = line.strip()
            if not stripped or not stripped.startswith("REQUEST "):
                return False
        return True

    def _is_export_message(self, normalized: str) -> bool:
        if not normalized:
            return False
        lines = normalized.splitlines()
        begin_count = sum(1 for line in lines if line.strip().startswith("BEGIN EXPORT_BLOCK "))
        end_count = sum(1 for line in lines if line.strip().startswith("END EXPORT_BLOCK "))
        if begin_count != 1 or end_count != 1:
            return False
        try:
            parse_export_block(normalized)
        except Exception:
            return False
        return True

    def _is_sim_evidence_pack_message(self, normalized: str) -> bool:
        if not normalized:
            return False
        try:
            blocks = parse_sim_evidence_pack(normalized)
        except Exception:
            return False
        return len(blocks) > 0

    def _is_snapshot_message(self, normalized: str) -> bool:
        if not normalized:
            return False
        lines = normalized.splitlines()
        begin_count = sum(1 for line in lines if line.strip() == "BEGIN THREAD_S_SAVE_SNAPSHOT v2")
        end_count = sum(1 for line in lines if line.strip() == "END THREAD_S_SAVE_SNAPSHOT v2")
        if begin_count != 1 or end_count != 1:
            return False
        if lines[0].strip() != "BEGIN THREAD_S_SAVE_SNAPSHOT v2":
            return False
        if lines[-1].strip() != "END THREAD_S_SAVE_SNAPSHOT v2":
            return False
        return True
