"""Keep public claim surfaces aligned with the package's demonstrated scope."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLAIM_SURFACES = (
    "README.md",
    "llms.txt",
    "AGENTS.md",
    "CITATION.cff",
    "SECURITY.md",
    "pyproject.toml",
)


def _text(name: str) -> str:
    return (ROOT / name).read_text(encoding="utf-8").lower()


def test_retired_denominator_and_unsupported_claims_are_absent() -> None:
    combined = "\n".join(_text(name) for name in CLAIM_SURFACES)
    forbidden = {
        "retired denominator": r"\bn\s*=\s*74\b",
        "categorical gradual detection": r"\b(?:catches?|detects?)\s+(?:the\s+)?gradual\b",
        "self-described benchmark": r"\bbenchmark\b",
        "deployment calibration implication": r"\bcalibrat(?:e|ed)\s+per\s+deployment\b",
        "unevaluated embedding fidelity": r"\bembeddings?\s+raise\s+fidelity\b",
        "unconditional no-network promise": r"\b(?:makes?\s+)?no\s+network\s+(?:calls?|is\s+touched)\b",
    }
    for label, pattern in forbidden.items():
        assert re.search(pattern, combined) is None, label


def test_primary_claim_surfaces_use_the_bounded_product_definition() -> None:
    for name in ("README.md", "llms.txt", "AGENTS.md", "CITATION.cff", "pyproject.toml"):
        assert "experimental lexical feature-delta telemetry" in _text(name), name


def test_heuristic_output_limits_are_explicit() -> None:
    for name in ("README.md", "llms.txt", "AGENTS.md"):
        text = re.sub(r"\s+", " ", _text(name))
        assert "uncalibrated" in text, name
        assert "not safety severity" in text, name
        assert "does not establish malicious drift" in text, name


def test_optional_network_and_silent_fallback_are_disclosed() -> None:
    for name in ("README.md", "llms.txt", "AGENTS.md", "SECURITY.md"):
        text = _text(name)
        assert "optional configured network call" in text, name
        assert "silently falls back" in text, name
