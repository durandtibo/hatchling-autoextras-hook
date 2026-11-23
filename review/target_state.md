# `hatchling_autoextras_hook`: target state and the changes to reach it

This document describes the design that `hatchling_autoextras_hook` should have, then the changes to
make to the current implementation (`main`, `a97ba10`) to get there. It replaces the previous
version of this file (written at `cd6059f`): every step of that version is merged (#261 to #264),
and a re-read of the code shows it matches that target. This review therefore starts from the code
as it is now and lists **only what still differs**, which is little. The design follows the rules of
`CLAUDE.md` (strict validation, `msg` variable, keyword-style options, docstrings, one behaviour per
test, every patched behaviour has an integration test) and the documented behaviour of `README.md`.
Its aim is a package that stays tiny and is easy to maintain: **one hook class, three options, one
normalization rule, no silent fallback, one source of truth for each fact**. Breaking changes are
accepted and the future state is more important than the past one.

Evidence comes from probes run on `main` (Python 3.14, hatchling 1.33.0; scripts kept outside the
repository) and from the previous review for the hatchling 1.18 results. Items marked
**[verified]** were reproduced in this review; **[reading]** comes from the code. Nothing in `src`,
`tests` or `docs` was changed.

## 1. Properties of the sub-package

These are the rules the hook guarantees. They are the documented properties (module docstring of
`hooks.py` and **Properties** in `README.md`), with two changes marked _new_ and one marked
_clarified_. Every design choice below exists to make one of them true **by construction** instead
of by the discipline of each code path.

| Property                | Statement                                                                                                                                                                                                                                                                                  | Enforced by                  |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------- |
| Union of the extras     | The generated extra contains every dependency string of every non-excluded extra, and nothing else. It never contains its own previous content. The strings are copied, not interpreted.                                                                                                   | `update`                     |
| Deterministic           | The output is the list of the distinct stripped dependency strings, sorted as strings (code point order, so `Zed` comes before `alpha`), whatever the order of the extras. The generated extra is always the last key of the table, whether it is new, replaced or renamed by `overwrite`. _Clarified:_ "sorted alphabetically" was wrong for upper case. | `sorted(set(...))`, `update` |
| Additive                | Original extras are never modified, reordered or removed. Only the generated extra is added (or replaced when `overwrite = true`).                                                                                                                                                         | `update`                     |
| Atomic                  | `update` either completes or raises with `metadata` unchanged. The metadata is mutated in one last step.                                                                                                                                                                                   | validate first, mutate last  |
| Idempotent on request   | _New._ With `overwrite = true`, running `update` again on its own output gives the same metadata. With `overwrite = false` the second run raises (the extra exists): a build runs the hook once per `ProjectMetadata`, and that is not a promise of the hook.                              | `update`                     |
| Name-normalized         | Extra names are compared after PEP 685 normalization (`Dev_Extra`, `dev-extra` and `dev.extra` are the same extra), for the option naming the generated extra, `exclude` and the collision check, like hatchling does.                                                                       | `_normalize`                 |
| Strict                  | By default, an unknown option, a wrong type, an invalid name, a non-string or blank dependency, and an `exclude` entry that matches no extra raise. Nothing is ignored silently.                                                                                                           | `_validate_config`, `update` |
| Lenient on request      | With `HATCHLING_AUTOEXTRAS_WARN_ONLY=1`, the two _recoverable_ problems (unknown option, unmatched `exclude` entry) emit a `UserWarning` and the build continues. Every other problem still raises.                                                                                         | `_report`                    |
| Output-invariant        | _New._ The warn-only mode never changes the generated extra: a build that succeeds in both modes produces the same metadata. It only turns an error into a warning for a problem that has no effect on the result (an ignored option, an `exclude` entry that matches nothing).             | `_report`                    |
| Early and named errors  | Configuration errors are raised in `__init__`, before any metadata is read. Every message of a configuration problem names the option and the table `[tool.hatch.metadata.hooks.autoextras]`; metadata errors name the extra and the position.                                             | `_validate_config`, `update` |
| Pure besides `metadata` | `update` reads the validated options and mutates only `metadata`. No file access, no global state, no state kept between calls. The only environment read is `HATCHLING_AUTOEXTRAS_WARN_ONLY`, once, in `__init__`.                                                                          | `update`                     |
| Minimal                 | One runtime dependency (`hatchling`). One hook class, one entry point, `__version__`. Three options, all keyword-style entries of the `pyproject.toml` hook table.                                                                                                                         | the module                   |
| Observable              | What was generated is logged at `DEBUG` level (`logger.debug`), never printed.                                                                                                                                                                                                             | `update`                     |

Not guaranteed, and documented as such:

- **Validity of a requirement.** The hook does not parse requirements. A string that is not a valid
  PEP 508 requirement is copied as is and rejected by hatchling afterwards.
- **Semantic deduplication.** `numpy>=2` and `numpy >= 2` are two strings, and so are `Numpy` and
  `numpy` **[verified]**: two entries of the generated extra. Hatchling merges them when it builds
  the metadata.
- **Self-references.** `docs = ["pkg[dev]"]` is a string like any other. With `exclude = ["dev"]`,
  the generated extra contains `pkg[dev]` (hatchling 1.18) or the dependencies of `dev` (hatchling
  1.33, which resolves the reference): excluding an extra does not remove it from an extra that
  depends on it.
- **Ambiguous input.** Two extras with the same normalized name (`All` and `all`) are rejected by
  hatchling itself (`both evaluate to all` **[verified]**); the hook does not report it first and
  does not try to repair it.
- **PEP 735 dependency groups** and hatchling's `allow-ambiguous-features`.
- **Hooks that do not run.** Hatchling runs a metadata hook only when `project.dynamic` is not empty.
  The hook cannot detect that it was not called.

## 2. Constraints

1. **Simple and easy to maintain.** The code is one module of 414 lines, 107 statements, 100 %
   branch coverage; **246 of the 414 lines are docstrings** **[verified]**. The target removes text
   and renames; it adds no function and no branch.
2. **Do not redo hatchling's work.** Hatchling validates requirements, normalizes names, rejects
   ambiguous extras, merges equivalent requirements and (after 1.18) resolves self-references. The
   hook produces the union of strings and fails early with a message that names the _source_ extra.
3. **Minimal footprint.** The only runtime dependency stays `hatchling>=1.18,<2.0`. No `packaging`.
4. **Major release.** Compatibility is not a design input: no alias, no deprecation period. The
   README already says that no API is stable before 1.0. The changes of section 4 are listed in the
   release notes.
5. **The supported range is tested for real.** Python >= 3.11 and hatchling >= 1.18, < 2.0 are
   promises; the integration project pins the hatchling of the environment (#261), so each version
   of the matrix builds a real project.
6. **Loud by default, lenient on request.** Every problem raises; only the two recoverable problems
   can be downgraded by the person who runs the build, never by the project.
7. **One public import path.** The class is imported from the package root.

## 3. What differs today

| #   | Finding                                                                                                                                                                                                                                                                                                                                                                                                                                                     | Status         | Fixed by |
| --- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------- | -------- |
| F1  | **`group-name` is the wrong word.** The option names the generated _extra_ (PEP 685, `Provides-Extra`); "group" is the PEP 735 word for `[dependency-groups]`, which the hook does not read, and the README needs a FAQ entry to say so. The word is also used for the concept inside the code (`_group`, `_group_name`, "extras group" in the `update` docstring, `Created '%s' group`). 22 hits in `src`, 13 in `README.md`, 49 in `tests`.                  | **[reading]**  | 1        |
| F2  | **The sort order is documented wrongly.** The README says "Sorts dependencies alphabetically" and `update` says "sorts them alphabetically"; the code sorts the strings by code point: `["sphinx>=5", "sphinx-rtd", "Zed", "alpha"]` gives `['Zed', 'alpha', 'sphinx-rtd', 'sphinx>=5']`. The behaviour is right (deterministic, no parsing), the word is not.                                                                                          | **[verified]** | 2        |
| F3  | **The same facts are written in five places.** Module docstring (properties), class docstring (options, warn-only paragraph), README **Features** (6 bullets), README **Properties** (table), README "Regardless of the options" (5 bullets) and the **Errors** table. Three of them restate the Properties (strict validation, atomic and "leaves extras unchanged", DEBUG log). `CLAUDE.md` demands that all stay in sync, so each change costs five edits. | **[reading]**  | 2        |
| F4  | **Two import paths in the docs.** `README.md` (Python API) and the doctests of `hooks.py` import `hatchling_autoextras_hook.hooks`; the public API is the package root (`__init__.__all__`). `hooks` is an implementation module and the entry point target, and may be renamed freely if the docs do not teach it.                                                                                                                                         | **[reading]**  | 2        |
| F5  | **Two properties are true and tested but not written.** Idempotence with `overwrite = true` (`test_update_is_idempotent_with_overwrite`) and the fact that the warn-only mode cannot change the output (`test_update_exclude_unmatched_warn_only_result`, `test_unknown_option_warn_only_ignores_the_option`). Idempotence matters because a second run with `overwrite = false` raises **[verified]**, which looks like a defect and is not.                  | **[verified]** | 2        |

Probed and **rejected** as findings (no change, with the reason):

| Probe                                                                                                       | Result                                                                                                         | Why no change                                                                                                       |
| ----------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| `{"All": ..., "all": ..., "dev": ...}` with `overwrite = true`                                              | the hook removes the last spelling, keeps the other and appends `all`; hatchling then fails with its own clear message | Hatchling rejects the input with or without the hook. A repair in the hook would hide an invalid project.         |
| `{"Dev": ..., "dev": ...}` with `exclude = ["dev"]`                                                         | both are excluded                                                                                              | Correct: they are the same extra after normalization.                                                               |
| A non-string key in `optional-dependencies` (`{1: [...]}`)                                                  | `TypeError: expected string or bytes-like object` from `re.sub`, not naming the extra                          | Unreachable from a build (TOML keys are strings). The Python API raises the right type; a check would add a branch for nothing. |
| `sdist` then two `wheel` builds in one process (`hatchling.build`)                                          | the three succeed with `overwrite = false`                                                                     | Each build reads a fresh table; the hook never sees its own output.                                                 |
| `exclude` of every extra, or no extra at all                                                                | `all = []` is generated                                                                                        | Intended and documented: `pkg[all]` stays installable and never warns that the extra does not exist. Decision D3.   |
| Cost of `__version__` (`importlib.metadata.version` at import)                                               | negligible next to the import of hatchling (the package imports in 52 ms, most of it hatchling)                | A missing distribution cannot happen: hatchling finds the hook through the installed distribution's entry point.    |

What is already right and must not change: one class registered through one `hatch` entry point;
`py.typed`; the `{defaults} | config` merge; the single option table `_DEFAULTS`; `_normalize` and
`_NAME_PATTERN` (the copy of hatchling's rules); the four stored attributes set once in
`_validate_config` and read once in `update`; atomic failure; `sorted(set(...))`; validation before
mutation; `_dependencies` as the only place that inspects an extra; `_report` as the only place that
decides between raising and warning; `_TABLE` in the messages; the `logger.debug` summary; the
dependency footprint; 100 % coverage.

## 4. Public API after the change

```python
from hatchling_autoextras_hook import AutoExtrasMetadataHook, __version__
```

```toml
[tool.hatch.metadata.hooks.autoextras]
extra-name = "complete"  # was: group-name
exclude = ["dev", "docs"]
overwrite = false
```

| Item                                                  | Change                                                                                                                                         |
| ----------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| `AutoExtrasMetadataHook(root, config)`                | Same signature. The option `group-name` is renamed `extra-name` (F1); `group-name` becomes an unknown option and fails with the list of valid options. |
| `AutoExtrasMetadataHook.update(metadata)`             | Unchanged behaviour. The debug and error messages say "extra" instead of "group".                                                              |
| `AutoExtrasMetadataHook.config`                       | Unchanged (merged table, keys `exclude`, `extra-name`, `overwrite`).                                                                           |
| Environment variable `HATCHLING_AUTOEXTRAS_WARN_ONLY` | Unchanged.                                                                                                                                     |
| `hatch_register_metadata_hook()`, entry point         | Unchanged.                                                                                                                                     |
| `__all__` of the package                              | Unchanged: `AutoExtrasMetadataHook`, `__version__`.                                                                                            |
| Docs                                                  | One import path (the root), "sorted as strings", two new properties, fewer restatements (section 7, step 2).                                   |

Why no alias for `group-name`: the hook is strict (unknown options raise and list the valid ones),
so a project that still writes `group-name` fails at the first build with
`Unknown option(s) in [tool.hatch.metadata.hooks.autoextras]: ['group-name']. Valid options:
['exclude', 'extra-name', 'overwrite']`, which is the whole migration guide. An alias would be a
second spelling to validate, document and test forever.

Release notes (one breaking change, no new behaviour):

1. The option `group-name` is renamed `extra-name`. A project that uses `group-name` fails with an
   unknown-option error until it is renamed.
2. The documentation says that the dependencies are sorted as strings.

## 5. Dependents

- **Users** are build systems with `[tool.hatch.metadata.hooks.autoextras]`. Only the projects that
  set `group-name` are affected (the default `all` needs no change); the failure is immediate and
  names the fix. The generated metadata is identical.
- **`tests/`**: 49 mentions of `group-name`/`group_name`/`_group` to rename (unit and integration);
  `tests/package_checks.py` (`AutoExtrasMetadataHook("test", {}).update({})`) is unaffected.
- **Docs to update:** `README.md` (options table, the `group-name` option details, errors table,
  FAQ), the class, module and `update` docstrings of `hooks.py`, `CLAUDE.md` (one mention).
  `dev/` and `.github/` have none.
- **Nothing imports the package** besides hatchling (entry point `autoextras`).

## 6. Evidence

Probes on `main`, Python API and `hatchling.build` of the installed hatchling 1.33.0:

| Probe                                                                                      | Result                                                                                                  |
| ------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------- |
| `["sphinx>=5", "sphinx-rtd", "Zed", "alpha"]` in one extra                                  | `all = ['Zed', 'alpha', 'sphinx-rtd', 'sphinx>=5']` (F2)                                                |
| `["Numpy", "numpy"]`, and two spellings of one requirement with different spaces            | two entries each (not guaranteed: semantic deduplication)                                               |
| `overwrite = true`, `update` called twice on the same dict                                  | same result (F5)                                                                                        |
| `overwrite = false`, `update` called twice on the same dict                                 | `ValueError: Cannot create the 'all' extra: 'all' already exists ...` (F5)                              |
| Real project with `All` and `dev`, then `All`, `all` and `dev`, `overwrite = true`          | hatchling: `Optional dependency groups All and all of field project.optional-dependencies both evaluate to all` (rejected finding) |
| `build_sdist`, `build_wheel`, `build_wheel` in one process, `overwrite = false`             | three builds succeed (rejected finding)                                                                 |
| `exclude = ["dev"]` and `exclude = ["dev", "Dev"]` with only `dev`                          | `all = []` (rejected finding, D3)                                                                       |
| `{1: ["a"]}` as `optional-dependencies`                                                     | `TypeError: expected string or bytes-like object, got 'int'` (rejected finding)                         |
| AST count of `hooks.py`                                                                     | 414 lines, 246 of them docstrings (F3)                                                                  |
| `grep` of `group-name`, `group_name`, `_group`                                              | `src` 22, `README.md` 13, `tests` 49, `CLAUDE.md` 1 (F1)                                               |
| `.venv/bin/pytest tests` (unit and integration), `ruff check`, `ty check` on `main`         | 216 passed, no finding; unit tests alone: 190 passed, 100 % coverage of `src`                           |

Not re-run in this review: the hatchling 1.18 to 1.32 matrix (the previous review verified 1.18 and
1.33; CI runs the matrix) and `pre-commit run --all-files`.

## 7. Changes to reach the target state

One branch and one pull request per step (`CLAUDE.md`). Both steps are small; step 1 is the only
breaking one. The documentation of a step ships with the step.

| Step | Branch                       | Change                                                                                                                                                                                                                                                                                                                                                                      | Breaking |
| ---- | ---------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- |
| 1    | `refactor/rename-extra-name` | **Rename `group-name` to `extra-name` (F1).** `_DEFAULTS`, `_validate_config` and its messages, the attributes (`_group_name` -> `_extra_name`, `_group` -> `_extra`), the log messages, the `update` and class docstrings, the README (options table, option details, errors table, FAQ), `CLAUDE.md`, the tests. No other behaviour changes; the whole-output tests keep their literals. | yes      |
| 2    | `docs/properties-and-order`  | **Documentation (F2 to F5).** "Sorted as strings" in the README and in `update`; two new properties (idempotent on request, output-invariant) in the module docstring and the README table; the README imports from the package root; README **Features** reduced to what is not a property, "Regardless of the options" merged into **Properties**; class docstring points at the README for the warn-only paragraph. | no       |

The steps are independent; step 2 may be merged first. Step 1 checks that its renamed tests fail
without the `src` change (`git stash push src`): in particular `group-name` must be an unknown
option after the change.

## 8. Tests and gates

Conventions of `CLAUDE.md` apply: one behaviour per test, literal expected values, no local imports,
`match` on every `pytest.raises`, no logic in a test body.

**Unit (`tests/unit/test_hooks.py`)** keeps its 190 cases. The additions are:

- rename: `group-name` is an unknown option and the message lists `['exclude', 'extra-name',
  'overwrite']` (one test, `match` on the whole list); `extra-name` is validated like `group-name`
  was (the existing type and value tests, renamed); the default is `all`;
- sort order: `["sphinx>=5", "sphinx-rtd", "Zed", "alpha"]` gives `['Zed', 'alpha', 'sphinx-rtd',
  'sphinx>=5']` (pins F2 and the word of the docs; full literal);
- output invariance: the same metadata gives the same result in strict mode and in warn-only mode
  when the configuration is valid (the two modes share one parametrised literal), complementing the
  tests that exist for the two downgraded problems;
- the existing tests of `_dependencies`, `_normalize`, `_read_warn_only` stay as they are.

**Integration (`tests/integration/test_hooks.py`)**, real builds without patching: the option is
renamed in the projects (`extra-name`); one new build that uses the old option name fails with the
unknown-option message (the migration of F1 is an observable behaviour of a real build). Everything
else stays: whole-`METADATA` assertions, the matrix pin of hatchling, the `dynamic` failure, the
warn-only builds.

**Gates** before each merge: `ruff check`, `ruff format`, `ty check`, `pre-commit run --all-files`,
`.venv/bin/pytest tests` with 100 % coverage of the changed lines, `inv test.doctest-src`, and
`ci.yaml` green. The code of this change has no `# noqa` and no `# type: ignore`.

## 9. Decisions for the maintainers

**D1. Rename `group-name` to `extra-name`?** _Recommended: yes, now._ The package is `0.x`, the
README already warns that the API is not stable, and the hook is strict, so the migration is one
loud error. After 1.0 the same rename costs a deprecation period and an alias. The alternatives:
`name` (shorter, but ambiguous next to the project `name`), or keep `group-name` and rely on the
FAQ entry (the confusion with PEP 735 only grows as `[dependency-groups]` becomes common).

**D2. Keep the warn-only mode?** _Recommended: keep._ It is a documented property, decided in the
two previous reviews. Its cost is about 55 lines and 13 statements (`_WARN_ONLY_*`,
`_read_warn_only`, `_report`, the warn-only integration tests), and with the new property
(output-invariant) it cannot change what is built, only whether a typo stops the build. The person
who rebuilds a project is not its author. Removing it later is a breaking change; adding it back
is not.

**D3. Generate an empty extra when there is nothing to collect?** _Recommended: yes_ (today). A
stable `pkg[all]` never makes pip warn that the extra does not exist, and the output is a function of
the input only. The alternative (omit the extra) makes the metadata depend on whether other extras
exist and breaks `pip install pkg[all]` for a project whose last extra is removed.

**D4. Generate `all` as self-references (`pkg[dev,docs]`) instead of copied strings?**
_Recommended: no._ It would delete `_dependencies`, the dedup, the sort and the strip, but hatchling
1.18 keeps `pkg[dev,docs]` as is while 1.33 flattens it (previous review, verified), so the built
`METADATA` would differ by hatchling version, and the hook would need `metadata["name"]`. Reconsider
only if the supported range starts at the first hatchling that resolves self-references.

**D5. Repair ambiguous spellings (`All` and `all`) with `overwrite = true`?** _Recommended: no._
Hatchling rejects the project with a precise message; the hook replacing one spelling and leaving the
other is accidental (it depends on the order of the table) and a repair would hide the invalid input.
A hook-side error would only repeat hatchling's.

**D6. Where do the properties live?** _Recommended:_ the module docstring is the source, the README
table repeats it with the same names and statements, and `CLAUDE.md` says so (already in place). Step
2 removes the other restatements (Features, "Regardless of the options") so that a change of a
property is two edits instead of five. A test that compares the two texts is not worth its code.

**D7. Keep `__version__` public?** _Recommended: yes._ It is used by `tests/package_checks.py` and
`tests/unit/test_init.py`; the hook does not need it, which is the reason not to add anything else
to the root.

## 10. Not covered

- **New features.** No `include` option, no merge with the previous content of the generated extra,
  no several generated extras, no PEP 735 groups (the hook receives the `project` table, not
  `[dependency-groups]`), no parsing of requirements (`packaging` is not a dependency). Nothing new
  argues for them; each would break "minimal" and "the strings are copied, not interpreted".
- **`dynamic` support beyond what hatchling allows.** The hook cannot make a static table dynamic;
  a project that wants the hook needs a dynamic field (already documented in the README, with the
  behaviours verified in the previous review).
- **Hatchling >= 2.0 and Python < 3.11:** the supported ranges are unchanged; the matrix file
  `dev/config/package_versions.json` is generated, never edited by hand.
- **Order of metadata hooks.** Hatchling runs one metadata hook per project; the README sentence is
  already "not specified".
- **The test suite beyond what the two steps touch** (190 unit and 26 integration tests, about 1,500
  lines for 107 statements) and **CI, release and tooling** (`.github/`, `.make/`, `dev/`): out of
  scope.

## Appendix: effect on the size of the package

| File                       | Today                 | Target (estimate)     | Why                                                                                      |
| -------------------------- | --------------------- | --------------------- | ---------------------------------------------------------------------------------------- |
| `hooks.py` (statements)    | 107                   | 107                   | a rename, no new code                                                                    |
| `hooks.py` (lines)         | 414 (246 docstrings)  | ~400                  | the class docstring points at the README for the warn-only paragraph; two properties added |
| `README.md`                | 483 lines             | ~470                  | **Features** and "Regardless of the options" removed (merged into **Properties**), two properties added |
| `tests/unit/test_hooks.py` | 1,002 lines           | ~1,030                | three new tests (unknown `group-name`, sort order, output invariance); the rest is renamed |
| `tests/integration`        | 530 lines             | ~545                  | one new failing build (the old option name)                                              |

The package does not grow: the code is renamed, the text is shorter, and the two promises that were
true but unwritten (idempotent on request, output-invariant) become checked properties.
