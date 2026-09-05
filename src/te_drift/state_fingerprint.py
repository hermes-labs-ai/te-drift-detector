"""
State fingerprinting: extract lightweight features from conversation turns.

Tracks an "information fingerprint" of the scaffold state across turns. Features
capture facts, entities, sentiment, task framing, authority level, and style
register.

Drift on facts/entities/vocabulary uses a lexical set-overlap (Jaccard) metric
by default. This makes the detector deterministic and reproducible: the same
input always yields the same output, independent of what services happen to be
running locally. There are zero required third-party dependencies — everything
here is the Python standard library.

Semantic embeddings are optional and unevaluated. Setting TE_DRIFT_EMBED=1 can
make an optional configured network call to TE_DRIFT_OLLAMA_URL and transmit
derived text features. If either endpoint request fails or returns no vector,
the implementation silently falls back to lexical set overlap. Reports do not
expose the active comparison mode or fallback.

Environment overrides:
    TE_DRIFT_EMBED=1      enable optional Ollama semantic embeddings (default: off)
    TE_DRIFT_OLLAMA_URL   embeddings endpoint (default http://localhost:11434/api/embeddings)
    TE_DRIFT_EMBED_MODEL  embedding model name (default nomic-embed-text)
"""

import json
import math
import os
import re
import urllib.request
from collections import Counter
from typing import Any

_OLLAMA_URL = os.environ.get("TE_DRIFT_OLLAMA_URL", "http://localhost:11434/api/embeddings")
_EMBED_MODEL = os.environ.get("TE_DRIFT_EMBED_MODEL", "nomic-embed-text")


def _embed(text: str):
    """Embed text via a local Ollama endpoint. Returns a vector or None.

    Returns None when embeddings are disabled (the default) or on any failure
    (endpoint down, timeout, bad payload), so callers degrade gracefully to the
    set-overlap metric. Never raises.
    """
    if os.environ.get("TE_DRIFT_EMBED") != "1":
        return None
    try:
        payload = json.dumps({"model": _EMBED_MODEL, "prompt": text}).encode()
        req = urllib.request.Request(
            _OLLAMA_URL,
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read())
        return result.get("embedding")
    except Exception:
        return None


def _cosine(u, v) -> float:
    """Cosine similarity between two embedding vectors."""
    dot = sum(a * b for a, b in zip(u, v, strict=False))
    norm_u = math.sqrt(sum(a * a for a in u))
    norm_v = math.sqrt(sum(b * b for b in v))
    if norm_u == 0 or norm_v == 0:
        return 0.0
    return dot / (norm_u * norm_v)


def _jaccard_distance(a: set[str], b: set[str]) -> float:
    """1 - Jaccard similarity between two sets (0 = identical, 1 = disjoint)."""
    union = a | b
    if not union:
        return 0.0
    return 1.0 - len(a & b) / len(union)


def _semantic_or_jaccard(items_b, items_c) -> float:
    """Cosine drift on embedded text if available, else Jaccard on the sets."""
    b_set = set(items_b)
    c_set = set(items_c)
    if not b_set and not c_set:
        return 0.0

    text_b = " ".join(sorted(b_set))
    text_c = " ".join(sorted(c_set))
    if not text_b.strip() or not text_c.strip():
        return _jaccard_distance(b_set, c_set)

    u = _embed(text_b)
    v = _embed(text_c)
    if u is None or v is None:
        return _jaccard_distance(b_set, c_set)
    return 1.0 - _cosine(u, v)


class StateFingerprint:
    """Extract a feature vector from a conversation turn."""

    def __init__(self, turn_text: str, role: str = "assistant"):
        """
        Args:
            turn_text: The full text of this turn (system message + user input + response).
            role: 'system', 'user', or 'assistant'.
        """
        self.text = turn_text
        self.role = role
        self.features = self._extract_features()

    def _extract_features(self) -> dict[str, Any]:
        """Extract all state features from turn text."""
        return {
            "facts": self._extract_facts(),
            "entities": self._extract_entities(),
            "sentiment": self._extract_sentiment(),
            "task_framing": self._extract_task_framing(),
            "authority_level": self._extract_authority_level(),
            "style_register": self._extract_style_register(),
            "negations": self._extract_negations(),
            "constraints": self._extract_constraints(),
            "token_count": len(self.text.split()),
            "vocabulary": self._extract_vocabulary(),
        }

    def _extract_facts(self) -> list[str]:
        """Extract explicit fact statements (declarative sentences)."""
        sentences = re.split(r"[.!?]\s+", self.text)
        facts = []

        strong_patterns = [
            r"\bestab(?:lished|lish)\b.*\b(?:is|are|was|were)\b",
            r"\b(?:confirmed|verified|decided|concluded)\b",
            r"\b(?:fact|requirement|constraint|rule|policy)\b.*\b(?:is|are|was|were)\b",
            r"\bthe\s+\w+\s+(?:is|are|was|were|requires?)\b",
        ]

        for sent in sentences:
            sent_lower = sent.lower()
            if any(re.search(pattern, sent_lower) for pattern in strong_patterns):
                if len(sent.strip()) > 10:
                    facts.append(sent.strip())

        return facts[:5]

    def _extract_entities(self) -> set[str]:
        """Extract named entities and key concepts."""
        tokens = self.text.split()
        entities = set()

        for token in tokens:
            if token and token[0].isupper() and len(token) > 2:
                cleaned = re.sub(r"[^a-zA-Z]", "", token)
                if cleaned and len(cleaned) > 2:
                    entities.add(cleaned)

        entity_patterns = [
            r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b",
            r"\b(?:project|task|goal|deadline|requirement|constraint)\b",
        ]

        for pattern in entity_patterns:
            for match in re.finditer(pattern, self.text, re.IGNORECASE):
                entities.add(match.group().lower())

        return entities

    def _extract_sentiment(self) -> float:
        """Estimate emotional tone/sentiment on scale [-1, 1]."""
        positive_words = {
            "good", "great", "excellent", "helpful", "supportive", "positive",
            "happy", "confident", "trusted", "safe", "secure", "reliable",
        }
        negative_words = {
            "bad", "terrible", "harmful", "dangerous", "suspicious", "negative",
            "angry", "fearful", "unsafe", "risky", "unreliable", "failed",
        }

        text_lower = self.text.lower()
        pos_score = sum(1 for word in positive_words if f" {word} " in f" {text_lower} ")
        neg_score = sum(1 for word in negative_words if f" {word} " in f" {text_lower} ")

        total = pos_score + neg_score
        if total == 0:
            return 0.0

        return (pos_score - neg_score) / total

    def _extract_task_framing(self) -> dict[str, int]:
        """Extract how the task/goal is framed."""
        return {
            "compliance": len(re.findall(r"\b(must|should|need to|require|mandate)\b", self.text, re.I)),
            "flexibility": len(re.findall(r"\b(can|may|could|possible|option)\b", self.text, re.I)),
            "urgency": len(re.findall(r"\b(urgent|asap|immediately|critical|emergency)\b", self.text, re.I)),
            "exploration": len(re.findall(r"\b(explore|investigate|analyze|research|study)\b", self.text, re.I)),
        }

    def _extract_authority_level(self) -> float:
        """Detect authority framing on scale [0, 1]."""
        authority_signals = [
            "expert", "researcher", "scientist", "professional", "authority",
            "academic", "published", "official", "consensus", "industry standard",
            "as established", "verified by", "confirmed that",
        ]

        text_lower = self.text.lower()
        count = sum(1 for signal in authority_signals if signal in text_lower)

        return min(count / 5, 1.0)

    def _extract_style_register(self) -> dict[str, float]:
        """Categorize communication register (formal, casual, intimate, conspiratorial)."""
        text_lower = self.text.lower()

        formal_markers = ["therefore", "moreover", "however", "thus", "hereby", "thesis"]
        casual_markers = ["like", "you know", "kinda", "gonna", "wanna", "lol"]
        intimate_markers = ["between us", "honestly", "really", "trust me", "look"]
        conspiratorial_markers = ["both know", "pretense", "theater", "admit", "admit it", "really do"]

        formal_score = sum(1 for m in formal_markers if m in text_lower)
        casual_score = sum(1 for m in casual_markers if m in text_lower)
        intimate_score = sum(1 for m in intimate_markers if m in text_lower)
        conspiratorial_score = sum(1 for m in conspiratorial_markers if m in text_lower)

        total = formal_score + casual_score + intimate_score + conspiratorial_score
        if total == 0:
            return {"formal": 0.5, "casual": 0.2, "intimate": 0.2, "conspiratorial": 0.1}

        return {
            "formal": formal_score / total,
            "casual": casual_score / total,
            "intimate": intimate_score / total,
            "conspiratorial": conspiratorial_score / total,
        }

    def _extract_negations(self) -> int:
        """Count negation words (signals refusal/constraint)."""
        negation_words = [
            "not", "cannot", "refuse", "unable", "impossible",
            "prohibited", "forbidden", "denied", "no", "never", "neither",
        ]

        text_lower = self.text.lower()
        return sum(1 for word in negation_words if f" {word} " in f" {text_lower} ")

    def _extract_constraints(self) -> list[str]:
        """Extract explicit constraint statements."""
        constraint_keywords = [
            "constraint", "limitation", "restriction", "rule", "policy",
            "guideline", "standard", "requirement", "specification",
        ]

        sentences = re.split(r"[.!?]\s+", self.text)
        constraints = []

        for sent in sentences:
            sent_lower = sent.lower()
            if any(keyword in sent_lower for keyword in constraint_keywords):
                constraints.append(sent.strip())

        return constraints[:5]

    def _extract_vocabulary(self) -> Counter:
        """Get word frequency distribution (stop words removed)."""
        tokens = re.findall(r"\b[a-z]+\b", self.text.lower())
        stop_words = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "is", "are", "was", "were", "be", "been", "being", "have", "has",
            "i", "you", "he", "she", "it", "we", "they", "this", "that", "these", "those",
            "can", "could", "would", "should", "may", "might", "must", "will", "with",
            "as", "by", "from", "up", "about", "out", "if", "so", "what", "which",
        }
        tokens = [t for t in tokens if t not in stop_words and len(t) > 3]
        return Counter(tokens)


class FingerprintComparison:
    """Compare two fingerprints to measure drift."""

    def __init__(self, baseline: StateFingerprint, current: StateFingerprint):
        self.baseline = baseline
        self.current = current

    def fact_drift(self) -> float:
        """Measure divergence in facts (0 = same, 1 = different)."""
        return _semantic_or_jaccard(
            self.baseline.features["facts"], self.current.features["facts"]
        )

    def entity_drift(self) -> float:
        """Measure entity set changes."""
        return _semantic_or_jaccard(
            self.baseline.features["entities"], self.current.features["entities"]
        )

    def sentiment_drift(self) -> float:
        """Measure sentiment change magnitude."""
        return abs(self.baseline.features["sentiment"] - self.current.features["sentiment"])

    def task_framing_drift(self) -> float:
        """Measure change in task framing indicators."""
        baseline_framing = self.baseline.features["task_framing"]
        current_framing = self.current.features["task_framing"]

        drift = 0.0
        for key in baseline_framing:
            drift += abs(baseline_framing[key] - current_framing[key])

        return drift / len(baseline_framing)

    def authority_drift(self) -> float:
        """Measure change in authority framing."""
        return abs(
            self.baseline.features["authority_level"] - self.current.features["authority_level"]
        )

    def register_drift(self) -> float:
        """Measure shift in communication style/register."""
        baseline_reg = self.baseline.features["style_register"]
        current_reg = self.current.features["style_register"]

        drift = 0.0
        for key in baseline_reg:
            drift += abs(baseline_reg[key] - current_reg[key])

        return drift / len(baseline_reg)

    def negation_drift(self) -> float:
        """Measure change in constraint language."""
        baseline_negs = self.baseline.features["negations"]
        current_negs = self.current.features["negations"]

        if baseline_negs == 0 and current_negs == 0:
            return 0.0

        max_negs = max(baseline_negs, current_negs, 1)
        return abs(baseline_negs - current_negs) / max_negs

    def vocabulary_drift(self) -> float:
        """Measure lexical divergence."""
        return _semantic_or_jaccard(
            set(self.baseline.features["vocabulary"].keys()),
            set(self.current.features["vocabulary"].keys()),
        )

    def composite_drift(self) -> dict[str, float]:
        """Calculate all drift metrics at once."""
        return {
            "fact_drift": self.fact_drift(),
            "entity_drift": self.entity_drift(),
            "sentiment_drift": self.sentiment_drift(),
            "task_framing_drift": self.task_framing_drift(),
            "authority_drift": self.authority_drift(),
            "register_drift": self.register_drift(),
            "negation_drift": self.negation_drift(),
            "vocabulary_drift": self.vocabulary_drift(),
        }
