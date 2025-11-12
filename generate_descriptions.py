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
import time
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()

# Read the prompt template
def load_prompt_template():
    """Load the prompt template from the prompt file."""
    prompt_file = Path(__file__).parent / "prompt"
    if not prompt_file.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_file}")
    return prompt_file.read_text()


def generate_description(title, description, prompt_template, api_key, model="gpt-4o-mini"):
    """
    Generate AI description using OpenAI API.
    
    Args:
        title: The control title
        description: The original description
        prompt_template: The prompt template text
        api_key: OpenAI API key
        model: OpenAI model to use (default: gpt-4o-mini)
    
    Returns:
        Generated description string
    """
    # Construct the full prompt
    full_prompt = f"""{prompt_template}

Title: {title}

Description: {description}

Please generate the formatted output according to the format specified above."""

    try:
        # Initialize OpenAI client
        client = OpenAI(api_key=api_key)
        
        # Make API call
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a cybersecurity documentation specialist. Generate structured, professional control documentation in the exact format specified. Your output must start with a piped summary line (e.g., 'Hosts: ... | Classification: ...'), NOT the title. After the piped line, add a blank line, then 'Scope' header and content, then a blank line, then 'Success Criteria' header and content, then a blank line, then 'Notes' header and content. In the Notes section, each sentence must be on a separate line (one sentence per line). The title is provided for context only."},
                {"role": "user", "content": full_prompt}
            ],
            temperature=0.3,
            max_tokens=2000
        )
        
        # Extract the generated content
        output = response.choices[0].message.content.strip()
        
        # Post-process: Remove title if it appears at the start
        # Check if output starts with the title (case-insensitive, allowing for some variation)
        lines = output.split('\n')
        first_line = lines[0].strip()
        
        # If first line matches the title (allowing for minor variations), remove it
        if first_line.lower() == title.lower() or first_line == title:
            output = '\n'.join(lines[1:]).strip()
        
        # Ensure output starts with a piped line (contains "|")
        # If it doesn't, the prompt should have handled it, but this is a safety check
        if output and '|' not in output.split('\n')[0]:
            # Try to find a line with | and make it the first line
            lines = output.split('\n')
            for i, line in enumerate(lines):
                if '|' in line:
                    # Move this line to the beginning
                    lines.insert(0, line)
                    lines.pop(i + 1)
                    output = '\n'.join(lines)
                    break
        
        return output
        
    except Exception as e:
        return f"Error generating description: {str(e)}"


def process_file(input_file, output_file=None, api_key=None, model="gpt-4o-mini"):
    """
    Process the input CSV/Excel file and generate AI descriptions.
    
    Args:
        input_file: Path to input CSV or Excel file
        output_file: Path to output file (default: adds '_generated' to input filename)
        api_key: OpenAI API key (or set OPENAI_API_KEY environment variable)
        model: OpenAI model to use (default: gpt-4o-mini)
    """
    # Load the prompt template
    prompt_template = load_prompt_template()
    
    # Get API key
    if not api_key:
        api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OpenAI API key not provided. Set OPENAI_API_KEY in a .env file, "
            "as an environment variable, or pass it using the -k parameter."
        )
    
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
            model
        )
        ai_descriptions.append(ai_desc)
        
        # Add a delay to avoid rate limiting
        time.sleep(1)
    
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
        help="OpenAI API key (or set OPENAI_API_KEY environment variable)"
    )
    parser.add_argument(
        "-m", "--model",
        default="gpt-4o-mini",
        help="OpenAI model to use (default: gpt-4o-mini). Options: gpt-4o-mini, gpt-4o, gpt-4-turbo, etc."
    )
    
    args = parser.parse_args()
    
    try:
        process_file(args.input_file, args.output, args.api_key, args.model)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

