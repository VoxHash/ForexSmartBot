"""
Shared authentication helpers for remote monitoring and cloud APIs.
"""

from __future__ import annotations

import hmac
import logging
import os
import secrets
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# Weak / placeholder secrets that must never be used in production.
_INSECURE_SECRETS = frozenset(
    {
        "",
        "default-secret-key-change-in-production",
        "changeme",
        "secret",
        "password",
        "api_key",
        "test",
    }
)


def package_version() -> str:
    """Return installed package version, falling back to local __version__."""
    try:
        from importlib.metadata import version

        return version("forexsmartbot")
    except Exception:
        try:
            from forexsmartbot import __version__

            return __version__
        except Exception:
            return "0.0.0"


def is_insecure_secret(value: Optional[str]) -> bool:
    """True if the value is empty or a known placeholder secret."""
    if value is None:
        return True
    normalized = value.strip().lower()
    return normalized in _INSECURE_SECRETS or len(value.strip()) < 16


def allow_insecure_mode() -> bool:
    """Explicit opt-in for local/dev use without a strong API key."""
    return os.getenv("FSB_ALLOW_INSECURE_MONITOR", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def extract_bearer_or_api_key(
    authorization_header: str = "",
    api_key_header: str = "",
) -> Optional[str]:
    """
    Extract a token from Authorization: Bearer <token> or X-API-Key.

    Returns None when neither header provides a token.
    """
    auth = (authorization_header or "").strip()
    if auth.lower().startswith("bearer "):
        token = auth[7:].strip()
        if token:
            return token
    key = (api_key_header or "").strip()
    return key or None


def constant_time_equals(provided: Optional[str], expected: Optional[str]) -> bool:
    """Constant-time string compare; False if either side is missing."""
    if provided is None or expected is None:
        return False
    try:
        return hmac.compare_digest(provided.encode("utf-8"), expected.encode("utf-8"))
    except Exception:
        return False


def generate_api_token(nbytes: int = 32) -> str:
    """Generate a cryptographically strong URL-safe API token."""
    return secrets.token_urlsafe(nbytes)


def resolve_api_key(
    explicit: Optional[str] = None,
    env_names: Tuple[str, ...] = ("API_KEY", "CLOUD_API_KEY"),
) -> str:
    """Resolve API key from constructor arg or environment (first non-empty)."""
    if explicit is not None and explicit.strip():
        return explicit.strip()
    for name in env_names:
        value = os.getenv(name, "")
        if value and value.strip():
            return value.strip()
    return ""


def validate_server_credentials(
    api_key: str,
    *,
    host: str = "127.0.0.1",
    secret_key: Optional[str] = None,
    service_name: str = "service",
) -> None:
    """
    Enforce safe defaults before binding a network service.

    Raises ValueError when credentials are too weak for the bind address
    unless FSB_ALLOW_INSECURE_MONITOR is set.
    """
    loopback = host in {"127.0.0.1", "localhost", "::1"}
    insecure_key = is_insecure_secret(api_key)
    insecure_secret = secret_key is not None and is_insecure_secret(secret_key)

    if not insecure_key and not insecure_secret:
        return

    if allow_insecure_mode():
        logger.warning(
            "%s starting with insecure credentials (FSB_ALLOW_INSECURE_MONITOR=1)",
            service_name,
        )
        return

    if not loopback:
        raise ValueError(
            f"{service_name}: strong API_KEY required when binding to {host}. "
            "Set API_KEY (min 16 chars) or FSB_ALLOW_INSECURE_MONITOR=1 for local testing only."
        )

    if insecure_key:
        logger.warning(
            "%s has no strong API key; localhost-only. Set API_KEY for authenticated access.",
            service_name,
        )
    if insecure_secret:
        logger.warning(
            "%s using weak API_SECRET_KEY; set a strong secret for JWT signing.",
            service_name,
        )
