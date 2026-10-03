"""Retry helpers for transient I/O failures."""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from auto_validator.utils.logging import get_logger

logger = get_logger("retry")

T = TypeVar("T")

# Transient errors worth retrying (file locks, NFS glitches, etc.)
TRANSIENT_ERRORS: tuple[type[BaseException], ...] = (
    OSError,
    TimeoutError,
    ConnectionError,
)


def retryable(
    max_attempts: int = 3,
    backoff_seconds: float = 1.0,
    exceptions: tuple[type[BaseException], ...] = TRANSIENT_ERRORS,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator factory: retry on transient exceptions with exponential backoff."""

    def decorator(fn: Callable[..., T]) -> Callable[..., T]:
        wrapped = retry(
            reraise=True,
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(multiplier=backoff_seconds, min=backoff_seconds, max=30),
            retry=retry_if_exception_type(exceptions),
            before_sleep=lambda rs: logger.warning(
                "Retrying %s after %s (attempt %s/%s)",
                fn.__name__,
                rs.outcome.exception() if rs.outcome else "?",
                rs.attempt_number,
                max_attempts,
            ),
        )(fn)
        return wrapped  # type: ignore[no-any-return]

    return decorator
