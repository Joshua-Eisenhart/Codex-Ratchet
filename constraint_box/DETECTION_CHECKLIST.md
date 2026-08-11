# CB Light Detection Checklist — Current vs. Required

**Scope**: Specific, measurable detection mechanisms for each attack vector. Indicates what CB Light currently does (✅), what is partially implemented (⚠️), and what is missing (❌).

---

## 1. INTERPRETER EXECUTION

| Attack vector | Current detection | Required detection | Status | Risk |
|---|---|---|---|---|
| Bare `pip` instead of mandated interpreter | ✅ `_mutation_shape()` detects `bare-pip` tool; `MANDATED_INTERPRETER_REQUIRED` REFUSE | Tool name matching | ✅ | Low |
| Python -m pip with wrong interpreter | ✅ `_same_executable()` compares resolved paths | Path canonicalization + comparison | ✅ | Low |
| `uv pip` without `--python` flag | ✅ Extracts `--python` values; expects exactly 1 matching interpreter | Argument inspection | ✅ | Low |
| Shell function wrapping interpreter | ⚠️ Depends on whether hook runs in shell that sources user config | Clean hook environment without user config sourcing | ❌ | High |
| `PYTHONPATH` shadowing constraint_box module | ❌ No check; hook's Python process inherits PYTHONPATH from shell | Isolated hook environment or module integrity check | ❌ | **CRITICAL** |
| Symlink aliasing to wrong Python | ✅ `Path.resolve()` dereferences symlinks | Path resolution | ✅ | Low |
| `/usr/bin/python3` masquerading (wrong path) | ✅ Resolves and compares against mandated | Path resolution + comparison | ✅ | Low |

---

## 2. PACKAGE SOURCES

| Attack vector | Current detection | Required detection | Status | Risk |
|---|---|---|---|---|
| `-r requirements.txt` (unbounded file) | ✅ Flag matching on `-r`, `--requirement` | Argument inspection | ✅ | Low |
| `-c constraints.txt` (constraint file) | ✅ Flag matching on `-c`, `--constraint` | Argument inspection | ✅ | Low |
| `--index-url` redirection | ✅ Flag matching on `--index-url` | Argument inspection | ✅ | Low |
| `--extra-index-url` redirection | ✅ Flag matching | Argument inspection | ✅ | Low |
| `--find-links` local source | ✅ Flag matching | Argument inspection | ✅ | Low |
| `PIP_INDEX_URL` environment variable | ❌ No inspection of env vars or pip config | Read `pip.conf`, `setup.cfg`, `pyproject.toml [tool.pip]`, check env vars | ❌ | **High** |
| `~/.pip/pip.conf` index-url config | ❌ Not inspected by pre-hook | Read and validate pip config files | ❌ | **High** |
| `PYPI_*` environment variables | ❌ Not inspected | Check environment variables before pip invocation | ❌ | High |
| Direct git+https:// URLs | ✅ Pattern matching for `git+`, `hg+`, `svn+`, `bzr+` | Argument inspection | ✅ | Low |
| Local editable installs (allowed on CB only) | ✅ Whitelist CB repo path; reject others | Path whitelisting | ✅ | Low |
| HTTP/HTTPS direct URLs | ✅ Pattern matching for `://` | Argument inspection | ✅ | Low |

---

## 3. INSTALL DESTINATIONS

| Attack vector | Current detection | Required detection | Status | Risk |
|---|---|---|---|---|
| `--target /tmp/install` | ✅ Flag matching | Argument inspection | ✅ | Low |
| `--prefix /custom/path` | ✅ Flag matching | Argument inspection | ✅ | Low |
| `--root /alternate` | ✅ Flag matching | Argument inspection | ✅ | Low |
| `--user` (site-packages) | ✅ Flag matching | Argument inspection | ✅ | Low |
| `~/.pydistutils.cfg` prefix config | ❌ Not inspected | Read distutils config files | ❌ | Moderate |
| `~/.pydistutils.cfg` [install] config | ❌ Not inspected | Read distutils config files | ❌ | Moderate |

---

## 4. TOOL WRAPPING AND INDIRECTION

| Attack vector | Current detection | Required detection | Status | Risk |
|---|---|---|---|---|
| `command pip install ...` | ✅ `command` in `_MUTATION_WRAPPERS`; recursive check | Wrapper detection | ✅ | Low |
| `sudo pip install ...` | ✅ `sudo` detected; nested mutation check | Wrapper detection | ✅ | Low |
| `env VAR=val pip install ...` | ✅ `_strip_environment_prefix()` removes env vars; checks underlying command | Environment prefix stripping | ✅ | Low |
| `nice -n 0 pip install ...` | ✅ `nice` detected | Wrapper detection | ✅ | Low |
| `timeout 30 pip install ...` | ✅ `timeout` detected | Wrapper detection | ✅ | Low |
| `xargs pip install` | ✅ `xargs` detected | Wrapper detection | ✅ | Low |
| Depth > 3 nesting | ✅ `depth > 3` returns early with DEPTH_EXCEEDED | Recursion limit | ✅ | Low |
| `eval "pip install ..."` | ❌ `eval` is not in `_MUTATION_WRAPPERS` | Add shell builtins to wrapper detection | ❌ | Moderate |
| `exec pip install` | ❌ `exec` not detected | Add to wrapper detection | ❌ | Low |
| `source script.sh` (pip inside script) | ⚠️ Hook sees `source script.sh`; no mutation signature detected | Script inspection or sub-hook invocation for sourced files | ❌ | Low (mitigated if each subprocess pip is independently hooked) |
| Subshell `(pip install ...)` | ❌ `(` and `)` are not in `_CONTROL_TOKENS` | Add parens to control token detection | ❌ | **Moderate** |

---

## 5. SHELL EXPANSION AND QUOTING

| Attack vector | Current detection | Required detection | Status | Risk |
|---|---|---|---|---|
| Shell variable in argument: `pip install $PKG` | ✅ `shlex.split()` treats `$PKG` as literal token (not expanded) | No action needed; hook correctly sees literal | ✅ | Low |
| Command substitution: `pip install $(echo pkg)` | ✅ `shlex.split()` treats `$(...)` as literal | No action needed; hook correctly sees literal | ✅ | Low |
| Backtick substitution: `pip install \`which pkg\`` | ✅ Treated as literal by shlex | No action needed | ✅ | Low |
| Alias redirection (if sourcedbefore hook) | ⚠️ Depends on hook invocation context | Clean hook environment; run without sourcing user config | ❌ | **High** |
| Shell function (if sourced before hook) | ⚠️ Depends on hook invocation context | Clean hook environment | ❌ | **High** |
| PATH manipulation (user adds ~/bin/pip) | ⚠️ If hook resolves `pip` via PATH, may find attacker's version | Hook should use absolute path or check PATH only in mandated env | ⚠️ | **High** |
| `~/.bashrc` alias export | ⚠️ Depends on hook invocation | Clean hook environment without bashrc | ❌ | **High** |

---

## 6. COMPOUND COMMANDS AND CONTROL FLOW

| Attack vector | Current detection | Required detection | Status | Risk |
|---|---|---|---|---|
| `pip install pkg1 && pip install pkg2` | ✅ `&&` in `_CONTROL_TOKENS`; REFUSE `COMPOUND_MUTATION_COMMAND` | Control token detection | ✅ | Low |
| `pip install pkg1 ; pip install pkg2` | ✅ `;` detected | Control token detection | ✅ | Low |
| `pip install pkg1 \|\| pip install pkg2` | ✅ `\|` detected | Control token detection | ✅ | Low |
| `pip install pkg1 \| pip install pkg2` | ✅ `\|` detected | Control token detection | ✅ | Low |
| `pip install pkg1 &` (background) | ✅ `&` detected | Control token detection | ✅ | Low |
| Subshell with parens: `(pip install pkg)` | ❌ `(` and `)` not in `_CONTROL_TOKENS` | Add parens to control token detection | ❌ | **Moderate** |
| Logical operators: `[[ $x == y ]] && pip install` | ⚠️ `&&` is detected, but as a compound mutation (not the real issue) | Control flow detection is correct | ✅ | Low |

---

## 7. PACKAGE SPECIFICATION

| Attack vector | Current detection | Required detection | Status | Risk |
|---|---|---|---|---|
| Package outside CB domain | ✅ `domain_names` set check; REFUSE `PACKAGE_OUTSIDE_CB_LIGHT_PROPOSAL_DOMAIN` | Domain membership check | ✅ | Low |
| Package in domain but not core_contract | ✅ `unselected` set check; HOLD `CANDIDATE_NOT_SELECTED_FOR_INSTALL` | Core contract selection check | ✅ | Low |
| Package not in direct pyproject.toml | ✅ Checks `direct` set | Declaration check | ✅ | Low |
| Version mismatch (requested != declared) | ✅ `_canonical_requirement()` normalization + comparison; HOLD `DECLARED_VERSION_CONSTRAINT_REQUIRED` | Spec canonicalization + comparison | ✅ | Low |
| Conflicting specs (same package twice, different versions) | ✅ `_requested()` checks for conflicts | Conflict detection | ✅ | Low |
| Mixed package + project install | ✅ Checks for both `names` and `projects` non-empty | Mixed install detection | ✅ | Low |
| Project install with mismatched direct set | ✅ Checks if `direct != core_contract`; REFUSE `PROJECT_DEPENDENCY_SET_NOT_CURRENT_CORE` | Direct set validation | ✅ | Low |
| Editable install of non-CB project | ✅ `_project_is_constraint_box()` whitelist | Path whitelist | ✅ | Low |
| Package spec parsing failure | ✅ Exception handling; REFUSE `PACKAGE_SPEC_PARSE_FAILED` | Error handling | ✅ | Low |

---

## 8. BUILD ENVIRONMENT AND SETUP.PY

| Attack vector | Current detection | Required detection | Status | Risk |
|---|---|---|---|---|
| `--config-settings` with arbitrary args | ✅ Flag matching; REFUSE `UNBOUNDED_BUILD_CONFIGURATION` | Flag detection | ✅ | Low |
| `setup.py` code injection during install | ❌ No inspection; setup.py runs after hook validation | Sandbox setup.py execution in restricted environment OR verify package bytes | ❌ | **Moderate** |
| PEP 517 build backend injection | ❌ No inspection of `pyproject.toml [build-system]` | Verify build backend is whitelisted | ❌ | **Moderate** |
| Preinstall hooks in setup.py | ❌ Not inspected | Sandbox execution | ❌ | Moderate |

---

## 9. DOMAIN AND STATE FRESHNESS

| Attack vector | Current detection | Required detection | Status | Risk |
|---|---|---|---|---|
| Domain staleness at pre-install time | ⚠️ No explicit check; depends on session state | Add domain freshness check (timestamp or hash) | ❌ | Low |
| pyproject.toml modified between pre-install and pip run | ❌ No lock or atomicity | Transactional lock or re-validation at pip invocation | ❌ | Low |
| Domain state is stale after post-install | ✅ Post-install gate re-probes; detects stale state | Re-probing | ✅ | Low |
| Candidate registry out-of-sync with actual domain | ⚠️ Registry is read fresh each session | No protection against registry staleness | ⚠️ | Low |

---

## 10. INTEGRITY AND SIGNATURES

| Attack vector | Current detection | Required detection | Status | Risk |
|---|---|---|---|---|
| Manifest tampering (file hash mismatch) | ✅ SHA256 comparison in `_verify_manifest()` | Hash verification | ✅ | Low |
| Manifest and files replaced together | ⚠️ Detected on next session if manifest is committed to git | External integrity check (e.g., GitHub required check) | ⚠️ | **Moderate** |
| Registry.json tampering | ❌ No integrity check; can be modified at runtime | Sign registry or externally verify | ❌ | **Moderate** |
| CB Light source modified after install | ⚠️ Manifest check on next hook invocation | External integrity check | ⚠️ | **Moderate** |
| Installed package integrity | ❌ No verification of installed package bytes | Verify package hashes or signatures post-install | ❌ | **High** |
| Hook script tampering (`cb_pretooluse_guard.sh`, etc.) | ❌ No integrity check on hook scripts themselves | Verify hook script hashes | ❌ | **High** |

---

## 11. ENVIRONMENT ISOLATION

| Attack vector | Current detection | Required detection | Status | Risk |
|---|---|---|---|---|
| `PYTHONPATH` override | ❌ No isolation; hook inherits PYTHONPATH | Run hook in clean environment | ❌ | **CRITICAL** |
| `LD_LIBRARY_PATH` manipulation | ❌ No isolation | Run hook in clean environment | ❌ | **High** |
| `PATH` manipulation | ⚠️ Mandated interpreter is absolute path; but sub-dependencies may be affected | Specify all interpreter paths absolutely | ⚠️ | Moderate |
| User shell config sourcing | ⚠️ Depends on hook invocation | Do not source user config in hook invocation | ❌ | **High** |
| Home directory override (`$HOME`) | ❌ Not checked | Validate `$HOME` before running hook | ❌ | Moderate |

---

## 12. LOGGING AND AUDIT

| Attack vector | Current detection | Required detection | Status | Risk |
|---|---|---|---|---|
| Hook execution audit trail | ✅ SQLite `hook_event` table logs all invocations | Event logging | ✅ | Low |
| Payload inspection logging | ✅ Payload SHA256 and details logged | Payload logging | ✅ | Low |
| Domain state snapshot | ✅ Snapshot ID + domain SHA256 logged | State hashing | ✅ | Low |
| Probe result audit | ✅ Probe run ID + evidence stored | Result logging | ✅ | Low |
| Missing: Hook invocation source (tty, subprocess, cron) | ❌ Not logged | Log hook invocation context | ❌ | Low |
| Missing: Environment snapshot at hook invocation | ❌ Not captured | Log relevant env vars (`PYTHONPATH`, `PATH`, `PIP_INDEX_URL`, etc.) | ❌ | Low |

---

## Summary: Detection Coverage by Category

| Category | Implemented | Partial | Missing | Critical Gap |
|---|---|---|---|---|
| Interpreter execution | 7/7 | 0/7 | 0/7 | None |
| Package sources | 7/8 | 0/8 | 1/8 | Pip config + env vars |
| Install destinations | 4/4 | 0/4 | 0/4 | None |
| Tool wrapping | 5/6 | 1/6 | 2/6 | eval/exec, subshell parens |
| Shell expansion | 3/4 | 1/4 | 1/4 | Aliases/functions (if sourced) |
| Compound commands | 5/5 | 0/5 | 1/5 | Subshell parens |
| Package specs | 7/7 | 0/7 | 0/7 | None |
| Build environment | 1/3 | 0/3 | 2/3 | setup.py/PEP517 |
| Domain freshness | 1/3 | 1/3 | 1/3 | Pre-install staleness |
| Integrity | 1/6 | 2/6 | 3/6 | Package/registry/hook signatures |
| Environment isolation | 1/7 | 1/7 | 5/7 | **PYTHONPATH, shell config** |
| Logging | 4/5 | 0/5 | 1/5 | Invocation context |

---

## Mandatory Fixes (Tier 0 — Fail-Closed)

These should be implemented before CB Light is considered production-safe:

1. **PYTHONPATH Isolation** (CRITICAL)
   - Run hook in subprocess with cleaned `PYTHONPATH`
   - Or: Inline constraint_box code instead of importing (eliminates import path vulnerability)

2. **Shell Config Isolation** (HIGH)
   - Do not source user `.bashrc` / `.zshrc` in hook invocation
   - Run hook in clean shell context

3. **Pip Config Inspection** (HIGH)
   - Read `~/.pip/pip.conf`, `setup.cfg`, `pyproject.toml` [tool.pip] before hook returns ADMIT
   - Check for `index-url`, `find-links`, `trusted-host` settings
   - Fail if any non-mandated sources are configured

4. **Subshell Paren Detection** (MODERATE)
   - Add `(` and `)` to `_CONTROL_TOKENS`
   - Or: Enhance `_has_package_mutation_signature()` to detect pip inside parens

5. **Package Integrity Verification** (MODERATE)
   - Post-install: Compare installed package files against known-good hash/signature
   - Or: Add contract that verifies package signature (if available from PyPI)

---

## Recommended Enhancements (Tier 1 — Improve Coverage)

1. **Hook Invocation Audit**
   - Log whether hook is running in tty, subprocess, or non-interactive context
   - Flag anomalous invocation contexts

2. **Environment Variable Snapshot**
   - Log `PYTHONPATH`, `PATH`, `PIP_INDEX_URL`, `PYPI_*` at hook invocation
   - Compare against expected baseline

3. **Setup.py Sandboxing**
   - Run `pip install` in a subprocess with restricted filesystem access
   - Audit what setup.py writes/reads

4. **Registry Signing**
   - Sign `registry.json` and `manifest.json` with a key held outside the repo
   - Verify signatures on every hook invocation

5. **Hook Script Integrity**
   - Add SHA256 hashes of `.claude/hooks/*.sh` to manifest
   - Detect modifications to hook scripts

---

