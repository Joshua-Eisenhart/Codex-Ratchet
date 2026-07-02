#!/usr/bin/env python3
import os, json, urllib.request, urllib.error

API_KEY = os.environ["OPENROUTER_API_KEY"]
URL = "https://openrouter.ai/api/v1/chat/completions"

MODELS = [
    "x-ai/grok-4.3",
    "google/gemini-3.1-pro-preview",
    "deepseek/deepseek-v3.2",
    "qwen/qwen3.7-max",
    "moonshotai/kimi-k2.6",
    "z-ai/glm-4.6",
    "mistralai/mistral-large",
    "minimax/minimax-m3",
]

FRAME = """The system is a NOMINALIST CONSTRAINT-ADMISSIBILITY engine. Root primitive = a constraint on distinguishability: a=a iff a~b (identity is probe-relative, never primitive). Exclusion-first: constraints KILL inadmissible distinctions/structures; they do NOT generate. F01 finitude (finite supports/probes; no completed infinities). N01 noncommutation (order matters). Three root expressions never collapsed: quotient S/~_M (elements), noncommutation (order), nonassociativity (grouping).
"PURGATORY" (better name than the old "graveyard") IS THE WORKING SPACE — not a holding pen you send rejects to. ALL work happens INSIDE it. Two THIN EDGES that rarely fire: HELL = proven impossible (z3/SMT UNSAT — the ONLY true finality); HEAVEN = earned-by-process canon (small, and itself provisional — a passing candidate is still a candidate). Everything else — nearly the whole system — is purgatory: provisional finite structures / sims, held PLURAL (MSS keeps Min(Surv(C)) plural, anti-collapse), re-testable, POSITIONED by their constraint-relations (which probes they survive; at what DEPTH they obstruct / fail to globalize). The whole model + every sim ever run is sent into purgatory FIRST as provisional evidence; a sim earns a SEAT only if it actually ran (engine-authentic, hash-pinned) — seat-certification is "did it really run", NOT "is it true". The MANIFOLD = the shape of how these provisional objects relate (an obstruction/refinement structure), NOT a separately-certified object. MSS = admit the weakest structure that survives the active constraints AND still evolves; stronger structure (rho/Hilbert/geometry/measure) is INSTALLED not forced unless a lower closure FORCES it."""

QUESTION = """How is a resident POSITIONED in purgatory: how do you compute the DEPTH at which a candidate structure obstructs (fails to globalize/survive)? Is "the manifold = the shape of the worked purgatory" literally an obstruction complex / nerve of a cover / refinement poset / a filtration? Give ONE concrete finite construction: given a finite candidate structure + a finite probe/constraint family, output its obstruction-depth and its position relative to other residents."""

def call(slug):
    body = {
        "model": slug,
        "messages": [
            {"role": "system", "content": FRAME},
            {"role": "user", "content": QUESTION},
        ],
        "max_tokens": 2000,
    }
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(URL, data=data, method="POST")
    req.add_header("Authorization", "Bearer " + API_KEY)
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=150) as resp:
        text = resp.read().decode("utf-8", errors="replace")
    parsed = json.loads(text, strict=False)
    choices = parsed.get("choices")
    if not choices:
        raise RuntimeError("no choices; raw=" + text[:500])
    msg = choices[0].get("message", {}) or {}
    content = msg.get("content")
    if not content:
        content = msg.get("reasoning")
    if not content:
        raise RuntimeError("empty content/reasoning; raw=" + text[:500])
    return content

results = {}
for slug in MODELS:
    print("=" * 100)
    print("MODEL:", slug)
    print("=" * 100)
    try:
        ans = call(slug)
        results[slug] = {"ok": True, "answer": ans}
        print(ans)
    except urllib.error.HTTPError as e:
        err_body = ""
        try:
            err_body = e.read().decode("utf-8", errors="replace")[:500]
        except Exception:
            pass
        msg = "HTTPError {}: {}".format(e.code, err_body)
        results[slug] = {"ok": False, "error": msg}
        print("ERROR:", msg)
    except Exception as e:
        msg = "{}: {}".format(type(e).__name__, e)
        results[slug] = {"ok": False, "error": msg}
        print("ERROR:", msg)
    print()

with open("/Users/joshuaeisenhart/Desktop/Codex Ratchet/q2_position_results.json", "w") as f:
    json.dump(results, f, indent=2)

ok = [m for m in MODELS if results.get(m, {}).get("ok")]
err = [m for m in MODELS if not results.get(m, {}).get("ok")]
print("=" * 100)
print("SUCCEEDED:", ok)
print("ERRORED:", err)
