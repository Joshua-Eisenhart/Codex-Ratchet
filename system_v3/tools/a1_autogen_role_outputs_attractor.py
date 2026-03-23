#!/usr/bin/env python3
"""
Local "host LLM" substitute for the A1 LLM lane.

This intentionally does NOT try to be smart. It exists so the ZIP-subagent
protocol can run end-to-end *inside Codex* without requiring an external
ChatUI thread.

It reads the emitted prompt files only to recover the required BRANCH_TRACK
anchor tokens and then generates a schema-valid A1_STRATEGY_v1 with:
- massive alternative count (default 1000)
- explicit BRANCH_TRACK on every candidate
- minimum coverage across anchors

This is a mechanical wiggle generator, not a theory generator.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
from pathlib import Path


_TRACK_RE = re.compile(r"^\s*\*\s*(TRACK_[A-Z0-9_]+)\s*$", re.IGNORECASE)


def _now_utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _sha256(obj: object) -> str:
    data = json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _extract_tracks(prompt_text: str) -> list[str]:
    tracks: list[str] = []
    in_list = False
    for line in prompt_text.splitlines():
        if "BRANCH_TRACK must be one of" in line:
            in_list = True
            continue
        if in_list:
            m = _TRACK_RE.match(line)
            if m:
                tracks.append(m.group(1).upper())
                continue
            # stop when list ends
            if line.strip() == "" or line.strip().startswith("Coverage:"):
                in_list = False
    # deterministic order
    return sorted(set(tracks))


def _candidate(
    *,
    cid: str,
    probe_id: str,
    track: str,
    salt: str,
    kind: str = "MATH_DEF",
) -> dict:
    # All token-like strings must be lower_snake_case-ish to satisfy kernel
    # mixed-case bans (this is still only a best-effort here).
    base = f"{track.lower()}_{salt}"
    return {
        "item_class": "SPEC_HYP",
        "id": cid,
        "kind": kind,
        "operator_id": "OP_REPAIR_DEF_FIELD",
        "requires": [probe_id],
        "asserts": [
            {"assert_id": "A_PROBE", "token_class": "PROBE_TOKEN", "token": f"PT_{probe_id}"},
        ],
        "def_fields": [
            {"field_id": "F_KIND", "name": "PROBE_KIND", "value_kind": "TOKEN", "value": "A1_GENERATED"},
            {"field_id": "F_TRACK", "name": "BRANCH_TRACK", "value_kind": "TOKEN", "value": track},
            {"field_id": "F_OBJ", "name": "OBJECTS", "value_kind": "TOKEN", "value": f"{base}_objects"},
            {"field_id": "F_OPS", "name": "OPERATIONS", "value_kind": "TOKEN", "value": f"{base}_operations"},
            {"field_id": "F_INV", "name": "INVARIANTS", "value_kind": "TOKEN", "value": f"{base}_invariants"},
            {"field_id": "F_DOM", "name": "DOMAIN", "value_kind": "TOKEN", "value": f"{base}_domain"},
            {"field_id": "F_COD", "name": "CODOMAIN", "value_kind": "TOKEN", "value": f"{base}_codomain"},
            {
                "field_id": "F_SIMHASH",
                "name": "SIM_CODE_HASH_SHA256",
                "value_kind": "TOKEN",
                "value": "0" * 64,
            },
        ],
    }


def _sim_plan(*, sim_id: str, binds_to: str) -> dict:
    return {"sim_id": sim_id, "binds_to": binds_to}


def _memo(*, run_id: str, sequence: int, role: str, tracks: list[str]) -> dict:
    return {
        "schema": "A1_LAWYER_MEMO_v1",
        "run_id": run_id,
        "sequence": sequence,
        "role": role,
        "claims": [],
        "risks": [],
        "graveyard_rescue_targets": [],
        "proposed_negative_classes": [],
        "proposed_terms": [],
        "note": f"AUTOGEN placeholder memo. tracks={tracks}",
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--combined-prompt", required=True, help="Path to COMBINED_PROMPT__A1_LLM_LANE__v1.md")
    ap.add_argument("--prompts-dir", required=True, help="Directory containing prompt .txt files")
    ap.add_argument("--out-dir", required=True, help="Directory to write role_outputs/*.json")
    ap.add_argument("--probe-id", default="P_A020002_lexeme_bound_realization", help="Existing probe id to reuse.")
    ap.add_argument("--total", type=int, default=1000)
    ap.add_argument("--pos-sims", type=int, default=60)
    ap.add_argument("--neg-sims", type=int, default=60)
    args = ap.parse_args(argv)

    combined = Path(args.combined_prompt).expanduser().resolve()
    prompts_dir = Path(args.prompts_dir).expanduser().resolve()
    out_dir = Path(args.out_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    tracks = _extract_tracks(_read_text(combined))
    if not tracks:
        raise SystemExit("no BRANCH_TRACK anchors found in combined prompt")

    # Ensure we always use at least 4 tracks and distribute evenly.
    tracks = tracks[:]
    if len(tracks) < 4:
        raise SystemExit(f"need >=4 BRANCH_TRACK anchors, found {len(tracks)}: {tracks}")

    total = int(args.total)
    if total < 200:
        raise SystemExit("total too small; use >=200")

    per_track_floor = 20
    used_tracks = tracks[:6]
    # deterministic distribution
    counts = {t: 0 for t in used_tracks}
    # seed floor
    for t in used_tracks:
        counts[t] = per_track_floor
    remaining = total - per_track_floor * len(used_tracks)
    i = 0
    while remaining > 0:
        t = used_tracks[i % len(used_tracks)]
        counts[t] += 1
        remaining -= 1
        i += 1

    probe_id = str(args.probe_id).strip()
    if not probe_id:
        raise SystemExit("missing probe-id")

    alternatives: list[dict] = []
    alt_index = 1
    for t in used_tracks:
        for j in range(counts[t]):
            cid = f"S{alt_index:04d}"
            alternatives.append(_candidate(cid=cid, probe_id=probe_id, track=t, salt=f"{alt_index:04d}"))
            alt_index += 1

    # Simple sims plan: bind sims to the first N candidates deterministically.
    pos_sims = int(args.pos_sims)
    neg_sims = int(args.neg_sims)
    sims_pos = [_sim_plan(sim_id=f"SIM_POS_{i+1:04d}", binds_to=alternatives[i]["id"]) for i in range(min(pos_sims, len(alternatives)))]
    sims_neg = [_sim_plan(sim_id=f"SIM_NEG_{i+1:04d}", binds_to=alternatives[-(i+1)]["id"]) for i in range(min(neg_sims, len(alternatives)))]

    strategy: dict = {
        "schema": "A1_STRATEGY_v1",
        "strategy_id": f"STRAT_{args.run_id}__AUTOGEN__{_now_utc().replace(':','').replace('-','')}",
        "inputs": {
            "state_hash": "0" * 64,
            "fuel_slice_hashes": [],
            "bootpack_rules_hash": "0" * 64,
            "pinned_ruleset_sha256": "0" * 64,
            "pinned_megaboot_sha256": "0" * 64,
        },
        "budget": {"max_items": len(alternatives), "max_sims": len(sims_pos) + len(sims_neg)},
        "policy": {
            "forbid_fields": sorted(["confidence", "embedding", "hidden_prompt", "probability", "raw_text"]),
            "overlay_ban_terms": [],
            "require_try_to_fail": True,
        },
        "targets": [
            _candidate(
                cid="S0000",
                probe_id=probe_id,
                track="TRACK_CONSTRAINT_LADDER",
                salt="target_0000",
            )
        ],
        "alternatives": alternatives,
        "sims": {"positive": sims_pos, "negative": sims_neg},
        "self_audit": {
            "strategy_hash": "",
            "compile_lane_digest": "",
            "candidate_count": 1,
            "alternative_count": len(alternatives),
            "operator_ids_used": ["STEELMAN_MASS", "ADVERSARIAL_NEG_MASS", "RESCUER_MASS", "ALT_FORMALISM_MASS", "PACK_SELECTOR_MASS"],
        },
    }
    # Fill hashes
    strategy_hash = _sha256(strategy)
    strategy["self_audit"]["strategy_hash"] = strategy_hash
    strategy["self_audit"]["compile_lane_digest"] = strategy_hash

    # Emit one output per prompt (memos for lanes, one strategy for PACK_SELECTOR).
    prompt_files = sorted(prompts_dir.glob("*.txt"), key=lambda p: p.name)
    if not prompt_files:
        raise SystemExit(f"no prompt .txt files found under: {prompts_dir}")
    # Try to infer sequence from filename prefix.
    seq = 0
    try:
        seq = int(prompt_files[0].name.split("_", 1)[0])
    except Exception:
        seq = 0

    for p in prompt_files:
        out_name = p.name[:-4] + ".json"
        role_upper = "UNKNOWN"
        try:
            # ..._ROLE_N_ROLELABEL__A1_PROMPT.txt
            role_upper = p.name.split("_ROLE_", 1)[1].split("__", 1)[0]
        except Exception:
            role_upper = "UNKNOWN"
        if "PACK_SELECTOR" in p.name:
            (out_dir / out_name).write_text(json.dumps(strategy, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        else:
            memo = _memo(run_id=args.run_id, sequence=seq if seq > 0 else 1, role=role_upper, tracks=used_tracks)
            (out_dir / out_name).write_text(json.dumps(memo, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
