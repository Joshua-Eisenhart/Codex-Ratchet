#!/usr/bin/env node
/**
 * ArchFence v0.1 — architectural invariants as exit codes, not spec prose.
 *
 *   archfence <rules.json> --estate <dir>
 *       exit 0 = clean, 1 = violations, 2 = error
 *
 * Rule types (rules.json = {"rules": [...]}):
 *
 *  { "id": "no-poly-handlers", "type": "forbidden_path",
 *    "path_regex": "core/poly/src/handlers/",
 *    "why": "poly is binder/surfaces only; handlers live in owning modules" }
 *
 *  { "id": "no-commands-dirs", "type": "forbidden_path",
 *    "path_regex": "/commands/",
 *    "why": "use src/handlers/ — 'commands' makes agents write CLI-specific code" }
 *
 *  { "id": "handlers-live-in-handlers", "type": "required_location",
 *    "file_regex": "\\.handler\\.(ts|js)$",
 *    "dir_regex": "src/handlers/",
 *    "why": "handler files only under src/handlers/" }
 *
 *  { "id": "plugins-no-core-internals", "type": "import_boundary",
 *    "source_regex": "plugins/",
 *    "forbidden_import_regex": "core/[^/]+/src/",
 *    "allowed_import_regex": "core/[^/]+/contracts?",
 *    "why": "plugins couple through declared contracts, never core internals" }
 *
 * Anti-theater: a rule that matched ZERO files/imports in the whole scan is
 * reported as a STALE-RULE warning — a fence that never touches anything may
 * be guarding a path that no longer exists (silent false security).
 *
 * No dependencies. Node >= 18.
 */

import fs from "node:fs";
import path from "node:path";

function die(msg, code = 2) {
  process.stderr.write(`archfence: ${msg}\n`);
  process.exit(code);
}

const CODE_EXT = new Set([".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".py", ".go", ".rs", ".jl"]);
const SKIP_DIRS = new Set(["node_modules", ".git", "__pycache__", "dist", "build", ".venv", "coverage"]);

function* walkFiles(dir) {
  const stack = [dir];
  while (stack.length) {
    const d = stack.pop();
    let entries;
    try { entries = fs.readdirSync(d, { withFileTypes: true }); } catch { continue; }
    for (const e of entries) {
      const p = path.join(d, e.name);
      if (e.isDirectory()) {
        if (!SKIP_DIRS.has(e.name) && !e.name.startsWith(".")) stack.push(p);
      } else if (e.isFile()) {
        yield p;
      }
    }
  }
}

// import specifiers: ES import/export-from, require(), python "from X import"/"import X"
const IMPORT_PATTERNS = [
  /(?:^|\n)\s*import\s+[^;'"]*?from\s+['"]([^'"]+)['"]/g,
  /(?:^|\n)\s*import\s+['"]([^'"]+)['"]/g,
  /(?:^|\n)\s*export\s+[^;'"]*?from\s+['"]([^'"]+)['"]/g,
  /require\(\s*['"]([^'"]+)['"]\s*\)/g,
  /(?:^|\n)\s*from\s+([\w.][\w.\/]*)\s+import\s+/g,
  /(?:^|\n)\s*import\s+([\w.][\w.\/]*)\s*$/gm,
];

function extractImports(src) {
  const out = [];
  for (const re of IMPORT_PATTERNS) {
    re.lastIndex = 0;
    let m;
    while ((m = re.exec(src)) !== null) {
      // line number = count of \n before match start; patterns anchored with
      // (?:^|\n) include the preceding newline in the match — correct for it
      const start = m.index + (m[0].startsWith("\n") ? 1 : 0);
      const line = src.slice(0, start).split("\n").length;
      out.push({ spec: m[1], line });
    }
  }
  return out;
}

function main() {
  const args = process.argv.slice(2);
  const rulesPath = args.find((a) => !a.startsWith("--"));
  const i = args.indexOf("--estate");
  const estate = i >= 0 ? args[i + 1] : null;
  if (!rulesPath || !estate) die("usage: archfence <rules.json> --estate <dir>");
  let cfg;
  try { cfg = JSON.parse(fs.readFileSync(rulesPath, "utf8")); } catch (e) { die(`bad rules file: ${e.message}`); }
  const rules = cfg.rules || [];
  if (!rules.length) die("rules file has no rules — an empty fence is not a fence", 2);

  // validate + compile rules up front (a broken regex must be a hard error, not a silent skip)
  for (const r of rules) {
    try {
      for (const k of ["path_regex", "file_regex", "dir_regex", "source_regex", "forbidden_import_regex", "allowed_import_regex"]) {
        if (r[k] !== undefined) r[`_${k}`] = new RegExp(r[k]);
      }
    } catch (e) {
      die(`rule '${r.id}': invalid regex — ${e.message}`);
    }
    if (!r.id || !r.type) die(`every rule needs id and type: ${JSON.stringify(r).slice(0, 80)}`);
  }

  const violations = [];
  const touched = new Map(rules.map((r) => [r.id, 0])); // anti-theater counters

  for (const file of walkFiles(estate)) {
    const rel = path.relative(estate, file).split(path.sep).join("/");
    const isCode = CODE_EXT.has(path.extname(file));

    for (const r of rules) {
      if (r.type === "forbidden_path") {
        if (r._path_regex.test(rel)) {
          touched.set(r.id, touched.get(r.id) + 1);
          violations.push({ rule: r.id, file: rel, detail: `path matches forbidden pattern '${r.path_regex}'${r.why ? " — " + r.why : ""}` });
        }
      } else if (r.type === "required_location") {
        if (r._file_regex.test(rel)) {
          touched.set(r.id, touched.get(r.id) + 1);
          if (!r._dir_regex.test(rel)) {
            violations.push({ rule: r.id, file: rel, detail: `file matches '${r.file_regex}' but is not under '${r.dir_regex}'${r.why ? " — " + r.why : ""}` });
          }
        }
      }
    }

    // import boundaries need file content — read code files once, lazily
    const importRules = rules.filter((r) => r.type === "import_boundary" && r._source_regex.test(rel));
    if (isCode && importRules.length) {
      let src = "";
      try { src = fs.readFileSync(file, "utf8"); } catch { continue; }
      const imports = extractImports(src);
      for (const r of importRules) {
        for (const im of imports) {
          if (!r._forbidden_import_regex.test(im.spec)) continue;
          touched.set(r.id, touched.get(r.id) + 1);
          if (r._allowed_import_regex && r._allowed_import_regex.test(im.spec)) continue;
          violations.push({ rule: r.id, file: `${rel}:${im.line}`, detail: `imports '${im.spec}' — forbidden by '${r.forbidden_import_regex}'${r.why ? " — " + r.why : ""}` });
        }
      }
    }
  }

  const stale = rules.filter((r) => touched.get(r.id) === 0).map((r) => ({
    rule: r.id,
    warning: `matched nothing in the entire scan — the fence may guard a path that no longer exists (verify the rule is still live, then keep or retire it)`,
  }));

  const report = {
    tool: "archfence",
    estate,
    rules_evaluated: rules.length,
    verdict: violations.length ? "VIOLATIONS" : "CLEAN",
    violations,
    stale_rule_warnings: stale,
  };
  process.stdout.write(JSON.stringify(report, null, 1) + "\n");
  process.exit(violations.length ? 1 : 0);
}

main();
