"""
Jira API client for the Label Bulk Modify script.
"""
import time
import logging
import requests
from requests.auth import HTTPBasicAuth
import json

from config import (
    JIRA_BASE_URL, 
    JIRA_EMAIL, 
    JIRA_API_TOKEN, 
    API_VERSION,
    REQUEST_TIMEOUT, 
    RATE_LIMIT_PAUSE,
    VERIFY_SSL,
    MAX_RESULTS_PER_PAGE
)
from utils.error_handler import handle_error, retry_on_error, JiraAPIError

logger = logging.getLogger("jira_label_bulk_modify")

class JiraApiClient:
    """Client for interacting with the Jira API"""
    
    def __init__(self):
        """Initialize the Jira API client"""
        self.base_url = JIRA_BASE_URL
        self.auth = HTTPBasicAuth(JIRA_EMAIL, JIRA_API_TOKEN)
        self.api_version = API_VERSION
        self.timeout = REQUEST_TIMEOUT
        self.verify_ssl = VERIFY_SSL
        
        # Cache for issue type editability
        self.editability_cache = {}
        
        # Request headers
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
    
    @retry_on_error
    def execute_jql_query(self, jql_query):
        """
        Execute JQL query and return matching issues
        
        Args:
            jql_query (str): JQL query string
            
        Returns:
            list: List of issue objects with id, key, and type
            
        Raises:
            JiraAPIError: If the API request fails
        """
        url = f"{self.base_url}/rest/api/{self.api_version}/search"
        
        start_at = 0
        max_results = MAX_RESULTS_PER_PAGE
        total_issues = []
        
        logger.info(f"Executing JQL query: {jql_query}")
        
        while True:
            params = {
                "jql": jql_query,
                "fields": "issuetype,labels",
                "startAt": start_at,
                "maxResults": max_results
            }
            
            response = requests.get(
                url,
                params=params,
                auth=self.auth,
                headers={"Accept": "application/json"},
                timeout=self.timeout,
                verify=self.verify_ssl
            )
            
            if response.status_code != 200:
                handle_error(response, exit_on_critical=False)
                raise JiraAPIError(
                    response.status_code,
                    f"Failed to execute JQL query",
                    response.text
                )
            
            data = response.json()
            
            if "issues" not in data:
                logger.warning("No 'issues' found in API response")
                break
                
            total_issues.extend(data["issues"])
            
            logger.info(f"Retrieved {len(data['issues'])} issues (total so far: {len(total_issues)})")
            
            if start_at + max_results >= data["total"]:
                logger.info(f"All {data['total']} issues retrieved")
                break
                
            start_at += max_results
            
            # Add delay to avoid rate limiting
            time.sleep(RATE_LIMIT_PAUSE)
        
        return [
            {
                "id": issue["id"],
                "key": issue["key"],
                "type": issue["fields"]["issuetype"]["name"],
                "currentLabels": issue["fields"].get("labels", [])
            }
            for issue in total_issues
        ]
    
    @retry_on_error
    def check_label_editability(self, issue_key, issue_type):
        """
        Check if labels can be edited for the issue
        
        Args:
            issue_key (str): Issue key
            issue_type (str): Issue type
            
        Returns:
            bool: True if labels can be edited, False otherwise
            
        Raises:
            JiraAPIError: If the API request fails
        """
        # Check cache first to avoid redundant API calls
        if issue_type in self.editability_cache:
            return self.editability_cache[issue_type]
        
        url = f"{self.base_url}/rest/api/{self.api_version}/issue/{issue_key}/editmeta"
        
        logger.debug(f"Checking label editability for issue type: {issue_type}")
        
        response = requests.get(
            url,
            auth=self.auth,
            headers={"Accept": "application/json"},
            timeout=self.timeout,
            verify=self.verify_ssl
        )
        
        if response.status_code != 200:
            handle_error(response, exit_on_critical=False)
            raise JiraAPIError(
                response.status_code,
                f"Failed to get edit metadata for issue {issue_key}",
                response.text
            )
        
        data = response.json()
        
        # Check if labels field exists and supports necessary operations
        can_edit_labels = False
        if "fields" in data and "labels" in data["fields"]:
            operations = data["fields"]["labels"].get("operations", [])
            can_edit_labels = "add" in operations and "remove" in operations
        
        # Cache the result for this issue type
        self.editability_cache[issue_type] = can_edit_labels
        
        logger.debug(f"Label editability for {issue_type}: {can_edit_labels}")
        return can_edit_labels
    
    @retry_on_error
    def modify_issue_labels(self, issue_key, labels_to_add, labels_to_remove):
        """
        Modify labels for an issue
        
        Args:
            issue_key (str): Issue key
            labels_to_add (list): Labels to add
            labels_to_remove (list): Labels to remove
            
        Returns:
            bool: True if successful, False otherwise
            
        Raises:
            JiraAPIError: If the API request fails
        """
        url = f"{self.base_url}/rest/api/{self.api_version}/issue/{issue_key}"
        
        # Prepare update operations
        update = {"labels": []}
        
        # Add labels
        for label in labels_to_add:
            update["labels"].append({"add": label})
        
        # Remove labels
        for label in labels_to_remove:
            update["labels"].append({"remove": label})
        
        # Prepare request body
        payload = {
            "update": update
        }
        
        logger.debug(f"Modifying labels for issue {issue_key}: add={labels_to_add}, remove={labels_to_remove}")
        
        response = requests.put(
            url,
            json=payload,
            auth=self.auth,
            headers=self.headers,
            timeout=self.timeout,
            verify=self.verify_ssl
        )
        
        # Check for rate limiting
        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", RATE_LIMIT_PAUSE * 2))
            raise JiraAPIError(
                response.status_code,
                f"Rate limit hit for issue {issue_key}",
                retry_after=retry_after
            )
        
        # Handle other errors
        if response.status_code not in (200, 204):
            handle_error(response, exit_on_critical=False)
            raise JiraAPIError(
                response.status_code,
                f"Failed to modify labels for issue {issue_key}",
                response.text
            )
        
        logger.info(f"Successfully modified labels for issue {issue_key}")
        return True