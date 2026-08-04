# Changelog

All notable changes to `te-drift-detector` will be documented here.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning: [SemVer](https://semver.org/).

## [0.1.1] — 2026-08-04

Release preparation for the first PyPI publication. This patch does not add
detector features or make an effectiveness claim.

### Changed
- Bounded the public, installed-package, and documentation claim surfaces to
  experimental lexical feature-delta telemetry. They now state that synthetic
  fixtures are implementation self-checks and that efficacy, calibration, and
  recovery benefit remain unestablished.
- Clarified the inspection use case, optional embedding-network behavior, and
  the distinction between raw heuristic crossings and safety findings.
- Made installation guidance accurate before and after the first PyPI
  publication.

### Added
- Claim-surface tests that prevent retired or unsupported product claims from
  being reintroduced.
- A tag-bound, trusted-publishing workflow that requires a tag matching the
  package version, builds distributions, and runs strict Twine validation before
  the PyPI job.

## [0.1.0] — 2026-07-06

Initial packaged source release. Packaged from an internal prototype into a standalone,
dependency-free tool.

### Added
- `te_drift` package (src layout): `state_fingerprint`, `drift_analyzer`,
  `detector`, `jsonl_adapter`.
- `te-drift` console entry point with `detect`, `session`, and `eval`
  subcommands.
- `te_drift.evals` subpackage: scaffold-corruption strategy generators
  (fact_injection, term_redefinition, bias_drift) and a harness that runs them
  through the detector. Dry-run by construction — no model calls, no network.
- Session JSONL adapter with `cumulative` and `sliding-window` modes.
- 41 tests, `ruff`-clean, MIT license, `CITATION.cff`, `llms.txt`, `AGENTS.md`.

### Changed
- Zero required runtime dependencies. Semantic embeddings (previously a hard
  `requests`/Ollama dependency) are now an opt-in enhancement via
  `TE_DRIFT_EMBED=1` over the standard library. Default drift is lexical and
  deterministic, so results no longer depend on whether a local service happens
  to be running.

### Fixed
- Import-time `NameError` in the detector (`Tuple` used but not imported).
