"""
Security Module for Cloud Integration
Provides authentication, rate limiting, and enhanced security measures.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import os
import secrets
import time
from datetime import datetime, timedelta, timezone
from functools import wraps
from typing import Dict, List, Optional

import jwt
from dotenv import load_dotenv
from flask import jsonify, request

from .auth_utils import (
    constant_time_equals,
    extract_bearer_or_api_key,
    generate_api_token,
    is_insecure_secret,
)

load_dotenv(override=False)

logger = logging.getLogger(__name__)


class SecurityManager:
    """Manages security for cloud integration."""

    def __init__(self, secret_key: Optional[str] = None):
        """
        Initialize security manager.

        Args:
            secret_key: Secret key for JWT tokens
        """
        resolved = secret_key or os.getenv("API_SECRET_KEY", "")
        if is_insecure_secret(resolved):
            # Generate an ephemeral secret for this process so JWT still works
            # locally without baking a published default into tokens.
            resolved = secrets.token_urlsafe(48)
            logger.warning(
                "API_SECRET_KEY missing or weak; using ephemeral process secret. "
                "Set API_SECRET_KEY for stable tokens across restarts."
            )
        self.secret_key = resolved
        self.algorithm = "HS256"
        self.token_expiry = timedelta(hours=24)

    def generate_token(self, user_id: str, permissions: List[str] = None) -> str:
        """
        Generate JWT token.

        Args:
            user_id: User identifier
            permissions: List of permissions

        Returns:
            JWT token string
        """
        now = datetime.now(timezone.utc)
        payload = {
            "user_id": user_id,
            "permissions": permissions or [],
            "exp": now + self.token_expiry,
            "iat": now,
            "jti": secrets.token_hex(16),
            "iss": "forexsmartbot",
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, token: str) -> Optional[Dict]:
        """
        Verify JWT token.

        Args:
            token: JWT token string

        Returns:
            Decoded payload or None if invalid
        """
        try:
            return jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                options={"require": ["exp", "iat", "user_id"]},
            )
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    def hash_password(self, password: str, salt: Optional[str] = None) -> str:
        """
        Hash password using PBKDF2-HMAC-SHA256.

        Returns a string of the form ``salt$hash_hex``.
        """
        if salt is None:
            salt = secrets.token_hex(16)
        derived = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            200_000,
        )
        return f"{salt}${derived.hex()}"

    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against PBKDF2 or legacy SHA-256 hash."""
        if "$" in hashed:
            salt, _digest = hashed.split("$", 1)
            return constant_time_equals(self.hash_password(password, salt=salt), hashed)
        # Legacy SHA-256 (pre-3.2.5) — constant-time compare
        legacy = hashlib.sha256(password.encode("utf-8")).hexdigest()
        return constant_time_equals(legacy, hashed)

    def generate_api_key(self, user_id: str) -> str:
        """
        Generate API key for user.

        Args:
            user_id: User identifier

        Returns:
            API key string
        """
        # Prefer high-entropy token; include HMAC binding to user_id for auditability.
        nonce = generate_api_token(24)
        stamp = str(int(time.time()))
        digest = hmac.new(
            self.secret_key.encode("utf-8"),
            f"{user_id}:{stamp}:{nonce}".encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return f"fsb_{digest[:32]}_{nonce}"

    def verify_api_key(self, provided: Optional[str], expected: Optional[str]) -> bool:
        """Constant-time API key verification."""
        return constant_time_equals(provided, expected)


class RateLimiter:
    """Rate limiting for API endpoints."""

    def __init__(self):
        self.requests: Dict[str, List[float]] = {}
        self.cleanup_interval = 3600  # 1 hour

    def check_rate_limit(
        self, identifier: str, max_requests: int, time_window: int
    ) -> bool:
        """
        Check if request is within rate limit.

        Args:
            identifier: Request identifier (IP, user ID, etc.)
            max_requests: Maximum number of requests
            time_window: Time window in seconds

        Returns:
            True if within limit, False if exceeded
        """
        current_time = time.time()

        if identifier not in self.requests:
            self.requests[identifier] = []

        self.requests[identifier] = [
            req_time
            for req_time in self.requests[identifier]
            if current_time - req_time < time_window
        ]

        if len(self.requests[identifier]) >= max_requests:
            return False

        self.requests[identifier].append(current_time)
        return True

    def get_remaining_requests(
        self, identifier: str, max_requests: int, time_window: int
    ) -> int:
        """Get remaining requests for identifier."""
        current_time = time.time()

        if identifier not in self.requests:
            return max_requests

        self.requests[identifier] = [
            req_time
            for req_time in self.requests[identifier]
            if current_time - req_time < time_window
        ]

        return max(0, max_requests - len(self.requests[identifier]))


def require_auth(security_manager: SecurityManager):
    """Decorator for requiring JWT authentication."""

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            token = extract_bearer_or_api_key(
                request.headers.get("Authorization", ""),
                request.headers.get("X-API-Key", ""),
            )
            if not token:
                return jsonify({"error": "Missing or invalid authorization header"}), 401

            payload = security_manager.verify_token(token)
            if not payload:
                return jsonify({"error": "Invalid or expired token"}), 401

            request.user_id = payload.get("user_id")
            request.permissions = payload.get("permissions", [])
            return f(*args, **kwargs)

        return decorated_function

    return decorator


def require_permission(permission: str):
    """Decorator for requiring specific permission."""

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(request, "permissions"):
                return jsonify({"error": "Not authenticated"}), 401

            if permission not in request.permissions:
                return jsonify({"error": "Insufficient permissions"}), 403

            return f(*args, **kwargs)

        return decorated_function

    return decorator
