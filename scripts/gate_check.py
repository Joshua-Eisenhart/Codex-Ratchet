#!/usr/bin/env python3
"""Preflight gate (Codex P2, owner-calibrated). AUTHORITY = Codex gpt-5.5 xhigh; xAI/Gemini = advisory alt-views.
Usage: gate_check.py '<source_glob>' '<result_glob>'
PASS only if: a durable receipt pinned to the CURRENT source path + sha256 exists, its AUTHORITY verdict == GENUINE,
and the result JSON is not older than the source. Alt-view DECORATIVE flags are advisory (reported, not blocking)."""
import sys, glob, json, os, hashlib, datetime
RECEIPTS = "/Users/joshuaeisenhart/Codex-Ratchet/system_v5/ops/audit_receipts"
reasons = []; warnings = []; status = "PASS"
src_files = sorted(glob.glob(sys.argv[1]))
res_files = sorted(glob.glob(sys.argv[2])) if len(sys.argv) > 2 else []
if not src_files:
    print(json.dumps({"status": "BLOCK", "reasons": ["no source file"]})); sys.exit(2)
src = src_files[0]
src_real = os.path.realpath(src)
src_sha = hashlib.sha256(open(src, "rb").read()).hexdigest(); src_mtime = os.path.getmtime(src)
rec = None; rec_path = None; hash_only = []

def audited_key(item):
    value = item[0].get("audited_at") or ""
    try:
        return datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return datetime.datetime.min.replace(tzinfo=datetime.timezone.utc)

exact = []
for rf in glob.glob(RECEIPTS + "/*.json"):
    try:
        d = json.load(open(rf))
    except Exception:
        continue
    if d.get("source_sha256") == src_sha:
        receipt_real = os.path.realpath(d.get("file_realpath") or d.get("file") or "")
        if receipt_real == src_real:
            exact.append((d, rf))
        else:
            hash_only.append(rf)
if exact:
    rec, rec_path = sorted(exact, key=audited_key)[-1]
if rec is None:
    status = "BLOCK"
    if hash_only:
        reasons.append("durable receipt exists for CURRENT source_sha256 but a different source path (path mismatch)")
    else:
        reasons.append("no durable receipt pinned to CURRENT source path + sha256 (un-audited or hash drift)")
else:
    auth = rec.get("authority", {}).get("verdict")
    if auth != "GENUINE":
        status = "BLOCK"; reasons.append(f"AUTHORITY verdict = {auth} (need GENUINE)")
    alt = {k: v.get("verdict") for k, v in rec.get("alt_views", {}).items()}
    flagged = [k for k, v in alt.items() if v == "DECORATIVE"]
    if flagged:
        reasons.append(f"alt-views flagged (ADVISORY, surfaced for review, not blocking): {flagged}")
if res_files:
    res = res_files[0]
    if os.path.getmtime(res) + 1 < src_mtime:
        status = "BLOCK"; reasons.append("STALE: result older than source")
    try:
        result = json.load(open(res))
        result_source = result.get("source_path")
        if result_source and os.path.realpath(result_source) != src_real:
            status = "BLOCK"; reasons.append("result source_path does not match gated source")
        result_sha = result.get("source_sha256")
        if result_sha and result_sha != src_sha:
            status = "BLOCK"; reasons.append("result source_sha256 does not match gated source")
        if not result_sha:
            warnings.append("result JSON lacks source_sha256; freshness is mtime/path based")
    except Exception as exc:
        warnings.append(f"result JSON could not be parsed for path/hash linkage: {type(exc).__name__}")
else:
    status = "BLOCK"; reasons.append("no result JSON found")
print(json.dumps({"status": status, "source": src.split("/")[-1], "source_sha256": src_sha[:12], "receipt": rec_path, "reasons": reasons or ["fresh + authority GENUINE"], "warnings": warnings}))
sys.exit(0 if status == "PASS" else 2)
