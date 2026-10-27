"""Transcript-only emotional analysis.

P1 ships a deterministic, keyword-driven mock. The Gemini-backed path
arrives in milestone P3 and fails loudly with a typed error until then —
it never fabricates a positive/neutral result after an API problem.

Scope note: everything here is inferred from transcript *text*. It is a
journaling reflection, not a clinical, psychological, or mental-health
assessment, and nothing in this module diagnoses the speaker.
"""

from __future__ import annotations

import re

from pydantic import ValidationError

from .config import load_config
from .errors import AnalysisError, EmptyTranscriptError
from .models import Analysis, Sentiment

_WORD_RE = re.compile(r"[a-z']+")

_POSITIVE_WORDS = frozenset(
    {"good", "great", "better", "best", "awesome", "wonderful", "nice", "love"}
)
_NEGATIVE_WORDS = frozenset(
    {"bad", "worse", "worst", "terrible", "awful", "hate", "horrible", "poor"}
)

_EMOTION_KEYWORDS: dict[str, frozenset[str]] = {
    "joy": frozenset(
        {"happy", "happier", "glad", "excited", "enjoy", "enjoyed", "fun", "smile"}
    ),
    "gratitude": frozenset(
        {"grateful", "thankful", "appreciate", "appreciation", "thanks"}
    ),
    "calm": frozenset({"calm", "peaceful", "relaxed", "content", "rested"}),
    "frustration": frozenset(
        {"frustrated", "annoyed", "angry", "irritated", "upset"}
    ),
    "sadness": frozenset({"sad", "down", "unhappy", "disappointed", "cry"}),
    "worry": frozenset({"worried", "anxious", "nervous", "stressed", "overwhelmed"}),
}

_DEFAULT_EMOTIONS: dict[Sentiment, list[str]] = {
    "positive": ["joy"],
    "negative": ["sadness"],
    "neutral": ["calm"],
}

_THEME_KEYWORDS: dict[str, frozenset[str]] = {
    "friends": frozenset({"friend", "friends", "buddy", "buddies", "pal"}),
    "family": frozenset(
        {"family", "mom", "dad", "mother", "father", "sister", "brother", "parents"}
    ),
    "school": frozenset(
        {"school", "class", "classes", "teacher", "exam", "homework", "study"}
    ),
    "work": frozenset({"work", "office", "boss", "job", "deadline", "meeting"}),
    "health": frozenset({"sleep", "tired", "exercise", "health", "sick", "walk"}),
    "hobbies": frozenset(
        {"music", "game", "games", "movie", "movies", "read", "reading", "hobby"}
    ),
}

_DEFAULT_THEME = "daily life"

_MAX_EMOTIONS = 3


def _tokenize(text: str) -> frozenset[str]:
    return frozenset(_WORD_RE.findall(text.lower()))


def _classify_sentiment(tokens: frozenset[str]) -> Sentiment:
    positive_hits = len(tokens & _POSITIVE_WORDS)
    negative_hits = len(tokens & _NEGATIVE_WORDS)
    if positive_hits > negative_hits:
        return "positive"
    if negative_hits > positive_hits:
        return "negative"
    return "neutral"


def _matched_labels(
    tokens: frozenset[str], keyword_map: dict[str, frozenset[str]]
) -> list[str]:
    matched = [
        label for label, keywords in keyword_map.items() if tokens & keywords
    ]
    return sorted(matched)


def _mock_analysis(text: str) -> Analysis:
    """Deterministic analysis derived purely from transcript keywords."""
    tokens = _tokenize(text)
    sentiment = _classify_sentiment(tokens)

    emotions = _matched_labels(tokens, _EMOTION_KEYWORDS)[:_MAX_EMOTIONS]
    if not emotions:
        emotions = list(_DEFAULT_EMOTIONS[sentiment])

    themes = _matched_labels(tokens, _THEME_KEYWORDS)
    if not themes:
        themes = [_DEFAULT_THEME]

    theme_phrase = " and ".join(themes[:3])
    summary = (
        f"The speaker describes a {sentiment} experience "
        f"mentioning {theme_phrase}."
    )

    return Analysis(
        sentiment=sentiment,
        emotions=emotions,
        themes=themes,
        summary=summary,
    )


def analyze_transcript(transcript: str) -> Analysis:
    """Analyze ``transcript`` text and return a validated Analysis.

    Modes:
      * mock  - deterministic keyword analysis (milestone P1)
      * gemini - Google Gemini structured output (milestone P3, not yet
        implemented; raises AnalysisError)
    """
    text = transcript.strip()
    if not text:
        raise EmptyTranscriptError("Cannot analyze an empty transcript.")

    config = load_config()
    if len(text) > config.max_transcript_chars:
        raise AnalysisError(
            "Transcript is too long to analyze "
            f"(limit {config.max_transcript_chars} characters)."
        )

    if config.analysis_mode == "mock":
        try:
            return _mock_analysis(text)
        except ValidationError as exc:  # pragma: no cover - defensive guard
            raise AnalysisError("Mock analysis produced invalid output.") from exc

    raise AnalysisError(
        "Gemini analysis is not implemented yet (milestone P3)."
    )
