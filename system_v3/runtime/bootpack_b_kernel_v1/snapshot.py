from state import KernelState


def build_snapshot_v2(
    state: KernelState,
    boot_id: str = "BOOTPACK_THREAD_B_v3.9.13",
    timestamp_utc: str = "",
    lexicographic: bool = True,
) -> str:
    lines: list[str] = []
    lines.append("BEGIN THREAD_S_SAVE_SNAPSHOT v2")
    lines.append(f"BOOT_ID: {boot_id}")
    if timestamp_utc:
        lines.append(f"TIMESTAMP_UTC: {timestamp_utc}")
    lines.append("SURVIVOR_LEDGER:")
    survivor_ids = sorted(state.survivor_ledger.keys()) if lexicographic else list(state.survivor_order)
    for item_id in survivor_ids:
        item = state.survivor_ledger.get(item_id)
        if not item:
            continue
        for line in str(item.get("item_text", "")).splitlines():
            lines.append(f"  {line}")
    lines.append("PARK_SET:")
    parked_with_bodies = False
    for item_id in sorted(state.park_set.keys()):
        entry = state.park_set[item_id]
        item_text = str(entry.get("item_text", "")).strip("\n")
        if not item_text:
            continue
        parked_with_bodies = True
        for line in item_text.splitlines():
            lines.append(f"  {line}")
    if not parked_with_bodies:
        lines.append("  EMPTY")
    lines.append("TERM_REGISTRY:")
    for term in sorted(state.term_registry.keys()):
        entry = state.term_registry[term]
        state_value = entry.get("state", "")
        bound = entry.get("bound_math_def", "") or "NONE"
        required = entry.get("required_evidence", "")
        required_value = required if required else "EMPTY"
        lines.append(f"  TERM {term} STATE {state_value} BINDS {bound} REQUIRED_EVIDENCE {required_value}")
    lines.append("EVIDENCE_PENDING:")
    has_pending = False
    for spec_id in sorted(state.evidence_pending.keys()):
        tokens = sorted(state.evidence_pending[spec_id])
        for token in tokens:
            has_pending = True
            lines.append(f"  PENDING {spec_id} REQUIRES_EVIDENCE {token}")
    if not has_pending:
        lines.append("  EMPTY")
    lines.append("PROVENANCE:")
    lines.append(f"  ACCEPTED_BATCH_COUNT={state.accepted_batch_count}")
    lines.append(f"  UNCHANGED_LEDGER_STREAK={state.unchanged_ledger_streak}")
    lines.append(f"  ACTIVE_MEGABOOT_ID={state.active_megaboot_id}")
    lines.append(f"  ACTIVE_MEGABOOT_SHA256={state.active_megaboot_sha256}")
    lines.append("END THREAD_S_SAVE_SNAPSHOT v2")
    return "\n".join(lines) + "\n"
