#!/usr/bin/env python3
"""
Script A: Split DB2 DDL into individual table files
Goal: Split DB2 DDL into one file per table with correct per-file header.

This script takes a large DB2 DDL file containing multiple CREATE TABLE statements
and splits it into individual files, one per table. Each output file includes:
- A header with source file information and extraction timestamp
- The complete CREATE TABLE statement for that specific table
- Proper file naming convention: SCHEMA__TABLE.sql

The script handles:
- Multiple input files (.sql and .txt)
- Comment stripping (both /* */ and -- styles)
- Schema extraction (uses "DEFAULT" if no schema specified)
- Manifest generation for tracking all extracted tables
"""

import argparse  # For command-line argument parsing
import json      # For creating the manifest.json file
import logging   # For progress and error reporting
import re        # For regular expressions to parse SQL
from datetime import datetime, timezone  # For timestamp generation
from pathlib import Path  # For cross-platform file path handling


def setup_logging():
    """
    Set up logging configuration for the script.
    
    This function configures Python's logging module to display INFO level messages
    and above (INFO, WARNING, ERROR, CRITICAL) in a simple format.
    This helps track the script's progress and any issues encountered.
    """
    logging.basicConfig(
        level=logging.INFO,  # Show INFO level and above
        format='%(levelname)s: %(message)s'  # Simple format: "INFO: message"
    )


def strip_comments(content):
    """
    Strip /* ... */ and -- ... comments while preserving line breaks.
    
    This function removes SQL comments from the input content to make parsing easier.
    It handles two types of SQL comments:
    1. Block comments: /* comment text */
    2. Line comments: -- comment text
    
    Args:
        content (str): The SQL content with comments
        
    Returns:
        str: The content with comments removed but line structure preserved
    """
    # Remove /* ... */ block comments using regex
    # re.DOTALL flag makes . match newlines too
    content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
    
    # Remove -- ... line comments (but preserve line breaks)
    lines = content.split('\n')
    cleaned_lines = []
    for line in lines:
        # Find -- comment and remove it, but keep the line if it had content before --
        if '--' in line:
            comment_pos = line.find('--')
            before_comment = line[:comment_pos].rstrip()  # Remove trailing whitespace
            if before_comment:  # Keep the line if there was content before the comment
                cleaned_lines.append(before_comment)
            else:  # Empty line after removing comment
                cleaned_lines.append('')
        else:
            cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines)


def extract_create_table_statements(content):
    """
    Extract CREATE TABLE statements from the content.
    
    This function parses SQL content to find complete CREATE TABLE statements.
    It handles nested parentheses correctly by tracking opening and closing parentheses.
    
    Args:
        content (str): The SQL content (with comments already stripped)
        
    Returns:
        list: List of complete CREATE TABLE statements as strings
    """
    statements = []
    # Use a more sophisticated approach to handle nested parentheses
    lines = content.split('\n')
    current_statement = []  # Accumulates lines for current CREATE TABLE
    paren_count = 0         # Tracks nested parentheses level
    in_create_table = False # Flag indicating we're inside a CREATE TABLE statement
    
    for line in lines:
        line = line.strip()
        if not line:  # Skip empty lines
            continue
            
        # Check if this line starts a CREATE TABLE (with or without schema)
        # Pattern matches: CREATE TABLE schema.table or CREATE TABLE table
        if re.match(r'CREATE\s+TABLE\s+\w+(?:\.\w+)?', line, re.IGNORECASE):
            if current_statement and in_create_table:
                # Save previous statement before starting new one
                statements.append('\n'.join(current_statement))
            current_statement = [line]
            in_create_table = True
            # Count parentheses in this line (opening - closing)
            paren_count = line.count('(') - line.count(')')
        elif in_create_table:
            current_statement.append(line)
            # Update parentheses count for this line
            paren_count += line.count('(') - line.count(')')
            
            # If we've closed all parentheses and hit a semicolon, we're done
            if paren_count <= 0 and line.endswith(';'):
                statements.append('\n'.join(current_statement))
                current_statement = []
                in_create_table = False
                paren_count = 0
    
    # Handle any remaining statement (in case file doesn't end with semicolon)
    if current_statement and in_create_table:
        statements.append('\n'.join(current_statement))
    
    return statements


def extract_schema_table_name(statement):
    """
    Extract schema and table name from CREATE TABLE statement.
    
    This function parses a CREATE TABLE statement to extract the schema and table names.
    If no schema is specified, it uses "DEFAULT" as the schema name.
    
    Args:
        statement (str): The complete CREATE TABLE statement
        
    Returns:
        tuple: (schema_name, table_name) or (None, None) if parsing fails
    """
    # Try to match with schema.table format first
    # Pattern: CREATE TABLE schema.table
    match = re.search(r'CREATE\s+TABLE\s+(\w+)\.(\w+)', statement, re.IGNORECASE)
    if match:
        return match.group(1), match.group(2)  # Return (schema, table)
    
    # If no schema, use DEFAULT as schema name
    # Pattern: CREATE TABLE table
    match = re.search(r'CREATE\s+TABLE\s+(\w+)', statement, re.IGNORECASE)
    if match:
        return "DEFAULT", match.group(1)  # Return (DEFAULT, table)
    
    return None, None  # Return None if parsing fails


def process_input_file(input_file, output_dir, manifest_data, source_file_path):
    """
    Process a single input file and extract CREATE TABLE statements.
    
    This function reads a single input file, extracts all CREATE TABLE statements,
    and writes each one to a separate output file with proper headers.
    
    Args:
        input_file (Path): Path to the input file to process
        output_dir (Path): Directory where output files will be written
        manifest_data (list): List to accumulate manifest entries
        source_file_path (str): Source file path for manifest entries
    """
    logging.info(f"Processing {input_file}")
    
    # Read the input file with UTF-8 encoding
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        logging.error(f"Error reading {input_file}: {e}")
        return
    
    # Strip comments to make parsing easier
    cleaned_content = strip_comments(content)
    
    # Extract all CREATE TABLE statements from the cleaned content
    statements = extract_create_table_statements(cleaned_content)
    
    if not statements:
        logging.warning(f"No CREATE TABLE statements found in {input_file}")
        return
    
    # Process each CREATE TABLE statement
    for statement in statements:
        # Extract schema and table names from the statement
        schema, table = extract_schema_table_name(statement)
        if not schema or not table:
            logging.warning(f"Could not extract schema/table from statement in {input_file}")
            continue
        
        # Create output filename using SCHEMA__TABLE.sql format
        output_filename = f"{schema}__{table}.sql"
        output_path = output_dir / output_filename
        
        # Create header with source file info and extraction timestamp
        utc_time = datetime.now(timezone.utc).isoformat()
        header = f"-- Source file: {source_file_path}\n-- Extracted: {utc_time}\n\n"
        
        # Write the table file with header and statement
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(header + statement)
            
            # Add entry to manifest for tracking
            manifest_data.append({
                "schema": schema,
                "table": table,
                "path": str(output_path),
                "source_file": str(source_file_path)
            })
            
            logging.info(f"Extracted {schema}.{table} to {output_filename}")
        except Exception as e:
            logging.error(f"Error writing {output_path}: {e}")


def main():
    """
    Main function that orchestrates the entire process.
    
    This function handles command-line arguments, runs self-tests if requested,
    and processes all input files to extract CREATE TABLE statements.
    """
    # Set up command-line argument parser
    parser = argparse.ArgumentParser(description='Split DB2 DDL into individual table files')
    parser.add_argument('--in', dest='input_dir', default='data/input',
                       help='Input directory containing .sql files')
    parser.add_argument('--out', dest='output_dir', default='data/output/original_db2_table_creation',
                       help='Output directory for individual table files')
    parser.add_argument('--selftest', action='store_true',
                       help='Run self-test with sample data')
    
    args = parser.parse_args()
    
    # Initialize logging
    setup_logging()
    
    # Handle self-test mode
    if args.selftest:
        logging.info("Running self-test...")
        # Create test data with a sample CREATE TABLE statement
        test_content = """CREATE TABLE APP.ACCOUNT (
  ACCOUNT_ID INTEGER NOT NULL CONSTRAINT PK_ACC PRIMARY KEY,
  NAME VARCHAR(100) FOR SBCS DATA NOT NULL WITH DEFAULT '',
  CRT_TS TIMESTAMP NOT NULL WITH DEFAULT CURRENT TIMESTAMP,
  BAL DECIMAL(18,2) WITH DEFAULT 0,
  NOTES CLOB(1M),
  CODE CHAR(3) WITH DEFAULT
);"""
        
        # Create temporary test file
        test_input_dir = Path('data/input')
        test_input_dir.mkdir(parents=True, exist_ok=True)
        test_file = test_input_dir / 'sample.sql'
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        # Process test file
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        manifest_data = []
        process_input_file(test_file, output_dir, manifest_data, 'data/input/sample.sql')
        
        # Write manifest file
        manifest_path = Path('data/output/manifest.json')
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest_data, f, indent=2)
        
        # Clean up test file
        test_file.unlink()
        
        logging.info("Self-test completed")
        return 0
    
    # Normal processing mode
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    
    # Validate input directory exists
    if not input_dir.exists():
        logging.error(f"Input directory {input_dir} does not exist")
        return 2
    
    # Find all .sql and .txt files in input directory
    sql_files = list(input_dir.glob('*.sql')) + list(input_dir.glob('*.txt'))
    if not sql_files:
        logging.error(f"No .sql or .txt files found in {input_dir}")
        return 2
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Process each input file
    manifest_data = []  # Will store metadata about all extracted tables
    tables_found = 0    # Counter for total tables extracted
    
    for sql_file in sql_files:
        process_input_file(sql_file, output_dir, manifest_data, f"data/input/{sql_file.name}")
        # Count tables extracted from this specific file
        tables_found += len([item for item in manifest_data if item['source_file'] == f"data/input/{sql_file.name}"])
    
    # Validate that we found at least one table
    if tables_found == 0:
        logging.error("No CREATE TABLE statements found in any input files")
        return 3
    
    # Write manifest file with metadata about all extracted tables
    manifest_path = Path('data/output/manifest.json')
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest_data, f, indent=2)
    
    logging.info(f"Successfully processed {len(sql_files)} files, extracted {tables_found} tables")
    return 0


if __name__ == '__main__':
    exit(main())
