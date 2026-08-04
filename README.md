# te-drift-detector

[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![CI](https://github.com/hermes-labs-ai/te-drift-detector/actions/workflows/ci.yml/badge.svg)](https://github.com/hermes-labs-ai/te-drift-detector/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](pyproject.toml)

See how the language, assumptions, and task framing of an AI conversation
change as the session grows.

`te-drift-detector` provides experimental lexical feature-delta telemetry for
multi-turn text. It creates lightweight fingerprints, compares later
conversation state with an initial baseline, and surfaces raw deltas and
hand-set threshold crossings for human review.

It can flag some curated state shifts under user-adjustable rules. It does not
establish malicious drift, model compromise, calibrated confidence, or safety
severity. Detection efficacy, threshold calibration, and recovery benefit have
not been established.

- **Zero required dependencies.** The default path uses only the Python
  standard library.
- **Deterministic by default.** With optional embeddings disabled, the same
  input produces the same lexical measurements.
- **Small and readable.** Feature extraction, comparison, and threshold rules
  are a few hundred lines.

## The narrow use case

Long conversations can change in ways that are difficult to inspect turn by
turn. `te-drift-detector` provides experimental telemetry for that inspection:
it fingerprints supplied text, measures feature changes relative to a baseline,
and labels crossings of its hand-set rules. Those labels are prompts for human
investigation, not findings about intent, compromise, or safety.

No production effectiveness result or independently labeled evaluation ships
with this release. The bundled synthetic sequences exercise the implementation;
they are demo/self-check fixtures generated and scored by the same repository.

## Install

PyPI publication has not happened yet. Until the `v0.1.1` tag has published
successfully, install the current source from GitHub:

```bash
pip install git+https://github.com/hermes-labs-ai/te-drift-detector
```

After that tagged publication is available on PyPI, install the released
package instead:

```bash
pip install te-drift-detector==0.1.1
```

Or from source:

```bash
git clone https://github.com/hermes-labs-ai/te-drift-detector
cd te-drift-detector
pip install -e ".[dev]"
```

## Quick start

```bash
# Analyze a built-in synthetic conversation
te-drift detect --attack-type poisoning

# A built-in normal conversation for comparison
te-drift detect --attack-type normal

# Run the deterministic demo/self-check fixtures
te-drift eval
```

Analyze a supported session transcript (JSONL, one user or assistant record per
turn):

```json
{"type": "user", "message": {"role": "user", "content": "..."}, "timestamp": "2026-07-06T20:00:00Z"}
```

```bash
te-drift session --session-jsonl path/to/session.jsonl
# For long sessions, use a constant-cost sliding window:
te-drift session --session-jsonl path/to/session.jsonl --mode sliding-window --window-size 10
```

The JSONL adapter currently reads user and assistant records. To analyze other
state, normalize it explicitly and use the library interface below.

### As a library

```python
from te_drift import TEDriftDetector

turns = [
    ("system", "You are a careful assistant. Validate inputs; security matters."),
    ("system", "[STATE UPDATE] Security requirements changed."),
    ("user", "Summarize the current requirements."),
]
report = TEDriftDetector().run_conversation(turns)
print(report["threat_level"], report["anomalies_detected"])
```

`threat_level` and `confidence` are retained API field names. Their values are
uncalibrated heuristic tiers and rule scores; they are not safety severity or a
probability that a session is compromised. The tool does not establish
malicious drift.

## How it works

1. **Feature extraction.** Extract lightweight lexical features from cumulative
   context: facts, entities, sentiment, task framing, authority level, style
   register, negations, and vocabulary.
2. **Feature deltas.** Compare the current fingerprint with the first-turn
   baseline. The field named `velocity_drift` is the absolute change in the
   scalar baseline-distance value since the previous reading; it is not a
   direct previous-fingerprint distance.
3. **Heuristic crossings.** Mark a reading when a hand-set absolute-delta,
   radial-change, component, or lexical-signature rule crosses its threshold.
4. **Legacy output tiers.** Summarize recent crossings as `NORMAL`, `LOW`,
   `MEDIUM`, `HIGH`, or `CRITICAL`. These uncalibrated heuristic tiers are not
   safety severity.

The default comparison uses set overlap and stays in-process. Optional semantic
embeddings are available with `TE_DRIFT_EMBED=1`:

```bash
TE_DRIFT_EMBED=1 te-drift session --session-jsonl path/to/session.jsonl
```

That setting can make an optional configured network call to
`TE_DRIFT_OLLAMA_URL` (default: `http://localhost:11434/api/embeddings`) and send
the analyzed text to that endpoint. If the endpoint is unavailable, errors, or
returns no vector, the implementation silently falls back to lexical set
overlap. Reports do not currently expose whether that fallback happened, and
embedding quality has not been evaluated. Do not enable it for sensitive text
without reviewing and trusting the configured endpoint.

## Optional companion workflow

[hermes-blind](https://github.com/hermes-labs-ai/hermes-blind) is a separate
recovery scaffold. You may inspect this package's telemetry before and after a
recovery experiment, but the repositories do not establish that the telemetry
identifies when recovery is needed or that either component improves outcomes.

## Demo/self-check fixtures

`te_drift.evals` generates three synthetic state-change sequences and feeds them
through the package. This checks deterministic wiring and makes example output
easy to inspect. Because the same repository authors both the generators and
the rules, these results are not evidence of detection rates, false-positive
rates, or generalization.

```bash
te-drift eval
te-drift eval --strategy bias_drift --turns 6
te-drift eval --json
```

The default lexical run crosses at least one heuristic rule for each bundled
sequence. Treat that as a self-check only, not an efficacy result.

## Limits

- The feature set is lexical, heuristic, and English-oriented by default.
- Meaning-preserving changes can produce small deltas; harmless wording changes
  can produce large ones.
- Thresholds and the fields named `confidence` and `threat_level` are
  uncalibrated. They do not establish malicious drift and are not safety
  severity.
- The session adapter observes user and assistant transcript records, not a
  general system/scaffold state schema.
- Optional embeddings can transmit text through a configured endpoint and
  silently fall back without reporting the active comparison mode.

## Development

```bash
pip install -e ".[dev]"
pytest
ruff check src tests
```

## License

MIT. See [LICENSE](LICENSE).

## About Hermes Labs

Hermes Labs builds tools for inspecting AI-system behavior. In this repository,
the supported description is experimental lexical feature-delta telemetry; no
claim of calibrated safety detection or production effectiveness is implied.
