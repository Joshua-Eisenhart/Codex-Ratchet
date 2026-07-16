#!/usr/bin/env python3
"""panel_adversarial_review.py -- route a sim's SOURCE + RESULTS through a cross-family LLM panel as INDEPENDENT
adversarial reviewers. Advisory only: the panel never gates a verdict (z3/cvc5 + the running sims do that, project
doctrine). Its job is to catch smuggled assumptions, tautological gates (a gate that cannot fail), unearned structure,
and overclaims -- the recurring failure mode -- from model families outside this session's own lineage.

Usage: python panel_adversarial_review.py <sim.py> [<results.json>]  (keys read from handoff/_apikeys.json)
"""
import json, os, sys, urllib.request, urllib.error

PANEL = [  # (label, provider, model)
    ("Gemini-3.1-pro","gemini","gemini-3.1-pro-preview"),
    ("Grok-4.5","xai","grok-4.5"),
    ("Qwen-3.5","nvidia","qwen/qwen3.5-397b-a17b"),
    ("GLM-5.2","nvidia","z-ai/glm-5.2"),
]
PROMPT = """You are an ADVERSARIAL scientific reviewer with a fresh context. You are handed the SOURCE and RESULTS of one
simulation from a constraint-based theory-of-everything project. The project's non-negotiable discipline: a gate that
CANNOT FAIL is a rubber stamp; structure must be FORCED by the constraints, not merely INSTALLED; external claims must be
attribution not verified fact; fixes go in the measurement never in the gate.

Your job: find the WEAKEST point. Specifically hunt for:
  1. A gate/assertion that is a TAUTOLOGY (true by construction/definition regardless of the physics) -- the worst sin.
  2. SMUGGLED structure: something asserted as forced/derived that is actually installed, fitted, or hand-picked.
  3. OVERCLAIM: the prose/verdict claiming more than the computation shows.
  4. A CONTROL that does not actually flip, or is ill-posed for the statistic it guards.

Be concrete: name the exact gate/line/claim. If a gate is genuinely sound and failable, say so explicitly. Do NOT be
agreeable by default -- your value is finding what an author's own eyes miss. Respond ONLY as JSON:
{"findings":[{"severity":"fail|warn|ok","target":"<exact gate/claim>","issue":"<one sentence>"}],"verdict":"<one line: is the core claim earned or overstated?>"}
"""

def _post(url, payload, headers, timeout=90):
    req=urllib.request.Request(url, data=json.dumps(payload).encode(), headers={"Content-Type":"application/json",**headers}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r: return r.status, json.load(r)
    except urllib.error.HTTPError as e: return e.code, e.read()[:200].decode('utf-8','replace')
    except Exception as e: return None, f"{type(e).__name__}: {str(e)[:120]}"

def ask(provider, model, K, content):
    if provider=="gemini":
        st,resp=_post(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key="+K["GOOGLE_API_KEY"],
            {"contents":[{"parts":[{"text":content}]}],"generationConfig":{"maxOutputTokens":8000,"temperature":0.3}},{})
        if st!=200: return None, str(resp)[:150]
        try:
            for p in resp["candidates"][0]["content"]["parts"]:
                if "text" in p: return p["text"], None
            return None, "no text part"
        except Exception as e: return None, f"parse {e}"
    else:
        url = "https://api.x.ai/v1/chat/completions" if provider=="xai" else "https://integrate.api.nvidia.com/v1/chat/completions"
        key = K["XAI_API_KEY"] if provider=="xai" else K["NVIDIA_API_KEY"]
        st,resp=_post(url,{"model":model,"messages":[{"role":"user","content":content}],"max_tokens":8000,"temperature":0.3},
            {"Authorization":"Bearer "+key})
        if st!=200: return None, str(resp)[:150]
        try: return resp["choices"][0]["message"]["content"], None
        except Exception as e: return None, f"parse {e}"

def extract_json(txt):
    import re
    m=re.search(r'\{.*\}', txt, re.DOTALL)
    if not m: return None
    for cand in (m.group(0),):
        try: return json.loads(cand)
        except Exception: pass
    return None

KEYS_PATH=os.environ.get("PANEL_KEYS","/Users/joshuaeisenhart/.claude-science/orgs/cd93c404-3ace-4713-b795-0756edc204c0/workspaces/e5f8866f-f4f1-4f45-b60b-61c153b13dac/handoff/_apikeys.json")
def review(sim_path, results_path=None):
    K=json.load(open(KEYS_PATH))
    src=open(sim_path).read()
    res=open(results_path).read() if results_path and os.path.exists(results_path) else "(no results file)"
    content=f"{PROMPT}\n\n=== SIM SOURCE ({os.path.basename(sim_path)}) ===\n{src}\n\n=== RESULTS JSON ===\n{res[:6000]}"
    out={}
    for label,prov,model in PANEL:
        txt,err=ask(prov,model,K,content)
        if err: out[label]={"error":err}; continue
        parsed=extract_json(txt)
        out[label]=parsed if parsed else {"raw":txt[:600]}
    return out

if __name__=="__main__":
    sim=sys.argv[1]; res=sys.argv[2] if len(sys.argv)>2 else None
    result=review(sim,res)
    outp=os.path.join(os.path.dirname(KEYS_PATH), "_panel_review.json")
    json.dump(result, open(outp,"w"), indent=2)
    for label,r in result.items():
        if "error" in r: print(f"\n### {label}: ERROR {r['error']}"); continue
        if "raw" in r: print(f"\n### {label}: (unparsed) {r['raw'][:200]}"); continue
        print(f"\n### {label} -- verdict: {r.get('verdict','?')}")
        for f in r.get("findings",[]):
            print(f"  [{f.get('severity','?')}] {f.get('target','?')}: {f.get('issue','?')}")
