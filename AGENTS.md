# AGENTS

## Scope

This file defines repository-level instructions for `yidl-lifecycle`.

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

