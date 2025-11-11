"""
Error Handling for Cloud Integration
Provides enhanced error handling for external APIs and cloud services.
"""

import logging
import traceback
from typing import Dict, Optional, Callable
from functools import wraps
from datetime import datetime
import requests


class CloudErrorHandler:
    """Enhanced error handling for cloud operations."""
    
    def __init__(self, max_retries: int = 3, retry_delay: float = 1.0):
        """
        Initialize error handler.
        
        Args:
            max_retries: Maximum number of retries
            retry_delay: Delay between retries in seconds
        """
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.logger = logging.getLogger(__name__)
        
    def handle_api_error(self, func: Callable):
        """Decorator for handling API errors with retries."""
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(self.max_retries):
                try:
                    return func(*args, **kwargs)
                except requests.exceptions.Timeout as e:
                    last_exception = e
                    self.logger.warning(f"API timeout (attempt {attempt + 1}/{self.max_retries}): {e}")
                    if attempt < self.max_retries - 1:
                        import time
                        time.sleep(self.retry_delay * (attempt + 1))
                except requests.exceptions.ConnectionError as e:
                    last_exception = e
                    self.logger.warning(f"Connection error (attempt {attempt + 1}/{self.max_retries}): {e}")
                    if attempt < self.max_retries - 1:
                        import time
                        time.sleep(self.retry_delay * (attempt + 1))
                except requests.exceptions.HTTPError as e:
                    # Don't retry on client errors (4xx)
                    if e.response.status_code < 500:
                        self.logger.error(f"Client error: {e}")
                        raise
                    last_exception = e
                    self.logger.warning(f"Server error (attempt {attempt + 1}/{self.max_retries}): {e}")
                    if attempt < self.max_retries - 1:
                        import time
                        time.sleep(self.retry_delay * (attempt + 1))
                except Exception as e:
                    self.logger.error(f"Unexpected error: {e}")
                    self.logger.debug(traceback.format_exc())
                    raise
                    
            # All retries failed
            self.logger.error(f"All retries failed: {last_exception}")
            raise last_exception
            
        return wrapper
        
    def handle_websocket_error(self, func: Callable):
        """Decorator for handling WebSocket errors."""
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                self.logger.error(f"WebSocket error: {e}")
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
            'error_type': type(error).__name__,
            'error_message': str(error),
            'timestamp': datetime.now().isoformat(),
            'context': context or {}
        }
        
        self.logger.error(f"Error occurred: {error_info}")
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
                'status': 'healthy' if status else 'unhealthy',
                'last_check': datetime.now().isoformat(),
                'available': status
            }
            return self.health_status[service_name]
        except Exception as e:
            self.health_status[service_name] = {
                'status': 'error',
                'last_check': datetime.now().isoformat(),
                'available': False,
                'error': str(e)
            }
            self.logger.error(f"Health check failed for {service_name}: {e}")
            return self.health_status[service_name]
            
    def get_all_health_status(self) -> Dict:
        """Get health status of all services."""
        return self.health_status
        
    def is_service_healthy(self, service_name: str) -> bool:
        """Check if a service is healthy."""
        if service_name not in self.health_status:
            return False
        return self.health_status[service_name].get('available', False)

