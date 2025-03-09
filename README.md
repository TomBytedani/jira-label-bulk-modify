# Jira Label Bulk Modify

A Python script for automating the process of adding and removing labels across multiple Jira issues based on JQL queries.

## Features

- Bulk add and remove labels across multiple Jira issues
- Select issues using JQL (Jira Query Language) queries
- Automatically handle rate limiting and API pagination
- Detailed logging and error handling
- Progress tracking for resumable operations
- Batch processing with status tracking

## Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/jira-label-bulk-modify.git
cd jira-label-bulk-modify
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project root with your Jira credentials:

```
JIRA_BASE_URL=https://your-domain.atlassian.net
JIRA_EMAIL=your-email@example.com
JIRA_API_TOKEN=your-api-token
```

You can generate an API token from your [Atlassian Account Security Settings](https://id.atlassian.com/manage/api-tokens).

## Usage

### Basic Usage

```bash
python main.py
```

This will read `jql_queries.json` in the current directory and process all batches with status "TO DO".

### Command Line Options

```
usage: main.py [-h] [-i INPUT] [-b BATCH] [-d] [-f] [--skip-validation]

Bulk modify Jira issue labels based on JQL queries.

optional arguments:
  -h, --help            show this help message and exit
  -i INPUT, --input INPUT
                        Path to the input JSON file (default: jql_queries.json)
  -b BATCH, --batch BATCH
                        Process only the specified batch name(s), comma-separated
  -d, --dry-run         Perform a dry run without making actual changes
  -f, --force           Force processing of batches marked as DONE
  --skip-validation     Skip input validation
```

### Input File Format

Create a `jql_queries.json` file with the following structure:

```json
[
    {
        "batchName": "Test cases for Wave 3",
        "add": "NewLabel",
        "remove": "OldLabel",
        "query": "issue in (38659,38658,12345)",
        "status": "TO DO"
    },
    {
        "batchName": "Query with various issue types",
        "add": ["NRT", "SecondLabel", "ThirdLabel"],
        "remove": ["SIT", "SecondLabelToRemove"],
        "query": "project = 'TEST' AND created > -30d",
        "status": "TO DO"
    }
]
```

Where:
- `batchName`: Name used for logging and output file identification
- `add`: String or array of strings for labels to add
- `remove`: String or array of strings for labels to remove
- `query`: JQL query to select issues
- `status`: "TO DO" or "DONE" to track progress

## Output

The script generates several output files in the `output` directory:

- Progress files for each batch tracking individual issue status
- Results files for each batch with detailed operation results
- A final results file with an overall summary

Log files are saved in the `logs` directory.

## Development

### Project Structure

```
jira-label-bulk-modify/
├── README.md
├── requirements.txt
├── config.py                 # Configuration settings
├── jira_api.py               # Jira API client
├── label_processor.py        # Core label processing logic
├── utils/
│   ├── __init__.py
│   ├── input_validator.py    # Input validation 
│   ├── logger.py             # Logging setup
│   └── error_handler.py      # Error handling utilities
├── tests/                    # Test suite
│   ├── __init__.py
│   ├── test_integration.py
│   └── test_unit.py
└── main.py                   # Entry point
```

### Testing

Run unit tests:

```bash
python -m unittest discover tests
```

### Security Considerations

- Never commit your `.env` file or expose your API token
- Keep SSL verification enabled (VERIFY_SSL=True) in production environments
- Use the Jira API token rather than your actual password

## License

[MIT License](LICENSE)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.