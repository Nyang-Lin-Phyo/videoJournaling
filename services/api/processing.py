
import logging

from .mock_processor import process_video_mock
from .repository import (
    advance_processing_status,
    complete_processing,
    fail_processing,
    get_video_path,
)


logger = logging.getLogger(__name__)


def process_queued_journal(journal_id: str) -> None:
    """
    Process a queued journal using the local mock.

    This function is invoked by FastAPI BackgroundTasks
    after the HTTP 202 response has been sent.

    The actual AI implementation will eventually
    replace the mock processor call.
    """

    # Claim the queued journal for processing.
    claimed = advance_processing_status(
        journal_id,
        expected_status="queued",
        new_status="transcribing",
    )

    if not claimed:
        logger.warning(
            "Journal %s could not be claimed for processing",
            journal_id,
        )
        return

    try:
        video_path = get_video_path(journal_id)

        if video_path is None:
            raise FileNotFoundError(
                "Journal has no attached video"
            )

        # Developer 3's real processor will eventually
        # replace this local mock call.
        transcript, analysis = process_video_mock(
            video_path
        )

        # The mock returns both outputs together, so
        # these stages complete almost immediately.
        advanced = advance_processing_status(
            journal_id,
            expected_status="transcribing",
            new_status="analyzing",
        )

        if not advanced:
            logger.warning(
                "Journal %s changed during processing",
                journal_id,
            )
            return

        saved = complete_processing(
            journal_id,
            transcript,
            analysis,
        )

        if not saved:
            logger.warning(
                "Could not save results for journal %s",
                journal_id,
            )
            return

        logger.info(
            "Mock processing completed for journal %s",
            journal_id,
        )

    except Exception:
        logger.exception(
            "Mock processing failed for journal %s",
            journal_id,
        )

        # Do not expose internal filesystem paths
        # or exception details in the public API.
        fail_processing(
            journal_id,
            "Mock processing failed",
        )
