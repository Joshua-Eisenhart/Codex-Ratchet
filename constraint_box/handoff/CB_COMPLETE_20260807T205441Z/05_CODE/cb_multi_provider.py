#!/usr/bin/env python3
"""cb_multi_provider — subsubagents across PROVIDER FAMILIES, not just slices.

Provider diversity is the strongest form of input diversity: different
base models cannot collapse into one basin the way a single model with
different prompts can. This is the v4.3 model-family matrix requirement,
and ClaimGate's own test — "reject same-provider fake swarms; accept
arbitrary provider names when the returned receipts are diverse."

Lanes available on this machine, verified:
  anthropic-haiku   claude CLI via claude_child_fanout.py
  openrouter-free   17 free models, incl. 7 NVIDIA Nemotron variants
  codex-native      codex exec (CLI present)
  gemini            gemini CLI + gemini_child_fanout.py

Reasoning-model handling: several free models spend the token budget on
`reasoning` before emitting `content`. A low max_tokens returns
content=None — that is a BUDGET defect, not a dead model. Minimum 400.

promotion_allowed=false.
"""
from __future__ import annotations
import concurrent.futures as cf
import difflib, itertools, json, os, subprocess, sys, time, urllib.request
from pathlib import Path

OR_URL = "https://openrouter.ai/api/v1/chat/completions"
MIN_TOKENS = 400          # below this, reasoning models return content=None

FREE = ["nvidia/nemotron-3-super-120b-a12b:free",
        "nvidia/nemotron-nano-9b-v2:free",
        "openai/gpt-oss-20b:free",
        "inclusionai/ling-3.0-tiny:free",
        "cohere/north-mini-code:free",
        "nvidia/nemotron-3-nano-30b-a3b:free"]

def or_key() -> str:
    k = os.environ.get("OPENROUTER_API_KEY", "")
    if k: return k
    p = Path.home() / ".config/openrouter/env.sh"
    if p.is_file():
        for line in p.read_text().splitlines():
            if "OPENROUTER_API_KEY" in line and "=" in line:
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""

def ask_openrouter(model: str, prompt: str, max_tokens: int = 600,
                   timeout: int = 120) -> dict:
    key = or_key()
    body = json.dumps({"model": model, "max_tokens": max(max_tokens, MIN_TOKENS),
                       "messages": [{"role": "user", "content": prompt}]}).encode()
    req = urllib.request.Request(OR_URL, data=body,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            d = json.load(r)
        m = d["choices"][0]["message"]
        txt = (m.get("content") or "").strip()
        return {"provider": "openrouter", "model": model, "ok": bool(txt),
                "text": txt, "reasoning_chars": len(m.get("reasoning") or ""),
                "finish": d["choices"][0].get("finish_reason"),
                "sec": round(time.time() - t0, 1),
                "usage": d.get("usage", {})}
    except Exception as e:
        return {"provider": "openrouter", "model": model, "ok": False,
                "text": "", "error": f"{type(e).__name__}: {str(e)[:70]}",
                "sec": round(time.time() - t0, 1)}

def ask_claude(prompt: str, model: str = "haiku", timeout: int = 120) -> dict:
    t0 = time.time()
    try:
        p = subprocess.run(["claude", "-p", "--model", model,
                            "--output-format", "json", prompt],
                           capture_output=True, text=True, timeout=timeout,
                           stdin=subprocess.DEVNULL)
        d = json.loads(p.stdout or "{}")
        txt = str(d.get("result", "")).strip()
        return {"provider": "anthropic", "model": model,
                "ok": bool(txt) and not d.get("is_error"),
                "text": txt, "sec": round(time.time() - t0, 1),
                "cost_usd": d.get("total_cost_usd")}
    except Exception as e:
        return {"provider": "anthropic", "model": model, "ok": False, "text": "",
                "error": f"{type(e).__name__}: {str(e)[:70]}",
                "sec": round(time.time() - t0, 1)}

def ask_codex(prompt: str, timeout: int = 180) -> dict:
    t0 = time.time()
    try:
        p = subprocess.run(["codex", "exec", "--skip-git-repo-check", prompt],
                           capture_output=True, text=True, timeout=timeout,
                           stdin=subprocess.DEVNULL, cwd="/tmp")
        txt = (p.stdout or "").strip()
        return {"provider": "codex", "model": "codex-native", "ok": bool(txt),
                "text": txt[-1200:], "sec": round(time.time() - t0, 1)}
    except Exception as e:
        return {"provider": "codex", "model": "codex-native", "ok": False,
                "text": "", "error": f"{type(e).__name__}: {str(e)[:70]}",
                "sec": round(time.time() - t0, 1)}

def ask_gemini(prompt: str, timeout: int = 120) -> dict:
    t0 = time.time()
    try:
        p = subprocess.run(["gemini", "-p", prompt], capture_output=True,
                           text=True, timeout=timeout, stdin=subprocess.DEVNULL)
        txt = (p.stdout or "").strip()
        return {"provider": "google", "model": "gemini-cli", "ok": bool(txt),
                "text": txt[-1200:], "sec": round(time.time() - t0, 1)}
    except Exception as e:
        return {"provider": "google", "model": "gemini-cli", "ok": False,
                "text": "", "error": f"{type(e).__name__}: {str(e)[:70]}",
                "sec": round(time.time() - t0, 1)}

def fanout(prompt: str, lanes: list, width: int = 6) -> list:
    """one question, many PROVIDERS. Lateral across families."""
    calls = []
    for lane in lanes:
        if lane == "haiku":   calls.append(lambda p=prompt: ask_claude(p, "haiku"))
        elif lane == "codex": calls.append(lambda p=prompt: ask_codex(p))
        elif lane == "gemini":calls.append(lambda p=prompt: ask_gemini(p))
        else:                 calls.append(lambda p=prompt, m=lane: ask_openrouter(m, p))
    with cf.ThreadPoolExecutor(max_workers=width) as ex:
        return list(ex.map(lambda f: f(), calls))

def provider_diversity(results: list) -> dict:
    """ClaimGate's rule: a swarm is real only if the RECEIPTS are diverse"""
    live = [r for r in results if r["ok"] and r["text"]]
    fams = {r["provider"] for r in live}
    texts = [" ".join(r["text"].split()).lower()[:600] for r in live]
    sims = [difflib.SequenceMatcher(None, a, b).ratio()
            for a, b in itertools.combinations(texts, 2)] or [0]
    mean = sum(sims) / len(sims)
    return {"lanes_called": len(results), "lanes_live": len(live),
            "provider_families": sorted(fams), "families": len(fams),
            "mean_similarity": round(mean, 3), "max_similarity": round(max(sims), 3),
            "verdict": ("FAKE_SWARM: one family" if len(fams) < 2 else
                        "COLLAPSED: receipts too similar" if mean >= 0.75 else
                        "REAL_SWARM: multiple families, diverse receipts")}


# ------------------------------------------------------------------ main
def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--claim", required=True)
    ap.add_argument("--lanes", default="haiku,nvidia/nemotron-3-super-120b-a12b:free,"
                    "nvidia/nemotron-nano-9b-v2:free,openai/gpt-oss-20b:free,"
                    "inclusionai/ling-3.0-tiny:free,cohere/north-mini-code:free")
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    lanes = [x.strip() for x in a.lanes.split(",") if x.strip()]
    Q = (f"TARGET CLAIM:\n{a.claim}\n\n"
         "Name the SINGLE strongest live falsifier for this claim: the one "
         "observation that would break it outright. Answer in one sentence "
         "under 30 words. State only the falsifier, no preamble.")
    t0 = time.time()
    print(f"MULTI-PROVIDER SUBSUBCOUNCIL — {len(lanes)} lanes, one question\n")
    res = fanout(Q, lanes, width=len(lanes))
    print(f"{'provider':<12}{'model':<42}{'sec':>6}  answer")
    for r in res:
        mark = "" if r["ok"] else "  [DEAD] " + r.get("error", "")[:40]
        txt = " ".join(r["text"].split())[:70] if r["ok"] else ""
        print(f"{r['provider']:<12}{r['model'][:41]:<42}{r['sec']:>6}  {txt}{mark}")
        if r.get("reasoning_chars"):
            print(f"{'':<60}  (reasoning {r['reasoning_chars']} chars before content)")
    d = provider_diversity(res)
    print(f"\nPROVIDER DIVERSITY AUDIT")
    print(f"   lanes called {d['lanes_called']}  live {d['lanes_live']}")
    print(f"   families: {d['provider_families']} ({d['families']})")
    print(f"   mean receipt similarity {d['mean_similarity']}  max {d['max_similarity']}")
    print(f"   VERDICT: {d['verdict']}")
    out = Path(a.out) if a.out else Path(
        "/Users/joshuaeisenhart/Codex-Ratchet/constraint_box/receipts") / \
        f"multiprovider_{time.strftime('%Y%m%dT%H%M%SZ')}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"schema": "cb.multi-provider.v1", "claim": a.claim,
        "lanes": lanes, "results": res, "diversity": d,
        "wall_seconds": round(time.time() - t0, 1), "promotion_allowed": False,
        "claim_ceiling": "provider diversity and lane liveness only"},
        indent=1, sort_keys=True))
    print(f"RECEIPT {out.name}  ({time.time()-t0:.1f}s)")
    return 0

if __name__ == "__main__":
    sys.exit(main())
