# Developer 3 — AI Processor (`services/processor/`)

Transcription + transcript-only emotional analysis for video journals.
Milestone **P1 (mock pipeline)** is implemented; P2 (Faster-Whisper) and
P3 (Gemini) are not yet.

The only processing entry point is the Contract B callable:

```python
from pathlib import Path
from services.processor.pipeline import process_video

result = process_video(Path("samples/test-journal.mp4"))
# {"transcript": str,
#  "analysis": {"sentiment": "positive"|"negative"|"neutral",
#               "emotions": [str], "themes": [str], "summary": str}}
```

`on_stage` (optional) fires `"transcribing"` then `"analyzing"`; the
backend owns status writes. Any failure raises a typed `ProcessorError`
subclass — never a fabricated success.

## Modes (environment variables)

| Variable | Values | Default | Meaning |
| --- | --- | --- | --- |
| `TRANSCRIPTION_MODE` | `mock` \| `faster_whisper` | `mock` | P1 implements mock only |
| `ANALYSIS_MODE` | `mock` \| `gemini` | `mock` | P1 implements mock only |
| `WHISPER_MODEL` | e.g. `tiny.en` | `tiny.en` | Used from P2 |
| `GEMINI_MODEL` | model id | empty | Used from P3 |
| `GEMINI_API_KEY` | secret | empty | Used from P3; never commit |

A root `.env` is read if present (python-dotenv, `override=False`); real
shell exports always win. Unknown mode values raise `ConfigError`.

## Setup and commands (repository root, WSL/Ubuntu)

```bash
uv venv --python 3.12 .venv        # Python 3.11+ required
source .venv/bin/activate
uv pip install -r services/processor/requirements.txt

# Offline deterministic smoke test (any existing small .mp4 works):
TRANSCRIPTION_MODE=mock ANALYSIS_MODE=mock \
  python -m services.processor.cli samples/test-journal.mp4

# stdout is pure JSON:
TRANSCRIPTION_MODE=mock ANALYSIS_MODE=mock \
  python -m services.processor.cli samples/test-journal.mp4 \
  | python -m json.tool

python -m pytest services/processor/tests -q
```

Mock mode needs no network, no API key, and no model downloads. The CLI
prints a `SYNTHETIC` notice to **stderr** whenever either mode is mock.

## Notes

- Tests build tiny synthetic MP4s at runtime (the repo `.gitignore`
  blocks `*.mp4`, so no video fixtures are committed).
- Analysis is inferred from transcript text only — a journaling
  reflection, not a clinical or psychological assessment.
- Real-mode branches raise typed "not implemented yet" errors in P1;
  they never fall back to mock silently.
