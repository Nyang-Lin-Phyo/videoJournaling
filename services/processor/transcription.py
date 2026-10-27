"""Speech-to-text for video journals.

P1 ships only the deterministic, offline mock implementation. The
Faster-Whisper CPU path arrives in milestone P2 and fails loudly with a
typed error until then — it never fabricates a transcript.
"""

from __future__ import annotations

from pathlib import Path

from .config import load_config
from .errors import InvalidVideoError, TranscriptionError

# Deterministic synthetic transcript for mock mode. It is clearly test text
# so nobody mistakes mock output for a real journal.
MOCK_TRANSCRIPT = (
    "This is a synthetic mock transcript used for local pipeline testing. "
    "I had a good day and I am grateful for my friends and school."
)


def _looks_like_mp4(path: Path) -> bool:
    """Minimal MVP sniff: ISO BMFF files carry an 'ftyp' box near the start.

    This is not malware scanning or full container validation; it just keeps
    obviously-wrong files (e.g. a text file named .mp4) out of the pipeline
    in mock mode. Real mode additionally decodes the audio stream.
    """
    try:
        with path.open("rb") as handle:
            header = handle.read(32)
    except OSError:
        return False
    return b"ftyp" in header


def transcribe_video(video_path: Path) -> str:
    """Return the transcript for the MP4 at ``video_path``.

    Modes:
      * mock           - deterministic offline transcript (milestone P1)
      * faster_whisper - local CPU transcription (milestone P2, not yet
        implemented; raises TranscriptionError)
    """
    path = Path(video_path)
    if not path.is_file():
        raise InvalidVideoError(f"Video file not found: {path.name}")
    if not _looks_like_mp4(path):
        raise InvalidVideoError(f"File does not look like an MP4: {path.name}")

    config = load_config()
    if config.transcription_mode == "mock":
        return MOCK_TRANSCRIPT

    raise TranscriptionError(
        "faster_whisper transcription is not implemented yet (milestone P2)."
    )
