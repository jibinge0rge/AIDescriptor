# Cybersecurity Control Description Generator

This script generates structured, professional cybersecurity control documentation using AI based on a prompt template.

## Setup

1. Install required dependencies:
```bash
pip install -r requirements.txt
```

2. Set your Cursor API key. You can do this in one of three ways:

   **Option 1: Using a .env file (Recommended)**
   Create a `.env` file in the same directory as the script:
   ```bash
   CURSOR_API_KEY=your-cursor-api-key-here
   CURSOR_REPOSITORY=https://github.com/your-org/your-repo
   ```
   
   **Note:** The `CURSOR_REPOSITORY` is required if the chat completions endpoint is not available, as the Agent API requires a repository URL.
   
   **Option 2: Environment variable**
   ```bash
   export CURSOR_API_KEY="your-cursor-api-key-here"
   ```
   
   **Option 3: Command-line argument**
   Pass it using the `-k` flag (see Usage below).

**Note:** Get your Cursor API key from the [Cursor Dashboard](https://docs.cursor.com/en/background-agent/api/overview).

## Usage

### Basic usage:
```bash
python generate_descriptions.py sample_data.csv
```

### Specify output file:
```bash
python generate_descriptions.py sample_data.csv -o output.csv
```

### Pass API key as argument:
```bash
python generate_descriptions.py sample_data.csv -k "your-cursor-api-key"
```

### With custom API URL:
```bash
python generate_descriptions.py sample_data.csv -u "https://api.cursor.com"
```

### With repository context (for Agent API):
```bash
python generate_descriptions.py sample_data.csv -r "https://github.com/your-org/your-repo"
```

### With Excel files:
```bash
python generate_descriptions.py data.xlsx -o output.xlsx
```

## Input File Format

The input CSV or Excel file must have the following columns:
- `title`: The control title
- `description`: The original description

## Output

The script will:
1. Read the input file
2. For each row, generate an AI-enhanced description based on the prompt template
3. Add a new column `AI generated description` with the formatted output
4. Save the results to a new file (default: adds `_generated` to the input filename)

## Example

Input file (`sample_data.csv`):
```csv
title,description
Active Hosts Covered by Tanium...,Type is not 'Mobile' or 'Container'...
```

Output will include the original columns plus:
- `AI generated description`: Formatted output following the prompt template structure

## Notes

- The script uses the `prompt` file in the same directory as the template
- **API Usage**: The script first tries to use Cursor's chat completions endpoint (if available), and falls back to the Agent API if needed
- **Rate limiting**: A 2 second delay is added between API calls to avoid rate limits
- **Agent API**: If using the Agent API, the script will poll for completion (up to 5 minutes per request)
- **Repository**: The repository is **required** for the Agent API. Set it in `.env` as `CURSOR_REPOSITORY` or pass it with the `-r` flag. The repository should be a GitHub URL that the API can access.

