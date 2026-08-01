"""te-drift-detector: experimental lexical feature-delta telemetry.

Public API:
    StateFingerprint, FingerprintComparison  - feature extraction + delta comparison
    DriftAnalyzer, DriftReading              - uncalibrated heuristic rule evaluation
    TEDriftDetector                          - orchestrator over supplied conversation text
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
