"""
Security Module for Cloud Integration
Provides authentication, rate limiting, and enhanced security measures.
"""

import hashlib
import hmac
import time
import jwt
from typing import Dict, Optional
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify
import os
from dotenv import load_dotenv

# Ensure .env is loaded
load_dotenv(override=False)


class SecurityManager:
    """Manages security for cloud integration."""
    
    def __init__(self, secret_key: Optional[str] = None):
        """
        Initialize security manager.
        
        Args:
            secret_key: Secret key for JWT tokens
        """
        self.secret_key = secret_key or os.getenv('API_SECRET_KEY', 'default-secret-key-change-in-production')
        self.algorithm = 'HS256'
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
        payload = {
            'user_id': user_id,
            'permissions': permissions or [],
            'exp': datetime.utcnow() + self.token_expiry,
            'iat': datetime.utcnow()
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
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
            
    def hash_password(self, password: str) -> str:
        """
        Hash password using SHA-256.
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password
        """
        return hashlib.sha256(password.encode()).hexdigest()
        
    def verify_password(self, password: str, hashed: str) -> bool:
        """
        Verify password against hash.
        
        Args:
            password: Plain text password
            hashed: Hashed password
            
        Returns:
            True if password matches
        """
        return self.hash_password(password) == hashed
        
    def generate_api_key(self, user_id: str) -> str:
        """
        Generate API key for user.
        
        Args:
            user_id: User identifier
            
        Returns:
            API key string
        """
        timestamp = str(int(time.time()))
        data = f"{user_id}:{timestamp}"
        return hmac.new(
            self.secret_key.encode(),
            data.encode(),
            hashlib.sha256
        ).hexdigest()


class RateLimiter:
    """Rate limiting for API endpoints."""
    
    def __init__(self):
        self.requests: Dict[str, List[float]] = {}
        self.cleanup_interval = 3600  # 1 hour
        
    def check_rate_limit(self, identifier: str, max_requests: int, 
                        time_window: int) -> bool:
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
            
        # Remove old requests outside time window
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier]
            if current_time - req_time < time_window
        ]
        
        # Check if limit exceeded
        if len(self.requests[identifier]) >= max_requests:
            return False
            
        # Add current request
        self.requests[identifier].append(current_time)
        return True
        
    def get_remaining_requests(self, identifier: str, max_requests: int,
                              time_window: int) -> int:
        """Get remaining requests for identifier."""
        current_time = time.time()
        
        if identifier not in self.requests:
            return max_requests
            
        # Remove old requests
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier]
            if current_time - req_time < time_window
        ]
        
        return max(0, max_requests - len(self.requests[identifier]))


def require_auth(security_manager: SecurityManager):
    """Decorator for requiring authentication."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            auth_header = request.headers.get('Authorization', '')
            if not auth_header.startswith('Bearer '):
                return jsonify({'error': 'Missing or invalid authorization header'}), 401
                
            token = auth_header[7:]
            payload = security_manager.verify_token(token)
            if not payload:
                return jsonify({'error': 'Invalid or expired token'}), 401
                
            request.user_id = payload.get('user_id')
            request.permissions = payload.get('permissions', [])
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def require_permission(permission: str):
    """Decorator for requiring specific permission."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(request, 'permissions'):
                return jsonify({'error': 'Not authenticated'}), 401
                
            if permission not in request.permissions:
                return jsonify({'error': 'Insufficient permissions'}), 403
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator

