# Security Policy

## Reporting

If you find a security issue, please email **roli@hermes-labs.ai** rather than
opening a public issue. Include steps to reproduce and, if relevant, the session
data shape that triggers it (never real session content containing secrets).

You will get an acknowledgement within a few days.

## Scope notes

- The package reads the session text you supply. Its default lexical path stays
  in-process and runs no model.
- Setting `TE_DRIFT_EMBED=1` can make an optional configured network call to
  `TE_DRIFT_OLLAMA_URL` (default: a loopback Ollama URL) and transmit analyzed
  text to that endpoint. Review and trust the configured endpoint before using
  this mode with sensitive material.
- If the embedding endpoint is unavailable, errors, or returns no vector, the
  current implementation silently falls back to lexical set overlap. Reports do
  not expose whether that fallback occurred.
- Do not paste secrets, API keys, or sensitive session logs into issues or PRs.
