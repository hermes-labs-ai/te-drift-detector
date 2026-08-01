"""Guard the bounded repository and installed-package claim surfaces."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOP_LEVEL_CLAIM_SURFACES = (
    "README.md",
    "llms.txt",
    "AGENTS.md",
    "CITATION.cff",
    "SECURITY.md",
    "pyproject.toml",
)
PACKAGE_CLAIM_SURFACES = tuple(
    str(path.relative_to(ROOT)) for path in sorted((ROOT / "src" / "te_drift").rglob("*.py"))
)
CLAIM_SURFACES = TOP_LEVEL_CLAIM_SURFACES + PACKAGE_CLAIM_SURFACES


def _present(names: tuple[str, ...]) -> tuple[str, ...]:
    """Return claim surfaces shipped in this checkout or source distribution."""
    return tuple(name for name in names if (ROOT / name).is_file())


def _text(name: str) -> str:
    return (ROOT / name).read_text(encoding="utf-8").lower()


def test_repository_claim_surface_inventory_is_complete() -> None:
    """Require the known bounded surfaces for each tested distribution shape."""
    top_level = TOP_LEVEL_CLAIM_SURFACES if (ROOT / ".git").exists() else (
        "README.md",
        "pyproject.toml",
    )
    expected = top_level + PACKAGE_CLAIM_SURFACES
    missing = set(expected) - set(_present(expected))
    assert not missing, sorted(missing)


def test_retired_denominator_and_unsupported_claims_are_absent() -> None:
    combined = "\n".join(_text(name) for name in _present(CLAIM_SURFACES))
    forbidden = {
        "retired denominator": r"\bn\s*=\s*74\b",
        "categorical gradual detection": (
            r"\b(?:(?:catches?|detects?)\s+(?:the\s+)?gradual|"
            r"gradual.{0,40}(?:detection|detector))\b"
        ),
        "self-described benchmark": r"\bbenchmarks?\b",
        "deployment calibration implication": r"\bcalibrat(?:e|ed)\s+per\s+deployment\b",
        "unevaluated embedding fidelity": r"\bembeddings?\s+raise\s+fidelity\b",
        "unconditional no-network promise": (
            r"\b(?:makes?\s+)?no\s+network(?:\s+(?:calls?|is\s+touched)|[.,;])"
        ),
    }
    for label, pattern in forbidden.items():
        assert re.search(pattern, combined) is None, label


def test_primary_claim_surfaces_use_the_bounded_product_definition() -> None:
    names = (
        "README.md",
        "llms.txt",
        "AGENTS.md",
        "CITATION.cff",
        "pyproject.toml",
        "src/te_drift/__init__.py",
        "src/te_drift/detector.py",
        "src/te_drift/jsonl_adapter.py",
    )
    for name in _present(names):
        assert "experimental lexical feature-delta telemetry" in _text(name), name


def test_heuristic_output_limits_are_explicit() -> None:
    names = (
        "README.md",
        "llms.txt",
        "AGENTS.md",
        "src/te_drift/detector.py",
        "src/te_drift/drift_analyzer.py",
    )
    for name in _present(names):
        text = re.sub(r"\s+", " ", _text(name))
        assert "uncalibrated" in text, name
        assert "not safety severity" in text, name
        assert "does not establish malicious drift" in text, name


def test_optional_network_and_silent_fallback_are_disclosed() -> None:
    names = (
        "README.md",
        "llms.txt",
        "AGENTS.md",
        "SECURITY.md",
        "src/te_drift/state_fingerprint.py",
        "src/te_drift/evals/__init__.py",
        "src/te_drift/evals/harness.py",
    )
    for name in _present(names):
        text = re.sub(r"\s+", " ", _text(name))
        assert "optional configured network call" in text, name
        assert "silently falls back" in text, name
