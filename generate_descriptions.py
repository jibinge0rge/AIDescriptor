#!/usr/bin/env python3
"""
Script to generate AI-enhanced descriptions for cybersecurity control documentation.
Reads Excel/CSV files with 'title' and 'description' columns and generates
structured descriptions using AI based on the prompt template.
"""

import pandas as pd
import os
import sys
from pathlib import Path
import requests
import time
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Read the prompt template
def load_prompt_template():
    """Load the prompt template from the prompt file."""
    prompt_file = Path(__file__).parent / "prompt"
    if not prompt_file.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_file}")
    return prompt_file.read_text()


def generate_description(title, description, prompt_template, api_key, api_url=None, repository=None):
    """
    Generate AI description using Cursor API.
    
    Args:
        title: The control title
        description: The original description
        prompt_template: The prompt template text
        api_key: Cursor API key
        api_url: Cursor API base URL (default: https://api.cursor.com)
        repository: Optional repository URL for agent context
    
    Returns:
        Generated description string
    """
    # Construct the full prompt
    full_prompt = f"""{prompt_template}

Title: {title}

Description: {description}

Please generate the formatted output according to the format specified above."""

    # Default API URL
    if not api_url:
        api_url = "https://api.cursor.com"
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    try:
        # Try using chat completions endpoint first (simpler approach)
        chat_url = f"{api_url}/v1/chat/completions"
        payload = {
            "model": "gpt-4",
            "messages": [
                {"role": "system", "content": "You are a cybersecurity documentation specialist. Generate structured, professional control documentation in the exact format specified."},
                {"role": "user", "content": full_prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 2000
        }
        
        response = requests.post(chat_url, headers=headers, json=payload, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            return result.get('choices', [{}])[0].get('message', {}).get('content', '').strip()
        elif response.status_code == 404:
            # If chat completions doesn't exist, try Agent API
            if not repository:
                return f"Error: Chat completions endpoint not available and repository not provided. Agent API requires a repository. Please provide a repository URL using -r flag or set CURSOR_REPOSITORY in .env file."
            return generate_description_with_agent(title, description, prompt_template, api_key, api_url, repository)
        else:
            # Try Agent API as fallback
            if not repository:
                return f"Error: Chat completions failed (status {response.status_code}) and repository not provided. Agent API requires a repository. Please provide a repository URL using -r flag or set CURSOR_REPOSITORY in .env file."
            return generate_description_with_agent(title, description, prompt_template, api_key, api_url, repository)
            
    except requests.exceptions.RequestException as e:
        # If chat endpoint fails, try Agent API
        if not repository:
            return f"Error: Chat endpoint failed and repository not provided. Agent API requires a repository. Please provide a repository URL using -r flag or set CURSOR_REPOSITORY in .env file. Original error: {str(e)}"
        try:
            return generate_description_with_agent(title, description, prompt_template, api_key, api_url, repository)
        except Exception as agent_error:
            return f"Error generating description: {str(e)} (Agent API also failed: {str(agent_error)})"
    except Exception as e:
        return f"Error generating description: {str(e)}"


def generate_description_with_agent(title, description, prompt_template, api_key, api_url, repository):
    """
    Generate description using Cursor Agent API (more complex, requires polling).
    
    Args:
        title: The control title
        description: The original description
        prompt_template: The prompt template text
        api_key: Cursor API key
        api_url: Cursor API base URL
        repository: Optional repository URL
    
    Returns:
        Generated description string
    """
    full_prompt = f"""{prompt_template}

Title: {title}

Description: {description}

Please generate the formatted output according to the format specified above."""

    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    # Agent API endpoint
    agents_url = f"{api_url}/v0/agents"
    
    # Prepare payload for agent creation
    # Note: Cursor Agent API requires a 'source' field
    if not repository:
        raise Exception("Repository is required for Cursor Agent API. Please provide a repository URL using -r flag or set CURSOR_REPOSITORY in .env file.")
    
    payload = {
        'prompt': {
            'text': full_prompt
        },
        'source': {
            'repository': repository,
            'ref': 'main'
        }
    }
    
    # Create agent
    response = requests.post(agents_url, headers=headers, json=payload, timeout=60)
    
    if response.status_code not in [200, 201]:
        raise Exception(f"Failed to create agent: {response.status_code} - {response.text}")
    
    agent_data = response.json()
    agent_id = agent_data.get('id')
    
    if not agent_id:
        raise Exception("No agent ID returned from API")
    
    # Poll for agent completion
    status_url = f"{agents_url}/{agent_id}"
    max_polls = 60  # Maximum number of polls (5 minutes with 5 second intervals)
    poll_count = 0
    
    while poll_count < max_polls:
        status_response = requests.get(status_url, headers=headers, timeout=60)
        
        if status_response.status_code != 200:
            raise Exception(f"Failed to get agent status: {status_response.status_code} - {status_response.text}")
        
        status_data = status_response.json()
        status = status_data.get('status')
        
        if status == 'FINISHED':
            # Extract the generated description from the agent result
            # The exact field name may vary - adjust based on Cursor API response
            result = status_data.get('summary') or status_data.get('result') or status_data.get('output', '')
            return str(result).strip()
        elif status in ['ERROR', 'EXPIRED', 'FAILED']:
            error_msg = status_data.get('error', 'Unknown error')
            raise Exception(f"Agent ended with status {status}: {error_msg}")
        
        # Wait before polling again
        time.sleep(5)
        poll_count += 1
    
    raise Exception("Agent did not complete within timeout period")


def process_file(input_file, output_file=None, api_key=None, api_url=None, repository=None):
    """
    Process the input CSV/Excel file and generate AI descriptions.
    
    Args:
        input_file: Path to input CSV or Excel file
        output_file: Path to output file (default: adds '_generated' to input filename)
        api_key: Cursor API key (or set CURSOR_API_KEY environment variable)
        api_url: Cursor API base URL (optional, defaults to https://api.cursor.com)
        repository: Optional repository URL for agent context
    """
    # Load the prompt template
    prompt_template = load_prompt_template()
    
    # Get API key
    if not api_key:
        api_key = os.getenv("CURSOR_API_KEY")
    if not api_key:
        raise ValueError(
            "Cursor API key not provided. Set CURSOR_API_KEY in a .env file, "
            "as an environment variable, or pass it using the -k parameter."
        )
    
    # Get repository from environment if not provided
    if not repository:
        repository = os.getenv("CURSOR_REPOSITORY")
    
    # Read the input file
    input_path = Path(input_file)
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")
    
    # Determine file type and read accordingly
    if input_path.suffix.lower() == '.csv':
        df = pd.read_csv(input_file)
    elif input_path.suffix.lower() in ['.xlsx', '.xls']:
        df = pd.read_excel(input_file)
    else:
        raise ValueError(f"Unsupported file type: {input_path.suffix}. Use .csv, .xlsx, or .xls")
    
    # Validate required columns
    required_columns = ['title', 'description']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")
    
    # Generate descriptions for each row
    print(f"Processing {len(df)} rows...")
    ai_descriptions = []
    
    for idx, row in df.iterrows():
        print(f"Processing row {idx + 1}/{len(df)}: {row['title'][:50]}...")
        ai_desc = generate_description(
            row['title'],
            row['description'],
            prompt_template,
            api_key,
            api_url,
            repository
        )
        ai_descriptions.append(ai_desc)
        
        # Add a delay to avoid rate limiting (longer for Agent API)
        time.sleep(2)
    
    # Add the AI generated descriptions to the dataframe
    df['AI generated description'] = ai_descriptions
    
    # Determine output file path
    if not output_file:
        output_path = input_path.parent / f"{input_path.stem}_generated{input_path.suffix}"
    else:
        output_path = Path(output_file)
    
    # Save the results
    if output_path.suffix.lower() == '.csv':
        df.to_csv(output_path, index=False)
    elif output_path.suffix.lower() in ['.xlsx', '.xls']:
        df.to_excel(output_path, index=False)
    else:
        # Default to CSV
        output_path = output_path.with_suffix('.csv')
        df.to_csv(output_path, index=False)
    
    print(f"\nCompleted! Results saved to: {output_path}")
    return df


def main():
    """Main entry point for the script."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Generate AI-enhanced descriptions for cybersecurity controls"
    )
    parser.add_argument(
        "input_file",
        help="Path to input CSV or Excel file with 'title' and 'description' columns"
    )
    parser.add_argument(
        "-o", "--output",
        help="Path to output file (default: adds '_generated' to input filename)"
    )
    parser.add_argument(
        "-k", "--api-key",
        help="Cursor API key (or set CURSOR_API_KEY environment variable)"
    )
    parser.add_argument(
        "-u", "--api-url",
        help="Cursor API base URL (default: https://api.cursor.com)"
    )
    parser.add_argument(
        "-r", "--repository",
        help="Repository URL for agent context (required for Agent API, can also set CURSOR_REPOSITORY in .env)"
    )
    
    args = parser.parse_args()
    
    try:
        process_file(args.input_file, args.output, args.api_key, args.api_url, args.repository)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

