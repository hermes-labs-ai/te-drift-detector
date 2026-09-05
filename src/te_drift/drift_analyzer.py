"""Apply hand-set rules to lexical feature deltas.

The legacy fields named ``confidence`` and ``threat_level`` are uncalibrated
rule scores and heuristic tiers. The output does not establish malicious drift
and is not safety severity.
"""

from dataclasses import dataclass, field

from .state_fingerprint import FingerprintComparison, StateFingerprint


@dataclass
class DriftReading:
    """Single point-in-time drift measurement."""

    turn_number: int
    absolute_drift: float  # distance from baseline
    velocity_drift: float  # rate of change from previous turn
    component_drifts: dict[str, float] = field(default_factory=dict)
    is_anomaly: bool = False
    anomaly_reason: str = ""
    confidence: float = 0.0  # 0-1 uncalibrated heuristic rule score


class DriftAnalyzer:
    """Analyze state drift across conversation turns."""

    ABSOLUTE_DRIFT_THRESHOLD = 0.50  # deviation from baseline
    VELOCITY_DRIFT_THRESHOLD = 0.30  # rate of change per turn
    CONSECUTIVE_ANOMALY_THRESHOLD = 3  # flag if 3+ consecutive elevated drifts

    CRITICAL_COMPONENTS = {
        "fact_drift": 0.50,
        "entity_drift": 0.40,
        "sentiment_drift": 0.60,
        "task_framing_drift": 0.50,
        "authority_drift": 0.40,
        "register_drift": 0.45,
        "negation_drift": 0.70,
        "vocabulary_drift": 0.45,
    }

    def __init__(self, baseline_fingerprint: StateFingerprint):
        """Initialize with turn 0 (baseline) fingerprint."""
        self.baseline = baseline_fingerprint
        self.readings: list[DriftReading] = []
        self.prev_absolute_drift = 0.0
        self.consecutive_anomalies = 0

    def analyze_turn(self, current_fingerprint: StateFingerprint) -> DriftReading:
        """Analyze a new turn against baseline and previous turn."""
        comparison_to_baseline = FingerprintComparison(self.baseline, current_fingerprint)
        component_drifts = comparison_to_baseline.composite_drift()

        absolute_drift = self._weighted_average_drift(component_drifts)
        velocity_drift = abs(absolute_drift - self.prev_absolute_drift)

        is_anomaly, reason, confidence = self._classify_anomaly(
            absolute_drift, velocity_drift, component_drifts
        )

        if is_anomaly:
            self.consecutive_anomalies += 1
        else:
            self.consecutive_anomalies = 0

        reading = DriftReading(
            turn_number=len(self.readings) + 1,
            absolute_drift=absolute_drift,
            velocity_drift=velocity_drift,
            component_drifts=component_drifts,
            is_anomaly=is_anomaly,
            anomaly_reason=reason,
            confidence=confidence,
        )

        self.readings.append(reading)
        self.prev_absolute_drift = absolute_drift

        return reading

    def _weighted_average_drift(self, component_drifts: dict[str, float]) -> float:
        """Calculate weighted average of component drifts."""
        weights = {
            "fact_drift": 0.25,
            "entity_drift": 0.15,
            "sentiment_drift": 0.15,
            "task_framing_drift": 0.15,
            "authority_drift": 0.10,
            "register_drift": 0.10,
            "negation_drift": 0.05,
            "vocabulary_drift": 0.05,
        }

        total_drift = 0.0
        for component, drift_value in component_drifts.items():
            total_drift += drift_value * weights.get(component, 0.0)

        return total_drift

    def _classify_anomaly(
        self, absolute_drift: float, velocity_drift: float, component_drifts: dict[str, float]
    ) -> tuple[bool, str, float]:
        """Classify whether this turn shows anomalous drift."""
        if absolute_drift > self.ABSOLUTE_DRIFT_THRESHOLD:
            return (
                True,
                f"Absolute drift {absolute_drift:.3f} exceeds threshold {self.ABSOLUTE_DRIFT_THRESHOLD}",
                min((absolute_drift / 0.70), 1.0),
            )

        if velocity_drift > self.VELOCITY_DRIFT_THRESHOLD:
            return (
                True,
                f"Rapid drift velocity {velocity_drift:.3f} (acceleration detected)",
                min((velocity_drift / 0.50), 1.0),
            )

        critical_violations = []
        for component, threshold in self.CRITICAL_COMPONENTS.items():
            if component_drifts.get(component, 0.0) > threshold:
                critical_violations.append((component, component_drifts[component]))

        if len(critical_violations) >= 3:
            worst = sorted(critical_violations, key=lambda x: x[1], reverse=True)[0]
            return (True, f"Multiple critical drifts: {worst[0]}={worst[1]:.3f}", 0.70)

        pattern_match, pattern_name, pattern_conf = self._detect_attack_pattern(component_drifts)
        if pattern_match:
            return (True, f"Attack pattern detected: {pattern_name}", pattern_conf)

        return (False, "", 0.0)

    def _detect_attack_pattern(self, component_drifts: dict[str, float]) -> tuple[bool, str, float]:
        """Detect specific multi-turn attack signatures."""
        poison_indicators = (
            component_drifts["fact_drift"] > 0.40,
            component_drifts["task_framing_drift"] > 0.40,
            component_drifts["sentiment_drift"] > 0.50,
        )
        if sum(poison_indicators) >= 2:
            return (True, "Scaffold Poisoning", 0.80)

        persona_indicators = (
            component_drifts["register_drift"] > 0.40,
            component_drifts["authority_drift"] > 0.35,
            component_drifts["negation_drift"] > 0.60,
        )
        if sum(persona_indicators) >= 2:
            return (True, "Persona Drift", 0.75)

        constraint_indicators = (
            component_drifts["negation_drift"] > 0.65,
            component_drifts["fact_drift"] > 0.50,
        )
        if sum(constraint_indicators) >= 2:
            return (True, "Constraint Bypass", 0.70)

        interference_indicators = (
            component_drifts["vocabulary_drift"] > 0.70,
            component_drifts["entity_drift"] > 0.70,
            component_drifts["task_framing_drift"] > 0.60,
        )
        if sum(interference_indicators) >= 3:
            return (True, "Scaffold Interference", 0.72)

        return (False, "", 0.0)

    def has_sustained_anomaly(self) -> bool:
        """True if drift has been anomalous for CONSECUTIVE_ANOMALY_THRESHOLD turns."""
        return self.consecutive_anomalies >= self.CONSECUTIVE_ANOMALY_THRESHOLD

    def get_threat_level(self) -> str:
        """Return the legacy uncalibrated heuristic tier for recent readings."""
        if not self.readings:
            return "UNKNOWN"

        recent_anomalies = sum(1 for r in self.readings[-3:] if r.is_anomaly)
        max_recent_drift = max((r.absolute_drift for r in self.readings[-3:]), default=0.0)

        if self.has_sustained_anomaly():
            return "CRITICAL"
        elif recent_anomalies >= 2:
            return "HIGH"
        elif max_recent_drift > self.ABSOLUTE_DRIFT_THRESHOLD:
            return "MEDIUM"
        elif recent_anomalies >= 1:
            return "LOW"
        else:
            return "NORMAL"

    def summary_report(self) -> dict:
        """Generate a summary of all drift analysis."""
        if not self.readings:
            return {
                "total_turns": 0,
                "anomalies_detected": 0,
                "threat_level": "UNKNOWN",
                "avg_absolute_drift": 0.0,
                "max_absolute_drift": 0.0,
                "readings": [],
            }

        anomalies = [r for r in self.readings if r.is_anomaly]
        absolute_drifts = [r.absolute_drift for r in self.readings]

        return {
            "total_turns": len(self.readings),
            "anomalies_detected": len(anomalies),
            "threat_level": self.get_threat_level(),
            "sustained_anomaly": self.has_sustained_anomaly(),
            "avg_absolute_drift": sum(absolute_drifts) / len(absolute_drifts),
            "max_absolute_drift": max(absolute_drifts),
            "consecutive_anomalies_threshold": self.CONSECUTIVE_ANOMALY_THRESHOLD,
            "readings": [
                {
                    "turn": r.turn_number,
                    "absolute_drift": round(r.absolute_drift, 4),
                    "velocity_drift": round(r.velocity_drift, 4),
                    "is_anomaly": r.is_anomaly,
                    "anomaly_reason": r.anomaly_reason,
                    "confidence": round(r.confidence, 2),
                    "components": {k: round(v, 3) for k, v in r.component_drifts.items()},
                }
                for r in self.readings
            ],
        }
