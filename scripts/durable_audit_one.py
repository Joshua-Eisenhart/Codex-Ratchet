#!/usr/bin/env python3
"""Durable single-rung audit. AUTHORITY = Codex gpt-5.5 xhigh fresh read-only.
ALT-VIEWS = current xAI/Gemini advisory models -- surface possibilities, NOT verdicts.
Records source_sha256, prompt_sha256, FULL raw outputs, model ids, source mtime. Writes a receipt JSON.
Usage: durable_audit_one.py '<glob>' [rung_name]"""
import sys, glob, json, os, re, hashlib, urllib.request, datetime, subprocess

ALT = {
    "grok43": "grok-4.3",
    "grok_build": "grok-build-0.1",
    "gemini31pro": "gemini-3.1-pro-preview",
    "gemini35flash": "gemini-3.5-flash",
}
RECEIPTS = "/Users/joshuaeisenhart/Codex-Ratchet/system_v5/ops/audit_receipts"
Q = ("This is an SMT-backed sim leg. Its claim rests on a negative-control flip (a constraint dropped giving UNSAT<->SAT). "
     "Decide GENUINE (the solver DERIVES the contradiction by COMPUTING the quantity in-solver from bound structure "
     "constants / matrix entries) vs DECORATIVE (it binds a PRECOMPUTED scalar/coefficient/boolean and re-checks it, a "
     "free-boolean P-and-not-P, a hardcoded literal, or a state-independent tautology). "
     "Answer with ONE final line EXACTLY: VERDICT=GENUINE|DECORATIVE; LINE=<n>; REASON=<one sentence>.")
files = sorted(glob.glob(sys.argv[1]))
rung = sys.argv[2] if len(sys.argv) > 2 else (files[0].split("/")[-1] if files else sys.argv[1].split("/")[-1])
if not files:
    print(json.dumps({"rung": rung, "authority": "NOFILE", "receipt": None})); sys.exit(0)
path = files[0]; src = open(path, encoding="utf-8").read()
src_sha = hashlib.sha256(src.encode()).hexdigest(); src_mtime = os.path.getmtime(path)
prompt_sha = hashlib.sha256(Q.encode()).hexdigest()
XAI = os.environ.get("XAI_API_KEY"); GEM = os.environ.get("GEMINI_API_KEY")
def post(u, d, h, t=240):
    return json.loads(urllib.request.urlopen(urllib.request.Request(u, data=json.dumps(d).encode(), headers=h, method="POST"), timeout=t).read().decode())
def vparse(t):
    m = re.findall(r"VERDICT\s*=\s*(GENUINE|DECORATIVE)", t, re.I)
    return m[-1].upper() if m else ("ERROR" if t.startswith("ERROR") else "UNPARSED")
def alt(mid):
    try:
        if mid.startswith("grok"):
            if not XAI:
                return "ERROR missing XAI_API_KEY", mid, None
            d = post("https://api.x.ai/v1/chat/completions", {"model": mid, "temperature": 0, "max_tokens": 6000,
                     "messages": [{"role": "user", "content": Q + "\n\nSOURCE:\n" + src}]},
                     {"Authorization": f"Bearer {XAI}", "Content-Type": "application/json"})
            return d["choices"][0]["message"].get("content", "").strip(), d.get("model", mid), d.get("id")
        if not GEM:
            return "ERROR missing GEMINI_API_KEY", mid, None
        d = post(f"https://generativelanguage.googleapis.com/v1beta/models/{mid}:generateContent?key={GEM}",
                 {"contents": [{"parts": [{"text": Q + "\n\nSOURCE:\n" + src}]}]}, {"Content-Type": "application/json"})
        return "".join(p.get("text", "") for p in d["candidates"][0]["content"]["parts"]).strip(), d.get("modelVersion", mid), d.get("responseId")
    except Exception as e:
        return f"ERROR {getattr(e,'code',type(e).__name__)}", mid, None
def authority():
    prompt = "AUDIT ONLY. Read-only: do NOT edit, build, or run anything. " + Q + "\n\nSOURCE:\n" + src
    env = dict(os.environ)
    _ah = os.environ.get("DURABLE_AUDIT_CODEX_HOME")  # auditor instance (!= builder); default codex1, set ~/.codex-second to use codex2
    if _ah: env["CODEX_HOME"] = os.path.expanduser(_ah)
    try:
        r = subprocess.run(["codex", "exec", "--dangerously-bypass-approvals-and-sandbox", "--skip-git-repo-check",
                            "-C", "/Users/joshuaeisenhart/Codex-Ratchet", "-c", "model=gpt-5.5", "-c", "model_reasoning_effort=xhigh", prompt],
                           capture_output=True, text=True, timeout=900, env=env)
        out = (r.stdout or "") + (r.stderr or "")
        return vparse(out), out, r.returncode
    except Exception as e:
        return f"ERROR {type(e).__name__}", str(e), None
alt_views = {}
for k, mid in ALT.items():
    txt, m, rid = alt(mid)
    alt_views[k] = {"model_id": m, "response_id": rid, "verdict": vparse(txt), "raw": txt}
auth_v, auth_raw, auth_returncode = authority()
receipt = {"schema_version": "durable_audit_receipt_v2",
           "rung": rung, "file": path, "file_realpath": os.path.realpath(path),
           "source_sha256": src_sha, "source_size_bytes": len(src.encode()),
           "source_mtime": src_mtime,
           "source_mtime_iso": datetime.datetime.utcfromtimestamp(src_mtime).isoformat() + "Z",
           "prompt_sha256": prompt_sha, "audited_at": datetime.datetime.utcnow().isoformat() + "Z",
           "authority": {"model": "codex gpt-5.5 xhigh fresh read-only", "returncode": auth_returncode, "verdict": auth_v, "raw": auth_raw},
           "alt_views": alt_views}
os.makedirs(RECEIPTS, exist_ok=True)
rp = f"{RECEIPTS}/{rung}__{src_sha[:12]}.json"
json.dump(receipt, open(rp, "w"), indent=2)
print(json.dumps({"rung": rung, "AUTHORITY": auth_v, "alt": {k: alt_views[k]["verdict"] for k in alt_views},
                  "source_sha256": src_sha[:12], "receipt": rp}))
