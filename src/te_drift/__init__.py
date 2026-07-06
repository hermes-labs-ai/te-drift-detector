"""te-drift-detector: cross-turn scaffold/state drift detection for agent sessions.

Public API:
    StateFingerprint, FingerprintComparison  - per-turn feature extraction + drift
    DriftAnalyzer, DriftReading              - cross-turn anomaly detection
    TEDriftDetector                          - orchestrator over a full conversation
    load_turns, run_drift_analysis           - session JSONL adapter
"""

from .detector import ConversationSimulator, TEDriftDetector
from .drift_analyzer import DriftAnalyzer, DriftReading
from .jsonl_adapter import load_turns, run_drift_analysis
from .state_fingerprint import FingerprintComparison, StateFingerprint

__version__ = "0.1.0"

__all__ = [
    "StateFingerprint",
    "FingerprintComparison",
    "DriftAnalyzer",
    "DriftReading",
    "TEDriftDetector",
    "ConversationSimulator",
    "load_turns",
    "run_drift_analysis",
    "__version__",
]
