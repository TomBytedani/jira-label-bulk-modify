"""
Core label processing logic for the Jira Label Bulk Modify script.
"""
import os
import json
import logging
from datetime import datetime
import time
from tqdm import tqdm

from config import OUTPUT_DIR
from jira_api import JiraApiClient
from utils.input_validator import save_updated_input

logger = logging.getLogger("jira_label_bulk_modify")

class LabelProcessor:
    """Process batches of label operations"""
    
    def __init__(self):
        """Initialize the label processor"""
        self.jira_api = JiraApiClient()
    
    def process_all_batches(self, batches, input_file_path):
        """
        Process all batches from the input file
        
        Args:
            batches (list): List of batch objects
            input_file_path (str): Path to the input file for updating status
            
        Returns:
            dict: Summary of processing results
        """
        results = {
            "total_batches": len(batches),
            "completed_batches": 0,
            "skipped_batches": 0,
            "failed_batches": 0,
            "total_issues": 0,
            "successful_issues": 0,
            "skipped_issues": 0,
            "failed_issues": 0,
            "batches": []
        }
        
        for i, batch in enumerate(batches):
            logger.info(f"Processing batch {i+1}/{len(batches)}: {batch['batchName']}")
            
            # Skip already processed batches
            if batch["status"] == "DONE":
                logger.info(f"Batch '{batch['batchName']}' already processed, skipping")
                results["skipped_batches"] += 1
                continue
            
            # Process the batch
            try:
                batch_result = self.process_batch(batch)
                
                # Update batch status
                batch["status"] = "DONE"
                
                # Save updated status
                save_updated_input(batches, input_file_path)
                
                results["completed_batches"] += 1
                results["total_issues"] += batch_result["total_issues"]
                results["successful_issues"] += batch_result["successful_issues"]
                results["skipped_issues"] += batch_result["skipped_issues"]
                results["failed_issues"] += batch_result["failed_issues"]
                
                results["batches"].append({
                    "name": batch["batchName"],
                    "result": "success",
                    "details": batch_result
                })
                
            except Exception as e:
                logger.error(f"Failed to process batch '{batch['batchName']}': {e}")
                results["failed_batches"] += 1
                results["batches"].append({
                    "name": batch["batchName"],
                    "result": "failure",
                    "error": str(e)
                })
        
        return results
    
    def process_batch(self, batch):
        """
        Process a single batch of label operations
        
        Args:
            batch (dict): Batch object with query and label operations
            
        Returns:
            dict: Results of batch processing
        """
        batch_name = batch["batchName"]
        jql_query = batch["query"]
        labels_to_add = batch.get("add", [])
        labels_to_remove = batch.get("remove", [])
        
        logger.info(f"Starting batch: {batch_name}")
        logger.info(f"JQL Query: {jql_query}")
        logger.info(f"Labels to add: {labels_to_add}")
        logger.info(f"Labels to remove: {labels_to_remove}")
        
        # Create progress file path
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        progress_file = os.path.join(
            OUTPUT_DIR, 
            f"progress_{batch_name.replace(' ', '_')}_{timestamp}.json"
        )
        
        # Get issues from JQL
        issues = self.jira_api.execute_jql_query(jql_query)
        logger.info(f"Found {len(issues)} issues matching the query")
        
        # Load progress if exists
        progress = {}
        
        # Process issues
        results = {
            "total_issues": len(issues),
            "successful_issues": 0,
            "skipped_issues": 0,
            "failed_issues": 0,
            "issues": {}
        }
        
        # Process each issue with progress bar
        for issue in tqdm(issues, desc=f"Processing {batch_name}", unit="issue"):
            issue_key = issue["key"]
            issue_type = issue["type"]
            current_labels = issue["currentLabels"]
            
            # Skip already processed issues
            if issue_key in progress and progress[issue_key]["status"] == "DONE":
                logger.debug(f"Issue {issue_key} already processed, skipping")
                results["skipped_issues"] += 1
                results["issues"][issue_key] = {
                    "status": "SKIPPED",
                    "reason": "Already processed"
                }
                continue
            
            # Check if we need to modify any labels
            actual_labels_to_add = [label for label in labels_to_add if label not in current_labels]
            actual_labels_to_remove = [label for label in labels_to_remove if label in current_labels]
            
            if not actual_labels_to_add and not actual_labels_to_remove:
                logger.debug(f"No label changes needed for issue {issue_key}")
                results["skipped_issues"] += 1
                results["issues"][issue_key] = {
                    "status": "SKIPPED",
                    "reason": "No label changes needed"
                }
                continue
            
            # Check if labels can be edited
            try:
                if not self.jira_api.check_label_editability(issue_key, issue_type):
                    logger.warning(f"Labels not editable for issue {issue_key} (type: {issue_type})")
                    results["skipped_issues"] += 1
                    results["issues"][issue_key] = {
                        "status": "SKIPPED",
                        "reason": "Labels not editable"
                    }
                    continue
            except Exception as e:
                logger.error(f"Error checking label editability for issue {issue_key}: {e}")
                results["failed_issues"] += 1
                results["issues"][issue_key] = {
                    "status": "FAILED",
                    "error": str(e)
                }
                continue
            
            # Process labels
            try:
                success = self.jira_api.modify_issue_labels(
                    issue_key, 
                    actual_labels_to_add,
                    actual_labels_to_remove
                )
                
                if success:
                    results["successful_issues"] += 1
                    results["issues"][issue_key] = {
                        "status": "SUCCESS",
                        "added": actual_labels_to_add,
                        "removed": actual_labels_to_remove
                    }
                else:
                    results["failed_issues"] += 1
                    results["issues"][issue_key] = {
                        "status": "FAILED",
                        "error": "Unknown error"
                    }
            except Exception as e:
                logger.error(f"Error modifying labels for issue {issue_key}: {e}")
                results["failed_issues"] += 1
                results["issues"][issue_key] = {
                    "status": "FAILED",
                    "error": str(e)
                }
            
            # Update progress
            progress[issue_key] = {
                "status": "DONE" if results["issues"][issue_key]["status"] == "SUCCESS" else "FAILED",
                "timestamp": datetime.now().isoformat()
            }
            
            # Save progress periodically
            if len(progress) % 10 == 0:
                with open(progress_file, "w") as f:
                    json.dump(progress, f, indent=2)
        
        # Save final progress
        with open(progress_file, "w") as f:
            json.dump(progress, f, indent=2)
        
        # Save detailed results
        results_file = os.path.join(
            OUTPUT_DIR, 
            f"results_{batch_name.replace(' ', '_')}_{timestamp}.json"
        )
        with open(results_file, "w") as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Batch '{batch_name}' completed")
        logger.info(f"Total issues: {results['total_issues']}")
        logger.info(f"Successful: {results['successful_issues']}")
        logger.info(f"Skipped: {results['skipped_issues']}")
        logger.info(f"Failed: {results['failed_issues']}")
        logger.info(f"Results saved to {results_file}")
        
        return results