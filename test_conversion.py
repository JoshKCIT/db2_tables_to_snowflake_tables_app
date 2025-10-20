#!/usr/bin/env python3
"""
Test script for DB2 to Snowflake Table Converter
This script runs the complete conversion process and validates the results.
"""

import subprocess
import sys
from pathlib import Path
import json

def run_command(cmd, description):
    """Run a command and return success status."""
    print(f"\n{'='*50}")
    print(f"Running: {description}")
    print(f"Command: {cmd}")
    print('='*50)
    
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print("SUCCESS")
        if result.stdout:
            print("Output:", result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print("FAILED")
        print("Error:", e.stderr)
        return False

def check_file_exists(file_path, description):
    """Check if a file exists and report status."""
    path = Path(file_path)
    if path.exists():
        print(f"SUCCESS - {description}: {file_path}")
        return True
    else:
        print(f"FAILED - {description}: {file_path} (NOT FOUND)")
        return False

def main():
    """Run the complete test suite."""
    print("DB2 to Snowflake Table Converter - Test Suite")
    print("=" * 60)
    
    # Test 1: Self-test for DDL splitting
    success1 = run_command(
        "python scripts/01_split_db2_ddl.py --selftest --out data/output/original_db2_table_creation",
        "DDL Splitting Self-Test"
    )
    
    # Test 2: Convert the output from Test 1 to Snowflake
    success2 = run_command(
        "python scripts/02_convert_to_snowflake.py --in data/output/original_db2_table_creation --out data/output/new_snowflake_table_creation --issues data/output/issues.txt",
        "Snowflake Conversion"
    )
    
    # Test 3: Check if output files were created
    print(f"\n{'='*50}")
    print("Checking Output Files")
    print('='*50)
    
    files_to_check = [
        ("data/output/original_db2_table_creation/APP__ACCOUNT.sql", "Original DB2 table file"),
        ("data/output/new_snowflake_table_creation/APP__ACCOUNT.sql", "Converted Snowflake file"),
        ("data/output/manifest.json", "Manifest file"),
        ("data/output/issues.txt", "Issues log file")
    ]
    
    all_files_exist = True
    for file_path, description in files_to_check:
        if not check_file_exists(file_path, description):
            all_files_exist = False
    
    # Test 4: Validate manifest content
    manifest_valid = False
    if Path("data/output/manifest.json").exists():
        try:
            with open("data/output/manifest.json", 'r') as f:
                manifest = json.load(f)
            if isinstance(manifest, list) and len(manifest) > 0:
                print("SUCCESS - Manifest contains valid data")
                manifest_valid = True
            else:
                print("FAILED - Manifest is empty or invalid")
        except Exception as e:
            print(f"FAILED - Manifest validation failed: {e}")
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print('='*60)
    
    tests_passed = 0
    total_tests = 4
    
    if success1:
        print("SUCCESS - DDL Splitting: PASSED")
        tests_passed += 1
    else:
        print("FAILED - DDL Splitting: FAILED")
    
    if success2:
        print("SUCCESS - Snowflake Conversion: PASSED")
        tests_passed += 1
    else:
        print("FAILED - Snowflake Conversion: FAILED")
    
    if all_files_exist:
        print("SUCCESS - Output Files: PASSED")
        tests_passed += 1
    else:
        print("FAILED - Output Files: FAILED")
    
    if manifest_valid:
        print("SUCCESS - Manifest Validation: PASSED")
        tests_passed += 1
    else:
        print("FAILED - Manifest Validation: FAILED")
    
    print(f"\nResults: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("All tests passed! The converter is working correctly.")
        return 0
    else:
        print("WARNING: Some tests failed. Please check the output above.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
