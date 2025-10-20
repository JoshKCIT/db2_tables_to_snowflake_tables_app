# Changelog

All notable changes to the DB2 to Snowflake Table Converter project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial release of DB2 to Snowflake Table Converter
- Support for splitting large DB2 DDL files into individual table files
- Comprehensive data type conversion from DB2 to Snowflake
- Primary key constraint handling with separate ALTER TABLE statements
- Default value conversion and function name mapping
- Issue logging for manual review of complex conversions
- Self-test mode for validation
- Cross-platform support (Windows, macOS, Linux)
- Comprehensive documentation and examples

### Features
- **DDL Splitting**: Parses DB2 DDL files and splits into individual table files
- **Data Type Conversion**: Maps 20+ DB2 data types to Snowflake equivalents
- **Constraint Handling**: Converts primary keys, nullability, and default values
- **Issue Tracking**: Generates detailed logs of conversions requiring manual review
- **Batch Processing**: Processes multiple files with manifest generation
- **Command Line Interface**: Flexible CLI with configurable input/output directories

### Supported DB2 Data Types
- Numeric: `DECIMAL`, `NUMERIC`, `INTEGER`, `SMALLINT`, `BIGINT`, `REAL`, `DOUBLE`, `DECFLOAT`
- String: `CHAR`, `VARCHAR`, `GRAPHIC`, `VARGRAPHIC`, `CLOB`, `BLOB`
- Date/Time: `DATE`, `TIME`, `TIMESTAMP`, `TIMESTAMP WITH TIME ZONE`
- Special: `XML` (converted to `VARIANT`)

### Supported Default Value Conversions
- `CURRENT TIMESTAMP` → `CURRENT_TIMESTAMP`
- `CURRENT DATE` → `CURRENT_DATE`
- `CURRENT TIME` → `CURRENT_TIME`
- `USER` → `CURRENT_USER`

## [1.0.0] - 2024-01-01

### Added
- Initial release
- Core conversion functionality
- Documentation and examples
- MIT License

---

## Version History

- **v1.0.0**: Initial release with core conversion features
- **Unreleased**: Future enhancements and improvements

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on contributing to this project.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
