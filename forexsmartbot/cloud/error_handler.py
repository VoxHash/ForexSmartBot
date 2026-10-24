"""
Error Handling for Cloud Integration
Provides enhanced error handling for external APIs and cloud services.
"""

from __future__ import annotations

import logging
import random
import time
import traceback
from datetime import datetime
from functools import wraps
from typing import Callable, Dict, Optional, TypeVar

import requests

T = TypeVar("T")


def compute_backoff_delay(
    attempt: int,
    base_delay: float = 1.0,
    *,
    max_delay: float = 30.0,
    jitter: bool = True,
) -> float:
    """Exponential backoff delay for zero-based attempt index."""
    delay = min(max_delay, base_delay * (2**attempt))
    if jitter:
        delay = delay * (0.5 + random.random() * 0.5)
    return delay


def retry_call(
    func: Callable[[], T],
    *,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    retry_on: tuple = (
        requests.exceptions.Timeout,
        requests.exceptions.ConnectionError,
    ),
    logger: Optional[logging.Logger] = None,
) -> T:
    """
    Call ``func`` with exponential backoff + jitter.

    Retries on connection/timeout errors and HTTP 5xx when ``func`` raises
    ``requests.exceptions.HTTPError``.
    """
    log = logger or logging.getLogger(__name__)
    last_exception: Optional[BaseException] = None

    for attempt in range(max_retries):
        try:
            return func()
        except requests.exceptions.HTTPError as exc:
            last_exception = exc
            status = getattr(getattr(exc, "response", None), "status_code", None)
            if status is not None and status < 500:
                log.error("Client error (no retry): %s", exc)
                raise
            log.warning(
                "Server error (attempt %s/%s): %s", attempt + 1, max_retries, exc
            )
        except retry_on as exc:
            last_exception = exc
            log.warning(
                "Transient error (attempt %s/%s): %s", attempt + 1, max_retries, exc
            )
        except Exception:
            raise

        if attempt < max_retries - 1:
            time.sleep(
                compute_backoff_delay(attempt, base_delay, max_delay=max_delay)
            )

    log.error("All retries failed: %s", last_exception)
    assert last_exception is not None
    raise last_exception


class CloudErrorHandler:
    """Enhanced error handling for cloud operations."""

    def __init__(self, max_retries: int = 3, retry_delay: float = 1.0):
        """
        Initialize error handler.

        Args:
            max_retries: Maximum number of retries
            retry_delay: Base delay between retries in seconds
        """
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.logger = logging.getLogger(__name__)

    def handle_api_error(self, func: Callable):
        """Decorator for handling API errors with retries."""

        @wraps(func)
        def wrapper(*args, **kwargs):
            return retry_call(
                lambda: func(*args, **kwargs),
                max_retries=self.max_retries,
                base_delay=self.retry_delay,
                logger=self.logger,
            )

        return wrapper

    def handle_websocket_error(self, func: Callable):
        """Decorator for handling WebSocket errors."""

        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                self.logger.error("WebSocket error: %s", e)
                self.logger.debug(traceback.format_exc())
                raise

        return wrapper

    def log_error(self, error: Exception, context: Dict = None):
        """
        Log error with context.

        Args:
            error: Exception object
            context: Additional context dictionary
        """
        error_info = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "timestamp": datetime.now().isoformat(),
            "context": context or {},
        }

        self.logger.error("Error occurred: %s", error_info)
        self.logger.debug(traceback.format_exc())

        return error_info


class CloudHealthMonitor:
    """Monitor health of cloud services."""

    def __init__(self):
        self.health_status: Dict[str, Dict] = {}
        self.logger = logging.getLogger(__name__)

    def check_service_health(self, service_name: str, check_func: Callable) -> Dict:
        """
        Check health of a cloud service.

        Args:
            service_name: Name of the service
            check_func: Function that returns health status

        Returns:
            Health status dictionary
        """
        try:
            status = check_func()
            self.health_status[service_name] = {
                "status": "healthy" if status else "unhealthy",
                "last_check": datetime.now().isoformat(),
                "available": bool(status),
            }
            return self.health_status[service_name]
        except Exception as e:
            self.health_status[service_name] = {
                "status": "error",
                "last_check": datetime.now().isoformat(),
                "available": False,
                "error": str(e),
            }
            self.logger.error("Health check failed for %s: %s", service_name, e)
            return self.health_status[service_name]

    def get_all_health_status(self) -> Dict:
        """Get health status of all services."""
        return self.health_status

    def is_service_healthy(self, service_name: str) -> bool:
        """Check if a service is healthy."""
        if service_name not in self.health_status:
            return False
        return self.health_status[service_name].get("available", False)
