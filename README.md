# Cybersecurity Control Description Generator

This script generates structured, professional cybersecurity control documentation using OpenAI's API based on a prompt template.

## Setup

1. Install required dependencies:
```bash
pip install -r requirements.txt
```

2. Set your OpenAI API key. You can do this in one of three ways:

   **Option 1: Using a .env file (Recommended)**
   Create a `.env` file in the same directory as the script:
   ```bash
   OPENAI_API_KEY=your-openai-api-key-here
   ```
   
   **Option 2: Environment variable**
   ```bash
   export OPENAI_API_KEY="your-openai-api-key-here"
   ```
   
   **Option 3: Command-line argument**
   Pass it using the `-k` flag (see Usage below).

**Note:** Get your OpenAI API key from the [OpenAI Platform](https://platform.openai.com/api-keys). You'll need to create an account and add billing information.

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
python generate_descriptions.py sample_data.csv -k "your-openai-api-key"
```

### Specify a different model:
```bash
python generate_descriptions.py sample_data.csv -m "gpt-4o"
```

Available models include:
- `gpt-4o-mini` (default, cost-effective)
- `gpt-4o` (more capable)
- `gpt-4-turbo` (high performance)
- `gpt-3.5-turbo` (legacy, cheaper)

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
- **API Usage**: The script uses OpenAI's Chat Completions API
- **Rate limiting**: A 1 second delay is added between API calls to avoid rate limits
- **Cost**: API usage will incur costs based on OpenAI's pricing. `gpt-4o-mini` is the most cost-effective option.
- **Model selection**: Use `-m` flag to choose a different model. More capable models cost more but may produce better results.
