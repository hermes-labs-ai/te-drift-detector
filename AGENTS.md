# AGENTS.md — te-drift-detector

Guidance for autonomous agents and LLM tooling that consume, extend, or
integrate this package.

## What this is

Experimental lexical feature-delta telemetry for multi-turn text. It extracts
features from supplied text, measures baseline-relative changes, and reports
hand-set threshold crossings for human inspection. It is not a model, API, or
judge.

The package does not establish malicious drift, model compromise, calibrated
confidence, or safety severity. Detection efficacy, threshold calibration, and
recovery benefit remain unproved.

## Appropriate use

Use the tool for exploratory inspection, local debugging, or for generating raw
measurements that a human will review. Do not use a crossing as an autonomous
security decision, a reason to block a user, or proof that a session was
compromised.

The direct library interface accepts caller-supplied `(role, text)` tuples. The
JSONL adapter observes user and assistant records; it does not currently model a
general system/scaffold state schema.

## Minimal invocation

```python
from te_drift import TEDriftDetector

turns = [(role, text), ...]
report = TEDriftDetector().run_conversation(turns)
inspect(report["readings"])
```

Session transcript (JSONL):

```python
from te_drift import load_turns, run_drift_analysis

turns = load_turns("session.jsonl")
report = run_drift_analysis(turns, mode="sliding-window", window_size=10)
```

## Output interpretation

`summary_report()` and `run_conversation()` return raw feature deltas plus
legacy fields named `confidence` and `threat_level`. Those fields are
uncalibrated rule scores and heuristic tiers; they are not safety severity or a
probability of compromise. The field named `velocity_drift` measures change in
the scalar baseline-distance value, not direct previous-fingerprint distance.

## Network and sensitive-input boundary

The default lexical path stays in-process. `TE_DRIFT_EMBED=1` can make an
optional configured network call to `TE_DRIFT_OLLAMA_URL` and transmit analyzed
text. If the endpoint is unavailable, errors, or returns no vector, the current
implementation silently falls back to lexical set overlap and does not expose
that fallback in its report. Embedding quality is unevaluated.

Do not enable optional networking for sensitive material without reviewing and
trusting the configured endpoint. Do not place private transcripts in tests,
issues, or commits.

## Demo/self-check fixtures

`te_drift.evals` generates three synthetic sequences and runs them through the
same repository's rules. These fixtures exercise deterministic wiring only.
They do not estimate false-positive rates, false-negative rates, effectiveness,
or generalization.

```python
from te_drift.evals import run_all

results = run_all(num_turns=5)
```

## Development signal

- The full test suite returns zero.
- `ruff check src tests` is clean.
- An sdist and wheel build and the installed CLI runs its documented commands.

Do not convert a green self-check into a claim of detection quality. Preserve
the name, public API, algorithms, and thresholds unless a separately authorized
change explicitly covers them.

## Extension points

- New lexical features live in `state_fingerprint.py`.
- Comparison and threshold rules live in `drift_analyzer.py`.
- Synthetic sequence generators live in `te_drift/evals/strategies.py`.

Do not add required runtime dependencies. Optional embeddings remain explicitly
configured and must retain the network and fallback disclosures above.
