@echo off
REM DB2 to Snowflake Table Conversion Script
REM This batch file runs the complete conversion process with one click
REM 
REM Script 1: Split DB2 DDL into individual table files
REM Script 2: Convert DB2 table files to Snowflake DDL
REM
REM Author: Generated for db2_tables_to_snowflake_tables_app
REM Date: %date%

echo ========================================
echo DB2 to Snowflake Table Conversion Tool
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python and try again
    pause
    exit /b 1
)

echo Python found. Starting conversion process...
echo.

REM Change to the script directory
cd /d "%~dp0"

REM Step 1: Split DB2 DDL into individual table files
echo ========================================
echo Step 1: Splitting DB2 DDL files
echo ========================================
echo.

python scripts\01_split_db2_ddl.py --in data\input --out data\output\original_db2_table_creation

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Step 1 failed - DB2 DDL splitting failed
    echo Please check the error messages above and try again
    pause
    exit /b 1
)

echo.
echo Step 1 completed successfully!
echo.

REM Step 2: Convert DB2 table files to Snowflake DDL
echo ========================================
echo Step 2: Converting to Snowflake DDL
echo ========================================
echo.

python scripts\02_convert_to_snowflake.py --in data\output\original_db2_table_creation --out data\output\new_snowflake_table_creation --issues data\output\issues.txt

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Step 2 failed - Snowflake conversion failed
    echo Please check the error messages above and try again
    pause
    exit /b 1
)

echo.
echo Step 2 completed successfully!
echo.

REM Display summary
echo ========================================
echo Conversion Complete!
echo ========================================
echo.
echo Results:
echo - Original DB2 tables: data\output\original_db2_table_creation\
echo - Snowflake tables: data\output\new_snowflake_table_creation\
echo - Issues log: data\output\issues.txt
echo - Manifest: data\output\manifest.json
echo.

REM Check if there are any issues
if exist "data\output\issues.txt" (
    for %%A in ("data\output\issues.txt") do (
        if %%~zA gtr 0 (
            echo WARNING: Issues were found during conversion
            echo Please review data\output\issues.txt for details
            echo.
        )
    )
)

echo Conversion process completed successfully!
echo You can now review the generated Snowflake DDL files.
echo.
pause
