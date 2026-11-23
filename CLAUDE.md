# Instructions for coding agents

Guidance for Claude Code and other coding agents working in this repository.

## Project overview

`hatchling-autoextras-hook` is a Hatchling metadata hook plugin that automatically generates an
`all` extra (name configurable) from a project's optional dependencies.

- Source: `src/hatchling_autoextras_hook/` (`hooks.py` holds `AutoExtrasMetadataHook`, registered
  through the `hatch` entry point `autoextras`).
- Tests: `tests/unit/` (mirrors the source tree) and `tests/integration/` (builds real projects).
- Dev tooling: `dev/` (hatchling version matrix generation), `.github/` (workflows), `.make/`
  (shared Makefile includes), `tasks.py` + `invoke.yaml` (invoke tasks).
- Supported Python: >= 3.11. Supported hatchling: >= 1.18, < 2.0.

## Environment

- Use the binaries in `.venv` (`.venv/bin/python`, `.venv/bin/pytest`, `.venv/bin/ruff`,
  `.venv/bin/ty`). Install with `uv sync --group dev`.
- Lint and format before committing: `.venv/bin/ruff check --fix .`, `.venv/bin/ruff format .`,
  `.venv/bin/ty check`, or run `pre-commit run --all-files`.
- Fix issues rather than suppressing them with `# noqa` or `# type: ignore`. If a suppression is
  truly unavoidable, name the specific rule (bare `# noqa` is rejected by pre-commit) and explain why.
- If a test fails, check whether it already fails on `main` (e.g. with `git stash`) before blaming
  your change, and report pre-existing failures.
- There is no `python` on the `PATH`; use the virtual environment. Prefer the `inv` tasks
  (`.venv/bin/inv --list`) provided by `invoke-tasklib`, e.g. `inv test.unit`, `inv format.fix-python`,
  `inv lint.check-python`, `inv types.check`, `inv test.doctest-src`.

## Workflow

- One branch and one pull request per logical change (one feature, one bug fix, one refactor).
  Branch from an up to date `main`.
- Name the branch `<type>/<short-description>` in lowercase kebab-case, for example
  `feat/add-cache-option` or `bugfix/handle-empty-input`. Use one of these types:
  `feat` (new feature), `bugfix` (bug fix), `hotfix` (urgent fix), `docs` (documentation),
  `refactor` (no behaviour change), `perf` (performance), `test` (tests only),
  `chore` (maintenance, dependencies, tooling), `ci` (CI configuration).
- Do not commit or push to `main`.
- When working on several sequential PRs where one depends on the previous one, use stacked PRs:
  branch each PR from the branch of the previous one (not from `main`) and open it with the
  previous branch as its base. Keep each PR small and reviewable on its own. Once a PR of the stack
  is merged, retarget the next PR to `main` and merge `origin/main` into it.
- Write commit messages and PR titles as a short imperative sentence starting with a verb such as
  `Add`, `Fix`, `Update`, `Remove` or `Improve`. Do not use conventional-commit prefixes like
  `docs:` or `feat:` (the type prefix is only for branch names). The squash-merge appends the PR
  number, so do not add one.
- In the PR description, say what was changed, what was deliberately not changed, and any
  behaviour change (for example a changed output, or a breaking change of the signature).
- Do not escape special characters such as the backtick in the PR title or description
  (no backslash before it): the backslash is not rendered well. Write the characters as is.
- When a PR conflicts with `main`, merge `origin/main` into the branch and resolve the conflicts
  (do not rebase and force-push). Most conflicts are two PRs appending tests at the end of the
  same test file: keep both. Check what `main` already contains before choosing a side.
- Update any documentation that tracks the change (`README.md`, `dev/README.md`,
  `.github/GUIDELINES.md`, `.github/CONTRIBUTING.md`).

## Code

- Match the style of the surrounding code: comment density, naming, docstring style. Line length
  is 100; docstrings use the Google style and are wrapped at 72 (enforced by `ruff` and
  `docformatter`).
- Follow the current style of the repository in everything you add (source, tests, docs, commit
  messages, PR descriptions). Look at a few neighbouring files first, and do not introduce a new
  convention or reformat code you do not otherwise change.
- Every function and method, public or private (leading underscore), needs a docstring with `Args`,
  `Returns`, `Raises` as relevant, and a doctest-style example where useful (examples are run by
  `xdoctest`; use ` ```pycon ` blocks closed with a blank line, as in `hooks.py`).
- Document constructor arguments in the class docstring or in `__init__` consistently with
  existing code; keep the documented configuration options in `AutoExtrasMetadataHook` in sync
  with `README.md` whenever options change.
- Add `from __future__ import annotations` to every module, keep `__all__` up to date, and fully
  annotate all code (checked by `ty`).
- Raise errors with a `msg` variable (`msg = "..."; raise ValueError(msg)`), per `EM`/`TRY` rules.
  Use `ValueError` for invalid values and `TypeError` for invalid types.
- Keep new options keyword-only (`*`) when they are added to a function signature.
- The module docstring of `hooks.py` is the source of the list of properties. The **Properties**
  table of `README.md` repeats it with the same names and the same statements: update both together.
- Keep docstrings and documentation up to date and comprehensive: update them whenever the
  behaviour, signature or options of the code change.
- New configuration options must be validated in `_validate_config`, given a default in
  `__init__`, and be keyword-style entries in the `pyproject.toml` hook table.
- Keep the dependency footprint minimal: the only runtime dependency is `hatchling`. Don't add
  runtime dependencies without a strong reason, and keep compatibility with the full supported
  hatchling range.
- Use `logging` (`logger.debug`) rather than `print`.

## Tests

- Always write tests for the code in `src/`, including every private function. Unit tests must be
  fast and efficient; move big or slow tests to `tests/integration/`.
- Unit tests mirror the source tree (`src/.../hooks.py` -> `tests/unit/test_hooks.py`). Tests that
  build real projects with hatchling, or are slow, go in `tests/integration/`.
- Do not use local imports inside tests. Import at the top of the module (under `TYPE_CHECKING`
  when only needed for annotations).
- One behaviour per test: a test has one `assert` or one `pytest.raises`. Split a test that checks
  several things into several tests.
- A test may combine `pytest.raises` (or `pytest.warns`) with an `assert` that checks the state
  after the error (for example that `metadata` was not mutated). This is one behaviour: the call
  fails and leaves the state unchanged.

  ```python
  with pytest.raises(ValueError, match=r"already exists"):
      hook.update(metadata)
  assert metadata == {...}
  ```

- Do not use `contextlib.suppress` in place of `pytest.raises` to swallow an expected exception:
  it passes when no exception is raised, so the test does not prove the error happens.
- Section headers in the tests have three lines. The second line is `#`, 5 spaces, the name,
  5 spaces and `#`. The first and third lines repeat `#` to match the length of the second line:

  ```python
  ###########################
  #     Tests for Fixed     #
  ###########################
  ```

- Keep the unit tests simple and fast: no sleeps, no large data, no real network or heavy I/O,
  and no logic (loops, branches) in the test body. Anything slow belongs in `tests/integration/`.
- Use `pytest.mark.parametrize` for the same check on several values.
- Every `pytest.raises` (and `pytest.warns`) must define `match` with a regular expression for the
  message (raw string if it has metacharacters), so a test does not pass on an unrelated error of
  the same type. An exception raised by a patched stand-in needs an explicit message for the same
  reason (`side_effect=KeyboardInterrupt("interrupted")`, not `side_effect=KeyboardInterrupt`).
- Add the missing tests to get 100% coverage of the code you add or change
  (`.venv/bin/pytest tests --cov=hatchling_autoextras_hook --cov-report=term-missing`). Do not use
  `# pragma: no cover` to skip a line that can be tested.
- Add a regression test for every bug fixed, and check that it fails without the fix (revert the
  `src` change with `git stash push src` and run it).
- Do not add tests for the exports of `__all__` or other trivial structure.
- Seed random data; no unseeded randomness in tests.
- Patching (`monkeypatch`, `unittest.mock.patch`) is fine in unit tests: it keeps them fast and
  simple and isolates the logic under test. But a patched test only proves the logic works against
  the patched stand-in, which may not match the real collaborator (signature, return type,
  behaviour). Every patched behaviour needs an integration test in `tests/integration/` that
  exercises the real thing without patching. The two kinds of test have different purposes; do not
  drop one because the other exists.
- Run tests with `.venv/bin/pytest tests/unit` (fast) and `.venv/bin/pytest tests` (all).

### Test assertions

- When asserting an expected value, write the final computed value, not the expression that
  produces it. If the derivation is not obvious, keep the expression as a comment above the
  assertion.
- When a function returns a composite value (a dict, a list, ...), include at least one test that
  asserts the entire output against a fully-specified literal (for example the full resulting
  `metadata` dict), not only individual keys or fields. This catches unexpected extra or missing
  entries that per-field assertions miss:

  ```python
  hook.update(metadata)
  assert metadata == {...}
  ```

### Test coverage

When implementing or modifying a function, write comprehensive unit tests, not just a happy-path
check. Cover, where applicable:

- Typical inputs.
- Edge cases: empty inputs, single-element inputs, duplicate inputs.
- Boundary values (empty string, whitespace-only string, empty list).
- Error conditions: inputs that should raise, with the right exception type and message.
- Interactions between parameters (for example `exclude` with `overwrite`, or a custom
  `group-name` with `exclude`), and the order of output entries.
- Side effects: in-place mutation of `metadata`, deduplication, sorting, whitespace stripping, and
  determinism across repeated calls.

Prefer many small, precisely named tests (one behaviour per test) over a few broad ones, so a
failure points at the specific behaviour that broke.

## GitHub Actions workflows

The workflows are in `.github/workflows/`; the composite actions are in `.github/actions/`.
`.github/GUIDELINES.md` has the full table of workflows, triggers and conventions: read it and keep
it up to date when you add, rename or remove a workflow.

- The file name starts with a prefix that gives the role of the workflow:
  - `ci-`: quality and test checks of the repository source. Most are reusable workflows
    (`workflow_call`, plus `workflow_dispatch` to run one alone) called from `ci.yaml`.
    `ci-verify-workflows.yaml` (every PR) is standalone and not called from `ci.yaml`.
  - `lib-`: reusable helpers that compute an output for other workflows (test matrix, package
    metadata, dependency versions).
  - `nightly-`: scheduled tests of the _published_ PyPI package, not of the source.
    `nightly-package.yaml` is the entry point; the other `nightly-test-*` are called by it.
  - `bot-`: scheduled automation that opens pull requests (dependency updates, pinning
    actions, formatting, ...) with the `ci-bot` GitHub App token.
  - `release-`: publishing to PyPI, triggered by version tags (`v*.*.*`) or manually; it runs
    `ci.yaml` before publishing.
  - `security-`: dependency review of PRs, scheduled dependency audit and scorecard.
- `ci.yaml` is the single entry point of the checks (pull request, push to `main`, nightly).
  It calls `lib-get-test-matrix.yaml` once and passes the matrix (`test-matrix` input) to the
  test workflows, so the Python versions and OS are defined in one place (they come from
  `durandtibo/workflow-config-action`). The package name, version and extras come from
  `lib-get-package-metadata.yaml` (`durandtibo/extract-pyproject-metadata-action`); do not
  hardcode the package name in a workflow. To add a check, create a `ci-<name>.yaml` reusable
  workflow and add a job in `ci.yaml`.
- Conventions: a header comment that says what the workflow does and when it runs; `permissions: {}`
  at the workflow level and the minimum permissions per job; `timeout-minutes` on every job;
  `workflow_dispatch` on every workflow; actions pinned to a commit SHA with a
  `# ratchet:owner/repo@vX.Y.Z` comment (`bot-pin-action.yaml` maintains them; never hand-pin
  without it).
- Set `permissions` on every job (including jobs that call a reusable workflow). Every workflow
  has `permissions: {}` at the workflow level (it grants nothing), never a grant.
- The hatchling version matrix comes from `dev/config/package_versions.json`, generated by
  `dev/generate_versions.py`; do not edit it by hand.
- `ci-verify-workflows.yaml` lints the workflows: validate your changes with `actionlint` (run
  from the repository root, or from `.github/workflows`) when available.

## Releases

- Releases are immutable exact version tags (e.g. `v0.1.3`). Do not create or move floating tags
  (`v0`, `latest`) and do not document them as an option.
- The version lives only in `pyproject.toml`. The integration test project installs the hook from
  the working tree through a `file://` URI (no version to keep consistent) and pins
  `hatchling==<version of the test environment>`, so the hatchling matrix of the CI builds real
  projects.

## Reporting

- Report faithfully: when finishing a task, state which tests, linters and type checks were run and
  which were not, and whether CI was awaited.
- Mention test failures that already exist on `main` instead of hiding them.
