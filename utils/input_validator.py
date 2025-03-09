"""
Input validation utilities for the Jira Label Bulk Modify script.
"""
import json
import sys
import jsonschema
import logging

logger = logging.getLogger("jira_label_bulk_modify")

# Schema for the input JSON file
INPUT_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "required": ["batchName", "query", "status"],
        "properties": {
            "batchName": {"type": "string"},
            "add": {
                "oneOf": [
                    {"type": "string"},
                    {"type": "array", "items": {"type": "string"}},
                    {"type": "null"}
                ]
            },
            "remove": {
                "oneOf": [
                    {"type": "string"},
                    {"type": "array", "items": {"type": "string"}},
                    {"type": "null"}
                ]
            },
            "query": {"type": "string"},
            "status": {"type": "string", "enum": ["TO DO", "DONE"]}
        }
    }
}


def load_and_validate_input(file_path):
    """
    Load and validate the input JSON file
    
    Args:
        file_path (str): Path to the input JSON file
        
    Returns:
        list: List of validated batch objects
        
    Raises:
        SystemExit: If validation fails
    """
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Validate against schema
        jsonschema.validate(instance=data, schema=INPUT_SCHEMA)
        
        # Additional validation and normalization
        for batch in data:
            batch["add"] = normalize_labels(batch.get("add", []))
            batch["remove"] = normalize_labels(batch.get("remove", []))
            
            # Check for labels with spaces
            all_labels = batch["add"] + batch["remove"]
            labels_with_spaces = [label for label in all_labels if " " in label]
            
            if labels_with_spaces:
                handle_labels_with_spaces(labels_with_spaces, batch)
        
        return data
    
    except FileNotFoundError:
        logger.error(f"Input file not found: {file_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in input file: {e}")
        sys.exit(1)
    except jsonschema.exceptions.ValidationError as e:
        logger.error(f"Input validation error: {e}")
        sys.exit(1)


def normalize_labels(labels):
    """
    Normalize labels to list format
    
    Args:
        labels (str, list, None): Labels to normalize
        
    Returns:
        list: Normalized list of labels
    """
    if labels is None:
        return []
    elif isinstance(labels, str):
        return [labels] if labels.strip() else []
    elif isinstance(labels, list):
        return [label for label in labels if isinstance(label, str) and label.strip()]
    return []


def handle_labels_with_spaces(labels_with_spaces, batch):
    """
    Handle labels with spaces based on user input
    
    Args:
        labels_with_spaces (list): List of labels containing spaces
        batch (dict): Batch object to modify
        
    Returns:
        None: Modifies batch in place
    """
    logger.warning(f"The following labels contain spaces: {', '.join(labels_with_spaces)}")
    logger.warning("Jira labels cannot contain spaces. Choose an action:")
    logger.warning("1. Strip spaces (e.g., 'My Label' becomes 'MyLabel')")
    logger.warning("2. Replace spaces with underscores (e.g., 'My Label' becomes 'My_Label')")
    logger.warning("3. Skip these labels")
    logger.warning("4. Abort")
    
    valid_choices = {"1", "2", "3", "4"}
    choice = None
    
    while choice not in valid_choices:
        choice = input("Enter your choice (1-4): ")
        if choice not in valid_choices:
            print("Invalid choice. Please enter 1, 2, 3, or 4.")
    
    if choice == "1":  # Strip spaces
        batch["add"] = [label.replace(" ", "") for label in batch["add"]]
        batch["remove"] = [label.replace(" ", "") for label in batch["remove"]]
        logger.info("Spaces stripped from labels.")
    
    elif choice == "2":  # Replace with underscores
        batch["add"] = [label.replace(" ", "_") for label in batch["add"]]
        batch["remove"] = [label.replace(" ", "_") for label in batch["remove"]]
        logger.info("Spaces replaced with underscores.")
    
    elif choice == "3":  # Skip
        batch["add"] = [label for label in batch["add"] if " " not in label]
        batch["remove"] = [label for label in batch["remove"] if " " not in label]
        logger.info("Labels with spaces skipped.")
    
    else:  # Abort
        logger.error("Aborting due to labels with spaces")
        sys.exit(1)


def save_updated_input(data, file_path):
    """
    Save the updated input data back to the file
    
    Args:
        data (list): Updated batch data
        file_path (str): Path to save the updated data
        
    Returns:
        None
    """
    try:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Updated input file saved to {file_path}")
    except Exception as e:
        logger.error(f"Failed to save updated input file: {e}")