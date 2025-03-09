#!/usr/bin/env python3
"""
Jira Label Bulk Modify - Main Entry Point

This script automates the process of adding and removing labels across multiple
Jira issues based on JQL queries.
"""
import sys
import argparse
import json
import os
from datetime import datetime

# Set up logging before other imports
from utils.logger import setup_logger
logger = setup_logger()

from config import DEFAULT_INPUT_FILE, OUTPUT_DIR
from utils.input_validator import load_and_validate_input
from label_processor import LabelProcessor


def parse_arguments():
    """
    Parse command line arguments
    
    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Bulk modify Jira issue labels based on JQL queries."
    )
    
    parser.add_argument(
        "-i", "--input", 
        default=DEFAULT_INPUT_FILE,
        help=f"Path to the input JSON file (default: {DEFAULT_INPUT_FILE})"
    )
    
    parser.add_argument(
        "-b", "--batch", 
        help="Process only the specified batch name(s), comma-separated"
    )
    
    parser.add_argument(
        "-d", "--dry-run",
        action="store_true",
        help="Perform a dry run without making actual changes"
    )
    
    parser.add_argument(
        "-f", "--force",
        action="store_true",
        help="Force processing of batches marked as DONE"
    )
    
    parser.add_argument(
        "--skip-validation",
        action="store_true",
        help="Skip input validation"
    )
    
    return parser.parse_args()


def main():
    """Main entry point"""
    args = parse_arguments()
    
    logger.info("Jira Label Bulk Modify script starting...")
    logger.info(f"Input file: {args.input}")
    
    # Load and validate input
    try:
        if args.skip_validation:
            logger.warning("Skipping input validation")
            with open(args.input, 'r') as f:
                batches = json.load(f)
        else:
            batches = load_and_validate_input(args.input)
    except Exception as e:
        logger.error(f"Failed to load input file: {e}")
        sys.exit(1)
    
    # Filter batches if batch argument provided
    if args.batch:
        batch_names = [name.strip() for name in args.batch.split(",")]
        batches = [batch for batch in batches if batch["batchName"] in batch_names]
        if not batches:
            logger.error(f"No batches found matching: {batch_names}")
            sys.exit(1)
        logger.info(f"Processing {len(batches)} specified batch(es)")
    
    # Force processing of DONE batches if requested
    if args.force:
        logger.info("Force flag set, processing all batches regardless of status")
        for batch in batches:
            if batch["status"] == "DONE":
                batch["status"] = "TO DO"
    
    # Filter out DONE batches
    unprocessed_batches = [batch for batch in batches if batch["status"] == "TO DO"]
    if not unprocessed_batches:
        logger.warning("No unprocessed batches found. Use --force to reprocess.")
        sys.exit(0)
    
    logger.info(f"Found {len(unprocessed_batches)} unprocessed batch(es)")
    
    # Print batch summary
    for i, batch in enumerate(unprocessed_batches):
        logger.info(f"Batch {i+1}: {batch['batchName']}")
        logger.info(f"  Query: {batch['query']}")
        logger.info(f"  Add: {batch.get('add', [])}")
        logger.info(f"  Remove: {batch.get('remove', [])}")
    
    # Dry run check
    if args.dry_run:
        logger.info("DRY RUN MODE: No changes will be made to Jira issues")
        sys.exit(0)
    
    # Process batches
    processor = LabelProcessor()
    
    try:
        results = processor.process_all_batches(batches, args.input)
        
        # Save overall results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = os.path.join(OUTPUT_DIR, f"final_results_{timestamp}.json")
        
        with open(results_file, "w") as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Processing completed. Results saved to {results_file}")
        logger.info(f"Summary: {results['successful_issues']} successful, "
                   f"{results['failed_issues']} failed, "
                   f"{results['skipped_issues']} skipped issues")
        
    except Exception as e:
        logger.error(f"Error during batch processing: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()