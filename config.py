"""
Configuration settings for the Jira Label Bulk Modify script.
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Jira API Configuration
JIRA_BASE_URL = os.getenv("JIRA_BASE_URL", "https://your-domain.atlassian.net")
JIRA_EMAIL = os.getenv("JIRA_EMAIL", "email@example.com")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN", "")
API_VERSION = os.getenv("API_VERSION", "3")

# Request settings
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))
RATE_LIMIT_PAUSE = float(os.getenv("RATE_LIMIT_PAUSE", "1"))  # seconds between requests
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
VERIFY_SSL = os.getenv("VERIFY_SSL", "True").lower() in ("true", "1", "t")

# Batch processing
MAX_RESULTS_PER_PAGE = int(os.getenv("MAX_RESULTS_PER_PAGE", "100"))

# Paths
DEFAULT_INPUT_FILE = os.getenv("DEFAULT_INPUT_FILE", "jql_queries.json")
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "output")
LOG_DIR = os.getenv("LOG_DIR", "logs")

# Ensure the output and log directories exist
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)