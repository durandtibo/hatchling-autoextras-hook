# `hatchling_autoextras_hook`: target state and the changes to reach it

This document describes the design that `hatchling_autoextras_hook` should have, then the changes to
make to the current implementation (`main`, `cd6059f`) to get there. It replaces the previous
version of this file (written at `6a04c5d`): the steps of that version are merged (#253 to #257),
so this review starts from the code as it is now and lists only what still differs. The design
follows the rules of `CLAUDE.md` (strict validation, `msg` variable, keyword-style options,
docstrings, one behaviour per test, every patched behaviour has an integration test) and the
documented behaviour in `README.md`. Its aim is a package that stays tiny and is easy to maintain:
**one hook class, three options, one normalization rule, no silent fallback, one source of truth for
each fact**. Breaking changes are accepted and the future state is more important than the past one.

Evidence comes from probes run on `main` (Python 3.14, hatchling 1.33.0, and 1.18.0 where stated;
scripts kept outside the repository). Items marked **[verified]** were reproduced; **[reading]**
comes from the code. Nothing in `src`, `tests` or `docs` was changed.

## 1. Properties of the sub-package

These are the rules the hook guarantees. They are the documented properties (module docstring of
`hooks.py` and **Properties** in `README.md`), kept as they are except for the three marked
_clarified_. Every design choice below exists to make one of them true **by construction** instead
of by the discipline of each code path.

| Property                | Statement                                                                                                                                                                                                                                                | Enforced by                    |
| ----------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------ |
| Union of the extras     | The generated extra contains every dependency string of every non-excluded extra, and nothing else. It never contains its own previous content. _Clarified:_ the strings are copied, not interpreted (see "Not guaranteed", self-references).                | `update`                       |
| Deterministic           | The output is the sorted list of the distinct stripped dependency strings, whatever the order of the extras. _Clarified:_ the generated extra is always the last key of the table, whether it is new, replaced or renamed by `overwrite`.                  | `sorted(set(...))`, `update`   |
| Additive                | Original extras are never modified, reordered or removed. Only the generated extra is added (or replaced when `overwrite = true`).                                                                                                                        | `update`                       |
| Atomic                  | `update` either completes or raises with `metadata` unchanged. The metadata is mutated in one last step.                                                                                                                                                  | validate first, mutate last    |
| Name-normalized         | Extra names are compared after PEP 685 normalization (`Dev_Extra`, `dev-extra` and `dev.extra` are the same extra), for `group-name`, `exclude` and the collision check, like hatchling does.                                                              | `_normalize`                   |
| Strict                  | By default, an unknown option, a wrong type, an invalid name, a non-string or blank dependency, and an `exclude` entry that matches no extra raise. Nothing is ignored silently.                                                                           | `_validate_config`, `update`   |
| Lenient on request      | With `HATCHLING_AUTOEXTRAS_WARN_ONLY=1`, the two _recoverable_ problems (unknown option, unmatched `exclude` entry) emit a `UserWarning` and the build continues. Every other problem still raises.                                                       | `_report`                      |
| Early and named errors  | Configuration errors are raised in `__init__`, before any metadata is read. Every message of a configuration problem names the option and the table `[tool.hatch.metadata.hooks.autoextras]` (_clarified_); metadata errors name the extra and the position. | `_validate_config`, `update`   |
| Pure besides `metadata` | `update` reads the validated options and mutates only `metadata`. No file access, no global state, no state kept between calls. The only environment read is `HATCHLING_AUTOEXTRAS_WARN_ONLY`, once, in `__init__`.                                         | `update`                       |
| Minimal                 | One runtime dependency (`hatchling`). One hook class, one entry point, `__version__`. Three options, all keyword-style entries of the `pyproject.toml` hook table.                                                                                        | the module                     |
| Observable              | What was generated is logged at `DEBUG` level (`logger.debug`), never printed.                                                                                                                                                                            | `update`                       |

Not guaranteed, and documented as such:

- **Validity of a requirement.** The hook does not parse requirements. A string that is not a valid
  PEP 508 requirement is copied as is and rejected by hatchling afterwards.
- **Semantic deduplication.** `numpy>=2` and `numpy >= 2` are two strings, so two entries of the
  generated extra. Hatchling merges them when it builds the metadata.
- **Self-references** (new, **[verified]**, F6). `docs = ["pkg[dev]"]` is a string like any other.
  With `exclude = ["dev"]`, the generated extra contains `pkg[dev]` (hatchling 1.18) or the
  dependencies of `dev` (hatchling 1.33, which resolves the reference): excluding an extra does not
  remove it from an extra that depends on it, which is the correct meaning.
- **PEP 735 dependency groups** and hatchling's `allow-ambiguous-features`.
- **Hooks that do not run.** Hatchling runs a metadata hook only when `project.dynamic` is not empty
  (F7). The hook cannot detect that it was not called.

## Constraints

1. **Simple and easy to maintain.** The package is one module of 393 lines (101 statements, 100 %
   branch coverage). The target removes code (one branch of `update`, one place that reads raw
   options) and adds none; the work is mostly in the tests and the documentation.
2. **Do not redo hatchling's work.** Hatchling validates requirements, normalizes names, merges
   equivalent requirements and (from a version after 1.18) resolves self-references. The hook
   produces the union of strings and fails early with a message that names the _source_ extra.
3. **Minimal footprint.** The only runtime dependency stays `hatchling>=1.18,<2.0`. No `packaging`
   import, no new dependency.
4. **Major release.** Compatibility is not a design input: no alias, no deprecation period. The
   changes of section 4 are listed in the release notes.
5. **The supported range is tested for real.** Python >= 3.11 and hatchling >= 1.18, < 2.0 are
   promises. Each hatchling version of the matrix must build a real project (F1).
6. **Loud by default, lenient on request.** Every problem raises; only the two recoverable problems
   can be downgraded by the person who runs the build, never by the project.

## 2. What differs today

| #   | Finding                                                                                                                                                                                                                                                                                                                                                                                                                                | Status         | Fixed by |
| --- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------- | -------- |
| F1  | **The integration builds ignore the hatchling matrix.** `build_minimal_project` writes `requires = ["hatchling", ...]` and `uv build` isolates the build, so every real build uses the latest hatchling. `ci-test-deps.yaml` installs 1.18 to 1.33 in the test environment, but only the Python API tests see it. Nothing proves that the output is accepted by the `core.py` of hatchling 1.18 (the example of F6 shows that 1.18 and 1.33 differ). | **[reading]**  | 1        |
| F2  | **Tests break the "one behaviour per test" rule of `CLAUDE.md`.** 10 unit tests and 10 integration tests have two to four `assert`/`pytest.raises` each (`test_update_does_not_overwrite_custom_group`, `test_hatch_register_metadata_hook_returns_correct_class`, ..., `test_autoextras_integration_exclude`). Integration tests check the `METADATA` with `in`/`not in` on a few lines: an extra or missing line is not detected, against the whole-output rule. | **[verified]** | 1, 2     |
| F3  | **Two sources of truth for the options.** `_validate_config` stores `_group` and `_exclude` (normalized), while `update` reads `self.config["group-name"]` and `self.config["overwrite"]` (raw). A change of a default or of a type has to be followed in two representations.                                                                                                                                                       | **[reading]**  | 3        |
| F4  | **The position of the generated extra depends on the spelling.** `overwrite = true` with an existing `All` and `group-name = "all"` deletes `All` and appends `all` (last); with the same spelling, the assignment keeps the old position. Keys of a TOML table have no meaning, hatchling sorts them, but the output of the hook is not a function of its input alone.                                                                  | **[verified]** | 3        |
| F5  | **Warnings and errors carry no context.** The warning of an unknown option points at `hooks.py:138` and the one of an unmatched `exclude` at `hooks.py:248` (`stacklevel=2` is the caller inside hatchling, not the user's file). The messages say `'exclude' contains names that match no extra`, but not which table: in a `python -m build` log of a project with several tools, that is a guess.                                  | **[verified]** | 3        |
| F6  | **The documentation does not describe self-references.** Probe: `dev = ["pytest"]`, `docs = ["sphinx", "pkg[dev]"]`, `exclude = ["dev"]` gives `all = ['pytest', 'sphinx']` on hatchling 1.33 and `all = ['pkg[dev]', 'sphinx']` on 1.18. Both are right, neither is written down.                                                                                                                                                   | **[verified]** | 4        |
| F7  | **The behaviour of `dynamic` is "not specified" in the README, but it is known.** No `dynamic` field: the hook never runs and no `all` is generated (**[verified]**). `dynamic = ["optional-dependencies"]` with a static table: hatchling fails (`cannot be both statically defined and listed in field project.dynamic`). Without a table the hook runs and writes `all = []`.                                                     | **[verified]** | 4        |
| F8  | **Stale and inconsistent text.** The class docstring says the warn-only mode downgrades "(currently the unknown options)" while it downgrades two problems (`hooks.py:90`); `Raises` of `__init__` says `TypeError: If the configuration is invalid` without the cases; the Minimal property says "one public class" but `__version__` is public; `CLAUDE.md` says the integration project pins `hatchling-autoextras-hook>=<version>`, it installs the working tree through a `file://` URI. | **[reading]**  | 4        |
| F9  | **The properties live in three places** (module docstring, README table, this review). No rule says which one wins; the first two already differ in wording.                                                                                                                                                                                                                                                                         | **[reading]**  | 4        |

What is already right and must not change: one class registered through one `hatch` entry point;
`py.typed`; the `{defaults} | config` merge; the single option table `_DEFAULTS`; `_normalize` and
`_NAME_PATTERN` (the copy of hatchling's rule, whose source is identical on 1.33.0 **[verified]**);
atomic failure; `sorted(set(...))`; validation before mutation; `_dependencies` as the only place
that inspects an extra; `_report` as the only place that decides between raising and warning; the
`logger.debug` summary; the dependency footprint; 100 % coverage.

## 3. Architecture

One module, `hooks.py`, one public class. No new module and no new public name.

```text
src/hatchling_autoextras_hook/
├── __init__.py   # re-exports AutoExtrasMetadataHook and __version__
└── hooks.py      # AutoExtrasMetadataHook, _dependencies, _normalize, _read_warn_only,
                  # hatch_register_metadata_hook
```

### 3.1 Configuration: validate once, store once (F3)

`_validate_config` keeps its four checks and their order (unknown options, `group-name`, `exclude`,
`overwrite`). It already computes the normalized values; the change is that it also stores the
validated raw ones, so `update` never reads `self.config`:

```python
def _validate_config(self) -> None:
    ...  # the checks of today, with the messages of section 3.3
    self._group_name: str = group_name  # written to the metadata, as the user spelled it
    self._group: str = _normalize(group_name)  # compared
    self._exclude: frozenset[str] = frozenset(_normalize(name) for name in exclude)
    self._overwrite: bool = overwrite
```

`self.config` stays what hatchling documents (the merged table); it is read once, in
`_validate_config`. That is the whole change of the option handling: four attributes, set in one
place, read in one place.

### 3.2 `update`: one rule for the position (F4)

The only structural change: the existing extra is removed whatever its spelling, and the generated
one is appended. This deletes the `if existing != group_name` branch.

```python
def update(self, metadata: dict[str, Any]) -> None:
    extras = metadata.get("optional-dependencies", {})
    if not isinstance(extras, dict):
        msg = "'optional-dependencies' must be a table of extras"
        raise TypeError(msg)

    by_name = {_normalize(name): name for name in extras}  # normalized -> declared
    existing = by_name.get(self._group)
    if existing is not None and not self._overwrite:
        ...  # ValueError, unchanged message
    if unmatched := sorted(self._exclude - by_name.keys()):
        self._report(f"...'exclude' ... match no extra: {unmatched}")

    sources = [
        n for n in extras if (key := _normalize(n)) != self._group and key not in self._exclude
    ]
    dependencies = {dep for name in sources for dep in _dependencies(name, extras[name])}

    # Everything is valid: the metadata is modified in one last step.
    extras.pop(existing, None)  # only reached with overwrite = true
    extras[self._group_name] = sorted(dependencies)
    metadata["optional-dependencies"] = extras  # the key is absent only if `extras` is a new dict
    logger.debug(...)
```

Contract: after `update`, `list(extras)[-1] == group-name` and every other key keeps its relative
order (Additive, Deterministic). Nothing else changes: same validation order, same atomicity, same
messages except section 3.3.

### 3.3 Messages name the table (F5)

One constant, used by the configuration messages and by `_report`:

```python
_TABLE = "[tool.hatch.metadata.hooks.autoextras]"
```

```text
Unknown option(s) in [tool.hatch.metadata.hooks.autoextras]: ['excludes']. Valid options: [...]
'exclude' in [tool.hatch.metadata.hooks.autoextras] contains names that match no extra: ['tset']
'group-name' in [tool.hatch.metadata.hooks.autoextras] must be a valid extra name (...), got 'a b'
```

`stacklevel=2` stays (it is required by `B028` and costs nothing), but the message no longer
depends on it: the location of a warning raised inside a build backend is not the user's file.
Metadata errors keep naming the extra and the position (`Dependency #2 of extra 'dev' ...`): the
table is not the culprit there.

### 3.4 Strict by default, warn-only on request

Unchanged and kept as is (decision D1): `_WARN_ONLY_ENV`, `_read_warn_only` (one read in
`__init__`, strict parsing of the value), `_report`. The recoverable problems are the unknown
option and the unmatched `exclude` entry; every other problem raises in both modes.

### 3.5 What is deliberately not in the target

- **No parsing of requirements** (`packaging`): it would allow a sort by project name and semantic
  deduplication, but hatchling does both and `packaging` is not a declared dependency.
- **No generated extra made of self-references** (`all = ["pkg[dev,docs]"]`). It looks like the
  simplest design (no copy, dedupe, strip or dependency validation), but it fails the supported
  range: **[verified]** hatchling 1.18 keeps `my-pkg[dev,docs]` as is in the metadata, while 1.33
  flattens it, so the built `METADATA` would differ by hatchling version and the hook would depend
  on the project `name` (D2).
- **No `include` option**, no merge with the previous content of the generated extra, no PEP 735
  groups, no several generated extras: unchanged from the previous review (nothing new argues
  for them).
- **No detection of a missing `dynamic` field.** The hook is not called, so it cannot report
  anything. The README says it first and shows the check (section 4).

## 4. Public API after the change

```python
from hatchling_autoextras_hook import AutoExtrasMetadataHook, __version__
```

| Item                                                  | Change                                                                                                                                           |
| ----------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| `AutoExtrasMetadataHook(root, config)`                | Same signature and options. The configuration messages name `[tool.hatch.metadata.hooks.autoextras]`.                                            |
| `AutoExtrasMetadataHook.update(metadata)`             | The generated extra is always the last key of `optional-dependencies` (before: in place when the spelling is the same). Same validation, same errors. |
| `AutoExtrasMetadataHook.config`                       | Unchanged (merged table). The hook no longer reads it after `__init__`.                                                                          |
| Environment variable `HATCHLING_AUTOEXTRAS_WARN_ONLY` | Unchanged.                                                                                                                                       |
| `hatch_register_metadata_hook()`                      | Unchanged.                                                                                                                                       |
| `__all__` of the package                              | Unchanged: `AutoExtrasMetadataHook`, `__version__`.                                                                                              |
| `pyproject.toml` hook table                           | Unchanged.                                                                                                                                       |

Release notes (behaviour, no signature change):

1. The generated extra is always the last key of `optional-dependencies`.
2. The messages of configuration problems name the `[tool.hatch.metadata.hooks.autoextras]` table.

Documentation of the target (F6 to F9), in the README:

- **Properties** table with the three clarifications of section 1, and the self-reference note in
  "Not guaranteed".
- **How hatchling calls the hook** (replaces "not specified"): the hook runs only if
  `project.dynamic` is not empty; `dynamic = ["optional-dependencies"]` cannot be combined with a
  static table (hatchling error); without a static table the hook generates `all = []`. A check to
  run after setting up: `hatch project metadata optional-dependencies` or `python -m build` and
  `Provides-Extra: all` in the `METADATA` of the wheel.
- The rule "the module docstring of `hooks.py` is the source of the **Properties** list; the README
  table repeats it with the same names and the same statements" goes in `CLAUDE.md` (D5).

## 5. Dependents

- **Users** are build systems with `[tool.hatch.metadata.hooks.autoextras]`. A valid project builds
  the same extra with the same content; only the position of the key can change and hatchling sorts
  the extras anyway (the built `METADATA` is identical **[reading]**).
- **`tests/integration/test_hooks.py`** installs the working tree through `file://` and must pin
  the hatchling version of the matrix (step 1).
- **`tests/package_checks.py`** (`AutoExtrasMetadataHook("test", {}).update({})` expects
  `{"optional-dependencies": {"all": []}}`) stays valid.
- **Docs to update:** `README.md`, the class docstring and the module docstring of `hooks.py`,
  `CLAUDE.md` (the pin sentence of **Releases**), `.github/CONTRIBUTING.md` only if a command
  changes (none planned).

## 6. Evidence

Probes on `main`, Python API and `ProjectMetadata` of the installed hatchling:

| Probe                                                                                          | Result                                                                                      |
| ---------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| Project with `optional-dependencies` and no `dynamic`                                           | no `all` in `core.optional_dependencies` (F7)                                               |
| Same project with `dynamic = ["description"]`                                                   | `all` generated (F7)                                                                        |
| `dynamic = ["optional-dependencies"]` and a static table                                        | `ValueError: Metadata field optional-dependencies cannot be both statically defined and listed in field project.dynamic` |
| `dynamic = ["optional-dependencies"]` and no table                                              | `{'all': []}` (F7)                                                                          |
| `docs = ["sphinx", "pkg[dev]"]`, `exclude = ["dev"]`, hatchling 1.33.0                          | `all = ['pytest', 'sphinx']` (F6)                                                           |
| Static `all = ["my-pkg[dev,docs]"]`, hatchling **1.18.0**                                       | `['my-pkg[dev,docs]']`, not flattened (rejects the self-reference design, D2)               |
| Same, hatchling **1.33.0**                                                                      | `['numpy>=2', 'pytest>=7', 'sphinx', "x; python_version < '3.12'"]`, flattened              |
| `{"All": ..., "dev": ..., "z": ...}` with `overwrite = true`                                    | key order `['dev', 'z', 'all']` (F4)                                                        |
| `HATCHLING_AUTOEXTRAS_WARN_ONLY=1` with an unknown option, then an unmatched `exclude`          | warnings located at `hooks.py:138` and `hooks.py:248` (F5)                                  |
| AST scan of `tests/`                                                                            | 10 unit and 10 integration tests with more than one assertion or `raises` (F2)              |
| `.venv/bin/pytest tests/unit --cov`, `ruff check`, `ty check` on `main`                         | 170 passed, 100 % coverage of `src`, no finding                                             |
| `is_valid_project_name` and `normalize_project_name` of hatchling 1.33.0                        | same regular expressions as `_NAME_PATTERN` (case-insensitive) and `_normalize`             |

Not run: the integration tests (they need `uv`, the network and build isolation) and the hatchling
1.18 to 1.32 matrix; F1 is a reading of the test project and of the workflows, and step 1 contains
the check that settles it.

## 7. Changes to reach the target state

One branch and one pull request per step (`CLAUDE.md`). The tests come first: steps 1 and 2 change
no behaviour and make steps 3 and 4 safe. Every step keeps the 100 % coverage gate.

| Step | Branch                          | Change                                                                                                                                                                                                                                                                                                   | Breaking |
| ---- | ------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- |
| 1    | `test/integration-matrix`       | **Real builds on the matrix (F1, F2).** The integration project requires `hatchling=={installed version}` (`importlib.metadata.version("hatchling")`). `read_extras(path) -> dict[str, list[str]]` parses the `METADATA`; each test asserts the whole dict against a literal. `validate_metadata` is deleted. | no       |
| 2    | `test/one-behaviour-per-test`   | **Split the 10 unit tests (F2).** One `assert` or one `raises` each; a failure test that checks "metadata unchanged" becomes two tests (the error, the unchanged metadata) sharing a fixture.                                                                                                              | no       |
| 3    | `refactor/validated-attributes` | **Sections 3.1 to 3.3 (F3, F4, F5).** Four stored attributes, `pop` then append, `_TABLE` in the messages. Regression tests first: key order after `overwrite` with the same and another spelling, the table name in each configuration message and in both warnings.                                    | yes (minor) |
| 4    | `docs/properties-and-dynamic`   | **Documentation (F6 to F9).** Properties wording, self-reference note, "How hatchling calls the hook" section with the verified behaviours, class docstring and `Raises` of `__init__`, `CLAUDE.md` pin sentence and the sync rule of D5.                                                                 | no       |

Steps 1 and 2 are independent; step 3 follows them; step 4 may be merged with step 3 if the diff
stays small. Step 3 checks that its regression tests fail without the `src` change
(`git stash push src`).

## 8. Tests and gates

Conventions of `CLAUDE.md` apply: one behaviour per test, literal expected values, no local imports,
`match` on every `pytest.raises`, no logic in a test body.

**Unit (`tests/unit/test_hooks.py`)** keeps its 170 cases; the additions and splits are:

- position: with `{"All": ..., "dev": ..., "z": ...}`, `group-name = "all"` and `overwrite = true`
  the keys are `["dev", "z", "all"]`; with `{"all": ..., "dev": ..., "z": ...}` and the same
  spelling they are also `["dev", "z", "all"]` (today: `["all", "dev", "z"]`); without an
  existing extra the generated extra is last; the original extras keep their relative
  order (parametrized on three layouts, full literal);
- messages: the unknown option, the invalid `group-name`, the `exclude` type and the unmatched
  `exclude` messages contain `[tool.hatch.metadata.hooks.autoextras]` (parametrized, one `match`);
  the warn-only variants emit the same text as a `UserWarning`;
- stored options: `update` gives the same result when `hook.config` is cleared after `__init__`
  (proves F3: nothing reads the raw table later);
- split tests (step 2): for each current multi-assert test, one test for the exception and one for
  the unchanged `metadata` (full literal);
- self-reference: `docs = ["pkg[dev]"]` with `exclude = ["dev"]` copies `pkg[dev]` unchanged (the
  documented behaviour of F6);
- the existing tests of `_dependencies`, `_normalize`, `_read_warn_only` stay as they are.

**Integration (`tests/integration/test_hooks.py`)**, real builds without patching:

- the project requires `hatchling=={version of the environment}` so the matrix of
  `ci-test-deps.yaml` and `nightly-package.yaml` builds with hatchling 1.18 to 1.33 (F1);
- each test reads `read_extras(wheel)` and asserts the complete mapping, for example the default
  build: `{"all": ["numpy>=2.0", "pytest>=9.0"], "dev": ["pytest>=9.0"], "numpy": ["numpy>=2.0"]}`;
  failures assert the return code and one `match` on the stderr message;
- **new:** a build with a self-reference extra and `exclude` asserts the content of `all` for the
  hatchling of the environment (the expected literal depends on the version: flattened from the
  version that resolves self-references; the test reads the version and picks one of two literals
  through a parameter of the test, not through a branch in its body);
- **new:** a build with `dynamic = ["optional-dependencies"]` and a static table fails with the
  hatchling message (documents F7 and detects a change of hatchling).

**Gates** before each merge: `ruff check`, `ruff format`, `ty check`, `pre-commit run --all-files`,
`.venv/bin/pytest tests` with 100 % coverage of the changed lines, `inv test.doctest-src`, and
`ci.yaml` green. The code of this change has no `# noqa` and no `# type: ignore`.

## 9. Decisions for the maintainers

**D1. Keep the warn-only mode?** _Recommended: keep._ It is a documented property and was decided
in the previous review. Its cost is about 55 of 393 lines and about 13 of 101 statements
(`_WARN_ONLY_*`, `_read_warn_only`, `_report`, two integration tests). The case for removing it:
a hook with no environment variable is simpler, and a project that cannot be changed can be patched
in its `pyproject.toml`. The case for keeping it: the person who rebuilds a project is not its
author. Removing it later is a breaking change for those users; adding it back is not.

**D2. Generate `all` as self-references (`pkg[dev,docs]`) instead of copied strings?**
_Recommended: no._ It would delete `_dependencies`, the dedup, the sort and the strip, but hatchling
1.18 and 1.33 build different metadata from it (section 6), and the hook would need
`metadata["name"]`.
Reconsider only if the supported range starts at the first hatchling that resolves self-references.

**D3. The generated extra is always last?** _Recommended: yes._ One rule instead of two, the output
is a function of the input, and the order of the TOML table is not significant to hatchling. The
alternative (keep the old position) needs the branch that this design removes.

**D4. Name the table in the configuration messages?** _Recommended: yes_ (one constant). The
alternative is to keep short messages and rely on the traceback, which a build frontend often hides.

**D5. Where do the properties live?** _Recommended:_ the module docstring is the source, the README
table repeats it, and `CLAUDE.md` says so (an update of one is an update of the other). A test that
compares them is not worth its code: the rule "no tests of trivial structure" applies, and a review
catches it.

**D6. Make `__version__` part of the properties?** _Recommended: yes, as a documented public name_
(the Minimal property already lists it). It is used by `tests/package_checks.py` and
`tests/unit/test_init.py`; the hook does not need it, which is the reason not to add more.

## 10. Not covered

- **`dynamic` support beyond what hatchling allows.** The hook cannot make a static table dynamic
  (F7); a project that wants it must keep a dummy dynamic field. A different design (the hook reads
  a table of its own instead of `optional-dependencies`) would be a different package.
- **Hatchling >= 2.0 and Python < 3.11:** the supported ranges are unchanged; the matrix file
  `dev/config/package_versions.json` is generated, never edited by hand.
- **Order of metadata hooks.** Hatchling runs one metadata hook per project; the README sentence is
  already "not specified".
- **CI, release and tooling** (`.github/`, `.make/`, `dev/`): out of scope, except the one pin of
  the hatchling version in the integration project (step 1).

## Appendix: effect on the size of the package

| File                       | Today                | Target (estimate)     | Why                                                                         |
| -------------------------- | -------------------- | --------------------- | --------------------------------------------------------------------------- |
| `hooks.py` (statements)    | 101                  | ~100                  | the `if existing != group_name` branch goes, four attribute assignments stay |
| `hooks.py` (docstrings)    | most of the 393 lines | same                  | Properties wording and `Raises` fixed, not extended                         |
| `tests/unit/test_hooks.py` | 97 tests, 851 lines  | ~115 tests, ~900 lines | the 10 multi-assert tests are split, the position and message tests are new |
| `tests/integration`        | 19 tests, 399 lines  | ~20 tests, ~350 lines | `read_extras` replaces `validate_metadata` and the substring checks         |

The package does not grow: the code gets one branch and one place that reads the options fewer, and
the tests get stronger (whole-output assertions on real builds of the whole hatchling range).
