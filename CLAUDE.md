# CLAUDE.md

Guidance for Claude Code when working in this repository.

## Project overview

`hatchling-autoextras-hook` is a Hatchling metadata hook plugin that automatically generates an
`all` extra (name configurable) from a project's optional dependencies.

- Source: `src/hatchling_autoextras_hook/` (`hooks.py` holds `AutoExtrasMetadataHook`, registered
  through the `hatch` entry point `autoextras`).
- Tests: `tests/unit/` (mirrors the source tree) and `tests/integration/` (builds real projects).
- Dev tooling: `dev/` (hatchling version matrix generation), `.github/` (workflows), `.make/`
  (shared Makefile includes), `tasks.py` + `invoke.yaml` (invoke tasks).
- Supported Python: >= 3.10. Supported hatchling: >= 1.18, < 2.0.

## Environment

- Use the binaries in `.venv` (`.venv/bin/python`, `.venv/bin/pytest`, `.venv/bin/ruff`,
  `.venv/bin/ty`). Install with `uv sync --group dev`.
- Lint and format before committing: `.venv/bin/ruff check --fix .`, `.venv/bin/ruff format .`,
  `.venv/bin/ty check`, or run `pre-commit run --all-files`.
- Fix issues rather than suppressing them with `# noqa` or `# type: ignore`. If a suppression is
  truly unavoidable, name the specific rule (bare `# noqa` is rejected by pre-commit) and explain why.
- If a test fails, check whether it already fails on `main` (e.g. with `git stash`) before blaming
  your change, and report pre-existing failures.

## Workflow

- One branch and one PR per logical change. Name branches `<type>/<short-description>` in
  kebab-case (e.g. `fix/exclude-validation`). Never commit directly to `main`.
- Use stacked PRs for changes that depend on each other.
- Write imperative commit and PR titles (e.g. "Add validation for exclude"), with no
  conventional-commit prefixes.
- Resolve conflicts by merging `origin/main` into the branch; do not rebase.
- Update any documentation that tracks the change (`README.md`, `dev/README.md`,
  `.github/GUIDELINES.md`).

## Code

- Match the style of the surrounding code. Line length is 100; docstrings use the Google style and
  are wrapped at 72 (enforced by `ruff` and `docformatter`).
- Every public class and function needs a docstring with `Args`, `Returns`, `Raises` as relevant,
  and a doctest-style example where useful (examples are run by `xdoctest`; use ` ```pycon `
  blocks closed with a blank line, as in `hooks.py`).
- Document constructor arguments in the class docstring or in `__init__` consistently with
  existing code; keep the documented configuration options in `AutoExtrasMetadataHook` in sync
  with `README.md` whenever options change.
- Add `from __future__ import annotations` to every module, keep `__all__` up to date, and fully
  annotate all code (checked by `ty`).
- Raise errors with a `msg` variable (`msg = "..."; raise ValueError(msg)`), per `EM`/`TRY` rules.
  Use `ValueError` for invalid values and `TypeError` for invalid types.
- New configuration options must be validated in `_validate_config`, given a default in
  `__init__`, and be keyword-style entries in the `pyproject.toml` hook table.
- Keep the dependency footprint minimal: the only runtime dependency is `hatchling`. Don't add
  runtime dependencies without a strong reason, and keep compatibility with the full supported
  hatchling range.
- Use `logging` (`logger.debug`) rather than `print`.

## Tests

- Test every function and method in the source, including private ones. Mirror the source tree
  in `tests/unit/` (`src/.../hooks.py` -> `tests/unit/test_hooks.py`).
- Put tests that build real projects with hatchling, or are slow, in `tests/integration/`.
- One behavior per test. Use `pytest.mark.parametrize` for input variations.
- Use `match=` on every `pytest.raises` and `pytest.warns`.
- Assert whole composite outputs (e.g. the full resulting `metadata` dict) against full literals,
  not only fragments.
- Cover typical, edge, boundary, error, parameter-interaction and side-effect cases (e.g. in-place
  mutation of `metadata`, deduplication, sorting, whitespace stripping, `exclude`, `overwrite`).
- Pair every test that patches or mocks something with an unpatched integration test.
- Keep coverage at 100% without `pragma: no cover`, and add a regression test for every bug fix.
- Run tests with `.venv/bin/pytest tests/unit` (fast) and `.venv/bin/pytest tests` (all).

## GitHub Actions

- Workflow files live flat in `.github/workflows/` and use the prefixes `ci-`, `lib-`, `nightly-`,
  `bot-`, `release-`, `security-`. See `.github/GUIDELINES.md` for the full conventions and keep
  it up to date when you change workflows.
- `ci.yaml` is the single entry point for PRs and pushes to `main`; job ids in it are load-bearing
  for branch protection.
- Set `permissions: {}` (or `contents: read`) at workflow level and grant extra permissions per
  job only.
- Add `timeout-minutes` to every job and `workflow_dispatch` to every workflow.
- Pin actions to commit SHAs with the `# ratchet:owner/repo@vX.Y.Z` comment (managed by
  `bot-pin-action.yaml`); never hand-pin without it.
- The hatchling version matrix comes from `dev/config/package_versions.json`, generated by
  `dev/generate_versions.py`; do not edit it by hand.
- Validate workflow changes with `actionlint` from `.github/workflows`.

## Releases

- Use immutable, exact version tags (e.g. `v0.1.3`). Do not create or move floating tags
  (`v0`, `latest`).
- The version lives only in `pyproject.toml`; the integration test project pins
  `hatchling-autoextras-hook>=<version>` and must be kept consistent when it is bumped.

## Reporting

- When finishing a task, state which tests, linters and type checks were run and which were not,
  and whether CI was awaited.
- Report any failures that also occur on `main`.
