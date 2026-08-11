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
NV_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
MIN_TOKENS = 400          # below this, reasoning models return content=None

FREE = ["nvidia/nemotron-3-super-120b-a12b:free",
        "nvidia/nemotron-nano-9b-v2:free",
        "openai/gpt-oss-20b:free",
        "inclusionai/ling-3.0-tiny:free",
        "cohere/north-mini-code:free",
        "nvidia/nemotron-3-nano-30b-a3b:free"]

# NVIDIA's own API (integrate.api.nvidia.com), free tier, OpenAI-compatible.
# Verified present in the catalog on this machine.
NVIDIA = ["nvidia/llama-3.3-nemotron-super-49b-v1.5",
          "nvidia/llama-3.1-nemotron-70b-instruct",
          "meta/llama-3.3-70b-instruct",
          "deepseek-ai/deepseek-v4-flash-0731",
          "mistralai/mistral-large-2-instruct",
          "qwen/qwen3-next-80b-a3b-instruct"]

def _key(env_name: str, *files) -> str:
    """Env first, then a shell file. Never printed, never written to a receipt."""
    k = os.environ.get(env_name, "")
    if k:
        return k
    for f in files:
        p = Path(f).expanduser()
        if p.is_file():
            for line in p.read_text().splitlines():
                if env_name in line and "=" in line:
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""

def or_key() -> str:
    return _key("OPENROUTER_API_KEY", "~/.config/openrouter/env.sh", "~/.zshrc")

def nv_key() -> str:
    return _key("NVIDIA_API_KEY", "~/.zshrc", "~/.zshenv")

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

def ask_nvidia(model: str, prompt: str, max_tokens: int = 600,
               timeout: int = 120) -> dict:
    """NVIDIA's own free API. Same OpenAI-compatible shape as OpenRouter."""
    key = nv_key()
    if not key:
        return {"provider": "nvidia", "model": model, "ok": False, "text": "",
                "error": "NVIDIA_API_KEY not found", "sec": 0.0}
    body = json.dumps({"model": model, "max_tokens": max(max_tokens, MIN_TOKENS),
                       "temperature": 0.6,
                       "messages": [{"role": "user", "content": prompt}]}).encode()
    req = urllib.request.Request(NV_URL, data=body,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json",
                 "Accept": "application/json"})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            d = json.load(r)
        m = d["choices"][0]["message"]
        txt = (m.get("content") or "").strip()
        return {"provider": "nvidia", "model": model, "ok": bool(txt), "text": txt,
                "reasoning_chars": len(m.get("reasoning_content") or ""),
                "finish": d["choices"][0].get("finish_reason"),
                "sec": round(time.time() - t0, 1), "usage": d.get("usage", {})}
    except Exception as e:
        return {"provider": "nvidia", "model": model, "ok": False, "text": "",
                "error": f"{type(e).__name__}: {str(e)[:70]}",
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

def ask_codex(prompt: str, timeout: int = 180, profile: str = "") -> dict:
    """codex1 is `CODEX_HOME=~/.codex codex`. --profile selects e.g. luna."""
    t0 = time.time()
    cmd = ["codex", "exec", "--skip-git-repo-check"]
    if profile:
        cmd += ["--profile", profile]
    cmd.append(prompt)
    env = dict(os.environ, CODEX_HOME=str(Path.home() / ".codex"))
    label = f"codex-{profile}" if profile else "codex-native"
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                           stdin=subprocess.DEVNULL, cwd="/tmp", env=env)
        txt = (p.stdout or "").strip()
        return {"provider": "openai", "model": label, "ok": bool(txt),
                "text": txt[-1200:], "sec": round(time.time() - t0, 1),
                "rc": p.returncode}
    except Exception as e:
        return {"provider": "openai", "model": label, "ok": False,
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

def call_lane(lane: str, prompt: str):
    """Resolve one lane name to one provider call.

      haiku                 anthropic CLI (cheapest paid lane)
      codex / codex:luna    codex1 exec, optional --profile
      gemini                gemini CLI
      nv:<model>            NVIDIA's own free API
      anything else         OpenRouter model id
    """
    if lane == "haiku":
        return ask_claude(prompt, "haiku")
    if lane.startswith("codex"):
        return ask_codex(prompt, profile=lane.split(":", 1)[1] if ":" in lane else "")
    if lane == "gemini":
        return ask_gemini(prompt)
    if lane.startswith("nv:"):
        return ask_nvidia(lane[3:], prompt)
    return ask_openrouter(lane, prompt)

def fanout(prompt: str, lanes: list, width: int = 6) -> list:
    """one question, many PROVIDERS. Lateral across families."""
    with cf.ThreadPoolExecutor(max_workers=max(width, 1)) as ex:
        return list(ex.map(lambda l: call_lane(l, prompt), lanes))

# A model's family is its VENDOR, read off the model id. The `provider` field is
# the routing path we chose, so counting it made five OpenRouter lanes reaching
# four different vendors score families=1 and any two CLIs score families=2.
def family_of(r: dict) -> str:
    m = str(r.get("model", "")).lower()
    for vendor in ("nvidia", "nemotron", "llama", "meta", "deepseek", "mistral",
                   "qwen", "cohere", "gemini", "claude", "haiku", "sonnet", "opus",
                   "gpt", "codex", "ling", "inclusionai"):
        if vendor in m:
            return {"nemotron": "nvidia", "meta": "meta-llama", "llama": "meta-llama",
                    "haiku": "anthropic", "sonnet": "anthropic", "opus": "anthropic",
                    "claude": "anthropic", "codex": "openai", "gpt": "openai",
                    "ling": "inclusionai"}.get(vendor, vendor)
    return str(r.get("provider", "unknown"))

def provider_diversity(results: list) -> dict:
    """ClaimGate's rule: a swarm is real only if the RECEIPTS are diverse."""
    live = [r for r in results if r["ok"] and r["text"]]
    fams = {family_of(r) for r in live}
    routes = {r.get("provider") for r in live}
    texts = [" ".join(r["text"].split()).lower()[:600] for r in live]
    sims = [difflib.SequenceMatcher(None, a, b).ratio()
            for a, b in itertools.combinations(texts, 2)] or [0]
    mean = sum(sims) / len(sims)
    return {"lanes_called": len(results), "lanes_live": len(live),
            "model_families": sorted(fams), "families": len(fams),
            "routing_paths": sorted(x for x in routes if x),
            "mean_similarity": round(mean, 3), "max_similarity": round(max(sims), 3),
            "verdict": ("FAKE_SWARM: one model family" if len(fams) < 2 else
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
