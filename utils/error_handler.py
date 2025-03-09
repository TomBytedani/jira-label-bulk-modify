"""
Error handling utilities for the Jira Label Bulk Modify script.
"""
import sys
import logging
import json

logger = logging.getLogger("jira_label_bulk_modify")

class JiraAPIError(Exception):
    """Exception raised for errors in the Jira API responses."""
    def __init__(self, status_code, message, response_text=None):
        self.status_code = status_code
        self.message = message
        self.response_text = response_text
        super().__init__(self.message)


def handle_error(response, exit_on_critical=True):
    """
    Handle API error responses
    
    Args:
        response (requests.Response): Response object from API call
        exit_on_critical (bool): Whether to exit on critical errors
        
    Returns:
        bool: True if handled without exit, False otherwise
        
    Raises:
        SystemExit: If exit_on_critical is True and error is critical
    """
    error_code = response.status_code
    
    try:
        error_data = response.json()
        if "errorMessages" in error_data and error_data["errorMessages"]:
            error_message = error_data["errorMessages"][0]
        elif "errors" in error_data and error_data["errors"]:
            error_message = json.dumps(error_data["errors"])
        else:
            error_message = "Unknown error"
    except:
        error_message = response.text or "Unknown error"
    
    if error_code == 400:
        logger.error(f"Bad request: {error_message}")
    elif error_code == 401:
        logger.error("Authentication failed. Check credentials.")
    elif error_code == 403:
        logger.error(f"Permission denied: {error_message}")
    elif error_code == 404:
        logger.error(f"Resource not found: {error_message}")
    elif error_code == 409:
        logger.error(f"Conflict: {error_message}")
    elif error_code == 422:
        logger.error(f"Validation error: {error_message}")
    elif error_code == 429:
        logger.warning(f"Rate limit exceeded: {error_message}")
        # Handled separately in the calling function
        return True
    else:
        logger.error(f"API error {error_code}: {error_message}")
    
    # Determine if we should exit based on error type
    critical_errors = (401, 403)
    if exit_on_critical and error_code in critical_errors:
        sys.exit(f"Fatal error: {error_message}")
    
    return False


def retry_on_error(func):
    """
    Decorator to retry function calls on certain errors
    
    Args:
        func (callable): Function to retry
        
    Returns:
        callable: Wrapped function with retry logic
    """
    from functools import wraps
    import time
    from config import MAX_RETRIES, RATE_LIMIT_PAUSE
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        retries = 0
        while retries <= MAX_RETRIES:
            try:
                return func(*args, **kwargs)
            except JiraAPIError as e:
                if e.status_code == 429:  # Rate limit
                    retry_after = int(getattr(e, 'retry_after', RATE_LIMIT_PAUSE * 2))
                    logger.warning(f"Rate limit hit. Waiting {retry_after} seconds.")
                    time.sleep(retry_after)
                    continue
                elif retries < MAX_RETRIES:
                    wait_time = RATE_LIMIT_PAUSE * (2 ** retries)
                    logger.warning(f"API error: {e}. Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                    retries += 1
                else:
                    logger.error(f"Failed after {MAX_RETRIES} retries: {e}")
                    raise
            except Exception as e:
                if retries < MAX_RETRIES:
                    wait_time = RATE_LIMIT_PAUSE * (2 ** retries)
                    logger.warning(f"Unexpected error: {e}. Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                    retries += 1
                else:
                    logger.error(f"Failed after {MAX_RETRIES} retries: {e}")
                    raise
        
        raise Exception(f"Failed after {MAX_RETRIES} retries")
    
    return wrapper