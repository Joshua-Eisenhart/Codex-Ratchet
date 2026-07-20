#!/usr/bin/env node
/**
 * FailureCard v0.1 — the mesh payload: failures as a first-class, shareable asset.
 *
 *   failurecard extract <failures.jsonl> [--anonymous] [--out archive.json]
 *       Turn curated failure records into a queryable archive.
 *       --anonymous scrubs source paths + a project-noun list so the archive
 *       is safe to gossip to another node. exit 0 ok, 2 error.
 *
 *   failurecard tried <archive.json> "<proposed approach>" [--k 3] [--min 0.12]
 *       "Have we tried this already?" — the most valuable eval, run at task-DESIGN
 *       time. Returns the nearest past failures to a proposed approach, so a
 *       plan gets caught against history before it burns a run.
 *       exit 0 = no strong match (novel), 3 = prior failure(s) found, 2 = error.
 *
 * Why this shape: the dev's insight — "the history of failures is ur most
 * valuable eval." A failure is only an asset if (a) it is a structured card,
 * not a prose log, (b) it is anonymized so nodes can share, (c) it is queryable
 * by approach at plan time. This file does exactly those three, nothing else.
 * The mesh transport (gossip between nodes) is not here — this produces the
 * payload the mesh carries.
 *
 * Card schema (one JSON object per line in failures.jsonl):
 *   id, class, trigger, signature[], approach, caught_by, outcome, source
 * Only `source` is scrubbed by --anonymous; the failure mode itself is already
 * domain-neutral (that is what makes it shareable).
 *
 * No dependencies. Node >= 18.
 */

import fs from "node:fs";
import path from "node:path";

function die(msg, code = 2) { process.stderr.write(`failurecard: ${msg}\n`); process.exit(code); }

// project-specific nouns scrubbed in --anonymous mode (extend per estate)
const SCRUB = [
  "codex-ratchet", "codex ratchet", "ratchet", "manifold", "axis-0", "axis0",
  "weyl", "hopf", "octonion", "spinor", "lev", "leviathan", "jepa", "holodeck",
];
const STOP = new Set(["the","a","an","of","for","and","or","to","in","on","with","is","are","it","that","this","by","as","at","be","from","its","own","not"]);

function tokens(s) {
  return new Set(String(s).replace(/([a-z0-9])([A-Z])/g, "$1 $2").toLowerCase()
    .split(/[^a-z0-9]+/).filter((t) => t.length > 2 && !STOP.has(t)));
}
function tokMatch(t, u) {
  if (t === u) return true;
  const [s, l] = t.length <= u.length ? [t, u] : [u, t];
  if (s.length >= 3 && (l === s + "s" || l === s + "es")) return true;
  return s.length >= 4 && l.startsWith(s);
}
function jaccard(a, b) {
  if (!a.size || !b.size) return 0;
  let inter = 0;
  for (const t of a) if ([...b].some((u) => tokMatch(t, u))) inter++;
  return inter / (a.size + b.size - inter);
}

function scrub(text) {
  if (typeof text !== "string") return text;
  let out = text;
  // strip absolute/relative paths to basenames
  out = out.replace(/(?:\/[\w.\-]+)+\/([\w.\-]+)/g, "[path]/$1");
  out = out.replace(/\bcommit\s+[0-9a-f]{6,}/gi, "commit [hash]");
  for (const w of SCRUB) out = out.replace(new RegExp(`\\b${w}\\b`, "gi"), "[domain]");
  return out;
}

function loadCards(jsonlPath) {
  const lines = fs.readFileSync(jsonlPath, "utf8").split("\n").filter((l) => l.trim());
  const cards = [];
  lines.forEach((l, i) => {
    let c;
    try { c = JSON.parse(l); } catch (e) { die(`line ${i + 1}: ${e.message}`); }
    if (!c.id || !c.trigger) die(`line ${i + 1}: card needs at least id and trigger`);
    cards.push(c);
  });
  return cards;
}

// the searchable surface of a card = the words a future plan would echo
function cardTokens(c) {
  return tokens([c.trigger, c.approach, (c.signature || []).join(" "), c.class].join(" "));
}

function extract(jsonlPath, anonymous, outPath) {
  const cards = loadCards(jsonlPath).map((c) => {
    const card = { ...c };
    if (anonymous) {
      delete card.source;
      card.trigger = scrub(card.trigger);
      card.approach = scrub(card.approach);
      card.outcome = scrub(card.outcome);
      card.signature = (card.signature || []).map(scrub);
      card.caught_by = scrub(card.caught_by);
    }
    return card;
  });
  const archive = {
    schema: "failurecard.archive.v1",
    anonymous: !!anonymous,
    count: cards.length,
    classes: [...new Set(cards.map((c) => c.class).filter(Boolean))].sort(),
    cards,
  };
  const out = JSON.stringify(archive, null, 1);
  if (outPath) { fs.writeFileSync(outPath, out + "\n"); process.stdout.write(`wrote ${cards.length} cards -> ${outPath}${anonymous ? " (anonymized)" : ""}\n`); }
  else process.stdout.write(out + "\n");
  process.exit(0);
}

function tried(archivePath, approach, k, min) {
  let archive;
  try { archive = JSON.parse(fs.readFileSync(archivePath, "utf8")); } catch (e) { die(`bad archive: ${e.message}`); }
  const cards = archive.cards || [];
  if (!approach || !approach.trim()) die("provide a proposed approach to check against history");
  const q = tokens(approach);
  const scored = cards.map((c) => ({ card: c, score: jaccard(q, cardTokens(c)) }))
    .filter((s) => s.score >= min)
    .sort((a, b) => b.score - a.score)
    .slice(0, k);
  const report = {
    tool: "failurecard.tried",
    proposed: approach,
    verdict: scored.length ? "PRIOR_FAILURES_FOUND" : "NO_STRONG_MATCH",
    matches: scored.map((s) => ({
      id: s.card.id, class: s.card.class, similarity: +s.score.toFixed(3),
      trigger: s.card.trigger, outcome: s.card.outcome, caught_by: s.card.caught_by,
    })),
  };
  process.stdout.write(JSON.stringify(report, null, 1) + "\n");
  process.exit(scored.length ? 3 : 0);
}

const [, , cmd, ...args] = process.argv;
const flag = (n, d) => { const i = args.indexOf(`--${n}`); return i >= 0 ? args[i + 1] : d; };

if (cmd === "extract") {
  const src = args.find((a) => !a.startsWith("--"));
  if (!src) die("usage: failurecard extract <failures.jsonl> [--anonymous] [--out archive.json]");
  extract(src, args.includes("--anonymous"), flag("out"));
} else if (cmd === "tried") {
  const nonFlags = args.filter((a, i) => !a.startsWith("--") && (i === 0 || !args[i - 1].startsWith("--") || ["--k", "--min", "--out"].indexOf(args[i - 1]) < 0));
  const archivePath = nonFlags[0];
  const approach = nonFlags.slice(1).join(" ");
  if (!archivePath || !approach) die('usage: failurecard tried <archive.json> "<proposed approach>" [--k 3] [--min 0.12]');
  tried(archivePath, approach, Number(flag("k", "3")), Number(flag("min", "0.12")));
} else {
  die(`unknown command '${cmd ?? ""}' — commands: extract, tried`, 2);
}
