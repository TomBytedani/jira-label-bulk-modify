# Jira Label Bulk Modify

<div align="center">

![Jira](https://img.shields.io/badge/jira-%230A0FFF.svg?style=for-the-badge&logo=jira&logoColor=white)
![Python](https://img.shields.io/badge/python-3.6+-blue.svg?style=for-the-badge&logo=python&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-green.svg?style=for-the-badge)

**A Python tool to automate adding and removing labels across multiple Jira issues using JQL queries.**

</div>

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
- [Quick Start](#-quick-start)
- [Usage](#-usage)
  - [Command Line Options](#command-line-options)
  - [Input File Format](#input-file-format)
- [Output](#-output)
- [Project Structure](#-project-structure)
- [Development](#-development)
  - [Testing](#testing)
- [Security Considerations](#-security-considerations)
- [Troubleshooting](#-troubleshooting)
- [License](#-license)
- [Contributing](#-contributing)

## 🚀 Overview

This tool simplifies managing Jira labels across multiple issues, saving time and ensuring consistency with your labeling system. The script uses the Jira REST API to fetch, update, and track changes to issue labels.

## ✨ Features

- **Bulk Operations** - Add and remove labels across multiple issues simultaneously
- **JQL Filtering** - Select target issues using Jira Query Language (JQL)
- **Smart Processing**:
  - Automatically handles rate limiting
  - Manages API pagination for large result sets
  - Skips issues that don't need changes
- **Resumable Operations** - Progress tracking allows interrupted runs to continue
- **Batch Processing** - Group operations into logical batches with status tracking
- **Detailed Reporting** - Comprehensive logs and results files

## 🔧 Prerequisites

- Python 3.6+
- A Jira account with API access
- Appropriate permissions to modify issues

## 📥 Installation

1. **Clone the repository**

```bash
git clone https://github.com/yourusername/jira-label-bulk-modify.git
cd jira-label-bulk-modify
```

2. **Create a virtual environment** (recommended)

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Configure your Jira credentials**

Create a `.env` file in the project root:

```ini
JIRA_BASE_URL=https://your-domain.atlassian.net
JIRA_EMAIL=your-email@example.com
JIRA_API_TOKEN=your-api-token
```

> 🔑 You can generate an API token from your [Atlassian Account Security Settings](https://id.atlassian.com/manage/api-tokens).

## 🏃‍♂️ Quick Start

1. Create a `jql_queries.json` file with your batch configuration (see [Input File Format](#input-file-format))
2. Run the script:

```bash
python main.py
```

## 📖 Usage

### Command Line Options

```
usage: main.py [-h] [-i INPUT] [-b BATCH] [-d] [-f] [--skip-validation]

Bulk modify Jira issue labels based on JQL queries.

options:
  -h, --help            show this help message and exit
  -i INPUT, --input INPUT
                        Path to the input JSON file (default: jql_queries.json)
  -b BATCH, --batch BATCH
                        Process only the specified batch name(s), comma-separated
  -d, --dry-run         Perform a dry run without making actual changes
  -f, --force           Force processing of batches marked as DONE
  --skip-validation     Skip input validation
```
The speed at which each Edit issue call is made can be modified from the .env file, or directly in the config.py file. Currently it's set as 0.2, but if you encounter API limits, feel free to increase it.

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
  },
  {
    "batchName": "High priority issues",
    "add": ["Priority-High", "NeedsReview"],
    "remove": [],
    "query": "priority = High AND status = 'In Progress'",
    "status": "TO DO"
  }
]
```

**Fields explained:**
- `batchName`: Descriptive name used for logging and output files
- `add`: String or array of strings for labels to add
- `remove`: String or array of strings for labels to remove
- `query`: JQL query to select target issues
- `status`: "TO DO" or "DONE" to track progress. "DONE" batches won't be processed by the script.

## 📊 Output

The script generates several output files in the `output` directory:

- **Progress files** (`progress_BatchName_TIMESTAMP.json`): 
  - Track individual issue status during processing
  - Allow for resuming interrupted operations

- **Batch results** (`results_BatchName_TIMESTAMP.json`):
  - Detailed operation results for each batch
  - Contains success/failure status for each issue

- **Final summary** (`final_results_TIMESTAMP.json`):
  - Overall summary of all batch operations
  - Aggregated statistics on successful/failed/skipped issues

Detailed logs are saved to the `logs` directory with timestamps.

## 📁 Project Structure

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
└── main.py                   # Entry point
```

## 🔒 Security Considerations

- Never commit your `.env` file or expose your API token
- Keep SSL verification enabled (`VERIFY_SSL=True`) in production environments
- Use the Jira API token rather than your actual password
- The script follows Jira API best practices for authentication

## ❓ Troubleshooting

**Common Issues:**

1. **Rate Limiting Errors**
   - Increase `RATE_LIMIT_PAUSE` in `.env` file
   - Consider batch processing during off-peak hours

2. **Permission Errors**
   - Ensure your Jira account has permission to modify the target issues
   - Check that your API token is correctly configured

3. **Connection Issues**
   - Verify your network connection
   - Check that your Jira instance is accessible

For more help, check the logs in the `logs` directory or open an issue on GitHub.

## 📄 License

This project is licensed under the [MIT License](LICENSE).

## 👥 Contributing

Contributions are welcome! Here's how you can contribute:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

Please make sure to update tests as appropriate and follow the existing code style.

---

<div align="center">
  <p>Made with ❤️ for Jira admins everywhere</p>
</div>