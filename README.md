# DB2 to Snowflake Table Converter

A powerful Python tool that automatically converts DB2 CREATE TABLE statements to Snowflake-compatible DDL. This tool handles complex data type conversions, constraint mappings, and generates detailed issue reports for manual review.

## 🚀 Features

- **Automated DDL Splitting**: Parses large DB2 DDL files and splits them into individual table files
- **Intelligent Type Conversion**: Converts DB2 data types to their Snowflake equivalents
- **Constraint Handling**: Properly handles primary keys, nullability, and default values
- **Issue Tracking**: Generates detailed logs of conversions that may need manual review
- **Batch Processing**: Processes multiple files and generates comprehensive manifests
- **Cross-Platform**: Works on Windows, macOS, and Linux

## 📋 Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage](#usage)
- [Conversion Rules](#conversion-rules)
- [Data Type Mappings](#data-type-mappings)
- [File Structure](#file-structure)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## 🛠 Installation

### Prerequisites

- Python 3.7 or higher
- No additional dependencies required (uses only Python standard library)

### Setup

1. Clone this repository:
```bash
git clone https://github.com/yourusername/db2-to-snowflake-converter.git
cd db2-to-snowflake-converter
```

2. No installation required - the tool runs directly from the repository!

## 🚀 Quick Start

1. **Place your DB2 DDL files** in the `data/input/` directory
2. **Run the conversion**:
   ```bash
   # On Windows
   run_conversion.bat
   
   # On macOS/Linux
   python scripts/01_split_db2_ddl.py
   python scripts/02_convert_to_snowflake.py
   ```
3. **Review the results** in `data/output/new_snowflake_table_creation/`
4. **Check for issues** in `data/output/issues.txt`

## 📖 Usage

### Command Line Options

#### Script 1: Split DB2 DDL (`01_split_db2_ddl.py`)

```bash
python scripts/01_split_db2_ddl.py [options]

Options:
  --in INPUT_DIR     Input directory containing .sql files (default: data/input)
  --out OUTPUT_DIR   Output directory for individual table files (default: data/output/original_db2_table_creation)
  --selftest         Run self-test with sample data
```

#### Script 2: Convert to Snowflake (`02_convert_to_snowflake.py`)

```bash
python scripts/02_convert_to_snowflake.py [options]

Options:
  --in INPUT_DIR     Input directory containing DB2 table files (default: data/output/original_db2_table_creation)
  --out OUTPUT_DIR   Output directory for Snowflake table files (default: data/output/new_snowflake_table_creation)
  --issues ISSUES_FILE  Issues log file (default: data/output/issues.txt)
  --selftest         Run self-test with sample data
```

### Self-Test Mode

Test the tool with sample data:

```bash
python scripts/01_split_db2_ddl.py --selftest
python scripts/02_convert_to_snowflake.py --selftest
```

## 🔄 Conversion Rules

### General Rules

1. **Schema Handling**: Tables without explicit schemas are assigned to "DEFAULT" schema
2. **Comment Preservation**: Source file headers and timestamps are preserved in output files
3. **Primary Keys**: Converted to separate `ALTER TABLE` statements (Snowflake requirement)
4. **Constraint Filtering**: DB2-specific constraints are removed (e.g., `AUDIT`, `DATA CAPTURE`)

### Data Type Conversion Rules

| DB2 Type | Snowflake Type | Notes |
|----------|----------------|-------|
| `DECIMAL(p,s)` | `NUMBER(p,s)` | Direct mapping |
| `NUMERIC(p,s)` | `NUMBER(p,s)` | Direct mapping |
| `INTEGER` | `INTEGER` | Direct mapping |
| `SMALLINT` | `SMALLINT` | Direct mapping |
| `BIGINT` | `BIGINT` | Direct mapping |
| `REAL` | `FLOAT` | Converted to FLOAT |
| `DOUBLE` | `FLOAT` | Converted to FLOAT |
| `DECFLOAT` | `FLOAT` | Converted to FLOAT |
| `CHAR(n)` | `CHAR(n)` | Direct mapping |
| `VARCHAR(n)` | `VARCHAR(n)` | Direct mapping |
| `GRAPHIC(n)` | `VARCHAR(n)` | Unicode conversion |
| `VARGRAPHIC(n)` | `VARCHAR(n)` | Unicode conversion |
| `CLOB` | `VARCHAR` | Size information lost |
| `BLOB` | `BINARY` | Direct mapping |
| `XML` | `VARIANT` | Converted to VARIANT |
| `DATE` | `DATE` | Direct mapping |
| `TIME` | `TIME` | Direct mapping |
| `TIMESTAMP` | `TIMESTAMP_NTZ` | No timezone |
| `TIMESTAMP WITH TIME ZONE` | `TIMESTAMP_TZ` | With timezone |

### Default Value Conversions

| DB2 Expression | Snowflake Expression | Notes |
|----------------|---------------------|-------|
| `CURRENT TIMESTAMP` | `CURRENT_TIMESTAMP` | Function name change |
| `CURRENT DATE` | `CURRENT_DATE` | Function name change |
| `CURRENT TIME` | `CURRENT_TIME` | Function name change |
| `USER` | `CURRENT_USER` | Function name change |
| `WITH DEFAULT` (no value) | *(removed)* | Ambiguous, logged as issue |

## 📁 File Structure

```
db2-to-snowflake-converter/
├── data/
│   ├── input/                          # Place your DB2 DDL files here
│   └── output/
│       ├── original_db2_table_creation/ # Individual DB2 table files
│       ├── new_snowflake_table_creation/ # Converted Snowflake DDL files
│       ├── manifest.json               # Table extraction manifest
│       └── issues.txt                  # Conversion issues log
├── scripts/
│   ├── 01_split_db2_ddl.py            # DDL splitting script
│   └── 02_convert_to_snowflake.py     # Conversion script
├── examples/                           # Example files and outputs
├── run_conversion.bat                  # Windows batch file
├── requirements.txt                    # Python dependencies
├── README.md                          # This file
├── LICENSE                            # MIT License
└── CONTRIBUTING.md                    # Contribution guidelines
```

## 📝 Examples

### Input DB2 DDL

```sql
CREATE TABLE APP.ACCOUNT (
  ACCOUNT_ID INTEGER NOT NULL CONSTRAINT PK_ACC PRIMARY KEY,
  NAME VARCHAR(100) FOR SBCS DATA NOT NULL WITH DEFAULT '',
  CRT_TS TIMESTAMP NOT NULL WITH DEFAULT CURRENT TIMESTAMP,
  BAL DECIMAL(18,2) WITH DEFAULT 0,
  NOTES CLOB(1M),
  CODE CHAR(3) WITH DEFAULT
);
```

### Output Snowflake DDL

```sql
-- Source file: data/input/sample.sql
-- Extracted: 2024-01-01T00:00:00Z

CREATE TABLE APP.ACCOUNT (
  ACCOUNT_ID INTEGER NOT NULL,
  NAME VARCHAR(100) NOT NULL DEFAULT '',
  CRT_TS TIMESTAMP_NTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  BAL NUMBER(18,2) DEFAULT 0,
  NOTES VARCHAR,
  CODE CHAR(3)
);
ALTER TABLE APP.ACCOUNT ADD PRIMARY KEY (ACCOUNT_ID);
```

### Issues Log Example

```
APP.ACCOUNT | NOTES | CLOB mapped to VARCHAR (possible size loss) | CLOB(1M)
APP.ACCOUNT | CODE | ambiguous default removed | WITH DEFAULT
```

## 🔍 Troubleshooting

### Common Issues

1. **"No CREATE TABLE statements found"**
   - Ensure your input files contain valid `CREATE TABLE` statements
   - Check that files are in the correct `data/input/` directory
   - Verify file extensions are `.sql` or `.txt`

2. **"Python is not installed or not in PATH"**
   - Install Python 3.7+ from [python.org](https://python.org)
   - Ensure Python is added to your system PATH

3. **Conversion errors in issues.txt**
   - Review the issues log for manual conversion requirements
   - Some DB2 features may not have direct Snowflake equivalents
   - Consider manual adjustments for complex data types

### Getting Help

- Check the [Issues](https://github.com/yourusername/db2-to-snowflake-converter/issues) page
- Review the examples in the `examples/` directory
- Run the self-test mode to verify installation

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built for the data engineering community
- Inspired by the need for efficient database migration tools
- Thanks to all contributors and users

---

**Made with ❤️ for data engineers migrating from DB2 to Snowflake**
