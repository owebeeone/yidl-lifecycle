# AGENTS

## Scope

This file defines repository-level instructions for `yidl-lifecycle`.

## Developer Documentation

- Start with `dev-docs/README.md` for current policy references and pending work.
- Completed rollout plans and review evidence belong in `dev-docs/history/`.
  Preserve their verdicts/revisions; archiving does not certify implementation
  or cancel an unresolved obligation.

## Paths In Version Control

- Do not store absolute filesystem paths in committed files.
- Prefer paths relative to this repository root.
- When referencing neighboring local checkouts in docs or examples, use
  relative paths such as `../yidl` or `../astichi`.

## Test Coverage Shape

- Prefer golden, snapshot, or integration-style coverage for successful
  end-to-end lifecycle behavior.
- Keep bespoke unit tests focused on marker parsing, harvesting mechanics,
  edge-case failures, diagnostics, and narrow runtime behavior that goldens
  cannot express cleanly.
- Avoid duplicating the same success-path assertions in both bespoke tests and
  canonical output tests.

## Package Boundary

`yidl-lifecycle` owns lifecycle-specific decorator, marker, harvester,
transaction, binding, generated lifecycle, parity, and performance code.
Generic YIDL compiler behavior belongs in the `yidl` project.

<!-- gearu:agents:start -->
## Releases

- This repository uses [Gearu](https://owebeeone.github.io/gearu/) for release
  preparation.
- Read `RELEASE.md` before planning or performing a release.
- `gearu plan VERSION` and `gearu plan --bump LEVEL` are read-only. Do not run
  `gearu release`, push a release tag, or create a GitHub Release unless the
  user explicitly requests it.
- Never move or reuse a release tag. Correct released content with a new version.
- Never publish directly to PyPI, crates.io, or npm from a local checkout.
  Registry publication belongs in the repository's release workflow.
<!-- gearu:agents:end -->
