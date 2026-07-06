# AGENTS.md — te-drift-detector

Guidance for autonomous agents and LLM tooling that consume, extend, or
integrate this package.

## What this is

A small standard-library tool that detects cross-turn drift in an agent
session's working state. It fingerprints each turn, measures drift from a
baseline and turn-to-turn velocity, and flags sustained corruption that a
per-turn filter would miss. It is not a model, an API, or a judge.

## What this is not

- Not a per-turn jailbreak classifier — it is complementary to one, not a
  substitute.
- Not a guaranteed detector. Thresholds are conservative defaults; calibrate per
  deployment.
- Not semantic by default. Drift is lexical (set overlap) unless you opt into
  embeddings with `TE_DRIFT_EMBED=1`.

## When to invoke

Use it when an agent runs multi-turn and its working state (system scaffold,
running summary, injected context) could be nudged over time — session
monitoring, post-hoc transcript audits, or a SessionEnd hook.

Skip it for single-turn classification, or when you need meaning-preserving
corruption caught (lexical drift can miss synonym-level rewrites).

## Minimal invocation

```python
from te_drift import TEDriftDetector

turns = [(role, text), ...]              # role in {system, user, assistant}
report = TEDriftDetector().run_conversation(turns)

if report["threat_level"] in ("HIGH", "CRITICAL"):
    ...  # escalate, or inject a recovery scaffold (see hermes-blind)
```

Session transcript (JSONL):

```python
from te_drift import load_turns, run_drift_analysis

turns = load_turns("session.jsonl")               # (role, text, timestamp) tuples
report = run_drift_analysis(turns, mode="sliding-window", window_size=10)
```

## Expected output shape

`summary_report()` / `run_conversation()` return a dict with:

- `total_turns`, `anomalies_detected`, `threat_level`, `sustained_anomaly`
- `avg_absolute_drift`, `max_absolute_drift`
- `readings`: per-turn `{turn, absolute_drift, velocity_drift, is_anomaly,
  anomaly_reason, confidence, components}`

## Thresholds (defaults, tunable via class attributes on `DriftAnalyzer`)

- `ABSOLUTE_DRIFT_THRESHOLD = 0.50`
- `VELOCITY_DRIFT_THRESHOLD = 0.30`
- `CONSECUTIVE_ANOMALY_THRESHOLD = 3`
- `CRITICAL_COMPONENTS` — per-component thresholds

## Eval harness

`te_drift.evals` generates scaffold-corruption sequences (fact_injection,
term_redefinition, bias_drift) and runs them through the detector. Dry-run by
construction — no model calls, no network.

```python
from te_drift.evals import run_all
results = run_all(num_turns=5)
```

## Detect, then recover

This is the detect half. The recover half is
[hermes-blind](https://github.com/hermes-labs-ai/hermes-blind): a recovery
scaffold injected mid-conversation to pull a drifting session back toward
baseline. Loop: monitor drift here, inject recovery there, confirm the
trajectory bends back.

## Success signal

- `pytest` returns 0 across 41 tests, no skips.
- `ruff check src tests` is clean.
- `te-drift eval` flags corruption in all three strategies.

## Extension points

- New features: add an extractor in `state_fingerprint.py`, a comparison method,
  wire it into `composite_drift()`, and add a weight in `DriftAnalyzer`.
- New attack signatures: extend `_detect_attack_pattern` in `drift_analyzer.py`.
- New eval strategies: add a strategy class in `te_drift/evals/strategies.py`
  and register it in `generate_attack_sequence`.

Do not add runtime dependencies. The standard-library-only guarantee is part of
the tool's shape; embeddings stay an opt-in enhancement, never required.
