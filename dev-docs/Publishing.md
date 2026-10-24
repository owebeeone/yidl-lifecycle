# Lifecycle release preparation and publication

## Scope and publisher identity

The operator authorized release setup in Lifecycle, Cache and YIDL and selected
LGPL-2.1 for all three. Lifecycle changes cover packaging metadata, license,
GEARU configuration, publishing guidance/workflow and the two canonical output
files that needed alignment with published Astichi 1.1.3. Runtime/compiler
implementation, Astichi, GEARU's implementation and GWZ configuration remain
unchanged. No commit, push, tag, GitHub release or package upload is performed
by this setup task.

The pending publisher identifies `owebeeone/yidl-lifecycle`, workflow
`publish.yml`, environment `Any`. The upload job uses official PyPA OIDC
publishing with job-local `id-token: write`, no secret token and no environment
requirement. Astichi's separate `pypi` environment remains unchanged.

## Preparation and artifact flow

Metadata declares the exact tested first-release closure: Astichi 1.1.3,
YIDL 0.1.0, Cache 0.1.0 and compat-sentinel 0.1.2. Both artifacts carry the README
and SPDX `LGPL-2.1-only` license metadata/text. Source and issue URLs are declared.

`gearu.toml`, `.release.env` and `RELEASE.md` configure preparation, source tests
on Python 3.12–3.14, wheel-from-sdist build and strict Twine validation. Checks
install the candidate and ignore sibling source overrides. Lock refresh uses
`--no-sources`, so release worktrees require public upstream packages rather
than adjacent development checkouts. Release resolution permits newly published
YIDL/Cache via package-specific zero-age cutoffs; the existing one-week age
policy still applies to other dependencies. This avoids an unintended one-week
wait between the ordered releases. The CLI accepts these overrides; the current
registry-only dry run correctly stops because YIDL is not published yet. Config loading is verified. A full
`gearu plan 0.1.0` requires a clean committed checkout and has not been run
against this uncommitted setup.

Manual workflow runs verify without uploading. A published GitHub release checks
out its exact tag and uploads only after all gates pass. Tags must be `v` plus
the metadata version. Each artifact is installed independently outside the
checkout using only registry dependencies. An installed probe decorates a class
with a mutable lazy integer field, verifies initial and reassigned values and
checks live constructor annotation identity. The Python backend is explicit;
only the installed smoke probes disable persistent caching. A separate Ubuntu
matrix runs the full repository suite on CPython 3.12, 3.13 and 3.14.

The upload job downloads the verified artifacts without rebuilding. Actions are
pinned to upstream commits, publication is restricted to this repository's
release events and concurrency does not cancel an active upload. The workflow
creates no tag or release and does not silently skip existing PyPI versions.

## Local verification and remaining order requirement

Preparation date: 2026-10-25. Source baseline:
`e979f2412b809e2a8a60eefb942790cef1e715ff` plus this uncommitted setup.
Local matrix: macOS arm64, CPython 3.12.12, 3.13.12 and 3.14.3,
`ASTICHI_LOWER_ENGINE=python`, published Astichi 1.1.3, Black 26.3.1 and
pytest 8.4.2. All local new-package candidates are 0.1.0.

- Wheel and sdist build and pass strict Twine checks; metadata, license and
  contents are inspected. Installed probes pass with the local YIDL/Cache
  candidate wheels and published Astichi, without sibling source paths.
- An ordinary registry-only install cannot yet resolve the new upstream
  packages. YIDL and Cache's PyPI project endpoints returned 404 during initial
  setup. This is an expected publication-order prerequisite, not an OIDC defect.
  The workflow keeps registry-only installation as a required gate.
- Initial full-suite runs passed 461 tests with 46 skips and one golden mismatch
  on every interpreter. Only the owned-fields fixture differed: Astichi 1.1.3
  gives repeated local temporaries distinct scoped names. All interpreter
  outputs agree, the fixture's execution/assertions pass, and normalizing only
  those names yields the same AST (with formatter wrapping in the prettier
  variant). Its two output files were refreshed for the declared SDK; no runtime
  code or comparison harness was changed. After the refresh, each interpreter
  passes 462 tests with 46 skips. Logs are ignored
  `build/release-tests-<python>.log` files.
- The 46 existing skips are 45 deferred/rejected historical Pyrolyze parity
  cases and one opt-in constructor throughput comparison (`YIDL_PERF_TESTS=1`).
  No new skip was introduced to accept the release candidate.
- YIDL's separate downstream Lifecycle smoke passes on all three interpreters
  against these candidate wheels. Workflow syntax and positive/negative version
  checks are verified locally. No hosted Actions run or OIDC exchange is claimed.

Commit and review the setup, then publish Cache 0.1.0 followed by YIDL 0.1.0.
Confirm each publication and fresh registry-only install before running
Lifecycle's build-only hosted check and authorized release. Local candidate
integration does not substitute for that registry-only gate or qualify native
backends/new platforms. See `RELEASE.md` for GEARU operations and support limits.

## Sentinel dependency follow-up

The operator separately requested replacing Lifecycle's use of YIDL's sentinel
helper with the published compat-sentinel 0.1.2 release. This follow-up changes
Lifecycle marker construction, its declared dependency/lock and focused
identity tests, plus this documentation. YIDL, Astichi, Cache and compat-sentinel
implementation remain reference-only. The prior evidence above describes the
pre-migration candidate; verification of the sentinel migration is separate.

Lifecycle owns `MISSING` and `_HAS_DEFAULT_FACTORY` as module-level sentinel
instances. The factory marker is registered under its actual private global
name for pickle lookup and retains `HAS_DEFAULT_FACTORY` as its displayed name.
Copying and pickling preserve identity, and existing public re-exports still
refer to those same instances. These are Lifecycle markers, not aliases of
YIDL's helper registry.

The sentinel migration passes the full Lifecycle suite on CPython 3.12.12,
3.13.12 and 3.14.3 with the explicit Python backend: 464 passed and 46 existing
skips on each. Fresh wheel and sdist installations obtain compat-sentinel from
PyPI; marker identity survives copying and pickling, including restoration in
a fresh process. Strict Twine validation passes both artifacts.

Before Pyrolyze's own separately authorized sentinel migration, its Lifecycle
integration and legacy lifecycle/freezable checks passed 434 tests on CPython
3.12.12 against this Lifecycle candidate and published Astichi. Pyrolyze source
was pinned to `092d055294df97666bee473126708c2868379c2d` for that consumer check.
The subsequent Pyrolyze migration has its own regression checks; this result
does not certify those later source edits.

## User-documentation follow-up

The operator authorized installation and first-transaction guidance, a field/hook
reference, public cache troubleshooting and separation of proposed APIs. These
pages are linked from the README and included with public docs/images in the
sdist. The existing transaction-guide filename remains stable for incoming
links; its heading and completion-failure explanation describe the current API.
The tutorial and existing transaction/custom-key/aggregate examples execute
against the installed candidate. Local links and headings are checked. A human
reading-path self-review follows install, first result and goal-specific links;
this does not claim independent release acceptance.
