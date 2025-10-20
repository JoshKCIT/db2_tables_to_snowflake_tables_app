#!/usr/bin/env python3
"""
Script B: Convert DB2 table files to Snowflake DDL
Goal: Convert each DB2 table file to Snowflake DDL and log issues.

This script takes individual DB2 CREATE TABLE files (created by script A) and converts
them to Snowflake-compatible DDL. It handles:
- Data type conversions (DB2 -> Snowflake)
- Default value conversions
- Constraint handling (especially PRIMARY KEY)
- Issue logging for manual review

The script processes files from the original_db2_table_creation directory and outputs
Snowflake DDL files to the new_snowflake_table_creation directory.
"""

import argparse  # For command-line argument parsing
import logging   # For progress and error reporting
import re        # For regular expressions to parse and convert SQL
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


def log_issue(issues_file, table_name, column_section, issue, snippet):
    """
    Log an issue to the issues file for manual review.
    
    This function appends issues to a log file in a pipe-delimited format.
    Issues include data type conversions, ambiguous defaults, and other
    transformations that might need manual verification.
    
    Args:
        issues_file (Path): Path to the issues log file
        table_name (str): Name of the table where the issue occurred
        column_section (str): Column or section where the issue occurred
        issue (str): Description of the issue
        snippet (str): Code snippet that caused the issue (truncated to 80 chars)
    """
    # Truncate snippet to keep log file readable
    snippet = snippet[:80] if len(snippet) > 80 else snippet
    with open(issues_file, 'a', encoding='utf-8') as f:
        f.write(f"{table_name} | {column_section} | {issue} | {snippet}\n")


def convert_data_type(db2_type, issues_file, table_name, column_name):
    """
    Convert DB2 data type to Snowflake data type.
    
    This function maps DB2 data types to their Snowflake equivalents.
    Some conversions may result in data loss or require manual review,
    which are logged as issues.
    
    Args:
        db2_type (str): The DB2 data type to convert
        issues_file (Path): Path to the issues log file
        table_name (str): Name of the table (for logging)
        column_name (str): Name of the column (for logging)
        
    Returns:
        str: The equivalent Snowflake data type
    """
    # Normalize the input type (uppercase, trimmed)
    db2_type = db2_type.strip().upper()
    
    # Remove DB2-specific FOR SBCS DATA clause (not needed in Snowflake)
    if 'FOR SBCS DATA' in db2_type:
        db2_type = db2_type.replace('FOR SBCS DATA', '').strip()
    
    # Handle FOR BIT DATA - maps to BINARY in Snowflake
    if 'FOR BIT DATA' in db2_type:
        log_issue(issues_file, table_name, column_name, 
                 "mapped to BINARY from FOR BIT DATA", db2_type)
        return 'BINARY'
    
    # Numeric type mappings
    if db2_type.startswith('DECIMAL') or db2_type.startswith('NUMERIC'):
        # DECIMAL and NUMERIC both become NUMBER in Snowflake
        return db2_type.replace('DECIMAL', 'NUMBER').replace('NUMERIC', 'NUMBER')
    elif db2_type in ['SMALLINT', 'INTEGER', 'BIGINT']:
        # These types are directly compatible
        return db2_type
    elif db2_type in ['REAL', 'DOUBLE', 'DECFLOAT']:
        # All floating point types become FLOAT in Snowflake
        return 'FLOAT'
    
    # String type mappings
    elif db2_type.startswith('CHAR') or db2_type.startswith('VARCHAR'):
        # CHAR and VARCHAR are directly compatible
        return db2_type
    elif db2_type.startswith('GRAPHIC') or db2_type.startswith('VARGRAPHIC'):
        # GRAPHIC types (Unicode) map to VARCHAR in Snowflake
        log_issue(issues_file, table_name, column_name,
                 "mapped (VAR)GRAPHIC to VARCHAR", db2_type)
        return db2_type.replace('GRAPHIC', 'VARCHAR').replace('VARGRAPHIC', 'VARCHAR')
    elif db2_type.startswith('CLOB'):
        # CLOB (Character Large Object) maps to VARCHAR with potential size loss
        log_issue(issues_file, table_name, column_name,
                 "CLOB mapped to VARCHAR (possible size loss)", db2_type)
        return 'VARCHAR'
    elif db2_type.startswith('BLOB'):
        # BLOB (Binary Large Object) maps to BINARY
        return 'BINARY'
    
    # Special type mappings
    elif db2_type == 'XML':
        # XML maps to VARIANT in Snowflake
        log_issue(issues_file, table_name, column_name,
                 "XML mapped to VARIANT", db2_type)
        return 'VARIANT'
    elif db2_type == 'DATE':
        return 'DATE'
    elif db2_type == 'TIME':
        return 'TIME'
    elif db2_type == 'TIMESTAMP WITH TIME ZONE':
        return 'TIMESTAMP_TZ'
    elif db2_type == 'TIMESTAMP':
        return 'TIMESTAMP_NTZ'
    else:
        # Return as-is for unknown types (may need manual review)
        return db2_type


def convert_default_value(default_expr, issues_file, table_name, column_name):
    """
    Convert DB2 default value to Snowflake format.
    
    This function converts DB2 default value expressions to Snowflake-compatible
    format. It handles function name changes and ambiguous defaults.
    
    Args:
        default_expr (str): The DB2 default expression
        issues_file (Path): Path to the issues log file
        table_name (str): Name of the table (for logging)
        column_name (str): Name of the column (for logging)
        
    Returns:
        str: The Snowflake-compatible default expression (empty string if no default)
    """
    if not default_expr:
        return ""
    
    default_expr = default_expr.strip()
    
    # Handle bare "WITH DEFAULT" (no value) - this is ambiguous in DB2
    if default_expr.upper() == 'WITH DEFAULT':
        log_issue(issues_file, table_name, column_name,
                 "ambiguous default removed", f"WITH DEFAULT")
        return ""
    
    # Remove "WITH DEFAULT" prefix to get the actual default value
    if default_expr.upper().startswith('WITH DEFAULT '):
        default_expr = default_expr[13:]
    
    # Convert DB2 function names to Snowflake equivalents
    # CURRENT TIMESTAMP -> CURRENT_TIMESTAMP
    default_expr = re.sub(r'\bCURRENT\s+TIMESTAMP\b', 'CURRENT_TIMESTAMP', default_expr, flags=re.IGNORECASE)
    # CURRENT DATE -> CURRENT_DATE
    default_expr = re.sub(r'\bCURRENT\s+DATE\b', 'CURRENT_DATE', default_expr, flags=re.IGNORECASE)
    # CURRENT TIME -> CURRENT_TIME
    default_expr = re.sub(r'\bCURRENT\s+TIME\b', 'CURRENT_TIME', default_expr, flags=re.IGNORECASE)
    
    # Convert USER to CURRENT_USER (DB2 uses USER, Snowflake uses CURRENT_USER)
    if re.search(r'\bUSER\b', default_expr, re.IGNORECASE):
        log_issue(issues_file, table_name, column_name,
                 "USER converted to CURRENT_USER", default_expr)
        default_expr = re.sub(r'\bUSER\b', 'CURRENT_USER', default_expr, flags=re.IGNORECASE)
    
    return f"DEFAULT {default_expr}"


def parse_column_definition(column_def, issues_file, table_name):
    """
    Parse a single column definition and convert it to Snowflake format.
    
    This function takes a DB2 column definition line and converts it to Snowflake
    format, handling data types, constraints, and default values.
    
    Args:
        column_def (str): The DB2 column definition line
        issues_file (Path): Path to the issues log file
        table_name (str): Name of the table (for logging)
        
    Returns:
        str: The converted Snowflake column definition
    """
    column_def = column_def.strip()
    
    # Skip empty lines
    if not column_def:
        return ""
    
    # Extract column name (first word in the definition)
    parts = column_def.split()
    if not parts:
        return column_def
    
    column_name = parts[0]
    
    # Find data type (everything after column name until NOT NULL, WITH DEFAULT, etc.)
    # These keywords mark the end of the data type specification
    type_end_keywords = ['NOT NULL', 'WITH DEFAULT', 'NULL', 'CONSTRAINT', 'PRIMARY KEY', 'UNIQUE', 'CHECK']
    type_end_pos = len(column_def)
    
    # Find the earliest occurrence of any type-ending keyword
    for keyword in type_end_keywords:
        pos = column_def.upper().find(keyword)
        if pos != -1 and pos < type_end_pos:
            type_end_pos = pos
    
    # Split the column definition into data type and remaining attributes
    data_type_part = column_def[len(column_name):type_end_pos].strip()
    remaining_part = column_def[type_end_pos:].strip()
    
    # Convert the data type to Snowflake format
    snowflake_type = convert_data_type(data_type_part, issues_file, table_name, column_name)
    
    # Parse remaining attributes (constraints, nullability, defaults)
    not_null = 'NOT NULL' in remaining_part.upper()
    null_attr = 'NULL' in remaining_part.upper() and 'NOT NULL' not in remaining_part.upper()
    
    # Extract default value using regex
    default_match = re.search(r'WITH\s+DEFAULT\s+([^,\s]+(?:\s+[^,\s]+)*)', remaining_part, re.IGNORECASE)
    default_value = ""
    if default_match:
        default_value = convert_default_value(default_match.group(0), issues_file, table_name, column_name)
    
    # Build the converted column definition
    result_parts = [column_name, snowflake_type]
    
    # Add nullability constraints
    if not_null:
        result_parts.append('NOT NULL')
    elif null_attr:
        result_parts.append('NULL')
    
    # Add default value if present
    if default_value:
        result_parts.append(default_value)
    
    return ' '.join(result_parts)


def extract_primary_keys(statement):
    """
    Extract primary key information from the CREATE TABLE statement.
    
    This function finds primary key definitions in DB2 CREATE TABLE statements.
    It handles both inline (column-level) and table-level primary key definitions.
    
    Args:
        statement (str): The complete CREATE TABLE statement
        
    Returns:
        list: List of column names that form the primary key
    """
    # Look for inline PRIMARY KEY (defined with the column)
    # Pattern: column_name data_type ... PRIMARY KEY
    inline_pk_match = re.search(r'(\w+)\s+[^,\n]+\s+PRIMARY\s+KEY', statement, re.IGNORECASE)
    if inline_pk_match:
        return [inline_pk_match.group(1)]
    
    # Look for table-level PRIMARY KEY definition
    # Pattern: PRIMARY KEY (col1, col2, ...)
    pk_match = re.search(r'PRIMARY\s+KEY\s*\(([^)]+)\)', statement, re.IGNORECASE | re.DOTALL)
    if pk_match:
        # Split the column list and clean up whitespace
        pk_columns = [col.strip() for col in pk_match.group(1).split(',')]
        return pk_columns
    
    return []  # No primary key found


def convert_db2_to_snowflake(content, issues_file, table_name):
    """
    Convert DB2 CREATE TABLE statement to Snowflake format.
    
    This function is the main conversion engine that transforms a complete
    DB2 CREATE TABLE statement into Snowflake-compatible DDL.
    
    Args:
        content (str): The complete DB2 CREATE TABLE statement
        issues_file (Path): Path to the issues log file
        table_name (str): Name of the table (for logging)
        
    Returns:
        str: The converted Snowflake CREATE TABLE statement
    """
    lines = content.split('\n')
    result_lines = []
    in_columns = False  # Flag indicating we're processing column definitions
    column_definitions = []  # List to accumulate converted column definitions
    primary_keys = []  # List to store primary key column names
    
    # Extract primary keys first (needed for separate ALTER TABLE statement)
    primary_keys = extract_primary_keys(content)
    
    for line in lines:
        line = line.strip()
        if not line:  # Skip empty lines
            continue
        
        # Skip comment lines
        if line.startswith('--'):
            continue
        
        # Handle CREATE TABLE line
        if line.upper().startswith('CREATE TABLE'):
            # Extract schema and table name
            # Try schema.table format first
            match = re.search(r'CREATE\s+TABLE\s+(\w+)\.(\w+)', line, re.IGNORECASE)
            if match:
                schema, table = match.groups()
                result_lines.append(f"CREATE TABLE {schema}.{table} (")
                in_columns = True
            else:
                # Handle tables without schema
                match = re.search(r'CREATE\s+TABLE\s+(\w+)', line, re.IGNORECASE)
                if match:
                    table = match.group(1)
                    result_lines.append(f"CREATE TABLE {table} (")
                    in_columns = True
            continue
        
        # Skip DB2-specific options that don't apply to Snowflake
        if any(keyword in line.upper() for keyword in ['PARTITION BY', 'AUDIT', 'DATA CAPTURE', 'CCSID']):
            continue
        
        # Handle end of column definitions
        if line == ')' or line == ');':
            in_columns = False
            # Add all converted column definitions
            for i, col_def in enumerate(column_definitions):
                comma = ',' if i < len(column_definitions) - 1 else ''
                result_lines.append(f"  {col_def}{comma}")
            result_lines.append(");")
            break
        
        # Handle column definitions
        if in_columns:
            # Skip constraint definitions (handled separately)
            if line.upper().startswith(('CONSTRAINT', 'PRIMARY KEY', 'UNIQUE', 'CHECK')):
                continue
                
            # Remove trailing comma from column definition
            if line.endswith(','):
                line = line[:-1]
            
            # Parse and convert column definition
            converted_col = parse_column_definition(line, issues_file, table_name)
            if converted_col and converted_col.strip():
                column_definitions.append(converted_col)
    
    # Add PRIMARY KEY as separate ALTER TABLE statement
    # Snowflake requires primary keys to be added after table creation
    if primary_keys:
        pk_columns = ', '.join(primary_keys)
        result_lines.append(f"ALTER TABLE {table_name} ADD PRIMARY KEY ({pk_columns});")
    
    return '\n'.join(result_lines)


def process_table_file(input_file, output_dir, issues_file):
    """
    Process a single table file and convert it to Snowflake format.
    
    This function reads a DB2 table file, converts it to Snowflake format,
    and writes the result to the output directory while preserving headers.
    
    Args:
        input_file (Path): Path to the input DB2 table file
        output_dir (Path): Directory where output files will be written
        issues_file (Path): Path to the issues log file
        
    Returns:
        bool: True if conversion was successful, False otherwise
    """
    logging.info(f"Processing {input_file}")
    
    # Read the input file
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        logging.error(f"Error reading {input_file}: {e}")
        log_issue(issues_file, "parse_error", "file_read", str(e), str(input_file))
        return False
    
    # Extract table name from filename (SCHEMA__TABLE.sql -> SCHEMA.TABLE)
    table_name = input_file.stem.replace('__', '.')
    
    # Extract header lines (comments at the top of the file)
    lines = content.split('\n')
    header_lines = []
    content_start = 0
    
    # Find all comment lines at the beginning of the file
    for i, line in enumerate(lines):
        if line.strip().startswith('--'):
            header_lines.append(line)
        else:
            content_start = i
            break
    
    # Convert the DB2 statement to Snowflake format
    try:
        converted_content = convert_db2_to_snowflake(content, issues_file, table_name)
    except Exception as e:
        logging.error(f"Error converting {input_file}: {e}")
        log_issue(issues_file, table_name, "conversion_error", str(e), str(input_file))
        return False
    
    # Create output file with the same name as input
    output_file = output_dir / input_file.name
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            # Write preserved header lines
            for header_line in header_lines:
                f.write(header_line + '\n')
            f.write('\n')  # Add blank line after header
            # Write converted content
            f.write(converted_content)
        
        logging.info(f"Converted {table_name} to {output_file.name}")
        return True
    except Exception as e:
        logging.error(f"Error writing {output_file}: {e}")
        log_issue(issues_file, table_name, "file_write", str(e), str(input_file))
        return False


def main():
    """
    Main function that orchestrates the conversion process.
    
    This function handles command-line arguments, runs self-tests if requested,
    and processes all DB2 table files to convert them to Snowflake format.
    """
    # Set up command-line argument parser
    parser = argparse.ArgumentParser(description='Convert DB2 table files to Snowflake DDL')
    parser.add_argument('--in', dest='input_dir', default='data/output/original_db2_table_creation',
                       help='Input directory containing DB2 table files')
    parser.add_argument('--out', dest='output_dir', default='data/output/new_snowflake_table_creation',
                       help='Output directory for Snowflake table files')
    parser.add_argument('--issues', dest='issues_file', default='data/output/issues.txt',
                       help='Issues log file')
    parser.add_argument('--selftest', action='store_true',
                       help='Run self-test with sample data')
    
    args = parser.parse_args()
    
    # Initialize logging
    setup_logging()
    
    # Handle self-test mode
    if args.selftest:
        logging.info("Running self-test...")
        
        # Create test input directory and file
        test_input_dir = Path('data/output/original_db2_table_creation')
        test_input_dir.mkdir(parents=True, exist_ok=True)
        
        # Create test content with various DB2 features
        test_content = """-- Source file: data/input/sample.sql
-- Extracted: 2025-10-20T00:00:00Z

CREATE TABLE APP.ACCOUNT (
  ACCOUNT_ID INTEGER NOT NULL CONSTRAINT PK_ACC PRIMARY KEY,
  NAME VARCHAR(100) FOR SBCS DATA NOT NULL WITH DEFAULT '',
  CRT_TS TIMESTAMP NOT NULL WITH DEFAULT CURRENT TIMESTAMP,
  BAL DECIMAL(18,2) WITH DEFAULT 0,
  NOTES CLOB(1M),
  CODE CHAR(3) WITH DEFAULT
);"""
        
        test_file = test_input_dir / 'APP__ACCOUNT.sql'
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        # Process test file
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Clear issues file for clean test
        issues_file = Path(args.issues_file)
        issues_file.parent.mkdir(parents=True, exist_ok=True)
        with open(issues_file, 'w', encoding='utf-8') as f:
            f.write("")
        
        success = process_table_file(test_file, output_dir, issues_file)
        
        # Clean up test file
        test_file.unlink()
        
        logging.info("Self-test completed")
        return 0 if success else 3
    
    # Normal processing mode
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    issues_file = Path(args.issues_file)
    
    # Validate input directory exists
    if not input_dir.exists():
        logging.error(f"Input directory {input_dir} does not exist")
        return 2
    
    # Find all .sql files in input directory
    sql_files = list(input_dir.glob('*.sql'))
    if not sql_files:
        logging.error(f"No .sql files found in {input_dir}")
        return 2
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Clear issues file for fresh run
    issues_file.parent.mkdir(parents=True, exist_ok=True)
    with open(issues_file, 'w', encoding='utf-8') as f:
        f.write("")
    
    # Process each DB2 table file
    converted_count = 0  # Counter for successfully converted tables
    
    for sql_file in sql_files:
        if process_table_file(sql_file, output_dir, issues_file):
            converted_count += 1
    
    # Validate that at least one table was converted
    if converted_count == 0:
        logging.error("No tables were successfully converted")
        return 3
    
    logging.info(f"Successfully converted {converted_count} tables")
    return 0


if __name__ == '__main__':
    exit(main())
