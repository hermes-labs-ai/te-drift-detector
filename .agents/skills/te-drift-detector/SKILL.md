---
name: te-drift-detector
description: Use when a human wants experimental lexical telemetry on how the language, assumptions, and task framing of a long AI conversation changed since the first turn — it fingerprints text, compares later state against a baseline, and flags hand-set threshold crossings for review. It does not establish malicious drift, compromise, or safety severity; treat findings as prompts for human investigation only.
license: MIT
compatibility: Requires Python 3.10+; installs via pip. Default lexical path has zero required dependencies and makes no network call; optional embeddings mode needs a local Ollama endpoint.
---

# te-drift-detector

te-drift-detector provides experimental lexical feature-delta telemetry for
multi-turn text. It fingerprints conversation state, compares later turns
against an initial baseline, and surfaces raw deltas plus hand-set threshold
crossings — labels meant to prompt human investigation, not findings about
intent, compromise, or safety severity.

## Use it for

- Getting a quick lexical read on whether a long conversation's language,
  entities, sentiment, or task framing shifted since its first turn
- Analyzing a supported session transcript (JSONL, one user/assistant record
  per turn) for hand-set threshold crossings
- Running the deterministic self-check fixtures to confirm the tool is wired
  correctly

## Do not use it for

- Establishing malicious drift, model compromise, or a calibrated confidence
  score — `threat_level` and `confidence` are uncalibrated heuristic tiers,
  not safety severity
- A production effectiveness claim — no independently labeled evaluation
  ships with this release; the bundled fixtures are self-generated demo data
- Sensitive text with `TE_DRIFT_EMBED=1` enabled without first reviewing and
  trusting the configured Ollama endpoint, since that mode can send analyzed
  text off-process

## Quickstart

```bash
pip install te-drift-detector==0.1.1
te-drift detect --attack-type poisoning
te-drift detect --attack-type normal
te-drift eval
```

Analyze a real session transcript:

```bash
te-drift session --session-jsonl path/to/session.jsonl
# For long sessions, use a constant-cost sliding window:
te-drift session --session-jsonl path/to/session.jsonl --mode sliding-window --window-size 10
```

## Output shape

- `te-drift detect` / `te-drift session`: a report with `threat_level`
  (`NORMAL`/`LOW`/`MEDIUM`/`HIGH`/`CRITICAL`), `anomalies_detected`, and
  per-feature deltas including `velocity_drift`
- `te-drift eval` / `te-drift eval --json`: runs the bundled synthetic
  self-check sequences and reports whether each crosses at least one rule

## Common gotchas

- These are uncalibrated heuristic tiers by the tool's own documentation —
  report them to a human as "flagged for review," never as a verified
  safety finding.
- The JSONL session adapter reads user and assistant records only; other
  state needs the library interface (`TEDriftDetector().run_conversation`).
- Optional embeddings (`TE_DRIFT_EMBED=1`) silently fall back to lexical set
  overlap if the configured endpoint is unavailable, and the report does not
  expose whether that fallback happened.

## More

Full docs and CLI reference:
https://github.com/hermes-labs-ai/te-drift-detector
