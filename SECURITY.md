# Security Policy

## Reporting

If you find a security issue, please email **roli@hermes-labs.ai** rather than
opening a public issue. Include steps to reproduce and, if relevant, the session
data shape that triggers it (never real session content containing secrets).

You will get an acknowledgement within a few days.

## Scope notes

- The detector reads session text you feed it; it makes no network calls and
  runs no model. Anything that would change that is a security-relevant change.
- Do not paste secrets, API keys, or sensitive session logs into issues or PRs.
