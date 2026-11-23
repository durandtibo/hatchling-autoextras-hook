# `hatchling_autoextras_hook`: target state and the changes to reach it

This document describes the design that `hatchling_autoextras_hook` should have, then the changes to
make to the current implementation (`main`, `6a04c5d`) to get there. The design follows the rules of
`CLAUDE.md` (strict validation, `msg` variable, keyword-style options, docstrings, one behaviour per
test, every patched behaviour has an integration test) and the documented behaviour in `README.md`.
Its aim is a package that stays tiny and is easy to maintain: **one hook class, three options, one
normalization rule, no silent fallback**. Breaking changes are accepted and the future state is more
important than the past one.

Evidence comes from probes run on `main` with hatchling 1.33.0 and the code of hatchling's
`metadata/core.py` (scripts kept outside the repository). Items marked **[verified]** were
reproduced; **[reading]** comes from the code. Nothing in `src`, `tests` or `docs` was changed.

## Constraints

1. **Simple and easy to maintain.** The package is one 185-line module. The target does not add
   code next to the existing one: it replaces the ad-hoc checks by one normalization helper and one
   option table, and it deletes the tolerant paths (silently ignored entries and options).
2. **Do not redo hatchling's work.** Hatchling already validates every requirement, normalizes
   extra names (PEP 685) and requirement names, deduplicates canonical requirements, sorts them and
   resolves self-references (`my-package[dev]`) after the hooks ran (`core.py`
   `optional_dependencies_complex`, **[reading]**). The hook must produce the right _union of
   strings_ and fail early with a message that names the _source_ extra; it must not parse
   requirements.
3. **Minimal footprint.** The only runtime dependency stays `hatchling>=1.18,<2.0`. No `packaging`
   import (it is a dependency of hatchling, not of this package), no new dependency.
4. **Major release.** Compatibility is not a design input: no alias, no deprecation period. The
   release notes list the changes (section 4). Python >= 3.11, hatchling >= 1.18, < 2.0 are kept.
5. **Fail early, name the culprit.** A build that succeeds with a wrong `all` extra is worse than a
   build that fails. Every error says which option or which extra is wrong.
6. **Loud by default, lenient on request.** Every problem raises. Only the problems for which the
   hook has an unambiguous way to continue (section 3.4) can be downgraded to a `UserWarning` by
   an environment variable, set by the person who runs the build, not by the project.

## 1. Properties of the sub-package

These are the rules the hook guarantees. Every design choice below exists to make one of them true
**by construction** instead of by the discipline of each code path. They must be written in the
package docstring and in the **Properties** section of the README.

| Property                | Statement                                                                                                                                                                                       | Enforced by                           |
| ----------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------- |
| Union of the extras     | The generated extra contains every dependency of every non-excluded extra, and nothing else. The generated extra never contains its own previous content.                                       | `update`                              |
| Deterministic           | The output is the sorted list of the distinct dependency strings. The same input always gives the same output, whatever the order of the extras.                                                 | `sorted(set(...))`                    |
| Additive                | Original extras are never modified, reordered or removed. Only the generated extra is added (or replaced when `overwrite = true`).                                                              | `update`                              |
| Atomic                  | `update` either completes or raises with `metadata` unchanged. The metadata is mutated in one last step.                                                                                        | validate first, mutate last           |
| Name-normalized         | Extra names are compared after PEP 685 normalization (`Dev_Extra`, `dev-extra` and `dev.extra` are the same extra), for `group-name`, `exclude` and the collision check, like hatchling does.  | `_normalize`                          |
| Strict                  | By default, an unknown option, a wrong type, an invalid name, a non-string or blank dependency, and an `exclude` entry that matches no extra all raise. Nothing is ignored silently.             | `_validate_config`, `update`          |
| Lenient on request      | With `HATCHLING_AUTOEXTRAS_WARN_ONLY=1`, the two _recoverable_ problems (unknown option, unmatched `exclude` entry) emit a `UserWarning` and the build continues. Every other problem still raises. | `_report`                             |
| Early and named errors  | Configuration errors are raised in `__init__` (before any metadata is read). Metadata errors name the extra and the position of the faulty entry. Invalid values raise `ValueError`, invalid types `TypeError`. | `_validate_config`, `update`          |
| Pure besides `metadata` | `update` reads the configuration and mutates only `metadata`. No file access, no global state, no state kept between calls: a hook instance can be reused and gives the same result each time. The only environment read is `HATCHLING_AUTOEXTRAS_WARN_ONLY`, once, in `__init__`. | `update`                              |
| Minimal                 | One runtime dependency (`hatchling`). One public class and one entry point. Three options, all keyword-style entries of the `pyproject.toml` hook table.                                        | the module                            |
| Observable              | What was generated is logged at `DEBUG` level (`logger.debug`), never printed.                                                                                                                  | `update`                              |

Not guaranteed, and documented as such:

- **Validity of a requirement.** The hook does not parse requirements. A string that is not a valid
  PEP 508 requirement is copied as is and rejected by hatchling afterwards (with a message that
  names the generated extra).
- **Semantic deduplication.** `numpy>=2` and `numpy >= 2` are two strings, so they are two entries
  of the generated extra. Hatchling merges them when it normalizes the metadata, so the built
  `METADATA` has one entry **[reading]**.
- **PEP 735 dependency groups**, `dynamic = ["optional-dependencies"]` and hatchling's
  `allow-ambiguous-features` (section 9, D6).

## 2. What differs today

| #   | Finding                                                                                                                                                                                                                                                                                                                                                                  | Status       | Fixed by |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------ | -------- |
| F1  | **Unknown options are ignored.** `{"excludes": ["a"]}` (typo) builds the extra with `a` included. The config is merged with `{...} \| config` and only the three known keys are read.                                                                                                                                                                                   | **[verified]** | 1      |
| F2  | **Names are compared case- and separator-sensitively.** `group-name = "All"` with an existing `all` produces both `all` and `All`; hatchling later fails with "both evaluate to `all`", far from the cause. `exclude = ["A"]` does not exclude `a`; `exclude = ["B.c"]` does not exclude `B_c`.                                                                          | **[verified]** | 2      |
| F3  | **`group-name` is not validated as a name.** Only "non-empty after `strip`" is checked, so `" all "`, `"a b"` or `"é"` are accepted and the key `" all "` is written to the metadata (hatchling rejects it later, naming the generated extra, not the option).                                                                                                              | **[verified]** | 2      |
| F4  | **Invalid dependency entries are dropped silently.** `[1, "  "]` produces `all = []` without any message, while a non-list value raises. The two cases are the same mistake (an invalid extra), handled in opposite ways, and a typo can remove a dependency from `all` unnoticed.                                                                                         | **[verified]** | 3      |
| F5  | **`exclude` entries that match no extra are ignored.** A typo (`exclude = ["tset"]`) silently puts the test dependencies into the public `all` extra. The README documents this as a feature, but it is the one option whose mistake leaks dependencies.                                                                                                                 | **[verified]** | 3      |
| F6  | **The conflict raises `RuntimeError`.** The situation is an invalid configuration (an extra already has the name), not a runtime failure. `CLAUDE.md` says `ValueError` for invalid values. A caller catching `ValueError` for "bad config" misses it.                                                                                                                     | **[reading]**  | 4      |
| F7  | **Two parallel checks of the same shape.** `__init__` validates with three inline blocks (two of them the same `exclude` check split in two `if`), and `update` repeats the type checks for the metadata. Defaults are in `__init__`, the allowed keys nowhere.                                                                                                           | **[reading]**  | 1      |
| F8  | **`update` mixes validation and mutation.** The loop validates `deps` while collecting, and `optional_dependencies` is the live dict of `metadata`. It is atomic today only because the assignment is the last statement; a later edit that assigns earlier would break the property without a test failing (the test exists, but the design does not make it obvious). | **[reading]**  | 3      |
| F9  | **`metadata["optional-dependencies"] = optional_dependencies` is redundant** when the key exists (same object) and is the only reason `update` has two paths for "no optional dependencies".                                                                                                                                                                             | **[reading]**  | 3      |
| F10 | **Documentation is not organized around properties.** The README lists "Features" and "Regardless of the options" bullet lists; the guarantees (atomic, deterministic, name matching) are not stated, and the docstring of `update` says "removes duplicates, sorts them alphabetically" without saying what is a duplicate.                                              | **[reading]**  | 5      |
| F11 | **`__version__` uses `version(__name__)`.** It works, but `__name__` is the import name, not the distribution name; the two only coincide up to `-`/`_` normalization. A literal `"hatchling-autoextras-hook"` is explicit and the `# pragma: no cover` fallback is unreachable in every supported install.                                                                | **[reading]**  | 6      |
| F12 | **Test gaps.** Missing: unknown option, name normalization, `exclude` of the generated name, a full-literal `metadata` assertion with several extras and a custom group name, determinism for a different order of extras. The integration tests build real wheels but none builds with a custom `group-name` plus `exclude` plus `overwrite` together.                  | **[reading]**  | 7      |

What is already right and must not change: one class registered through one `hatch` entry point;
`py.typed`; the `{defaults} | config` merge idea; atomic failure; `sorted(set(...))`; the
`logger.debug` summary; the dependency footprint; the integration tests that build real projects
with several hatchling versions.

## 3. Architecture

One module, `hooks.py`, one public class. No new module: the helpers are private functions of the
same file. A second module would only be justified by a second hook.

```text
src/hatchling_autoextras_hook/
├── __init__.py   # re-exports AutoExtrasMetadataHook and __version__
└── hooks.py      # AutoExtrasMetadataHook, _normalize, hatch_register_metadata_hook
```

### 3.1 Configuration

The options live in one table, so the allowed keys, the defaults and the documentation come from the
same place.

```python
_DEFAULTS: dict[str, Any] = {"group-name": "all", "exclude": [], "overwrite": False}
_NAME_PATTERN = re.compile(r"^([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9._-]*[A-Za-z0-9])$")


def _normalize(name: str) -> str:
    r"""Normalize an extra name (PEP 685 / PEP 503).

    ```pycon

    >>> _normalize("Dev_Extra")
    'dev-extra'

    ```
    """
    return re.sub(r"[-_.]+", "-", name).lower()
```

`_NAME_PATTERN` is the rule of hatchling (`is_valid_project_name`); it is copied, not imported,
because `hatchling.metadata.utils` is not public API and the supported range starts at 1.18.

`__init__` merges the defaults and `config` and calls `_validate_config`, which now has four
checks, in this order, each with a message that names the option:

1. `unknown = config.keys() - _DEFAULTS.keys()` → `_report("Unknown option(s): ['excludes'].
   Valid options: ['exclude', 'group-name', 'overwrite']")` (F1): a `ValueError` by default, a
   warning in warn-only mode (section 3.4). The unknown keys are dropped from the config.
2. `group-name` is a `str` (else `TypeError`) matching `_NAME_PATTERN` (else `ValueError`) (F3).
3. `exclude` is a `list` of `str` (one check, one message; F7) and does not contain `group-name`
   after normalization (`ValueError`: excluding the generated extra is meaningless).
4. `overwrite` is a `bool` (`TypeError`).

The validated and normalized values are stored once (`self._group`, `self._exclude` as a
`frozenset` of normalized names) so `update` does no conversion.

### 3.2 `update`

Validate everything first, mutate last (F8, F9). Sketch, not final code:

```python
def update(self, metadata: dict[str, Any]) -> None:
    extras = metadata.get("optional-dependencies", {})
    if not isinstance(extras, dict):
        msg = "'optional-dependencies' must be a table of extras"
        raise TypeError(msg)

    by_name = {_normalize(name): name for name in extras}  # normalized -> declared
    if (conflict := by_name.get(self._group)) is not None and not self._overwrite:
        msg = (
            f"Cannot create the '{self.config['group-name']}' extra: '{conflict}' already exists. "
            f"Existing extras: {sorted(extras)}. Set another 'group-name' or 'overwrite = true'"
        )
        raise ValueError(msg)
    if unknown := self._exclude - by_name.keys():
        msg = f"'exclude' contains names that match no extra: {sorted(unknown)}"
        self._report(msg)  # raises ValueError, or warns in warn-only mode

    sources = [n for n in extras if (key := _normalize(n)) != self._group and key not in self._exclude]
    dependencies = {dep for name in sources for dep in _dependencies(name, extras[name])}

    extras.pop(conflict, None)  # only reached with overwrite=True
    extras[self.config["group-name"]] = sorted(dependencies)
    metadata["optional-dependencies"] = extras
    logger.debug(...)
```

`_dependencies(name, value)` is the only place that inspects an extra: it raises
`TypeError("Dependencies of extra 'dev' must be a list of strings")` for a non-list, `TypeError`
naming the extra and the 1-based position (`"Dependency #2 of extra 'dev' must be a string"`) for a
non-string, `ValueError` for a blank string, and returns the stripped strings (F4). It is a private
function with its own docstring and tests.

Three decisions are visible in the sketch:

- The excluded extras and the generated extra are skipped _before_ their content is validated, as
  today. A broken extra that is excluded does not fail the build (it is not the hook's business);
  hatchling still validates it afterwards.
- The unmatched `exclude` entry goes through `_report` (section 3.4): it is the only metadata
  problem that can be downgraded to a warning.
- The unknown-`exclude` check uses the normalized names of **all** extras, including the generated
  one, so `exclude = ["all"]` is rejected earlier by the option check and never reaches here.

`metadata["optional-dependencies"] = extras` stays, but only for the case where the key was absent
(`metadata.get` returns a fresh `{}`), and the code comment says so. If the key exists the same
object is mutated.

### 3.3 Registration

Unchanged: `PLUGIN_NAME = "autoextras"`, `hatch_register_metadata_hook`, the entry point
`autoextras = "hatchling_autoextras_hook.hooks"`.

### 3.4 Strict by default, warn-only on request

One private method decides what happens to a _recoverable_ problem, so the rule is in one place:

```python
_WARN_ONLY_ENV = "HATCHLING_AUTOEXTRAS_WARN_ONLY"


def _report(self, msg: str) -> None:
    if not self._warn_only:
        raise ValueError(msg)
    warnings.warn(msg, UserWarning, stacklevel=2)
```

- **Reading.** `__init__` reads `os.environ.get(_WARN_ONLY_ENV)` once and stores a `bool`. Accepted
  values (case-insensitive): `1`, `true`, `yes`, `on` (enable) and `0`, `false`, `no`, `off`, empty
  or unset (disable). Any other value raises `ValueError` naming the variable: a typo must not
  silently disable the mode, or silently enable it.
- **Why an environment variable and not a fifth option.** Strictness is a property of _who builds_
  (strict in CI and for releases, lenient on a laptop or in a downstream rebuild of a sdist), not of
  the project, and the hook table is committed. The option table stays at three keys and the project
  cannot weaken its own checks by accident. The variable is read by the build backend process, so
  `python -m build` and `pip install .` pass it through (build isolation keeps the environment).
- **Why `warnings.warn` and not `logger.warning`.** Build frontends do not configure `logging`, so
  a logged warning is invisible; a `UserWarning` is shown on stderr by default. `print` is
  forbidden by `CLAUDE.md`.
- **What is recoverable** (the hook can continue and the result is well defined and documented):

  | Problem                                   | Strict (default)   | Warn-only                                      |
  | ----------------------------------------- | ------------------ | ---------------------------------------------- |
  | Unknown option                            | `ValueError`       | warning, the option is ignored                 |
  | `exclude` entry that matches no extra     | `ValueError`       | warning, the entry has no effect               |

- **What is never recoverable** (continuing would produce a wrong or ambiguous extra, or hatchling
  rejects the result anyway): a wrong type or an invalid name for an option, `group-name` in
  `exclude`, an existing extra with the generated name and `overwrite = false`, `optional-dependencies`
  that is not a table, an extra that is not a list, a non-string or blank dependency (hatchling
  rejects it in the source extra afterwards, so dropping it would only move the error).
- **No per-problem switches.** One boolean for the whole hook. A list of ignorable problems would
  be a second configuration language to document and test.

### 3.5 What is deliberately not in the target

- **No parsing of requirements** (`packaging.requirements.Requirement`). It would allow a sort by
  project name and semantic deduplication, but hatchling does both afterwards, `packaging` is not a
  declared dependency, and the string order is the order hatchling writes anyway **[reading]**.
- **No `include` option.** `exclude` plus `group-name` covers the use cases; a second selection
  option would need rules for their interaction (precedence, conflicts, tests) for no new capability.
- **No merge with the previous content of the generated extra.** `overwrite = true` replaces it, as
  documented; "append" would make the output depend on a hand-written list the user cannot see in
  the built metadata.
- **No dependency-group (PEP 735) support**: they are not package metadata.
- **No multiple generated extras** (a table of groups). One hook table = one extra. A project that
  needs two can be served by a future, separate decision (D5), not by growing this class.

## 4. Public API after the change

```python
from hatchling_autoextras_hook import AutoExtrasMetadataHook, __version__
```

| Item                                         | Change                                                                                                  |
| -------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| `AutoExtrasMetadataHook(root, config)`       | Unknown options raise `ValueError` (a warning with `HATCHLING_AUTOEXTRAS_WARN_ONLY=1`); `group-name` must be a valid extra name; `exclude` is normalized. |
| `AutoExtrasMetadataHook.update(metadata)`    | Conflict raises `ValueError` (was `RuntimeError`); invalid dependency entries raise (were dropped); an `exclude` entry that matches no extra raises `ValueError` (a warning with `HATCHLING_AUTOEXTRAS_WARN_ONLY=1`); names are compared normalized. |
| Environment variable `HATCHLING_AUTOEXTRAS_WARN_ONLY` | New. Truthy (`1`, `true`, `yes`, `on`) downgrades the two recoverable problems to a `UserWarning`. Any other unrecognized value raises `ValueError`. |
| `hatch_register_metadata_hook()`             | Unchanged.                                                                                              |
| `__all__` of the package                     | Unchanged: `AutoExtrasMetadataHook`, `__version__`.                                                     |
| `pyproject.toml` hook table                  | Same three keys, same defaults. Existing valid configurations keep working; only previously silent mistakes now fail. |

Release notes (breaking behaviour, no signature change):

1. Unknown keys in `[tool.hatch.metadata.hooks.autoextras]` are rejected.
2. `group-name` must be a valid extra name; it is no longer accepted with surrounding whitespace.
3. Names in `exclude` must match an extra (normalized comparison), and the match is no longer
   case-sensitive.
4. Non-string and blank dependency entries raise instead of being dropped.
5. An existing extra with the same name raises `ValueError` instead of `RuntimeError`.
6. New environment variable `HATCHLING_AUTOEXTRAS_WARN_ONLY=1`: unknown options and unmatched
   `exclude` entries warn instead of failing. Everything else still fails.

## 5. Dependents

- **Users** are build systems that enable the hook with `[tool.hatch.metadata.hooks.autoextras]`.
  A project that is valid today and has no typo builds identically (same extra, same order). A
  project that fails after the change had a silent mistake (section 2); the messages say which.
- **The integration test project** (`tests/integration/test_hooks.py`) pins
  `hatchling-autoextras-hook>=0.1.3` and must be bumped with the version (see `CLAUDE.md`,
  **Releases**).
- **`tests/package_checks.py`** calls `AutoExtrasMetadataHook("test", {}).update({})` and expects
  `{"optional-dependencies": {"all": []}}`: it stays valid (the empty-project case is kept).
- **Docs to update:** `README.md` (Properties section, Errors table with a "Warn-only" column, a "Strict and warn-only
  modes" section for the environment variable, `exclude` notes, FAQ),
  `.github/CONTRIBUTING.md` only if a command changes (none planned), the class docstring (kept in
  sync with the README options, per `CLAUDE.md`).

## 6. Evidence

Probes on `main` (hatchling 1.33.0, `.venv/bin/python`), all on the Python API:

| Probe                                                           | Result on `main`                                                         |
| --------------------------------------------------------------- | ------------------------------------------------------------------------ |
| `{"excludes": ["a"]}` with extras `a`, `b`                       | no error; `all = ["x", "y"]` (F1)                                        |
| `group-name = " all "`                                           | key `' all '` written, no error (F3)                                     |
| `group-name = "All"` with an existing `all`                      | both `all` and `All` in the table, no error (F2)                         |
| `exclude = ["A"]` with extra `a`; `exclude = ["B.c"]` with `B_c`  | nothing excluded (F2)                                                    |
| extra `a = [1, "  "]`                                            | `all = []`, no error (F4)                                                |
| `a = ["numpy>=2", "numpy >= 2", "NumPy>=2.0"]`                   | three entries in `all` (kept; hatchling merges them later, section 1)    |
| `b = ["pkg[a]", "x; python_version<'3.12'"]`                     | copied unchanged, as wanted: hatchling resolves `pkg[a]` itself          |

Hatchling facts used (**[reading]** of `hatchling/metadata/core.py`, 1.33.0): option names are
validated with `is_valid_project_name`, normalized with `normalize_project_name` (unless
`allow-ambiguous-features`), two options with the same normalized name raise, every entry must be a
`str` and a valid requirement, entries are stored in a dict keyed by the formatted normalized
requirement and sorted. The step that checks the hatchling **1.18** behaviour must be done with the
version matrix (`dev/config/package_versions.json`) in the integration test (section 8).

## 7. Changes to reach the target state

One branch and one pull request per step (`CLAUDE.md`). The order keeps every step releasable and
each PR small. Branch names in the second column.

| Step | Branch                       | Change                                                                                                                                                                                                  | Breaking |
| ---- | ---------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- |
| 1    | `refactor/option-table`      | **Option table, unknown options and the warn-only switch (F1, F7).** `_DEFAULTS`, one `exclude` check, reject unknown keys, `_WARN_ONLY_ENV` and `_report` (section 3.4). Tests: unknown option (message listing the valid ones), warn-only mode, invalid variable value, `exclude` type errors merged. | yes      |
| 2    | `bugfix/normalize-names`     | **Name normalization (F2, F3).** `_normalize`, `_NAME_PATTERN`, `group-name` validation, normalized `exclude` and collision check, replace the colliding key on overwrite. Regression tests first.       | yes      |
| 3    | `refactor/validate-then-mutate` | **Strict extras and atomic update (F4, F5, F8, F9).** `_dependencies` helper, errors for non-string and blank entries, unknown `exclude` entries, validate-then-mutate structure.                    | yes      |
| 4    | `refactor/value-error-conflict` | **`ValueError` for the conflict (F6).** Message updated, README errors table and troubleshooting section (`Cannot create 'all' group` title) updated. Can be merged into step 3.                   | yes      |
| 5    | `docs/properties`            | **Documentation (F10).** Properties table in the package docstring and in the README, Errors table, `exclude` notes (matching rules), FAQ entry "Why does the build fail on a typo?".                  | no       |
| 6    | `chore/version-literal`      | **`__version__` (F11).** Read the version with the literal distribution name; keep `importlib.metadata` as the source (D4) and drop the `# pragma: no cover` fallback if D4 is accepted.             | no       |
| 7    | `test/fill-gaps`             | **Tests (F12).** Full-literal `metadata` assertions, order-independence, idempotence with the new rules, the combined integration build. Can be spread over steps 1 to 4 (preferred).                  | no       |

Steps 1 to 4 each add their own regression tests and check that they fail without the `src` change
(`git stash push src`). Step 6 is optional; drop it if the maintainers prefer the current code (D4).

## 8. Tests and gates

Unit tests mirror the source tree (`tests/unit/test_hooks.py`); the conventions of `CLAUDE.md`
apply (one behaviour per test, literal expected values, a regression test for every bug, no local
imports, `match` on every `pytest.raises`).

**Configuration (`__init__`, `_validate_config`)**

- unknown option raises `ValueError` and the message lists the valid options (F1);
- with `HATCHLING_AUTOEXTRAS_WARN_ONLY=1` (`monkeypatch.setenv`), the same unknown option emits a
  `UserWarning` (`pytest.warns`, `match` on the message), does not raise, and is absent from the
  merged config;
- warn-only variable: `1`, `true`, `TRUE`, `yes`, `on` enable; `0`, `false`, `no`, `off`, `""` and
  unset disable (parametrized); `"maybe"` raises `ValueError` that names the variable;
- warn-only mode does not downgrade a non-recoverable problem: an invalid `group-name` and a wrong
  `overwrite` type still raise;
- two unknown options are both reported, sorted;
- `group-name`: valid values are accepted (`"all"`, `"full"`, `"my_extra"`, `"a.b"`, a single
  character); invalid values raise `ValueError` (`""`, `" "`, `" all "`, `"a b"`, `"-a"`, `"a-"`,
  `"é"`) (F3, parametrized); a non-string raises `TypeError`;
- `exclude`: non-list and non-string items raise `TypeError`; `exclude` containing the group name in
  another spelling (`group-name = "all"`, `exclude = ["ALL"]`) raises `ValueError`;
- `overwrite`: non-bool raises `TypeError` (`"true"`, `1`, `None`);
- defaults: the merged config equals `{"group-name": "all", "exclude": [], "overwrite": False}`, and
  an override changes only its own key.

**`_normalize`**: `Dev_Extra` → `dev-extra`, `a..b` → `a-b`, `A-_-B` → `a-b`, already normalized is
unchanged, idempotent.

**`_dependencies`** (private, tested directly): list of strings returned stripped; a non-list raises
`TypeError` that names the extra; a non-string item raises `TypeError` that names the extra and the
position (`#2`); a blank item raises `ValueError` that names the extra and the position; an empty
list returns `[]`.

**`update`**

- typical: default group, custom group, no optional dependencies, empty table, one extra, several
  extras;
- duplicates across extras are merged; duplicates inside one extra are merged; whitespace is
  stripped; the output is sorted; the result does not depend on the order of the extras (two
  parametrized orders, same literal);
- `exclude`: one, several, an extra excluded and also listed in another (dependency still included
  through the other extra), the match is normalized (`exclude = ["B.c"]` excludes `B_c`) (F2),
  an unknown name raises `ValueError` that lists it (F5); in warn-only mode the same name emits a
  `UserWarning` and the generated extra is identical to the one without that name (asserted against
  a full literal); an excluded extra whose content is invalid does not fail the build;
- warn-only mode with a conflict (`overwrite = false`), a non-list extra or a non-string entry
  still raises (the mode downgrades only the two recoverable problems);
- `overwrite`: `false` raises `ValueError` (message names the existing extra and the existing
  extras); `true` replaces and discards the previous content; an existing `All` is replaced, not
  duplicated, when `group-name = "all"` and `overwrite = true` (F2); `overwrite = true` without an
  existing extra is a no-op option; `overwrite` with `exclude`; a custom `group-name` with `exclude`;
- invalid metadata: `optional-dependencies` is not a table; an extra is not a list; an entry is not
  a string; an entry is blank; each leaves `metadata` unchanged (atomic) (F8), asserted against the
  full literal;
- side effects: the original extras are unchanged, other metadata keys are preserved, a second call
  with `overwrite = true` gives the same result (idempotent), a second call with `overwrite = false`
  raises, a hook instance can be reused;
- **whole-output assertion**: at least one test per scenario asserts the entire `metadata` dict
  against a literal (several extras, a custom group name, an exclusion, a duplicate), as required by
  `CLAUDE.md`;
- logging: the `DEBUG` record contains the group name, the number of dependencies and the extras
  that were used; the overwrite record is emitted only with `overwrite = true`.

**Integration (`tests/integration/test_hooks.py`)** keeps real builds, no patching:

- the existing builds (default, custom name, exclude, overwrite, conflict);
- **new:** a build with `group-name = "Full_Extra"`: the built `METADATA` has `Provides-Extra:
  full-extra` (name normalized by hatchling) and the dependency lines carry `extra == 'full-extra'`;
- **new:** a build with an extra that references the package (`testpkg[numpy]`): the generated extra
  contains the dependencies of `numpy` once, which proves that the hatchling resolution and the hook
  agree (the unit tests only prove that the string is copied);
- **new:** a build with an unknown option fails and the error output contains the option name;
- **new:** the same build with `HATCHLING_AUTOEXTRAS_WARN_ONLY=1` in the environment of the
  subprocess succeeds, the stderr contains the warning, and the built `METADATA` is the same as the
  build without the unknown option (proves the variable reaches the isolated build backend);
- run on the hatchling matrix of `dev/config/package_versions.json` through the existing CI jobs;
  nothing is added to the matrix.

**Gates** (what must be true before each PR is merged): `ruff check`, `ruff format`, `ty check`,
`pre-commit run --all-files`, `.venv/bin/pytest tests` with 100% coverage of the changed lines
(`--cov=hatchling_autoextras_hook --cov-report=term-missing`), `inv test.doctest-src`, and the CI
`ci.yaml` workflow green. The target file has no `# noqa` and no `# type: ignore`.

## 9. Decisions for the maintainers

**D1. [Decided] Raise on an `exclude` entry that matches no extra, and offer a warn-only mode?**
_Decision: fail loudly by default; `HATCHLING_AUTOEXTRAS_WARN_ONLY=1` downgrades the recoverable
problems (this one and the unknown option) to a `UserWarning`._ An `exclude` typo silently _adds_
dependencies (often `dev` or `test`) to a public extra (F5), so the default must stop the build.
The escape hatch is for a shared hook configuration that lists extras which only exist in some
projects, or for rebuilding a project one does not own. See section 3.4 for the recoverable list and
the reasons for an environment variable. Open sub-question: the variable name (alternatives:
`AUTOEXTRAS_WARN_ONLY`, a `HATCHLING_AUTOEXTRAS_STRICT=0` that reads as "not strict"); the
recommendation is the explicit, prefixed `..._WARN_ONLY`.

**D2. Raise on invalid dependency entries instead of dropping them?** _Recommended: yes._ The two
cases (non-list, bad entry) are the same mistake and hatchling raises for both afterwards; dropping
makes the error appear later, with a message that names the generated extra instead of the source
one. Alternative: pass every entry through unchanged and let hatchling report it (even simpler
code, worse message).

**D3. Which exception for an existing extra: `ValueError` or a dedicated exception?** _Recommended:
`ValueError`_ (`CLAUDE.md`: invalid values). A dedicated `AutoExtrasError(ValueError)` would let
tools catch the hook's errors only, at the price of one more public name. Not needed for a
single-purpose build hook.

**D4. `__version__` from the metadata or a literal?** _Recommended: keep `importlib.metadata`_ but
use the distribution name literal. It is the single source of truth (`pyproject.toml`), and a
literal in the code would add a second place to bump. The `# pragma: no cover` fallback stays only
if it cannot be tested; the cheap alternative is to drop the fallback and let `PackageNotFoundError`
propagate (an uninstalled package cannot be loaded as a hatchling plugin anyway).

**D5. Several generated extras?** _Recommended: no._ One table, one extra keeps the properties
checkable. If it is needed later, a separate step can accept a list of tables
(`[[tool.hatch.metadata.hooks.autoextras.groups]]`), which is additive and does not conflict with
this design.

**D6. Support `allow-ambiguous-features`?** _Recommended: no._ Hatchling's switch disables the
normalization of extra names; supporting it means reading `tool.hatch.metadata` from the hook for
a legacy option. The normalized comparison is the PEP 685 behaviour and the default.

## 10. Not covered

- **`dynamic = ["optional-dependencies"]`.** Hatchling forbids a field to be both static and
  dynamic, and the hook receives only the static fields; whether another hook can feed this one is
  not specified. Check the behaviour on the matrix before documenting anything.
- **Order of metadata hooks.** Hatchling runs one metadata hook per project (`custom` or one named
  plugin); the README's "compatible with other hooks" sentence should be verified or removed.
- **Python < 3.11 and hatchling >= 2.0.** The supported ranges are unchanged.
- **CI, release and tooling** (`.github/`, `.make/`, `dev/`): out of scope, they were aligned with
  `coola` in the last three commits.

## Appendix: effect on the size of the package

| File                        | Today | Target (estimate) | Why                                                                                   |
| --------------------------- | ----- | ----------------- | ------------------------------------------------------------------------------------- |
| `hooks.py` (code)           | ~75   | ~85               | `_normalize`, `_dependencies` and the option table replace the inline checks          |
| `hooks.py` (docstrings)     | ~110  | ~130              | Properties table in the module docstring, `Raises` of the two new helpers             |
| `tests/unit/test_hooks.py`  | 34 tests | ~70 tests      | one behaviour per test, the new rules, parametrized names                             |
| `tests/integration`         | existing | +3 builds      | normalized name, self-reference, unknown option                                       |

The package grows slightly in lines and shrinks in behaviours that need explanation: every
exception in the table of the README maps to one check, and no input is ignored.
