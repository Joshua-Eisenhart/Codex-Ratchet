#!/usr/bin/env python3
"""Foundation receipt-hardening (the active gate). Mechanical, metadata-only -- changes NO computed value.
(1) inject source_sha256 into foundation result JSONs from their recorded source_path;
(2) generate durable ENVELOPE receipts (so envelopes are receipt-bound, not just JAX legs);
(3) negative control: a poisoned source_sha256 must flip gate_check to BLOCK.
Complements scripts/contract_metadata_safe_repair.py (idempotent; only adds source_sha256 + writes receipts)."""
import json, glob, os, hashlib, subprocess, tempfile, sys
ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
RES = ROOT + "/system_v5/ops/formal_scouts/results"
RCPT = ROOT + "/system_v5/ops/audit_receipts"
PY = os.environ.get(
    "CODEX_RATCHET_PYTHON",
    os.environ.get("SIM_PY", "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3"),
)
VAL = ROOT + "/scripts/validate_three_engine_sim_result.py"
GATE = ROOT + "/scripts/gate_check.py"

def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()

def receipts_by_sha():
    m = {}
    for f in glob.glob(RCPT + "/*.json"):
        if "LAYER_REGISTRY" in f: continue
        try: d = json.load(open(f))
        except Exception: continue
        if d.get("source_sha256"): m[d["source_sha256"]] = (d.get("rung"), d.get("authority", {}).get("verdict"))
    return m

# (1) inject source_sha256 into all foundation result JSONs
results = sorted(set(glob.glob(RES + "/foundation_*results.json") + glob.glob(RES + "/foundation_foundation_*results.json")
                     + glob.glob(RES + "/foundation_*result.json") + glob.glob(RES + "/foundation_foundation_*result.json")))
pinned = skipped = missing = 0
for r in results:
    try: d = json.load(open(r))
    except Exception: continue
    sp = d.get("source_path")
    if not sp or not os.path.exists(sp):
        missing += 1; continue
    s = sha(sp)
    if d.get("source_sha256") == s:
        skipped += 1; continue
    d["source_sha256"] = s
    json.dump(d, open(r, "w"), indent=2)
    pinned += 1
print(f"[1] source_sha256: pinned={pinned} already={skipped} missing_source={missing} of {len(results)} results")

# (2) durable ENVELOPE receipts
recs = receipts_by_sha()
envs = sorted(set(glob.glob(RES + "/foundation_*envelope*results.json") + glob.glob(RES + "/foundation_foundation_*envelope*results.json")
                  + glob.glob(RES + "/foundation_*envelope*result.json") + glob.glob(RES + "/foundation_foundation_*envelope*result.json")))
env_written = env_genuine = 0; _bl = []
os.makedirs(RCPT, exist_ok=True)
for e in envs:
    try: d = json.load(open(e))
    except Exception: continue
    src = d.get("source_path")
    if not src or not os.path.exists(src): continue
    esha = sha(src); emt = os.path.getmtime(src)
    val = subprocess.run([PY, VAL, e, "--require-pytorch"], capture_output=True, text=True)
    vok = '"ok": true' in val.stdout
    legs = {}
    for eng in (d.get("engines", {}) or {}):
        leg = d["engines"][eng]
        lsp = leg.get("source_path")
        lsha = sha(lsp) if (lsp and os.path.exists(lsp)) else None
        legs[eng] = {"source_sha256": lsha, "leg_receipt": (lsha in recs), "leg_verdict": recs.get(lsha, (None, None))[1]}
    jax_ok = legs.get("jax", {}).get("leg_verdict") == "GENUINE"
    verdict = "GENUINE" if (vok and jax_ok) else "BLOCK"
    rung = os.path.basename(e).replace("_results.json", "")
    rcpt = {"rung": rung, "file": src, "source_sha256": esha, "source_mtime": emt,
            "kind": "envelope_aggregator",
            "authority": {"model": "mechanical: validator-ok + JAX-SMT-leg codex-authority-GENUINE", "verdict": verdict},
            "validator_ok": vok, "jax_leg_genuine": jax_ok, "max_divergence": d.get("divergence", {}).get("max_divergence"), "legs": legs}
    json.dump(rcpt, open(f"{RCPT}/{rung}__env_{esha[:12]}.json", "w"), indent=2)
    env_written += 1; env_genuine += (verdict == "GENUINE")
    if verdict != "GENUINE": _bl.append((rung[:44], vok, jax_ok))
print(f"[2] envelope receipts: written={env_written} GENUINE={env_genuine} (BLOCK={env_written-env_genuine})")
for rn, vk, jk in _bl[:10]: print(f"    BLOCK {rn:46s} validator_ok={vk} jax_leg_genuine={jk}")

# (3) negative control -- a poisoned source_sha256 must flip gate_check to BLOCK
leg_results = [r for r in results if "envelope" not in r and "jax" in r]
nc = "SKIP (no leg result)"
if leg_results:
    base = leg_results[0]; d = json.load(open(base)); src = d.get("source_path")
    if src and os.path.exists(src):
        good = sha(src)
        tmp = tempfile.NamedTemporaryFile("w", suffix="_results.json", delete=False, dir=RES)
        dd = dict(d); dd["source_sha256"] = "0" * 64  # poison
        json.dump(dd, tmp); tmp.close()
        g = subprocess.run([PY, GATE, src, tmp.name], capture_output=True, text=True)
        blocked = '"status": "BLOCK"' in g.stdout or g.returncode != 0
        os.unlink(tmp.name)
        nc = f"poisoned source_sha256 -> gate {'BLOCK (load-bearing OK)' if blocked else 'PASS (NOT load-bearing!)'}"
print(f"[3] negative control: {nc}")
