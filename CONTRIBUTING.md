# Contributing

Thanks for helping improve te-drift-detector.

## Quick setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e ".[dev]"
```

## Before you open a PR

Run these checks locally:

```bash
ruff check src/ tests/
pytest -q
te-drift --help
```

## Pull request expectations

Please keep PRs:
- **Focused** (small, clear scope)
- **Tested** (add/update tests when behavior changes)
- **Documented** (update README/docs for user-visible changes)
- **Deterministic** (the detector is zero-LLM by design — changes must not add model calls or network access to the detection path)
